import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// VITE_API_URL is set by docker-compose (http://backend:8000) for the
// preview server used in production containers; dev defaults to the local
// uvicorn port. Both `vite dev` (server.proxy) and `vite preview`
// (preview.proxy) must forward /api — preview does NOT inherit server.proxy,
// so without this the deployed frontend 404s on every API call.
const apiTarget = process.env.VITE_API_URL || 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        target: apiTarget,
        changeOrigin: true,
      },
    },
  },
});
