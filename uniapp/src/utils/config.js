// 本地开发：默认 http://127.0.0.1:8000
// 生产构建：读取 VITE_API_BASE_URL 环境变量（来自 .env.production）
// 生产未配置 HTTPS 时 API 调用将因 URL 为空而失败，不会静默回退到本地地址

const _raw = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL) || ''
const _isPlaceholder = !_raw || _raw.startsWith('__CHANGE_ME')
const API_BASE_URL = _isPlaceholder ? 'http://127.0.0.1:8000' : _raw

// 如果生产构建但 VITE_API_BASE_URL 仍是占位符，运行时报错
if (_isPlaceholder && _raw.startsWith('__CHANGE_ME')) {
  console.error('[址得选] VITE_API_BASE_URL 未配置为 HTTPS 地址，API 调用将使用本地地址。请检查 .env.production 文件。')
}

export default { API_BASE_URL }
