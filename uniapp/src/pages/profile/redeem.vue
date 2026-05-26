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

export default {
  data () { return { code: '', loading: false, resultMsg: '', resultOk: false } },
  methods: {
    async onRedeem () {
      if (!this.code.trim()) return
      this.loading = true; this.resultMsg = ''
      try {
        const r = await api.activateCdk(this.code.trim().toUpperCase())
        if (r.ok) {
          this.resultOk = true
          this.resultMsg = `兑换成功，+${r.data.credits_added} 点已到账`
          this.code = ''
        } else {
          this.resultOk = false
          if (r.statusCode === 404) this.resultMsg = '兑换码不存在'
          else if (r.statusCode === 429) this.resultMsg = '尝试次数过多，请稍后重试'
          else this.resultMsg = r.data?.detail || '兑换失败'
        }
      } catch (e) { this.resultOk = false; this.resultMsg = '网络异常，请重试' }
      finally { this.loading = false }
    }
  }
}
</script>

<style scoped>
.redeem-page { min-height:100vh; background:linear-gradient(180deg,#eaf2ff 0%,#f2f6ff 42%,#f0f4ff 100%); padding:48rpx 32rpx; }
.card { background:#fff; border-radius:20rpx; padding:40rpx 32rpx; box-shadow:0 8rpx 30rpx rgba(79,119,186,0.08); }
.title { display:block; font-size:34rpx; font-weight:800; color:#17244e; }
.desc { display:block; font-size:26rpx; color:#8b99b6; margin-top:8rpx; margin-bottom:32rpx; }
.field { width:100%; border:1px solid #d1d5db; border-radius:14rpx; padding:20rpx 18rpx; font-size:30rpx; box-sizing:border-box; letter-spacing:4rpx; }
.btn { width:100%; background:#0f172a; color:#fff; border-radius:14rpx; font-size:30rpx; font-weight:700; padding:24rpx 0; margin-top:24rpx; }
.btn[disabled] { opacity:0.35; }
.result { margin-top:20rpx; text-align:center; }
.result-text { font-size:26rpx; } .result-text.ok { color:#16a34a; } .result-text.err { color:#dc2626; }
</style>
