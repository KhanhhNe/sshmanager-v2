<template>
  <div id="app">
    <SSHList :sshList="sshList" :listName="`SSH (${sshList.length})`" @update-ssh-list="sshList = $event"
             class="all-ssh"></SSHList>
    <SSHTabs class="live-die">
      <SSHList :sshList="liveList" :listName="`Live (${liveList.length})`" :readOnly="true"></SSHList>
      <SSHList :sshList="dieList" :listName="`Die (${dieList.length})`" :readOnly="true"></SSHList>
    </SSHTabs>
    <Ports :ports="ports" @add-ports="addPorts($event)" class="ports"></Ports>
    <Settings :settings="settings" @update-settings="this.settings = $event" class="settings"></Settings>
  </div>
</template>

<script>
import SSHList from './components/SSHList.vue'
import SSHTabs from './components/SSHTabs.vue'
import Ports from './components/Ports.vue'
import Settings from "@/components/Settings";
import '@picocss/pico'

export default {
  name: 'App',
  components: {
    SSHList,
    SSHTabs,
    Ports,
    Settings
  },
  data() {
    return {
      sshList: [
        {
          status: 'live', ip: '255.255.255.1',
          username: 'username',
          password: 'password'
        },
        {
          status: 'live', ip: '255.255.255.2',
          username: 'username',
          password: 'password'
        },
        {
          status: 'live', ip: '255.255.255.3',
          username: 'username',
          password: 'password'
        },
        {
          status: 'die', ip: '255.255.255.4',
          username: 'username',
          password: 'password'
        }
      ],
      ports: [
        {
          port: 80,
          ip: '255.255.255.1'
        },
        {
          port: 8013,
          ip: '255.255.255.2'
        }
      ],
      settings: [
        {
          name: 'remove_died',
          readable_name: "Xoá SSH die",
          value: false
        }
      ]
    }
  },
  computed: {
    liveList() {
      return this.sshList.filter(ssh => ssh.status === 'live')
    },
    dieList() {
      return this.sshList.filter(ssh => ssh.status === 'die')
    }
  },
  methods: {
    addPorts(ports) {
      this.ports = this.ports.concat(ports.map(port => {
        return {
          port,
          ip: ''
        }
      }))
    }
  }
}
</script>

<style lang="scss">
#app {
  $padding: 1rem;
  $gap: 1rem;
  $used_space_vertical: $padding - $gap / 2;
  $used_space_horizontal: $padding - $gap / 2;
  height: 100vh;
  padding: $padding;
  display: grid;
  grid-template-areas:
      "live-die all"
      "ports settings";
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