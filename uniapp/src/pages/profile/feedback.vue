<template>
  <view class="fb-page">
    <view class="header">
      <text class="brand">址得选</text>
      <text class="title">我的反馈</text>
      <text class="sub">提交问题、查看处理进度和运营回复</text>
    </view>

    <view class="tabs">
      <view class="tab" :class="{ active: activeTab === 'submit' }" @tap="activeTab = 'submit'">提交反馈</view>
      <view class="tab" :class="{ active: activeTab === 'list' }" @tap="switchList">我的反馈</view>
    </view>

    <view class="card" v-if="activeTab === 'submit'">
      <view class="report-context" v-if="reportContext.report_uuid">
        <text class="ctx-label">关联报告</text>
        <text class="ctx-title">{{ reportContext.report_title || '选址报告' }}</text>
        <text class="ctx-sub" v-if="reportContext.report_address">{{ reportContext.report_address }}</text>
      </view>

      <view class="form-group">
        <label>反馈内容 <text class="req">*</text></label>
        <textarea v-model="content" placeholder="请输入至少10个字（例如：报告疑问、功能建议、遇到的问题）" :maxlength="1000" />
        <text class="counter">{{ content.length }}/1000</text>
      </view>
      <view class="form-group">
        <label>联系方式（选填）</label>
        <input v-model="contact" placeholder="手机号或其他联系方式，方便我们联系你" :maxlength="120" />
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

    <view class="list-wrap" v-if="activeTab === 'list'">
      <view class="empty" v-if="!listLoading && !feedbacks.length">
        <text class="empty-icon">📭</text>
        <text class="empty-title">暂无反馈记录</text>
        <text class="empty-sub">提交后，运营回复会显示在这里</text>
        <button class="empty-btn" @tap="activeTab = 'submit'">去提交</button>
      </view>

      <view class="fb-card" v-for="item in feedbacks" :key="item.id">
        <view class="fb-head">
          <text class="fb-source">{{ item.source === 'report_detail' ? '报告反馈' : '我的反馈' }}</text>
          <text class="fb-status" :class="{ done: item.status === 'replied' }">{{ item.status === 'replied' ? '已回复' : '待回复' }}</text>
        </view>
        <view class="fb-report" v-if="item.report_uuid">
          <text class="fb-report-title">{{ item.report_title || '选址报告' }}</text>
          <text class="fb-report-addr" v-if="item.report_address">{{ item.report_address }}</text>
        </view>
        <text class="fb-content">{{ item.content }}</text>
        <view class="thumb-row" v-if="item.images && item.images.length">
          <image class="thumb" v-for="(img, idx) in item.images" :key="idx" :src="assetUrl(img)" mode="aspectFill" @tap="previewImages(item.images, idx)" />
        </view>
        <view class="reply-box" :class="{ pending: item.status !== 'replied' }">
          <text class="reply-label">运营回复</text>
          <text class="reply-text">{{ item.admin_reply || '运营人员查看后会在这里回复' }}</text>
          <text class="reply-time" v-if="item.replied_at">{{ fmtTime(item.replied_at) }}</text>
        </view>
        <text class="created-at">{{ fmtTime(item.created_at) }}</text>
      </view>

      <view class="loading-line" v-if="listLoading">加载中...</view>
    </view>
  </view>
</template>

<script>
import config from '../../utils/config'
import { formatTime } from '../../utils/format'

export default {
  data () {
    return {
      activeTab: 'submit',
      content: '',
      contact: '',
      images: [],
      submitting: false,
      errMsg: '',
      feedbacks: [],
      listLoading: false,
      reportContext: {
        report_uuid: '',
        report_title: '',
        report_address: '',
        source: 'profile'
      }
    }
  },
  onLoad (options = {}) {
    const decodeOpt = (value) => {
      try { return decodeURIComponent(value || '') } catch (e) { return value || '' }
    }
    const reportUuid = decodeOpt(options.report_uuid)
    if (reportUuid) {
      this.reportContext = {
        report_uuid: reportUuid,
        report_title: decodeOpt(options.report_title),
        report_address: decodeOpt(options.report_address),
        source: 'report_detail'
      }
      this.activeTab = 'submit'
    }
    this.loadMyFeedbacks()
  },
  onPullDownRefresh () {
    this.loadMyFeedbacks().finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    switchList () {
      this.activeTab = 'list'
      this.loadMyFeedbacks()
    },
    pickImage () {
      uni.chooseImage({
        count: 3 - this.images.length,
        sizeType: ['compressed'],
        sourceType: ['album', 'camera'],
        success: (res) => { this.images = this.images.concat(res.tempFilePaths).slice(0, 3) }
      })
    },
    removeImg (i) { this.images.splice(i, 1) },
    assetUrl (url) {
      if (!url) return ''
      if (/^https?:\/\//.test(url)) return url
      return config.API_BASE_URL + url
    },
    previewImages (imgs, idx) {
      const urls = (imgs || []).map(this.assetUrl)
      if (!urls.length) return
      uni.previewImage({ urls, current: urls[idx] })
    },
    fmtTime: formatTime,
    async loadMyFeedbacks () {
      const token = uni.getStorageSync('token')
      if (!token) return
      this.listLoading = true
      try {
        const res = await new Promise((resolve, reject) => {
          uni.request({
            url: config.API_BASE_URL + '/api/feedback/my',
            method: 'GET',
            header: { Authorization: 'Bearer ' + token },
            success: resolve,
            fail: reject
          })
        })
        if (res.statusCode >= 200 && res.statusCode < 300) {
          this.feedbacks = (res.data && res.data.feedbacks) || []
        }
      } catch (e) {
        // 列表加载失败不阻塞用户提交反馈
      } finally {
        this.listLoading = false
      }
    },
    async uploadOne (filePath) {
      const token = uni.getStorageSync('token')
      return new Promise((resolve, reject) => {
        uni.uploadFile({
          url: config.API_BASE_URL + '/api/feedback/upload',
          name: 'file',
          filePath,
          header: token ? { Authorization: 'Bearer ' + token } : {},
          success: (res) => {
            try {
              const d = JSON.parse(res.data)
              if (res.statusCode >= 200 && res.statusCode < 300 && d.ok) {
                resolve(d.url)
              } else {
                reject(new Error(d.detail || '图片上传失败'))
              }
            } catch (e) { reject(new Error('图片上传解析失败')) }
          },
          fail: (e) => { reject(new Error(e.errMsg || '图片上传网络异常')) }
        })
      })
    },
    async onSubmit () {
      if (this.submitting) return
      const c = (this.content || '').trim()
      if (c.length < 10) { this.errMsg = '反馈内容至少10个字'; return }
      this.submitting = true; this.errMsg = ''

      try {
        const urls = []
        for (const img of this.images) {
          try {
            const url = await this.uploadOne(img)
            urls.push(url)
          } catch (e) {
            this.errMsg = (e && e.message) || '图片上传失败'
            this.submitting = false
            return
          }
        }

        const token = uni.getStorageSync('token')
        const res = await new Promise((resolve, reject) => {
          uni.request({
            url: config.API_BASE_URL + '/api/feedback',
            method: 'POST',
            header: {
              'Content-Type': 'application/x-www-form-urlencoded',
              ...(token ? { Authorization: 'Bearer ' + token } : {})
            },
            data: {
              content: c,
              contact: (this.contact || '').trim(),
              image_urls: JSON.stringify(urls),
              report_uuid: this.reportContext.report_uuid || '',
              report_title: this.reportContext.report_title || '',
              report_address: this.reportContext.report_address || '',
              source: this.reportContext.source || 'profile'
            },
            success: resolve,
            fail: reject
          })
        })
        const data = res.data
        if (res.statusCode >= 200 && res.statusCode < 300) {
          uni.showToast({ title: data.message || '提交成功', icon: 'none', duration: 2200 })
          this.content = ''
          this.contact = ''
          this.images = []
          await this.loadMyFeedbacks()
          this.activeTab = 'list'
        } else {
          this.errMsg = (data && data.detail) || '提交失败'
        }
      } catch (e) {
        this.errMsg = (e && e.errMsg) || '网络异常，请重试'
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.fb-page { min-height:100vh; padding:0 24rpx 118rpx; background:linear-gradient(180deg,#dce4f2 0%,#e0e8f6 42%,#dce4f2 100%); }
.header { margin:0 -24rpx 22rpx; padding:62rpx 48rpx 82rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.22),transparent 26%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); }
.brand { font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; display:block; }
.title { font-size:42rpx; font-weight:900; color:#fff; display:block; margin-top:2rpx; }
.sub { font-size:24rpx; color:rgba(232,240,255,0.76); margin-top:8rpx; display:block; }
.tabs { margin:-54rpx 0 20rpx; padding:8rpx; border-radius:20rpx; background:#fff; display:flex; gap:8rpx; box-shadow:0 16rpx 36rpx rgba(61,88,135,0.10); position:relative; z-index:1; }
.tab { flex:1; height:72rpx; line-height:72rpx; border-radius:16rpx; text-align:center; font-size:27rpx; font-weight:900; color:#64748b; }
.tab.active { background:#eef4ff; color:#315bff; }
.card, .fb-card, .empty { background:#fff; border-radius:22rpx; padding:32rpx 28rpx; margin-top:20rpx; box-shadow:0 12rpx 30rpx rgba(61,88,135,0.07); border:1rpx solid rgba(213,224,246,0.86); }
.report-context { background:#f8fbff; border:1rpx solid #dbe7fb; border-radius:16rpx; padding:20rpx; margin-bottom:28rpx; }
.ctx-label { display:inline-block; font-size:22rpx; color:#315bff; font-weight:900; background:#eef4ff; padding:5rpx 12rpx; border-radius:999rpx; margin-bottom:12rpx; }
.ctx-title { display:block; font-size:28rpx; font-weight:900; color:#17244e; line-height:1.45; }
.ctx-sub { display:block; font-size:24rpx; color:#64748b; margin-top:8rpx; line-height:1.55; }
.form-group { margin-bottom:26rpx; }
label { font-size:28rpx; font-weight:800; color:#17244e; display:block; margin-bottom:12rpx; }
.req { color:#ef4444; }
textarea { width:100%; height:200rpx; border:1rpx solid #d9e0ea; border-radius:12rpx; padding:14rpx; font-size:28rpx; box-sizing:border-box; color:#17244e; }
input { width:100%; height:76rpx; border:1rpx solid #d9e0ea; border-radius:12rpx; padding:0 14rpx; font-size:28rpx; box-sizing:border-box; color:#17244e; }
.counter { font-size:22rpx; color:#98a2b3; text-align:right; margin-top:6rpx; display:block; }
.submit-btn { width:100%; height:88rpx; line-height:88rpx; background:linear-gradient(135deg,#315bff,#5b4be6); color:#fff; border-radius:16rpx; font-size:30rpx; font-weight:900; }
.submit-btn::after, .empty-btn::after { border:none; }
.submit-btn[disabled] { opacity:.6; }
.err { color:#dc2626; font-size:24rpx; display:block; text-align:center; margin-top:16rpx; }
.img-row { display:flex; flex-wrap:wrap; gap:14rpx; }
.img-item { width:160rpx; height:160rpx; border-radius:12rpx; position:relative; overflow:hidden; }
.img-thumb { width:100%; height:100%; }
.img-del { position:absolute; top:-4rpx; right:-4rpx; width:36rpx; height:36rpx; border-radius:50%; background:#ef4444; color:#fff; font-size:24rpx; text-align:center; line-height:36rpx; }
.add-btn { width:160rpx; height:160rpx; border:2rpx dashed #cbd5e1; border-radius:12rpx; display:flex; align-items:center; justify-content:center; font-size:48rpx; color:#94a3b8; }
.empty { text-align:center; padding:52rpx 28rpx; }
.empty-icon { display:block; font-size:72rpx; }
.empty-title { display:block; margin-top:14rpx; font-size:30rpx; font-weight:900; color:#17244e; }
.empty-sub { display:block; margin-top:8rpx; font-size:25rpx; color:#8b99b6; }
.empty-btn { margin-top:24rpx; width:240rpx; height:72rpx; line-height:72rpx; border-radius:16rpx; background:#eef4ff; color:#315bff; font-size:27rpx; font-weight:900; }
.fb-card { padding:26rpx 24rpx; }
.fb-head { display:flex; justify-content:space-between; align-items:center; gap:12rpx; margin-bottom:16rpx; }
.fb-source { font-size:24rpx; font-weight:900; color:#315bff; background:#eef4ff; border-radius:999rpx; padding:6rpx 14rpx; }
.fb-status { font-size:24rpx; font-weight:900; color:#b45309; background:#fff7ed; border-radius:999rpx; padding:6rpx 14rpx; }
.fb-status.done { color:#047857; background:#ecfdf5; }
.fb-report { background:#f8fbff; border-radius:14rpx; padding:16rpx; margin-bottom:16rpx; border:1rpx solid #e6eefb; }
.fb-report-title { display:block; font-size:26rpx; font-weight:900; color:#17244e; line-height:1.45; }
.fb-report-addr { display:block; font-size:24rpx; color:#64748b; margin-top:6rpx; line-height:1.55; }
.fb-content { display:block; font-size:27rpx; color:#344256; line-height:1.72; word-break:break-all; }
.thumb-row { display:flex; gap:12rpx; flex-wrap:wrap; margin-top:16rpx; }
.thumb { width:128rpx; height:128rpx; border-radius:12rpx; border:1rpx solid #e2e8f0; }
.reply-box { margin-top:20rpx; padding:18rpx 20rpx; border-radius:16rpx; background:#f0fdf4; border-left:6rpx solid #16a34a; }
.reply-box.pending { background:#f8fafc; border-left-color:#cbd5e1; }
.reply-label { display:block; font-size:23rpx; color:#64748b; font-weight:900; margin-bottom:8rpx; }
.reply-text { display:block; font-size:26rpx; color:#334155; line-height:1.65; word-break:break-all; }
.reply-box.pending .reply-text { color:#8b99b6; }
.reply-time, .created-at { display:block; margin-top:12rpx; font-size:22rpx; color:#9aa6bd; }
.created-at { text-align:right; }
.loading-line { text-align:center; padding:34rpx 0; font-size:25rpx; color:#8b99b6; }
</style>
