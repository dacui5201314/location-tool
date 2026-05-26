<template>
  <view class="edit-page">
    <!-- 头像 -->
    <view class="section">
      <view class="sec-title">头像</view>
      <view class="avatar-row">
        <image v-if="displayAvatarUrl" class="avatar-img" :src="displayAvatarUrl" mode="aspectFill" />
        <text v-else class="avatar-fb">👤</text>
        <button class="avatar-btn" open-type="chooseAvatar" @chooseavatar="onChooseAvatar">更换头像</button>
      </view>
    </view>

    <!-- 昵称 -->
    <view class="section">
      <view class="sec-title">昵称</view>
      <input class="nick-input" type="nickname" :value="nickname" placeholder="点击设置昵称" @blur="onNicknameBlur" />
    </view>

    <!-- 手机号 -->
    <view class="section">
      <view class="sec-title">手机号</view>
      <view class="phone-row" v-if="phoneText">
        <text class="phone-val">{{ phoneText }}</text>
        <button class="phone-change" open-type="getPhoneNumber" @getphonenumber="onGetPhoneNumber">更换</button>
      </view>
      <button v-else class="phone-btn" open-type="getPhoneNumber" @getphonenumber="onGetPhoneNumber">📱 绑定手机号</button>
      <text class="hint" v-if="phoneBindErr">{{ phoneBindErr }}</text>
    </view>

    <!-- 错误 -->
    <text class="err" v-if="errMsg">{{ errMsg }}</text>

    <!-- 保存 -->
    <button class="save-btn" @tap="onSave">{{ isOnboarding ? '完成并进入' : '保存' }}</button>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'
import config from '../../utils/config'

export default {
  data () {
    return {
      isOnboarding: false,
      avatarUrl: '',
      avatarChanged: false,
      nickname: '',
      phoneText: '',
      rawPhone: '',
      phoneBindErr: '',
      errMsg: ''
    }
  },
  computed: {
    displayAvatarUrl () {
      const url = this.avatarUrl || ''
      if (!url) return ''
      // 用户刚选择新头像时，允许本地临时路径预览（含 wxfile:// 等）
      if (this.avatarChanged) return url
      // 非预览模式：过滤已知临时/失效头像
      if (url.indexOf('__tmp__') >= 0 || url.indexOf('tmp.weixin.qq.com') >= 0 || url.indexOf('127.0.0.1:26205') >= 0) return ''
      // /assets/ 永久资源补全域名
      if (url.startsWith('/assets/')) return config.API_BASE_URL + url
      return url
    }
  },
  onLoad (options) {
    this.isOnboarding = options && options.onboarding === '1'
  },
  onShow () {
    const user = auth.getUser() || {}
    this.avatarUrl = user.avatar_url || user.avatarUrl || ''
    this.avatarChanged = false
    this.nickname = user.nickname || user.name || ''
    const phone = user.phone_number || user.phone || ''
    this.rawPhone = phone
    this.phoneText = phone ? phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') : ''
  },
  methods: {
    onChooseAvatar (e) {
      const url = e.detail && e.detail.avatarUrl
      if (url) { this.avatarUrl = url; this.avatarChanged = true; this.errMsg = '' }
    },
    onNicknameBlur (e) {
      const val = e.detail && e.detail.value
      if (val && val.trim()) { this.nickname = val.trim(); this.errMsg = '' }
    },
    onGetPhoneNumber (e) {
      this.phoneBindErr = ''
      if (e.detail.errMsg && e.detail.errMsg.indexOf('deny') >= 0) {
        this.phoneBindErr = '授权已取消'; return
      }
      const code = e.detail.code
      if (!code) { this.phoneBindErr = '获取手机号失败'; return }
      api.bindPhone(code).then(r => {
        if (r.ok) {
          this.rawPhone = r.data.phone
          this.phoneText = r.data.phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')
          this.phoneBindErr = ''
        } else {
          if (r.statusCode === 409) this.phoneBindErr = '该手机号已绑定其他账号'
          else this.phoneBindErr = r.data?.detail || '绑定失败'
        }
      }).catch(() => { this.phoneBindErr = '网络异常' })
    },
    async onSave () {
      this.errMsg = ''
      uni.showLoading({ title: '保存中...' })
      let avatarUrl = this.avatarUrl || ''
      // 仅当用户选择了新头像时才上传
      if (this.avatarChanged && avatarUrl && !avatarUrl.startsWith('/assets/')) {
        try {
          let filePath = avatarUrl
          // http/https 临时 URL：先下载到本地再上传
          if (avatarUrl.startsWith('http://') || avatarUrl.startsWith('https://')) {
            const dl = await new Promise((resolve, reject) => {
              uni.downloadFile({ url: avatarUrl, success: resolve, fail: reject })
            })
            if (dl.statusCode < 200 || dl.statusCode >= 300 || !dl.tempFilePath) {
              uni.hideLoading()
              this.errMsg = '头像上传失败，请稍后重试'
              return
            }
            filePath = dl.tempFilePath
          }
          const uploadR = await api.uploadAvatar(filePath)
          if (uploadR.ok && uploadR.data && uploadR.data.avatar_url) {
            avatarUrl = uploadR.data.avatar_url
          } else {
            uni.hideLoading()
            this.errMsg = uploadR.data?.detail || '头像上传失败，请稍后重试'
            return
          }
        } catch (e) {
          uni.hideLoading()
          this.errMsg = '头像上传失败，请稍后重试'
          return
        }
      }
      // 保存昵称到服务器；保存后刷新服务器最新 profile
      try {
        const r = await api.updateProfile({ avatar_url: avatarUrl, nickname: this.nickname })
        uni.hideLoading()
        if (r.ok) {
          if (r.data && r.data.user) auth.setUser(r.data.user)
          // 拉取服务端最新数据确保本地同步
          try {
            const freshest = await api.fetchProfile()
            if (freshest.ok && freshest.data && freshest.data.user) {
              auth.setUser(freshest.data.user)
            }
          } catch (e) { /* soft fail */ }
          this.avatarChanged = false
          uni.showToast({ title: '已保存', icon: 'success' })
          if (this.isOnboarding) {
            setTimeout(() => uni.switchTab({ url: '/pages/profile/index' }), 800)
          } else {
            setTimeout(() => uni.navigateBack({ delta: 1 }), 800)
          }
        } else {
          this.errMsg = r.data?.detail || '保存失败'
        }
      } catch (e) {
        uni.hideLoading()
        this.errMsg = '网络异常，请重试'
      }
    }
  }
}
</script>

<style scoped>
.edit-page { min-height:100vh; background:#eef3f9; padding:24rpx; }
.section { background:#fff; border-radius:16rpx; padding:28rpx; margin-bottom:20rpx; }
.sec-title { font-size:28rpx; font-weight:700; color:#1e293b; margin-bottom:20rpx; }
.avatar-row { display:flex; align-items:center; gap:20rpx; }
.avatar-img { width:100rpx; height:100rpx; border-radius:50rpx; }
.avatar-fb { font-size:80rpx; }
.avatar-btn { background:#f1f5f9; color:#475569; font-size:26rpx; padding:14rpx 24rpx; border-radius:14rpx; }
.nick-input { border:2rpx solid #e2e8f0; border-radius:14rpx; padding:20rpx; font-size:28rpx; background:#fff; }
.phone-row { display:flex; align-items:center; justify-content:space-between; }
.phone-val { font-size:28rpx; color:#1e293b; }
.phone-change { background:#f1f5f9; color:#475569; font-size:24rpx; padding:10rpx 20rpx; border-radius:12rpx; }
.phone-btn { width:100%; background:#07c160; color:#fff; font-size:28rpx; padding:20rpx 0; border-radius:14rpx; font-weight:600; }
.hint { display:block; font-size:22rpx; color:#94a3b8; margin-top:10rpx; }
.err { display:block; font-size:24rpx; color:#dc2626; text-align:center; margin-bottom:16rpx; }
.save-btn { width:100%; background:linear-gradient(135deg,#0f172a,#1e40af); color:#fff; border-radius:16rpx; font-size:30rpx; font-weight:700; padding:22rpx 0; }
</style>
