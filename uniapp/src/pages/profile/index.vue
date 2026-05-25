<template>
  <view class="profile-page">
    <!-- Top section -->
    <view class="top">
      <template v-if="loggedIn">
        <view class="top-row" @tap="goEdit">
          <image v-if="avatarUrl" class="avatar-img" :src="avatarUrl" mode="aspectFill" />
          <text v-else class="avatar-fb">👤</text>
          <view class="top-mid">
            <text class="uname">{{ displayName }}</text>
            <text class="uid" v-if="uidText">{{ uidText }}</text>
          </view>
          <text class="arrow">›</text>
        </view>
      </template>
      <template v-else>
        <text class="avatar-fb"></text>
        <text class="uname">未登录</text>
        <view class="login-actions">
          <button class="top-login" @tap="goLogin">手机号登录</button>
          <button class="top-login secondary" @tap="showLoginSheet = true">微信登录</button>
        </view>
      </template>
      <text class="login-err" v-if="loginErr">{{ loginErr }}</text>
    </view>

    <!-- Stats -->
    <view class="stats">
      <view class="stat" @tap="goRecords">
        <text class="sv">{{ reportCount }}</text>
        <text class="sl">已生成报告</text>
      </view>
      <view class="stat" @tap="goFavorites">
        <text class="sv">{{ favCount }}</text>
        <text class="sl">收藏地址</text>
      </view>
      <view class="stat">
        <text class="sv">{{ points }}</text>
        <text class="sl">剩余点数</text>
      </view>
    </view>

    <!-- VIP card -->
    <view class="vip-card">
      <view class="vc-top">
        <view class="vc-copy">
          <text class="vc-title">VIP会员 {{ memberDays > 0 ? memberDays+'天' : '未开通' }}</text>
          <text class="vc-desc">{{ memberDays > 0 ? '有效期至 '+memberExpiry : '开通会员，解锁全部高级功能' }}</text>
        </view>
        <button class="vc-btn" @tap="openRecharge">{{ memberDays > 0 ? '立即续费' : '立即开通' }}</button>
      </view>
      <view class="vc-benefits">
        <view class="vb" v-for="b in benefits" :key="b.label">
          <text class="vb-icon">{{ b.icon }}</text>
          <text class="vb-label">{{ b.label }}</text>
          <text class="vb-desc">{{ b.desc }}</text>
        </view>
      </view>
    </view>

    <!-- Points card -->
    <view class="points-card">
      <view class="pc-head">
        <text class="pc-title">● 我的点数</text>
        <view class="pc-actions">
          <text class="pca" @tap="cdkOpen = true">兑换码</text>
          <text class="pca primary" @tap="openRecharge">获取点数</text>
        </view>
      </view>
      <view class="pc-body">
        <text class="pc-num">{{ points }}</text>
        <text class="pc-unit">点</text>
        <text class="pc-desc">当前剩余点数 · 可用于生成选址分析报告</text>
        <text class="pc-desc warn" v-if="freePointExpiry && !freePointActive">免费赠送点已过期，实际有效 {{ Math.max(0, points - 1) }} 点</text>
      </view>
      <view class="pc-warn" v-if="!memberDays && points <= 3">
        <text>剩余点数较少</text>
      </view>
    </view>

    <!-- Menu -->
    <view class="menu-card">
      <view class="menu-item" @tap="goEdit">
        <text class="mi-icon">◈</text>
        <view class="mi-body"><text class="mi-label">完善资料</text></view>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" v-if="csQrUrl || csWechat || csPhone" @tap="openCsSheet">
        <text class="mi-icon">☎</text>
        <view class="mi-body"><text class="mi-label">联系客服</text></view>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" v-if="loggedIn" @tap="onLogout">
        <text class="mi-icon">🚪</text>
        <view class="mi-body"><text class="mi-label">退出登录</text></view>
        <text class="mi-arrow">›</text>
      </view>
    </view>

    <view class="footer">以上分析仅供参考，不构成投资建议</view>

    <!-- 充值弹层 -->
    <view class="sheet-mask" v-if="rechargeOpen" @tap="rechargeOpen = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">开通会员或购买点数</text>
        <text class="sheet-desc">请扫码添加专属客服微信，或使用兑换码激活</text>

        <view class="rc-tabs">
          <text class="rc-tab" :class="{ active: rechargeTab === 'points' }" @tap="rechargeTab = 'points'">点数包</text>
          <text class="rc-tab" :class="{ active: rechargeTab === 'membership' }" @tap="rechargeTab = 'membership'">会员套餐</text>
        </view>

        <!-- points tab -->
        <view class="rc-list" v-if="rechargeTab === 'points'">
          <view class="rc-item" v-for="s in pointSkus" :key="s.id" @tap="onBuy(s)">
            <view class="rci-left">
              <text class="rci-label">{{ s.label }}</text>
              <text class="rci-desc">{{ s.desc }}</text>
            </view>
            <view class="rci-right">
              <text class="rci-price">¥{{ s.price }}</text>
              <text class="rci-credits">+{{ s.credits }}点</text>
            </view>
          </view>
          <view class="rc-empty" v-if="!pointSkus.length">
            <text>暂无点数套餐，请联系客服</text>
          </view>
        </view>
        <!-- membership tab -->
        <view class="rc-list" v-if="rechargeTab === 'membership'">
          <view class="rc-item" v-for="s in memberSkus" :key="s.id" @tap="onBuy(s)">
            <view class="rci-left">
              <text class="rci-label">{{ s.label }}</text>
              <text class="rci-desc">{{ s.desc || s.duration_days+'天' }}</text>
            </view>
            <view class="rci-right">
              <text class="rci-price">¥{{ s.price }}</text>
              <text class="rci-credits" v-if="s.credits">+{{ s.credits }}点</text>
            </view>
          </view>
          <view class="rc-empty" v-if="!memberSkus.length">
            <text>暂无会员套餐，请联系客服</text>
          </view>
        </view>

        <!-- 客服二维码 -->
        <view class="cs-section" v-if="csQrUrl">
          <image class="cs-qr-img" :src="csQrFullUrl" mode="aspectFit" @tap="previewCsQr" />
          <text class="cs-hint">扫码联系专属客服充值</text>
        </view>
        <text class="cs-hint" v-else-if="!csQrUrl">暂未配置客服入口</text>
        <text class="rc-note" v-if="payErr">{{ payErr }}</text>
      </view>
    </view>

    <!-- CDK 兑换弹层 -->
    <view class="sheet-mask" v-if="cdkOpen" @tap="cdkOpen = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">激活兑换码</text>
        <text class="sheet-desc">输入兑换码，点数即时到账</text>
        <input class="cdk-field" v-model="cdkCode" placeholder="输入兑换码" />
        <button class="cdk-act-btn" :disabled="cdkLoading || !cdkCode.trim()" @tap="onCdkRedeem">{{ cdkLoading ? '激活中...' : '立即激活' }}</button>
        <text class="cdk-err" v-if="payErr">{{ payErr }}</text>
      </view>
    </view>

    <!-- 客服联系方式弹层 -->
    <view class="sheet-mask" v-if="csSheetOpen" @tap="csSheetOpen = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">联系客服</text>
        <image class="cs-qr-img" v-if="csQrUrl" :src="csQrFullUrl" mode="aspectFit" @tap="previewCsQr" />
        <view class="cs-lines">
          <text class="cs-line" v-if="csWechat" @tap="copyCs(csWechat)">微信：{{ csWechat }}（点击复制）</text>
          <text class="cs-line" v-if="csPhone" @tap="callCs(csPhone)">电话：{{ csPhone }}（点击拨打）</text>
        </view>
      </view>
    </view>

    <!-- 登录底部弹层 -->
    <view class="sheet-mask" v-if="showLoginSheet">
      <view class="sheet">
        <view class="sheet-handle" />
        <text class="sheet-title">登录址得选</text>
        <text class="sheet-desc">使用手机号快速登录，体验完整功能</text>
        <button class="sheet-btn primary" open-type="getPhoneNumber" @getphonenumber="onPhoneLogin">📱 手机号一键登录</button>
        <button class="sheet-btn secondary" @tap="onWxLogin">💬 微信登录</button>
        <text class="sheet-skip" @tap="showLoginSheet = false">暂时跳过，先看看</text>
        <text class="sheet-privacy">登录即表示同意《用户协议》和《隐私政策》</text>
      </view>
    </view>
  </view>
</template>

<script>
import auth from '../../utils/auth'
import api from '../../utils/api'
import config from '../../utils/config'

export default {
  data () {
    return {
      loggedIn: false, loginLoading: false, loginErr: '',
      showLoginSheet: false,
      avatarUrl: '', phoneText: '', userName: '', uidText: '',
      points: 0, freePointActive: true, freePointExpiry: '',
      memberDays: 0, memberExpiry: '', reportCount: 0, favCount: 0,
      rechargeOpen: false, rechargeTab: 'points',
      cdkOpen: false, cdkCode: '', cdkLoading: false, payErr: '',
      csSheetOpen: false, csQrUrl: '', csWechat: '', csPhone: '',
      skus: [],
      benefits: [
        { icon:'∞',label:'无限分析',desc:'次数不限' },
        { icon:'📄',label:'高级报告',desc:'多维评估' },
        { icon:'⌁',label:'盈利预测',desc:'精准估算' },
        { icon:'◎',label:'高级模型',desc:'多维评估' },
        { icon:'▥',label:'数据对比',desc:'深度分析' },
        { icon:'☎',label:'专属客服',desc:'优先服务' }
      ]
    }
  },
  computed: {
    displayName () {
      if (this.userName) return this.userName
      if (this.phoneText) return this.phoneText
      return '用户' + (this.uidText ? ' ' + this.uidText : '')
    },
    pointSkus () { return this.skus.filter(s => s.type !== 'membership') },
    memberSkus () { return this.skus.filter(s => s.type === 'membership') },
    csQrFullUrl () {
      if (!this.csQrUrl) return ''
      return this.csQrUrl.startsWith('/') ? config.API_BASE_URL + this.csQrUrl : this.csQrUrl
    }
  },
  onShow () { this.refreshState() },
  methods: {
    refreshState () {
      const token = auth.getToken()
      if (token) {
        const user = auth.getUser() || {}
        this.loggedIn = true
        this.points = user.balance_credits ?? 0
        this.userName = user.nickname || user.name || ''
        this.avatarUrl = user.avatar_url || user.avatarUrl || ''
        const phone = user.phone_number || user.phone || ''
        this.phoneText = phone ? phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : ''
        this.uidText = user.id ? '用户编号：' + user.id : ''
        this.memberDays = user.membership_days_left || 0
        this.memberExpiry = user.membership_expiry || ''
        api.fetchProfile().then(r => {
          if (r.ok && r.data) {
            const p = r.data
            this.points = p.points ?? (p.user && p.user.balance_credits) ?? this.points
            this.freePointActive = (p.user && p.user.free_point_active) ?? true
            this.freePointExpiry = (p.user && p.user.free_point_expire_at) || ''
            this.memberDays = p.membership_days_left ?? this.memberDays
            this.memberExpiry = p.membership_expiry || this.memberExpiry
            this.reportCount = p.total_reports ?? 0
            this.favCount = p.favorite_count ?? 0
            if (p.user) auth.setUser(p.user)
          }
        }).catch(() => {})
        // CS QR + UI config + SKU
        api.fetchCsQr().then(r => { if (r.ok && r.data) this.csQrUrl = r.data.url || '' }).catch(() => {})
        api.fetchUiConfig().then(r => {
          if (r.ok && r.data) {
            this.csWechat = r.data.cs_wechat || ''
            this.csPhone = r.data.cs_phone || ''
          }
        }).catch(() => {})
        api.fetchSkus().then(r => {
          if (r.ok && Array.isArray(r.data?.skus)) this.skus = r.data.skus.filter(s => s.visible)
        }).catch(() => {})
      } else {
        this.loggedIn = false
      }
    },
    openRecharge () { this.rechargeOpen = true; this.payErr = '' },
    async onBuy (sku) {
      this.payErr = ''
      if (!sku || !sku.id) return
      try {
        const r = await api.createPrepay(sku.id)
        if (r.ok) {
          const pp = r.data
          const outTradeNo = pp.out_trade_no
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
                    this.rechargeOpen = false
                    uni.showToast({ title: '支付成功，已到账', icon: 'success' })
                    this.refreshState()
                    return
                  }
                } catch (e) { /* retry */ }
              }
              this.payErr = '支付处理中，请稍后刷新页面查看'
              this.refreshState()
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
    },
    goLogin () { uni.navigateTo({ url: '/pages/profile/login' }) },
    goRecords () { uni.switchTab({ url: '/pages/records/index' }) },
    goFavorites () { uni.switchTab({ url: '/pages/favorites/index' }) },
    goEdit () { uni.navigateTo({ url: '/pages/profile/edit' }) },
    openCsSheet () { this.csSheetOpen = true },
    copyCs (text) { uni.setClipboardData({ data: text, success: () => uni.showToast({ title: '已复制', icon: 'none' }) }) },
    callCs (phone) { uni.makePhoneCall({ phoneNumber: phone }) },
    previewCsQr () {
      if (this.csQrFullUrl) uni.previewImage({ urls: [this.csQrFullUrl] })
    },
    async onCdkRedeem () {
      if (!this.cdkCode.trim()) return
      this.cdkLoading = true; this.payErr = ''
      try {
        const r = await api.activateCdk(this.cdkCode.trim().toUpperCase())
        if (r.ok) {
          uni.showToast({ title: `兑换成功，+${r.data.credits_added} 点`, icon: 'success' })
          this.cdkCode = ''; this.cdkOpen = false
          this.refreshState()
        } else {
          if (r.statusCode === 404) this.payErr = '兑换码不存在'
          else if (r.statusCode === 429) this.payErr = '尝试次数过多，请稍后重试'
          else this.payErr = r.data?.detail || '兑换失败'
        }
      } catch (e) { this.payErr = '网络异常' }
      finally { this.cdkLoading = false }
    },
    // ── 手机号一键登录 ──
    onPhoneLogin (e) {
      this.loginErr = ''
      const detail = e.detail || {}
      if (detail.errMsg && detail.errMsg.indexOf('deny') >= 0) { this.loginErr = '手机号授权已取消'; return }
      const phoneCode = detail.code
      if (!phoneCode) { this.loginErr = '获取手机号失败'; return }
      this.loginLoading = true; this.showLoginSheet = false
      uni.login({
        provider: 'weixin',
        success: (loginRes) => {
          if (!loginRes.code) { this.loginLoading = false; this.loginErr = '微信登录失败'; return }
          api.phoneLogin(loginRes.code, phoneCode).then(r => {
            this.loginLoading = false
            if (r.ok) {
              auth.setToken(r.data.token); auth.setUser(r.data.user)
              if (r.data.wx_mini_openid) uni.setStorageSync('wx_mini_openid', r.data.wx_mini_openid)
              this.refreshState()
            } else {
              const sc = r.statusCode
              if (sc === 503) this.loginErr = '登录服务暂不可用'
              else if (sc === 400) this.loginErr = '登录参数无效，请重试'
              else if (sc === 409) this.loginErr = '该手机号已绑定其他账号'
              else this.loginErr = r.error || '登录失败'
            }
          }).catch(() => { this.loginLoading = false; this.loginErr = '网络异常' })
        },
        fail: () => { this.loginLoading = false; this.loginErr = '微信登录失败' }
      })
    },
    onWxLogin () {
      this.loginLoading = true; this.loginErr = ''; this.showLoginSheet = false
      auth.wechatLogin().then(r => {
        this.loginLoading = false
        if (r.ok) { this.refreshState() } else {
          const sc = r.statusCode
          if (sc === 503) this.loginErr = '登录服务暂不可用'
          else if (sc === 400) this.loginErr = '微信登录参数无效，请重试'
          else if (sc === 409) this.loginErr = '微信身份已绑定其他账号'
          else if (sc) this.loginErr = '登录失败 (HTTP ' + sc + ')，请重试'
          else this.loginErr = '登录失败，请稍后重试'
        }
      }).catch(() => { this.loginLoading = false; this.loginErr = '网络异常，请稍后重试' })
    },
    onLogout () { auth.clearToken(); this.loggedIn = false; this.points = 0; this.reportCount = 0; this.favCount = 0 }
  }
}
</script>

<style scoped>
.profile-page { min-height:100vh; background:linear-gradient(180deg,#eaf2ff 0%,#f2f6ff 42%,#eef3fb 100%); padding-bottom:80rpx; }
.top { background:linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 100%); padding:60rpx 32rpx 48rpx; text-align:center; color:#fff; }
.top-row { display:flex; align-items:center; text-align:left; }
.avatar-img { width:100rpx; height:100rpx; border-radius:50%; border:3rpx solid rgba(255,255,255,0.3); flex-shrink:0; }
.avatar-fb { font-size:80rpx; }
.top-mid { flex:1; margin-left:24rpx; }
.uname { display:block; font-size:36rpx; font-weight:700; }
.uid { display:block; font-size:24rpx; color:rgba(255,255,255,0.6); margin-top:4rpx; }
.arrow { font-size:40rpx; color:rgba(255,255,255,0.4); }
.login-actions { display:flex; gap:16rpx; margin-top:20rpx; justify-content:center; }
.top-login { width:240rpx; height:64rpx; line-height:64rpx; padding:0; background:linear-gradient(135deg,#fff3c4,#f8c861 58%,#dba640); color:#17244e; border:1px solid rgba(255,255,255,0.48); border-radius:999rpx; font-size:26rpx; font-weight:900; }
.top-login.secondary { background:rgba(255,255,255,0.15); color:rgba(255,255,255,0.9); border-color:rgba(255,255,255,0.25); box-shadow:none; }
.top-login::after { border:none; }
.login-err { display:block; margin-top:14rpx; font-size:24rpx; color:#fca5a5; }

.stats { display:flex; background:#fff; margin:-30rpx 24rpx 24rpx; border-radius:20rpx; padding:24rpx 0; box-shadow:0 4rpx 24rpx rgba(0,0,0,0.06); }
.stat { flex:1; text-align:center; }
.sv { display:block; font-size:36rpx; font-weight:800; color:#1e293b; } .sl { display:block; font-size:22rpx; color:#8b99b6; }

.vip-card { background:linear-gradient(135deg,#0b3fbd,#151f8f 58%,#5b3fd9); margin:0 24rpx 20rpx; border-radius:20rpx; padding:28rpx; color:#fff; box-shadow:0 18rpx 42rpx rgba(21,31,143,0.24); }
.vc-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:24rpx; }
.vc-title { font-size:30rpx; font-weight:700; display:block; } .vc-desc { font-size:24rpx; color:rgba(255,255,255,0.7); display:block; margin-top:4rpx; }
.vc-btn { background:linear-gradient(135deg,#fff3c4,#f8c861 58%,#dba640); color:#17244e; border-radius:14rpx; font-size:26rpx; font-weight:800; padding:14rpx 28rpx; border:1px solid rgba(255,255,255,0.48); box-shadow:0 14rpx 28rpx rgba(248,200,97,0.16); }
.vc-btn::after { border:none; }
.vc-benefits { display:flex; flex-wrap:wrap; gap:16rpx; }
.vb { width:calc(33.3% - 12rpx); text-align:center; } .vb-icon { font-size:36rpx; display:block; } .vb-label { font-size:22rpx; display:block; margin-top:4rpx; } .vb-desc { font-size:20rpx; color:rgba(255,255,255,0.5); display:block; }

.points-card { background:#fff; margin:0 24rpx 20rpx; border-radius:20rpx; padding:28rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.pc-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:20rpx; }
.pc-title { font-size:28rpx; font-weight:700; color:#1e293b; }
.pc-actions { display:flex; gap:12rpx; } .pca { font-size:24rpx; font-weight:800; padding:8rpx 20rpx; border-radius:14rpx; background:#f3f7ff; color:#315bff; } .pca.primary { background:#315bff; color:#fff; }
.pc-body { text-align:center; margin-bottom:20rpx; }
.pc-num { font-size:80rpx; font-weight:900; color:#315bff; } .pc-unit { font-size:28rpx; color:#8b99b6; }
.pc-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; } .pc-desc.warn { color:#dc2626; }
.pc-warn { padding:16rpx; background:#fef2f2; border-radius:12rpx; } .pc-warn text { font-size:24rpx; color:#dc2626; }

.menu-card { background:#fff; margin:0 24rpx 24rpx; border-radius:20rpx; }
.menu-item { display:flex; align-items:center; padding:28rpx; border-bottom:1px solid #f1f5f9; }
.mi-icon { font-size:36rpx; margin-right:16rpx; } .mi-body { flex:1; } .mi-label { font-size:28rpx; color:#1e293b; display:block; }
.mi-arrow { font-size:32rpx; color:#cbd5e1; }
.footer { text-align:center; font-size:20rpx; color:#cbd5e1; padding:24rpx; }

/* Sheet */
.sheet-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:500; display:flex; align-items:flex-end; }
.sheet { width:100%; background:#fff; border-radius:24rpx 24rpx 0 0; padding:32rpx 28rpx 48rpx; text-align:center; max-height:85vh; overflow-y:auto; }
.sheet-handle { width:60rpx; height:6rpx; background:#e2e8f0; border-radius:3rpx; margin:0 auto 24rpx; }
.sheet-title { display:block; font-size:32rpx; font-weight:800; color:#1e293b; }
.sheet-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; margin-bottom:28rpx; }

/* Recharge */
.rc-tabs { display:flex; gap:0; background:#f3f7ff; border-radius:14rpx; padding:6rpx; margin-bottom:20rpx; }
.rc-tab { flex:1; text-align:center; font-size:26rpx; font-weight:700; color:#8b99b6; padding:14rpx 0; border-radius:10rpx; }
.rc-tab.active { background:#315bff; color:#fff; }
.rc-list { text-align:left; margin-bottom:16rpx; }
.rc-item { display:flex; justify-content:space-between; align-items:center; padding:18rpx 0; border-top:1px solid #f1f5f9; }
.rci-label { font-size:26rpx; font-weight:700; color:#1e293b; } .rci-desc { font-size:22rpx; color:#8b99b6; }
.rci-price { font-size:28rpx; font-weight:800; color:#315bff; } .rci-credits { font-size:22rpx; color:#16a34a; }
.rc-empty { padding:20rpx; font-size:24rpx; color:#94a3b8; }
.rc-note { font-size:22rpx; color:#dc2626; margin-top:10rpx; }

/* CS */
.cs-section { margin:16rpx 0; }
.cs-qr-img { width:280rpx; height:280rpx; margin:0 auto; display:block; border:1px solid #e2e8f0; border-radius:16rpx; }
.cs-hint { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; }
.cs-lines { padding:16rpx 0; }
.cs-line { display:block; font-size:26rpx; color:#315bff; padding:12rpx 0; }

/* CDK */
.cdk-field { width:100%; border:1px solid #d1d5db; border-radius:12rpx; padding:18rpx 16rpx; font-size:28rpx; margin-top:20rpx; box-sizing:border-box; }
.cdk-act-btn { width:100%; background:#0f172a; color:#fff; border-radius:14rpx; font-size:28rpx; font-weight:700; padding:20rpx 0; margin-top:16rpx; }
.cdk-err { display:block; font-size:24rpx; color:#dc2626; margin-top:12rpx; }

/* Login sheet */
.sheet-btn { width:100%; border-radius:16rpx; font-size:30rpx; font-weight:600; padding:24rpx 0; margin-bottom:16rpx; }
.sheet-btn.primary { background:#07c160; color:#fff; }
.sheet-btn.secondary { background:#f1f5f9; color:#475569; }
.sheet-skip { display:block; font-size:24rpx; color:#94a3b8; padding:12rpx; }
.sheet-privacy { display:block; font-size:20rpx; color:#cbd5e1; margin-top:16rpx; }
</style>
