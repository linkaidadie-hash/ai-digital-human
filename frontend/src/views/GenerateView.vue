<template>
  <div class="generate-view">
    <h2>视频生成</h2>

    <div class="generate-form">
      <div class="form-section">
        <h3>1. 选择模板</h3>
        <select v-model.number="selectedTemplateId" class="template-select">
          <option :value="0">请选择模板</option>
          <option v-for="template in templates" :key="template.id" :value="template.id">
            {{ template.name }}
          </option>
        </select>
      </div>

      <div class="form-section">
        <h3>2. 输入文案</h3>
        <textarea
          v-model="script"
          placeholder="请输入要生成的视频文案..."
          rows="6"
        ></textarea>
      </div>

      <div class="form-section">
        <h3>3. 选择音色</h3>
        <select v-model="selectedVoice">
          <option value="">请选择音色</option>
          <option v-for="voice in voices" :key="voice.name" :value="voice.name">
            {{ voice.name }} ({{ voice.locale }})
          </option>
        </select>
        <button class="btn-test" @click="testVoice" :disabled="!selectedVoice || !script">
          试听
        </button>
      </div>

      <button
        class="btn-generate"
        @click="startGenerate"
        :disabled="!selectedTemplateId || !script || !selectedVoice || generating"
      >
        {{ generating ? '生成中...' : '开始生成' }}
      </button>
    </div>

    <!-- 进度显示 -->
    <div class="progress-section" v-if="generating || projectStatus">
      <h3>生成进度</h3>
      <ProgressBar :progress="progress" :status="projectStatus" />
      <p class="status-text">{{ statusText }}</p>
    </div>

    <!-- 结果区域 -->
    <div class="result-section" v-if="completed && outputPath">
      <h3>生成完成</h3>
      <div class="video-player">
        <video :src="videoUrl" controls autoplay></video>
      </div>
      <div class="result-actions">
        <button class="btn-primary" @click="openDirectory">打开目录</button>
        <button class="btn-secondary" @click="downloadVideo">下载视频</button>
      </div>
    </div>

    <!-- 历史项目 -->
    <div class="history-section">
      <h3>历史项目</h3>
      <div class="history-list" v-if="projects.length > 0">
        <div
          v-for="project in projects"
          :key="project.id"
          class="history-item"
          @click="loadProject(project)"
        >
          <div class="project-info">
            <span class="project-name">{{ project.name }}</span>
            <span class="project-status" :class="project.status">
              {{ getStatusLabel(project.status) }}
            </span>
          </div>
          <span class="project-date">{{ formatDate(project.createdAt) }}</span>
        </div>
      </div>
      <div class="empty-history" v-else>
        <p>暂无历史项目</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { getTemplates, Template } from '@/api/templates';
import { getVoices, TTSVoice } from '@/api/tts';
import { getProjects, createProject, getProjectStatus, Project } from '@/api/render';
import ProgressBar from '@/components/ProgressBar.vue';

const templates = ref<Template[]>([]);
const voices = ref<TTSVoice[]>([]);
const projects = ref<Project[]>([]);

const selectedTemplateId = ref<number>(0);
const script = ref('');
const selectedVoice = ref('zh-CN-XiaoxiaoNeural');

const generating = ref(false);
const currentProjectId = ref<number>(0);
const progress = ref(0);
const projectStatus = ref<'pending' | 'processing' | 'completed' | 'failed'>('pending');
const outputPath = ref('');
const pollInterval = ref<number | null>(null);

const videoUrl = computed(() => outputPath.value ? `file://${outputPath.value}` : '');

const statusText = computed(() => {
  switch (projectStatus.value) {
    case 'pending': return '等待开始...';
    case 'processing': return `处理中... ${progress.value}%`;
    case 'completed': return '生成完成！';
    case 'failed': return '生成失败';
    default: return '';
  }
});

const completed = computed(() => projectStatus.value === 'completed');

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    pending: '等待中',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  };
  return labels[status] || status;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN');
}

function loadProject(project: Project) {
  selectedTemplateId.value = project.template_id;
  script.value = project.script_text;
  selectedVoice.value = project.voice;
}

async function loadTemplates() {
  try {
    templates.value = await getTemplates();
  } catch (error) {
    console.error('Failed to load templates:', error);
  }
}

async function loadVoices() {
  try {
    voices.value = await getVoices();
    if (voices.value.length === 0) {
      // 使用默认音色列表
      voices.value = [
        { name: 'zh-CN-XiaoxiaoNeural', locale: 'zh-CN', gender: 'Female' },
        { name: 'zh-CN-YunxiNeural', locale: 'zh-CN', gender: 'Male' },
        { name: 'zh-CN-XiaoyiNeural', locale: 'zh-CN', gender: 'Female' },
        { name: 'zh-CN-YunyangNeural', locale: 'zh-CN', gender: 'Male' }
      ];
    }
  } catch (error) {
    // 使用默认音色
    voices.value = [
      { name: 'zh-CN-XiaoxiaoNeural', locale: 'zh-CN', gender: 'Female' },
      { name: 'zh-CN-YunxiNeural', locale: 'zh-CN', gender: 'Male' },
      { name: 'zh-CN-XiaoyiNeural', locale: 'zh-CN', gender: 'Female' },
      { name: 'zh-CN-YunyangNeural', locale: 'zh-CN', gender: 'Male' }
    ];
  }
}

async function loadProjects() {
  try {
    projects.value = await getProjects();
  } catch (error) {
    console.error('Failed to load projects:', error);
  }
}

async function testVoice() {
  console.log('Testing voice:', selectedVoice.value, script.value);
  // TODO: 调用测试API
}

async function startGenerate() {
  if (!selectedTemplateId.value || !script.value || !selectedVoice.value) return;

  generating.value = true;
  projectStatus.value = 'pending';
  progress.value = 0;
  outputPath.value = '';

  try {
    const project = await createProject({
      templateId: selectedTemplateId.value,
      script: script.value,
      voice: selectedVoice.value
    });

    currentProjectId.value = project.id;
    startPolling();
  } catch (error) {
    console.error('Create project failed:', error);
    projectStatus.value = 'failed';
    generating.value = false;
  }
}

function startPolling() {
  pollInterval.value = window.setInterval(async () => {
    if (!currentProjectId.value) return;

    try {
      const project = await getProjectStatus(currentProjectId.value);
      projectStatus.value = project.status;
      progress.value = project.progress;

      if (project.status === 'completed') {
        outputPath.value = project.output_path || '';
        stopPolling();
        generating.value = false;
      } else if (project.status === 'failed') {
        stopPolling();
        generating.value = false;
      }
    } catch (error) {
      console.error('Poll failed:', error);
    }
  }, 2000);
}

function stopPolling() {
  if (pollInterval.value) {
    clearInterval(pollInterval.value);
    pollInterval.value = null;
  }
}

function openDirectory() {
  if (outputPath.value && window.electronAPI) {
    window.electronAPI.openPath(outputPath.value);
  }
}

function downloadVideo() {
  if (outputPath.value) {
    // 下载视频逻辑
    console.log('Download:', outputPath.value);
  }
}

onMounted(() => {
  loadTemplates();
  loadVoices();
  loadProjects();
});

onUnmounted(() => {
  stopPolling();
});
</script>

<style scoped>
.generate-view {
  padding: 24px;
  max-width: 900px;
  margin: 0 auto;
}

h2 {
  font-size: 24px;
  color: #1a1a2e;
  margin-bottom: 24px;
}

.generate-form {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.form-section {
  margin-bottom: 24px;
}

.form-section h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 12px;
}

.form-section select,
.form-section textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.form-section textarea {
  resize: vertical;
  font-family: inherit;
}

.btn-test {
  margin-top: 8px;
  padding: 8px 16px;
  background: #e9ecef;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.btn-generate {
  width: 100%;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 18px;
  cursor: pointer;
  transition: opacity 0.3s;
}

.btn-generate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.progress-section,
.result-section,
.history-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.progress-section h3,
.result-section h3,
.history-section h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 16px;
}

.status-text {
  text-align: center;
  color: #666;
  margin-top: 8px;
}

.video-player {
  width: 100%;
  margin-bottom: 16px;
}

.video-player video {
  width: 100%;
  max-height: 400px;
  border-radius: 8px;
}

.result-actions {
  display: flex;
  gap: 12px;
}

.btn-primary {
  background: #667eea;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.btn-secondary {
  background: #e9ecef;
  color: #495057;
  border: none;
  padding: 12px 24px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
}

.history-item:hover {
  background: #e9ecef;
}

.project-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.project-name {
  font-size: 14px;
  color: #333;
}

.project-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.project-status.pending {
  background: #fff3cd;
  color: #856404;
}

.project-status.processing {
  background: #cce5ff;
  color: #004085;
}

.project-status.completed {
  background: #d4edda;
  color: #155724;
}

.project-status.failed {
  background: #f8d7da;
  color: #721c24;
}

.project-date {
  font-size: 12px;
  color: #666;
}

.empty-history {
  text-align: center;
  padding: 30px;
  color: #666;
}
</style>