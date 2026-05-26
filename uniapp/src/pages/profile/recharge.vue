<template>
  <view class="recharge-page">
    <!-- Tabs -->
    <view class="tabs">
      <text class="tab" :class="{ active: tab === 'points' }" @tap="tab = 'points'">点数包</text>
      <text class="tab" :class="{ active: tab === 'membership' }" @tap="tab = 'membership'">会员套餐</text>
    </view>

    <!-- Points -->
    <view class="sku-list" v-if="tab === 'points'">
      <view class="sku-item" v-for="s in pointSkus" :key="s.id" @tap="onBuy(s)">
        <view class="sku-left">
          <text class="sku-label">{{ s.label }}</text>
          <text class="sku-desc">{{ s.desc }}</text>
        </view>
        <view class="sku-right">
          <text class="sku-price">¥{{ s.price }}</text>
          <text class="sku-credits">+{{ s.credits }}点</text>
        </view>
      </view>
      <view class="empty" v-if="!pointSkus.length">暂无点数套餐</view>
    </view>

    <!-- Membership -->
    <view class="sku-list" v-if="tab === 'membership'">
      <view class="sku-item" v-for="s in memberSkus" :key="s.id" @tap="onBuy(s)">
        <view class="sku-left">
          <text class="sku-label">{{ s.label }}</text>
          <text class="sku-desc">{{ s.desc || s.duration_days+'天' }}</text>
        </view>
        <view class="sku-right">
          <text class="sku-price">¥{{ s.price }}</text>
        </view>
      </view>
      <view class="empty" v-if="!memberSkus.length">暂无会员套餐</view>
    </view>

    <!-- 客服 -->
    <view class="cs-section" v-if="csQrUrl || csWechat || csPhone">
      <view class="cs-title">联系客服</view>
      <image v-if="csQrUrl" class="cs-qr" :src="csQrFullUrl" mode="aspectFit" @tap="previewCsQr" />
      <text class="cs-line" v-if="csWechat" @tap="copyText(csWechat)">微信：{{ csWechat }}</text>
      <text class="cs-line" v-if="csPhone" @tap="callPhone(csPhone)">电话：{{ csPhone }}</text>
    </view>

    <!-- CDK 入口 -->
    <view class="cdk-entry" @tap="goRedeem">
      <text>已有兑换码？立即激活</text>
    </view>

    <text class="pay-err" v-if="payErr">{{ payErr }}</text>
  </view>
</template>

<script>
import api from '../../utils/api'
import config from '../../utils/config'

export default {
  data () {
    return {
      tab: 'points',
      skus: [],
      csQrUrl: '', csWechat: '', csPhone: '',
      payErr: ''
    }
  },
  computed: {
    pointSkus () { return this.skus.filter(s => s.type !== 'membership') },
    memberSkus () { return this.skus.filter(s => s.type === 'membership') },
    csQrFullUrl () {
      if (!this.csQrUrl) return ''
      return this.csQrUrl.startsWith('/') ? config.API_BASE_URL + this.csQrUrl : this.csQrUrl
    }
  },
  mounted () {
    api.fetchSkus().then(r => {
      if (r.ok && Array.isArray(r.data?.skus)) this.skus = r.data.skus.filter(s => s.visible)
    }).catch(() => {})
    api.fetchCsQr().then(r => { if (r.ok && r.data) this.csQrUrl = r.data.url || '' }).catch(() => {})
    api.fetchUiConfig().then(r => {
      if (r.ok && r.data) { this.csWechat = r.data.cs_wechat || ''; this.csPhone = r.data.cs_phone || '' }
    }).catch(() => {})
  },
  methods: {
    goRedeem () { uni.navigateTo({ url: '/pages/profile/redeem' }) },
    previewCsQr () { if (this.csQrFullUrl) uni.previewImage({ urls: [this.csQrFullUrl] }) },
    copyText (t) { uni.setClipboardData({ data: t, success: () => uni.showToast({ title: '已复制', icon: 'none' }) }) },
    callPhone (p) { uni.makePhoneCall({ phoneNumber: p }) },
    async onBuy (sku) {
      this.payErr = ''
      if (!sku || !sku.id) return
      try {
        const r = await api.createPrepay(sku.id)
        if (r.ok) {
          const pp = r.data; const outTradeNo = pp.out_trade_no
          uni.requestPayment({
            timeStamp: pp.timeStamp, nonceStr: pp.nonceStr,
            package: pp.package, signType: pp.signType || 'RSA', paySign: pp.paySign,
            success: async () => {
              this.payErr = '支付处理中...'
              for (let i = 0; i < 8; i++) {
                await new Promise(resolve => setTimeout(resolve, 2500))
                try {
                  const qr = await api.queryOrder(outTradeNo)
                  if (qr.ok && qr.data && qr.data.status === 'PAID') {
                    this.payErr = ''
                    uni.showToast({ title: '支付成功，已到账', icon: 'success' })
                    return
                  }
                } catch (e) {}
              }
              this.payErr = '支付处理中，请稍后刷新'
            },
            fail: (e) => {
              if (e.errMsg && e.errMsg.indexOf('cancel') >= 0) this.payErr = '支付已取消'
              else this.payErr = '支付失败，请稍后重试'
            }
          })
        } else {
          if (r.statusCode === 503) this.payErr = '支付服务暂不可用'
          else if (r.statusCode === 400 && (r.data?.detail || '').includes('微信')) this.payErr = '请先在微信中登录授权后再支付'
          else this.payErr = r.data?.detail || '支付请求失败'
        }
      } catch (e) { this.payErr = '网络异常' }
    }
  }
}
</script>

<style scoped>
.recharge-page { min-height:100vh; background:linear-gradient(180deg,#eaf2ff 0%,#f2f6ff 42%,#f0f4ff 100%); padding:48rpx 28rpx; }
.tabs { display:flex; background:#f3f7ff; border-radius:14rpx; padding:6rpx; margin-bottom:28rpx; }
.tab { flex:1; text-align:center; font-size:28rpx; font-weight:700; color:#8b99b6; padding:16rpx 0; border-radius:10rpx; }
.tab.active { background:#315bff; color:#fff; }
.sku-list { background:#fff; border-radius:16rpx; padding:0 24rpx; box-shadow:0 4rpx 20rpx rgba(79,119,186,0.06); }
.sku-item { display:flex; justify-content:space-between; align-items:center; padding:24rpx 0; border-bottom:1px solid #f1f5f9; }
.sku-label { font-size:28rpx; font-weight:700; color:#1e293b; } .sku-desc { font-size:24rpx; color:#8b99b6; }
.sku-price { font-size:30rpx; font-weight:800; color:#315bff; } .sku-credits { font-size:24rpx; color:#16a34a; }
.empty { text-align:center; padding:40rpx; font-size:26rpx; color:#94a3b8; background:#fff; border-radius:16rpx; }
.cs-section { margin-top:28rpx; padding:24rpx; background:#fff; border-radius:16rpx; box-shadow:0 4rpx 20rpx rgba(79,119,186,0.06); }
.cs-title { font-size:28rpx; font-weight:700; color:#1e293b; margin-bottom:16rpx; }
.cs-qr { width:200rpx; height:200rpx; display:block; margin:0 auto 16rpx; border-radius:12rpx; }
.cs-line { display:block; font-size:26rpx; color:#315bff; padding:8rpx 0; text-align:center; }
.cdk-entry { text-align:center; padding:28rpx; margin-top:20rpx; background:#f3f7ff; border-radius:14rpx; font-size:26rpx; color:#315bff; font-weight:600; }
.pay-err { display:block; text-align:center; font-size:24rpx; color:#dc2626; margin-top:16rpx; }
</style>
