const { API_BASE_URL } = require('./config')

/**
 * 封装 wx.request，自动拼接 API_BASE_URL。
 * auth=true 时从 storage 取 token 附加 Authorization 头。
 */
function request ({ url, method = 'GET', data = {}, auth = true }) {
  return new Promise((resolve, reject) => {
    const header = { 'Content-Type': 'application/json' }
    if (auth) {
      const token = wx.getStorageSync('token')
      if (token) header['Authorization'] = 'Bearer ' + token
    }

    wx.request({
      url: API_BASE_URL + url,
      method,
      data,
      header,
      success (res) {
        // 保留 statusCode 和后端 detail/message 字段
        resolve({
          ok: res.statusCode >= 200 && res.statusCode < 300,
          statusCode: res.statusCode,
          data: res.data
        })
      },
      fail (err) {
        reject(err)
      }
    })
  })
}

/** 微信小程序登录：wx.login code → /api/auth/wechat/mini */
function wechatMiniLogin (code) {
  return request({ url: '/api/auth/wechat/mini', method: 'POST', data: { code }, auth: false })
}

/** 后端健康检查 */
function getHealth () {
  return request({ url: '/api/health', auth: false })
}

/** 获取当前用户分析记录 */
function getRecords (page = 1) {
  return request({ url: `/api/records?page=${page}&page_size=10` })
}

module.exports = { request, wechatMiniLogin, getHealth, getRecords }
