import api from './index';

export interface Asset {
  id: number;
  name: string;
  type: 'character_video' | 'action_video' | 'background_image' | 'background_video' | 'product_image' | 'product_video' | 'bgm' | 'sound_effect' | 'font';
  path: string;
  tags: string;
  duration: number;
  width: number;
  height: number;
  created_at: string;
}

export interface UploadResponse {
  success: boolean;
  asset_id: number;
  path: string;
  duration: number;
  width: number;
  height: number;
}

// 获取素材列表
export async function getAssets(params?: {
  type?: string;
  page?: number;
  pageSize?: number;
}): Promise<{ assets: Asset[]; count: number }> {
  return api.get('/assets', { params });
}

// 上传素材
export async function uploadAsset(file: File, type: string, name: string, tags?: string): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('type', type);
  formData.append('name', name);
  if (tags) {
    formData.append('tags', tags);
  }

  return api.post('/assets/import', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
}

// 删除素材
export async function deleteAsset(id: number): Promise<void> {
  return api.delete(`/assets/${id}`);
}