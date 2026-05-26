import api from './index';

export type ProjectStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Project {
  id: number;
  name: string;
  template_id: number;
  script_text: string;
  voice: string;
  status: ProjectStatus;
  progress?: number;
  audio_path?: string;
  subtitle_path?: string;
  output_path?: string;
  error?: string;
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
  subtitleFontSize?: number;
  subtitlePosition?: string;
  subtitleStroke?: number;
  bgmVolume?: number;
  productPosition?: string;
  productScale?: number;
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

export async function createProject(data: {
  templateId: number; script: string; voice: string;
}): Promise<Project> {
  return api.post('/projects', data);
}

export async function getProjectStatus(id: number): Promise<Project> {
  return api.get(`/projects/${id}/status`);
}

export async function cancelProject(id: number): Promise<void> {
  return api.delete(`/projects/${id}`);
}