import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
  server: {
    host: true, // 允许通过局域网 IP 访问
    port: 5173,
    proxy: {
      // API代理 - 直接转发，不包含版本号
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      // 静态文件代理
      '/uploads': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  // 构建配置
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['vue', 'vue-router', 'pinia'],
          ui: ['ant-design-vue'],
        },
      },
    },
  },
  // 环境变量配置
  define: {
    __VUE_OPTIONS_API__: true,
    __VUE_PROD_DEVTOOLS__: false,
  },
})
