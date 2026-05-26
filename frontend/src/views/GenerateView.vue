<template>
  <div class="generate-view">
    <h2>视频生成</h2>

    <!-- 模板选择区 -->
    <div class="form-section template-section">
      <h3>0. 选择模板</h3>
      <select v-model.number="selectedTemplateId" @change="onTemplateChange" class="template-select">
        <option :value="0">—— 不使用模板，自定义配置 ——</option>
        <option v-for="t in templates" :key="t.id" :value="t.id">
          {{ t.is_default ? '📌 ' : '' }}{{ t.name }}
        </option>
      </select>
      <p class="template-hint" v-if="selectedTemplateId">已加载模板配置，可在此基础上修改</p>
    </div>

    <div class="generate-form">

      <!-- 素材选择区 -->
      <div class="form-section">
        <h3>1. 选择素材</h3>

        <!-- 主视频 -->
        <div class="asset-row">
          <label>主视频：</label>
          <select v-model.number="mainVideoId" @change="onMainVideoChange">
            <option :value="0">不选</option>
            <option v-for="v in mainVideos" :key="v.id" :value="v.id">
              {{ v.name }} {{ v.width ? `(${v.width}×${v.height})` : '' }} {{ v.duration ? formatDur(v.duration) : '' }}
            </option>
          </select>
          <span v-if="mainVideoId && selectedMainVideo" class="asset-spec">
            {{ selectedMainVideo.width }}×{{ selectedMainVideo.height }} · {{ formatDur(selectedMainVideo.duration) }} · {{ selectedMainVideo.codec || '' }}
          </span>
        </div>

        <!-- 背景 -->
        <div class="asset-row">
          <label>背景：</label>
          <select v-model.number="backgroundId">
            <option :value="0">黑色背景</option>
            <option v-for="b in backgrounds" :key="b.id" :value="b.id">
              {{ b.name }} {{ b.width ? `(${b.width}×${b.height})` : '' }}
            </option>
          </select>
        </div>

        <!-- 商品图 -->
        <div class="asset-row">
          <label>商品图：</label>
          <select v-model.number="productId">
            <option :value="0">不显示</option>
            <option v-for="p in products" :key="p.id" :value="p.id">
              {{ p.name }}
            </option>
          </select>
          <span v-if="productId" class="product-controls">
            <select v-model="productPosition">
              <option value="bottom-right">右下角</option>
              <option value="bottom-left">左下角</option>
              <option value="top-right">右上角</option>
              <option value="top-left">左上角</option>
            </select>
            <select v-model.number="productScale">
              <option :value="0.15">小 15%</option>
              <option :value="0.25">中 25%</option>
              <option :value="0.35">大 35%</option>
              <option :value="0.50">超大 50%</option>
            </select>
          </span>
        </div>

        <!-- BGM -->
        <div class="asset-row">
          <label>BGM：</label>
          <select v-model.number="bgmId">
            <option :value="0">不添加</option>
            <option v-for="m in bgms" :key="m.id" :value="m.id">
              {{ m.name }} {{ m.duration ? formatDur(m.duration) : '' }}
            </option>
          </select>
          <span v-if="bgmId" class="bgm-vol">
            <label>BGM音量：</label>
            <input type="range" v-model.number="bgmVolume" min="0" max="1" step="0.05" style="width:80px" />
            {{ Math.round(bgmVolume * 100) }}%
          </span>
        </div>

      </div>

      <!-- 文案 + 音色 -->
      <div class="form-section">
        <h3>2. 文案与音色</h3>
        <textarea v-model="script" placeholder="请输入要生成的视频文案..." rows="5"></textarea>
        <select v-model="selectedVoice" class="voice-select">
          <option v-for="v in voices" :key="v.name" :value="v.name">
            {{ v.name }} ({{ v.locale }})
          </option>
        </select>
      </div>

      <!-- 布局设置 -->
      <div class="form-section">
        <h3>3. 布局设置</h3>
        <div class="layout-grid">
          <!-- 主视频布局 -->
          <div class="layout-group">
            <h4>主视频</h4>
            <div class="layout-row">
              <label>缩放：</label>
              <input type="range" v-model.number="mainVideoScale" min="0.1" max="1.0" step="0.05" />
              <span class="layout-val">{{ Math.round(mainVideoScale * 100) }}%</span>
            </div>
            <div class="layout-row">
              <label>X偏移：</label>
              <input type="number" v-model.number="mainVideoX" min="-500" max="500" step="10" />
              <span class="layout-hint">像素</span>
            </div>
            <div class="layout-row">
              <label>Y偏移：</label>
              <input type="number" v-model.number="mainVideoY" min="-500" max="500" step="10" />
              <span class="layout-hint">像素</span>
            </div>
          </div>
          <!-- 输出分辨率 -->
          <div class="layout-group">
            <h4>输出分辨率</h4>
            <div class="resolution-presets">
              <button v-for="r in resolutionPresets" :key="r.label"
                :class="{ active: outputWidth === r.w && outputHeight === r.h }"
                @click="setResolution(r.w, r.h)">
                {{ r.label }}
              </button>
            </div>
            <div class="layout-row" style="margin-top:8px">
              <label>宽：</label>
              <input type="number" v-model.number="outputWidth" min="360" max="4096" step="2" />
            </div>
            <div class="layout-row">
              <label>高：</label>
              <input type="number" v-model.number="outputHeight" min="360" max="4096" step="2" />
            </div>
          </div>
        </div>
      </div>

      <!-- 字幕样式 -->
      <div class="form-section">
        <h3>4. 字幕样式</h3>
        <div class="subtitle-controls">
          <div class="ctrl-item">
            <label>字号：</label>
            <select v-model.number="subtitleFontSize">
              <option value="36">小 36</option>
              <option value="48">中 48</option>
              <option value="64">大 64</option>
              <option value="80">超大 80</option>
            </select>
          </div>
          <div class="ctrl-item">
            <label>位置：</label>
            <select v-model="subtitlePosition">
              <option value="top">顶部</option>
              <option value="middle">中部</option>
              <option value="bottom">底部</option>
            </select>
          </div>
          <div class="ctrl-item">
            <label>描边：</label>
            <select v-model.number="subtitleStroke">
              <option value="1">细</option>
              <option value="2">中</option>
              <option value="4">粗</option>
            </select>
          </div>
        </div>
      </div>

      <button class="btn-generate" @click="startGenerate"
        :disabled="!script || generating || (!mainVideoId && !backgroundId)">
        {{ generating ? '生成中...' : '🚀 开始生成' }}
      </button>
    </div>

    <!-- 进度 -->
    <div class="progress-section" v-if="generating || projectStatus">
      <h3>生成进度</h3>
      <ProgressBar :progress="progress" :status="projectStatus" />
      <p class="status-text">{{ statusText }}</p>
      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
    </div>

    <!-- 结果 -->
    <div class="result-section" v-if="completed && outputPath">
      <h3>生成完成</h3>
      <div class="video-player">
        <video :src="videoUrl" controls autoplay></video>
      </div>
      <div class="result-actions">
        <button class="btn-primary" @click="openDirectory">📁 打开目录</button>
        <button class="btn-secondary" @click="downloadVideo">⬇ 下载视频</button>
      </div>
    </div>

    <!-- 历史 -->
    <div class="history-section">
      <h3>历史项目</h3>
      <div class="history-list" v-if="projects.length > 0">
        <div v-for="p in projects" :key="p.id" class="history-item" @click="loadProject(p)">
          <div class="project-info">
            <span class="project-name">{{ p.name }}</span>
            <span class="project-status" :class="p.status">{{ getStatusLabel(p.status) }}</span>
          </div>
          <span class="project-date">{{ formatDate(p.created_at) }}</span>
        </div>
      </div>
      <div class="empty-history" v-else><p>暂无历史项目</p></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute } from 'vue-router';
import { getAssets, Asset } from '@/api/assets';
import { getVoices, TTSVoice } from '@/api/tts';
import { getTemplates, Template } from '@/api/templates';
import { getProjects, runPipeline, getProjectStatus, getProject, Project } from '@/api/render';
import ProgressBar from '@/components/ProgressBar.vue';

const route = useRoute();

const mainVideos = ref<Asset[]>([]);
const backgrounds = ref<Asset[]>([]);
const products = ref<Asset[]>([]);
const bgms = ref<Asset[]>([]);
const voices = ref<TTSVoice[]>([]);
const templates = ref<Template[]>([]);
const projects = ref<Project[]>([]);

// Template selection
const selectedTemplateId = ref(0);

// Form state
const mainVideoId = ref(0);
const backgroundId = ref(0);
const productId = ref(0);
const bgmId = ref(0);
const script = ref('');
const selectedVoice = ref('zh-CN-XiaoxiaoNeural');
// Subtitle
const subtitleFontSize = ref(48);
const subtitlePosition = ref('bottom');
const subtitleStroke = ref(2);
// Product
const productPosition = ref('bottom-right');
const productScale = ref(0.25);
// BGM
const bgmVolume = ref(0.15);
// Layout
const mainVideoScale = ref(0.4);
const mainVideoX = ref(30);
const mainVideoY = ref(10);
// Output
const outputWidth = ref(1080);
const outputHeight = ref(1920);

const resolutionPresets = [
  { label: '9:16竖屏', w: 1080, h: 1920 },
  { label: '16:9横屏', w: 1920, h: 1080 },
  { label: '1:1方屏', w: 1080, h: 1080 },
];

// Generation state
const generating = ref(false);
const currentProjectId = ref(0);
const progress = ref(0);
const projectStatus = ref<'pending'|'processing'|'completed'|'failed'>('pending');
const stepText = ref('');
const outputPath = ref('');
const errorMessage = ref('');
const pollInterval = ref<number | null>(null);

const selectedMainVideo = computed(() => mainVideos.value.find(v => v.id === mainVideoId.value));
const videoUrl = computed(() => outputPath.value ? `file://${outputPath.value}` : '');
const completed = computed(() => projectStatus.value === 'completed');

const statusText = computed(() => {
  if (projectStatus.value === 'failed') return errorMessage.value || '生成失败';
  if (stepText.value) return stepText.value;
  switch (projectStatus.value) {
    case 'pending': return '等待开始...';
    case 'processing': return `处理中... ${progress.value}%`;
    case 'completed': return '生成完成！';
    default: return '';
  }
});

function getStatusLabel(s: string) {
  return { pending:'等待中', processing:'处理中', completed:'已完成', failed:'失败' }[s] || s;
}
function formatDate(s: string) { return new Date(s).toLocaleString('zh-CN'); }
function formatDur(s: number) { return `${Math.floor(s/60)}:${Math.floor(s%60).toString().padStart(2,'0')}`; }

function setResolution(w: number, h: number) {
  outputWidth.value = w;
  outputHeight.value = h;
}

function onTemplateChange() {
  const id = selectedTemplateId.value;
  if (!id) {
    // Reset to defaults
    return;
  }
  const t = templates.value.find(t => t.id === id);
  if (!t) return;

  // Apply template asset IDs
  mainVideoId.value = t.main_video_asset_id || 0;
  backgroundId.value = t.background_asset_id || 0;
  productId.value = t.product_asset_id || 0;
  bgmId.value = t.bgm_asset_id || 0;

  // Apply subtitle style
  const sub = t.subtitle_style_json || {};
  if (sub.fontSize !== undefined) subtitleFontSize.value = Number(sub.fontSize);
  if (sub.position !== undefined) subtitlePosition.value = sub.position;
  if (sub.stroke !== undefined) subtitleStroke.value = Number(sub.stroke);

  // Apply layout
  const layout = t.layout_json || {};
  if (layout.mainVideoScale !== undefined) mainVideoScale.value = Number(layout.mainVideoScale);
  if (layout.mainVideoX !== undefined) mainVideoX.value = Number(layout.mainVideoX);
  if (layout.mainVideoY !== undefined) mainVideoY.value = Number(layout.mainVideoY);

  // Apply volume
  if (t.bgm_volume !== undefined) bgmVolume.value = Number(t.bgm_volume);

  // Apply product
  if (t.product_scale !== undefined) productScale.value = Number(t.product_scale);
  if (t.product_position !== undefined) productPosition.value = t.product_position;

  // Apply output resolution
  if (t.output_width) outputWidth.value = t.output_width;
  if (t.output_height) outputHeight.value = t.output_height;
}

function loadProject(p: Project) {
  script.value = p.script_text || '';
  selectedVoice.value = p.voice || 'zh-CN-XiaoxiaoNeural';
}

function onMainVideoChange() {
  // nothing extra needed — v-model already updates mainVideoId
}

async function loadAllAssets() {
  try {
    const [av, ab, ap, abgm, tdata] = await Promise.all([
      getAssets({ type: 'character_video', pageSize: 100 }),
      getAssets({ type: 'background', pageSize: 100 }),
      getAssets({ type: 'product', pageSize: 100 }),
      getAssets({ type: 'bgm', pageSize: 100 }),
      getTemplates(),
    ]);
    mainVideos.value = av.assets;
    backgrounds.value = ab.assets;
    products.value = ap.assets;
    bgms.value = abgm.assets;
    templates.value = tdata.templates || [];
  } catch (e) { console.error('Load assets failed:', e); }
}

async function loadVoices() {
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
}

async function loadProjects() {
  try { projects.value = await getProjects(); } catch {}
}

async function startGenerate() {
  if (!script.value) return;
  generating.value = true;
  projectStatus.value = 'pending';
  progress.value = 0;
  outputPath.value = '';
  errorMessage.value = '';
  stepText.value = '正在启动...';

  try {
    const res = await runPipeline({
      templateId: selectedTemplateId.value || null,
      script: script.value,
      voice: selectedVoice.value,
      mainVideoAssetId: mainVideoId.value || null,
      backgroundAssetId: backgroundId.value || null,
      productAssetId: productId.value || null,
      bgmAssetId: bgmId.value || null,
      subtitleFontSize: subtitleFontSize.value,
      subtitlePosition: subtitlePosition.value,
      subtitleStroke: subtitleStroke.value,
      bgmVolume: bgmVolume.value,
      productPosition: productPosition.value,
      productScale: productScale.value,
      mainVideoScale: mainVideoScale.value,
      mainVideoX: mainVideoX.value,
      mainVideoY: mainVideoY.value,
      outputWidth: outputWidth.value,
      outputHeight: outputHeight.value,
    });
    currentProjectId.value = res.project_id;
    stepText.value = '语音生成中...';
    startPolling();
  } catch (err: any) {
    projectStatus.value = 'failed';
    errorMessage.value = err?.response?.data?.detail || err?.message || '连接服务器失败，请检查后端是否启动';
    generating.value = false;
  }
}

function startPolling() {
  pollInterval.value = window.setInterval(async () => {
    if (!currentProjectId.value) return;
    try {
      const p = await getProjectStatus(currentProjectId.value);
      projectStatus.value = p.status;
      progress.value = p.progress || 0;
      if (p.status === 'pending') stepText.value = '等待处理...';
      else if (p.status === 'processing') {
        if (progress.value < 25) stepText.value = '正在生成语音...';
        else if (progress.value < 40) stepText.value = '正在生成字幕...';
        else stepText.value = '正在合成视频...';
      }
      if (p.status === 'completed') {
        outputPath.value = p.output_path || '';
        stepText.value = '生成完成！';
        stopPolling(); generating.value = false;
      } else if (p.status === 'failed') {
        errorMessage.value = p.error || '视频合成失败';
        stepText.value = '生成失败';
        stopPolling(); generating.value = false;
      }
    } catch {
      projectStatus.value = 'failed'; stopPolling(); generating.value = false;
    }
  }, 2000);
}

function stopPolling() {
  if (pollInterval.value) { clearInterval(pollInterval.value); pollInterval.value = null; }
}

function openDirectory() {
  if (outputPath.value && (window as any).electronAPI) {
    (window as any).electronAPI.openPath(outputPath.value);
  }
}
function downloadVideo() { console.log('Download:', outputPath.value); }

// Load project from URL query param
async function initFromQuery() {
  const projectId = route.query.project;
  if (projectId) {
    try {
      const p = await getProject(Number(projectId));
      loadProject(p);
    } catch {}
  }
}

onMounted(() => { loadAllAssets(); loadVoices(); loadProjects(); initFromQuery(); });
onUnmounted(() => { stopPolling(); });
</script>

<style scoped>
.generate-view { padding: 24px; max-width: 900px; margin: 0 auto; }
h2 { font-size: 24px; color: #1a1a2e; margin-bottom: 24px; }
.generate-form { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 24px; }
.form-section { margin-bottom: 24px; }
.form-section h3 { font-size: 16px; color: #333; margin-bottom: 12px; border-left: 4px solid #667eea; padding-left: 8px; }

/* Template section */
.template-section { background: #f8f9ff; border-radius: 10px; padding: 16px; margin-bottom: 20px; border: 1px solid #e0e4ff; }
.template-select { width: 100%; padding: 10px 12px; border: 1px solid #c5cae9; border-radius: 8px; font-size: 14px; background: white; }
.template-hint { font-size: 12px; color: #667eea; margin-top: 6px; }

.asset-row { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.asset-row label { width: 70px; font-size: 14px; color: #666; flex-shrink: 0; }
.asset-row select { flex: 1; min-width: 200px; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.asset-spec { font-size: 12px; color: #888; white-space: nowrap; }
.product-controls { display: flex; gap: 6px; }
.product-controls select { padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 12px; }
.bgm-vol { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #666; }
.bgm-vol label { width: auto; font-size: 12px; }

.form-section textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; resize: vertical; font-family: inherit; margin-bottom: 10px; }
.voice-select { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }

/* Layout */
.layout-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.layout-group { background: #f8f9fa; border-radius: 8px; padding: 12px; }
.layout-group h4 { font-size: 13px; color: #555; margin-bottom: 10px; font-weight: 500; }
.layout-row { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.layout-row label { font-size: 12px; color: #666; width: 50px; flex-shrink: 0; }
.layout-row input[type="range"] { flex: 1; }
.layout-row input[type="number"] { width: 70px; padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.layout-val, .layout-hint { font-size: 12px; color: #888; width: 40px; text-align: right; }
.resolution-presets { display: flex; gap: 6px; flex-wrap: wrap; }
.resolution-presets button { padding: 4px 10px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer; font-size: 12px; }
.resolution-presets button.active { background: #667eea; color: white; border-color: #667eea; }

.subtitle-controls { display: flex; gap: 16px; flex-wrap: wrap; }
.ctrl-item { display: flex; align-items: center; gap: 8px; }
.ctrl-item label { font-size: 13px; color: #666; }
.ctrl-item select { padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }

.btn-generate { width: 100%; padding: 16px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; transition: opacity 0.3s; }
.btn-generate:disabled { opacity: 0.5; cursor: not-allowed; }

.progress-section, .result-section, .history-section { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 24px; }
.progress-section h3, .result-section h3, .history-section h3 { font-size: 16px; color: #333; margin-bottom: 16px; }
.status-text { text-align: center; color: #666; margin-top: 8px; }
.error-text { text-align: center; color: #e74c3c; margin-top: 8px; font-size: 13px; }
.video-player video { width: 100%; max-height: 400px; border-radius: 8px; }
.result-actions { display: flex; gap: 12px; margin-top: 16px; }
.btn-primary { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.btn-secondary { background: #e9ecef; color: #495057; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.history-list { display: flex; flex-direction: column; gap: 8px; }
.history-item { display: flex; justify-content: space-between; align-items: center; padding: 12px; background: #f8f9fa; border-radius: 8px; cursor: pointer; transition: background 0.3s; }
.history-item:hover { background: #e9ecef; }
.project-info { display: flex; align-items: center; gap: 12px; }
.project-name { font-size: 14px; color: #333; }
.project-status { font-size: 12px; padding: 2px 8px; border-radius: 4px; }
.project-status.pending { background: #fff3cd; color: #856404; }
.project-status.processing { background: #cce5ff; color: #004085; }
.project-status.completed { background: #d4edda; color: #155724; }
.project-status.failed { background: #f8d7da; color: #721c24; }
.project-date { font-size: 12px; color: #666; }
.empty-history { text-align: center; padding: 30px; color: #666; }
</style>