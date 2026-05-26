<template>
  <div class="template-card">
    <div class="preview">
      <div class="preview-content">
        <span class="icon">📋</span>
      </div>
    </div>
    <div class="info">
      <h4 class="name">
        <span v-if="template.is_default" class="default-badge">默认</span>
        {{ template.name }}
      </h4>
      <div class="meta">
        <span class="date">{{ formatDate(template.created_at) }}</span>
        <span v-if="template.main_video_asset_id" class="asset-tag">有主视频</span>
        <span v-if="template.product_asset_id" class="asset-tag">有商品</span>
        <span v-if="template.bgm_asset_id" class="asset-tag">有BGM</span>
      </div>
    </div>
    <div class="actions">
      <button class="btn-copy" @click="$emit('copy', template)" title="复制模板" :disabled="template.is_default === 1">
        📋复制
      </button>
      <button class="btn-edit" @click="$emit('edit', template)" title="编辑">
        ✏️
      </button>
      <button class="btn-delete" @click="$emit('delete', template)" title="删除" :disabled="template.is_default === 1">
        🗑️
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Template } from '@/api/templates';

const props = defineProps<{
  template: Template;
}>();

const emit = defineEmits<{
  (e: 'edit', template: Template): void;
  (e: 'delete', template: Template): void;
  (e: 'copy', template: Template): void;
}>();

function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-CN');
}
</script>

<style scoped>
.template-card {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  transition: transform 0.3s, box-shadow 0.3s;
}
.template-card:hover { transform: translateY(-4px); box-shadow: 0 4px 16px rgba(0,0,0,0.15); }
.preview { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; display: flex; align-items: center; justify-content: center; }
.preview-content { width: 80px; height: 80px; background: rgba(255,255,255,0.2); border-radius: 16px; display: flex; align-items: center; justify-content: center; }
.icon { font-size: 40px; }
.info { padding: 16px; flex: 1; }
.name { font-size: 16px; font-weight: 500; color: #333; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.default-badge { font-size: 10px; background: #667eea; color: white; padding: 1px 6px; border-radius: 4px; }
.meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.date { font-size: 12px; color: #999; }
.asset-tag { font-size: 10px; background: #e8eaf6; color: #5c6bc0; padding: 1px 6px; border-radius: 4px; }
.actions { display: flex; justify-content: flex-end; gap: 6px; padding: 0 16px 16px; align-items: center; }
.btn-copy { font-size: 12px; padding: 4px 8px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; }
.btn-copy:hover:not(:disabled) { background: #e8eaf6; }
.btn-edit, .btn-delete { width: 32px; height: 32px; border: none; background: #f8f9fa; border-radius: 6px; cursor: pointer; font-size: 14px; transition: background 0.2s; }
.btn-edit:hover { background: #e9ecef; }
.btn-delete:hover:not(:disabled) { background: #f8d7da; }
.btn-copy:disabled, .btn-delete:disabled { opacity: 0.4; cursor: not-allowed; }
</style>