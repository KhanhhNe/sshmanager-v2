<template>
  <div id="app">
    <SSHList :sshList="sshList" listName="Danh sách SSH" @update-ssh-list="sshList = $event"></SSHList>
    <SSHList :sshList="liveList" listName="Live" :readOnly="true"></SSHList>
    <SSHList :sshList="dieList" listName="Die" :readOnly="true"></SSHList>
  </div>
</template>

<script>
import SSHList from './components/SSHList.vue'
import '@picocss/pico'

export default {
  name: 'App',
  components: {
    SSHList
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
</style>
