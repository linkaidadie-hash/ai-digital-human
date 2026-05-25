<template>
  <div class="templates-view">
    <div class="header">
      <h2>模板管理</h2>
      <button class="btn-primary" @click="createNewTemplate">新建模板</button>
    </div>

    <div class="templates-grid" v-if="templates.length > 0">
      <TemplateCard
        v-for="template in templates"
        :key="template.id"
        :template="template"
        @edit="editTemplate"
        @delete="handleDelete"
      />
    </div>

    <div class="empty-state" v-else>
      <p>暂无模板</p>
      <button class="btn-secondary" @click="createNewTemplate">创建第一个模板</button>
    </div>

    <!-- 编辑对话框 -->
    <div class="dialog-overlay" v-if="showEditor" @click.self="closeEditor">
      <div class="editor-dialog">
        <h3>{{ isEditing ? '编辑模板' : '新建模板' }}</h3>

        <div class="form-group">
          <label>模板名称：</label>
          <input type="text" v-model="editorData.name" placeholder="输入模板名称" />
        </div>

        <div class="form-group">
          <label>主视频（角色视频）：</label>
          <select v-model.number="editorData.main_video_asset_id">
            <option :value="0">请选择角色视频</option>
            <option v-for="asset in characterVideos" :key="asset.id" :value="asset.id">
              {{ asset.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>背景：</label>
          <select v-model.number="editorData.background_asset_id">
            <option :value="0">无背景</option>
            <option v-for="asset in backgrounds" :key="asset.id" :value="asset.id">
              {{ asset.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>商品（可选）：</label>
          <select v-model.number="editorData.product_asset_id">
            <option :value="0">无商品</option>
            <option v-for="asset in products" :key="asset.id" :value="asset.id">
              {{ asset.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>BGM（可选）：</label>
          <select v-model.number="editorData.bgm_asset_id">
            <option :value="0">无BGM</option>
            <option v-for="asset in bgms" :key="asset.id" :value="asset.id">
              {{ asset.name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>字幕样式：</label>
          <div class="subtitle-style">
            <input type="text" v-model="editorData.subtitleStyle.font" placeholder="字体名称" />
            <input type="number" v-model.number="editorData.subtitleStyle.size" placeholder="大小" min="12" max="72" />
            <input type="color" v-model="editorData.subtitleStyle.color" />
          </div>
        </div>

        <div class="form-group">
          <label>角色位置：</label>
          <div class="slider-group">
            <span>X: {{ editorData.layout.character?.x || 0 }}%</span>
            <input type="range" v-model.number="editorData.layout.character!.x" min="0" max="100" />
          </div>
          <div class="slider-group">
            <span>Y: {{ editorData.layout.character?.y || 0 }}%</span>
            <input type="range" v-model.number="editorData.layout.character!.y" min="0" max="100" />
          </div>
        </div>

        <div class="dialog-actions">
          <button class="btn-secondary" @click="closeEditor">取消</button>
          <button class="btn-primary" @click="saveTemplate" :disabled="!editorData.name || !editorData.main_video_asset_id">
            保存模板
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { getTemplates, createTemplate, updateTemplate, deleteTemplate, Template } from '@/api/templates';
import { getAssets, Asset } from '@/api/assets';
import TemplateCard from '@/components/TemplateCard.vue';

const templates = ref<Template[]>([]);
const showEditor = ref(false);
const isEditing = ref(false);
const editingId = ref<number>(0);

const defaultEditorData = () => ({
  name: '',
  main_video_asset_id: 0 as number,
  background_asset_id: 0 as number,
  product_asset_id: 0 as number,
  bgm_asset_id: 0 as number,
  subtitleStyle: { font: 'Arial', size: 24, color: '#FFFFFF' },
  layout: {
    character: { x: 50, y: 50, w: 40, h: 80 },
    product: { x: 80, y: 70, w: 15, h: 20 }
  },
  output_width: 1080,
  output_height: 1920
});

const editorData = ref(defaultEditorData());

const allAssets = ref<Asset[]>([]);

const characterVideos = computed(() =>
  allAssets.value.filter(a => a.type === 'character_video' || a.type === 'action_video')
);

const backgrounds = computed(() =>
  allAssets.value.filter(a => a.type === 'background_image' || a.type === 'background_video')
);

const products = computed(() =>
  allAssets.value.filter(a => a.type === 'product_image' || a.type === 'product_video')
);

const bgms = computed(() =>
  allAssets.value.filter(a => a.type === 'bgm')
);

async function loadTemplates() {
  try {
    templates.value = await getTemplates();
  } catch (error) {
    console.error('Failed to load templates:', error);
  }
}

async function loadAssets() {
  try {
    const data = await getAssets({ pageSize: 1000 });
    allAssets.value = data.assets;
  } catch (error) {
    console.error('Failed to load assets:', error);
  }
}

function createNewTemplate() {
  isEditing.value = false;
  editingId.value = 0;
  editorData.value = defaultEditorData();
  showEditor.value = true;
}

function editTemplate(template: Template) {
  isEditing.value = true;
  editingId.value = template.id;
  editorData.value = {
    name: template.name,
    main_video_asset_id: template.main_video_asset_id,
    background_asset_id: template.background_asset_id,
    product_asset_id: template.product_asset_id || 0,
    bgm_asset_id: template.bgm_asset_id || 0,
    subtitleStyle: {
      font: template.subtitle_style_json?.font || 'Arial',
      size: template.subtitle_style_json?.size || 24,
      color: template.subtitle_style_json?.color || '#FFFFFF'
    },
    layout: {
      character: {
        x: template.layout_json?.character?.x || 50,
        y: template.layout_json?.character?.y || 50,
        w: template.layout_json?.character?.w || 40,
        h: template.layout_json?.character?.h || 80
      },
      product: template.layout_json?.product
        ? { x: template.layout_json.product.x, y: template.layout_json.product.y, w: template.layout_json.product.w, h: template.layout_json.product.h }
        : { x: 80, y: 70, w: 15, h: 20 }
    },
    output_width: template.output_width,
    output_height: template.output_height
  };
  showEditor.value = true;
}

function closeEditor() {
  showEditor.value = false;
}

async function saveTemplate() {
  try {
    const payload = {
      name: editorData.value.name,
      main_video_asset_id: editorData.value.main_video_asset_id,
      background_asset_id: editorData.value.background_asset_id || null,
      product_asset_id: editorData.value.product_asset_id || null,
      bgm_asset_id: editorData.value.bgm_asset_id || null,
      subtitle_style_json: JSON.stringify(editorData.value.subtitleStyle),
      layout_json: JSON.stringify(editorData.value.layout),
      output_width: editorData.value.output_width,
      output_height: editorData.value.output_height
    };
    if (isEditing.value) {
      await updateTemplate(editingId.value, payload);
    } else {
      await createTemplate(payload);
    }
    closeEditor();
    loadTemplates();
  } catch (error) {
    console.error('Save failed:', error);
    alert('保存失败，请重试');
  }
}

async function handleDelete(template: Template) {
  if (confirm(`确定要删除模板 "${template.name}" 吗？`)) {
    try {
      await deleteTemplate(template.id);
      loadTemplates();
    } catch (error) {
      console.error('Delete failed:', error);
    }
  }
}

onMounted(() => {
  loadTemplates();
  loadAssets();
});
</script>

<style scoped>
.templates-view { padding: 24px; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.header h2 { font-size: 24px; color: #1a1a2e; }
.btn-primary { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.btn-secondary { background: #e9ecef; color: #495057; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 14px; }
.templates-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.empty-state { text-align: center; padding: 60px; color: #666; }
.dialog-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.editor-dialog { background: white; border-radius: 16px; padding: 32px; width: 600px; max-width: 90%; max-height: 90vh; overflow-y: auto; }
.editor-dialog h3 { margin-bottom: 24px; font-size: 20px; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 8px; font-size: 14px; color: #666; }
.form-group input, .form-group select { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
.subtitle-style { display: flex; gap: 12px; align-items: center; }
.subtitle-style input[type="text"] { flex: 1; }
.subtitle-style input[type="number"] { width: 80px; }
.subtitle-style input[type="color"] { width: 50px; height: 36px; padding: 2px; cursor: pointer; }
.slider-group { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.slider-group span { width: 80px; font-size: 14px; color: #666; }
.slider-group input[type="range"] { flex: 1; }
.dialog-actions { display: flex; justify-content: flex-end; gap: 12px; margin-top: 24px; }
</style>