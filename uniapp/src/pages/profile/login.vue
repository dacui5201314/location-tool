<template>
  <view class="login-page">
    <view class="hero-area">
      <image class="logo" src="/static/brand-logo.png" mode="aspectFit" />
      <text class="brand">址得选</text>
      <text class="slogan">商业选址分析参考</text>
    </view>

    <view class="login-card">
      <!-- 模式切换 -->
      <view class="mode-tabs">
        <text class="mtab" :class="{ active: mode === 'quick' }" @tap="switchMode('quick')">快捷登录</text>
        <text class="mtab" :class="{ active: mode === 'pwd' }" @tap="switchMode('pwd')">密码登录</text>
        <text class="mtab" :class="{ active: mode === 'reg' }" @tap="switchMode('reg')">注册</text>
      </view>

      <view class="main-section">
      <!-- 快捷登录 -->
      <view v-if="mode === 'quick'">
        <view class="quick-copy">
          <text class="quick-title">使用微信手机号登录</text>
          <text class="quick-desc">同步会员、点数、报告记录和收藏地址</text>
        </view>
        <button v-if="agreed" class="btn-phone" open-type="getPhoneNumber" @getphonenumber="onWxPhoneLogin">
          手机号快捷登录
        </button>
        <button v-else class="btn-phone" @tap="requireAgreement">
          手机号快捷登录
        </button>
        <text class="quick-hint">若无法使用，请切换至密码登录</text>
      </view>

      <!-- 密码登录 -->
      <view v-if="mode === 'pwd'">
        <view class="form-title">
          <text>账号密码登录</text>
        </view>
        <view class="field-group">
          <text class="field-label">手机号</text>
          <input class="field-input" v-model="phone" type="number" maxlength="11" placeholder="请输入手机号" />
        </view>
        <view class="field-group">
          <text class="field-label">密码</text>
          <input class="field-input" v-model="password" type="password" placeholder="至少 6 位" />
        </view>
        <button class="btn-submit" :disabled="loading || !phone || password.length < 6" @tap="onPwdLogin">
          {{ loading ? '登录中...' : '登录' }}
        </button>
      </view>

      <!-- 注册 -->
      <view v-if="mode === 'reg'">
        <view class="form-title">
          <text>注册新账号</text>
        </view>
        <view class="field-group">
          <text class="field-label">手机号</text>
          <input class="field-input" v-model="regPhone" type="number" maxlength="11" placeholder="请输入手机号" />
        </view>
        <view class="field-group">
          <text class="field-label">密码</text>
          <input class="field-input" v-model="regPassword" type="password" placeholder="至少 6 位" />
        </view>
        <button class="btn-submit" :disabled="regLoading || !regPhone || regPassword.length < 6" @tap="onRegister">
          {{ regLoading ? '注册中...' : '注册' }}
        </button>
      </view>

      <!-- 协议勾选 -->
      <view class="agree-row">
        <text class="agree-check" @tap="toggleAgree">{{ agreed ? '●' : '○' }}</text>
        <text class="agree-text">已阅读并同意</text>
        <text class="agree-link" @tap="openUserAgreement">《用户协议》</text>
        <text class="agree-link" @tap="openPrivacyPolicy">《隐私政策》</text>
      </view>
      <text class="agree-err" v-if="showAgreeErr">请先阅读并同意用户协议和隐私政策</text>

      <text class="err-msg" v-if="errMsg">{{ errMsg }}</text>
      </view>
    </view>

    <view class="bottom-section">
      <text class="skip" @tap="goBack">暂不登录</text>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'

export default {
  data () {
    return {
      mode: 'quick', agreed: false, showAgreeErr: false,
      phone: '', password: '', regPhone: '', regPassword: '',
      loading: false, regLoading: false, errMsg: ''
    }
  },
  methods: {
    toggleAgree () { this.agreed = !this.agreed; this.showAgreeErr = false; this.errMsg = '' },
    switchMode (m) { this.mode = m; this.showAgreeErr = false; this.errMsg = '' },
    goBack () { uni.navigateBack({ delta: 1 }).catch(() => uni.reLaunch({ url: '/pages/home/index' })) },
    openUserAgreement () { uni.navigateTo({ url: '/pages/legal/user-agreement' }) },
    openPrivacyPolicy () { uni.navigateTo({ url: '/pages/legal/privacy-policy' }) },
    requireAgreement () {
      this.showAgreeErr = true
      this.errMsg = ''
    },
    isProfileIncomplete (user) {
      if (!user) return true
      const nick = (user.nickname || user.name || '').trim()
      const av = (user.avatar_url || user.avatarUrl || '')
      // 昵称为空 → 需要补全
      if (!nick) return true
      // 头像是临时URL → 需要补全
      if (av && (av.indexOf('__tmp__') >= 0 || av.indexOf('tmp.weixin.qq.com') >= 0 || av.indexOf('127.0.0.1:26205') >= 0 || av.indexOf('http://tmp/') >= 0)) return true
      // 昵称有值 + 头像为空或为永久URL → 资料可用，不打扰
      return false
    },
    async goToEditOnboarding () {
      uni.navigateTo({ url: '/pages/profile/edit?onboarding=1' })
    },
    handleAfterLogin (user) {
      if (this.isProfileIncomplete(user)) {
        uni.showToast({ title: '请完善个人资料', icon: 'none' })
        setTimeout(() => this.goToEditOnboarding(), 800)
      } else {
        uni.showToast({ title: '登录成功', icon: 'success' })
        setTimeout(() => uni.navigateBack({ delta: 1 }), 600)
      }
    },
    async onWxPhoneLogin (e) {
      this.showAgreeErr = false
      // agreed 已由按钮 v-if 保证，此处不再检查
      const detail = e.detail || {}
      if (detail.errMsg && detail.errMsg.indexOf('deny') >= 0) { this.errMsg = '授权已取消'; return }
      const phoneCode = detail.code
      if (!phoneCode) { this.errMsg = '获取手机号失败'; return }
      uni.showLoading({ title: '登录中...' })
      try {
        const loginRes = await new Promise((resolve, reject) => {
          uni.login({ provider: 'weixin', success: resolve, fail: reject })
        })
        if (!loginRes.code) { uni.hideLoading(); this.errMsg = '微信登录失败'; return }
        const r = await api.phoneLogin(loginRes.code, phoneCode)
        uni.hideLoading()
        if (r.ok) {
          auth.setToken(r.data.token); auth.setUser(r.data.user)
          if (r.data.wx_mini_openid) uni.setStorageSync('wx_mini_openid', r.data.wx_mini_openid)
          this.handleAfterLogin(r.data.user)
        } else {
          const sc = r.statusCode
          if (sc === 404) this.errMsg = '后端登录接口未更新，请重启服务'
          else if (sc === 503) this.errMsg = '微信登录配置未完成'
          else if (sc === 400) {
            if (r.data?.detail === 'invalid_code') {
              this.errMsg = '当前环境无法使用手机号快捷登录，请切换至密码登录'
            } else {
              this.errMsg = r.data?.detail || '登录失败'
            }
          }
          else this.errMsg = r.data?.detail || '登录失败'
        }
      } catch (e) { uni.hideLoading(); this.errMsg = '网络异常' }
    },
    async onPwdLogin () {
      this.errMsg = ''
      if (!this.agreed) { this.requireAgreement(); return }
      if (!this.phone || this.phone.length < 11) { this.errMsg = '请输入有效手机号'; return }
      if (!this.password || this.password.length < 6) { this.errMsg = '密码至少 6 位'; return }
      this.loading = true
      try {
        const r = await api.request({ url: '/api/auth/login', method: 'POST', data: { phone: this.phone.trim(), password: this.password }, auth: false })
        if (r.ok) {
          auth.setToken(r.data.token); if (r.data.user) auth.setUser(r.data.user)
          this.handleAfterLogin(r.data.user)
        } else {
          if (r.statusCode === 401) this.errMsg = '手机号或密码错误'
          else this.errMsg = r.data?.detail || '登录失败'
        }
      } catch (e) { this.errMsg = '网络异常' }
      finally { this.loading = false }
    },
    async onRegister () {
      this.errMsg = ''
      if (!this.agreed) { this.requireAgreement(); return }
      if (!this.regPhone || this.regPhone.length < 11) { this.errMsg = '请输入有效手机号'; return }
      if (!this.regPassword || this.regPassword.length < 6) { this.errMsg = '密码至少 6 位'; return }
      this.regLoading = true
      try {
        const r = await api.request({ url: '/api/auth/register', method: 'POST', data: { phone: this.regPhone.trim(), password: this.regPassword }, auth: false })
        if (r.ok) {
          auth.setToken(r.data.token); if (r.data.user) auth.setUser(r.data.user)
          this.handleAfterLogin(r.data.user)
        } else {
          if (r.statusCode === 409) this.errMsg = '该手机号已注册'
          else this.errMsg = r.data?.detail || '注册失败'
        }
      } catch (e) { this.errMsg = '网络异常' }
      finally { this.regLoading = false }
    }
  }
}
</script>

<style scoped>
.login-page { min-height:100vh; background:linear-gradient(180deg,#dce4f2 0%,#edf3ff 44%,#dce4f2 100%); display:flex; flex-direction:column; padding:0 32rpx calc(44rpx + env(safe-area-inset-bottom)); box-sizing:border-box; }
.hero-area { text-align:center; padding:72rpx 0 34rpx; }
.logo { width:86rpx; height:86rpx; border-radius:22rpx; margin:0 auto; display:block; box-shadow:0 16rpx 34rpx rgba(49,91,255,0.22); }
.brand { display:block; font-size:40rpx; font-weight:900; color:#17244e; margin-top:18rpx; line-height:1.2; }
.slogan { display:block; font-size:26rpx; color:#8b99b6; margin-top:8rpx; }
.login-card { background:rgba(255,255,255,0.96); border:1rpx solid rgba(219,230,255,0.92); border-radius:26rpx; padding:26rpx 26rpx 30rpx; box-shadow:0 18rpx 44rpx rgba(79,119,186,0.14); }
.mode-tabs { display:flex; gap:10rpx; padding:0 0 24rpx; }
.mtab { flex:1; text-align:center; font-size:27rpx; font-weight:900; color:#94a3b8; padding:18rpx 0; border-radius:16rpx; background:#f6f9ff; }
.mtab.active { color:#315bff; background:#eef3ff; box-shadow:inset 0 -4rpx 0 #315bff; }
.main-section { padding:0; }
.quick-copy { text-align:center; padding:10rpx 0 24rpx; }
.quick-title { display:block; font-size:32rpx; font-weight:900; color:#17244e; line-height:1.25; }
.quick-desc { display:block; font-size:25rpx; color:#64748b; margin-top:10rpx; line-height:1.45; }
.btn-phone { width:420rpx; height:78rpx; line-height:78rpx; margin:0 auto 16rpx; padding:0; background:linear-gradient(135deg,#315bff,#0b3fbd); color:#fff; border-radius:999rpx; font-size:28rpx; font-weight:900; box-shadow:0 14rpx 28rpx rgba(49,91,255,0.22); }
.btn-phone::after { border:none; }
.quick-hint { display:block; text-align:center; font-size:24rpx; color:#94a3b8; line-height:1.45; margin-bottom:4rpx; }
.form-title { font-size:30rpx; font-weight:900; color:#17244e; margin:4rpx 0 22rpx; }
.field-group { margin-bottom:22rpx; }
.field-label { display:block; font-size:27rpx; font-weight:900; color:#334155; margin-bottom:12rpx; }
.field-input { width:100%; height:82rpx; line-height:82rpx; border:1rpx solid #d6e0f5; border-radius:16rpx; padding:0 22rpx; font-size:28rpx; box-sizing:border-box; background:#fbfdff; color:#17244e; }
.btn-submit { width:100%; height:84rpx; line-height:84rpx; background:linear-gradient(135deg,#315bff,#0b3fbd); color:#fff; border-radius:16rpx; font-size:29rpx; font-weight:900; padding:0; margin-top:12rpx; box-shadow:0 14rpx 28rpx rgba(49,91,255,0.18); }
.btn-submit::after { border:none; }
.btn-submit[disabled] { background:#eef2f7; color:#a8b2c4; box-shadow:none; opacity:1; }
.agree-row { display:flex; align-items:center; flex-wrap:wrap; margin-top:28rpx; padding:0 4rpx; row-gap:6rpx; }
.agree-check { font-size:26rpx; color:#8b99b6; margin-right:10rpx; }
.agree-text { font-size:25rpx; color:#64748b; }
.agree-link { font-size:25rpx; color:#315bff; font-weight:800; }
.agree-err { font-size:24rpx; line-height:1.45; color:#dc2626; padding-left:40rpx; display:block; margin-top:8rpx; }
.err-msg { display:block; text-align:center; font-size:25rpx; color:#dc2626; margin-top:14rpx; line-height:1.45; }
.bottom-section { text-align:center; padding:36rpx 0 0; margin-top:auto; }
.skip { font-size:27rpx; color:#94a3b8; }
</style>
