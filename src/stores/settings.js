import {defineStore} from 'pinia'
import _ from "lodash";

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        settings: {},
        settingNames: {},
        originalSettings: "{}"
    }),
    getters: {
        isChanged(state) {
            return !_.isEqual(JSON.parse(state.originalSettings), state.settings)
        },
        getReadableName(state) {
            return name => state.settingNames[name]
        }
    },
    actions: {
        async loadSettings() {
            this.settings = await (await fetch('/api/settings')).json()
            this.originalSettings = JSON.stringify(this.settings)
            this.settingNames = await (await fetch('/api/settings/names')).json()
        },

        async revertSettings() {
            this.settings = JSON.parse(this.originalSettings)
        },

        async updateSettings() {
            await fetch('/api/settings', {
                method: 'post',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(this.settings)
            })
            await this.loadSettings()
        },

        async resetSettings() {
            await fetch('/api/settings', {method: 'delete'})
            await this.loadSettings()
        }
    }
})