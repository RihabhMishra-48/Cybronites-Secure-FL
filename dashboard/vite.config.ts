import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendPort = env.VITE_BACKEND_PORT || '7880';
  console.log(`\n[AI GUARDIAN] PROXY TARGET: http://localhost:${backendPort}\n`);

  return {
    plugins: [react()],
    server: {
      proxy: {
        // Proxy all /api/* calls to the FastAPI backend (keep path as-is)
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
          // Do NOT rewrite - backend expects /api prefix
        },
        // Proxy WebSocket connections
        '/ws': {
          target: `http://localhost:${backendPort}`,
          ws: true,
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})
