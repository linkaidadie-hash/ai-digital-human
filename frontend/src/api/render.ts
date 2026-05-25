import api from './index';

export type ProjectStatus = 'pending' | 'processing' | 'completed' | 'failed';

export interface Project {
  id: number;
  name: string;
  template_id: number;
  script_text: string;
  voice: string;
  status: ProjectStatus;
  audio_path?: string;
  subtitle_path?: string;
  output_path?: string;
  error?: string;
  created_at: string;
}

// 获取项目列表
export async function getProjects(): Promise<Project[]> {
  const res = await api.get('/projects');
  return res.projects || [];
}

// 获取单个项目
export async function getProject(id: number): Promise<Project> {
  return api.get(`/projects/${id}`);
}

// 创建项目（开始生成）
export async function createProject(data: {
  templateId: number;
  script: string;
  voice: string;
}): Promise<Project> {
  return api.post('/projects', data);
}

// 获取项目状态（用于轮询）
export async function getProjectStatus(id: number): Promise<Project> {
  return api.get(`/projects/${id}/status`);
}

// 取消项目
export async function cancelProject(id: number): Promise<void> {
  return api.delete(`/projects/${id}`);
}