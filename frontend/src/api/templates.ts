import api from './index';

export interface Template {
  id: number;
  name: string;
  main_video_asset_id: number | null;
  background_asset_id: number | null;
  product_asset_id: number | null;
  bgm_asset_id: number | null;
  subtitle_style_json: Record<string, any>;
  layout_json: Record<string, any>;
  output_width: number;
  output_height: number;
  is_default: number;
  bgm_volume: number;
  tts_volume: number;
  product_scale: number;
  product_position: string;
  main_video_scale: number;
  created_at: string;
}

export async function getTemplates(): Promise<{ templates: Template[]; count: number }> {
  return api.get('/templates');
}

export async function getTemplate(id: number): Promise<Template> {
  return api.get(`/templates/${id}`);
}

export async function createTemplate(data: Record<string, any>): Promise<{ success: boolean; template_id: number }> {
  return api.post('/templates', data);
}

export async function updateTemplate(id: number, data: Record<string, any>): Promise<{ success: boolean; template_id: number }> {
  return api.put(`/templates/${id}`, data);
}

export async function deleteTemplate(id: number): Promise<void> {
  return api.delete(`/templates/${id}`);
}

export async function copyTemplate(id: number): Promise<{ success: boolean; template_id: number; name: string }> {
  return api.post(`/templates/${id}/copy`);
}