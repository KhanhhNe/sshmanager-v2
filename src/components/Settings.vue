<template>
  <article>
    <ArticleTitle title="Settings">
      <button
          @click="settingsStore.resetSettings()"
          data-tippy-content="Đặt lại toàn bộ cài đặt"
          class="outline"><i class="fi fi-spinner-refresh"></i></button>
      <div>
        <button
            @click="settingsStore.revertSettings()"
            :disabled="!isChanged"
            data-tippy-content="Huỷ bỏ thay đổi"
            class="secondary"><i class="fi fi-ban"></i></button>
        <button
            @click="settingsStore.updateSettings()"
            :disabled="!isChanged"
            data-tippy-content="Cập nhật cài đặt"><i class="fi fi-check"></i></button>
      </div>
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
        <tr v-for="(value, name) in settings" :key="name">
          <td :data-tooltip="name">{{ settingsStore.getReadableName(name) }}</td>
          <td>
            <input
                v-model="settings[name]"
                v-if="typeof value === 'boolean'" type="checkbox">
            <input
                v-model="settings[name]"
                v-else-if="typeof value === 'number'" type="number">
            <input
                v-model="settings[name]"
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
import {storeToRefs} from "pinia";

export default {
  name: "Settings",
  components: {
    ArticleTitle
  },
  data: () => {
    const settingsStore = useSettingsStore()
    const {settings, isChanged} = storeToRefs(settingsStore)

    return {
      settingsStore,
      settings,
      isChanged
    }
  }
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