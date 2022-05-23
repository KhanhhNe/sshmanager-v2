<template>
  <div class="tabs-wrapper">
    <ul>
      <li v-for="tab in tabs" :key="tab.title">
        <button
            @click="selectTab(tab)"
            :class="tab !== currentTab ? 'outline' : ''">{{ tab.title }}
        </button>
      </li>
    </ul>
    <div class="tabs" ref="tabs">
      <slot></slot>
    </div>
  </div>
</template>

<script>
import _ from 'lodash'

export default {
  name: 'TabsComponent',
  data() {
    return {
      tabs: [],
      currentTab: undefined
    }
  },
  methods: {
    /**
     * Deselect the current active tab and select a new one
     * @param tab
     */
    selectTab(tab) {
      this.tabs.forEach(tab => tab.classList.add('hidden'))
      this.currentTab = tab || this.currentTab
      if (this.currentTab) {
        this.currentTab.classList.remove('hidden')
      }
    }
  },
  mounted() {
    this.tabs = this.$refs.tabs.children
    this.selectTab(this.tabs[0])
    const self = this

    setInterval(function updateTitle() {
      self.tabs = _.map(self.$refs.tabs.children, tab => {
        tab.title = tab.querySelector('.title').textContent
        return tab
      })
    })
  }
}
</script>

<style lang="scss">
.tabs-wrapper {
  display: flex;
  flex-direction: column;

  ul {
    display: flex;
    padding: 0;
    margin: 0;

    li {
      flex-grow: 1;
      list-style-type: none;

      &:not(:first-child) button {
        border-top-left-radius: 0;
        border-bottom-left-radius: 0;
      }

      &:not(:last-child) button {
        border-top-right-radius: 0;
        border-bottom-right-radius: 0;
      }
    }
  }

  .tabs {
    display: flex;
    flex-direction: column;
    flex-grow: 1;
    min-height: 0;

    & > * {
      flex-grow: 1;
    }
  }
}

.hidden {
  display: none !important;
}
</style>
