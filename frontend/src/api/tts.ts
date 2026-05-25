import api from './index';

export interface TTSVoice {
  name: string;
  locale: string;
  gender?: string;
}

// 获取可用音色列表
export async function getVoices(): Promise<TTSVoice[]> {
  return api.get('/tts/voices');
}

// 生成TTS音频
export async function synthesize(text: string, voice: string): Promise<{ audioPath: string }> {
  return api.post('/tts/synthesize', { text, voice });
}

// 测试音色
export async function testVoice(text: string, voice: string): Promise<void> {
  return api.post('/tts/test', { text, voice });
}