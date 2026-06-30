import { defineConfig } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

const raw = process.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
const lower = raw.toLowerCase()
const isPlaceholder = lower.includes('localhost') || lower.includes('127.0.0.1')
    || lower.includes('example.com') || lower.includes('change_me')
    || lower.includes('__change_me__')

// mp-weixin 生产构建时，占位符必须直接失败
if (isPlaceholder && process.env.NODE_ENV === 'production') {
  console.error('[BUILD] VITE_API_BASE_URL 不能使用占位符: ' + raw)
  console.error('[BUILD] 请设置环境变量 VITE_API_BASE_URL 为真实生产域名')
  process.exit(1)
}

// 生产构建必须使用 HTTPS，拒绝 http:// 明文传输
if (process.env.NODE_ENV === 'production' && !raw.startsWith('https://')) {
  console.error('[BUILD] 生产构建 VITE_API_BASE_URL 必须以 https:// 开头: ' + raw)
  console.error('[BUILD] 开发环境可用 http://127.0.0.1:8000，生产环境请使用 https://www.oliver188.top')
  process.exit(1)
}

export default defineConfig({
  plugins: [uni()],
  define: {
    __API_BASE_URL__: JSON.stringify(raw)
  }
})
