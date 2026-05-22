import config from './config'

// ── 内部封装 ──
function request ({ url, method = 'GET', data = {}, auth = true }) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    if (auth) {
      const token = uni.getStorageSync('token')
      if (token) header['Authorization'] = 'Bearer ' + token
    }
    uni.request({
      url: config.API_BASE_URL + url,
      method,
      data,
      header,
      success (res) {
        resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, statusCode: res.statusCode, data: res.data })
      },
      fail (err) { reject(err) }
    })
  })
}

// ── 错误提取 ──
function normalizeError (result) {
  if (!result) return '网络异常，请重试'
  const d = result.data
  if (typeof d === 'string') return d
  if (d?.detail) return d.detail
  if (d?.error) return d.error
  if (d?.message) return d.message
  return `请求失败 (HTTP ${result.statusCode || '?'})`
}

// ── Auth ──
/** 匿名设备 token（Web 兼容降级） */
function ensureAnonToken () {
  return request({ url: '/api/auth/token?device_id=uni-default', auth: false })
}

/** 微信小程序登录：code → /api/auth/wechat/mini → JWT */
function wechatMiniLogin (code) {
  return request({ url: '/api/auth/wechat/mini', method: 'POST', data: { code }, auth: false })
}

// ── User / Records / Favorites ──
function fetchProfile () { return request({ url: '/api/user/profile' }) }
function fetchRecords (page = 1, pageSize = 20) { return request({ url: `/api/records?page=${page}&page_size=${pageSize}` }) }
function fetchRecordDetail (uuid) { return request({ url: `/api/records/${uuid}` }) }
function deleteRecord (uuid) { return request({ url: `/api/records/${uuid}`, method: 'DELETE' }) }
function fetchFavorites () { return request({ url: '/api/favorites' }) }
function deleteFavorite (id) { return request({ url: `/api/favorites/${id}`, method: 'DELETE' }) }
function fetchIndustries () { return request({ url: '/api/industries/active', auth: false }) }

// ── Location ──
function locationSuggest (keyword, city = '') {
  const qs = `keyword=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}`
  return request({ url: `/api/location/suggest?${qs}`, auth: false })
}

function locationRegeocode (lng, lat) {
  return request({ url: `/api/location/regeocode?lng=${lng}&lat=${lat}`, auth: false })
}

// ── Health ──
function getHealth () { return request({ url: '/api/health', auth: false }) }

export default {
  request, normalizeError, ensureAnonToken, wechatMiniLogin,
  fetchProfile, fetchRecords, fetchRecordDetail, deleteRecord,
  fetchFavorites, deleteFavorite, fetchIndustries, locationSuggest, locationRegeocode, getHealth
}
