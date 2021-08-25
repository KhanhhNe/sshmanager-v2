<template>
  <article>
    <div class="title">
      <h2>Ports ({{ ports.length }})</h2>
      <button @click="showPortsInput = !showPortsInput">Thêm Port</button>
    </div>
    <div class="ports-input" v-show="showPortsInput">
      <input type="text" id="ports" placeholder="8080,8000-8005,...">
      <a role="button">Thêm</a>
    </div>
    <div class="ports">
      <table>
        <thead>
        <tr>
          <th>Port</th>
          <th>IP</th>
          <th><a role="button" @click="changeIP('all')">Đổi</a></th>
          <th><a role="button" @click="changeIP('all')" class="secondary">Xoá</a></th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="portInfo in ports" :key="portInfo.port">
          <td>{{ portInfo.port }}</td>
          <td>{{ portInfo.ip }}</td>
          <td><a role="button" @click="changeIP(portInfo)">Đổi</a></td>
          <td><a role="button" @click="removePort(portInfo)" class="secondary">Xoá</a></td>
        </tr>
        </tbody>
      </table>
    </div>
  </article>
</template>

<script>
export default {
  name: "Ports",
  props: {
    ports: Array
  },
  data() {
    return {
      showPortsInput: false
    }
  },
  methods: {
    changeIP(portInfo) {
      if (portInfo === 'all') {
        this.ports.map(pInfo => this.changeIP(pInfo))
        return
      }
      alert('change ' + portInfo.port)
    },
    removePort(portInfo) {
      if (portInfo === 'all') {
        this.ports.map(pInfo => this.removePort(pInfo))
        return
      }
      alert('remove ' + portInfo.port)
    }
  }
}
</script>

<style lang="scss" scoped>
article {
  display: flex;
  flex-direction: column;
  margin: 0;

  .title {
    display: flex;
    align-items: center;
    justify-content: space-between;

    h2 {
      margin-bottom: 1rem;
    }

    button {
      width: auto;
    }
  }

  .ports-input {
    display: flex;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;

    * {
      margin: 0 !important;
    }
  }

  .ports {
    flex-shrink: 1;
    overflow: auto;

    a[role=button] {
      padding: 0.25rem 0.5rem;
    }
  }
}
</style>