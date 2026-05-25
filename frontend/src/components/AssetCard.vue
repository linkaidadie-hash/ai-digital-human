<template>
  <div class="asset-card">
    <div class="thumbnail" @click="$emit('preview', asset)">
      <img v-if="thumbnailUrl" :src="thumbnailUrl" :alt="asset.name" />
      <div v-else class="placeholder">
        <span class="type-icon">{{ getTypeIcon() }}</span>
      </div>
      <div class="overlay">
        <span>预览</span>
      </div>
    </div>
    <div class="info">
      <h4 class="name">{{ asset.name }}</h4>
      <div class="meta">
        <span class="type-badge">{{ getTypeLabel() }}</span>
        <span v-if="asset.duration" class="duration">{{ formatDuration(asset.duration) }}</span>
      </div>
      <div class="tags" v-if="asset.tags.length > 0">
        <span v-for="tag in asset.tags.slice(0, 2)" :key="tag" class="tag">{{ tag }}</span>
      </div>
    </div>
    <button class="btn-delete" @click="$emit('delete', asset)" title="删除">
      ×
    </button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Asset } from '@/api/assets';

const props = defineProps<{
  asset: Asset;
}>();

const emit = defineEmits<{
  (e: 'delete', asset: Asset): void;
  (e: 'preview', asset: Asset): void;
}>();

const thumbnailUrl = computed(() => {
  if (props.asset.thumbnail) {
    return `file://${props.asset.thumbnail}`;
  }
  return null;
});

function getTypeIcon(): string {
  const icons: Record<string, string> = {
    character_video: '🎬',
    action_video: '🎭',
    background_image: '🖼',
    background_video: '🎥',
    product_image: '📦',
    product_video: '🎁',
    bgm: '🎵',
    sound_effect: '🔊',
    font: '🔤'
  };
  return icons[props.asset.type] || '📁';
}

function getTypeLabel(): string {
  const labels: Record<string, string> = {
    character_video: '角色视频',
    action_video: '动作视频',
    background_image: '背景图',
    background_video: '背景视频',
    product_image: '商品图',
    product_video: '商品视频',
    bgm: 'BGM',
    sound_effect: '音效',
    font: '字体'
  };
  return labels[props.asset.type] || props.asset.type;
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
</script>

<style scoped>
.asset-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  transition: transform 0.3s, box-shadow 0.3s;
}

.asset-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.thumbnail {
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #f0f0f0;
  position: relative;
  cursor: pointer;
  overflow: hidden;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.type-icon {
  font-size: 40px;
}

.overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s;
}

.thumbnail:hover .overlay {
  opacity: 1;
}

.overlay span {
  color: white;
  font-size: 14px;
  padding: 8px 16px;
  background: rgba(102, 126, 234, 0.9);
  border-radius: 4px;
}

.info {
  padding: 12px;
}

.name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.type-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: #667eea;
  color: white;
  border-radius: 4px;
}

.duration {
  font-size: 12px;
  color: #666;
}

.tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.tag {
  font-size: 11px;
  padding: 2px 6px;
  background: #e9ecef;
  color: #666;
  border-radius: 3px;
}

.btn-delete {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  color: #666;
  opacity: 0;
  transition: opacity 0.3s, background 0.3s;
}

.asset-card:hover .btn-delete {
  opacity: 1;
}

.btn-delete:hover {
  background: #fff;
  color: #e74c3c;
}
</style>