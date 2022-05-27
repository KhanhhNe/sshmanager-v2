import {defineStore} from 'pinia'
import _ from "lodash";

export const useSettingsStore = defineStore('settings', {
    state: () => ({
        settings: {},
        originalSettings: "{}"
    }),
    getters: {
        isChanged(state) {
            return !_.isEqual(JSON.parse(state.originalSettings), state.settings)
        }
    },
    actions: {
        async loadSettings() {
            const settingsValues = await (await fetch('/api/settings')).json()
            const settingsNames = await (await fetch('/api/settings/names')).json()
            const settings = {}
            for (const [name, value] of Object.entries(settingsValues)) {
                settings[name] = {value, readable_name: settingsNames[name]}
            }
            this.settings = settings
            this.originalSettings = JSON.stringify(settings)
        },

        async revertSettings() {
            this.settings = JSON.parse(this.originalSettings)
        },

        async updateSettings() {
            const settings = {}
            for (const [name, setting] of Object.entries(this.settings)) {
                settings[name] = setting.value
            }
            await fetch('/api/settings', {
                method: 'post',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            })
            await this.loadSettings()
        },

        async resetSettings() {
            await fetch('/api/settings', {method: 'delete'})
            await this.loadSettings()
        }
    }
})