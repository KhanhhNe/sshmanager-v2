<template>
  <div id="app">
    <SSHList :sshList="sshList"
             :listName="`SSH (${sshList.length})`"
             @add-ssh="sshRequest($event, 'post')"
             @delete-ssh="sshRequest($event, 'delete')"
             class="all-ssh"></SSHList>
    <SSHTabs class="live-die">
      <SSHList :sshList="liveList"
               :listName="`Live (${liveList.length})`"
               @delete-ssh="sshRequest($event, 'delete')"
               :readOnly="true"></SSHList>
      <SSHList :sshList="dieList"
               :listName="`Die (${dieList.length})`"
               @delete-ssh="sshRequest($event, 'delete')"
               :readOnly="true"></SSHList>
    </SSHTabs>
    <Ports
        :ports="ports"
        @add-ports="portsRequest($event, 'post')"
        @reset-port="portsRequest($event, 'put')"
        @remove-port="portsRequest($event, 'delete')"
        class="ports"></Ports>
  </div>
</template>

<!--suppress JSUnresolvedVariable -->
<script>
import SSHList from './components/SSHList.vue'
import SSHTabs from './components/SSHTabs.vue'
import Ports from './components/Ports.vue'
import '@picocss/pico'
import 'fontisto'

export default {
  name: 'App',
  components: {
    SSHList,
    SSHTabs,
    Ports
  },
  data() {
    return {
      sshSocket: new WebSocket(`ws://${location.host}/api/ssh/`),
      portsSocket: new WebSocket(`ws://${location.host}/api/ports/`),
      sshList: [],
      ports: []
    }
  },
  computed: {
    liveList() {
      return this.sshList.filter(ssh => ssh.is_checked && ssh.is_live)
    },
    dieList() {
      return this.sshList.filter(ssh => ssh.is_checked && !ssh.is_live)
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
      await fetch(`${new URL(location.href).origin}/api/ssh/`, {
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
      await fetch(`${new URL(location.href).origin}/api/ports/`, {
        method,
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(ports)
      })
      this.portsSocket.send('update')
    }
  },
  mounted() {
    const self = this
    this.sshSocket.addEventListener('message', function (event) {
      self.sshList = JSON.parse(event.data)
      for (const ssh of self.sshList) {
        ssh.is_checked = ssh.last_checked !== null
      }
    })
    this.portsSocket.addEventListener('message', function (event) {
      self.ports = JSON.parse(event.data)
    })
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
      "ports all";
  grid-auto-columns: calc(50% - #{$used_space_vertical}) calc(50% - #{$used_space_vertical});
  grid-auto-rows: calc(55% - #{$used_space_vertical}) calc(45% - #{$used_space_horizontal});
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