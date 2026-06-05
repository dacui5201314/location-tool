<template>
  <view class="pp-panel" :class="{ guest: !loggedIn }">
    <view class="top">
      <template v-if="loggedIn">
        <view class="top-row">
          <button class="avatar-pick-btn" open-type="chooseAvatar" @chooseavatar="onProfileAvatar" :disabled="avatarUploading">
            <image v-if="displayAvatarUrl" class="avatar-img" :src="displayAvatarUrl" mode="aspectFill" />
            <text v-else class="avatar-fb">👤</text>
          </button>
          <view class="top-mid">
            <view class="name-area">
              <text class="uname" @tap.stop="goEdit">{{ displayName }}</text>
              <text class="uid" v-if="uidText">{{ uidText }}</text>
            </view>
            <view class="identity-line">
              <text class="identity-pill" :class="{ active: memberDays > 0 }" @tap.stop="openRecharge">{{ memberBadgeText }}</text>
              <text class="identity-pill points" @tap.stop="openRecharge">{{ points }}点</text>
            </view>
          </view>
          <text class="edit-link" @tap.stop="goEdit">完善资料</text>
        </view>
      </template>
      <template v-else>
        <view class="guest-card">
          <view class="guest-icon">
            <view class="guest-shield">
              <text class="guest-head"></text>
              <text class="guest-body"></text>
            </view>
          </view>
          <view class="guest-copy">
            <text class="guest-title">登录后查看账户权益</text>
            <text class="guest-desc">同步会员、点数、报告记录和收藏地址</text>
            <button class="top-login" @tap.stop="goLogin">登录 / 注册</button>
          </view>
        </view>
      </template>
      <text class="login-err" v-if="loginErr">{{ loginErr }}</text>
    </view>

    <view class="stats">
      <view class="stat" @tap="$emit('go-tab','records')">
        <view class="stat-icon">▤</view>
        <view class="stat-copy"><text class="sl">分析报告</text><text class="sv">{{ reportCount }}</text><text class="st">查看记录 ›</text></view>
      </view>
      <view class="stat" @tap="$emit('go-tab','favorites')">
        <view class="stat-icon">★</view>
        <view class="stat-copy"><text class="sl">收藏地址</text><text class="sv">{{ favCount }}</text><text class="st">管理地址 ›</text></view>
      </view>
      <view class="stat"><view class="stat-icon">▰</view><view class="stat-copy"><text class="sl">剩余点数</text><text class="sv">{{ points }}</text><text class="st">生成报告 ›</text></view></view>
    </view>

    <view class="vip-card">
      <view class="vc-top">
        <view class="vc-copy">
          <view class="vc-kicker"><image class="vc-crown-img" :src="vipCrownIcon" mode="aspectFit" /><text>会员权益</text></view>
          <text class="vc-title">{{ memberTitle }}</text>
          <text class="vc-desc">{{ memberSubtitle }}</text>
        </view>
        <button class="vc-btn" @tap="openRecharge">{{ primaryActionText }}</button>
      </view>
      <view class="vc-benefits">
        <view class="vb" v-for="b in benefits" :key="b.label">
          <text class="vb-icon">{{ b.icon }}</text><text class="vb-label">{{ b.label }}</text><text class="vb-desc">{{ b.desc }}</text>
        </view>
      </view>
    </view>

    <view class="points-card">
      <view class="pc-head">
        <view class="pc-copy">
          <image class="pc-asset-img" :src="coinStackIcon" mode="aspectFit" />
          <view>
            <text class="pc-title">账户点数</text>
            <text class="pc-subtitle">用于生成商业选址分析报告</text>
          </view>
        </view>
        <view class="pc-actions">
          <button class="pca primary" @tap="openRecharge"><text class="pca-icon">◎</text>获取点数</button>
          <button class="pca" @tap="openRedeem">兑换码</button>
        </view>
      </view>
      <view class="pc-body">
        <view class="pc-balance">
          <view class="pc-balance-num">
            <text class="pc-num">{{ points }}</text><text class="pc-unit">点</text>
          </view>
          <text class="pc-desc">{{ pointsHint }}</text>
          <text class="pc-desc warn" v-if="freePointExpiry && !freePointActive">免费赠送点已过期，实际有效 {{ Math.max(0, points - 1) }} 点</text>
        </view>
        <view class="pc-divider"></view>
        <view class="pc-usage">
          <text class="pc-flow-title">点数可用于生成选址分析报告</text>
          <view class="pc-flow">
            <view class="pc-flow-step">
              <text class="pc-flow-icon">⌖</text>
              <text class="pc-flow-label">选地址</text>
            </view>
            <text class="pc-flow-arrow">›</text>
            <view class="pc-flow-step">
              <text class="pc-flow-icon ai">AI</text>
              <text class="pc-flow-label">AI分析</text>
            </view>
            <text class="pc-flow-arrow">›</text>
            <view class="pc-flow-step">
              <text class="pc-flow-icon">▤</text>
              <text class="pc-flow-label">生成报告</text>
            </view>
          </view>
        </view>
      </view>
      <view class="pc-warn" v-if="loggedIn && !memberDays && points <= 3"><text>剩余点数较少，可先使用兑换码或联系客服开通</text></view>
    </view>

    <view class="menu-card">
      <view class="menu-item" @tap="goEdit">
        <text class="mi-icon">◈</text><view class="mi-body"><text class="mi-label">完善资料</text><text class="mi-desc">头像、昵称和联系信息</text></view><text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="openFeedback">
        <text class="mi-icon">✎</text><view class="mi-body"><text class="mi-label">意见反馈</text><text class="mi-desc">告诉我们你的想法，赠送1点</text></view><text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="openContact">
        <text class="mi-icon">☎</text><view class="mi-body"><text class="mi-label">联系客服</text><text class="mi-desc">购买咨询与售后支持</text></view><text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" v-if="loggedIn" @tap="onLogout">
        <text class="mi-icon muted">×</text><view class="mi-body"><text class="mi-label">退出登录</text><text class="mi-desc">退出当前账户</text></view><text class="mi-arrow">›</text>
      </view>
    </view>

    <view class="footer">会员权益与账户信息以实际页面为准</view>

    <!-- 客服弹层 -->
    <view class="sheet-mask" v-if="csSheetOpen" @tap="csSheetOpen = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" /><text class="sheet-title">联系客服</text>
        <image class="cs-qr-img" v-if="csQrUrl" :src="csQrFullUrl" mode="aspectFit" @tap="previewCsQr" />
        <view class="cs-lines">
          <text class="cs-line" v-if="csWechat" @tap="copyCs(csWechat)">微信：{{ csWechat }}（点击复制）</text>
          <text class="cs-line" v-if="csPhone" @tap="callCs(csPhone)">电话：{{ csPhone }}（点击拨打）</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import auth from '../../utils/auth'
import api from '../../utils/api'
import config from '../../utils/config'
import vipCrownIcon from '../../static/vip-crown.png'
import coinStackIcon from '../../static/coin-stack-v2.png'

export default {
  name: 'ProfilePanel',
  emits: ['go-tab'],
  data () {
    return {
      loggedIn: false, loginErr: '',
      avatarUploading: false, avatarUrl: '', phoneText: '', userName: '', uidText: '',
      points: 0, freePointActive: true, freePointExpiry: '',
      memberDays: 0, memberExpiry: '', reportCount: 0, favCount: 0,
      csQrUrl: '', csWechat: '', csPhone: '',
      vipCrownIcon,
      coinStackIcon,
      csSheetOpen: false,
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
    displayAvatarUrl () {
      const url = this.avatarUrl || ''
      if (!url) return ''
      if (url.indexOf('__tmp__') >= 0 || url.indexOf('tmp.weixin.qq.com') >= 0 || url.indexOf('127.0.0.1:26205') >= 0) return ''
      if (url.startsWith('/assets/')) return config.API_BASE_URL + url
      return url
    },
    displayName () {
      if (this.userName) return this.userName
      if (this.phoneText) return this.phoneText
      return '用户' + (this.uidText ? ' ' + this.uidText : '')
    },
    memberBadgeText () {
      return this.memberDays > 0 ? '年卡会员' : '普通用户'
    },
    memberTitle () {
      return this.memberDays > 0 ? '年卡会员权益生效中' : '开通会员权益'
    },
    memberSubtitle () {
      if (this.memberDays > 0) {
        const expiry = this.formattedMemberExpiry ? '，到期 ' + this.formattedMemberExpiry : ''
        return '剩余 ' + this.memberDays + ' 天' + expiry
      }
      return '适合持续评估多个商铺位置'
    },
    formattedMemberExpiry () {
      return this.formatDateOnly(this.memberExpiry)
    },
    primaryActionText () {
      return this.memberDays > 0 ? '查看续费' : '查看套餐'
    },
    pointsHint () {
      if (!this.loggedIn) return '登录后同步点数和会员权益'
      if (this.points <= 0) return '当前暂无可用点数，可使用兑换码或联系客服'
      return '当前可继续生成选址分析报告'
    },
    csQrFullUrl () {
      if (!this.csQrUrl) return ''
      return this.csQrUrl.startsWith('/') ? config.API_BASE_URL + this.csQrUrl : this.csQrUrl
    }
  },
  mounted () { this.refresh() },
  methods: {
    refresh () { this.refreshState() },
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
            if (p.user) {
              auth.setUser(p.user)
              this.avatarUrl = p.user.avatar_url || p.user.avatarUrl || ''
              this.userName = p.user.nickname || p.user.name || this.userName
              const ph = p.user.phone_number || p.user.phone || ''
              this.phoneText = ph ? ph.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : ''
            }
          }
        }).catch(() => {})
        api.fetchCsQr().then(r => { if (r.ok && r.data) this.csQrUrl = r.data.url || '' }).catch(() => {})
        api.fetchUiConfig().then(r => { if (r.ok && r.data) { this.csWechat = r.data.cs_wechat || ''; this.csPhone = r.data.cs_phone || '' } }).catch(() => {})
      } else {
        this.loggedIn = false
      }
    },
    openRecharge () {
      if (!auth.isLoggedIn()) {
        uni.showModal({
          title: '请先登录',
          content: '登录后才能查看套餐和获取点数',
          confirmText: '去登录',
          cancelText: '稍后',
          success: (res) => {
            if (res.confirm) uni.navigateTo({ url: '/pages/profile/login' })
          }
        })
        return
      }
      uni.navigateTo({ url: '/pages/profile/recharge' })
    },
    openFeedback () { uni.navigateTo({ url: '/pages/profile/feedback' }) },
    openContact () { uni.navigateTo({ url: '/pages/profile/contact' }) },
    openRedeem () {
      if (!auth.isLoggedIn()) {
        uni.showModal({
          title: '请先登录',
          content: '登录后才能使用兑换码激活点数',
          confirmText: '去登录',
          cancelText: '稍后',
          success: (res) => {
            if (res.confirm) uni.navigateTo({ url: '/pages/profile/login' })
          }
        })
        return
      }
      uni.navigateTo({ url: '/pages/profile/redeem' })
    },
    goLogin () { uni.navigateTo({ url: '/pages/profile/login' }) },
    goEdit () {
      if (!auth.isLoggedIn()) {
        uni.showModal({
          title: '请先登录',
          content: '登录后才能完善资料',
          confirmText: '去登录',
          cancelText: '稍后',
          success: (res) => {
            if (res.confirm) uni.navigateTo({ url: '/pages/profile/login' })
          }
        })
        return
      }
      uni.navigateTo({ url: '/pages/profile/edit' })
    },
    async onProfileAvatar (e) {
      if (this.avatarUploading) return
      const url = e.detail && e.detail.avatarUrl; if (!url) return
      this.avatarUploading = true; uni.showLoading({ title: '上传中...' })
      try {
        const uploadR = await api.uploadAvatar(url); uni.hideLoading()
        if (uploadR.ok && uploadR.data && uploadR.data.avatar_url) {
          if (uploadR.data.user) auth.setUser(uploadR.data.user)
          this.avatarUrl = uploadR.data.avatar_url; uni.showToast({ title: '头像已更新', icon: 'success' })
        } else { uni.showToast({ title: uploadR.data?.detail || '头像上传失败', icon: 'none' }) }
      } catch (e) { uni.hideLoading(); uni.showToast({ title: '头像上传失败', icon: 'none' }) }
      this.avatarUploading = false
    },
    copyCs (text) { uni.setClipboardData({ data: text, success: () => uni.showToast({ title: '已复制', icon: 'none' }) }) },
    callCs (phone) { uni.makePhoneCall({ phoneNumber: phone }) },
    previewCsQr () { if (this.csQrFullUrl) uni.previewImage({ urls: [this.csQrFullUrl] }) },
    formatDateOnly (value) {
      if (!value) return ''
      const text = String(value).trim()
      const m = text.match(/^(\d{4})-(\d{2})-(\d{2})/)
      if (m) return m[1] + '-' + m[2] + '-' + m[3]
      const d = new Date(text)
      if (Number.isNaN(d.getTime())) return text
      const y = d.getFullYear()
      const mo = String(d.getMonth() + 1).padStart(2, '0')
      const day = String(d.getDate()).padStart(2, '0')
      return y + '-' + mo + '-' + day
    },
    onLogout () { auth.clearToken(); this.loggedIn = false; this.points = 0; this.reportCount = 0; this.favCount = 0 }
  }
}
</script>

<style scoped>
.pp-panel { min-height:100vh; background:linear-gradient(180deg,#dce4f2,#e0e8f6 42%,#dce4f2); padding-bottom:40rpx; }
.pp-panel.guest { min-height:calc(100vh - 88rpx - env(safe-area-inset-bottom)); }
.top { background:radial-gradient(circle at 76% 34%,rgba(83,137,255,0.42),transparent 25%),linear-gradient(180deg,#0b3fbd,#0d35ad 28%,#151f8f); padding:58rpx 32rpx 72rpx; text-align:center; color:#fff; position:relative; overflow:hidden; }
.top::before { content:''; position:absolute; left:-90rpx; top:-130rpx; width:520rpx; height:260rpx; border-radius:0 0 56% 56%; background:linear-gradient(180deg,rgba(255,255,255,0.15),rgba(255,255,255,0.02)); transform:rotate(8deg); }
.top-row { display:flex; align-items:center; text-align:left; position:relative; z-index:2; }
.avatar-img { width:104rpx; height:104rpx; border-radius:50%; border:4rpx solid rgba(255,255,255,0.42); flex-shrink:0; box-shadow:0 14rpx 28rpx rgba(5,22,88,0.22); }
.avatar-fb { font-size:80rpx; }
.avatar-pick-btn { background:transparent; border:0; padding:0; margin:0; line-height:1; display:flex; align-items:center; justify-content:center; flex-shrink:0; border-radius:50%; }
.avatar-pick-btn::after { border:none; }
.top-mid { flex:1; margin-left:24rpx; }
.name-area { display:inline-block; }
.uname { display:block; font-size:36rpx; font-weight:900; line-height:1.2; }
.uid { display:block; font-size:24rpx; color:rgba(255,255,255,0.72); margin-top:6rpx; }
.identity-line { display:flex; flex-wrap:wrap; gap:10rpx; margin-top:14rpx; }
.identity-pill { display:inline-flex; align-items:center; height:44rpx; padding:0 17rpx; border-radius:999rpx; background:rgba(255,255,255,0.14); border:1rpx solid rgba(255,255,255,0.18); color:rgba(255,255,255,0.84); font-size:23rpx; font-weight:800; }
.identity-pill.active { background:rgba(248,200,97,0.22); border-color:rgba(248,200,97,0.42); color:#fff3c4; }
.identity-pill.points { background:rgba(255,255,255,0.18); color:#fff; }
.edit-link { flex-shrink:0; font-size:24rpx; font-weight:800; color:rgba(255,255,255,0.88); background:rgba(255,255,255,0.14); border:1rpx solid rgba(255,255,255,0.18); border-radius:999rpx; padding:10rpx 17rpx; }
.guest-card { position:relative; z-index:2; display:flex; align-items:center; gap:28rpx; text-align:left; background:radial-gradient(circle at 86% 18%,rgba(92,160,255,0.34),transparent 30%),linear-gradient(135deg,rgba(255,255,255,0.18),rgba(255,255,255,0.08)); border:1rpx solid rgba(194,218,255,0.34); border-radius:24rpx; padding:34rpx 30rpx; overflow:hidden; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.26),0 18rpx 42rpx rgba(2,20,88,0.18); }
.guest-card::after { content:''; position:absolute; right:-130rpx; bottom:-92rpx; width:420rpx; height:220rpx; border:2rpx solid rgba(155,206,255,0.20); border-radius:50%; transform:rotate(-18deg); }
.guest-icon { position:relative; z-index:1; width:112rpx; height:112rpx; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.guest-shield { position:relative; width:98rpx; height:98rpx; background:radial-gradient(circle at 34% 18%,rgba(255,255,255,0.34),transparent 28%),linear-gradient(145deg,#86d0ff 0%,#4b88f5 54%,#2760dd 100%); border-radius:24rpx; box-shadow:0 18rpx 34rpx rgba(7,34,120,0.30),inset 0 2rpx 0 rgba(255,255,255,0.46); overflow:hidden; }
.guest-shield::before { content:''; position:absolute; left:-12rpx; right:-12rpx; bottom:-28rpx; height:62rpx; border-radius:50%; background:rgba(36,83,206,0.30); }
.guest-shield::after { content:''; position:absolute; inset:1rpx; border-radius:23rpx; border:1rpx solid rgba(255,255,255,0.22); }
.guest-head { position:absolute; left:50%; top:25rpx; width:28rpx; height:28rpx; margin-left:-14rpx; border-radius:50%; background:linear-gradient(180deg,#ffffff,#dbe7ff); z-index:2; box-shadow:0 4rpx 10rpx rgba(12,34,102,0.12); }
.guest-body { position:absolute; left:50%; top:59rpx; width:58rpx; height:28rpx; margin-left:-29rpx; border-radius:32rpx 32rpx 10rpx 10rpx; background:linear-gradient(180deg,#f8fbff,#c9dbff); z-index:2; }
.guest-copy { position:relative; z-index:1; min-width:0; flex:1; text-align:left; }
.guest-title { display:block; font-size:38rpx; line-height:1.25; font-weight:900; color:#fff; }
.guest-desc { display:block; font-size:26rpx; line-height:1.55; color:rgba(232,240,255,0.84); margin-top:10rpx; }
.top-login { width:244rpx; height:66rpx; line-height:66rpx; padding:0; background:linear-gradient(135deg,#fff0bd 0%,#ffd166 58%,#e2aa37 100%); color:#432400; border:1px solid rgba(255,255,255,0.66); border-radius:999rpx; font-size:27rpx; font-weight:900; margin:22rpx 0 0 calc(50% - 192rpx); box-shadow:0 18rpx 34rpx rgba(247,190,79,0.30),inset 0 2rpx 0 rgba(255,255,255,0.66); }
.top-login[disabled] { opacity:0.6; } .top-login::after { border:none; }
.login-err { display:block; margin-top:14rpx; font-size:24rpx; color:#fca5a5; }
.stats { display:grid; grid-template-columns:repeat(3,1fr); gap:14rpx; margin:-46rpx 24rpx 24rpx; position:relative; z-index:3; }
.stat { min-height:146rpx; background:linear-gradient(180deg,#ffffff,#f8fbff); border-radius:20rpx; padding:18rpx 14rpx; box-shadow:0 18rpx 38rpx rgba(51,87,150,0.13); border:1rpx solid rgba(219,230,255,0.96); box-sizing:border-box; display:flex; align-items:center; gap:12rpx; }
.stat-icon { width:58rpx; height:58rpx; line-height:58rpx; text-align:center; flex-shrink:0; border-radius:50%; background:linear-gradient(145deg,#eaf2ff,#d9e6ff); color:#315bff; font-size:30rpx; font-weight:900; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.9),0 10rpx 20rpx rgba(49,91,255,0.13); }
.stat-copy { min-width:0; flex:1; text-align:center; }
.sv { display:block; font-size:38rpx; font-weight:900; color:#0f1b3d; line-height:1.1; margin-top:7rpx; }
.sl { display:block; font-size:24rpx; color:#475569; line-height:1.2; font-weight:800; white-space:nowrap; }
.st { display:block; font-size:22rpx; color:#64748b; margin-top:8rpx; white-space:nowrap; }
.vip-card { position:relative; overflow:hidden; background:radial-gradient(circle at 78% 18%,rgba(112,154,255,0.34),transparent 30%),linear-gradient(135deg,#0b3fbd 0%,#1f37c8 50%,#5b3fd9 100%); margin:0 24rpx 20rpx; border-radius:24rpx; padding:30rpx 28rpx 32rpx; color:#fff; box-shadow:0 24rpx 52rpx rgba(49,91,255,0.24),inset 0 1rpx 0 rgba(255,255,255,0.18); border:1rpx solid rgba(194,218,255,0.22); }
.vip-card::before { content:''; position:absolute; right:-150rpx; bottom:-90rpx; width:520rpx; height:320rpx; border:2rpx solid rgba(188,205,255,0.18); border-radius:50%; transform:rotate(-22deg); }
.vip-card::after { content:''; position:absolute; right:-190rpx; bottom:28rpx; width:560rpx; height:260rpx; border-top:2rpx solid rgba(188,205,255,0.14); border-radius:50%; transform:rotate(-14deg); }
.vc-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:24rpx; }
.vc-copy { min-width:0; padding-right:18rpx; position:relative; z-index:1; }
.vc-kicker { display:flex; align-items:center; gap:8rpx; min-height:32rpx; font-size:24rpx; line-height:32rpx; color:#ffe5a2; font-weight:900; margin-bottom:10rpx; }
.vc-kicker > text { line-height:32rpx; }
.vc-crown-img { width:36rpx; height:30rpx; flex-shrink:0; display:block; transform:translateY(1rpx); }
.vc-title { font-size:36rpx; line-height:1.25; font-weight:900; display:block; color:#fff; }
.vc-desc { font-size:26rpx; line-height:1.55; color:rgba(232,240,255,0.84); display:block; margin-top:10rpx; }
.vc-btn { background:linear-gradient(135deg,#fff0bd 0%,#ffd166 58%,#e2aa37 100%); color:#432400; border-radius:999rpx; font-size:26rpx; font-weight:900; padding:0 30rpx; height:68rpx; line-height:68rpx; border:1px solid rgba(255,255,255,0.66); flex-shrink:0; align-self:center; position:relative; z-index:2; box-shadow:0 18rpx 34rpx rgba(247,190,79,0.26),inset 0 2rpx 0 rgba(255,255,255,0.66); }
.vc-btn::after { border:none; }
.vc-benefits { position:relative; z-index:1; display:grid; grid-template-columns:repeat(3,1fr); gap:28rpx 14rpx; padding-top:12rpx; }
.vb { min-width:0; text-align:center; border-radius:18rpx; padding:10rpx 4rpx 4rpx; box-sizing:border-box; }
.vb-icon { width:78rpx; height:78rpx; line-height:78rpx; margin:0 auto; border-radius:50%; background:linear-gradient(145deg,rgba(255,255,255,0.18),rgba(255,255,255,0.05)); border:1rpx solid rgba(255,255,255,0.24); color:#ffd875; font-size:34rpx; font-weight:900; display:block; box-shadow:inset 0 2rpx 0 rgba(255,255,255,0.20),0 16rpx 28rpx rgba(0,0,0,0.18); }
.vb-label { font-size:25rpx; display:block; margin-top:15rpx; font-weight:900; line-height:1.2; color:#fff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.vb-desc { font-size:23rpx; color:rgba(232,240,255,0.74); display:block; margin-top:8rpx; line-height:1.25; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.points-card { background:linear-gradient(180deg,#ffffff,#f9fbff); margin:0 24rpx 20rpx; border-radius:22rpx; padding:28rpx; box-shadow:0 18rpx 38rpx rgba(51,87,150,0.13); border:1rpx solid rgba(219,230,255,0.96); }
.pc-head { display:flex; justify-content:space-between; align-items:center; gap:16rpx; margin-bottom:24rpx; }
.pc-copy { display:flex; align-items:center; gap:18rpx; min-width:0; flex:1; }
.pc-asset-img { width:96rpx; height:76rpx; flex-shrink:0; display:block; filter:drop-shadow(0 12rpx 18rpx rgba(244,173,22,0.20)); }
.pc-title { display:block; font-size:29rpx; font-weight:900; color:#1e293b; line-height:1.2; }
.pc-subtitle { display:block; font-size:24rpx; color:#8b99b6; margin-top:8rpx; line-height:1.45; }
.pc-actions { display:flex; flex-direction:row; align-items:center; gap:12rpx; flex-shrink:0; }
.pca { min-width:132rpx; height:62rpx; line-height:62rpx; margin:0; padding:0 18rpx; border-radius:14rpx; background:#fff; color:#1646d2; font-size:25rpx; font-weight:900; border:1rpx solid rgba(49,91,255,0.30); box-shadow:0 8rpx 18rpx rgba(49,91,255,0.08); }
.pca.primary { background:linear-gradient(135deg,#fff0bd 0%,#ffd166 58%,#e2aa37 100%); color:#432400; box-shadow:0 14rpx 26rpx rgba(248,200,97,0.24),inset 0 2rpx 0 rgba(255,255,255,0.66); border-color:rgba(255,255,255,0.66); }
.pca::after { border:none; }
.pca-icon { font-size:25rpx; margin-right:8rpx; }
.pc-body { display:flex; align-items:center; gap:24rpx; margin-bottom:20rpx; padding:28rpx 22rpx; border-radius:20rpx; background:radial-gradient(circle at 8% 18%,rgba(49,91,255,0.08),transparent 30%),linear-gradient(180deg,#f9fbff,#f4f7ff); border:1rpx solid rgba(219,230,255,0.96); box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.92); }
.pc-balance { width:34%; min-width:0; text-align:center; }
.pc-balance-num { white-space:nowrap; }
.pc-num { font-size:86rpx; font-weight:900; color:#315bff; line-height:1; }
.pc-unit { font-size:28rpx; color:#8b99b6; margin-left:8rpx; }
.pc-desc { display:block; font-size:24rpx; line-height:1.45; color:#7f8eac; margin:12rpx auto 0; max-width:520rpx; } .pc-desc.warn { color:#dc2626; }
.pc-divider { width:1rpx; height:150rpx; background:linear-gradient(180deg,transparent,#dbe6ff,transparent); flex-shrink:0; }
.pc-usage { flex:1; min-width:0; padding:24rpx 18rpx; border-radius:18rpx; background:linear-gradient(180deg,rgba(255,255,255,0.76),rgba(246,249,255,0.76)); border:1rpx solid rgba(219,230,255,0.92); text-align:center; }
.pc-flow-title { display:block; font-size:25rpx; line-height:1.35; font-weight:900; color:#5f6f96; margin-bottom:22rpx; }
.pc-flow { display:flex; align-items:center; justify-content:space-between; gap:8rpx; }
.pc-flow-step { flex:1; min-width:0; text-align:center; }
.pc-flow-icon { width:64rpx; height:64rpx; line-height:64rpx; display:block; margin:0 auto; border-radius:50%; background:#fff; color:#315bff; font-size:32rpx; font-weight:900; box-shadow:0 10rpx 22rpx rgba(49,91,255,0.10),inset 0 1rpx 0 rgba(255,255,255,0.9); }
.pc-flow-icon.ai { border-radius:18rpx; background:linear-gradient(145deg,#2f68ff,#1f49d8); color:#fff; font-size:24rpx; }
.pc-flow-label { display:block; margin-top:12rpx; font-size:23rpx; line-height:1.2; font-weight:900; color:#5f6f96; white-space:nowrap; }
.pc-flow-arrow { flex-shrink:0; font-size:44rpx; line-height:1; font-weight:900; color:#8fa2c7; padding-bottom:32rpx; }
.pc-warn { padding:16rpx; background:#fef2f2; border-radius:14rpx; } .pc-warn text { font-size:24rpx; color:#dc2626; }
.menu-card { background:linear-gradient(180deg,#ffffff,#f9fbff); margin:0 24rpx 24rpx; border-radius:22rpx; overflow:hidden; box-shadow:0 18rpx 38rpx rgba(51,87,150,0.11); border:1rpx solid rgba(219,230,255,0.96); }
.menu-item { display:flex; align-items:center; padding:28rpx; border-bottom:1px solid #edf2fb; }
.mi-icon { width:54rpx; height:54rpx; line-height:54rpx; text-align:center; border-radius:18rpx; background:linear-gradient(180deg,#f2f6ff,#e7eeff); color:#315bff; font-size:30rpx; margin-right:16rpx; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.9); }
.mi-icon.muted { color:#94a3b8; background:#f8fafc; }
.mi-body { flex:1; }
.mi-label { font-size:28rpx; color:#1e293b; font-weight:800; display:block; }
.mi-desc { display:block; color:#8b99b6; font-size:24rpx; margin-top:6rpx; line-height:1.35; }
.mi-arrow { font-size:32rpx; color:#cbd5e1; }
.footer { text-align:center; font-size:22rpx; color:#94a3b8; padding:44rpx 24rpx 44rpx; line-height:1.55; }
.sheet-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:500; display:flex; align-items:flex-end; }
.sheet { width:100%; background:#fff; border-radius:24rpx 24rpx 0 0; padding:32rpx 28rpx 48rpx; text-align:center; max-height:85vh; overflow-y:auto; }
.sheet-handle { width:60rpx; height:6rpx; background:#e2e8f0; border-radius:3rpx; margin:0 auto 24rpx; }
.sheet-title { display:block; font-size:32rpx; font-weight:800; color:#1e293b; } .sheet-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; margin-bottom:28rpx; }
.cs-section { margin:16rpx 0; } .cs-qr-img { width:280rpx; height:280rpx; margin:0 auto; display:block; border:1px solid #e2e8f0; border-radius:16rpx; }
.cs-hint { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; } .cs-lines { padding:16rpx 0; } .cs-line { display:block; font-size:26rpx; color:#315bff; padding:12rpx 0; }
</style>
