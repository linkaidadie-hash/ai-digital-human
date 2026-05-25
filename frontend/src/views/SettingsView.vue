<template>
  <div class="settings-view">
    <h2>设置</h2>

    <div class="settings-form">
      <div class="setting-group">
        <label>FFmpeg 路径</label>
        <div class="input-with-button">
          <input
            type="text"
            v-model="settings.ffmpegPath"
            placeholder="自动检测或手动输入路径"
            readonly
          />
          <button @click="detectFFmpeg" :disabled="detecting">
            {{ detecting ? '检测中...' : '自动检测' }}
          </button>
          <button @click="selectFFmpegPath">浏览</button>
        </div>
        <p class="hint">FFmpeg 用于视频处理，请确保已安装并配置正确的路径</p>
      </div>

      <div class="setting-group">
        <label>输出目录</label>
        <div class="input-with-button">
          <input
            type="text"
            v-model="settings.outputDir"
            placeholder="选择视频输出目录"
            readonly
          />
          <button @click="selectOutputDir">浏览</button>
        </div>
        <p class="hint">生成的视频将保存到此目录</p>
      </div>

      <div class="setting-group">
        <label>默认 TTS 音色</label>
        <select v-model="settings.defaultTTSVoice">
          <option value="zh-CN-XiaoxiaoNeural">晓晓 (女声)</option>
          <option value="zh-CN-YunxiNeural">云希 (男声)</option>
          <option value="zh-CN-XiaoyiNeural">小艺 (女声)</option>
          <option value="zh-CN-YunyangNeural">云扬 (男声)</option>
        </select>
        <p class="hint">新建视频时的默认音色选择</p>
      </div>

      <div class="setting-group">
        <label>默认分辨率</label>
        <select v-model="settings.defaultResolution">
          <option value="1920x1080">1920x1080 (1080p)</option>
          <option value="1280x720">1280x720 (720p)</option>
          <option value="854x480">854x480 (480p)</option>
        </select>
        <p class="hint">新建视频时的默认分辨率</p>
      </div>

      <div class="setting-actions">
        <button class="btn-save" @click="saveSettings">保存设置</button>
      </div>
    </div>

    <div class="about-section">
      <h3>关于</h3>
      <p>AI数字人视频生成系统 v1.0.0</p>
      <p class="version-info">基于 Electron + Vue 3 构建</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useAppStore } from '@/stores/app';

const appStore = useAppStore();

const settings = ref({
  ffmpegPath: '',
  outputDir: '',
  defaultTTSVoice: 'zh-CN-XiaoxiaoNeural',
  defaultResolution: '1920x1080'
});

const detecting = ref(false);

function detectFFmpeg() {
  detecting.value = true;
  // 模拟自动检测
  setTimeout(() => {
    // 尝试从系统路径检测
    const commonPaths = [
      'C:\\ffmpeg\\bin\\ffmpeg.exe',
      'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
      'C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe'
    ];

    // 检测成功后的处理
    settings.value.ffmpegPath = commonPaths[0];
    detecting.value = false;
  }, 1500);
}

function selectFFmpegPath() {
  if (window.electronAPI) {
    window.electronAPI.selectFile([
      { name: 'FFmpeg', extensions: ['exe'] }
    ]).then((path: string | null) => {
      if (path) {
        settings.value.ffmpegPath = path;
      }
    });
  }
}

function selectOutputDir() {
  if (window.electronAPI) {
    window.electronAPI.selectDirectory().then((path: string | null) => {
      if (path) {
        settings.value.outputDir = path;
      }
    });
  }
}

function saveSettings() {
  appStore.updateSettings(settings.value);
  // 保存到本地存储
  localStorage.setItem('app-settings', JSON.stringify(settings.value));
  alert('设置已保存');
}

function loadSettings() {
  const saved = localStorage.getItem('app-settings');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      settings.value = { ...settings.value, ...parsed };
      appStore.updateSettings(settings.value);
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
  }
}

onMounted(loadSettings);
</script>

<style scoped>
.settings-view {
  padding: 24px;
  max-width: 800px;
  margin: 0 auto;
}

h2 {
  font-size: 24px;
  color: #1a1a2e;
  margin-bottom: 24px;
}

.settings-form {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 24px;
}

.setting-group {
  margin-bottom: 24px;
}

.setting-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.input-with-button {
  display: flex;
  gap: 8px;
}

.input-with-button input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.input-with-button button {
  padding: 10px 16px;
  background: #e9ecef;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
}

.input-with-button button:hover {
  background: #dee2e6;
}

.setting-group select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.hint {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}

.setting-actions {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #eee;
}

.btn-save {
  padding: 12px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
}

.btn-save:hover {
  opacity: 0.9;
}

.about-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.about-section h3 {
  font-size: 16px;
  color: #333;
  margin-bottom: 12px;
}

.about-section p {
  color: #666;
  margin-bottom: 4px;
}

.version-info {
  font-size: 12px;
  color: #999;
}
</style>