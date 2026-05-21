Page({
  startAnalysis () {
    wx.showModal({
      title: '提示',
      content: 'Web 端已支持完整分析功能。移动端分析功能开发中，请使用浏览器访问。',
      showCancel: false
    })
  },

  viewReports () {
    const token = wx.getStorageSync('token')
    if (token) {
      wx.switchTab({ url: '/pages/profile/profile' })
    } else {
      wx.switchTab({ url: '/pages/profile/profile' })
      // profile 页会自动显示未登录态 + 登录按钮
    }
  }
})
