<template>
  <article>
    <ArticleTitle>
      <template v-slot:title>Settings</template>
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
            <input v-model="setting.value" v-if="typeof setting.value === 'boolean'" type="checkbox">
            <input v-model="setting.value" v-else type="text">
          </td>
        </tr>
        </tbody>
      </table>
      <a @click="updateSettings" role="button">Cập nhật</a>
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
    settings: Object
  },
  methods: {
    updateSettings() {
      this.$emit('update-settings', this.settings)
    }
  }
}
</script>

<style lang="scss" scoped>
.content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  overflow: auto;

  input[type=text] {
    height: 2rem !important;
    padding: 0.25rem !important;
    margin: 0;
  }
}
</style>