<template>
  <div class="progress-bar">
    <div class="progress-track">
      <div
        class="progress-fill"
        :style="{ width: `${progress}%` }"
        :class="status"
      ></div>
    </div>
    <div class="progress-info">
      <span class="progress-text">{{ progressText }}</span>
      <span class="progress-percent">{{ progress }}%</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  progress: number;
  status?: 'pending' | 'processing' | 'completed' | 'failed';
}>(), {
  status: 'pending'
});

const progressText = computed(() => {
  switch (props.status) {
    case 'pending': return '等待中';
    case 'processing': return '处理中';
    case 'completed': return '已完成';
    case 'failed': return '失败';
    default: return '';
  }
});
</script>

<style scoped>
.progress-bar {
  width: 100%;
}

.progress-track {
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.5s ease;
}

.progress-fill.pending {
  background: #ffc107;
}

.progress-fill.processing {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.progress-fill.completed {
  background: #28a745;
}

.progress-fill.failed {
  background: #dc3545;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
}

.progress-text {
  font-size: 14px;
  color: #666;
}

.progress-percent {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}
</style>