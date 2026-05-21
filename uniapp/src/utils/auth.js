import api from './api'

/**
 * 仿 Web ensureToken：优先微信小程序登录，降级 device token。
 * 当前 Phase 23A 不接真实登录，只做结构占位。
 */
export function ensureToken () {
  return api.ensureToken()
}

export function getToken () {
  return uni.getStorageSync('token') || ''
}

export function setToken (token) {
  uni.setStorageSync('token', token)
}

export function clearToken () {
  uni.removeStorageSync('token')
  uni.removeStorageSync('user')
}

export function getUser () {
  return uni.getStorageSync('user') || null
}

export function setUser (user) {
  uni.setStorageSync('user', user)
}

export default { ensureToken, getToken, setToken, clearToken, getUser, setUser }
