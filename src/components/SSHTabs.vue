<template>
  <div class="tabs-wrapper">
    <ul>
      <li v-for="tab in tabs" :key="tab.listName">
        <button @click="selectTab(tab)">{{ tab.listName }}</button>
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
      this.tabs.map(tab => tab.hidden = true)
      this.currentTab = tab || this.currentTab
      if (this.currentTab) {
        this.currentTab.hidden = false
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
  display: flex;
  flex-direction: column;
  gap: 1rem;

  ul {
    display: flex;
    gap: 1rem;
    padding: 0;
    margin: 0;

    li {
      flex-grow: 1;
      list-style-type: none;

      button {
        margin: 0;
      }
    }
  }
}
</style>