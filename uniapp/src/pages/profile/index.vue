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
    <view class="sheet-mask" v-if="showLoginSheet" @tap="showLoginSheet = false">
      <view class="sheet" @tap.stop>
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
              if (sc === 503) this.loginErr = '小程序未配置，请联系管理员'
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
          if (sc === 503) this.loginErr = '小程序登录未配置，请先在管理后台配置小程序凭据'
          else if (sc === 400) this.loginErr = '微信登录参数无效，请重新尝试'
          else if (sc === 409) this.loginErr = '微信身份已绑定其他账号'
          else if (sc) this.loginErr = '登录失败 (HTTP ' + sc + ')，请重试'
          else this.loginErr = '登录失败，请检查后端日志'
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
.profile-page { min-height:100vh; background:#eef3f9; padding-bottom:60rpx; }
.top { background:linear-gradient(135deg,#02091d,#071843); padding:60rpx 32rpx 40rpx; text-align:center; color:#fff; }
.top-row { display:flex; align-items:center; text-align:left; }
.avatar-img { width:100rpx; height:100rpx; border-radius:50rpx; border:3rpx solid rgba(255,255,255,0.3); flex-shrink:0; }
.avatar-fb { font-size:80rpx; }
.top-mid { flex:1; margin-left:24rpx; }
.uname { display:block; font-size:36rpx; font-weight:700; }
.uid { display:block; font-size:24rpx; color:rgba(255,255,255,0.6); margin-top:4rpx; }
.arrow { font-size:40rpx; color:rgba(255,255,255,0.4); }
.top-login { margin-top:28rpx; width:400rpx; background:#07c160; color:#fff; border-radius:40rpx; font-size:32rpx; font-weight:600; padding:20rpx 0; }
.login-err { display:block; margin-top:14rpx; font-size:24rpx; color:#fca5a5; }

.stats { display:flex; background:#fff; margin:-30rpx 24rpx 24rpx; border-radius:20rpx; padding:24rpx 0; box-shadow:0 4rpx 24rpx rgba(0,0,0,0.06); }
.stat { flex:1; text-align:center; }
.sv { display:block; font-size:36rpx; font-weight:800; color:#1e293b; } .sl { display:block; font-size:24rpx; color:#334155; font-weight:600; margin-top:4rpx; } .ss { display:block; font-size:20rpx; color:#94a3b8; margin-top:2rpx; }

.vip-card { background:linear-gradient(135deg,#1e293b,#0f172a); margin:0 24rpx 20rpx; border-radius:20rpx; padding:28rpx; color:#fff; }
.vc-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:24rpx; }
.vc-title { font-size:30rpx; font-weight:700; display:block; } .vc-desc { font-size:24rpx; color:rgba(255,255,255,0.7); display:block; margin-top:4rpx; }
.vc-btn { background:#d6a84f; color:#1e293b; border-radius:14rpx; font-size:26rpx; font-weight:700; padding:14rpx 28rpx; }
.vc-benefits { display:flex; flex-wrap:wrap; gap:16rpx; }
.vb { width:calc(33.3% - 12rpx); text-align:center; } .vb-icon { font-size:36rpx; display:block; } .vb-label { font-size:22rpx; display:block; margin-top:4rpx; } .vb-desc { font-size:20rpx; color:rgba(255,255,255,0.5); display:block; }

.points-card { background:#fff; margin:0 24rpx 20rpx; border-radius:20rpx; padding:28rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.pc-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:20rpx; }
.pc-title { font-size:28rpx; font-weight:700; color:#1e293b; }
.pc-actions { display:flex; gap:12rpx; } .pca { font-size:24rpx; padding:8rpx 20rpx; border-radius:14rpx; background:#f1f5f9; color:#475569; } .pca.primary { background:#246bff; color:#fff; }
.pc-body { text-align:center; margin-bottom:24rpx; }
.pc-num { font-size:80rpx; font-weight:900; color:#1e293b; } .pc-unit { font-size:28rpx; color:#667085; }
.pc-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; } .pc-desc.warn { color:#dc2626; }
.pc-warn { margin-top:16rpx; padding:16rpx; background:#fef2f2; border-radius:12rpx; } .pc-warn text { font-size:24rpx; color:#dc2626; }

.menu-card { background:#fff; margin:0 24rpx 24rpx; border-radius:20rpx; }
.menu-item { display:flex; align-items:center; padding:28rpx; border-bottom:1rpx solid #f1f5f9; }
.mi-icon { font-size:36rpx; margin-right:16rpx; } .mi-body { flex:1; } .mi-label { font-size:28rpx; color:#1e293b; display:block; } .mi-desc { font-size:22rpx; color:#94a3b8; }
.mi-arrow { font-size:32rpx; color:#cbd5e1; }
.footer { text-align:center; font-size:20rpx; color:#cbd5e1; padding:24rpx; }

/* ── 登录底部弹层 ── */
.sheet-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:500; display:flex; align-items:flex-end; }
.sheet { width:100%; background:#fff; border-radius:24rpx 24rpx 0 0; padding:32rpx 28rpx 48rpx; text-align:center; }
.sheet-handle { width:60rpx; height:6rpx; background:#e2e8f0; border-radius:3rpx; margin:0 auto 24rpx; }
.sheet-title { display:block; font-size:34rpx; font-weight:800; color:#1e293b; }
.sheet-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; margin-bottom:32rpx; }
.sheet-btn { width:100%; border-radius:16rpx; font-size:30rpx; font-weight:600; padding:24rpx 0; margin-bottom:16rpx; }
.sheet-btn.primary { background:#07c160; color:#fff; }
.sheet-btn.secondary { background:#f1f5f9; color:#475569; display:flex; align-items:center; justify-content:center; gap:8rpx; }
.sheet-skip { display:block; font-size:24rpx; color:#94a3b8; padding:12rpx; }
.sheet-privacy { display:block; font-size:20rpx; color:#cbd5e1; margin-top:16rpx; }
</style>
