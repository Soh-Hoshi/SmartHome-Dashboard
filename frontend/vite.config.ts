import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    host: true, // Listen on 0.0.0.0 so Tailscale / LAN can preview
    allowedHosts: ['dev.sohhoshi.com', 'home.sohhoshi.com', 'localhost'],
    hmr: {
      clientPort: 443,
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
})

