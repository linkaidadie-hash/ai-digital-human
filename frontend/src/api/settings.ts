import api from './index';

export interface Settings {
  ffmpeg_path: string;
  output_directory: string;
  default_voice: string;
  default_resolution: string;
}

export interface SettingsStatus {
  ffmpeg: { status: string; path?: string };
  edge_tts: { status: string };
  output_dir: { status: string; path?: string };
  backend: { status: string };
}

export async function getSettings(): Promise<Settings> {
  return api.get('/settings');
}

export async function updateSettings(data: Partial<Settings>): Promise<{ success: boolean; updated: string[] }> {
  return api.post('/settings', data);
}

export async function getSystemStatus(): Promise<any> {
  const raw = await api.get('/health');
  // Normalize to what SettingsView expects: { ffmpeg: {...}, edge_tts: {...} }
  return {
    ffmpeg: raw.checks?.ffmpeg || { status: 'unknown' },
    edge_tts: raw.checks?.edge_tts || { status: 'unknown' },
  };
}

export async function detectFFmpeg(): Promise<{ ffmpeg: { status: string; path?: string } }> {
  return api.get('/status');
}