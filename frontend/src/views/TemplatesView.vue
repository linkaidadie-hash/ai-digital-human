<template>
  <div class="templates-view">
    <div class="header">
      <h2>模板管理</h2>
      <button class="btn-primary" @click="createNewTemplate">+ 新建模板</button>
    </div>

    <!-- 加载中 -->
    <div class="loading" v-if="loading">
      <p>加载中...</p>
    </div>

    <!-- 模板列表 -->
    <div class="templates-grid" v-else-if="templates.length > 0">
      <TemplateCard
        v-for="template in templates"
        :key="template.id"
        :template="template"
        @edit="editTemplate"
        @delete="confirmDelete"
        @copy="copyTemplate"
      />
    </div>

    <!-- 空状态 -->
    <div class="empty-state" v-else>
      <div class="empty-icon">📋</div>
      <p>还没有模板</p>
      <p class="empty-sub">创建模板可以保存常用配置，省去每次重复选择的麻烦</p>
      <button class="btn-secondary" @click="createNewTemplate">创建第一个模板</button>
    </div>

    <!-- 编辑对话框 -->
    <div class="dialog-overlay" v-if="showEditor" @click.self="closeEditor">
      <div class="editor-dialog">
        <h3>{{ isEditing ? '✏️ 编辑模板' : '➕ 新建模板' }}</h3>

        <div class="form-group">
          <label>模板名称 <span class="required">*</span></label>
          <input type="text" v-model="editorData.name" placeholder="例如：我的半身口播模板" />
        </div>

        <div class="form-group">
          <label>主视频（角色视频）</label>
          <select v-model.number="editorData.main_video_asset_id">
            <option :value="0">不选</option>
            <option v-for="asset in characterVideos" :key="asset.id" :value="asset.id">
              {{ asset.name }} {{ asset.width ? `${asset.width}×${asset.height}` : '' }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>背景</label>
          <select v-model.number="editorData.background_asset_id">
            <option :value="0">黑色背景</option>
            <option v-for="asset in backgrounds" :key="asset.id" :value="asset.id">
              {{ asset.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>商品图</label>
          <select v-model.number="editorData.product_asset_id">
            <option :value="0">不显示</option>
            <option v-for="asset in products" :key="asset.id" :value="asset.id">
              {{ asset.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>BGM 背景音乐</label>
          <select v-model.number="editorData.bgm_asset_id">
            <option :value="0">不添加</option>
            <option v-for="asset in bgms" :key="asset.id" :value="asset.id">
              {{ asset.name }} {{ asset.duration ? formatDur(asset.duration) : '' }}
            </option>
          </select>
        </div>

        <!-- 布局设置 -->
        <div class="form-group">
          <label>布局设置</label>
          <div class="layout-fields">
            <div class="layout-row">
              <label>主视频缩放</label>
              <input type="range" v-model.number="editorData.main_video_scale" min="0.1" max="1.0" step="0.05" />
              <span>{{ Math.round(editorData.main_video_scale * 100) }}%</span>
            </div>
            <div class="layout-row">
              <label>BGM 音量</label>
              <input type="range" v-model.number="editorData.bgm_volume" min="0" max="1" step="0.05" />
              <span>{{ Math.round(editorData.bgm_volume * 100) }}%</span>
            </div>
            <div class="layout-row">
              <label>商品位置</label>
              <select v-model="editorData.product_position">
                <option value="bottom-right">右下角</option>
                <option value="bottom-left">左下角</option>
                <option value="top-right">右上角</option>
                <option value="top-left">左上角</option>
              </select>
            </div>
            <div class="layout-row">
              <label>商品缩放</label>
              <input type="range" v-model.number="editorData.product_scale" min="0.1" max="0.8" step="0.05" />
              <span>{{ Math.round(editorData.product_scale * 100) }}%</span>
            </div>
          </div>
        </div>

        <!-- 字幕样式 -->
        <div class="form-group">
          <label>字幕样式</label>
          <div class="subtitle-fields">
            <select v-model.number="editorData.subtitle_font_size">
              <option :value="36">小 36</option>
              <option :value="48">中 48</option>
              <option :value="64">大 64</option>
              <option :value="80">超大 80</option>
            </select>
            <select v-model="editorData.subtitle_position">
              <option value="top">顶部</option>
              <option value="middle">中部</option>
              <option value="bottom">底部</option>
            </select>
            <select v-model.number="editorData.subtitle_stroke">
              <option :value="1">细描边</option>
              <option :value="2">中描边</option>
              <option :value="4">粗描边</option>
            </select>
          </div>
        </div>

        <!-- 输出分辨率 -->
        <div class="form-group">
          <label>输出分辨率</label>
          <div class="resolution-row">
            <input type="number" v-model.number="editorData.output_width" min="360" max="4096" step="2" />
            <span>×</span>
            <input type="number" v-model.number="editorData.output_height" min="360" max="4096" step="2" />
          </div>
        </div>

        <div class="dialog-actions">
          <button class="btn-secondary" @click="closeEditor">取消</button>
          <button class="btn-primary" @click="saveTemplate" :disabled="!editorData.name">
            💾 保存模板
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { getTemplates, createTemplate, updateTemplate, deleteTemplate, copyTemplate as apiCopyTemplate, Template } from '@/api/templates';
import { getAssets, Asset } from '@/api/assets';
import TemplateCard from '@/components/TemplateCard.vue';

const templates = ref<Template[]>([]);
const allAssets = ref<Asset[]>([]);
const showEditor = ref(false);
const isEditing = ref(false);
const editingId = ref<number>(0);
const loading = ref(false);
const saveError = ref('');

const characterVideos = computed(() => allAssets.value.filter(a => a.type === 'character_video' || a.type === 'action_video'));
const backgrounds = computed(() => allAssets.value.filter(a => a.type === 'background_image' || a.type === 'background_video'));
const products = computed(() => allAssets.value.filter(a => a.type === 'product_image' || a.type === 'product_video'));
const bgms = computed(() => allAssets.value.filter(a => a.type === 'bgm'));

function formatDur(s: number) { return `${Math.floor(s/60)}:${Math.floor(s%60).toString().padStart(2,'0')}`; }

function defaultEditorData() {
  return {
    name: '',
    main_video_asset_id: 0 as number,
    background_asset_id: 0 as number,
    product_asset_id: 0 as number,
    bgm_asset_id: 0 as number,
    main_video_scale: 0.4,
    bgm_volume: 0.15,
    product_position: 'bottom-right',
    product_scale: 0.25,
    subtitle_font_size: 48,
    subtitle_position: 'bottom',
    subtitle_stroke: 2,
    output_width: 1080,
    output_height: 1920,
  };
}

const editorData = ref(defaultEditorData());

async function loadTemplates() {
  try {
    const data = await getTemplates();
    templates.value = data.templates || [];
  } catch (e) {
    console.error('Failed to load templates:', e);
  }
}

async function loadAssets() {
  try {
    const data = await getAssets({ pageSize: 1000 });
    allAssets.value = data.assets;
  } catch (e) {
    console.error('Failed to load assets:', e);
  }
}

function createNewTemplate() {
  isEditing.value = false;
  editingId.value = 0;
  editorData.value = defaultEditorData();
  saveError.value = '';
  showEditor.value = true;
}

function editTemplate(template: Template) {
  isEditing.value = true;
  editingId.value = template.id;
  saveError.value = '';

  const sub = template.subtitle_style_json || {};
  editorData.value = {
    name: template.name,
    main_video_asset_id: template.main_video_asset_id || 0,
    background_asset_id: template.background_asset_id || 0,
    product_asset_id: template.product_asset_id || 0,
    bgm_asset_id: template.bgm_asset_id || 0,
    main_video_scale: template.main_video_scale || 0.4,
    bgm_volume: template.bgm_volume || 0.15,
    product_position: template.product_position || 'bottom-right',
    product_scale: template.product_scale || 0.25,
    subtitle_font_size: sub.fontSize || 48,
    subtitle_position: sub.position || 'bottom',
    subtitle_stroke: sub.stroke || 2,
    output_width: template.output_width || 1080,
    output_height: template.output_height || 1920,
  };
  showEditor.value = true;
}

function closeEditor() {
  showEditor.value = false;
}

async function saveTemplate() {
  if (!editorData.value.name) return;
  saveError.value = '';

  // Build subtitle_style_json
  const subtitleStyleJson = {
    fontSize: editorData.value.subtitle_font_size,
    position: editorData.value.subtitle_position,
    stroke: editorData.value.subtitle_stroke,
  };

  // Build layout_json
  const layoutJson = {
    mainVideoScale: editorData.value.main_video_scale,
    mainVideoX: 30,
    mainVideoY: 10,
  };

  // API uses camelCase keys
  const payload: Record<string, any> = {
    name: editorData.value.name,
    mainVideoAssetId: editorData.value.main_video_asset_id || null,
    backgroundAssetId: editorData.value.background_asset_id || null,
    productAssetId: editorData.value.product_asset_id || null,
    bgmAssetId: editorData.value.bgm_asset_id || null,
    subtitleStyleJson: JSON.stringify(subtitleStyleJson),
    layoutJson: JSON.stringify(layoutJson),
    bgmVolume: editorData.value.bgm_volume,
    productScale: editorData.value.product_scale,
    productPosition: editorData.value.product_position,
    mainVideoScale: editorData.value.main_video_scale,
    outputWidth: editorData.value.output_width,
    outputHeight: editorData.value.output_height,
  };

  try {
    if (isEditing.value) {
      await updateTemplate(editingId.value, payload);
    } else {
      await createTemplate(payload);
    }
    closeEditor();
    await loadTemplates();
  } catch (e: any) {
    saveError.value = e?.response?.data?.detail || e?.message || '保存失败，请重试';
    alert(saveError.value);
  }
}

async function confirmDelete(template: Template) {
  if (template.is_default === 1) {
    alert('默认模板不能删除');
    return;
  }
  if (!confirm(`确定要删除模板「${template.name}」吗？此操作无法撤销。`)) return;
  try {
    await deleteTemplate(template.id);
    await loadTemplates();
  } catch (e: any) {
    alert(e?.response?.data?.detail || e?.message || '删除失败');
  }
}

async function copyTemplate(template: Template) {
  try {
    await apiCopyTemplate(template.id);
    await loadTemplates();
  } catch (e: any) {
    alert(e?.response?.data?.detail || e?.message || '复制失败');
  }
}

onMounted(async () => {
  loading.value = true;
  await Promise.all([loadTemplates(), loadAssets()]);
  loading.value = false;
});
</script>

<style scoped>
.templates-view { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header h2 { font-size: 24px; color: #1a1a2e; }
.btn-primary { background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.btn-secondary { background: #e9ecef; color: #495057; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.loading { text-align: center; padding: 60px; color: #888; }
.templates-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 16px; }
.empty-state { text-align: center; padding: 80px 40px; color: #666; background: white; border-radius: 12px; }
.empty-icon { font-size: 64px; margin-bottom: 16px; }
.empty-state p { font-size: 16px; margin-bottom: 8px; }
.empty-sub { font-size: 13px; color: #999; margin-bottom: 20px; }
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.editor-dialog { background: white; border-radius: 16px; padding: 32px; width: 560px; max-width: 95%; max-height: 90vh; overflow-y: auto; }
.editor-dialog h3 { margin-bottom: 24px; font-size: 20px; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 8px; font-size: 14px; color: #555; font-weight: 500; }
.required { color: #e74c3c; }
.form-group input[type="text"], .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; box-sizing: border-box; }
.layout-fields { background: #f8f9fa; border-radius: 8px; padding: 12px; }
.layout-row { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.layout-row label { font-size: 13px; color: #666; width: 80px; flex-shrink: 0; }
.layout-row input[type="range"] { flex: 1; }
.layout-row span { font-size: 13px; color: #888; width: 45px; }
.layout-row select { padding: 4px 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 13px; }
.subtitle-fields { display: flex; gap: 10px; flex-wrap: wrap; }
.subtitle-fields select { flex: 1; min-width: 100px; padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.resolution-row { display: flex; align-items: center; gap: 8px; }
.resolution-row input { width: 80px; padding: 8px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; text-align: center; }
.resolution-row span { font-size: 14px; color: #666; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 28px; padding-top: 20px; border-top: 1px solid #eee; }
</style>