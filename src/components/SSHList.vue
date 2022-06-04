<!--suppress JSUnresolvedVariable -->
<template>
  <article>
    <ArticleTitle :title="title">
      <div>
        <button
            v-if="!readOnly"
            v-on:click="$refs.fileInput.click()"
            data-tippy-content="Tải lên"><i class="fi fi-upload"></i></button>
        <button
            @click="downloadSSHList"
            data-tippy-content="Tải xuống"><i class="fi fi-download"></i></button>
      </div>
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
            :class="[ssh.status_text, isRecent(ssh) ? 'recent' : '']"
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
          @change="uploadSSHFile($event.target.files[0])"
          type="file"
          accept="text/plain, text/csv"
          style="display: none">
    </div>

    <div class="footer">
      <small v-if="!readOnly">{{ checkSpeed }} <sub>SSH/phút</sub></small>
      <div>
        <label>Hiển thị</label>
        <select v-model="displayLimit" style="width: 6rem">
          <option :value="200" selected>200</option>
          <option :value="500">500</option>
          <option :value="1000">1000</option>
          <option :value="2000">2000</option>
          <option :value="Infinity">Tất cả</option>
        </select>
      </div>
    </div>
  </article>
</template>

<!--suppress JSUnusedGlobalSymbols -->
<script>
import ArticleTitle from "@/components/ArticleTitle";
import {saveAs} from "file-saver";
import {getSshText, getTimeDisplay, isRecent} from "@/utils";
import moment from "moment";
import _ from "lodash";

export default {
  name: 'SSHList',
  components: {
    ArticleTitle
  },
  data() {
    return {
      displayLimit: 200,
      checkSpeed: 0
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
    isRecent,

    /**
     * Get SSH list from input#file-upload
     * @param file
     * @returns {Promise<void>}
     */
    async uploadSSHFile(file) {
      const form = new FormData()
      form.append('ssh_file', file)
      await fetch('/api/ssh/upload', {
        method: 'post',
        body: form
      })
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
     * Update SSH checking speed
     */
    updateCheckSpeed() {
      const totalMinutes = 10

      const sshList = this.sshList
          .filter(s => (
              !s.is_checking &&
              moment().diff(moment(s.last_checked || ''), 'seconds') <= totalMinutes * 60
          ))
      const oldest = _.minBy(sshList, s => s.last_checked)
      const oldestTime = oldest ? oldest.last_checked : ''
      const totalTime = moment().diff(moment(oldestTime), 'seconds') / 60
      this.checkSpeed = _.round(sshList.length / totalTime, 1)
    }
  },
  mounted() {
    if (this.readOnly) {
      return
    }

    setInterval(this.updateCheckSpeed)
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style lang="scss" scoped>
article {
  display: flex;
  flex-direction: column;

  .list-content {
    flex-grow: 1;
    min-height: 0;
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
      transition: background-color 1s ease;

      &.live td:first-child {
        color: green
      }

      &.die td:first-child {
        color: red
      }

      &.recent {
        background-color: rgba(3, 206, 3, 0.27);
      }
    }
  }

  .footer {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-top: 1rem;
    margin-left: auto;

    & > div {
      display: flex;
      align-items: center;
      gap: 0.25rem;
    }
  }
}
</style>
