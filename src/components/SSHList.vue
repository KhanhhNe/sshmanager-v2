<!--suppress JSUnresolvedVariable -->
<template>
  <article v-show="!hidden">
    <ArticleTitle>
      <template v-slot:title>{{ listName }}</template>
      <button @click="toggleDisplayMode">
        <span>Chế độ </span>
        <span v-show="displayMode === 'table'">Bảng</span>
        <span v-show="displayMode === 'text'">Chữ</span>
      </button>
    </ArticleTitle>
    <div class="list-content">
      <table v-show="displayMode === 'table'">
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
      <!--suppress HtmlUnknownAttribute -->
      <textarea :value="sshText"
                @change="sshText = $event.target.value"
                :readonly="readOnly"
                v-show="displayMode === 'text'"
      ></textarea>
    </div>
  </article>
</template>

<!--suppress JSUnusedGlobalSymbols -->
<script>
import ArticleTitle from "@/components/ArticleTitle";
import {getSshText, getTimeDisplay, isInList, isSameSSH} from "@/utils";

export default {
  name: 'SSHList',
  components: {
    ArticleTitle
  },
  data() {
    return {
      displayMode: 'table',
      hidden: false
    }
  },
  props: {
    sshList: Array,
    listName: String,
    readOnly: Boolean
  },
  computed: {
    sshText: {
      get() {
        return this.sshList.map(this.getSshText).join('\n')
      },

      /**
       * Parse SSH text into valid SSH list, ignoring malformed data.
       * @param text SSH text
       */
      set(text) {
        // Don't do parsing with read only SSHList (live/die list)
        if (this.readOnly) {
          return
        }

        // Store all parsed SSH in this
        const sshList = []
        for (const line of text.split('\n')) {
          try {
            const [ip, username, password] = line
                .match(new RegExp(/(\d+\.){3}\d+(\|[^|]*){2}/g))[0]
                .split('|')
            const ssh = {
              is_live: false,
              ip,
              username,
              password
            }
            let already = sshList.filter(s => this.isSameSSH(s, ssh))

            // Only add more if it's not added
            if (!already.length) {
              sshList.push(ssh)
            }
          } catch (e) {
            // Ignore parsing errors
          }
        }
        this.updateSSH(sshList)
      }
    }
  },
  methods: {
    getTimeDisplay,
    getSshText,
    isSameSSH,
    isInList,

    /**
     * Toggle component's display mode between table and text mode
     */
    toggleDisplayMode() {
      if (this.displayMode === 'table') {
        this.displayMode = 'text'
      } else {
        this.displayMode = 'table'
      }
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
