<template>
  <div v-show="isActive">
    <slot></slot>
  </div>
</template>

<script>
export default {
  name: "Tab",
  props: {
    title: String
  },
  data() {
    return {
        isActive: false
    }
  }
}
</script>

<style scoped>

</style>