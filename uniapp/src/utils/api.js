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

function bindPhone (code) {
  return request({ url: '/api/auth/wechat/mini/bind-phone', method: 'POST', data: { code } })
}

function phoneLogin (loginCode, phoneCode) {
  return request({ url: '/api/auth/wechat/mini/phone-login', method: 'POST', data: { login_code: loginCode, phone_code: phoneCode }, auth: false })
}

// ── User / Records / Favorites ──
function fetchProfile () { return request({ url: '/api/user/profile' }) }
function updateProfile (data) { return request({ url: '/api/user/profile', method: 'PUT', data }) }
function uploadAvatar (filePath) {
  return new Promise((resolve, reject) => {
    const token = uni.getStorageSync('token')
    uni.uploadFile({
      url: config.API_BASE_URL + '/api/user/avatar',
      filePath,
      name: 'file',
      header: token ? { 'Authorization': 'Bearer ' + token } : {},
      success (res) {
        try {
          const data = JSON.parse(res.data)
          resolve({ ok: res.statusCode >= 200 && res.statusCode < 300, statusCode: res.statusCode, data })
        } catch (e) {
          resolve({ ok: false, statusCode: res.statusCode, data: res.data })
        }
      },
      fail (err) { reject(err) }
    })
  })
}
function fetchRecords (page = 1, pageSize = 20) { return request({ url: `/api/records?page=${page}&page_size=${pageSize}` }) }
function fetchRecordDetail (uuid) { return request({ url: `/api/records/${uuid}` }) }
function fetchSharedReport (uuid) { return request({ url: `/api/reports/share/${uuid}`, auth: false }) }
function deleteRecord (uuid) { return request({ url: `/api/records/${uuid}`, method: 'DELETE' }) }
function fetchFavorites () { return request({ url: '/api/favorites' }) }
function deleteFavorite (id) { return request({ url: `/api/favorites/${id}`, method: 'DELETE' }) }
function checkFavorite (lat, lng) { return request({ url: `/api/favorites/check?latitude=${lat}&longitude=${lng}` }) }
function addFavorite (data) { return request({ url: '/api/favorites', method: 'POST', data }) }
function fetchIndustries () { return request({ url: '/api/industries/active', auth: false }) }

// ── Location ──
function locationSuggest (keyword, city = '') {
  const qs = `keyword=${encodeURIComponent(keyword)}&city=${encodeURIComponent(city)}`
  return request({ url: `/api/location/suggest?${qs}`, auth: false })
}

function locationRegeocode (lng, lat) {
  return request({ url: `/api/location/regeocode?lng=${lng}&lat=${lat}`, auth: false })
}

// ── Analyze ──
/** 发起选址分析请求，解析 SSE text/event-stream 响应 */
function analyzeLocation (payload) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    const token = uni.getStorageSync('token')
    if (token) header['Authorization'] = 'Bearer ' + token
    uni.request({
      url: config.API_BASE_URL + '/api/analyze',
      method: 'POST',
      data: payload,
      header,
      responseType: 'text',
      timeout: 120000,
      success (res) {
        const body = res.data
        // 解析 SSE text/event-stream → 提取 steps 和 final result
        const steps = []
        let result = null
        let recordId = ''
        let sseError = ''
        if (typeof body === 'string') {
          const lines = body.split('\n')
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue
            try {
              const evt = JSON.parse(line.slice(6))
              if (evt.step === 'error') {
                sseError = evt.msg || '分析服务异常'
              } else if (evt.step && evt.msg) {
                steps.push({ step: evt.step, msg: evt.msg })
              }
              if (evt.result && typeof evt.result === 'object') {
                result = evt.result
                recordId = evt.result.record_id || ''
              }
            } catch (e) { /* skip non-JSON SSE lines */ }
          }
        }
        if (res.statusCode === 401) {
          resolve({ ok: false, statusCode: 401, error: '登录已过期，请去「我的」重新登录', steps: [] })
        } else if (res.statusCode === 402) {
          let detail = '余额不足，请充值后重试'
          if (typeof body === 'string') {
            try { const parsed = JSON.parse(body); detail = parsed.detail || detail } catch (e) { detail = body || detail }
          }
          resolve({ ok: false, statusCode: 402, error: detail, steps: [] })
        } else if (res.statusCode >= 500) {
          resolve({ ok: false, statusCode: res.statusCode, error: '分析服务暂不可用，请稍后重试', steps: [] })
        } else if (sseError && !result) {
          resolve({ ok: false, statusCode: res.statusCode, error: sseError, steps })
        } else if (result) {
          resolve({ ok: true, statusCode: res.statusCode, steps, result, recordId, error: '' })
        } else {
          resolve({ ok: false, statusCode: res.statusCode, error: sseError || '分析返回为空，请重试', steps })
        }
      },
      fail (err) {
        const msg = err.errMsg || err.message || ''
        reject(msg.includes('timeout') ? '分析请求超时，请稍后重试' : '分析服务暂不可用，请稍后重试')
      }
    })
  })
}

// ── Config / Pay ──
function fetchUiConfig () { return request({ url: '/api/admin/ui-config', auth: false }) }
function fetchCsQr () { return request({ url: '/api/admin/customer-service-qrcode', auth: false }) }
function fetchSkus () { return request({ url: '/api/user/skus' }) }
function activateCdk (code) { return request({ url: '/api/admin/cdk/activate', method: 'POST', data: { code } }) }
function createPrepay (skuId) { return request({ url: '/api/pay/wechat/prepay', method: 'POST', data: { sku_id: skuId } }) }
function queryOrder (outTradeNo) { return request({ url: `/api/pay/orders/${outTradeNo}` }) }

// ── Health ──
function getHealth () { return request({ url: '/api/health', auth: false }) }

export default {
  request, normalizeError, ensureAnonToken, wechatMiniLogin, bindPhone, phoneLogin,
  fetchProfile, updateProfile, uploadAvatar, fetchRecords, fetchRecordDetail, fetchSharedReport, deleteRecord,
  fetchFavorites, deleteFavorite, checkFavorite, addFavorite, fetchIndustries, locationSuggest, locationRegeocode, analyzeLocation, fetchUiConfig, fetchCsQr, fetchSkus, activateCdk, createPrepay, queryOrder, getHealth
}
