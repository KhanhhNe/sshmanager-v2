<template>
  <div id="app">
    <SSHList :sshList="sshList" :listName="`SSH (${sshList.length})`" @update-ssh-list="sshList = $event" class="all-ssh"></SSHList>
    <SSHTabs class="live-die">
      <SSHList :sshList="liveList" :listName="`Live (${liveList.length})`" :readOnly="true"></SSHList>
      <SSHList :sshList="dieList" :listName="`Die (${dieList.length})`" :readOnly="true"></SSHList>
    </SSHTabs>
    <Ports :ports="ports"></Ports>
  </div>
</template>

<script>
import SSHList from './components/SSHList.vue'
import SSHTabs from './components/SSHTabs.vue'
import Ports from './components/Ports.vue'
import '@picocss/pico'

export default {
  name: 'App',
  components: {
    SSHList,
    SSHTabs,
    Ports
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
  }
}
</script>

<style lang="scss">
#app {
  $padding: 1rem;
  $gap: 1rem;
  $used_space: $padding - $gap / 2;
  height: 100vh;
  padding: $padding;
  display: grid;
  grid-template-areas:
      "live-die all"
      "ports all";
  grid-auto-columns: calc(50% - #{$used_space}) calc(50% - #{$used_space});
  grid-auto-rows: calc(50% - #{$used_space}) calc(50% - #{$used_space});
  gap: $gap;
  overflow: hidden;

  .all-ssh {
    grid-area: all;
  }

  .live-die {
    grid-area: live-die;
  }

  article {
    padding: 1rem;
  }

  table td, table th {
    padding: 0.25rem;
  }
}
</style>