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

export default defineConfig({
  plugins: [uni()],
  define: {
    __API_BASE_URL__: JSON.stringify(raw)
  }
})
