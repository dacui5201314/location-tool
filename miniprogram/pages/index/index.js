const { getHealth, getRecords } = require('../../utils/api')

Page({
  data: {
    loggedIn: false,
    balanceCredits: 0,
    maskedOpenid: '',
    giftNote: '',
    healthResult: '',
    recordsResult: ''
  },

  onShow () {
    const token = wx.getStorageSync('token')
    if (!token) {
      this.setData({ loggedIn: false })
      return
    }

    const user = wx.getStorageSync('user') || {}
    const openid = wx.getStorageSync('wx_mini_openid') || ''
    const giftNote = wx.getStorageSync('gift_note') || ''

    this.setData({
      loggedIn: true,
      balanceCredits: user.balance_credits ?? 0,
      maskedOpenid: openid ? openid.slice(0, 1) + '****' + openid.slice(-3) : '',
      giftNote: giftNote
    })
  },

  async checkHealth () {
    this.setData({ healthResult: '请求中...' })
    try {
      const r = await getHealth()
      if (r.ok) {
        this.setData({ healthResult: '后端正常: ' + JSON.stringify(r.data) })
      } else {
        this.setData({ healthResult: '后端异常 HTTP ' + r.statusCode })
      }
    } catch (err) {
      this.setData({ healthResult: '网络错误' })
    }
  },

  async fetchRecords () {
    this.setData({ recordsResult: '请求中...' })
    try {
      const r = await getRecords(1)
      if (r.ok) {
        const total = r.data?.total ?? 0
        this.setData({ recordsResult: '请求成功，共 ' + total + ' 条记录' })
      } else {
        this.setData({ recordsResult: '请求失败 HTTP ' + r.statusCode })
      }
    } catch (err) {
      this.setData({ recordsResult: '网络错误' })
    }
  },

  handleLogout () {
    wx.clearStorageSync()
    wx.reLaunch({ url: '/pages/login/login' })
  },

  goLogin () {
    wx.reLaunch({ url: '/pages/login/login' })
  }
})
