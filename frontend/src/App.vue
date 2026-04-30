<template>
  <div id="app">
    <div class="container">
      <header class="header">
        <h1>🔧 AWS资源智能分析系统</h1>
        <p>通过自然语言查询，自动分析AWS资源问题并提供解决方案</p>
      </header>
      
      <nav class="navigation">
        <div 
          class="nav-item" 
          :class="{ active: currentRoute === '/' }"
          @click="navigateTo('/')"
        >
          🤖 智能分析
        </div>
        <div 
          class="nav-item" 
          :class="{ active: currentRoute === '/resources' }"
          @click="navigateTo('/resources')"
        >
          📊 资源列表
        </div>
      </nav>
      
      <router-view />
    </div>
  </div>
</template>

<script>
export default {
  name: 'App',
  computed: {
    currentRoute() {
      return this.$route.path
    }
  },
  methods: {
    navigateTo(path) {
      this.$router.push(path)
    }
  }
}
</script>
