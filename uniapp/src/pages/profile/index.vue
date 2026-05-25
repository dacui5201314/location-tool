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
        <text class="avatar-fb">👤</text>
        <text class="uname">未登录</text>
        <button class="top-login" @tap="showLoginSheet = true">登录 / 注册</button>
      </template>
      <text class="login-err" v-if="loginErr">{{ loginErr }}</text>
    </view>

    <!-- Stats panel -->
    <view class="stats">
      <view class="stat" v-for="s in stats" :key="s.label">
        <text class="sv">{{ s.value }}</text>
        <text class="sl">{{ s.label }}</text>
        <text class="ss">{{ s.sub }}</text>
      </view>
    </view>

    <!-- VIP card -->
    <view class="vip-card">
      <view class="vc-top">
        <view>
          <text class="vc-title">VIP会员 {{ memberDays > 0 ? memberDays+'天' : '未开通' }}</text>
          <text class="vc-desc">{{ memberDays > 0 ? '有效期至 '+memberExpiry : '开通会员，解锁全部高级功能' }}</text>
        </view>
        <button class="vc-btn" @tap="onUpgrade">{{ memberDays > 0 ? '立即续费' : '立即开通' }}</button>
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
          <text class="pca" @tap="onCDK">兑换码</text>
          <text class="pca primary" @tap="onBuy">获取点数</text>
        </view>
      </view>
      <view class="pc-body">
        <text class="pc-num">{{ points }}</text>
        <text class="pc-unit">点</text>
        <text class="pc-desc">当前剩余点数 · 可用于生成选址分析报告</text>
        <text class="pc-desc warn" v-if="freePointExpiry && !freePointActive">⚠️ 免费赠送点已过期，实际有效 {{ Math.max(0, points - 1) }} 点</text>
      </view>
      <view class="pc-warn" v-if="!memberDays && points <= 3">
        <text>点数即将用完，建议充值或开通会员</text>
      </view>
    </view>

    <!-- Menu card -->
    <view class="menu-card">
      <view class="menu-item" @tap="onUpgrade">
        <text class="mi-icon">◇</text>
        <view class="mi-body"><text class="mi-label">会员权益</text><text class="mi-desc">了解会员特权</text></view>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="onCS">
        <text class="mi-icon">☎</text>
        <view class="mi-body"><text class="mi-label">联系客服</text><text class="mi-desc">专属客服支持</text></view>
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
    stats () {
      return [
        { value: this.points, label: '剩余点数', sub: '可用点数' },
        { value: this.reportCount, label: '已生成报告', sub: '累计分析' },
        { value: this.favCount, label: '收藏地址', sub: '机会池' }
      ]
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
            // 只 merge user 对象，不 merge profile 顶层
            if (p.user) auth.setUser(p.user)
          }
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
    onUpgrade () { uni.showToast({ title: '会员充值接入中', icon: 'none' }) },
    onCDK () { uni.showToast({ title: '兑换码接入中', icon: 'none' }) },
    onBuy () { uni.showToast({ title: '点数购买接入中', icon: 'none' }) },
    onCS () { uni.showToast({ title: '客服接入中', icon: 'none' }) }
  }
}
</script>

<style scoped>
.profile-page { min-height:100vh; background:radial-gradient(circle at 50% -8%,rgba(49,91,255,0.12),transparent 34%),linear-gradient(180deg,#f8fbff 0%,#f2f6ff 48%,#eef3fb 100%); padding-bottom:118rpx; }
.top { background:radial-gradient(circle at 78% 32%,rgba(93,171,255,0.48),transparent 24%),radial-gradient(circle at 64% 62%,rgba(248,200,97,0.12),transparent 24%),linear-gradient(160deg,#0d4bdc 0%,#0f45d0 24%,#1533b4 64%,#1d2497 100%); padding:56rpx 32rpx 76rpx; text-align:center; color:#fff; position:relative; overflow:hidden; }
.top::before { content:''; position:absolute; left:-120rpx; top:-150rpx; width:660rpx; height:320rpx; border-radius:0 0 56% 56%; background:linear-gradient(180deg,rgba(255,255,255,0.16),rgba(255,255,255,0.02)); transform:rotate(8deg); }
.top::after { content:''; position:absolute; right:52rpx; bottom:0; width:40rpx; height:164rpx; border-radius:9rpx 9rpx 0 0; background:linear-gradient(180deg,rgba(219,234,254,0.56),rgba(37,99,235,0.08)); box-shadow:-58rpx 34rpx 0 rgba(191,219,254,0.34),-114rpx 72rpx 0 rgba(191,219,254,0.22),58rpx 24rpx 0 rgba(191,219,254,0.28); opacity:0.58; }
.top-row { display:flex; align-items:center; text-align:left; position:relative; z-index:1; }
.avatar-img { width:104rpx; height:104rpx; border-radius:30rpx; border:3rpx solid rgba(255,255,255,0.28); flex-shrink:0; background:#fff; }
.avatar-fb { font-size:72rpx; display:inline-flex; align-items:center; justify-content:center; width:104rpx; height:104rpx; border-radius:30rpx; background:rgba(255,255,255,0.14); }
.top-mid { flex:1; margin-left:24rpx; }
.uname { display:block; font-size:38rpx; font-weight:900; }
.uid { display:block; font-size:24rpx; color:rgba(255,255,255,0.6); margin-top:4rpx; }
.arrow { font-size:40rpx; color:rgba(255,255,255,0.4); }
.top-login { margin-top:28rpx; width:400rpx; background:#fff; color:#315bff; border-radius:18rpx; font-size:32rpx; font-weight:900; padding:20rpx 0; box-shadow:0 16rpx 34rpx rgba(5,16,51,0.16); position:relative; z-index:1; }
.top-login::after { border:none; }
.login-err { display:block; margin-top:14rpx; font-size:24rpx; color:#fca5a5; }

.stats { display:flex; background:rgba(255,255,255,0.95); margin:-42rpx 24rpx 24rpx; border-radius:22rpx; padding:24rpx 0; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.14); border:1px solid rgba(219,230,255,0.92); position:relative; z-index:2; }
.stat { flex:1; text-align:center; }
.sv { display:block; font-size:38rpx; font-weight:900; color:#0d4bdc; } .sl { display:block; font-size:24rpx; color:#17244e; font-weight:900; margin-top:4rpx; } .ss { display:block; font-size:20rpx; color:#8b99b6; margin-top:2rpx; }

.vip-card { background:linear-gradient(135deg,#101b48,#1735b8 58%,#5b4be6); margin:0 24rpx 20rpx; border-radius:22rpx; padding:30rpx; color:#fff; box-shadow:0 18rpx 42rpx rgba(22,54,184,0.24),inset 0 1rpx 0 rgba(248,200,97,0.20); }
.vc-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:24rpx; }
.vc-title { font-size:30rpx; font-weight:900; display:block; } .vc-desc { font-size:24rpx; color:rgba(255,255,255,0.74); display:block; margin-top:4rpx; }
.vc-btn { background:rgba(255,255,255,0.14); color:#fff; border:1px solid rgba(255,255,255,0.30); border-radius:14rpx; font-size:26rpx; font-weight:900; padding:14rpx 28rpx; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.18); }
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
