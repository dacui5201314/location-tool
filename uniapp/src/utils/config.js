// API 地址由 vite.config.js 在构建时通过 __API_BASE_URL__ 注入
// 开发默认 http://127.0.0.1:8000，生产由环境变量 VITE_API_BASE_URL 设置
// 不要在此硬编码生产域名

const API_BASE_URL = typeof __API_BASE_URL__ !== 'undefined' ? __API_BASE_URL__ : 'http://127.0.0.1:8000'

export default { API_BASE_URL }
