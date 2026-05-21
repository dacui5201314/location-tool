import config from './config'

/**
 * 封装 uni.request，对齐 Web authFetch。
 * auth=true 时从 storage 取 token 附加 Authorization 头。
 */
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

/** 匿名 token 获取 */
function ensureToken () {
  return request({ url: '/api/auth/token?device_id=uni-default', auth: false })
}

/** 获取用户 profile */
function fetchProfile () {
  return request({ url: '/api/user/profile' })
}

/** 获取分析记录 */
function fetchRecords (page = 1) {
  return request({ url: `/api/records?page=${page}&page_size=20` })
}

/** 获取单条记录 */
function fetchRecordDetail (uuid) {
  return request({ url: `/api/records/${uuid}` })
}

/** 获取收藏 */
function fetchFavorites () {
  return request({ url: '/api/favorites' })
}

/** 获取业态列表 */
function fetchIndustries () {
  return request({ url: '/api/industries/active', auth: false })
}

export default { request, ensureToken, fetchProfile, fetchRecords, fetchRecordDetail, fetchFavorites, fetchIndustries }
