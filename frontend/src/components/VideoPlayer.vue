<template>
  <div class="video-player">
    <video
      ref="videoRef"
      :src="src"
      :controls="controls"
      :autoplay="autoplay"
      @play="onPlay"
      @pause="onPause"
      @ended="onEnded"
      @error="onError"
    ></video>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const props = withDefaults(defineProps<{
  src: string;
  controls?: boolean;
  autoplay?: boolean;
}>(), {
  controls: true,
  autoplay: false
});

const emit = defineEmits<{
  (e: 'play'): void;
  (e: 'pause'): void;
  (e: 'ended'): void;
  (e: 'error', error: Error): void;
}>();

const videoRef = ref<HTMLVideoElement | null>(null);

function onPlay() {
  emit('play');
}

function onPause() {
  emit('pause');
}

function onEnded() {
  emit('ended');
}

function onError(e: Event) {
  const target = e.target as HTMLVideoElement;
  emit('error', new Error(`Video load failed: ${target.error?.message}`));
}

// 控制方法
function play() {
  videoRef.value?.play();
}

function pause() {
  videoRef.value?.pause();
}

function seek(time: number) {
  if (videoRef.value) {
    videoRef.value.currentTime = time;
  }
}

function setVolume(volume: number) {
  if (videoRef.value) {
    videoRef.value.volume = Math.max(0, Math.min(1, volume));
  }
}

defineExpose({ play, pause, seek, setVolume });
</script>

<style scoped>
.video-player {
  width: 100%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}

video {
  width: 100%;
  display: block;
}
</style>