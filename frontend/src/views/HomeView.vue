<template>
  <div class="home">
    <div class="hero">
      <h1>AI数字人视频生成系统</h1>
      <p>快速创建专业的数字人视频</p>
    </div>

    <div class="menu-grid">
      <div class="menu-card" @click="navigateTo('/generate')">
        <div class="icon">+</div>
        <h3>新建视频</h3>
        <p>创建新的数字人视频项目</p>
      </div>

      <div class="menu-card" @click="navigateTo('/assets')">
        <div class="icon">📁</div>
        <h3>素材库</h3>
        <p>管理角色视频、背景、商品等素材</p>
      </div>

      <div class="menu-card" @click="navigateTo('/templates')">
        <div class="icon">📋</div>
        <h3>模板管理</h3>
        <p>创建和编辑视频模板</p>
      </div>

      <div class="menu-card" @click="showHistory">
        <div class="icon">📜</div>
        <h3>历史项目</h3>
        <p>查看已完成的项目记录</p>
      </div>
    </div>

    <div class="quick-stats">
      <div class="stat-item">
        <span class="stat-value">{{ recentProjects.length }}</span>
        <span class="stat-label">最近项目</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ totalAssets }}</span>
        <span class="stat-label">素材数量</span>
      </div>
      <div class="stat-item">
        <span class="stat-value">{{ totalTemplates }}</span>
        <span class="stat-label">可用模板</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { getProjects } from '@/api/render';
import { getAssets } from '@/api/assets';
import { getTemplates } from '@/api/templates';

const router = useRouter();
const recentProjects = ref<any[]>([]);
const totalAssets = ref(0);
const totalTemplates = ref(0);

function navigateTo(path: string) {
  router.push(path);
}

async function showHistory() {
  router.push('/generate');
}

onMounted(async () => {
  try {
    const projects = await getProjects();
    recentProjects.value = projects.slice(0, 5);

    const assetsData = await getAssets({ pageSize: 1 });
    totalAssets.value = assetsData.total;

    const templates = await getTemplates();
    totalTemplates.value = templates.length;
  } catch (error) {
    console.error('Failed to load stats:', error);
  }
});
</script>

<style scoped>
.home {
  padding: 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.hero {
  text-align: center;
  margin-bottom: 60px;
}

.hero h1 {
  font-size: 48px;
  color: #1a1a2e;
  margin-bottom: 16px;
}

.hero p {
  font-size: 18px;
  color: #666;
}

.menu-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  margin-bottom: 60px;
}

.menu-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.3s, box-shadow 0.3s;
  color: white;
}

.menu-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px rgba(102, 126, 234, 0.4);
}

.menu-card .icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.menu-card h3 {
  font-size: 20px;
  margin-bottom: 8px;
}

.menu-card p {
  font-size: 14px;
  opacity: 0.9;
}

.quick-stats {
  display: flex;
  justify-content: center;
  gap: 60px;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 12px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  color: #667eea;
  display: block;
}

.stat-label {
  font-size: 14px;
  color: #666;
}
</style>