import api from './index';

export type ProjectStatus = 'draft' | 'pending' | 'processing' | 'completed' | 'failed';

export interface Project {
  id: number;
  name: string;
  template_id: number | null;
  script_text: string;
  voice: string;
  status: ProjectStatus;
  progress?: number;
  audio_path?: string;
  subtitle_path?: string;
  output_path?: string;
  error?: string;
  main_video_asset_id?: number | null;
  background_asset_id?: number | null;
  product_asset_id?: number | null;
  bgm_asset_id?: number | null;
  subtitle_style_json?: string;
  created_at: string;
}

export interface PipelineRunRequest {
  templateId?: number | null;
  script: string;
  voice: string;
  mainVideoAssetId?: number | null;
  backgroundAssetId?: number | null;
  productAssetId?: number | null;
  bgmAssetId?: number | null;
  characterImageAssetId?: number | null;
  mainVideoScale?: number;
  productScale?: number;
  productPosition?: string;
  bgmVolume?: number;
  subtitleFontSize?: number;
  subtitlePosition?: string;
  subtitleStroke?: number;
  mainVideoX?: number;
  mainVideoY?: number;
  outputWidth?: number;
  outputHeight?: number;
}

export interface PipelineRunResponse {
  success: boolean;
  project_id: number;
  message: string;
}

export async function runPipeline(data: PipelineRunRequest): Promise<PipelineRunResponse> {
  return api.post('/pipeline/run', data);
}

export async function getProjects(): Promise<Project[]> {
  const res = await api.get('/projects');
  return res.projects || [];
}

export async function getProject(id: number): Promise<Project> {
  return api.get(`/projects/${id}`);
}

export async function createProject(data: Record<string, any>): Promise<{ success: boolean; project_id: number }> {
  return api.post('/projects', data);
}

export async function updateProject(id: number, data: Record<string, any>): Promise<{ success: boolean }> {
  return api.put(`/projects/${id}`, data);
}

export async function getProjectStatus(id: number): Promise<Project> {
  return api.get(`/projects/${id}/status`);
}

export async function deleteProject(id: number): Promise<void> {
  return api.delete(`/projects/${id}`);
}

export async function copyProject(id: number): Promise<{ success: boolean; project_id: number; name: string }> {
  return api.post(`/projects/${id}/copy`);
}