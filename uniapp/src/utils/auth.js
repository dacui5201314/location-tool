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
  // ★ 只 merge user 对象字段，不 merge profile 顶层对象（points/memberDays 等）
  const prev = getUser() || {}
  // 过滤掉非用户字段（如 points/memberDays/freePointActive 等 profile 顶层字段）
  const userFields = {}
  const allowed = ['id','nickname','name','avatar_url','avatarUrl','phone','phone_number',
    'balance_credits','membership_tier','membership_days_left','membership_expiry',
    'is_member','free_point_active','free_point_expire_at','wx_unionid','wx_mini_openid']
  Object.keys(user).forEach(k => {
    if (allowed.includes(k) || k.startsWith('wx_') || k.startsWith('membership_')) {
      userFields[k] = user[k]
    }
  })
  // 如果调用方只传了少数几个字段（如 {avatarUrl:...}），直接合并
  if (Object.keys(user).length <= 3 && !user.id) {
    uni.setStorageSync('user', Object.assign({}, prev, user))
    return
  }
  uni.setStorageSync('user', Object.assign({}, prev, userFields))
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
