<template>
  <div class="settings-view">
    <h2>设置</h2>

    <!-- 系统状态 -->
    <div class="status-cards" v-if="systemStatus">
      <div class="status-card" :class="systemStatus.ffmpeg?.status">
        <span class="status-icon">{{ systemStatus.ffmpeg?.status === 'ok' ? '✅' : '❌' }}</span>
        <span>FFmpeg: {{ systemStatus.ffmpeg?.status === 'ok' ? '正常' : '未找到' }}</span>
      </div>
      <div class="status-card" :class="systemStatus.edge_tts?.status">
        <span class="status-icon">{{ systemStatus.edge_tts?.status === 'ok' ? '✅' : '❌' }}</span>
        <span>TTS: {{ systemStatus.edge_tts?.status === 'ok' ? '正常' : '未找到' }}</span>
      </div>
    </div>

    <div class="settings-form">
      <div class="setting-group">
        <label>FFmpeg 路径</label>
        <div class="input-with-button">
          <input type="text" v-model="settings.ffmpeg_path" placeholder="自动检测或手动输入路径" readonly />
          <button class="btn-detect" @click="detectFFmpeg" :disabled="detecting">
            {{ detecting ? '检测中...' : '🔍 自动检测' }}
          </button>
          <button class="btn-browse" @click="selectFFmpegPath">浏览</button>
        </div>
        <p class="hint" v-if="ffmpegStatus">{{ ffmpegStatus }}</p>
        <p class="hint error" v-if="ffmpegError">{{ ffmpegError }}</p>
      </div>

      <div class="setting-group">
        <label>输出目录</label>
        <div class="input-with-button">
          <input type="text" v-model="settings.output_directory" placeholder="默认使用 outputs 目录" readonly />
          <button class="btn-browse" @click="selectOutputDir">浏览</button>
        </div>
        <p class="hint">生成的视频将保存到此目录，留空则使用默认目录</p>
      </div>

      <div class="setting-group">
        <label>默认 TTS 音色</label>
        <select v-model="settings.default_voice">
          <option value="zh-CN-XiaoxiaoNeural">晓晓 (女声)</option>
          <option value="zh-CN-YunxiNeural">云希 (男声)</option>
          <option value="zh-CN-XiaoyiNeural">小艺 (女声)</option>
          <option value="zh-CN-YunyangNeural">云扬 (男声)</option>
        </select>
        <p class="hint">新建视频时的默认音色选择</p>
      </div>

      <div class="setting-group">
        <label>默认分辨率</label>
        <select v-model="settings.default_resolution">
          <option value="1080x1920">1080×1920 (9:16竖屏)</option>
          <option value="1920x1080">1920×1080 (16:9横屏)</option>
          <option value="1080x1080">1080×1080 (1:1方屏)</option>
        </select>
        <p class="hint">新建视频时的默认分辨率</p>
      </div>

      <div class="setting-actions">
        <button class="btn-save" @click="saveSettings" :disabled="saving">
          {{ saving ? '保存中...' : '💾 保存设置' }}
        </button>
      </div>
    </div>

    <div class="about-section">
      <h3>关于</h3>
      <p>AI数字人视频生成系统 <strong>V1.3</strong></p>
      <p class="version-info">基于 Electron + Vue 3 + FastAPI 构建</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getSettings, updateSettings, getSystemStatus } from '@/api/settings';

const settings = ref({
  ffmpeg_path: '',
  output_directory: '',
  default_voice: 'zh-CN-XiaoxiaoNeural',
  default_resolution: '1080x1920',
});

const systemStatus = ref<any>(null);
const detecting = ref(false);
const saving = ref(false);
const ffmpegStatus = ref('');
const ffmpegError = ref('');

async function loadSettings() {
  try {
    const data = await getSettings();
    settings.value = { ...settings.value, ...data };
  } catch (e) {
    console.error('Load settings failed:', e);
  }
}

async function loadSystemStatus() {
  try {
    systemStatus.value = await getSystemStatus();
  } catch (e) {
    console.error('Load status failed:', e);
  }
}

async function detectFFmpeg() {
  detecting.value = true;
  ffmpegStatus.value = '';
  ffmpegError.value = '';
  try {
    // Re-check via system status endpoint
    const status = await getSystemStatus();
    systemStatus.value = status;
    if (status.ffmpeg?.status === 'ok') {
      settings.value.ffmpeg_path = status.ffmpeg.path || '';
      ffmpegStatus.value = `✅ 检测成功！路径：${settings.value.ffmpeg_path}`;
    } else {
      ffmpegError.value = '❌ 未检测到 FFmpeg，请手动安装或指定路径';
    }
  } catch (e: any) {
    ffmpegError.value = '检测失败：' + (e?.message || '未知错误');
  } finally {
    detecting.value = false;
  }
}

function selectFFmpegPath() {
  if ((window as any).electronAPI) {
    (window as any).electronAPI.selectFile([
      { name: 'FFmpeg', extensions: ['exe'] }
    ]).then((path: string | null) => {
      if (path) {
        settings.value.ffmpeg_path = path;
        ffmpegStatus.value = '';
        ffmpegError.value = '';
      }
    });
  }
}

function selectOutputDir() {
  if ((window as any).electronAPI) {
    (window as any).electronAPI.selectDirectory().then((path: string | null) => {
      if (path) {
        settings.value.output_directory = path;
      }
    });
  }
}

async function saveSettings() {
  saving.value = true;
  try {
    await updateSettings(settings.value);
    ffmpegStatus.value = '✅ 设置已保存';
    ffmpegError.value = '';
    setTimeout(() => { ffmpegStatus.value = ''; }, 3000);
  } catch (e: any) {
    ffmpegError.value = '保存失败：' + (e?.response?.data?.detail || e?.message || '未知错误');
  } finally {
    saving.value = false;
  }
}

onMounted(async () => {
  await Promise.all([loadSettings(), loadSystemStatus()]);
});
</script>

<style scoped>
.settings-view { padding: 24px; max-width: 800px; margin: 0 auto; }
h2 { font-size: 24px; color: #1a1a2e; margin-bottom: 24px; }

.status-cards { display: flex; gap: 12px; margin-bottom: 24px; }
.status-card { display: flex; align-items: center; gap: 8px; padding: 10px 16px; background: white; border-radius: 8px; font-size: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.status-card.ok { background: #f0fff4; color: #276749; }
.status-card.error { background: #fff5f5; color: #c53030; }
.status-icon { font-size: 18px; }

.settings-form { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 24px; }
.setting-group { margin-bottom: 24px; }
.setting-group label { display: block; font-size: 14px; font-weight: 500; color: #333; margin-bottom: 8px; }
.input-with-button { display: flex; gap: 8px; }
.input-with-button input { flex: 1; padding: 10px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; background: #f8f9fa; }
.input-with-button input:focus { outline: none; border-color: #667eea; background: white; }
.input-with-button button { padding: 10px 16px; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; white-space: nowrap; }
.btn-detect { background: #e8f0fe; color: #1a73e8; }
.btn-detect:hover:not(:disabled) { background: #d2e3fc; }
.btn-detect:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-browse { background: #e9ecef; color: #495057; }
.btn-browse:hover { background: #dee2e6; }
.setting-group select { width: 100%; padding: 10px 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.hint { font-size: 12px; color: #999; margin-top: 6px; }
.hint.error { color: #e74c3c; }

.setting-actions { margin-top: 32px; padding-top: 24px; border-top: 1px solid #eee; }
.btn-save { padding: 12px 32px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; }
.btn-save:hover:not(:disabled) { opacity: 0.9; }
.btn-save:disabled { opacity: 0.5; cursor: not-allowed; }

.about-section { background: white; padding: 24px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
.about-section h3 { font-size: 16px; color: #333; margin-bottom: 12px; }
.about-section p { color: #666; margin-bottom: 4px; }
.version-info { font-size: 12px; color: #999; }
</style>