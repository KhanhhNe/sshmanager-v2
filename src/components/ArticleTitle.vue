<template ref="title">
  <div class="title">
    <h2>{{ title }}</h2>
    <div>
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: "ArticleTitle.vue",
  props: {
    title: String
  }
}
</script>

<style lang="scss" scoped>
.title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  white-space: nowrap;

  & > div {
    display: flex;
    align-items: center;
    gap: 0.75rem;

    & > :deep(div) {
      display: flex;
      gap: 0.2rem;
      align-items: center;
    }
  }
}
</style>