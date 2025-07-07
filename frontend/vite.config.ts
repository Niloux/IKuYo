import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import viteCompression from 'vite-plugin-compression'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    vueDevTools(),
    viteCompression({
      algorithm: 'gzip',
      threshold: 10240, // 10KB
      ext: '.gz',
    }),
    viteCompression({
      algorithm: 'brotliCompress',
      threshold: 10240, // 10KB
      ext: '.br',
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('vue')) {
              return 'vendor_vue';
            }
            if (id.includes('pinia')) {
              return 'vendor_pinia';
            }
            if (id.includes('vue-router')) {
              return 'vendor_router';
            }
            return 'vendor';
          }
        },
      },
    },
  },
})
