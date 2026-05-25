<template>
  <view class="profile-page">
    <!-- Top section -->
    <view class="top">
      <!-- 已登录 -->
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
      <!-- 未登录 -->
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

    <!-- Stats panel (clickable) -->
    <view class="stats">
      <view class="stat" @tap="goRecords">
        <text class="sv">{{ reportCount }}</text>
        <text class="sl">已生成报告</text>
        <text class="ss">累计分析</text>
      </view>
      <view class="stat" @tap="goFavorites">
        <text class="sv">{{ favCount }}</text>
        <text class="sl">收藏地址</text>
        <text class="ss">机会池</text>
      </view>
      <view class="stat">
        <text class="sv">{{ points }}</text>
        <text class="sl">剩余点数</text>
        <text class="ss">可用点数</text>
      </view>
    </view>

    <!-- VIP card -->
    <view class="vip-card">
      <view class="vc-top">
        <view class="vc-copy">
          <text class="vc-title">VIP会员 {{ memberDays > 0 ? memberDays+'天' : '未开通' }}</text>
          <text class="vc-desc">{{ memberDays > 0 ? '有效期至 '+memberExpiry : '当前为普通状态，已购点数可用于单次分析' }}</text>
        </view>
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
        <text class="pca primary" @tap="showRecharge = !showRecharge">{{ showRecharge ? '收起' : '获取点数' }}</text>
      </view>
      <view class="pc-body">
        <text class="pc-num">{{ points }}</text>
        <text class="pc-unit">点</text>
        <text class="pc-desc">当前剩余点数 · 可用于生成选址分析报告</text>
        <text class="pc-desc warn" v-if="freePointExpiry && !freePointActive">⚠️ 免费赠送点已过期，实际有效 {{ Math.max(0, points - 1) }} 点</text>
      </view>
      <!-- SKU 套餐列表 -->
      <view class="sku-list" v-if="showRecharge && skus.length">
        <view class="sku-item" v-for="s in skus" :key="s.id" @tap="onBuy(s)">
          <view class="sku-left">
            <text class="sku-label">{{ s.label }}</text>
            <text class="sku-desc">{{ s.desc }}</text>
          </view>
          <view class="sku-right">
            <text class="sku-price">¥{{ s.price }}</text>
            <text class="sku-credits" v-if="s.credits">+{{ s.credits }}点</text>
          </view>
        </view>
        <text class="sku-note" v-if="payErr">{{ payErr }}</text>
      </view>
      <!-- CDK 兑换 -->
      <view class="cdk-row" v-if="loggedIn && showRecharge">
        <input class="cdk-input" v-model="cdkCode" placeholder="输入兑换码" />
        <button class="cdk-btn" :disabled="cdkLoading || !cdkCode" @tap="onCdkRedeem">{{ cdkLoading ? '兑换中' : '兑换' }}</button>
      </view>
      <view class="pc-warn" v-if="!memberDays && points <= 3">
        <text>剩余点数较少</text>
      </view>
    </view>

    <!-- Menu card -->
    <view class="menu-card">
      <view class="menu-item" @tap="goEdit">
        <text class="mi-icon">◈</text>
        <view class="mi-body"><text class="mi-label">完善资料</text><text class="mi-desc">头像、昵称、手机号</text></view>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" v-if="csQrUrl" @tap="previewCsQr">
        <text class="mi-icon">☎</text>
        <view class="mi-body"><text class="mi-label">联系客服</text><text class="mi-desc">扫码添加客服微信</text></view>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" v-if="loggedIn" @tap="onLogout">
        <text class="mi-icon">🚪</text>
        <view class="mi-body"><text class="mi-label">退出登录</text></view>
        <text class="mi-arrow">›</text>
      </view>
    </view>

    <view class="footer">(c) 2026 AI 选址初筛参考工具</view>

    <!-- 登录底部弹层 -->
    <view class="sheet-mask" v-if="showLoginSheet">
      <view class="sheet">
        <view class="sheet-handle" />
        <text class="sheet-title">登录址得选</text>
        <text class="sheet-desc">使用手机号快速登录，体验完整功能</text>

        <!-- 手机号一键登录 -->
        <button class="sheet-btn primary" open-type="getPhoneNumber" @getphonenumber="onPhoneLogin">
          📱 手机号一键登录
        </button>

        <!-- 微信登录（兜底） -->
        <button class="sheet-btn secondary" @tap="onWxLogin">
          <text class="wx-icon">💬</text> 微信登录
        </button>

        <!-- 暂时跳过 -->
        <text class="sheet-skip" @tap="showLoginSheet = false">暂时跳过，先看看</text>

        <!-- 隐私提示 -->
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
      loggedIn: false,
      loginLoading: false,
      loginErr: '',
      phoneLoginDiag: '',
      showLoginSheet: false,
      avatarUrl: '',
      phoneText: '',
      userName: '',
      uidText: '',
      points: 0,
      freePointActive: true,
      freePointExpiry: '',
      csQrUrl: '',
      showRecharge: false,
      skus: [],
      cdkCode: '',
      cdkLoading: false,
      payErr: '',
      memberDays: 0,
      memberExpiry: '',
      reportCount: 0,
      favCount: 0,
      benefits: [
        { icon:'∞',label:'无限分析',desc:'次数不限' },{ icon:'📄',label:'高级报告',desc:'多维评估' },
        { icon:'⌁',label:'盈利预测',desc:'精准估算' },{ icon:'◎',label:'高级模型',desc:'多维评估' },
        { icon:'▥',label:'数据对比',desc:'深度分析' },{ icon:'☎',label:'专属客服',desc:'优先服务' }
      ]
    }
  },
  computed: {
    displayName () {
      if (this.userName) return this.userName
      if (this.phoneText) return this.phoneText
      return '用户' + (this.uidText ? ' ' + this.uidText : '')
    },
    stats () { return [] },
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
            // 只 merge user 对象，不 merge profile 顶层
            if (p.user) auth.setUser(p.user)
          }
        }).catch(() => {})
        // 客服二维码 + SKU（独立拉取，失败静默）
        api.fetchCsQr().then(r => {
          if (r.ok && r.data && r.data.url) this.csQrUrl = r.data.url
        }).catch(() => {})
        api.fetchSkus().then(r => {
          if (r.ok && Array.isArray(r.data?.skus)) this.skus = r.data.skus.filter(s => s.visible)
        }).catch(() => {})
      } else {
        this.loggedIn = false
      }
    },
    // ── 手机号一键登录 ──
    onPhoneLogin (e) {
      this.loginErr = ''
      const detail = e.detail || {}
      const errMsg = detail.errMsg || ''
      const code = detail.code || ''
      // [DEV] release 前移除 console 诊断
      console.log('[phoneLoginDiag]', { errMsg, hasCode: !!code })
      if (errMsg && errMsg.indexOf('deny') >= 0) {
        this.loginErr = '手机号授权已取消'; return
      }
      const phoneCode = detail.code
      if (!phoneCode) { this.loginErr = '获取手机号失败'; return }

      this.loginLoading = true
      this.showLoginSheet = false

      uni.login({
        provider: 'weixin',
        success: (loginRes) => {
          if (!loginRes.code) { this.loginLoading = false; this.loginErr = '微信登录失败'; return }
          api.phoneLogin(loginRes.code, phoneCode).then(r => {
            this.loginLoading = false
            if (r.ok) {
              const d = r.data
              auth.setToken(d.token)
              auth.setUser(d.user)
              if (d.gift_note) uni.setStorageSync('gift_note', d.gift_note)
              if (d.wx_mini_openid) uni.setStorageSync('wx_mini_openid', d.wx_mini_openid)
              if (d.wx_unionid) uni.setStorageSync('wx_unionid', d.wx_unionid)
              this.refreshState()
            } else {
              const sc = r.statusCode
              if (sc === 503) this.loginErr = '登录服务暂不可用，请稍后重试'
              else if (sc === 400) this.loginErr = '登录参数无效，请重试'
              else if (sc === 409) this.loginErr = '该手机号已绑定其他账号'
              else this.loginErr = r.error || '登录失败'
            }
          }).catch(() => { this.loginLoading = false; this.loginErr = '网络异常' })
        },
        fail: () => { this.loginLoading = false; this.loginErr = '微信登录失败' }
      })
    },
    // ── 微信登录（兜底）──
    onWxLogin () {
      this.loginLoading = true; this.loginErr = ''; this.showLoginSheet = false
      auth.wechatLogin().then(r => {
        this.loginLoading = false
        if (r.ok) { this.refreshState() } else {
          const sc = r.statusCode
          if (sc === 503) this.loginErr = '登录服务暂不可用，请稍后重试'
          else if (sc === 400) this.loginErr = '微信登录参数无效，请重新尝试'
          else if (sc === 409) this.loginErr = '微信身份已绑定其他账号'
          else if (sc) this.loginErr = '登录失败 (HTTP ' + sc + ')，请重试'
          else this.loginErr = '登录失败，请稍后重试'
        }
      }).catch(() => { this.loginLoading = false; this.loginErr = '网络异常，请稍后重试' })
    },
    goEdit () { uni.navigateTo({ url: '/pages/profile/edit' }) },
    onLogout () {
      auth.clearToken()
      this.loggedIn = false; this.points = 0; this.reportCount = 0; this.favCount = 0
    },
    goLogin () { uni.navigateTo({ url: '/pages/profile/login' }) },
    goRecords () { uni.switchTab({ url: '/pages/records/index' }) },
    goFavorites () { uni.switchTab({ url: '/pages/favorites/index' }) },
    async onBuy (sku) {
      this.payErr = ''
      try {
        const r = await api.createPrepay(sku.id)
        if (r.ok) {
          const pp = r.data
          const outTradeNo = pp.out_trade_no
          uni.requestPayment({
            timeStamp: pp.timeStamp,
            nonceStr: pp.nonceStr,
            package: pp.package,
            signType: pp.signType || 'RSA',
            paySign: pp.paySign,
            success: async () => {
              // 轮询订单确认到账
              this.payErr = '支付处理中，请稍后刷新...'
              for (let i = 0; i < 6; i++) {
                await new Promise(resolve => setTimeout(resolve, 2000))
                try {
                  const qr = await api.queryOrder(outTradeNo)
                  if (qr.ok && qr.data && qr.data.status === 'PAID') {
                    uni.showToast({ title: '支付成功，点数已到账', icon: 'success' })
                    this.payErr = ''
                    this.showRecharge = false
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
          if (r.statusCode === 503) this.payErr = '支付服务暂不可用，请联系管理员配置'
          else if (r.statusCode === 400 && (r.data?.detail || '').indexOf('微信') >= 0) this.payErr = '请先在微信中登录并授权后再支付'
          else if (r.statusCode === 400) this.payErr = r.data?.detail || '请求参数有误'
          else this.payErr = r.data?.detail || '支付请求失败'
        }
      } catch (e) { this.payErr = '网络异常' }
    },
    async onCdkRedeem () {
      if (!this.cdkCode.trim()) return
      this.cdkLoading = true; this.payErr = ''
      try {
        const r = await api.activateCdk(this.cdkCode.trim().toUpperCase())
        if (r.ok) {
          uni.showToast({ title: `兑换成功，+${r.data.credits_added} 点`, icon: 'success' })
          this.cdkCode = ''
          this.refreshState()
        } else {
          if (r.statusCode === 404) this.payErr = '兑换码不存在'
          else if (r.statusCode === 429) this.payErr = '尝试次数过多，请稍后重试'
          else this.payErr = r.data?.detail || '兑换失败'
        }
      } catch (e) { this.payErr = '网络异常' }
      finally { this.cdkLoading = false }
    },
    previewCsQr () {
      if (!this.csQrUrl) return
      const url = this.csQrUrl.startsWith('/') ? config.API_BASE_URL + this.csQrUrl : this.csQrUrl
      uni.previewImage({ urls: [url], current: url })
    }
  }
}
</script>

<style scoped>
.profile-page { min-height:100vh; background:radial-gradient(circle at 50% -8%,rgba(49,91,255,0.12),transparent 34%),linear-gradient(180deg,#f8fbff 0%,#f2f6ff 48%,#eef3fb 100%); padding-bottom:118rpx; }
.top { background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.22),transparent 26%),radial-gradient(circle at 58% 58%,rgba(248,200,97,0.10),transparent 22%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); padding:56rpx 32rpx 76rpx; text-align:center; color:#fff; position:relative; overflow:hidden; }
.top::before { content:''; position:absolute; left:-120rpx; top:-150rpx; width:660rpx; height:320rpx; border-radius:0 0 56% 56%; background:linear-gradient(180deg,rgba(255,255,255,0.16),rgba(255,255,255,0.02)); transform:rotate(8deg); }
.top::after { content:''; position:absolute; right:52rpx; bottom:0; width:40rpx; height:164rpx; border-radius:9rpx 9rpx 0 0; background:linear-gradient(180deg,rgba(219,234,254,0.56),rgba(37,99,235,0.08)); box-shadow:-58rpx 34rpx 0 rgba(191,219,254,0.34),-114rpx 72rpx 0 rgba(191,219,254,0.22),58rpx 24rpx 0 rgba(191,219,254,0.28); opacity:0.58; }
.top-row { display:flex; align-items:center; text-align:left; position:relative; z-index:1; }
.avatar-img { width:104rpx; height:104rpx; border-radius:30rpx; border:3rpx solid rgba(255,255,255,0.28); flex-shrink:0; background:#fff; }
.avatar-fb { display:inline-flex; align-items:center; justify-content:center; width:108rpx; height:108rpx; border-radius:32rpx; background:linear-gradient(145deg,rgba(255,255,255,0.20),rgba(255,255,255,0.08)); border:1px solid rgba(248,200,97,0.34); box-shadow:0 16rpx 34rpx rgba(5,16,51,0.18),inset 0 1rpx 0 rgba(255,255,255,0.20); position:relative; z-index:1; overflow:hidden; }
.avatar-fb::before { content:''; position:absolute; left:31rpx; top:24rpx; width:46rpx; height:46rpx; border-radius:50%; background:linear-gradient(145deg,#7dd3fc,#5b4be6); box-shadow:0 0 0 10rpx rgba(255,255,255,0.10); }
.avatar-fb::after { content:''; position:absolute; left:24rpx; bottom:20rpx; width:60rpx; height:28rpx; border-radius:32rpx 32rpx 12rpx 12rpx; background:linear-gradient(145deg,#f8c861,#5b4be6); opacity:0.92; }
.top-mid { flex:1; margin-left:24rpx; }
.uname { display:block; font-size:38rpx; font-weight:900; }
.uid { display:block; font-size:24rpx; color:rgba(255,255,255,0.6); margin-top:4rpx; }
.arrow { font-size:40rpx; color:rgba(255,255,255,0.4); }
.login-actions { display:flex; gap:16rpx; margin-top:20rpx; justify-content:center; }
.top-login { width:240rpx; height:64rpx; line-height:64rpx; padding:0; background:linear-gradient(135deg,#fff3c4,#f8c861 58%,#dba640); color:#17244e; border:1px solid rgba(255,255,255,0.48); border-radius:999rpx; font-size:26rpx; font-weight:900; box-shadow:0 14rpx 28rpx rgba(248,200,97,0.18),inset 0 1rpx 0 rgba(255,255,255,0.45); position:relative; z-index:1; }
.top-login.secondary { background:rgba(255,255,255,0.15); color:rgba(255,255,255,0.9); border-color:rgba(255,255,255,0.25); box-shadow:none; }
.top-login::after { border:none; }
.login-err { display:block; margin-top:14rpx; font-size:24rpx; color:#fca5a5; }

.stats { display:flex; background:rgba(255,255,255,0.95); margin:-42rpx 24rpx 24rpx; border-radius:22rpx; padding:24rpx 0; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.14); border:1px solid rgba(219,230,255,0.92); position:relative; z-index:2; }
.stat { flex:1; text-align:center; }
.sv { display:block; font-size:38rpx; font-weight:900; color:#0d4bdc; } .sl { display:block; font-size:24rpx; color:#17244e; font-weight:900; margin-top:4rpx; } .ss { display:block; font-size:20rpx; color:#8b99b6; margin-top:2rpx; }

.vip-card { background:linear-gradient(135deg,#10173d,#151f8f 58%,#5b3fd9); margin:0 24rpx 20rpx; border-radius:22rpx; padding:30rpx; color:#fff; box-shadow:0 18rpx 42rpx rgba(21,31,143,0.24),inset 0 1rpx 0 rgba(248,200,97,0.20); }
.vc-top { display:flex; justify-content:space-between; align-items:flex-start; gap:18rpx; margin-bottom:24rpx; }
.vc-copy { flex:1; min-width:0; padding-top:4rpx; }
.vc-title { font-size:30rpx; font-weight:900; display:block; } .vc-desc { font-size:24rpx; color:rgba(255,255,255,0.74); display:block; margin-top:4rpx; }
.vc-btn { width:auto; min-width:146rpx; height:62rpx; line-height:62rpx; margin:0; padding:0 24rpx; background:linear-gradient(135deg,#fff3c4,#f8c861 58%,#dba640); color:#17244e; border:1px solid rgba(255,255,255,0.44); border-radius:16rpx; font-size:24rpx; font-weight:900; box-shadow:0 12rpx 24rpx rgba(248,200,97,0.18),inset 0 1rpx 0 rgba(255,255,255,0.45); flex-shrink:0; }
.vc-btn::after { border:none; }
.vc-benefits { display:flex; flex-wrap:wrap; gap:16rpx; }
.vb { width:calc(33.3% - 12rpx); text-align:center; background:rgba(255,255,255,0.10); border-radius:16rpx; padding:14rpx 4rpx; box-sizing:border-box; } .vb-icon { font-size:34rpx; display:block; } .vb-label { font-size:22rpx; font-weight:800; display:block; margin-top:4rpx; } .vb-desc { font-size:20rpx; color:rgba(255,255,255,0.58); display:block; }

.points-card { background:rgba(255,255,255,0.94); margin:0 24rpx 20rpx; border-radius:22rpx; padding:28rpx; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); border:1px solid rgba(219,230,255,0.92); }
.pc-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:20rpx; }
.pc-title { font-size:28rpx; font-weight:900; color:#17244e; }
.pc-actions { display:flex; gap:12rpx; } .pca { font-size:24rpx; font-weight:800; padding:8rpx 20rpx; border-radius:14rpx; background:#f3f7ff; color:#315bff; } .pca.primary { background:linear-gradient(135deg,#4a75ff,#315bff); color:#fff; }
.pc-body { text-align:center; margin-bottom:24rpx; }
.pc-num { font-size:80rpx; font-weight:900; color:#315bff; } .pc-unit { font-size:28rpx; color:#8b99b6; }
.pc-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; } .pc-desc.warn { color:#dc2626; }
.pc-warn { margin-top:16rpx; padding:16rpx; background:#fef2f2; border-radius:12rpx; } .pc-warn text { font-size:24rpx; color:#dc2626; }
.sku-list { margin-top:20rpx; }
.sku-item { display:flex; justify-content:space-between; align-items:center; padding:18rpx 0; border-top:1px solid #f1f5f9; }
.sku-left { flex:1; } .sku-label { font-size:26rpx; font-weight:700; color:#1e293b; display:block; } .sku-desc { font-size:22rpx; color:#8b99b6; }
.sku-right { text-align:right; } .sku-price { font-size:28rpx; font-weight:800; color:#315bff; display:block; } .sku-credits { font-size:22rpx; color:#16a34a; }
.sku-note { font-size:22rpx; color:#dc2626; text-align:center; padding:10rpx 0; }
.cdk-row { display:flex; gap:12rpx; margin-top:16rpx; padding-top:16rpx; border-top:1px solid #f1f5f9; }
.cdk-input { flex:1; border:1px solid #d1d5db; border-radius:10rpx; padding:14rpx 14rpx; font-size:26rpx; }
.cdk-btn { background:#0f172a; color:#fff; border-radius:10rpx; font-size:26rpx; padding:14rpx 28rpx; }

.menu-card { background:rgba(255,255,255,0.94); margin:0 24rpx 24rpx; border-radius:22rpx; border:1px solid rgba(219,230,255,0.92); box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); overflow:hidden; }
.menu-item { display:flex; align-items:center; padding:28rpx; border-bottom:1rpx solid rgba(219,230,255,0.78); }
.mi-icon { font-size:34rpx; margin-right:18rpx; width:48rpx; height:48rpx; line-height:48rpx; text-align:center; border-radius:14rpx; background:#f3f7ff; color:#315bff; } .mi-body { flex:1; } .mi-label { font-size:28rpx; font-weight:900; color:#17244e; display:block; } .mi-desc { font-size:22rpx; color:#8b99b6; }
.mi-arrow { font-size:32rpx; color:#cbd5e1; }
.footer { text-align:center; font-size:20rpx; color:#94a3b8; padding:24rpx; }

/* ── 登录底部弹层 ── */
.sheet-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:500; display:flex; align-items:flex-end; }
.sheet { width:100%; background:#fff; border-radius:26rpx 26rpx 0 0; padding:32rpx 28rpx 48rpx; text-align:center; box-shadow:0 -20rpx 60rpx rgba(15,23,42,0.18); }
.sheet-handle { width:60rpx; height:6rpx; background:#e2e8f0; border-radius:3rpx; margin:0 auto 24rpx; }
.sheet-title { display:block; font-size:34rpx; font-weight:800; color:#1e293b; }
.sheet-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; margin-bottom:32rpx; }
.sheet-btn { width:100%; border-radius:16rpx; font-size:30rpx; font-weight:600; padding:24rpx 0; margin-bottom:16rpx; }
.sheet-btn.primary { background:linear-gradient(135deg,#4a75ff,#315bff); color:#fff; }
.sheet-btn.secondary { background:#f3f7ff; color:#315bff; display:flex; align-items:center; justify-content:center; gap:8rpx; }
.sheet-btn::after { border:none; }
.sheet-skip { display:block; font-size:24rpx; color:#94a3b8; padding:12rpx; }
.sheet-privacy { display:block; font-size:20rpx; color:#cbd5e1; margin-top:16rpx; }
</style>
