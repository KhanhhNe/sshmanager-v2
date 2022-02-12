<template>
  <article v-show="!hidden">
    <ArticleTitle>
      <template v-slot:title>{{ title }}</template>
      <div
          class="warning"
          v-if="needRestart">Khởi động lại SSHManager để cập nhật cài đặt
      </div>
      <a
          @click="$emit('reset-settings')"
          role="button"
          data-tippy-content="Đặt lại toàn bộ cài đặt"
          class="outline"><i class="fi fi-spinner-refresh"></i></a>
      <a
          @click="updateSettings"
          data-tippy-content="Cập nhật cài đặt"
          role="button"><i class="fi fi-check"></i></a>
    </ArticleTitle>
    <div class="content">
      <table>
        <thead>
        <tr>
          <th>Tên</th>
          <th>Giá trị</th>
        </tr>
        </thead>
        <tbody>
        <tr v-for="setting in settings" :key="setting.name">
          <td>{{ setting.readable_name }}</td>
          <td>
            <input
                v-model="setting.value"
                v-if="typeof setting.value === 'boolean'" type="checkbox">
            <input
                v-model="setting.value"
                v-else-if="typeof setting.value === 'number'" type="number">
            <input
                v-model="setting.value"
                v-else type="text">
          </td>
        </tr>
        </tbody>
      </table>
    </div>
  </article>
</template>

<script>
import ArticleTitle from "@/components/ArticleTitle";

export default {
  name: "Settings",
  components: {
    ArticleTitle
  },
  props: {
    title: String,
    settings: Array,
    needRestart: Boolean
  },
  data() {
    return {
      hidden: false,
    }
  },
  methods: {
    updateSettings() {
      this.$emit('update-settings', this.settings)
    }
  }
}
</script>

<style lang="scss" scoped>
.warning {
  color: red;
  font-size: 0.85rem;
}

.content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  overflow: auto;

  table {
    table-layout: auto;

    tr td:first-child {
      white-space: nowrap;
    }
  }

  input {
    height: 2rem !important;
    padding: 0.25rem !important;
    margin: 0 !important;
    width: 5rem !important;

    &[type=checkbox] {
      height: 2rem !important;
      width: 2rem !important;

      &:not(:checked):after {
        content: "?";
      }
    }
  }
}
</style>