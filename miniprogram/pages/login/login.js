const { wechatMiniLogin } = require('../../utils/api')

Page({
  data: {
    loading: false,
    errorMsg: ''
  },

  handleLogin () {
    this.setData({ loading: true, errorMsg: '' })

    wx.login({
      success: async (loginRes) => {
        if (!loginRes.code) {
          this.setData({ loading: false, errorMsg: 'wx.login 未返回 code，请重试' })
          return
        }

        try {
          const result = await wechatMiniLogin(loginRes.code)

          if (result.ok) {
            const { token, user, gift_note, wx_mini_openid, wx_unionid } = result.data
            wx.setStorageSync('token', token)
            wx.setStorageSync('user', user)
            if (gift_note) wx.setStorageSync('gift_note', gift_note)
            if (wx_mini_openid) wx.setStorageSync('wx_mini_openid', wx_mini_openid)
            if (wx_unionid) wx.setStorageSync('wx_unionid', wx_unionid)

            wx.switchTab({ url: '/pages/profile/profile' })
          } else {
            const statusCode = result.statusCode
            const detail = result.data?.detail || ''
            let msg = '登录失败，请稍后重试'
            if (statusCode === 503) {
              msg = '服务端未配置小程序，请联系管理员'
            } else if (statusCode === 400) {
              msg = '授权过期或 code 无效，请重试'
            } else if (statusCode === 409) {
              msg = '微信身份已绑定其他账号，请联系客服'
            }
            this.setData({ loading: false, errorMsg: msg })
          }
        } catch (err) {
          console.error('登录请求失败', err)
          this.setData({
            loading: false,
            errorMsg: '网络请求失败，请检查网络或域名配置'
          })
        }
      },
      fail (err) {
        console.error('wx.login 失败', err)
        this.setData({ loading: false, errorMsg: '微信登录接口调用失败' })
      }
    })
  }
})
