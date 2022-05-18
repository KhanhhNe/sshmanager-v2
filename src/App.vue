<template>
  <div id="main-app">
    <span
        v-if="newVersion && newVersion !== currentVersion"
        class="update-available"
    >Đã có phiên bản mới {{ newVersion }}!</span>
    <Tabs class="live-die">
      <Ports
          :ports="ports"
          :title="`Ports (${ports.length})`"
          @add-ports="portsRequest($event, 'post')"
          @reset-port="portsRequest($event, 'put')"
          @remove-port="portsRequest($event, 'delete')"
      />
    </Tabs>
    <Tabs class="all-ssh">
      <SSHList
          :sshList="sortedList"
          :title="`SSH (${sortedList.length})`"
          @add-ssh="sshRequest($event, 'post')"
          @delete-ssh="sshRequest($event, 'delete')"/>
      <SSHList
          :sshList="liveList"
          :title="`Live (${liveList.length})`"
          @delete-ssh="sshRequest($event, 'delete')"
          :readOnly="true"/>
      <SSHList
          :sshList="dieList"
          :title="`Die (${dieList.length})`"
          @delete-ssh="sshRequest($event, 'delete')"
          :readOnly="true"/>
    </Tabs>
    <Tabs>
      <Settings
          title="Settings"
          :settings="settings"
          :needRestart="needRestart"
          @update-settings="updateSettings($event)"
          @reset-settings="resetSettings()"
          class="settings"/>
    </Tabs>
  </div>
</template>

<!--suppress JSUnresolvedVariable -->
<script>
import SSHList from './components/SSHList.vue'
import Tabs from './components/Tabs.vue'
import Ports from './components/Ports.vue'
import Settings from './components/Settings.vue'
import tippy from 'tippy.js'
import '@picocss/pico'
import 'fontisto'
import _ from 'lodash';

export default {
  name: 'App',
  components: {
    Tabs,
    SSHList,
    Ports,
    Settings,
  },
  data() {
    return {
      sshList: [],
      ports: [],
      settings: [],
      currentVersion: "",
      newVersion: "",
      needRestart: false
    }
  },
  computed: {
    liveList() {
      return this.sshList.filter(ssh => ssh.last_checked !== null && ssh.is_live)
    },
    dieList() {
      return this.sshList.filter(ssh => ssh.last_checked !== null && !ssh.is_live)
    },
    sortedList() {
      return _.orderBy(this.sshList, ({last_checked}) => last_checked || '', ['desc'])
    }
  },
  methods: {
    /**
     * Send request to /api/ssh with SSH list and specified method
     * @param sshList
     * @param method
     * @returns {Promise<void>}
     */
    async sshRequest(sshList, method) {
      if (method === 'delete') {
        sshList = _.map(sshList, ssh => ssh.id)
      }
      await fetch('/api/ssh', {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(sshList)
      })
    },

    /**
     * Send request to /api/ports with ports and specified method
     * @param ports
     * @param method
     * @returns {Promise<void>}
     */
    async portsRequest(ports, method) {
      if (['put', 'delete'].includes(method)) {
        ports = _.map(ports, port => port.port_number)
      }
      await fetch('/api/ports', {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(ports)
      })
    },

    /**
     * Get settings and settings names, merge them together and update to
     * this.settings
     * @returns {Promise<void>}
     */
    async getSettings() {
      const settingsValues = await (await fetch('/api/settings')).json()
      const settingsNames = await (await fetch('/api/settings/names')).json()
      const settings = []
      for (const [name, value] of Object.entries(settingsValues)) {
        const readable_name = settingsNames[name]
        settings.push({name, value, readable_name})
      }
      this.settings = settings
    },

    /**
     * Send settings update request to BE and call getSettings to sync FE & BE
     * again
     * @returns {Promise<void>}
     */
    async updateSettings(newSettings) {
      const settings = {}
      for (const setting of newSettings) {
        settings[setting.name] = setting.value
      }
      this.needRestart = await (await fetch('/api/settings', {
        method: 'post',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
      })).json().needRestart
      await this.getSettings()
    },

    /**
     * Reset all settings and call getSettings
     * @returns {Promise<void>}
     */
    async resetSettings() {
      await fetch('/api/settings', {method: 'delete'})
      this.needRestart = false
      await this.getSettings()
    }
  },
  beforeCreate() {
  },
  mounted() {
    fetch('/openapi.json').then(resp => resp.json()).then(data => {
      document.title = `SSHManager v${data.info.version}`
    })

    function setupWebsocket(objectsList, endpoint) {
      let socket, updateInterval
      let lastModified = null
      connect()

      function connect() {
        try {
          if (socket) socket.close()
          socket = new WebSocket(endpoint)
          addListeners(socket)
        } catch (e) {
          console.error(e)
          setTimeout(connect, 1000)
        }
      }

      function requestUpdate() {
        if (socket.readyState !== WebSocket.OPEN) return

        socket.send(JSON.stringify({
          last_modified: lastModified,
          ids: _.map(objectsList, item => item.id)
        }))
      }

      function addListeners(s) {
        s.addEventListener('open', function () {
          requestUpdate()
          clearInterval(updateInterval)
          updateInterval = setInterval(requestUpdate, 200)
        })

        s.addEventListener('message', function (event) {
          const data = JSON.parse(event.data)
          lastModified = data.last_modified || lastModified

          // Update/Insert objects from database
          for (const item of data.objects) {
            const itemInList = _.find(objectsList, val => val.id === item.id)
            if (itemInList) {
              Object.assign(itemInList, item)
            } else {
              objectsList.push(item)
            }
          }

          // Remove objects that no longer in the database
          for (const itemId of data.removed) {
            const itemIndex = _.findIndex(objectsList, item => item.id === itemId)
            if (itemIndex !== -1) {
              objectsList.splice(itemIndex, 1)
            }
          }
        })

        s.addEventListener('close', () => setTimeout(connect, 1000))
      }
    }

    setupWebsocket(this.sshList, `ws://${location.host}/api/ssh`)
    setupWebsocket(this.ports, `ws://${location.host}/api/ports`)

    const self = this

    this.getSettings()
    tippy('[data-tippy-content]')

    fetch('/openapi.json')
        .then(resp => resp.json())
        .then(json => {
          self.currentVersion = json.info.version
        })
    fetch('https://raw.githubusercontent.com/KhanhhNe/sshmanager-v2/master/package.json')
        .then(resp => resp.json())
        .then(json => {
          self.newVersion = json.version
        })
  }
}
</script>

<style lang="scss">
@use "sass:math";

$base-font-size: 15px;

h1, h2, h3, h4, h5, h6 {
  --typography-spacing-vertical: 0;
}

:root {
  --font-size: #{$base-font-size};
  --spacing: 0.5rem;
  --form-element-spacing-vertical: 0.5rem;
  --form-element-spacing-horizontal: 0.75rem;
  --border-radius: 0.5rem;
}

@media (min-width: 576px) {
  :root {
    --font-size: #{$base-font-size + 1};
  }
}

@media (min-width: 768px) {
  :root {
    --font-size: #{$base-font-size + 2};
  }
}

@media (min-width: 992px) {
  :root {
    --font-size: #{$base-font-size + 3};
  }
}

@media (min-width: 1200px) {
  :root {
    --font-size: #{$base-font-size + 4};
  }
}

article {
  margin: 0;
}

input, select, textarea, button {
  margin-bottom: 0 !important;
}

.update-available {
  position: absolute;
  bottom: 0;
  color: red;
  font-size: 1rem;
}

#main-app {
  $padding: 1rem;
  $gap: 2rem;
  height: 100vh;
  padding: $padding;
  display: grid;
  grid-template-areas:
      "all live-die"
      "all settings";
  grid-auto-columns: calc(60% - #{$padding}) calc(40% - #{$padding});
  grid-auto-rows: calc(50% - #{$padding}) calc(50% - #{$padding});
  gap: $gap;
  //overflow: hidden;

  .all-ssh {
    grid-area: all;
  }

  .live-die {
    grid-area: live-die;
  }

  .ports {
    grid-area: ports;
  }

  .settings {
    grid-area: settings;
  }

  & > * {
    display: flex;
    flex-direction: column;
    height: 100%;

    table {
      margin-bottom: auto;
    }
  }
}
</style>