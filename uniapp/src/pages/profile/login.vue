<template>
  <view class="login-page">
    <view class="hero-area">
      <image class="logo" src="/static/brand-logo.png" mode="aspectFit" />
      <text class="brand">址得选</text>
      <text class="slogan">商业选址初筛参考</text>
    </view>

    <view class="main-section">
      <!-- 手机号快捷登录 -->
      <button class="btn-phone" open-type="getPhoneNumber" @getphonenumber="onWxPhoneLogin">
        手机号快捷登录
      </button>

      <!-- 协议勾选 -->
      <view class="agree-row" @tap="toggleAgree">
        <text class="agree-check">{{ agreed ? '●' : '○' }}</text>
        <text class="agree-text">已阅读并同意《用户协议》《隐私政策》</text>
      </view>
      <text class="agree-err" v-if="showAgreeErr">请先阅读并同意协议</text>

      <!-- 次入口 + 提示 -->
      <text class="quick-hint">若快捷登录不可用，请使用下方密码登录</text>
      <view class="alt-login">
        <text class="alt-link" @tap="goPhoneLogin">手机号密码登录</text>
      </view>
    </view>

    <view class="bottom-section">
      <text class="skip" @tap="goBack">暂不登录</text>
    </view>

    <!-- 手机号密码登录弹层 -->
    <view class="sheet-mask" v-if="showPwdSheet" @tap="showPwdSheet = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">手机号密码登录</text>
        <view class="field-group">
          <text class="field-label">手机号</text>
          <input class="field-input" v-model="phone" type="number" maxlength="11" placeholder="请输入手机号" />
        </view>
        <view class="field-group">
          <text class="field-label">密码</text>
          <input class="field-input" v-model="password" type="password" placeholder="至少 6 位" />
        </view>
        <button class="sheet-submit" :disabled="loading || !phone || password.length < 6" @tap="onPwdLogin">
          {{ loading ? '登录中...' : '登录' }}
        </button>
        <text class="sheet-switch" @tap="showPwdSheet = false; showRegSheet = true">没有账号？去注册</text>
        <text class="sheet-err" v-if="errMsg">{{ errMsg }}</text>
      </view>
    </view>

    <!-- 注册弹层 -->
    <view class="sheet-mask" v-if="showRegSheet" @tap="showRegSheet = false">
      <view class="sheet" @tap.stop>
        <view class="sheet-handle" />
        <text class="sheet-title">手机号注册</text>
        <view class="field-group">
          <text class="field-label">手机号</text>
          <input class="field-input" v-model="regPhone" type="number" maxlength="11" placeholder="请输入手机号" />
        </view>
        <view class="field-group">
          <text class="field-label">密码</text>
          <input class="field-input" v-model="regPassword" type="password" placeholder="至少 6 位" />
        </view>
        <button class="sheet-submit" :disabled="regLoading || !regPhone || regPassword.length < 6" @tap="onRegister">
          {{ regLoading ? '注册中...' : '注册' }}
        </button>
        <text class="sheet-switch" @tap="showRegSheet = false; showPwdSheet = true">已有账号？去登录</text>
        <text class="sheet-err" v-if="errMsg">{{ errMsg }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'

export default {
  data () {
    return {
      agreed: false, showAgreeErr: false,
      showPwdSheet: false, showRegSheet: false,
      phone: '', password: '', regPhone: '', regPassword: '',
      loading: false, regLoading: false, errMsg: ''
    }
  },
  methods: {
    toggleAgree () { this.agreed = !this.agreed; this.showAgreeErr = false },
    goBack () { uni.navigateBack({ delta: 1 }).catch(() => uni.switchTab({ url: '/pages/home/index' })) },
    goPhoneLogin () { this.showPwdSheet = true },
    // ── 微信手机号一键登录 ──
    async onWxPhoneLogin (e) {
      this.showAgreeErr = false
      if (!this.agreed) { this.showAgreeErr = true; return }
      const detail = e.detail || {}
      if (detail.errMsg && detail.errMsg.indexOf('deny') >= 0) { uni.showToast({ title: '授权已取消', icon: 'none' }); return }
      const phoneCode = detail.code
      if (!phoneCode) { uni.showToast({ title: '获取手机号失败', icon: 'none' }); return }
      uni.showLoading({ title: '登录中...' })
      try {
        const loginRes = await new Promise((resolve, reject) => {
          uni.login({ provider: 'weixin', success: resolve, fail: reject })
        })
        if (!loginRes.code) { uni.hideLoading(); uni.showToast({ title: '微信登录失败', icon: 'none' }); return }
        const r = await api.phoneLogin(loginRes.code, phoneCode)
        uni.hideLoading()
        if (r.ok) {
          auth.setToken(r.data.token); auth.setUser(r.data.user)
          if (r.data.wx_mini_openid) uni.setStorageSync('wx_mini_openid', r.data.wx_mini_openid)
          uni.showToast({ title: '登录成功', icon: 'success' })
          setTimeout(() => uni.navigateBack({ delta: 1 }), 600)
        } else {
          const sc = r.statusCode
          if (sc === 404) uni.showToast({ title: '后端登录接口未更新，请重启服务', icon: 'none' })
          else if (sc === 503) uni.showToast({ title: '微信登录配置未完成', icon: 'none' })
          else if (sc === 400) uni.showToast({ title: '微信登录参数无效，请稍后重试', icon: 'none' })
          else uni.showToast({ title: r.data?.detail || '登录失败', icon: 'none' })
        }
      } catch (e) { uni.hideLoading(); uni.showToast({ title: '网络异常', icon: 'none' }) }
    },
    // ── 手机号密码登录 ──
    async onPwdLogin () {
      this.errMsg = ''
      if (!this.phone || this.phone.length < 11) { this.errMsg = '请输入有效手机号'; return }
      if (!this.password || this.password.length < 6) { this.errMsg = '密码至少 6 位'; return }
      this.loading = true
      try {
        const r = await api.request({ url: '/api/auth/login', method: 'POST', data: { phone: this.phone.trim(), password: this.password }, auth: false })
        if (r.ok) {
          auth.setToken(r.data.token); if (r.data.user) auth.setUser(r.data.user)
          uni.showToast({ title: '登录成功', icon: 'success' })
          setTimeout(() => uni.navigateBack({ delta: 1 }), 600)
        } else {
          if (r.statusCode === 401) this.errMsg = '手机号或密码错误'
          else this.errMsg = r.data?.detail || '登录失败'
        }
      } catch (e) { this.errMsg = '网络异常' }
      finally { this.loading = false }
    },
    // ── 注册 ──
    async onRegister () {
      this.errMsg = ''
      if (!this.regPhone || this.regPhone.length < 11) { this.errMsg = '请输入有效手机号'; return }
      if (!this.regPassword || this.regPassword.length < 6) { this.errMsg = '密码至少 6 位'; return }
      this.regLoading = true
      try {
        const r = await api.request({ url: '/api/auth/register', method: 'POST', data: { phone: this.regPhone.trim(), password: this.regPassword }, auth: false })
        if (r.ok) {
          auth.setToken(r.data.token); if (r.data.user) auth.setUser(r.data.user)
          uni.showToast({ title: '注册成功', icon: 'success' })
          setTimeout(() => uni.navigateBack({ delta: 1 }), 600)
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
.login-page { min-height:100vh; background:linear-gradient(180deg,#eaf2ff 0%,#f2f6ff 42%,#f0f4ff 100%); display:flex; flex-direction:column; }
.hero-area { text-align:center; padding:80rpx 0 48rpx; }
.logo { width:80rpx; height:80rpx; border-radius:18rpx; margin:0 auto; display:block; }
.brand { display:block; font-size:36rpx; font-weight:800; color:#17244e; margin-top:16rpx; }
.slogan { display:block; font-size:24rpx; color:#8b99b6; margin-top:6rpx; }
.main-section { flex:1; padding:0 40rpx; }
.btn-phone { width:100%; background:linear-gradient(135deg,#0b3fbd,#315bff); color:#fff; border-radius:14rpx; font-size:32rpx; font-weight:700; padding:26rpx 0; margin-bottom:20rpx; }
.agree-row { display:flex; align-items:center; padding:0 8rpx; margin-bottom:8rpx; }
.agree-check { font-size:24rpx; color:#8b99b6; margin-right:10rpx; }
.agree-text { font-size:24rpx; color:#8b99b6; }
.agree-err { font-size:22rpx; color:#dc2626; padding-left:40rpx; display:block; }
.quick-hint { display:block; text-align:center; font-size:22rpx; color:#cbd5e1; margin-top:12rpx; }
.alt-login { text-align:center; margin-top:20rpx; }
.alt-link { font-size:26rpx; color:#315bff; }
.bottom-section { text-align:center; padding:32rpx 0 48rpx; }
.skip { font-size:26rpx; color:#cbd5e1; }
/* Sheet */
.sheet-mask { position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:500; display:flex; align-items:flex-end; }
.sheet { width:100%; background:#fff; border-radius:24rpx 24rpx 0 0; padding:32rpx 32rpx 48rpx; }
.sheet-handle { width:60rpx; height:6rpx; background:#e2e8f0; border-radius:3rpx; margin:0 auto 28rpx; }
.sheet-title { display:block; font-size:30rpx; font-weight:800; color:#1e293b; text-align:center; margin-bottom:28rpx; }
.field-group { margin-bottom:20rpx; }
.field-label { display:block; font-size:26rpx; font-weight:600; color:#334155; margin-bottom:10rpx; }
.field-input { width:100%; border:1px solid #d1d5db; border-radius:12rpx; padding:18rpx 16rpx; font-size:28rpx; box-sizing:border-box; }
.sheet-submit { width:100%; background:#0f172a; color:#fff; border-radius:14rpx; font-size:30rpx; font-weight:700; padding:22rpx 0; margin-top:8rpx; }
.sheet-submit[disabled] { opacity:0.35; }
.sheet-switch { display:block; text-align:center; font-size:24rpx; color:#315bff; margin-top:16rpx; }
.sheet-err { display:block; text-align:center; font-size:24rpx; color:#dc2626; margin-top:12rpx; }
</style>
