// 高德地图 JS API Key (免费申请: https://console.amap.com/)
// 通过 Vite 环境变量注入：在 frontend/.env.local 中设置 VITE_AMAP_KEY
export const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''

// 高德地图安全密钥
// 通过 Vite 环境变量注入：在 frontend/.env.local 中设置 VITE_AMAP_SECURITY_CODE
export const AMAP_SECURITY_CODE = import.meta.env.VITE_AMAP_SECURITY_CODE || ''

export const AMAP_VERSION = '2.0'

export const PROVIDERS = [
  { id: 'deepseek', name: 'DeepSeek', icon: '🔍', color: 'bg-blue-500' },
  { id: 'gemini', name: 'Gemini', icon: '🤖', color: 'bg-green-500' },
  { id: 'kimi', name: 'Kimi 月之暗面', icon: '🌙', color: 'bg-purple-500' },
  { id: 'minimax', name: 'MiniMax', icon: '✨', color: 'bg-orange-500' },
  { id: 'zhipu', name: '智谱 GLM', icon: '🧠', color: 'bg-red-500' },
]

export const DEFAULT_PROVIDER = 'deepseek'

// ★ 业态-AMAP 映射已迁移至后端 industry_config.py（数据驱动）；
//    前端选择器直接绑定 GET /api/industries/active，不再需要本地映射。
