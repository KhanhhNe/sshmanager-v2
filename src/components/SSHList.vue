<!--suppress JSUnresolvedVariable -->
<template>
  <article v-show="!hidden">
    <ArticleTitle>
      <template v-slot:title>{{ title }}</template>
      <label style="padding-right: 0">Hiển thị</label>
      <select v-model="displayLimit" style="margin-right: 0.75rem">
        <option :value="200" selected>200</option>
        <option :value="500">500</option>
        <option :value="1000">1000</option>
        <option :value="2000">2000</option>
        <option :value="Infinity">Tất cả</option>
      </select>
      <button
          v-if="!readOnly"
          v-on:click="$refs.fileInput.click()"
          data-tippy-content="Tải lên"><i class="fi fi-upload"></i></button>
      <button
          @click="downloadSSHList"
          data-tippy-content="Tải xuống"
          style="margin-right: 0.75rem"><i class="fi fi-download"></i></button>
      <button
          @click="$emit('delete-ssh', sshList)"
          data-tippy-content="Xoá"
          class="secondary outline"><i class="fi fi-trash"></i></button>
    </ArticleTitle>
    <div class="list-content">
      <table>
        <thead>
        <tr>
          <td>T.Trạng</td>
          <td>IP</td>
          <td>Username</td>
          <td>Password</td>
          <td>Check</td>
        </tr>
        </thead>
        <tbody>
        <tr
            v-for="ssh in sshList.slice(0, displayLimit)"
            :key="getSshText(ssh)"
            :class="ssh.status_text"
            class="ssh">
          <td>{{ ssh.status_text || (ssh.is_checking ? 'checking' : '') }}
          </td>
          <td>{{ ssh.ip }}</td>
          <td>{{ ssh.username }}</td>
          <td>{{ ssh.password }}</td>
          <td>{{ getTimeDisplay(ssh.last_checked) }}
          </td>
        </tr>
        </tbody>
      </table>
      <input
          v-if="!readOnly"
          ref="fileInput"
          @change="getSSHListFromFile($event.target.files[0])"
          type="file"
          accept="text/plain, text/csv"
          style="display: none">
    </div>
  </article>
</template>

<!--suppress JSUnusedGlobalSymbols -->
<script>
import ArticleTitle from "@/components/ArticleTitle";
import {saveAs} from "file-saver";
import {getSshText, getTimeDisplay, isInList, readFileAsText} from "@/utils";

export default {
  name: 'SSHList',
  components: {
    ArticleTitle
  },
  data() {
    return {
      hidden: false,
      displayLimit: 200
    }
  },
  props: {
    sshList: Array,
    title: String,
    readOnly: Boolean
  },
  computed: {
    sshText() {
      return this.sshList.map(this.getSshText).join('\n')
    }
  },
  methods: {
    getTimeDisplay,
    getSshText,

    /**
     * Get SSH list from input#file-upload
     * @param file
     * @returns {Promise<void>}
     */
    async getSSHListFromFile(file) {
      const sshList = []
      for (const line of (await readFileAsText(file)).split('\n')) {
        try {
          const [ip, username, password] = line
              .match(new RegExp(/(?:\d+\.){3}\d+(?:\|[^|]*){2}/g))[0]
              .split('|')
          const ssh = {
            is_live: false,
            ip, username, password
          }
          // Only add more if it's not added
          if (!isInList(ssh, sshList)) {
            sshList.push(ssh)
          }
        } catch (e) {
          console.error(`SSH file parsing error: ${e}`)
        }
      }
      await this.updateSSH(sshList)
    },

    /**
     * Download SSH list to a text file
     */
    downloadSSHList() {
      const data = new Blob([this.sshText], {
        type: 'text/plain;charset=utf-8'
      })
      saveAs(data, `${this.title}.txt`)
    },

    /**
     * Update SSH list to backend
     */
    async updateSSH(sshList) {
      const added = sshList.filter(ssh => !isInList(ssh, this.sshList))
      const removed = this.sshList.filter(ssh => !isInList(ssh, sshList))

      this.$emit('delete-ssh', removed)
      this.$emit('add-ssh', added)
    }
  },
  mounted() {
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
article {
  .list-content {
    display: flex;
    overflow: auto;

    textarea {
      flex-grow: 1;
      margin: 0;
      resize: none;
    }
  }

  table {
    white-space: nowrap;

    .ssh {
      &.live td:first-child {
        color: green
      }

      &.die td:first-child {
        color: red
      }
    }
  }
}
</style>
