import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import dts from 'vite-plugin-dts'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    dts({
      insertTypesEntry: true
    })
  ],
  
  build: {
    lib: {
      entry: resolve(__dirname, 'src/index.ts'),
      name: 'TraderTerminalUI',
      fileName: 'index'
    },
    rollupOptions: {
      // Externalize peer dependencies
      external: ['vue', 'pinia', '@vueuse/core'],
      output: {
        globals: {
          vue: 'Vue',
          pinia: 'Pinia',
          '@vueuse/core': 'VueUse'
        }
      }
    },
    sourcemap: true,
    emptyOutDir: true
  },
  
  resolve: {
    alias: {
      '@': resolve(__dirname, './src')
    }
  }
})