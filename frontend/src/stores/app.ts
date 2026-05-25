import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAppStore = defineStore('app', () => {
  const settings = ref({
    ffmpegPath: '',
    outputDir: '',
    defaultTTSVoice: 'zh-CN-XiaoxiaoNeural',
    defaultResolution: '1920x1080'
  });

  const currentProject = ref<any>(null);
  const isLoading = ref(false);

  function updateSettings(newSettings: Partial<typeof settings.value>) {
    settings.value = { ...settings.value, ...newSettings };
  }

  function setCurrentProject(project: any) {
    currentProject.value = project;
  }

  function setLoading(loading: boolean) {
    isLoading.value = loading;
  }

  return {
    settings,
    currentProject,
    isLoading,
    updateSettings,
    setCurrentProject,
    setLoading
  };
});