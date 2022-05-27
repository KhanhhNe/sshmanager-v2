<template>
  <article>
    <ArticleTitle title="Settings">
      <button
          @click="settingsStore.resetSettings()"
          data-tippy-content="Đặt lại toàn bộ cài đặt"
          class="outline"><i class="fi fi-spinner-refresh"></i></button>
      <button
          @click="settingsStore.revertSettings()"
          :disabled="!settingsStore.isChanged"
          data-tippy-content="Huỷ bỏ thay đổi"><i class="fi fi-ban"></i></button>
      <button
          @click="settingsStore.updateSettings()"
          :disabled="!settingsStore.isChanged"
          data-tippy-content="Cập nhật cài đặt"><i class="fi fi-check"></i></button>
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
        <tr v-for="(setting, name) in settingsStore.settings" :key="name">
          <td :data-tooltip="name">{{ setting.readable_name }}</td>
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
import {useSettingsStore} from "@/stores/settings";

export default {
  name: "Settings",
  components: {
    ArticleTitle
  },
  data: () => ({
    settingsStore: useSettingsStore()
  })
}
</script>

<style lang="scss" scoped>
article {
  display: flex;
  flex-direction: column;

  .warning {
    color: red;
    font-size: 0.85rem;
  }

  .content {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    overflow: auto;

    input {
      height: 2rem !important;
      padding: 0.25rem !important;
      margin: 0 !important;
      width: 5rem !important;

      &[type=checkbox] {
        height: 2rem !important;
        width: 2rem !important;
      }
    }
  }
}
</style>