<template>
  <div class="tabs-wrapper">
    <ul>
      <li v-for="tab in tabs" :key="tab.title">
        <button @click="selectTab(tab)">{{ tab.title }}</button>
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
    selectTab(tab) {
      if (this.currentTab) {
        this.currentTab.isActive = false
      }
      this.currentTab = tab || this.currentTab
      if (this.currentTab) {
        this.currentTab.isActive = true
      }
    }
  },
  mounted() {
    this.tabs = this.$children
    this.selectTab(this.tabs[0])
  }
}
</script>

<style lang="scss">
.tabs-wrapper {
  ul {
    display: flex;
    gap: 1rem;
    padding: 0;

    li {
      flex-grow: 1;
      list-style-type: none;
    }
  }
}
</style>