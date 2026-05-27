import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

export default defineConfig({
  plugins: [uni()],
  define: {
    // 生产构建：读取 .env.production 的 VITE_API_BASE_URL
    // 开发/未配置时：默认 http://127.0.0.1:8000
    __API_BASE_URL__: JSON.stringify(process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000')
  }
})
