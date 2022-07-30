<!--suppress JSUnresolvedVariable -->
<template>
  <article>
    <ArticleTitle :title="title">
      <div>
        <input
            type="text"
            v-model="portsText"
            placeholder="8080,8000-8005,..."
            style="width: 10rem">
        <button
            @click="addPorts"
            data-tippy-content="Thêm ports"><i class="fi fi-plus-a"></i></button>
      </div>
    </ArticleTitle>
    <div class="ports">
      <table>
        <thead>
        <tr>
          <th>Port</th>
          <th>IP</th>
          <th>Check</th>
          <th>
            <button
                @click="$emit('reset-port', ports)"
                data-tippy-content="Đổi lại toàn bộ ports"
            ><i class="fi fi-spinner-refresh"></i></button>
          </th>
          <th>
            <button
                @click="$emit('remove-port', ports)"
                class="secondary outline"
                data-tippy-content="Xoá toàn bộ ports"
            ><i class="fi fi-trash"></i></button>
          </th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="portInfo in ports" :key="portInfo.port_number">
          <td @click="copyProxyUrl()" :data-clipboard-text="proxyUrl(portInfo)" class="port-number">
            {{ portInfo.port_number }}
          </td>
          <td class="port-info" v-if="portInfo.ssh">
            <span v-if="!portInfo.time_connected" data-tooltip="Đang kết nối">
              <i class="fi fi-spinner fi-spin"
                 style="color: var(--primary)"></i>
            </span>
            <span v-else-if="portInfo.public_ip === portInfo.ssh.ip" data-tooltip="Đã kết nối">
              <i class="fi fi-slightly-smile"
                 style="color: green"></i>
            </span>
            <span v-else data-tooltip="Kết nối thất bại">
              <i class="fi fi-frowning"
                 style="color: red"></i>
            </span>
            <span class="proxy-ip">{{ portInfo.ssh.ip }}</span>
          </td>
          <td v-else class="port-info">
            <i class="fi fi-frowning" style="color: red"></i>
            <span style="opacity: 0.3">Chưa kết nối</span>
          </td>
          <td>{{ getTimeDisplay(portInfo.last_checked) || '' }}</td>
          <td>
            <button
                @click="$emit('reset-port', [portInfo])"
            ><i class="fi fi-spinner-refresh"></i></button>
          </td>
          <td>
            <button
                @click="$emit('remove-port', [portInfo])"
                class="secondary outline"
            ><i class="fi fi-trash"></i></button>
          </td>
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
import "tippy.js/dist/tippy.css"

export default {
  name: "Ports",
  components: {
    ArticleTitle,
  },
  props: {
    ports: Array,
    title: String,
  },
  data() {
    return {
      showPortsInput: false,
      portsText: '',
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
            return {port_number: port}
          }))
        } catch (e) {
          // Do nothing
        }
      }
    },

    /**
     * Copy proxy URL to clipboard
     */
    copyProxyUrl() {
      const clipboard = new ClipboardJS('.port-number')
      clipboard.on('success', e => {
        e.clearSelection()
        e.trigger.setAttribute('data-tooltip', 'Đã copy')
        setTimeout(() => {
          e.trigger.removeAttribute('data-tooltip')
        }, 1000)
      })
    },

    /**
     * Get proxy URL
     */
    proxyUrl(portInfo) {
      return `socks5://${new URL(location.href).hostname}:${portInfo.port_number}`
    },
  },
  watch: {
    ports() {
      new ClipboardJS('.port-info')
      // noinspection JSUnusedGlobalSymbols
      delegate('.ports', {
        target: '.port-info',
        content: 'Đã copy',
        trigger: 'click',
        onShow(instance) {
          setTimeout(() => instance.hide(), 1000)
        },
      })
    },
  },
}
</script>

<style lang="scss" scoped>
article {
  display: flex;
  flex-direction: column;

  .ports {
    overflow: auto;

    th button {
      border-width: 1px !important;
    }

    .port-number {
      z-index: 999;

      &:hover {
        cursor: pointer;
        text-decoration: underline;
      }
    }

    .port-info > * {
      margin-top: auto;
      margin-bottom: auto;
      margin-right: 0.5rem;
    }
  }
}
</style>