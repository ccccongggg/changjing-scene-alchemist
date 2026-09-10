import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  },
  // 预览用生产构建（无 HMR，页面不会被开发时的热更新打断）
  preview: {
    port: 4173,
    proxy: {
      '/api': 'http://localhost:8000'
    }
  },
  build: {
    emptyOutDir: false
  }
})
