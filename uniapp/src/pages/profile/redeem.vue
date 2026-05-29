<template>
  <view class="redeem-page">
    <view class="card">
      <text class="title">激活兑换码</text>
      <text class="desc">输入兑换码，点数即时到账</text>
      <input class="field" v-model="code" placeholder="请输入兑换码" />
      <button class="btn" :disabled="loading || !code.trim()" @tap="onRedeem">
        {{ loading ? '激活中...' : '立即激活' }}
      </button>
      <view class="result" v-if="resultMsg">
        <text class="result-text" :class="resultOk ? 'ok' : 'err'">{{ resultMsg }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'

export default {
  data () { return { code: '', loading: false, resultMsg: '', resultOk: false } },
  onShow () {
    if (!auth.isLoggedIn()) this.promptLogin()
  },
  methods: {
    promptLogin () {
      uni.showModal({
        title: '请先登录',
        content: '登录后才能使用兑换码激活点数',
        confirmText: '去登录',
        cancelText: '稍后',
        success: (res) => {
          if (res.confirm) uni.navigateTo({ url: '/pages/profile/login' })
        }
      })
    },
    async onRedeem () {
      if (!this.code.trim()) return
      if (!auth.isLoggedIn()) {
        this.resultOk = false
        this.resultMsg = '请先登录后再激活兑换码'
        this.promptLogin()
        return
      }
      this.loading = true; this.resultMsg = ''
      try {
        const r = await api.activateCdk(this.code.trim().toUpperCase())
        if (r.ok) {
          this.resultOk = true
          this.resultMsg = `兑换成功，+${r.data.credits_added} 点已到账`
          this.code = ''
          // 刷新后端点数到本地
          try {
            const p = await api.fetchProfile()
            if (p.ok && p.data) auth.setUser(p.data.user || p.data)
          } catch (e) {}
          setTimeout(() => uni.navigateBack({ delta: 1 }), 1200)
        } else {
          this.resultOk = false
          if (r.statusCode === 404) this.resultMsg = '兑换码不存在'
          else if (r.statusCode === 429) this.resultMsg = '尝试次数过多，请稍后重试'
          else if (r.statusCode === 401 || r.statusCode === 403 || /Bearer|Token|token|认证|登录/.test(String(r.data?.detail || ''))) {
            this.resultMsg = '请先登录后再激活兑换码'
            this.promptLogin()
          }
          else this.resultMsg = r.data?.detail || '兑换失败'
        }
      } catch (e) { this.resultOk = false; this.resultMsg = '网络异常，请重试' }
      finally { this.loading = false }
    }
  }
}
</script>

<style scoped>
.redeem-page { min-height:100vh; background:linear-gradient(180deg,#eef4ff 0%,#e8eef7 42%,#dce4f2 100%); padding:48rpx 28rpx calc(72rpx + env(safe-area-inset-bottom)); box-sizing:border-box; }
.card { position:relative; background:#fff; border-radius:24rpx; padding:44rpx 32rpx 36rpx; box-shadow:0 12rpx 28rpx rgba(79,119,186,0.10); border:1rpx solid rgba(219,230,255,0.92); overflow:hidden; }
.card::before { content:''; position:absolute; left:0; top:0; right:0; height:8rpx; background:linear-gradient(90deg,#315bff,#0b3fbd 58%,#f8c861); }
.title { display:block; font-size:36rpx; line-height:1.25; font-weight:900; color:#17244e; text-align:center; }
.desc { display:block; font-size:26rpx; line-height:1.45; color:#64748b; margin-top:10rpx; margin-bottom:36rpx; text-align:center; }
.field { width:100%; height:88rpx; line-height:88rpx; border:1rpx solid #d6e0f5; border-radius:16rpx; padding:0 22rpx; font-size:29rpx; box-sizing:border-box; letter-spacing:2rpx; text-align:center; background:#fbfdff; color:#17244e; }
.btn { width:100%; height:88rpx; line-height:88rpx; background:linear-gradient(135deg,#315bff,#0b3fbd); color:#fff; border-radius:16rpx; font-size:29rpx; font-weight:900; padding:0; margin-top:24rpx; box-shadow:0 14rpx 24rpx rgba(49,91,255,0.18); }
.btn::after { border:none; }
.btn[disabled] { background:#eef2f7; color:#94a3b8; box-shadow:none; opacity:1; }
.result { margin-top:20rpx; text-align:center; }
.result-text { font-size:26rpx; line-height:1.45; } .result-text.ok { color:#16a34a; } .result-text.err { color:#dc2626; }
</style>
