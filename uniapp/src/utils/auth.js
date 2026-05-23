import api from './api'

// ── token/user storage ──
export function getToken () { return uni.getStorageSync('token') || '' }
export function setToken (token) { uni.setStorageSync('token', token) }
export function clearToken () {
  const keys = ['token', 'user', 'gift_note', 'wx_mini_openid', 'wx_unionid']
  keys.forEach(k => { try { uni.removeStorageSync(k) } catch (e) { /* ignore */ } })
}
export function getUser () { return uni.getStorageSync('user') || null }
export function setUser (user) {
  const prev = getUser() || {}
  uni.setStorageSync('user', Object.assign({}, prev, user))
}

// ── 微信小程序登录 ──
export function wechatLogin () {
  return new Promise((resolve, reject) => {
    uni.login({
      provider: 'weixin',
      success (loginRes) {
        if (!loginRes.code) { clearToken(); return reject(new Error('uni.login 未返回 code')) }
        api.wechatMiniLogin(loginRes.code).then(result => {
          if (result.ok) {
            const { token, user, gift_note, wx_mini_openid, wx_unionid } = result.data
            setToken(token)
            setUser(user)
            if (gift_note) uni.setStorageSync('gift_note', gift_note)
            if (wx_mini_openid) uni.setStorageSync('wx_mini_openid', wx_mini_openid)
            if (wx_unionid) uni.setStorageSync('wx_unionid', wx_unionid)
            resolve(result)
          } else {
            clearToken() // 登录失败清理残留
            resolve(result)
          }
        }).catch(reject)
      },
      fail: reject
    })
  })
}

// ── 仿 Web ensureToken ──
export function ensureToken () {
  const t = getToken()
  if (t) return Promise.resolve(t)
  return api.ensureAnonToken().then(r => {
    if (r.ok && r.data.token) {
      setToken(r.data.token)
      if (r.data.user) setUser(r.data.user)
      return r.data.token
    }
    return ''
  })
}

export function isLoggedIn () { return !!getToken() }

export default { getToken, setToken, clearToken, getUser, setUser, wechatLogin, ensureToken, isLoggedIn }
