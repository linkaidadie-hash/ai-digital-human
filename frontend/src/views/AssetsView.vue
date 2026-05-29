<template>
  <div class="assets-view">
    <div class="header">
      <h2>素材库</h2>
      <button class="btn-primary" @click="showImportDialog">导入素材</button>
    </div>

    <div class="filters">
      <div class="filter-group">
        <label>素材类型：</label>
        <select v-model="selectedType" @change="loadAssets">
          <option value="">全部</option>
          <option value="character_video">角色视频</option>
          <option value="character_image">角色图片</option>
          <option value="action_video">动作视频</option>
          <option value="image">图片</option>
          <option value="background_image">背景图</option>
          <option value="background_video">背景视频</option>
          <option value="product_image">商品图</option>
          <option value="product_video">商品视频</option>
          <option value="bgm">BGM</option>
          <option value="font">字体</option>
        </select>
      </div>
    </div>

    <div class="assets-grid" v-if="assets.length > 0">
      <AssetCard
        v-for="asset in assets"
        :key="asset.id"
        :asset="asset"
        @delete="handleDelete"
        @preview="handlePreview"
      />
    </div>
    <div class="empty-state" v-else>
      <p>暂无素材</p>
      <button class="btn-secondary" @click="showImportDialog">导入第一个素材</button>
    </div>

    <!-- 预览弹窗 -->
    <div class="preview-overlay" v-if="previewAsset" @click.self="closePreview">
      <div class="preview-dialog">
        <h3>{{ previewAsset.name }}</h3>
        <div class="preview-content">
          <video v-if="isVideoType(previewAsset.type)" :src="'file://' + previewAsset.path" controls autoplay />
          <img v-else-if="isImageType(previewAsset.type)" :src="'file://' + previewAsset.path" alt="preview" />
          <audio v-else-if="isAudioType(previewAsset.type)" :src="'file://' + previewAsset.path" controls />
        </div>
        <div class="preview-meta">
          <span v-if="previewAsset.duration">{{ formatDuration(previewAsset.duration) }}</span>
          <span v-if="previewAsset.width">{{ previewAsset.width }}×{{ previewAsset.height }}</span>
          <span v-if="previewAsset.fps">{{ previewAsset.fps }}fps</span>
          <span v-if="previewAsset.codec">{{ previewAsset.codec }}</span>
          <span v-if="previewAsset.has_audio">🔊有音轨</span>
          <span v-if="previewAsset.file_size_kb">{{ previewAsset.file_size_kb }}KB</span>
        </div>
        <button class="btn-secondary" @click="closePreview">关闭</button>
      </div>
    </div>

    <!-- 导入对话框 -->
    <div class="dialog-overlay" v-if="showDialog" @click.self="closeDialog">
      <div class="dialog">
        <h3>导入素材</h3>
        <div class="form-group">
          <label>素材类型：</label>
          <select v-model="importType">
            <option value="image">图片</option>
            <option value="character_video">角色视频</option>
            <option value="character_image">角色图片</option>
            <option value="action_video">动作视频</option>
            <option value="background_image">背景图</option>
            <option value="background_video">背景视频</option>
            <option value="product_image">商品图</option>
            <option value="product_video">商品视频</option>
            <option value="bgm">BGM</option>
            <option value="font">字体</option>
          </select>
        </div>
        <div class="dropzone" :class="{ 'drag-over': isDragOver }"
          @dragover.prevent="isDragOver = true" @dragleave="isDragOver = false" @drop.prevent="onDrop">
          <input type="file" ref="fileInput" @change="onFileSelect" :accept="getAcceptTypes()" style="display:none" />
          <div v-if="!selectedFile">
            <p>支持：mp4 / mov / webm / jpg / png / webp / mp3 / wav</p>
            <p>拖拽文件到此处或点击选择</p>
          </div>
          <div v-else>已选择: {{ selectedFile.name }}</div>
          <button type="button" @click="fileInput.click()">选择文件</button>
        </div>
        <div class="form-group">
          <label>标签（逗号分隔）：</label>
          <input type="text" v-model="importTags" placeholder="如：人物,正面" />
        </div>
        <div v-if="uploadResult" class="upload-result" :class="uploadResult.ok ? 'ok' : 'err'">
          {{ uploadResult.msg }}
        </div>
        <div class="dialog-actions">
          <button class="btn-secondary" @click="closeDialog">取消</button>
          <button class="btn-primary" @click="uploadAsset" :disabled="!selectedFile || uploading">
            {{ uploading ? '上传中...' : '上传' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { getAssets, deleteAsset, uploadAsset as apiUpload, Asset } from '@/api/assets';
import AssetCard from '@/components/AssetCard.vue';

const assets = ref<Asset[]>([]);
const selectedType = ref('');
const showDialog = ref(false);
const importType = ref('character_video');
const selectedFile = ref<File | null>(null);
const importTags = ref('');
const isDragOver = ref(false);
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);
const previewAsset = ref<Asset | null>(null);
const uploadResult = ref<{ok: boolean; msg: string} | null>(null);

async function loadAssets() {
  try {
    const data = await getAssets({ type: selectedType.value || undefined, pageSize: 100 });
    assets.value = data.assets;
  } catch (error) {
    console.error('Failed to load assets:', error);
  }
}

function showImportDialog() {
  showDialog.value = true; selectedFile.value = null;
  importTags.value = ''; uploadResult.value = null;
}
function closeDialog() { showDialog.value = false; }

function getAcceptTypes() {
  const types: Record<string, string> = {
    image: 'image/jpeg,image/png,image/webp',
    character_video: 'video/mp4,video/quicktime,video/webm',
    character_image: 'image/jpeg,image/png,image/webp',
    action_video: 'video/mp4,video/quicktime,video/webm',
    background_image: 'image/jpeg,image/png,image/webp',
    background_video: 'video/mp4,video/quicktime,video/webm',
    product_image: 'image/jpeg,image/png,image/webp',
    product_video: 'video/mp4,video/quicktime,video/webm',
    bgm: 'audio/mpeg,audio/wav',
    font: '.ttf,.otf,.woff,.woff2'
  };
  return types[importType.value] || '*';
}

function onDrop(e: DragEvent) {
  isDragOver.value = false;
  if (e.dataTransfer?.files?.[0]) selectedFile.value = e.dataTransfer.files[0];
}
function onFileSelect(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0];
  if (f) selectedFile.value = f;
}

async function uploadAsset() {
  if (!selectedFile.value) return;
  uploading.value = true; uploadResult.value = null;
  try {
    const res = await apiUpload(selectedFile.value, importType.value, importTags.value || undefined);
    uploadResult.value = { ok: true, msg: `上传成功！${res.width ? `${res.width}×${res.height}` : ''}${res.duration ? `, ${res.duration.toFixed(1)}s` : ''}` };
    closeDialog(); loadAssets();
  } catch (err: any) {
    uploadResult.value = { ok: false, msg: err?.response?.data?.detail || err?.message || '上传失败' };
  } finally {
    uploading.value = false;
  }
}

async function handleDelete(asset: Asset) {
  if (confirm(`确定删除素材「${asset.name}」吗？`)) {
    await deleteAsset(asset.id); loadAssets();
  }
}

function handlePreview(asset: Asset) { previewAsset.value = asset; }
function closePreview() { previewAsset.value = null; }

function isVideoType(type: string) { return ['character_video','action_video','background_video','product_video'].includes(type); }
function isImageType(type: string) { return ['image','background_image','product_image','character_image'].includes(type); }
function isAudioType(type: string) { return ['bgm'].includes(type); }
function formatDuration(s: number) { return `${Math.floor(s/60)}:${Math.floor(s%60).toString().padStart(2,'0')}`; }

onMounted(loadAssets);
</script>

<style scoped>
.assets-view { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header h2 { font-size: 24px; color: #1a1a2e; }
.btn-primary { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.btn-secondary { background: #e9ecef; color: #495057; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.filters { display: flex; gap: 24px; margin-bottom: 24px; padding: 16px; background: #f8f9fa; border-radius: 8px; }
.filter-group { display: flex; align-items: center; gap: 8px; }
.filter-group label { font-size: 14px; color: #666; }
.filter-group select { padding: 8px 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
.assets-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; }
.empty-state { text-align: center; padding: 60px; color: #666; }

.preview-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.preview-dialog { background: white; border-radius: 16px; padding: 32px; width: 600px; max-width: 90%; }
.preview-dialog h3 { margin-bottom: 16px; font-size: 18px; color: #333; }
.preview-content { background: #1a1a2e; border-radius: 8px; overflow: hidden; margin-bottom: 12px; max-height: 400px; display: flex; align-items: center; justify-content: center; }
.preview-content video, .preview-content img { max-width: 100%; max-height: 360px; }
.preview-content audio { width: 100%; }
.preview-meta { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; font-size: 13px; color: #666; }

.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.dialog { background: white; border-radius: 16px; padding: 32px; width: 500px; max-width: 90%; }
.dialog h3 { margin-bottom: 24px; font-size: 20px; }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; margin-bottom: 8px; font-size: 14px; color: #666; }
.form-group select, .form-group input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.dropzone { border: 2px dashed #ddd; border-radius: 8px; padding: 30px; text-align: center; margin-bottom: 16px; cursor: pointer; transition: border-color 0.3s; }
.dropzone.drag-over { border-color: #667eea; }
.dropzone p { margin: 4px 0; font-size: 13px; color: #888; }
.dropzone button { margin-top: 12px; padding: 8px 20px; background: #e9ecef; border: none; border-radius: 6px; cursor: pointer; }
.upload-result { padding: 10px; border-radius: 8px; margin-bottom: 12px; font-size: 13px; }
.upload-result.ok { background: #d4edda; color: #155724; }
.upload-result.err { background: #f8d7da; color: #721c24; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
</style>