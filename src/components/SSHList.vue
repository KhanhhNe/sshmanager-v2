<template>
  <article v-show="!hidden">
    <div class="title">
      <h2>{{ listName }}</h2>
      <button @click="toggleDisplayMode">
        <span>Chế độ </span>
        <span v-show="displayMode === 'table'">Bảng</span>
        <span v-show="displayMode === 'text'">Chữ</span>
      </button>
    </div>
    <div class="list-content">
      <table v-show="displayMode === 'table'">
        <thead>
        <tr>
          <td>Trạng thái</td>
          <td>IP</td>
          <td>Username</td>
          <td>Password</td>
        </tr>
        </thead>
        <tbody>
        <tr v-for="ssh in sshList" :key="getSshText(ssh)" :class="[ssh.status]" class="ssh">
          <td>{{ ssh.status }}</td>
          <td>{{ ssh.ip }}</td>
          <td>{{ ssh.username }}</td>
          <td>{{ ssh.password }}</td>
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
export default {
  name: 'SSHList',
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
            const [status, ip, username, password] = line.split('|')
            let already = sshList.filter(ssh => {
              return ssh.ip === ip && ssh.username === username && ssh.password === password
            })

            // Only add more if it's not added
            if (!already.length) {
              sshList.push({status, ip, username, password})
            }
          } catch (e) {
            // Ignore parsing errors
          }
        }
        // Emit parsed SSH list to parent element
        this.$emit('update-ssh-list', sshList)
      }
    }
  },
  methods: {
    /**
     * Get SSH display text, in format of status|ip|username|password
     * @param ssh SSH object
     * @returns {string} SSH display text
     */
    getSshText(ssh) {
      return Object.values(ssh).join('|')
    },

    /**
     * Toggle component's display mode between table and text mode
     */
    toggleDisplayMode() {
      if (this.displayMode === 'table') {
        this.displayMode = 'text'
      } else {
        this.displayMode = 'table'
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
article {
  margin: 0;
  display: flex;
  flex-direction: column;

  .list-content {
    overflow: auto;
    flex-grow: 1;
  }

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

  .ssh {
    td:first-child {
      text-transform: capitalize;
    }

    &.live td:first-child {
      color: green
    }

    &.die td:first-child {
      color: red
    }
  }

  textarea {
    height: 100%;
    width: 100%;
    margin: 0;
    resize: none;
  }
}
</style>
