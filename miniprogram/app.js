App({
  onLaunch () {
    // 检查是否已有登录态
    const token = wx.getStorageSync('token')
    if (token) {
      // 已有 token，直接跳首页
      wx.reLaunch({ url: '/pages/index/index' })
    }
    // 无 token 则留在 login 页（app.json 默认首页）
  }
})
