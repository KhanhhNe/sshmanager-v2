<template>
  <article v-show="!hidden">
    <ArticleTitle>
      <template v-slot:title>{{ title }}</template>
      <button
          @click="$refs.fileInput.click()"
          data-tippy-content="Thêm plugins"><i class="fi fi-plus-a"></i>
      </button>
    </ArticleTitle>
    <div class="content">
      <div
          v-for="plugin in plugins"
          :key="plugin.name"
          class="plugin">
        <div class="plugin-title">
          <h6 style="margin-bottom: 0">{{ plugin.name }}</h6>
          <button
              @click="deletePlugin(plugin)"
              class="secondary outline"><i class="fi fi-trash"></i>
          </button>
        </div>
        <div :ref="plugin.name"></div>
      </div>
      <input
          ref="fileInput"
          @change="addPlugin($event.target.files[0])"
          type="file"
          accept="text/javascript"
          style="display: none">
    </div>
  </article>
</template>

<script>
import ArticleTitle from "@/components/ArticleTitle";

export default {
  name: "Plugins",
  components: {
    ArticleTitle
  },
  props: {
    title: String,
  },
  data() {
    return {
      hidden: false,
      plugins: [],
      ranPlugins: []
    }
  },
  methods: {
    /**
     * Add a new plugin (send request to server)
     * @param file
     */
    addPlugin(file) {
      const reader = new FileReader()
      const self = this

      reader.addEventListener('load', async function uploadPlugin(event) {
        await fetch('/api/plugins/', {
          method: 'post',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            name: file.name,
            code: event.target.result
          })
        })
        await self.getPlugins()
      })

      reader.readAsText(file)
    },

    /**
     * Delete a plugin (send request to server)
     * @param plugin
     * @returns {Promise<void>}
     */
    async deletePlugin(plugin) {
      if (!confirm(`Bạn có chắc muốn xoá plugin ${plugin.name} không?`)) return

      await fetch(`/api/plugins/?plugin_name=${plugin.name}`, {
        method: 'delete'
      })
      this.plugins = this.plugins.filter(p => p !== plugin)
    },

    /**
     * Run a plugin and show its output
     * @param plugin
     */
    runPlugin(plugin) {
      const output = eval(plugin.code)
      this.$refs[plugin.name][0].append(output)
    },

    /**
     * Get plugins from server
     * @returns {Promise<void>}
     */
    async getPlugins() {
      this.plugins = await (await fetch('/api/plugins/')).json()
    }
  },
  mounted() {
    this.getPlugins()
  },
  watch: {
    plugins(plugins) {
      for (const plugin of plugins) {
        if (!this.ranPlugins.includes(plugin)) {
          setTimeout(() => this.runPlugin(plugin), 1000)
          this.ranPlugins.push(plugin)
        }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.plugin {
  padding: 1rem 0;
  border-top: 1px solid lightgrey;

  .plugin-title {
    display: flex;
    justify-content: space-between;
    margin-right: 0.25rem;

    button {
      width: auto;
      padding: 0.5rem 0.75rem;
    }
  }
}
</style>