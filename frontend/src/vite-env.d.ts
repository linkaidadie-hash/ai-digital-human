/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface Window {
  electronAPI?: {
    selectDirectory: () => Promise<string | null>;
    selectFile: (filters?: Array<{ name: string; extensions: string[] }>) => Promise<string | null>;
    openPath: (filePath: string) => Promise<void>;
    getAppVersion: () => Promise<string>;
    platform: string;
  };
}