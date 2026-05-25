<template>
  <div id="app">
    <nav class="main-nav" v-if="showNav">
      <router-link to="/" class="nav-logo">AI数字人</router-link>
      <div class="nav-links">
        <router-link to="/">首页</router-link>
        <router-link to="/assets">素材库</router-link>
        <router-link to="/templates">模板管理</router-link>
        <router-link to="/generate">视频生成</router-link>
        <router-link to="/settings">设置</router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

const showNav = computed(() => {
  return route.path !== '/';
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
}

.main-nav {
  display: flex;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 100;
}

.nav-logo {
  font-size: 20px;
  font-weight: bold;
  color: #667eea;
  text-decoration: none;
  margin-right: 48px;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-links a {
  font-size: 14px;
  color: #666;
  text-decoration: none;
  padding: 8px 0;
  border-bottom: 2px solid transparent;
  transition: all 0.3s;
}

.nav-links a:hover,
.nav-links a.router-link-active {
  color: #667eea;
  border-bottom-color: #667eea;
}

.main-content {
  min-height: calc(100vh - 60px);
}
</style>