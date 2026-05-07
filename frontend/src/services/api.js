/**
 * API 客户端 — 统一 JWT 鉴权拦截器
 *
 * 所有需要鉴权的请求自动附带 Authorization: Bearer <token>。
 * Token 通过 localStorage 持久化，首次使用前需调用 ensureToken() 获取。
 */
import { getDeviceId } from '../utils/deviceId'

const API_BASE = '/api'
const TOKEN_KEY = '_auth_token'
const ADMIN_TOKEN_KEY = '_admin_token'

/**
 * 构造静态资源完整 URL — 开发环境走 Vite 代理，生产环境可配置 VITE_API_BASE_URL
 * 用法：getAssetUrl('/assets/qr_code.png') → 'http://localhost:8000/assets/qr_code.png' 或 '/assets/qr_code.png'
 */
export function getAssetUrl(path) {
  if (!path) return ''
  if (path.startsWith('http') || path.startsWith('data:')) return path
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}${path}`
}

// ── Token 管理 ────────────────────────────────────────────

let _currentUser = null

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch (e) {
    return null
  }
}

export function setToken(token) {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch (e) { /* */ }
}

export function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch (e) { /* */ }
}

export function getAdminToken() {
  try {
    return localStorage.getItem(ADMIN_TOKEN_KEY)
  } catch (e) {
    return null
  }
}

export function setAdminToken(token) {
  try {
    localStorage.setItem(ADMIN_TOKEN_KEY, token)
  } catch (e) { /* */ }
}

export function clearAdminToken() {
  try {
    localStorage.removeItem(ADMIN_TOKEN_KEY)
  } catch (e) { /* */ }
}

export function setCurrentUser(user) {
  _currentUser = user
}

// ── Token 就绪门控 ────────────────────────────────────────

/**
 * 模块级 Promise 缓存，确保多个并发调用者共享同一个 Token 签发请求。
 * 消除"页面组件 mount 即发请求，但 Token 尚未获取"的抢跑问题。
 */
let _tokenPromise = null

export async function ensureToken() {
  // 已有有效 Token → 立即返回
  const existing = getToken()
  if (existing) {
    return { token: existing, isNew: false }
  }

  // Token 签发正在进行中 → 复用同一个 Promise，避免重复请求
  if (_tokenPromise) {
    return _tokenPromise
  }

  // 发起新的 Token 签发请求
  _tokenPromise = (async () => {
    try {
      const deviceId = getDeviceId()
      const resp = await fetch(`${API_BASE}/auth/token?device_id=${encodeURIComponent(deviceId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })

      if (!resp.ok) {
        throw new Error('无法获取认证令牌，请检查网络连接')
      }

      const data = await resp.json()
      setToken(data.token)
      setCurrentUser(data.user)
      return { token: data.token, isNew: true, user: data.user, giftNote: data.gift_note }
    } finally {
      // 无论成功失败都清除缓存，允许失败后重试
      _tokenPromise = null
    }
  })()

  return _tokenPromise
}

// ── 鉴权请求拦截器 ────────────────────────────────────────

/**
 * 统一 fetch 封装 — 自动注入 Authorization Header。
 * 每次请求前自动 await ensureToken() 确保 Token 已就绪，
 * 彻底消除"请求抢跑导致 401"的竞态问题。
 * 收到 401 时清除 Token 并触发重新签发。
 */
async function authFetch(url, options = {}) {
  // ★ 门控：确保 Token 就绪后再发起请求
  try {
    await ensureToken()
  } catch (e) {
    // Token 签发失败 — 继续无 Token 请求（后端返回 401 由调用方处理）
  }

  const token = getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const resp = await fetch(url, { ...options, headers })

  if (resp.status === 401) {
    clearToken()
  }

  return resp
}

// ── 业务 API ──────────────────────────────────────────────
// ★ analyzeLocation / fetchProviders 已移除 — analyze 走 SSE 流（见 HomePage.jsx handleAnalyze），
//    非流式调用会导致 JSON 解析崩溃。

export async function fetchProfile() {
  const resp = await authFetch(`${API_BASE}/user/profile`)
  if (!resp.ok) throw new Error('获取用户信息失败')
  return resp.json()
}

export async function fetchRecords(page = 1, pageSize = 20) {
  const resp = await authFetch(`${API_BASE}/records?page=${page}&page_size=${pageSize}`)
  if (!resp.ok) throw new Error('获取记录失败')
  return resp.json()
}

export async function fetchRecordDetail(reportUuid) {
  const resp = await authFetch(`${API_BASE}/records/${reportUuid}`)
  if (!resp.ok) throw new Error('记录不存在')
  return resp.json()
}

export async function deleteRecord(reportUuid) {
  const resp = await authFetch(`${API_BASE}/records/${reportUuid}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('删除失败')
  return resp.json()
}

export async function unlockPdf(reportUuid) {
  const resp = await authFetch(`${API_BASE}/records/${reportUuid}/unlock-pdf`, { method: 'POST' })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || '解锁失败')
  }
  return resp.json()
}

export async function fetchFavorites() {
  const resp = await authFetch(`${API_BASE}/favorites`)
  if (!resp.ok) throw new Error('获取收藏失败')
  return resp.json()
}

export async function checkFavorite(latitude, longitude) {
  const resp = await authFetch(`${API_BASE}/favorites/check?latitude=${latitude}&longitude=${longitude}`)
  if (!resp.ok) throw new Error('检查收藏失败')
  return resp.json()
}

export async function addFavorite(customName, address, latitude, longitude) {
  const resp = await authFetch(`${API_BASE}/favorites`, {
    method: 'POST',
    body: JSON.stringify({ custom_name: customName, address, latitude, longitude }),
  })
  if (!resp.ok) throw new Error('添加收藏失败')
  return resp.json()
}

export async function deleteFavorite(favoriteId) {
  const resp = await authFetch(`${API_BASE}/favorites/${favoriteId}`, { method: 'DELETE' })
  if (!resp.ok) throw new Error('取消收藏失败')
  return resp.json()
}

// ── 管理后台 API（需要 Admin JWT） ──────────────────────────

export async function adminLogin(password) {
  const resp = await fetch(`${API_BASE}/admin/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ password }),
  })
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}))
    throw new Error(err.detail || '密码错误')
  }
  const data = await resp.json()
  setAdminToken(data.token)
  return data
}

export async function fetchSystemSettings() {
  const token = getAdminToken()
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const resp = await fetch(`${API_BASE}/admin/system-settings`, { headers })
  if (!resp.ok) throw new Error('获取系统参数失败')
  return resp.json()
}

export async function saveSystemSettings(items) {
  const token = getAdminToken()
  const headers = { 'Content-Type': 'application/json' }
  if (token) headers['Authorization'] = `Bearer ${token}`
  const resp = await fetch(`${API_BASE}/admin/system-settings`, {
    method: 'PUT',
    headers,
    body: JSON.stringify({ items }),
  })
  if (!resp.ok) throw new Error('保存系统参数失败')
  return resp.json()
}
