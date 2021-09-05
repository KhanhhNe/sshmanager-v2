<!--suppress JSUnresolvedVariable -->
<template>
  <article>
    <ArticleTitle>
      <template v-slot:title>Ports ({{ ports.length }})</template>
      <input type="text" v-model="portsText" placeholder="8080,8000-8005,...">
      <button @click="addPorts">Thêm Port</button>
    </ArticleTitle>
    <div class="ports">
      <table>
        <thead>
        <tr>
          <th>Port</th>
          <th>IP</th>
          <th>Check</th>
          <th><a role="button"
                 @click="$emit('reset-port', ports)">Đổi</a></th>
          <th><a role="button"
                 @click="$emit('remove-port', ports)"
                 class="secondary">Xoá</a></th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="portInfo in ports" :key="portInfo.port">
          <td>{{ portInfo.port }}</td>
          <td>{{ portInfo.ip }}</td>
          <td>{{ getTimeDisplay(portInfo.last_checked) }}</td>
          <td><a role="button"
                 @click="$emit('reset-port', [portInfo])">Đổi</a></td>
          <td><a role="button"
                 @click="$emit('remove-port', [portInfo])"
                 class="secondary">Xoá</a></td>
        </tr>
        </tbody>
      </table>
    </div>
  </article>
</template>

<script>
import ArticleTitle from "@/components/ArticleTitle"
import {getTimeDisplay} from "@/utils"

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
    getTimeDisplay,

    /**
     * Add ports to list by parsing from user's input
     */
    addPorts() {
      for (const portText of this.portsText.split(',')) {
        try {
          let ports
          if (portText.includes('-')) {
            const [start, stop] = portText
                .split('-')
                .map(p => parseInt(p))
            ports = [...new Array(stop - start + 1).keys()]
                .map(val => val + start)
          } else {
            ports = [parseInt(portText)]
          }

          // Filter out already added ports
          ports = ports.filter(port => !this.ports.includes(port))
          this.$emit('add-ports', ports.map(port => {
            return {port: port}
          }))
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

  input {
    padding: 0 0.25rem !important;
    height: auto !important;
    width: 35% !important;
  }
}
</style>