<template>
  <div id="app">
    <SSHList
        :sshList="sshList"
        :title="`SSH (${sshList.length})`"
        @add-ssh="sshRequest($event, 'post')"
        @delete-ssh="sshRequest($event, 'delete')"
        class="all-ssh"/>
    <Tabs class="live-die">
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
      <Ports
          :ports="ports"
          :title="`Ports (${ports.length})`"
          @add-ports="portsRequest($event, 'post')"
          @reset-port="portsRequest($event, 'put')"
          @remove-port="portsRequest($event, 'delete')"
      />
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
      sshSocket: new WebSocket(`ws://${location.host}/api/ssh/`),
      portsSocket: new WebSocket(`ws://${location.host}/api/ports/`),
      sshList: [],
      ports: [],
      settings: [],
      needRestart: false
    }
  },
  computed: {
    liveList() {
      return this.sshList.filter(ssh => ssh.last_checked !== null && ssh.is_live)
    },
    dieList() {
      return this.sshList.filter(ssh => ssh.last_checked !== null && !ssh.is_live)
    }
  },
  methods: {
    /**
     * Send request to /api/ssh/ with SSH list and specified method, then
     * request an update from server via WebSocket
     * @param sshList
     * @param method
     * @returns {Promise<void>}
     */
    async sshRequest(sshList, method) {
      await fetch('/api/ssh/', {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(sshList)
      })
      this.sshSocket.send('update')
    },

    /**
     * Send request to /api/ports/ with ports and specified method, then request
     * an update from server via WebSocket
     * @param ports
     * @param method
     * @returns {Promise<void>}
     */
    async portsRequest(ports, method) {
      await fetch('/api/ports/', {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(ports)
      })
      this.portsSocket.send('update')
    },

    /**
     * Get settings and settings names, merge them together and update to
     * this.settings
     * @returns {Promise<void>}
     */
    async getSettings() {
      const settingsValues = await (await fetch('/api/settings/')).json()
      const settingsNames = await (await fetch('/api/settings/names/')).json()
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
      this.needRestart = await (await fetch('/api/settings/', {
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
      await fetch('/api/settings/', {method: 'delete'})
      this.needRestart = false
      await this.getSettings()
    }
  },
  mounted() {
    const self = this
    this.sshSocket.addEventListener('message', function (event) {
      self.sshList = JSON.parse(event.data)
    })
    this.portsSocket.addEventListener('message', function (event) {
      self.ports = JSON.parse(event.data)
    })
    this.getSettings()
    tippy('[data-tippy-content]')
  }
}
</script>

<style lang="scss">
@use "sass:math";

#app {
  $padding: 1rem;
  $gap: 1rem;
  $used_space_vertical: $padding - math.div($gap, 2);
  $used_space_horizontal: $padding - math.div($gap, 2);
  height: 100vh;
  padding: $padding;
  display: grid;
  grid-template-areas:
      "live-die all"
      "settings all";
  grid-auto-columns: calc(50% - #{$used_space_vertical}) calc(50% - #{$used_space_vertical});
  grid-auto-rows: calc(50% - #{$used_space_vertical}) calc(50% - #{$used_space_horizontal});
  gap: $gap;
  overflow: hidden;

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

  article {
    display: flex;
    flex-direction: column;
    height: 100%;
    margin: 0;
    padding: 1rem;

    & > *:last-child {
      flex-grow: 1;
    }

    table {
      margin-bottom: auto;

      td, th {
        padding: 0.25rem;
      }
    }
  }
}
</style>