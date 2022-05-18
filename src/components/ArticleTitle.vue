<template>
  <div class="title">
    <h2>
      <slot name="title"></slot>
    </h2>
    <div>
      <slot></slot>
    </div>
  </div>
</template>

<script>
export default {
  name: "ArticleTitle.vue"
}
</script>

<style lang="scss" scoped>
.title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  white-space: nowrap;

  & > div:not(:first-child) {
    display: flex;
    align-items: center;
    gap: 0.75rem;

    & > div {
      display: flex;
      gap: 0.2rem;
      align-items: center;
    }
  }
}
</style>