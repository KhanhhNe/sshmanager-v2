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
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: "Tabs",
  data() {
    return {
      currentTab: undefined,
      tabs: []
    }
  },
  methods: {
    /**
     * Deselect the current active tab and select a new one
     * @param tab
     */
    selectTab(tab) {
      this.tabs.forEach(tab => tab.$el.classList.add('hidden'))
      this.currentTab = tab || this.currentTab
      if (this.currentTab) {
        this.currentTab.$el.classList.remove('hidden')
      }
    }
  },
  mounted() {
    // Get tabs from children and select the first one
    this.tabs = this.$children
    this.selectTab(this.tabs[0])
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
}

.hidden {
  display: none;
}
</style>