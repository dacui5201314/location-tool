<template>
  <view class="recharge-page">
    <view class="status-card">
      <view class="status-copy">
        <text class="eyebrow">充值中心</text>
        <text class="status-title">充值中心</text>
        <text class="status-desc">选择套餐，微信支付即时到账</text>
      </view>
      <view class="status-grid">
        <view class="status-cell">
          <text class="status-value">{{ points }}</text>
          <text class="status-label">剩余点数</text>
        </view>
        <view class="status-cell">
          <text class="status-value">{{ memberText }}</text>
          <text class="status-label">会员状态</text>
        </view>
      </view>
    </view>

    <view class="tabs">
      <text class="tab" :class="{ active: tab === 'points' }" @tap="tab = 'points'">点数包</text>
      <text class="tab" :class="{ active: tab === 'membership' }" @tap="tab = 'membership'">会员套餐</text>
    </view>

    <view class="sku-list" v-if="tab === 'points'">
      <view class="sku-item" v-for="s in pointSkus" :key="s.id" :class="{ selected: selectedSku && selectedSku.id === s.id }" @tap="selectSku(s)">
        <view class="sku-left">
          <text class="sku-label">{{ s.label }}</text>
          <text class="sku-desc">{{ s.desc }}</text>
        </view>
        <view class="sku-right">
          <text class="sku-price">¥{{ s.price }}</text>
          <text class="sku-credits">+{{ s.credits }}点</text>
          <view v-if="selectedSku && selectedSku.id === s.id" class="sku-check">✓</view>
        </view>
      </view>
      <view class="empty" v-if="!pointSkus.length">暂无点数套餐，请联系客服</view>
    </view>

    <view class="sku-list" v-if="tab === 'membership'">
      <view class="sku-item" v-for="s in memberSkus" :key="s.id" :class="{ selected: selectedSku && selectedSku.id === s.id }" @tap="selectSku(s)">
        <view class="sku-left">
          <text class="sku-label">{{ s.label }}</text>
          <text class="sku-desc">{{ s.desc || s.duration_days+'天' }}</text>
        </view>
        <view class="sku-right">
          <text class="sku-price">¥{{ s.price }}</text>
          <view v-if="selectedSku && selectedSku.id === s.id" class="sku-check">✓</view>
        </view>
      </view>
      <view class="empty" v-if="!memberSkus.length">暂无会员套餐，请联系客服</view>
    </view>

    <view class="action-card">
      <view class="action-copy">
        <text class="action-title">{{ selectedSku ? selectedSku.label : '请选择套餐' }}</text>
        <text class="action-desc">{{ selectedSku ? selectedSkuDesc : '请选择套餐后发起支付' }}</text>
      </view>
      <button class="pay-btn" :class="{ ready: selectedSku }" :disabled="paying" @tap="onPay">{{ paying ? '支付中...' : (selectedSku ? '微信支付 ¥' + selectedSku.price : '请先选择套餐') }}</button>
    </view>

    <view class="cs-section" @tap="goContact">
      <view class="cs-title">联系客服购买</view>
      <text class="cs-tip">如需提前购买点数或开通会员，请进入客服页查看二维码、微信或电话。</text>
      <button class="cs-btn">进入客服页</button>
    </view>

    <view class="cdk-entry" @tap="goRedeem">
      <text>已有兑换码？立即激活</text>
    </view>

    <text class="pay-err" v-if="payErr">{{ payErr }}</text>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'
import config from '../../utils/config'

export default {
  data () {
    return {
      tab: 'points',
      skus: [],
      selectedSku: null,
      points: 0,
      memberDays: 0,
      memberExpiry: '',
      csQrUrl: '', csWechat: '', csPhone: '',
      payErr: '',
      paying: false
    }
  },
  computed: {
    pointSkus () { return this.skus.filter(s => s.type !== 'membership') },
    memberSkus () { return this.skus.filter(s => s.type === 'membership') },
    memberText () {
      return this.memberDays > 0 ? this.memberDays + '天' : '未开通'
    },
    selectedSkuDesc () {
      if (!this.selectedSku) return ''
      if (this.selectedSku.type === 'membership') {
        return this.selectedSku.desc || ((this.selectedSku.duration_days || 0) + '天会员权益')
      }
      return this.selectedSku.desc || ('购买后增加 ' + (this.selectedSku.credits || 0) + ' 点')
    },
    csQrFullUrl () {
      if (!this.csQrUrl) return ''
      return this.csQrUrl.startsWith('/') ? config.API_BASE_URL + this.csQrUrl : this.csQrUrl
    }
  },
  mounted () {
    this.loadProfile()
    api.fetchSkus().then(r => {
      if (r.ok && Array.isArray(r.data?.skus)) this.skus = r.data.skus.filter(s => s.visible)
    }).catch(() => {})
    api.fetchCsQr().then(r => { if (r.ok && r.data) this.csQrUrl = r.data.url || '' }).catch(() => {})
    api.fetchUiConfig().then(r => {
      if (r.ok && r.data) { this.csWechat = r.data.cs_wechat || ''; this.csPhone = r.data.cs_phone || '' }
    }).catch(() => {})
  },
  methods: {
    async loadProfile () {
      const user = auth.getUser() || {}
      this.points = user.balance_credits ?? 0
      this.memberDays = user.membership_days_left || 0
      this.memberExpiry = user.membership_expiry || ''
      try {
        const r = await api.fetchProfile()
        if (r.ok && r.data) {
          const p = r.data
          this.points = p.points ?? (p.user && p.user.balance_credits) ?? this.points
          this.memberDays = p.membership_days_left ?? this.memberDays
          this.memberExpiry = p.membership_expiry || this.memberExpiry
        }
      } catch (e) {}
    },
    goRedeem () { uni.navigateTo({ url: '/pages/profile/redeem' }) },
    goContact () { uni.navigateTo({ url: '/pages/profile/contact' }) },
    previewCsQr () { if (this.csQrFullUrl) uni.previewImage({ urls: [this.csQrFullUrl] }) },
    copyText (t) { uni.setClipboardData({ data: t, success: () => uni.showToast({ title: '已复制', icon: 'none' }) }) },
    callPhone (p) { uni.makePhoneCall({ phoneNumber: p }) },
    selectSku (sku) {
      this.selectedSku = sku
      this.payErr = ''
    },
    async onPay () {
      if (this.paying || !this.selectedSku) return
      this.paying = true
      this.payErr = ''
      try {
        const r = await api.createPrepay(this.selectedSku.id)
        if (!r.ok) {
          const msg = (r.data && (r.data.detail || r.data.error)) || '创建订单失败'
          if (msg.includes('微信中登录')) {
            this.payErr = '请先在微信中授权登录后再支付'
          } else if (msg.includes('支付服务暂不可用')) {
            this.payErr = '支付服务未配置，请联系管理员'
          } else {
            this.payErr = msg
          }
          return
        }
        const pp = r.data
        // 拉起微信支付
        try {
          await new Promise((resolve, reject) => {
            uni.requestPayment({
              provider: 'wxpay',
              timeStamp: String(pp.timeStamp || ''),
              nonceStr: pp.nonceStr || '',
              package: pp.package || '',
              signType: pp.signType || 'RSA',
              paySign: pp.paySign || '',
              success: resolve,
              fail: reject
            })
          })
        } catch (payErr) {
          if (payErr && payErr.errMsg && payErr.errMsg.includes('cancel')) {
            this.payErr = '支付已取消'
          } else {
            this.payErr = (payErr && (payErr.errMsg || payErr.message)) || '支付失败'
          }
          return
        }
        // requestPayment 成功 → 轮询确认订单已到账
        const outTradeNo = pp.out_trade_no || ''
        if (!outTradeNo) {
          this.payErr = '支付确认中，请稍后刷新或联系客服'
          return
        }
        let paid = false
        for (let i = 0; i < 6; i++) {
          await new Promise(r => setTimeout(r, 1500))
          try {
            const qr = await api.queryOrder(outTradeNo)
            if (qr.ok && qr.data && qr.data.status === 'PAID') {
              paid = true
              break
            }
          } catch (e) {
            // queryOrder 网络异常不中断轮询
          }
        }
        if (paid) {
          uni.showToast({ title: '支付成功', icon: 'success' })
          this.selectedSku = null
          try {
            await this.loadProfile()
          } catch (e) {
            // loadProfile 失败不影响已确认的支付结果
            this.payErr = '支付成功，资料刷新失败，请稍后下拉刷新'
          }
        } else {
          this.payErr = '支付确认中，请稍后刷新'
        }
      } catch (e) {
        this.payErr = (e && (e.errMsg || e.message)) || '支付失败'
      } finally {
        this.paying = false
      }
    }
  }
}
</script>

<style scoped>
.recharge-page { min-height:100vh; background:linear-gradient(180deg,#eef4ff 0%,#e8eef7 42%,#dce4f2 100%); padding:32rpx 28rpx 56rpx; padding-bottom:calc(56rpx + env(safe-area-inset-bottom)); box-sizing:border-box; }
.status-card { background:linear-gradient(135deg,#0b3fbd,#172a8d); border-radius:24rpx; padding:30rpx; color:#fff; box-shadow:0 14rpx 34rpx rgba(21,31,143,0.20); margin-bottom:24rpx; }
.eyebrow { display:block; font-size:23rpx; color:rgba(255,255,255,0.70); font-weight:800; }
.status-title { display:block; font-size:40rpx; line-height:1.2; font-weight:900; margin-top:8rpx; }
.status-desc { display:block; font-size:26rpx; line-height:1.55; color:rgba(255,255,255,0.80); margin-top:10rpx; }
.status-grid { display:flex; gap:16rpx; margin-top:26rpx; }
.status-cell { flex:1; background:rgba(255,255,255,0.12); border:1rpx solid rgba(255,255,255,0.18); border-radius:16rpx; padding:18rpx; }
.status-value { display:block; font-size:32rpx; font-weight:900; }
.status-label { display:block; font-size:23rpx; color:rgba(255,255,255,0.72); margin-top:6rpx; }
.tabs { display:flex; background:#f3f7ff; border-radius:14rpx; padding:6rpx; margin-bottom:22rpx; border:1rpx solid rgba(219,230,255,0.92); }
.tab { flex:1; text-align:center; font-size:28rpx; font-weight:800; color:#8b99b6; padding:16rpx 0; border-radius:10rpx; }
.tab.active { background:#315bff; color:#fff; box-shadow:0 8rpx 18rpx rgba(49,91,255,0.16); }
.sku-list { background:#fff; border-radius:20rpx; padding:0 24rpx; box-shadow:0 12rpx 28rpx rgba(79,119,186,0.09); border:1rpx solid rgba(219,230,255,0.92); }
.sku-item { display:flex; justify-content:space-between; align-items:center; padding:26rpx 0; border-bottom:1px solid #f1f5f9; }
.sku-item:last-child { border-bottom:0; }
.sku-item.selected .sku-label { color:#315bff; }
.sku-left { min-width:0; flex:1; padding-right:20rpx; }
.sku-label { display:block; font-size:29rpx; font-weight:800; color:#1e293b; line-height:1.35; }
.sku-desc { display:block; font-size:25rpx; color:#64748b; line-height:1.45; margin-top:6rpx; }
.sku-right { flex-shrink:0; min-width:144rpx; text-align:right; }
.sku-price { display:block; font-size:30rpx; font-weight:900; color:#315bff; }
.sku-credits { display:block; font-size:24rpx; color:#16a34a; margin-top:4rpx; }
.sku-state { display:inline-block; font-size:22rpx; color:#92400e; background:#fff7ed; border-radius:999rpx; padding:5rpx 12rpx; margin-top:8rpx; }
.empty { text-align:center; padding:44rpx 28rpx; font-size:26rpx; line-height:1.45; color:#64748b; background:#fff; border-radius:18rpx; border:1rpx solid rgba(219,230,255,0.92); }
.action-card { margin-top:24rpx; padding:26rpx; background:#fff; border-radius:20rpx; box-shadow:0 12rpx 28rpx rgba(79,119,186,0.09); border:1rpx solid rgba(219,230,255,0.92); }
.action-title { display:block; font-size:28rpx; color:#1e293b; font-weight:800; }
.action-desc { display:block; font-size:25rpx; color:#64748b; line-height:1.5; margin-top:8rpx; }
.pay-btn { width:100%; height:86rpx; line-height:86rpx; margin-top:22rpx; border-radius:16rpx; background:#eef2f7; color:#64748b; font-size:28rpx; font-weight:900; }
.pay-btn::after { border:none; }
.pay-btn.ready { background:linear-gradient(135deg,#ffe8b0 0%,#f8c861 54%,#dba640 100%); color:#4a2600; box-shadow:0 14rpx 26rpx rgba(248,200,97,0.20); }
.sku-check { font-size:24rpx; font-weight:900; color:#16a34a; margin-left:8rpx; }
.cs-section { margin-top:28rpx; padding:26rpx; background:linear-gradient(180deg,#ffffff,#f8fbff); border-radius:20rpx; box-shadow:0 12rpx 28rpx rgba(79,119,186,0.09); border:1rpx solid rgba(219,230,255,0.92); text-align:center; }
.cs-title { display:block; font-size:30rpx; font-weight:900; color:#1e293b; margin-bottom:10rpx; }
.cs-qr { width:200rpx; height:200rpx; display:block; margin:0 auto 16rpx; border-radius:12rpx; }
.cs-line { display:block; font-size:26rpx; color:#315bff; padding:8rpx 0; text-align:center; }
.cs-tip { display:block; text-align:center; font-size:25rpx; color:#64748b; line-height:1.5; margin-top:10rpx; }
.cs-btn { width:280rpx; height:68rpx; line-height:68rpx; margin:22rpx auto 0; padding:0; border-radius:999rpx; background:linear-gradient(135deg,#ffe8b0 0%,#f8c861 54%,#dba640 100%); color:#4a2600; font-size:26rpx; font-weight:900; box-shadow:0 14rpx 26rpx rgba(248,200,97,0.20),inset 0 1rpx 0 rgba(255,255,255,0.58); }
.cs-btn::after { border:none; }
.cdk-entry { text-align:center; padding:28rpx; margin-top:20rpx; background:#f3f7ff; border-radius:16rpx; font-size:27rpx; color:#315bff; font-weight:900; border:1rpx solid rgba(219,230,255,0.92); }
.pay-err { display:block; text-align:center; font-size:24rpx; color:#dc2626; margin-top:16rpx; }
</style>
