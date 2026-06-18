import config from './config'

// ── 内部封装 ──
function request ({ url, method = 'GET', data = {}, auth = true, header: extraHeader = {} }) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json', ...extraHeader }
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
        // ★ Global 401 handler: clear expired token so user is prompted to re-login
        if (res.statusCode === 401 && auth) {
          uni.removeStorageSync('token')
        }
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
/** 匿名设备 token（Web 兼容降级） — 首次启动生成随机设备ID，持久化复用 */
function ensureAnonToken () {
  let deviceId = uni.getStorageSync('_zdx_device_id')
  if (!deviceId) {
    deviceId = 'uni_' + Date.now() + '_' + Math.random().toString(36).slice(2, 10)
    uni.setStorageSync('_zdx_device_id', deviceId)
  }
  return request({ url: '/api/auth/token?device_id=' + encodeURIComponent(deviceId), auth: false })
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
function fetchSharedReport (token) { return request({ url: `/api/reports/share/${token}`, auth: false }) }
function createShareToken (uuid) { return request({ url: `/api/records/${uuid}/share-token`, method: 'POST' }) }
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
// ── 响应体归一化：真机 uni.request responseType:'text' 可能返回 ArrayBuffer 或 object ──
function _toTextBody (data) {
  if (typeof data === 'string') return data
  if (data instanceof ArrayBuffer) {
    // 微信真机可能返回 ArrayBuffer；手写 UTF-8 解码兜底（TextDecoder 不可用时）
    try {
      if (typeof TextDecoder !== 'undefined') return new TextDecoder('utf-8').decode(data)
    } catch (e) { /* fall through */ }
    const arr = new Uint8Array(data)
    let str = ''
    let i = 0
    while (i < arr.length) {
      const b = arr[i++]
      if (b < 0x80) { str += String.fromCharCode(b) }
      else if (b >= 0xC0 && b < 0xE0) { str += String.fromCharCode(((b & 0x1F) << 6) | (arr[i++] & 0x3F)) }
      else if (b >= 0xE0 && b < 0xF0) { str += String.fromCharCode(((b & 0x0F) << 12) | ((arr[i++] & 0x3F) << 6) | (arr[i++] & 0x3F)) }
      else { i += (b >= 0xF0 ? 3 : 0) } // 4-byte skip for basic BMP compatibility
    }
    return str
  }
  if (typeof data === 'object') {
    try { return JSON.stringify(data) } catch (e) { return '' }
  }
  return String(data || '')
}

function _parseAnalyzeBody (bodyText) {
  const steps = []
  let result = null
  let recordId = ''
  let sseError = ''
  let detail = ''
  // P0-A 结构化错误字段
  let sseRequestId = ''
  let sseErrorStage = ''
  let sseBillingSource = ''
  let sseBillingStatus = ''  // not_charged / refund_pending / refunded / member_no_charge / unknown

  if (!bodyText) return { steps, result, recordId, sseError, detail,
    sseRequestId, sseErrorStage, sseBillingSource, sseBillingStatus }

  // 尝试直接 JSON parse（非 SSE 错误响应如 402 会返回纯 JSON）
  if (bodyText.trim().startsWith('{')) {
    try {
      const obj = JSON.parse(bodyText)
      detail = obj.detail || ''
      if (obj.result && typeof obj.result === 'object') {
        result = obj.result
        recordId = obj.result.record_id || ''
      }
      if (obj.step && obj.msg) {
        if (obj.step === 'error') {
          sseError = obj.msg
          sseRequestId = obj.request_id || ''
          sseErrorStage = obj.error_stage || ''
          sseBillingSource = obj.billing_source || ''
          if (obj.billing_status) sseBillingStatus = obj.billing_status
          else if (typeof obj.refunded === 'boolean') sseBillingStatus = obj.refunded ? 'refunded' : 'unknown'
        } else {
          steps.push({ step: obj.step, msg: obj.msg })
        }
      }
      if (detail && !result && steps.length === 0 && !sseError) {
        return { steps, result, recordId, sseError, detail,
          sseRequestId, sseErrorStage, sseBillingSource, sseBillingStatus }
      }
    } catch (e) { /* 不是合法 JSON，继续 SSE 解析 */ }
  }

  // SSE text/event-stream 解析
  const lines = bodyText.split('\n')
  for (const line of lines) {
    if (!line.startsWith('data: ')) continue
    try {
      const evt = JSON.parse(line.slice(6))
      if (evt.step === 'error') {
        sseError = evt.msg || '分析服务异常'
        sseRequestId = evt.request_id || ''
        sseErrorStage = evt.error_stage || ''
        sseBillingSource = evt.billing_source || ''
        if (evt.billing_status) sseBillingStatus = evt.billing_status
        else if (typeof evt.refunded === 'boolean') sseBillingStatus = evt.refunded ? 'refunded' : 'unknown'
      } else if (typeof evt.step === 'number' && evt.msg) {
        steps.push({ step: evt.step, msg: evt.msg })
      }
      if (evt.result && typeof evt.result === 'object') {
        result = evt.result
        recordId = evt.result.record_id || ''
      }
    } catch (e) { /* skip non-JSON SSE lines */ }
  }

  return { steps, result, recordId, sseError, detail,
    sseRequestId, sseErrorStage, sseBillingSource, sseBillingStatus }
}

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
        const bodyText = _toTextBody(res.data)
        const { steps, result, recordId, sseError, detail,
          sseRequestId, sseErrorStage, sseBillingSource, sseBillingStatus } = _parseAnalyzeBody(bodyText)

        if (res.statusCode === 401) {
          resolve({ ok: false, statusCode: 401, error: '登录已过期，请去「我的」重新登录', steps: [] })
        } else if (res.statusCode === 422) {
          let msg = '分析参数校验失败'
          try {
            const d = JSON.parse(bodyText || '{}').detail
            if (Array.isArray(d) && d.length) {
              const parts = d.slice(0, 3).map(e => {
                const loc = (e.loc || []).join('.')
                const m = e.msg || ''
                const t = e.type || ''
                const inp = e.input !== undefined ? ' input=' + JSON.stringify(e.input).slice(0, 40) : ''
                return loc + (m ? ' - ' + m : '') + (t ? ' (' + t + ')' : '') + inp
              })
              msg = '分析参数校验失败：' + parts.join('; ')
              if (process.env.NODE_ENV !== 'production') console.log('[422 Detail]', JSON.stringify(d.slice(0, 3)))
            } else if (typeof d === 'string') {
              msg = '分析参数校验失败：' + d
            }
          } catch (e) { /* keep default msg */ }
          resolve({ ok: false, statusCode: 422, error: msg, steps: [] })
        } else if (res.statusCode === 402) {
          const d = detail || '余额不足，请充值后重试'
          resolve({ ok: false, statusCode: 402, error: d, steps: [] })
        } else if (sseError && !result) {
          resolve({ ok: false, statusCode: res.statusCode, error: sseError, steps,
            requestId: sseRequestId, errorStage: sseErrorStage,
            billingSource: sseBillingSource, billingStatus: sseBillingStatus })
        } else if (res.statusCode >= 500) {
          resolve({ ok: false, statusCode: res.statusCode, error: '分析服务暂不可用，请稍后重试', steps: [] })
        } else if (result) {
          resolve({ ok: true, statusCode: res.statusCode, steps, result, recordId, error: '' })
        } else {
          resolve({ ok: false, statusCode: res.statusCode, error: sseError || '分析返回为空，请重试', steps,
            requestId: sseRequestId, errorStage: sseErrorStage,
            billingSource: sseBillingSource, billingStatus: sseBillingStatus })
        }
      },
      fail (err) {
        const msg = err.errMsg || err.message || ''
        reject(msg.includes('timeout') ? '分析请求超时，请稍后重试' : (msg || '分析服务暂不可用，请稍后重试'))
      }
    })
  })
}

// ── Config / Pay ──
function fetchUiConfig () { return request({ url: '/api/admin/ui-config', auth: false }) }
function fetchShareConfig () { return request({ url: '/api/admin/share-config/public', auth: false }) }
function fetchCsQr () { return request({ url: '/api/admin/customer-service-qrcode', auth: false }) }
function fetchSkus () { return request({ url: '/api/user/skus' }) }
function activateCdk (code) { return request({ url: '/api/admin/cdk/activate', method: 'POST', data: { code } }) }
function refreshWxLogin () {
  return new Promise((resolve) => {
    uni.login({
      success: (res) => {
        if (res.code) {
          wechatMiniLogin(res.code).then(r => resolve(r)).catch(() => resolve({ ok: false, data: { detail: '微信登录态刷新失败' } }))
        } else {
          resolve({ ok: false, data: { detail: '微信登录态刷新失败' } })
        }
      },
      fail: () => resolve({ ok: false, data: { detail: '微信登录态刷新失败' } })
    })
  })
}
function createVirtualPrepay (skuId) { return request({ url: '/api/virtual-pay/prepay', method: 'POST', data: { sku_id: skuId } }) }
function payExistingOrder (orderNo) { return request({ url: `/api/virtual-pay/pay-existing/${orderNo}`, method: 'POST' }) }
function queryVirtualOrder (orderNo) { return request({ url: `/api/virtual-pay/order/${orderNo}` }) }
function reconcileVirtualOrder (orderNo) { return request({ url: `/api/virtual-pay/reconcile/${orderNo}`, method: 'POST' }) }
function refundRequestVirtual (orderNo) { return request({ url: `/api/virtual-pay/refund-request/${orderNo}`, method: 'POST' }) }
function fetchMyOrders () { return request({ url: '/api/user/orders' }) }
function submitFeedback (content, contact) {
  return request({
    url: '/api/feedback',
    method: 'POST',
    header: { 'Content-Type': 'application/x-www-form-urlencoded' },
    data: { content, contact }
  })
}

// ── Health ──
function getHealth () { return request({ url: '/api/health', auth: false }) }

export default {
  request, normalizeError, ensureAnonToken, wechatMiniLogin, refreshWxLogin, bindPhone, phoneLogin,
  fetchProfile, updateProfile, uploadAvatar, fetchRecords, fetchRecordDetail, fetchSharedReport, createShareToken, deleteRecord,
  fetchFavorites, deleteFavorite, checkFavorite, addFavorite, fetchIndustries, locationSuggest, locationRegeocode, analyzeLocation, fetchUiConfig, fetchShareConfig, fetchCsQr, fetchSkus, activateCdk, fetchMyOrders, createVirtualPrepay, payExistingOrder, queryVirtualOrder, reconcileVirtualOrder, refundRequestVirtual, submitFeedback, getHealth
}
