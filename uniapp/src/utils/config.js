// 本地开发：默认 http://127.0.0.1:8000
// 生产构建：通过 Vite define 注入 __API_BASE_URL__（来自 .env.production 的 VITE_API_BASE_URL）
// 注意：不使用 import.meta.env，其 Vite 编译产物在微信小程序中会生成 require("url") 导致所有页面空白

const API_BASE_URL = __API_BASE_URL__

export default { API_BASE_URL }
