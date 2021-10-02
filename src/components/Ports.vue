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
          <td v-if="portInfo.ssh">
            <span :data-clipboard-text="proxyUrl(portInfo)"
                  class="proxy-ip">{{ portInfo.ip }}</span>
          </td>
          <td v-else class="no-proxy">Chưa kết nối</td>
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
import ClipboardJS from "clipboard"
import {delegate} from "tippy.js"
import "tippy.js/dist/tippy.css";

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
    },

    /**
     * Get proxy URL for display. Returns an empty string if port is not
     * connected to any SSH
     * @param portInfo port
     * @returns {string} Proxy string in format <scheme>://<host>:<port>
     */
    proxyUrl(portInfo) {
      if (portInfo.ssh) {
        return `socks5://${new URL(location.href).hostname}:${portInfo.port}`
      } else {
        return ''
      }
    }
  },
  watch: {
    ports() {
      new ClipboardJS('.proxy-ip')
      delegate('.ports', {
        target: '.proxy-ip',
        content: 'Đã copy',
        trigger: 'click',
        onShow(instance) {
          setTimeout(() => instance.hide(), 1000)
        }
      })
    }
  }
}
</script>

<style lang="scss" scoped>
article {
  .ports {
    overflow: auto;

    a[role=button] {
      padding: 0.25rem 0.5rem;
    }

    .proxy-ip:hover {
      cursor: pointer;
    }

    .no-proxy {
      opacity: 0.3;
    }
  }

  input {
    padding: 0 0.25rem !important;
    height: auto !important;
    width: 35% !important;
  }
}
</style>