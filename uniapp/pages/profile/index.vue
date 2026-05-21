<template>
  <view class="profile-page">
    <!-- Top dark section -->
    <view class="top-section">
      <view class="avatar">👤</view>
      <view class="username">{{ loggedIn ? '用户' : '未登录' }}</view>
      <view class="uid" v-if="loggedIn">ID: 000****001</view>
    </view>

    <!-- Stats -->
    <view class="stats-panel">
      <view class="stat-item" v-for="s in stats" :key="s.label">
        <text class="stat-num">{{ s.value }}</text>
        <text class="stat-label">{{ s.label }}</text>
      </view>
    </view>

    <!-- Login / logged-in state -->
    <view class="card" v-if="!loggedIn">
      <view class="card-title">登录后查看更多</view>
      <view class="card-desc">登录即可查看余额、历史报告和 PDF 下载权限</view>
      <button class="login-btn" @tap="onLogin">微信一键登录</button>
    </view>

    <view class="card" v-if="loggedIn">
      <view class="card-title">账户信息</view>
      <view class="info-row"><text class="ilabel">余额</text><text class="ival">3 点</text></view>
      <view class="info-row"><text class="ilabel">报告数</text><text class="ival">12 份</text></view>
      <view class="info-row"><text class="ilabel">收藏</text><text class="ival">3 个</text></view>
    </view>

    <!-- VIP card -->
    <view class="vip-card">
      <view class="vip-header">💎 会员中心</view>
      <view class="vip-desc">开通会员享无限次分析和 PDF 导出</view>
      <button class="vip-btn" @tap="onUpgrade">立即开通</button>
    </view>

    <!-- Menu -->
    <view class="menu-card">
      <view class="menu-item" v-for="m in menuItems" :key="m.label" @tap="m.action">
        <text class="menu-icon">{{ m.icon }}</text>
        <text class="menu-label">{{ m.label }}</text>
        <text class="menu-arrow">›</text>
      </view>
    </view>

    <!-- Footer -->
    <view class="footer">址得选 · AI 选址初筛参考工具</view>
  </view>
</template>

<script>
export default {
  data () {
    return {
      loggedIn: false,
      stats: [
        { value: 3, label: '剩余点数' },
        { value: 12, label: '分析报告' },
        { value: 3, label: '收藏地址' }
      ],
      menuItems: [
        { icon: '💎', label: '会员权益', action: () => uni.showToast({ title: '会员介绍接入中', icon: 'none' }) },
        { icon: '💬', label: '联系客服', action: () => uni.showToast({ title: '客服接入中', icon: 'none' }) }
      ]
    }
  },
  methods: {
    onLogin () {
      uni.showToast({ title: '微信登录接入中', icon: 'none', duration: 2000 })
    },
    onUpgrade () {
      uni.showToast({ title: '会员充值接入中', icon: 'none', duration: 2000 })
    }
  }
}
</script>

<style scoped>
.profile-page { min-height: 100vh; padding-bottom: 60rpx; }
.top-section {
  background: linear-gradient(135deg, #02091d, #071843);
  padding: 60rpx 32rpx 40rpx; text-align: center; color: #fff;
}
.avatar { font-size: 80rpx; margin-bottom: 16rpx; }
.username { font-size: 36rpx; font-weight: 700; }
.uid { font-size: 24rpx; color: rgba(255,255,255,0.6); margin-top: 6rpx; }
.stats-panel {
  display: flex; background: #fff; margin: -30rpx 24rpx 24rpx;
  border-radius: 20rpx; padding: 28rpx 0; box-shadow: 0 4rpx 24rpx rgba(0,0,0,0.06);
}
.stat-item { flex: 1; text-align: center; }
.stat-num { display: block; font-size: 36rpx; font-weight: 800; color: #1e293b; }
.stat-label { display: block; font-size: 22rpx; color: #94a3b8; margin-top: 4rpx; }
.card {
  background: #fff; margin: 0 24rpx 20rpx; border-radius: 20rpx; padding: 28rpx;
  box-shadow: 0 2rpx 16rpx rgba(0,0,0,0.04);
}
.card-title { font-size: 28rpx; font-weight: 700; color: #1e293b; margin-bottom: 10rpx; }
.card-desc { font-size: 26rpx; color: #94a3b8; margin-bottom: 20rpx; }
.login-btn { width: 100%; background: #07c160; color: #fff; border-radius: 14rpx; font-size: 30rpx; font-weight: 600; padding: 22rpx 0; }
.info-row { display: flex; justify-content: space-between; padding: 16rpx 0; border-bottom: 1rpx solid #f1f5f9; }
.ilabel { color: #64748b; font-size: 28rpx; }
.ival { font-size: 28rpx; font-weight: 600; color: #1e293b; }
.vip-card {
  background: linear-gradient(135deg, #1e293b, #0f172a);
  margin: 0 24rpx 20rpx; border-radius: 20rpx; padding: 28rpx; color: #fff;
}
.vip-header { font-size: 28rpx; font-weight: 700; margin-bottom: 8rpx; }
.vip-desc { font-size: 24rpx; color: rgba(255,255,255,0.7); margin-bottom: 20rpx; }
.vip-btn { width: 100%; background: #d6a84f; color: #1e293b; border-radius: 14rpx; font-size: 28rpx; font-weight: 700; padding: 18rpx 0; }
.menu-card { background: #fff; margin: 0 24rpx 24rpx; border-radius: 20rpx; }
.menu-item {
  display: flex; align-items: center; padding: 28rpx; border-bottom: 1rpx solid #f1f5f9;
}
.menu-icon { font-size: 32rpx; margin-right: 16rpx; }
.menu-label { flex: 1; font-size: 28rpx; color: #1e293b; }
.menu-arrow { font-size: 32rpx; color: #cbd5e1; }
.footer { text-align: center; font-size: 22rpx; color: #cbd5e1; padding: 24rpx; }
</style>
