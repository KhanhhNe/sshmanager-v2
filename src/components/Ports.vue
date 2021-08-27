<template>
  <article>
    <ArticleTitle>
      <template v-slot:title>Ports ({{ ports.length }})</template>
      <button @click="showPortsInput = !showPortsInput">Thêm Port</button>
    </ArticleTitle>
    <div class="ports-input" v-show="showPortsInput">
      <input type="text" v-model="portsText" placeholder="8080,8000-8005,...">
      <a role="button" @click="addPorts">Thêm</a>
    </div>
    <div class="ports">
      <table>
        <thead>
        <tr>
          <th>Port</th>
          <th>IP</th>
          <th><a role="button" @click="changeIP('all')">Đổi</a></th>
          <th><a role="button" @click="removePort('all')" class="secondary">Xoá</a></th>
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
import ArticleTitle from "@/components/ArticleTitle";

export default {
  name: "Ports",
  components: {
    ArticleTitle
  },
  props: {
    ports: Array
  },
  data() {
    return {
      showPortsInput: false,
      portsText: ''
    }
  },
  methods: {
    /**
     * Change a port's proxy (or IP)
     * @param portInfo
     */
    changeIP(portInfo) {
      if (portInfo === 'all') {
        this.ports.map(pInfo => this.changeIP(pInfo))
        return
      }
      alert('change ' + portInfo.port) // TODO add backend code
    },

    /**
     * Remove a port and disconnect it from the proxy
     * @param portInfo
     */
    removePort(portInfo) {
      if (portInfo === 'all') {
        this.ports.map(pInfo => this.removePort(pInfo))
        return
      }
      alert('remove ' + portInfo.port) // TODO add backend code
    },

    /**
     * Add ports to list by parsing from user's input
     */
    addPorts() {
      for (const portText of this.portsText.split(',')) {
        try {
          let ports
          if (portText.includes('-')) {
            const [start, stop] = portText.split('-').map(p => parseInt(p))
            ports = new Array(stop - start + 1).map((val, ind) => start + ind)
          } else {
            ports = [parseInt(portText)]
          }

          // Filter out already added ports
          ports = ports.filter(port => this.ports.filter(p => p.port === port).length === 0)
          this.$emit('add-ports', ports)
        } catch (e) {
          // Do nothing
        }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
article {
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
    overflow: auto;

    a[role=button] {
      padding: 0.25rem 0.5rem;
    }
  }
}
</style>