import api from './index';

export interface Asset {
  id: number;
  name: string;
  type: string;
  path: string;
  tags: string;
  duration: number;
  width: number;
  height: number;
  fps?: number;
  codec?: string;
  has_audio?: boolean;
  format?: string;
  file_size_kb?: number;
  created_at: string;
}

export interface UploadResponse {
  success: boolean;
  asset_id: number;
  path: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  codec: string;
  has_audio: boolean;
  format: string;
  file_size_kb: number;
}

export async function getAssets(params?: {
  type?: string;
  page?: number;
  pageSize?: number;
}): Promise<{ assets: Asset[]; count: number }> {
  return api.get('/assets', { params });
}

export async function uploadAsset(file: File, type: string, tags?: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('asset_type', type);
  if (tags) formData.append('tags', tags);
  return api.post('/assets/import', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
}

export async function getAsset(id: number): Promise<Asset> {
  return api.get(`/assets/${id}`);
}

export async function deleteAsset(id: number): Promise<void> {
  return api.delete(`/assets/${id}`);
}