import api from './index';

export interface Template {
  id: number;
  name: string;
  main_video_asset_id: number;
  background_asset_id: number;
  product_asset_id?: number;
  bgm_asset_id?: number;
  subtitle_style_json: {
    font?: string;
    size?: number;
    color?: string;
  };
  layout_json: {
    character?: { x: number; y: number; w?: number; h?: number };
    product?: { x: number; y: number; w?: number; h?: number };
  };
  output_width: number;
  output_height: number;
  created_at: string;
}

// 获取模板列表
export async function getTemplates(): Promise<Template[]> {
  const res = await api.get('/templates');
  return res.templates || [];
}

// 获取单个模板
export async function getTemplate(id: number): Promise<Template> {
  return api.get(`/templates/${id}`);
}

// 创建模板
export async function createTemplate(data: Omit<Template, 'id' | 'created_at'>): Promise<Template> {
  return api.post('/templates', data);
}

// 更新模板
export async function updateTemplate(id: number, data: Partial<Template>): Promise<Template> {
  return api.put(`/templates/${id}`, data);
}

// 删除模板
export async function deleteTemplate(id: number): Promise<void> {
  return api.delete(`/templates/${id}`);
}