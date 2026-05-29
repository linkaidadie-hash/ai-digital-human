<template>
  <div class="asset-card" :class="{ selected: isSelected }" @click="$emit('select', asset)">
    <div class="thumbnail" @click.stop="$emit('preview', asset)">
      <video
        v-if="isVideo"
        :src="assetUrl"
        :poster="posterUrl"
        muted
        @mouseenter="$event.target.play()"
        @mouseleave="$event.target.pause(); $event.target.currentTime = 0"
      />
      <img v-else-if="isImage" :src="assetUrl" :alt="asset.name" />
      <div v-else-if="isAudio" class="audio-thumb">
        <span class="audio-icon">🎵</span>
        <span class="audio-name">{{ asset.name }}</span>
      </div>
      <div v-else class="placeholder">
        <span class="type-icon">{{ typeIcon }}</span>
      </div>
      <div class="overlay">
        <span>{{ isVideo ? '播放' : isImage ? '预览' : '试听' }}</span>
      </div>
      <div v-if="isSelected" class="select-badge">✓</div>
    </div>
    <div class="info">
      <h4 class="name" :title="asset.name">{{ asset.name }}</h4>
      <div class="meta">
        <span class="type-badge">{{ typeLabel }}</span>
        <span v-if="asset.duration" class="duration">{{ formatDuration(asset.duration) }}</span>
        <span v-if="asset.width && asset.height" class="resolution">{{ asset.width }}×{{ asset.height }}</span>
      </div>
      <div class="specs" v-if="asset.fps || asset.codec || asset.has_audio !== undefined">
        <span v-if="asset.fps" class="spec-chip">{{ asset.fps }}fps</span>
        <span v-if="asset.codec" class="spec-chip">{{ asset.codec }}</span>
        <span v-if="asset.has_audio" class="spec-chip has-audio">🔊</span>
      </div>
    </div>
    <button class="btn-delete" @click.stop="$emit('delete', asset)" title="删除">×</button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { Asset } from '@/api/assets';

const props = defineProps<{
  asset: Asset;
  isSelected?: boolean;
}>();

defineEmits<{
  (e: 'delete', asset: Asset): void;
  (e: 'preview', asset: Asset): void;
  (e: 'select', asset: Asset): void;
}>();

const isVideo = computed(() =>
  ['character_video', 'action_video', 'background_video'].includes(props.asset.type)
);
const isImage = computed(() =>
  ['image', 'background_image', 'product_image', 'character_image'].includes(props.asset.type)
);
const isAudio = computed(() =>
  ['bgm', 'sound_effect'].includes(props.asset.type)
);

const assetUrl = computed(() => props.asset.path ? `file://${props.asset.path}` : '');
const posterUrl = computed(() => '');

const typeIcon = computed(() => ({
  character_video: '🎬', character_image: '🖼️',
  action_video: '🎭',
  background_image: '🖼️', background_video: '🎥',
  product_image: '📦', product_video: '🎁',
  bgm: '🎵', sound_effect: '🔊', font: '🔤',
  image: '🖼️'
}[props.asset.type] || '📁'));

const typeLabel = computed(() => ({
  character_video: '角色视频', character_image: '角色图片',
  action_video: '动作视频',
  background_image: '背景图', background_video: '背景视频',
  product_image: '商品图', product_video: '商品图',
  bgm: 'BGM', sound_effect: '音效', font: '字体',
  image: '图片'
}[props.asset.type] || props.asset.type));

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
  transition: transform 0.3s, box-shadow 0.3s, border 0.3s;
  cursor: pointer;
  border: 2px solid transparent;
}
.asset-card:hover { transform: translateY(-4px); box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
.asset-card.selected { border-color: #667eea; }

.thumbnail {
  width: 100%; aspect-ratio: 16/9;
  background: #1a1a2e; position: relative; overflow: hidden;
}
.thumbnail video { width: 100%; height: 100%; object-fit: cover; }
.thumbnail img { width: 100%; height: 100%; object-fit: cover; }

.audio-thumb {
  width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white; gap: 8px;
}
.audio-icon { font-size: 32px; }
.audio-name { font-size: 11px; padding: 0 8px; text-align: center; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 90%; }

.placeholder {
  width: 100%; height: 100%;
  display: flex; align-items: center; justify-content: center;
}
.type-icon { font-size: 40px; }

.overlay {
  position: absolute; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: opacity 0.3s;
}
.thumbnail:hover .overlay { opacity: 1; }
.overlay span {
  color: white; font-size: 14px; padding: 8px 16px;
  background: rgba(102, 126, 234, 0.9); border-radius: 4px;
}

.select-badge {
  position: absolute; top: 8px; left: 8px;
  width: 24px; height: 24px; border-radius: 50%;
  background: #667eea; color: white;
  display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: bold;
}

.info { padding: 12px; }
.name { font-size: 14px; font-weight: 500; color: #333; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 4px; }
.type-badge { font-size: 11px; padding: 2px 6px; background: #667eea; color: white; border-radius: 4px; }
.duration, .resolution { font-size: 11px; color: #666; }

.specs { display: flex; gap: 4px; flex-wrap: wrap; }
.spec-chip { font-size: 10px; padding: 1px 5px; background: #f0f0f0; color: #666; border-radius: 3px; }
.spec-chip.has-audio { background: transparent; }

.btn-delete {
  position: absolute; top: 8px; right: 8px;
  width: 28px; height: 28px; border: none;
  background: rgba(255,255,255,0.9); border-radius: 50%;
  cursor: pointer; font-size: 18px; color: #666;
  opacity: 0; transition: opacity 0.3s, background 0.3s;
}
.asset-card:hover .btn-delete { opacity: 1; }
.btn-delete:hover { background: #fff; color: #e74c3c; }
</style>
