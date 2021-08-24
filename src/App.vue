<template>
  <div id="app">
    <SSHList :sshList="sshList" listName="Danh sách SSH" @update-ssh-list="sshList = $event" class="all-ssh"></SSHList>
    <SSHTabs class="live-die">
      <SSHList :sshList="liveList" listName="Live" :readOnly="true"></SSHList>
      <SSHList :sshList="dieList" listName="Die" :readOnly="true"></SSHList>
    </SSHTabs>
  </div>
</template>

<script>
import SSHList from './components/SSHList.vue'
import SSHTabs from './components/SSHTabs.vue'
import '@picocss/pico'

export default {
  name: 'App',
  components: {
    SSHList,
    SSHTabs
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
  height: 100vh;
  padding: $padding;
  display: grid;
  grid-template-areas:
      "live-die all"
      "ports all";
  grid-auto-columns: calc(50% - #{$padding}) calc(50% - #{$padding});
  grid-auto-rows: calc(50% - #{$padding}) calc(50% - #{$padding});
  gap: 2rem;
  overflow: hidden;

  .all-ssh {
    grid-area: all;
  }

  .live-die {
    grid-area: live-die;
  }
}
</style>
