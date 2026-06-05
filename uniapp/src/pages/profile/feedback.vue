<template>
  <view class="fb-page">
    <view class="header">
      <text class="brand">址得选</text>
      <text class="title">意见反馈</text>
      <text class="sub">告诉我们你的想法，首次反馈赠送 1 点</text>
    </view>
    <view class="card">
      <view class="form-group">
        <label>反馈内容 <text class="req">*</text></label>
        <textarea v-model="content" placeholder="请输入至少10个字...&#10;例如：希望增加某个功能、报告哪里不准、遇到了什么问题" :maxlength="1000" />
        <text class="counter">{{ content.length }}/1000</text>
      </view>
      <view class="form-group">
        <label>联系方式（选填）</label>
        <input v-model="contact" placeholder="手机号或微信号，方便我们联系你" :maxlength="120" />
      </view>
      <view class="form-group">
        <label>截图（选填，最多3张）</label>
        <view class="img-row">
          <view class="img-item" v-for="(img, i) in images" :key="i">
            <image :src="img" mode="aspectFill" class="img-thumb" />
            <view class="img-del" @tap="removeImg(i)">×</view>
          </view>
          <view class="add-btn" v-if="images.length < 3" @tap="pickImage">
            <text>+</text>
          </view>
        </view>
      </view>
      <button class="submit-btn" :disabled="submitting" @tap="onSubmit">
        {{ submitting ? '提交中...' : '提交反馈' }}
      </button>
      <text class="err" v-if="errMsg">{{ errMsg }}</text>
    </view>
  </view>
</template>

<script>
import config from '../../utils/config'

export default {
  data () {
    return { content: '', contact: '', images: [], submitting: false, errMsg: '' }
  },
  methods: {
    pickImage () {
      uni.chooseImage({
        count: 3 - this.images.length,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => { this.images = this.images.concat(res.tempFilePaths).slice(0, 3) }
      })
    },
    removeImg (i) { this.images.splice(i, 1) },
    async onSubmit () {
      if (this.submitting) return
      const c = (this.content || '').trim()
      if (c.length < 10) { this.errMsg = '反馈内容至少10个字'; return }
      this.submitting = true; this.errMsg = ''
      const token = uni.getStorageSync('token')
      uni.uploadFile({
        url: config.API_BASE_URL + '/api/feedback',
        name: 'files',
        formData: { content: c, contact: (this.contact || '').trim() },
        filePath: this.images[0] || '',
        files: this.images.map(p => ({ name: 'files', uri: p })),
        header: token ? { Authorization: 'Bearer ' + token } : {},
        success: (res) => {
          try {
            const data = JSON.parse(res.data)
            if (res.statusCode >= 200 && res.statusCode < 300) {
              uni.showToast({ title: data.message || '提交成功', icon: 'none', duration: 2500 })
              setTimeout(() => { uni.navigateBack({ delta: 1 }) }, 1800)
            } else {
              this.errMsg = data.detail || '提交失败'
            }
          } catch (e) { this.errMsg = '提交失败' }
        },
        fail: () => { this.errMsg = '网络异常，请重试' },
        complete: () => { this.submitting = false }
      })
    }
  }
}
</script>

<style scoped>
.fb-page { min-height:100vh; padding:0 24rpx 118rpx; background:linear-gradient(180deg,#dce4f2 0%,#e0e8f6 42%,#dce4f2 100%); }
.header { margin:0 -24rpx 22rpx; padding:62rpx 48rpx 82rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.22),transparent 26%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); }
.brand { font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; display:block; }
.title { font-size:42rpx; font-weight:900; color:#fff; display:block; margin-top:2rpx; }
.sub { font-size:24rpx; color:rgba(232,240,255,0.76); margin-top:8rpx; }
.card { background:#fff; border-radius:22rpx; padding:32rpx 28rpx; margin-top:20rpx; }
.form-group { margin-bottom:26rpx; }
label { font-size:28rpx; font-weight:800; color:#17244e; display:block; margin-bottom:12rpx; }
.req { color:#ef4444; }
textarea { width:100%; height:200rpx; border:1rpx solid #d9e0ea; border-radius:12rpx; padding:14rpx; font-size:28rpx; box-sizing:border-box; }
input { width:100%; height:76rpx; border:1rpx solid #d9e0ea; border-radius:12rpx; padding:0 14rpx; font-size:28rpx; box-sizing:border-box; }
.counter { font-size:22rpx; color:#98a2b3; text-align:right; margin-top:6rpx; display:block; }
.submit-btn { width:100%; height:88rpx; line-height:88rpx; background:linear-gradient(135deg,#315bff,#5b4be6); color:#fff; border-radius:16rpx; font-size:30rpx; font-weight:900; }
.submit-btn::after { border:none; }
.submit-btn[disabled] { opacity:.6; }
.err { color:#dc2626; font-size:24rpx; display:block; text-align:center; margin-top:16rpx; }
.img-row { display:flex; flex-wrap:wrap; gap:14rpx; }
.img-item { width:160rpx; height:160rpx; border-radius:12rpx; position:relative; overflow:hidden; }
.img-thumb { width:100%; height:100%; }
.img-del { position:absolute; top:-4rpx; right:-4rpx; width:36rpx; height:36rpx; border-radius:50%; background:#ef4444; color:#fff; font-size:24rpx; text-align:center; line-height:36rpx; }
.add-btn { width:160rpx; height:160rpx; border:2rpx dashed #cbd5e1; border-radius:12rpx; display:flex; align-items:center; justify-content:center; font-size:48rpx; color:#94a3b8; }
</style>
