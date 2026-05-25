<template>
  <view class="login-page">
    <view class="card">
      <view class="tabs">
        <text class="tab" :class="{ active: mode === 'login' }" @tap="mode = 'login'">登录</text>
        <text class="tab" :class="{ active: mode === 'register' }" @tap="mode = 'register'">注册</text>
      </view>

      <view class="field-group">
        <text class="label">手机号</text>
        <input class="field" v-model="phone" type="number" maxlength="11" placeholder="请输入手机号" />
      </view>
      <view class="field-group">
        <text class="label">密码</text>
        <input class="field" v-model="password" type="password" placeholder="至少 6 位" />
      </view>

      <button class="submit-btn" :disabled="loading || !phone || password.length < 6" @tap="onSubmit">
        {{ loading ? '处理中...' : (mode === 'login' ? '登录' : '注册') }}
      </button>

      <text class="err" v-if="errMsg">{{ errMsg }}</text>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'

export default {
  data () {
    return { mode: 'login', phone: '', password: '', loading: false, errMsg: '' }
  },
  methods: {
    async onSubmit () {
      this.errMsg = ''
      if (!this.phone || this.phone.length < 11) { this.errMsg = '请输入有效手机号'; return }
      if (!this.password || this.password.length < 6) { this.errMsg = '密码至少 6 位'; return }

      this.loading = true
      try {
        const endpoint = this.mode === 'login' ? '/api/auth/login' : '/api/auth/register'
        const r = await api.request({ url: endpoint, method: 'POST', data: { phone: this.phone.trim(), password: this.password }, auth: false })
        if (r.ok) {
          auth.setToken(r.data.token)
          if (r.data.user) auth.setUser(r.data.user)
          uni.showToast({ title: this.mode === 'login' ? '登录成功' : '注册成功', icon: 'success' })
          setTimeout(() => uni.navigateBack({ delta: 1 }), 600)
        } else {
          const detail = r.data?.detail || ''
          if (r.statusCode === 409) this.errMsg = '该手机号已注册，请直接登录'
          else if (r.statusCode === 401) this.errMsg = '手机号或密码错误'
          else this.errMsg = detail || '请求失败，请重试'
        }
      } catch (e) { this.errMsg = '网络异常，请重试' }
      finally { this.loading = false }
    }
  }
}
</script>

<style scoped>
.login-page { min-height:100vh; background:linear-gradient(180deg,#eaf2ff 0%,#f2f6ff 42%,#eef3fb 100%); padding:48rpx 24rpx; }
.card { background:#fff; border-radius:22rpx; padding:40rpx 32rpx; box-shadow:0 12rpx 36rpx rgba(79,119,186,0.10); }
.tabs { display:flex; gap:0; margin-bottom:36rpx; background:#f3f7ff; border-radius:14rpx; padding:6rpx; }
.tab { flex:1; text-align:center; font-size:28rpx; font-weight:700; color:#8b99b6; padding:16rpx 0; border-radius:10rpx; }
.tab.active { background:#315bff; color:#fff; }
.field-group { margin-bottom:24rpx; } .label { display:block; font-size:26rpx; font-weight:600; color:#334155; margin-bottom:10rpx; }
.field { width:100%; border:1px solid #d1d5db; border-radius:12rpx; padding:18rpx 16rpx; font-size:28rpx; box-sizing:border-box; }
.submit-btn { width:100%; background:#0f172a; color:#fff; border-radius:14rpx; font-size:30rpx; font-weight:700; padding:22rpx 0; margin-top:12rpx; }
.submit-btn[disabled] { opacity:0.35; }
.err { display:block; text-align:center; font-size:24rpx; color:#dc2626; margin-top:16rpx; }
</style>
