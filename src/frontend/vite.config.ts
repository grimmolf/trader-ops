import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  root: './renderer',
  base: './',
  build: {
    outDir: './dist',
    emptyOutDir: true,
    rollupOptions: {
      input: resolve(__dirname, 'renderer/index.html')
    }
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'renderer/src')
    }
  },
  server: {
    port: 5173,
    strictPort: true
  }
})