<template>
  <div class="title">
    <h2>
      <slot name="title"></slot>
    </h2>
    <slot></slot>
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
  align-items: stretch;
  justify-content: space-between;
  height: 2.5rem;
  margin-bottom: 1rem;

  h2 {
    margin-bottom: 0;
  }

  button {
    width: auto;
    height: 100%;
    padding: 0.5rem 0.75rem;
    box-sizing: border-box;
  }
}
</style>