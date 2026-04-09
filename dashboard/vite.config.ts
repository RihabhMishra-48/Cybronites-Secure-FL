import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const backendPort = env.VITE_BACKEND_PORT || '7861';
  console.log(`\n[AI GUARDIAN] PROXY TARGET DETECTED: http://localhost:${backendPort}\n`);

  return {
    plugins: [react()],
    server: {
      proxy: {
        '/api': {
          target: `http://localhost:${backendPort}`,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, '')
        },
        '/bridge/ws': {
          target: `http://localhost:${backendPort}`,
          ws: true,
          changeOrigin: true,
          secure: false
        }
      }
    }
  }
})
