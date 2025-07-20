import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  root: resolve(__dirname, '../src/frontend/renderer'),
  base: './',
  build: {
    outDir: resolve(__dirname, '../build/renderer'),
    emptyOutDir: true,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, '../src/frontend/renderer'),
    },
  },
  server: {
    port: 3000,
    strictPort: true,
  },
})