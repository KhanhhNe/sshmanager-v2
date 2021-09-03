<!--suppress JSUnresolvedVariable -->
<template>
  <article v-show="!hidden">
    <ArticleTitle>
      <template v-slot:title>{{ listName }}</template>
      <button v-if="!readOnly"
              @click="fileInput.click()"><i class="fi fi-upload"></i></button>
      <button @click="downloadSSHList"><i class="fi fi-download"></i></button>
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
            v-for="ssh in sshList"
            :key="getSshText(ssh)"
            :class="[ssh.is_checked ? (ssh.is_live ? 'live' : 'die') : '']"
            class="ssh"
        >
          <td>{{ ssh.is_checked ? (ssh.is_live ? 'Live' : 'Die') : '' }}</td>
          <td>{{ ssh.ip }}</td>
          <td>{{ ssh.username }}</td>
          <td>{{ ssh.password }}</td>
          <td>{{ getTimeDisplay(ssh.last_checked) }}</td>
        </tr>
        </tbody>
      </table>
      <input v-if="!readOnly"
             :id="`${listName}-upload`"
             @change="getSSHListFromFile"
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
import {getSshText, getTimeDisplay, isInList, isSameSSH} from "@/utils";

export default {
  name: 'SSHList',
  components: {
    ArticleTitle
  },
  data() {
    return {
      hidden: false
    }
  },
  props: {
    sshList: Array,
    listName: String,
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
    isSameSSH,
    isInList,

    /**
     * Get SSH list from input#file-upload
     */
    getSSHListFromFile() {
      const file = this.fileInput.files[0]
      const reader = new FileReader()
      const self = this

      reader.addEventListener('load', function updateSSHList(event) {
        // Store all parsed SSH in this
        const sshList = []
        for (const line of event.target.result.split('\n')) {
          try {
            const [ip, username, password] = line
                .match(new RegExp(/(\d+\.){3}\d+(\|[^|]*){2}/g))[0]
                .split('|')
            const ssh = {
              is_live: false,
              ip, username, password
            }
            // Only add more if it's not added
            if (!self.isInList(ssh, sshList)) {
              sshList.push(ssh)
            }
          } catch (e) {
            // Ignore parsing errors
          }
        }
        self.updateSSH(sshList)
      })

      reader.readAsText(file)
    },

    /**
     * Download SSH list to a text file
     */
    downloadSSHList() {
      const data = new Blob([this.sshText], {
        type: 'text/plain;charset=utf-8'
      })
      saveAs(data, `${this.listName}.txt`)
    },

    /**
     * Update SSH list to backend
     */
    async updateSSH(sshList) {
      const added = sshList.filter(ssh => !this.isInList(ssh, this.sshList))
      const removed = this.sshList.filter(ssh => !this.isInList(ssh, sshList))

      this.$emit('delete-ssh', removed)
      this.$emit('add-ssh', added)
    }
  },
  mounted() {
    this.fileInput = document.getElementById(`${this.listName}-upload`)
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

  .ssh {
    &.live td:first-child {
      color: green
    }

    &.die td:first-child {
      color: red
    }
  }
}
</style>
