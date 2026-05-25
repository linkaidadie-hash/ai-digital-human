import { createRouter, createWebHashHistory } from 'vue-router';
import HomeView from '@/views/HomeView.vue';
import AssetsView from '@/views/AssetsView.vue';
import TemplatesView from '@/views/TemplatesView.vue';
import GenerateView from '@/views/GenerateView.vue';
import SettingsView from '@/views/SettingsView.vue';

const routes = [
  { path: '/', name: 'home', component: HomeView },
  { path: '/assets', name: 'assets', component: AssetsView },
  { path: '/templates', name: 'templates', component: TemplatesView },
  { path: '/generate', name: 'generate', component: GenerateView },
  { path: '/settings', name: 'settings', component: SettingsView }
];

const router = createRouter({
  history: createWebHashHistory(),
  routes
});

export default router;