<template>
  <article>
    <ArticleTitle title="SSHStore">
      <div>
        <button
            @click="settingsStore.revertSettings()"
            :disabled="!settingsStore.isChanged"
            data-tippy-content="Huỷ bỏ thay đổi"
            class="secondary"><i class="fi fi-ban"></i></button>
        <button
            @click="settingsStore.updateSettings()"
            :disabled="!settingsStore.isChanged"
            data-tippy-content="Cập nhật"><i class="fi fi-check"></i></button>
      </div>
    </ArticleTitle>

    <div class="sshstore">
      <div class="form-line">
        <label for="sshstore-enabled">Kích hoạt</label>
        <div>
          <input v-model="settings.sshstore_enabled" type="checkbox" id="sshstore-enabled">
        </div>
      </div>
      <div class="form-line">
        <label for="sshstore-api_key">API key</label>
        <input v-model="settings.sshstore_api_key" :disabled="!settings.sshstore_enabled" type="text"
               id="sshstore-api_key">
      </div>
      <div class="form-line">
        <label for="sshstore-country">Quốc gia</label>
        <select v-model="settings.sshstore_country" :disabled="!settings.sshstore_enabled" id="sshstore-country">
          <option :value="country" v-for="country in allowedCountries" :key="country">{{ country }}</option>
        </select>
      </div>
    </div>
  </article>
</template>

<script>
import ArticleTitle from "@/components/ArticleTitle";
import {useSettingsStore} from "@/stores/settings";
import {storeToRefs} from "pinia";

export default {
  name: "SSHStore",
  components: {
    ArticleTitle
  },
  data: () => {
    const settingsStore = useSettingsStore()
    const {settings} = storeToRefs(settingsStore)

    return {
      settingsStore,
      settings,
      allowedCountries: ['All', 'AU', 'BR', 'CA', 'CN', 'DE', 'DZ', 'EG', 'ES', 'FR', 'GB', 'HK', 'ID', 'IN', 'JP', 'KR', 'MX', 'MY', 'PK', 'RU', 'SE', 'SG', 'TH', 'TR', 'TW', 'UAE', 'UK', 'US', 'VE', 'VN']
    }
  }
}
</script>

<style lang="scss" scoped>
article {
  display: flex;
  flex-direction: column;

  .sshstore {
    --form-element-spacing-horizontal: 0.5rem;
    --form-element-spacing-vertical: 0.25rem;

    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    overflow: auto;

    .form-line {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;

      label {
        white-space: nowrap;
      }

      & > input:not(input[type=checkbox]), & > div, & > select {
        width: 100%;
        max-width: 50%;
      }
    }
  }
}
</style>