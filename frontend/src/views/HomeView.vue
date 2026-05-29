<template>
  <div class="home">
    <div class="hero">
      <h1>AI数字人视频生成系统</h1>
      <p>V1.3 — 模板化数字人口播工具</p>
    </div>

    <!-- 一键生成区 -->
    <div class="quick-generate" v-if="hasAssets">
      <h2>一键生成视频</h2>
      <div class="quick-form">
        <select v-model.number="quickTemplateId">
          <option :value="0">请选择模板</option>
          <option v-for="t in templates" :key="t.id" :value="t.id">
            {{ t.is_default ? '📌 ' : '' }}{{ t.name }}
          </option>
        </select>
        <textarea v-model="quickScript" placeholder="输入视频文案..." rows="4"></textarea>
        <select v-model="quickVoice">
          <option v-for="v in voices" :key="v.name" :value="v.name">{{ v.name }}</option>
        </select>
        <button class="btn-generate" @click="startQuickGenerate"
          :disabled="!quickTemplateId || !quickScript || generating">
          {{ generating ? '生成中...' : '🚀 开始生成' }}
        </button>
      </div>
      <!-- Quick progress -->
      <div class="quick-progress" v-if="generating || quickProject">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: (quickProject?.progress || 0) + '%' }"></div>
        </div>
        <p class="quick-status">{{ quickStatusText }}</p>
        <div v-if="quickProject?.status === 'completed' && quickProject?.output_path" class="quick-result">
          <video :src="'file://' + quickProject.output_path" controls></video>
          <div class="quick-actions">
            <button @click="openDir(quickProject.output_path)">📁 打开目录</button>
            <button @click="playResult(quickProject)">▶ 查看成片</button>
          </div>
        </div>
        <div v-if="quickProject?.status === 'failed'" class="quick-error">
          生成失败：{{ quickProject.error || '未知错误' }}
        </div>
      </div>
    </div>

    <!-- 无素材提示 -->
    <div class="empty-tip" v-else>
      <p>⚠️ 还没有素材，请先 <router-link to="/assets">导入素材</router-link></p>
    </div>

    <!-- 新手引导 -->
    <div class="guide-section" v-if="showGuide">
      <h3>🚀 快速上手</h3>
      <div class="guide-cards">
        <div class="guide-card" @click="$router.push('/assets')">
          <div class="guide-icon">📁</div>
          <div class="guide-text">
            <h4>Step 1 — 导入素材</h4>
            <p>上传你的角色视频或角色图片</p>
          </div>
          <div class="guide-arrow">→</div>
        </div>
        <div class="guide-card" @click="$router.push('/generate')">
          <div class="guide-icon">🖼️</div>
          <div class="guide-text">
            <h4>Step 2 — 图片角色模式</h4>
            <p>上传一张照片作为数字人，支持文案+语音驱动</p>
          </div>
          <div class="guide-arrow">→</div>
        </div>
        <div class="guide-card" @click="$router.push('/generate')">
          <div class="guide-icon">🎬</div>
          <div class="guide-text">
            <h4>Step 3 — 视频角色模式</h4>
            <p>用真实视频作为数字人口播，导入背景+文案即可</p>
          </div>
          <div class="guide-arrow">→</div>
        </div>
        <div class="guide-card" @click="$router.push('/templates')">
          <div class="guide-icon">📋</div>
          <div class="guide-text">
            <h4>Step 4 — 保存模板</h4>
            <p>配置好后保存为模板，下次一键生成</p>
          </div>
          <div class="guide-arrow">→</div>
        </div>
      </div>
    </div>

    <div class="menu-grid">
      <div class="menu-card primary" @click="$router.push('/generate')">
        <div class="icon">+</div>
        <h3>新建视频</h3>
        <p>完整配置生成</p>
      </div>
      <div class="menu-card" @click="$router.push('/assets')">
        <div class="icon">📁</div>
        <h3>素材库</h3>
        <p>{{ assetCount }} 个素材</p>
      </div>
      <div class="menu-card" @click="$router.push('/templates')">
        <div class="icon">📋</div>
        <h3>模板管理</h3>
        <p>{{ templateCount }} 个模板</p>
      </div>
      <div class="menu-card" @click="$router.push('/generate?history=1')">
        <div class="icon">📜</div>
        <h3>历史项目</h3>
        <p>{{ projectCount }} 个项目</p>
      </div>
    </div>

    <!-- 最近项目 -->
    <div class="recent-section" v-if="recentProjects.length > 0">
      <h3>最近项目</h3>
      <div class="recent-list">
        <div v-for="p in recentProjects" :key="p.id" class="recent-item" @click="openProject(p)">
          <div class="recent-info">
            <span class="recent-name">{{ p.name }}</span>
            <span class="recent-date">{{ formatDate(p.created_at) }}</span>
          </div>
          <span class="recent-status" :class="p.status">{{ getStatusLabel(p.status) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { getProjects, getProjectStatus, Project, runPipeline, copyProject } from '@/api/render';
import { getAssets } from '@/api/assets';
import { getTemplates, TTSVoice, Template } from '@/api/templates';
import { getVoices } from '@/api/tts';

const router = useRouter();

const quickTemplateId = ref(0);
const quickScript = ref('');
const quickVoice = ref('zh-CN-XiaoxiaoNeural');
const templates = ref<Template[]>([]);
const voices = ref<TTSVoice[]>([]);
const generating = ref(false);
const quickProject = ref<Project | null>(null);
const quickPollInterval = ref<number | null>(null);
const recentProjects = ref<Project[]>([]);
const assetCount = ref(0);
const templateCount = ref(0);
const projectCount = ref(0);

const hasAssets = computed(() => assetCount.value > 0);
const showGuide = computed(() => templateCount.value === 0 && projectCount.value === 0);

const quickStatusText = computed(() => {
  const p = quickProject.value;
  if (!p) return '';
  if (p.status === 'completed') return '✅ 生成完成！';
  if (p.status === 'failed') return '❌ 生成失败';
  return `⏳ 处理中... ${p.progress || 0}%`;
});

function formatDate(s: string) { return new Date(s).toLocaleString('zh-CN'); }
function getStatusLabel(s: string) {
  return { draft:'草稿', pending:'等待中', processing:'处理中', completed:'已完成', failed:'失败' }[s] || s;
}

async function loadAll() {
  try {
    const [tdata, adata, pdata] = await Promise.all([
      getTemplates(),
      getAssets({ pageSize: 1 }),
      getProjects(),
    ]);
    templates.value = tdata.templates || [];
    assetCount.value = adata.count || 0;
    templateCount.value = tdata.count || 0;
    projectCount.value = pdata.length;
    recentProjects.value = pdata.slice(0, 5);

    try {
      voices.value = await getVoices();
    } catch {
      voices.value = [
        { name: 'zh-CN-XiaoxiaoNeural', locale: 'zh-CN', gender: 'Female' },
        { name: 'zh-CN-YunxiNeural', locale: 'zh-CN', gender: 'Male' },
        { name: 'zh-CN-XiaoyiNeural', locale: 'zh-CN', gender: 'Female' },
        { name: 'zh-CN-YunyangNeural', locale: 'zh-CN', gender: 'Male' },
      ];
    }
  } catch (e) { console.error('Load failed:', e); }
}

async function startQuickGenerate() {
  if (!quickTemplateId.value || !quickScript.value) return;
  generating.value = true;
  quickProject.value = null;

  try {
    const res = await runPipeline({
      templateId: quickTemplateId.value,
      script: quickScript.value,
      voice: quickVoice.value,
    });
    quickProject.value = { id: res.project_id, name: '', status: 'pending', script_text: '', voice: '', created_at: '' } as any;
    startQuickPoll(res.project_id);
  } catch (err: any) {
    alert(err?.response?.data?.detail || err?.message || '启动失败');
    generating.value = false;
  }
}

function startQuickPoll(projectId: number) {
  quickPollInterval.value = window.setInterval(async () => {
    try {
      const p = await getProjectStatus(projectId);
      quickProject.value = p;
      if (p.status === 'completed' || p.status === 'failed') {
        stopQuickPoll();
        generating.value = false;
      }
    } catch { stopQuickPoll(); generating.value = false; }
  }, 2000);
}

function stopQuickPoll() {
  if (quickPollInterval.value) { clearInterval(quickPollInterval.value); quickPollInterval.value = null; }
}

function openDir(path: string) {
  if (path && (window as any).electronAPI) (window as any).electronAPI.openPath(path);
}

function playResult(p: Project) {
  router.push('/generate?project=' + p.id);
}

function openProject(p: Project) {
  router.push('/generate?project=' + p.id);
}

onMounted(loadAll);
onUnmounted(stopQuickPoll);
</script>

<style scoped>
.home { padding: 40px; max-width: 900px; margin: 0 auto; }
.hero { text-align: center; margin-bottom: 40px; }
.hero h1 { font-size: 42px; color: #1a1a2e; margin-bottom: 8px; }
.hero p { font-size: 16px; color: #888; }

.quick-generate { background: white; border-radius: 16px; padding: 32px; margin-bottom: 32px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
.quick-generate h2 { font-size: 20px; color: #333; margin-bottom: 20px; border-left: 4px solid #667eea; padding-left: 12px; }
.quick-form { display: flex; flex-direction: column; gap: 12px; }
.quick-form select, .quick-form textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; font-family: inherit; }
.quick-form textarea { resize: vertical; }
.btn-generate { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; font-size: 18px; cursor: pointer; }
.btn-generate:disabled { opacity: 0.5; cursor: not-allowed; }

.quick-progress { margin-top: 20px; }
.progress-bar { height: 8px; background: #eee; border-radius: 4px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); transition: width 0.3s; }
.quick-status { text-align: center; margin: 10px 0; font-size: 14px; color: #666; }
.quick-result video { width: 100%; max-height: 300px; border-radius: 8px; margin-top: 12px; }
.quick-actions { display: flex; gap: 12px; margin-top: 10px; }
.quick-actions button { padding: 8px 20px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-size: 13px; }
.quick-error { color: #e74c3c; text-align: center; padding: 10px; background: #fdf2f2; border-radius: 6px; margin-top: 10px; font-size: 13px; }

.empty-tip { text-align: center; padding: 20px; background: #fff3cd; border-radius: 8px; margin-bottom: 32px; color: #856404; font-size: 15px; }
.empty-tip a { color: #667eea; text-decoration: none; }

.guide-section { background: white; border-radius: 16px; padding: 28px; margin-bottom: 32px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.guide-section h3 { font-size: 18px; color: #333; margin-bottom: 20px; border-left: 4px solid #667eea; padding-left: 10px; }
.guide-cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.guide-card { display: flex; align-items: center; gap: 14px; padding: 16px; background: #f8f9ff; border-radius: 10px; cursor: pointer; transition: background 0.2s, transform 0.15s; }
.guide-card:hover { background: #eef0ff; transform: translateX(2px); }
.guide-icon { font-size: 28px; flex-shrink: 0; }
.guide-text h4 { font-size: 14px; color: #333; margin-bottom: 4px; }
.guide-text p { font-size: 12px; color: #888; margin: 0; }
.guide-arrow { margin-left: auto; font-size: 18px; color: #667eea; }

.menu-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 40px; }
.menu-card { background: white; border-radius: 16px; padding: 32px 20px; text-align: center; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.menu-card:hover { transform: translateY(-4px); box-shadow: 0 8px 20px rgba(0,0,0,0.12); }
.menu-card.primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
.menu-card .icon { font-size: 40px; margin-bottom: 12px; }
.menu-card h3 { font-size: 16px; margin-bottom: 6px; }
.menu-card p { font-size: 12px; opacity: 0.7; }

.recent-section { background: white; border-radius: 16px; padding: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.recent-section h3 { font-size: 16px; color: #333; margin-bottom: 16px; }
.recent-list { display: flex; flex-direction: column; gap: 8px; }
.recent-item { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #f8f9fa; border-radius: 8px; cursor: pointer; transition: background 0.2s; }
.recent-item:hover { background: #e9ecef; }
.recent-info { display: flex; gap: 12px; align-items: center; }
.recent-name { font-size: 14px; color: #333; }
.recent-date { font-size: 12px; color: #888; }
.recent-status { font-size: 12px; padding: 2px 10px; border-radius: 4px; }
.recent-status.completed { background: #d4edda; color: #155724; }
.recent-status.processing { background: #cce5ff; color: #004085; }
.recent-status.failed { background: #f8d7da; color: #721c24; }
.recent-status.pending, .recent-status.draft { background: #f8f9fa; color: #666; }
</style>