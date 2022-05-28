<template>
  <div id="main-wrapper">
    <NavBar :version="currentVersion" style="grid-area: navbar"></NavBar>
    <div id="main-app" style="grid-area: main-app">
    <span
        v-if="newVersion && newVersion !== currentVersion"
        class="update-available"
    >Đã có phiên bản mới {{ newVersion }}!</span>
      <Tabs style="grid-area: all">
        <SSHList
            :sshList="sortedList"
            :title="`SSH (${sortedList.length})`"
            @add-ssh="sshRequest($event, 'post')"
            @delete-ssh="sshRequest($event, 'delete')"/>
        <SSHList
            :sshList="liveList"
            :title="`Live (${liveList.length})`"
            :readOnly="true"
            @delete-ssh="sshRequest($event, 'delete')"/>
        <SSHList
            :sshList="dieList"
            :title="`Die (${dieList.length})`"
            :readOnly="true"
            @delete-ssh="sshRequest($event, 'delete')"/>
      </Tabs>
      <Tabs style="grid-area: ports">
        <Ports
            :ports="ports"
            :title="`Ports (${ports.length})`"
            @add-ports="portsRequest($event, 'post')"
            @reset-port="portsRequest($event, 'put')"
            @remove-port="portsRequest($event, 'delete')"
        />
        <SSHStore></SSHStore>
      </Tabs>
      <Tabs style="grid-area: settings">
        <Settings
            title="Settings"
            class="settings"/>
      </Tabs>
    </div>
  </div>
</template>

<!--suppress JSUnresolvedVariable -->
<script>
import NavBar from "@/components/NavBar";
import SSHList from './components/SSHList.vue'
import Tabs from './components/Tabs.vue'
import Ports from './components/Ports.vue'
import Settings from './components/Settings.vue'
import tippy from 'tippy.js'
import '@picocss/pico'
import 'fontisto'
import _ from 'lodash';
import {setupWebsocket} from "@/utils";
import SSHStore from "@/components/SSHStore";
import {useSettingsStore} from "@/stores/settings";

export default {
  name: 'App',
  components: {
    SSHStore,
    NavBar,
    Tabs,
    SSHList,
    Ports,
    Settings,
  },
  data() {
    return {
      a: SSHStore,
      sshList: [],
      ports: [],
      settingsStore: useSettingsStore(),
      currentVersion: "",
      newVersion: ""
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
    }
  },
  mounted() {
    const self = this, sshList = this.sshList, ports = this.ports

    setTimeout(() => setupWebsocket(sshList, `ws://${location.host}/api/ssh`))
    setTimeout(() => setupWebsocket(ports, `ws://${location.host}/api/ports`))

    this.settingsStore.loadSettings()
    tippy('[data-tippy-content]')

    this.currentVersion = localStorage.getItem("SSHManager version")
    fetch('/openapi.json')
        .then(resp => resp.json())
        .then(json => {
          self.currentVersion = json.info.version
          localStorage.setItem("SSHManager version", self.currentVersion)
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
  width: auto;
}

[data-tooltip]:not(a):not(button):not(input) {
  border-bottom: none;
}

td {
  border-bottom: var(--border-width) solid var(--table-border-color) !important;
}

#main-wrapper {
  display: grid;
  grid-template-areas: "navbar main-app";
  grid-auto-columns: min-content 1fr;
  gap: 1rem;

  #main-app {
    $padding: 1rem;
    $gap: 2rem;
    height: 100vh;
    padding: $padding;
    display: grid;
    grid-template-areas:
      "all ports"
      "all settings";
    grid-auto-columns: calc(60% - #{$padding}) calc(40% - #{$padding});
    grid-auto-rows: calc(50% - #{$padding}) calc(50% - #{$padding});
    gap: $gap;
    //overflow: hidden;

    & > * {
      display: flex;
      flex-direction: column;
      height: 100%;

      table {
        margin-bottom: auto;
      }
    }

    .update-available {
      position: absolute;
      top: 95vh;
      color: red;
      font-size: 1rem;
    }
  }
}
</style>