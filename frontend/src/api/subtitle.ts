import api from './index';

export interface SubtitleStyle {
  font: string;
  size: number;
  color: string;
  position: 'bottom' | 'top' | 'center';
}

// 获取字幕样式
export async function getSubtitleStyle(): Promise<SubtitleStyle> {
  return api.get('/subtitle/style');
}

// 更新字幕样式
export async function updateSubtitleStyle(style: SubtitleStyle): Promise<void> {
  return api.put('/subtitle/style', style);
}

// 生成字幕文件
export async function generateSubtitle(text: string, style: SubtitleStyle): Promise<{ srtPath: string }> {
  return api.post('/subtitle/generate', { text, style });
}