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
          <option value="action_video">动作视频</option>
          <option value="background_image">背景图</option>
          <option value="background_video">背景视频</option>
          <option value="product_image">商品图</option>
          <option value="product_video">商品视频</option>
          <option value="bgm">BGM</option>
          <option value="sound_effect">音效</option>
          <option value="font">字体</option>
        </select>
      </div>

      <div class="filter-group">
        <label>标签筛选：</label>
        <input type="text" v-model="tagFilter" placeholder="输入标签名称" />
        <button @click="loadAssets">筛选</button>
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

    <!-- 导入对话框 -->
    <div class="dialog-overlay" v-if="showDialog" @click.self="closeDialog">
      <div class="dialog">
        <h3>导入素材</h3>
        <div class="form-group">
          <label>素材类型：</label>
          <select v-model="importType">
            <option value="character_video">角色视频</option>
            <option value="action_video">动作视频</option>
            <option value="background_image">背景图</option>
            <option value="background_video">背景视频</option>
            <option value="product_image">商品图</option>
            <option value="product_video">商品视频</option>
            <option value="bgm">BGM</option>
            <option value="sound_effect">音效</option>
            <option value="font">字体</option>
          </select>
        </div>

        <div
          class="dropzone"
          @dragover.prevent="onDragOver"
          @dragleave="onDragLeave"
          @drop.prevent="onDrop"
          :class="{ 'drag-over': isDragOver }"
        >
          <input
            type="file"
            ref="fileInput"
            @change="onFileSelect"
            :accept="getAcceptTypes()"
            style="display: none"
          />
          <div v-if="!selectedFile">拖拽文件到此处或点击选择</div>
          <div v-else>已选择: {{ selectedFile.name }}</div>
          <button @click="fileInput.click()">选择文件</button>
        </div>

        <div class="form-group">
          <label>标签（逗号分隔）：</label>
          <input type="text" v-model="importTags" placeholder="如：人物,正面" />
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
const tagFilter = ref('');
const showDialog = ref(false);
const importType = ref('character_video');
const selectedFile = ref<File | null>(null);
const importTags = ref('');
const isDragOver = ref(false);
const uploading = ref(false);
const fileInput = ref<HTMLInputElement | null>(null);

async function loadAssets() {
  try {
    const tags = tagFilter.value ? tagFilter.value.split(',').map(t => t.trim()) : undefined;
    const data = await getAssets({
      type: selectedType.value || undefined,
      tags,
      pageSize: 100
    });
    assets.value = data.assets;
  } catch (error) {
    console.error('Failed to load assets:', error);
  }
}

function showImportDialog() {
  showDialog.value = true;
  selectedFile.value = null;
  importTags.value = '';
}

function closeDialog() {
  showDialog.value = false;
  selectedFile.value = null;
}

function getAcceptTypes() {
  const types: Record<string, string> = {
    character_video: 'video/*',
    action_video: 'video/*',
    background_image: 'image/*',
    background_video: 'video/*',
    product_image: 'image/*',
    product_video: 'video/*',
    bgm: 'audio/*',
    sound_effect: 'audio/*',
    font: '.ttf,.otf,.woff,.woff2'
  };
  return types[importType.value] || '*';
}

function onDragOver() {
  isDragOver.value = true;
}

function onDragLeave() {
  isDragOver.value = false;
}

function onDrop(e: DragEvent) {
  isDragOver.value = false;
  const files = e.dataTransfer?.files;
  if (files && files.length > 0) {
    selectedFile.value = files[0];
  }
}

function onFileSelect(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files.length > 0) {
    selectedFile.value = target.files[0];
  }
}

async function uploadAsset() {
  if (!selectedFile.value) return;

  uploading.value = true;
  try {
    const tags = importTags.value ? importTags.value.split(',').map(t => t.trim()) : [];
    await apiUpload(selectedFile.value, importType.value, tags);
    closeDialog();
    loadAssets();
  } catch (error) {
    console.error('Upload failed:', error);
    alert('上传失败，请重试');
  } finally {
    uploading.value = false;
  }
}

async function handleDelete(asset: Asset) {
  if (confirm(`确定要删除素材 "${asset.name}" 吗？`)) {
    try {
      await deleteAsset(asset.id);
      loadAssets();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  }
}

function handlePreview(asset: Asset) {
  // 可以在这里打开预览对话框
  console.log('Preview:', asset);
}

onMounted(loadAssets);
</script>

<style scoped>
.assets-view {
  padding: 24px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header h2 {
  font-size: 24px;
  color: #1a1a2e;
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

.filters {
  display: flex;
  gap: 24px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  color: #666;
}

.filter-group select,
.filter-group input {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.assets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.empty-state {
  text-align: center;
  padding: 60px;
  color: #666;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: white;
  border-radius: 16px;
  padding: 32px;
  width: 500px;
  max-width: 90%;
}

.dialog h3 {
  margin-bottom: 24px;
  font-size: 20px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: #666;
}

.form-group select,
.form-group input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
}

.dropzone {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  margin-bottom: 16px;
  cursor: pointer;
  transition: border-color 0.3s;
}

.dropzone.drag-over {
  border-color: #667eea;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}
</style>