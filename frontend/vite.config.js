import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      // Windows 下 fs.watch 会对被占用的临时文件抛 EBUSY 并导致 dev server 整体退出
      // （编辑器/工具写文件时生成的临时目录会触发），改用轮询监听可避免崩溃
      usePolling: true
    },
    proxy: {
      '/api': {
        target: 'http://localhost:5412',
        changeOrigin: true
      },
      '/static': {
        target: 'http://localhost:5412',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:5412',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'axios'],
          'bootstrap': ['bootstrap']
        }
      }
    }
  }
})
