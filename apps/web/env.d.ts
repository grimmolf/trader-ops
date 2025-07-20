/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_DEPLOYMENT_MODE: 'web' | 'electron' | 'tauri'
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}