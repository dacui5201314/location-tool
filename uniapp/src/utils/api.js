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
          resolve({ ok: false, statusCode: res.statusCode, error: '后端服务异常，请稍后重试', steps: [] })
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
        reject(msg.includes('timeout') ? '请求超时，请确认后端服务可访问' : '后端服务未连接，请确认 http://127.0.0.1:8000/api/health 可访问')
      }
    })
  })
}

// ── Health ──
function getHealth () { return request({ url: '/api/health', auth: false }) }

export default {
  request, normalizeError, ensureAnonToken, wechatMiniLogin, bindPhone,
  fetchProfile, fetchRecords, fetchRecordDetail, deleteRecord,
  fetchFavorites, deleteFavorite, fetchIndustries, locationSuggest, locationRegeocode, analyzeLocation, getHealth
}
