<template>
  <view class="contact-page">
    <view class="hero-card">
      <text class="eyebrow">专属服务</text>
      <text class="title">联系客服</text>
      <text class="desc">购买点数、会员开通、售后问题，可通过以下真实入口联系运营人员。</text>
    </view>

    <view class="qr-card" v-if="csQrFullUrl">
      <view class="qr-head">
        <text class="qr-title">微信客服二维码</text>
        <text class="qr-sub">点击二维码可放大查看</text>
      </view>
      <image class="qr-img" :src="csQrFullUrl" mode="aspectFit" @tap="previewQr" />
      <button class="primary-btn" @tap="previewQr">查看二维码</button>
    </view>

    <view class="contact-card">
      <view class="contact-row" v-if="csWechat" @tap="copyText(csWechat)">
        <view class="ci">微</view>
        <view class="cb">
          <text class="cl">客服微信</text>
          <text class="cv">{{ csWechat }}</text>
        </view>
        <text class="ca">复制</text>
      </view>
      <view class="contact-row" v-if="csPhone" @tap="callPhone(csPhone)">
        <view class="ci phone">电</view>
        <view class="cb">
          <text class="cl">客服电话</text>
          <text class="cv">{{ csPhone }}</text>
        </view>
        <text class="ca">拨打</text>
      </view>
      <view class="empty" v-if="!csQrFullUrl && !csWechat && !csPhone && loaded">
        <text class="empty-title">客服信息暂未配置</text>
        <text class="empty-desc">请稍后重试，或返回上一页查看其他服务入口。</text>
      </view>
      <view class="loading" v-if="!loaded">
        <text>加载客服信息...</text>
      </view>
    </view>

    <view class="tips-card">
      <text class="tips-title">联系时建议说明</text>
      <text class="tip">需要购买点数或会员套餐</text>
      <text class="tip">需要处理兑换码、报告或账号问题</text>
      <text class="tip">已经生成报告，需要人工协助核对</text>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import config from '../../utils/config'

export default {
  data () {
    return {
      loaded: false,
      csQrUrl: '',
      csWechat: '',
      csPhone: ''
    }
  },
  computed: {
    csQrFullUrl () {
      if (!this.csQrUrl) return ''
      return this.csQrUrl.startsWith('/') ? config.API_BASE_URL + this.csQrUrl : this.csQrUrl
    }
  },
  onShow () {
    this.loadContact()
  },
  methods: {
    async loadContact () {
      this.loaded = false
      try {
        const [qr, cfg] = await Promise.all([
          api.fetchCsQr().catch(() => null),
          api.fetchUiConfig().catch(() => null)
        ])
        if (qr && qr.ok && qr.data) this.csQrUrl = qr.data.url || ''
        if (cfg && cfg.ok && cfg.data) {
          this.csWechat = cfg.data.cs_wechat || ''
          this.csPhone = cfg.data.cs_phone || ''
        }
      } finally {
        this.loaded = true
      }
    },
    previewQr () {
      if (this.csQrFullUrl) uni.previewImage({ urls: [this.csQrFullUrl] })
    },
    copyText (text) {
      uni.setClipboardData({ data: text, success: () => uni.showToast({ title: '已复制', icon: 'none' }) })
    },
    callPhone (phone) {
      uni.makePhoneCall({ phoneNumber: phone })
    }
  }
}
</script>

<style scoped>
.contact-page { min-height:100vh; background:linear-gradient(180deg,#dce4f2,#edf3ff 46%,#dce4f2); padding:32rpx 28rpx calc(56rpx + env(safe-area-inset-bottom)); box-sizing:border-box; }
.hero-card { background:radial-gradient(circle at 82% 28%,rgba(248,200,97,0.22),transparent 26%),linear-gradient(135deg,#0b3fbd,#151f8f 58%,#5b3fd9); border-radius:26rpx; padding:34rpx 30rpx; color:#fff; box-shadow:0 18rpx 42rpx rgba(21,31,143,0.24),inset 0 1rpx 0 rgba(248,200,97,0.20); }
.eyebrow { display:block; font-size:23rpx; color:rgba(255,255,255,0.70); font-weight:800; }
.title { display:block; font-size:42rpx; line-height:1.2; font-weight:900; margin-top:8rpx; }
.desc { display:block; font-size:26rpx; line-height:1.55; color:rgba(255,255,255,0.80); margin-top:12rpx; }
.qr-card,.contact-card,.tips-card { background:rgba(255,255,255,0.96); border:1rpx solid rgba(219,230,255,0.92); border-radius:24rpx; padding:28rpx; margin-top:24rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.10); }
.qr-head { text-align:center; margin-bottom:22rpx; }
.qr-title { display:block; font-size:31rpx; font-weight:900; color:#17244e; }
.qr-sub { display:block; font-size:24rpx; color:#8b99b6; margin-top:8rpx; }
.qr-img { width:360rpx; height:360rpx; margin:0 auto; display:block; border:1rpx solid #d6e0f5; border-radius:20rpx; background:#fff; }
.primary-btn { width:320rpx; height:72rpx; line-height:72rpx; margin:24rpx auto 0; padding:0; border-radius:999rpx; background:linear-gradient(135deg,#ffe8b0 0%,#f8c861 54%,#dba640 100%); color:#4a2600; font-size:27rpx; font-weight:900; box-shadow:0 16rpx 30rpx rgba(248,200,97,0.22),inset 0 1rpx 0 rgba(255,255,255,0.58); }
.primary-btn::after { border:none; }
.contact-row { display:flex; align-items:center; padding:22rpx 0; border-bottom:1rpx solid rgba(219,230,255,0.78); }
.contact-row:last-child { border-bottom:none; }
.ci { width:58rpx; height:58rpx; line-height:58rpx; border-radius:18rpx; text-align:center; color:#315bff; background:#eef3ff; font-size:26rpx; font-weight:900; margin-right:18rpx; }
.ci.phone { color:#4a2600; background:#fff3c4; }
.cb { flex:1; min-width:0; }
.cl { display:block; font-size:25rpx; color:#8b99b6; }
.cv { display:block; font-size:29rpx; color:#17244e; font-weight:900; margin-top:4rpx; word-break:break-all; }
.ca { font-size:25rpx; font-weight:900; color:#315bff; background:#f3f7ff; border-radius:999rpx; padding:10rpx 18rpx; }
.empty,.loading { text-align:center; padding:46rpx 20rpx; }
.empty-title { display:block; font-size:30rpx; font-weight:900; color:#17244e; }
.empty-desc,.loading text { display:block; font-size:25rpx; color:#64748b; line-height:1.45; margin-top:10rpx; }
.tips-title { display:block; font-size:30rpx; font-weight:900; color:#17244e; margin-bottom:16rpx; }
.tip { display:block; font-size:26rpx; color:#475569; line-height:1.6; padding:8rpx 0; }
</style>
