import api from './api'

// ── token/user storage ──
export function getToken () { return uni.getStorageSync('token') || '' }
export function setToken (token) { uni.setStorageSync('token', token) }
// 身份标识字段（不得写入前端 storage）
var _IDENTITY_KEYS = ['wx_mini_openid','wx_unionid','wx_openid','wx_mp_openid','openid','unionid','wx_session_key']

function _stripIdentity(obj) {
  if (!obj) return obj
  var cleaned = {}
  Object.keys(obj).forEach(function(k) {
    if (_IDENTITY_KEYS.indexOf(k) < 0) cleaned[k] = obj[k]
  })
  return cleaned
}

export function clearToken () {
  var keys = ['token', 'user', 'gift_note'].concat(_IDENTITY_KEYS)
  keys.forEach(function(k) { try { uni.removeStorageSync(k) } catch (e) { /* ignore */ } })
}
export function getUser () { return uni.getStorageSync('user') || null }
export function setUser (user) {
  user = _stripIdentity(user)
  var prev = _stripIdentity(getUser() || {})
  var allowed = ['id','nickname','name','avatar_url','avatarUrl','phone','phone_number',
    'balance_credits','membership_tier','membership_days_left','membership_expiry',
    'is_member','free_point_active','free_point_expire_at']
  var userFields = {}
  Object.keys(user).forEach(function(k) {
    if (allowed.indexOf(k) >= 0 || k.indexOf('membership_') === 0) {
      userFields[k] = user[k]
    }
  })
  // 少量字段直接合并（strip 后的 prev）
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
            const { token, user, gift_note } = result.data
            setToken(token)
            setUser(user)
            if (gift_note) uni.setStorageSync('gift_note', gift_note)
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

export function handleAuthExpired () {
  try { uni.removeStorageSync('token') } catch (e) {}
  try { uni.removeStorageSync('user') } catch (e) {}
  try { if (typeof uni.$emit === 'function') uni.$emit('auth:expired') } catch (e) {}
}

export default { getToken, setToken, clearToken, getUser, setUser, wechatLogin, ensureToken, isLoggedIn, handleAuthExpired }

