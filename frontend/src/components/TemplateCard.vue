<template>
  <div class="template-card">
    <div class="preview">
      <div class="preview-content">
        <span class="icon">📋</span>
      </div>
    </div>
    <div class="info">
      <h4 class="name">{{ template.name }}</h4>
      <div class="meta">
        <span class="date">{{ formatDate(template.created_at) }}</span>
      </div>
    </div>
    <div class="actions">
      <button class="btn-edit" @click="$emit('edit', template)" title="编辑">
        ✏️
      </button>
      <button class="btn-delete" @click="$emit('delete', template)" title="删除">
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
}>();

function formatDate(dateStr: string): string {
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

.template-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.preview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-content {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon {
  font-size: 40px;
}

.info {
  padding: 16px;
}

.name {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  margin-bottom: 8px;
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.date {
  font-size: 12px;
  color: #999;
}

.actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 0 16px 16px;
}

.btn-edit,
.btn-delete {
  width: 36px;
  height: 36px;
  border: none;
  background: #f8f9fa;
  border-radius: 8px;
  cursor: pointer;
  font-size: 16px;
  transition: background 0.3s;
}

.btn-edit:hover {
  background: #e9ecef;
}

.btn-delete:hover {
  background: #f8d7da;
}
</style>