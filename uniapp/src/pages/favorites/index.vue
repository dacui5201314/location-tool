<template>
  <view class="fav-page">
    <view class="header">
      <text class="title">收藏地址</text>
      <text class="sub">保存的地址，可随时发起分析</text>
    </view>

    <!-- 未登录 -->
    <view class="login-guide" v-if="!isLoggedIn && !loading">
      <text class="lg-text">登录后可查看收藏地址</text>
      <button class="lg-btn" @tap="goLogin">去登录</button>
    </view>

    <!-- Summary card -->
    <view class="summary-card" v-if="isLoggedIn">
      <text class="sc-text">你已收藏 {{ list.length }} 个地址</text>
      <text class="sc-sub" v-if="list.length">点击卡片可快速开始分析</text>
    </view>

    <!-- Filter tabs -->
    <view class="tabs" v-if="isLoggedIn">
      <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @tap="activeTab = tab.key">
        {{ tab.label }} {{ counts[tab.key] || '' }}
      </view>
    </view>

    <!-- Loading -->
    <view class="loading" v-if="loading"><text class="ld-dots">...</text><text class="ld-text">加载中...</text></view>

    <!-- Error -->
    <view class="error-box" v-if="!loading && errMsg && isLoggedIn">
      <text>⚠️ {{ errMsg }}</text>
      <button class="err-btn" @tap="loadFavorites">点击重试</button>
    </view>

    <!-- Empty -->
    <view class="empty" v-if="!loading && !errMsg && isLoggedIn && filteredList.length === 0">
      <text class="emp-icon">☆</text>
      <text class="emp-title">暂无收藏地址</text>
      <text class="emp-desc">把待评估铺位加入收藏，后续可快速生成报告</text>
    </view>

    <!-- Cards -->
    <view class="list" v-if="!loading && !errMsg && filteredList.length">
      <view class="card" v-for="f in filteredList" :key="f.id">
        <view class="card-body" @tap="onSelect(f)">
          <view class="card-top">
            <text class="card-title">{{ favTitle(f) }}</text>
            <text class="badge" :class="f.is_analyzed ? 'done' : 'pending'">{{ f.is_analyzed ? '已分析' : '待分析' }}</text>
          </view>
          <view class="card-addr">📍 {{ f.address || f.report_address || '-' }}</view>
          <view class="card-time">{{ f.is_analyzed ? '分析时间' : '收藏时间' }}：{{ fmtTime(f.created_at) }}</view>
        </view>
        <view class="card-actions">
          <button v-if="f.is_analyzed && (f.report_uuid || f.record_id)" class="act" @tap="onViewReport(f)">▤ 查看报告</button>
          <button v-else class="act primary" @tap="onAnalyze(f)">✎ 评估赚钱潜力</button>
          <button class="act danger" @tap="onRemove(f)">删除地址</button>
        </view>
      </view>
    </view>

    <!-- Delete confirm -->
    <view class="modal-mask" v-if="delTarget">
      <view class="modal-box">
        <text class="modal-title">确认删除该收藏地址？</text>
        <text class="modal-body">删除后将移除真实收藏记录。已生成的分析记录不会被删除。</text>
        <view class="modal-actions">
          <button class="ma-cancel" @tap="delTarget = null">取消删除</button>
          <button class="ma-confirm" :disabled="delLoading" @tap="confirmRemove">{{ delLoading ? '删除中...' : '确认删除' }}</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'
import { formatTime } from '../../utils/format'

export default {
  data () {
    return {
      loading: false, errMsg: '', isLoggedIn: false,
      activeTab: 'all',
      tabs: [{ key:'all',label:'全部' },{ key:'pending',label:'待分析' },{ key:'done',label:'已分析' }],
      list: [],
      delTarget: null, delLoading: false
    }
  },
  computed: {
    filteredList () {
      if (this.activeTab === 'done') return this.list.filter(f => f.is_analyzed)
      if (this.activeTab === 'pending') return this.list.filter(f => !f.is_analyzed)
      return this.list
    },
    counts () {
      const l = this.list
      return { all: l.length, pending: l.filter(f => !f.is_analyzed).length, done: l.filter(f => f.is_analyzed).length }
    }
  },
  onShow () {
    this.isLoggedIn = auth.isLoggedIn()
    if (this.isLoggedIn) this.loadFavorites()
    else { this.list = []; this.errMsg = '' }
  },
  methods: {
    fmtTime: formatTime,
    favTitle (f) { return f.custom_name || f.report_brand_desc || f.address?.slice(0, 30) || '收藏地址' },
    goLogin () { uni.switchTab({ url: '/pages/profile/index' }) },
    async loadFavorites () {
      this.loading = true; this.errMsg = ''
      try {
        const r = await api.fetchFavorites()
        if (r.ok) {
          const data = r.data?.favorites || r.data || []
          this.list = Array.isArray(data) ? data : []
        } else {
          if (r.statusCode === 401) { auth.clearToken(); this.isLoggedIn = false; this.errMsg = '' }
          else { this.errMsg = api.normalizeError(r) }
        }
      } catch (e) { this.errMsg = '网络异常，请重试' }
      finally { this.loading = false }
    },
    onSelect (f) {
      const addr = f.address || f.report_address || ''
      if (addr) uni.setStorageSync('pending_analysis_address', addr)
      uni.switchTab({ url: '/pages/home/index' })
    },
    onViewReport (f) {
      const id = f.report_uuid || f.record_id
      if (id) uni.navigateTo({ url: '/pages/report-detail/index?id=' + id })
    },
    onAnalyze (f) {
      const addr = f.address || f.report_address || ''
      if (addr) uni.setStorageSync('pending_analysis_address', addr)
      uni.switchTab({ url: '/pages/home/index' })
    },
    onRemove (f) { this.delTarget = f },
    async confirmRemove () {
      const f = this.delTarget; if (!f) return
      this.delLoading = true
      try {
        const r = await api.deleteFavorite(f.id)
        if (r.ok || r.statusCode === 404) {
          this.list = this.list.filter(x => x.id !== f.id)
          uni.showToast({ title: '已删除', icon: 'none' })
        } else {
          uni.showToast({ title: api.normalizeError(r), icon: 'none' })
        }
      } catch (e) { uni.showToast({ title: '网络异常', icon: 'none' }) }
      this.delLoading = false; this.delTarget = null
    }
  }
}
</script>

<style scoped>
.fav-page { min-height:100vh; padding:28rpx 24rpx 118rpx; background:radial-gradient(circle at 50% -8%,rgba(49,91,255,0.12),transparent 34%),linear-gradient(180deg,#f8fbff 0%,#f2f6ff 48%,#eef3fb 100%); }
.header { margin-bottom:22rpx; padding:12rpx 4rpx 4rpx; } .title { font-size:42rpx; font-weight:900; color:#071d5d; display:block; } .sub { font-size:24rpx; color:#8b99b6; }
.login-guide { text-align:center; padding:82rpx 28rpx; background:rgba(255,255,255,0.92); border:1px solid rgba(219,230,255,0.9); border-radius:22rpx; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); } .lg-text { display:block; font-size:28rpx; color:#64748b; margin-bottom:24rpx; } .lg-btn { width:360rpx; background:linear-gradient(135deg,#4a75ff,#315bff); color:#fff; border-radius:18rpx; font-size:30rpx; font-weight:800; padding:20rpx 0; box-shadow:0 14rpx 30rpx rgba(49,91,255,0.18); }
.lg-btn::after { border:none; }
.summary-card { background:linear-gradient(135deg,#4a75ff,#315bff 58%,#7c55ff); border-radius:22rpx; padding:30rpx; color:#fff; margin-bottom:20rpx; box-shadow:0 18rpx 42rpx rgba(49,91,255,0.22); }
.sc-text { font-size:30rpx; font-weight:700; display:block; } .sc-sub { font-size:24rpx; color:rgba(255,255,255,0.7); display:block; margin-top:6rpx; }
.tabs { display:flex; gap:12rpx; margin-bottom:18rpx; } .tab { padding:14rpx 26rpx; border-radius:999rpx; background:rgba(255,255,255,0.86); border:1px solid rgba(219,230,255,0.95); font-size:25rpx; font-weight:800; color:#5c677d; box-shadow:0 8rpx 18rpx rgba(74,111,172,0.05); } .tab.active { background:#f3f7ff; color:#315bff; border-color:rgba(88,105,255,0.44); }
.loading { text-align:center; padding:60rpx 0; } .ld-dots { font-size:60rpx; letter-spacing:12rpx; color:#94a3b8; display:block; } .ld-text { font-size:26rpx; color:#94a3b8; display:block; margin-top:8rpx; }
.error-box { text-align:center; padding:70rpx 28rpx; background:rgba(255,255,255,0.92); border:1px solid rgba(254,202,202,0.9); border-radius:22rpx; } .error-box text { display:block; font-size:26rpx; color:#dc2626; margin-bottom:16rpx; } .err-btn { background:#f3f7ff; color:#315bff; border-radius:14rpx; padding:16rpx 40rpx; font-size:28rpx; }
.empty { text-align:center; padding:86rpx 28rpx; background:rgba(255,255,255,0.92); border:1px solid rgba(219,230,255,0.9); border-radius:22rpx; } .emp-icon { font-size:72rpx; display:block; } .emp-title { font-size:30rpx; font-weight:800; color:#17244e; display:block; margin:16rpx 0 8rpx; } .emp-desc { font-size:26rpx; color:#8b99b6; }
.list { padding-top:8rpx; }
.card { background:rgba(255,255,255,0.94); border-radius:22rpx; padding:28rpx; margin-bottom:18rpx; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); border:1px solid rgba(219,230,255,0.92); }
.card-body { margin-bottom:16rpx; }
.card-top { display:flex; justify-content:space-between; align-items:center; } .card-title { font-size:30rpx; font-weight:900; color:#17244e; flex:1; }
.badge { font-size:22rpx; font-weight:800; padding:6rpx 14rpx; border-radius:999rpx; } .badge.done { background:#dcfce7; color:#166534; } .badge.pending { background:#fff7ed; color:#c2410c; }
.card-addr { font-size:24rpx; color:#64748b; margin-top:10rpx; line-height:1.45; } .card-time { font-size:22rpx; color:#8b99b6; margin-top:6rpx; }
.card-actions { display:flex; gap:12rpx; border-top:1rpx solid rgba(219,230,255,0.78); padding-top:16rpx; }
.act { flex:1; font-size:24rpx; font-weight:800; border-radius:14rpx; padding:14rpx 0; background:#f3f7ff; color:#315bff; } .act.primary { background:linear-gradient(135deg,#4a75ff,#315bff); color:#fff; } .act.danger { background:#fff5f5; color:#dc2626; }
.act::after { border:none; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:22rpx; padding:40rpx; width:560rpx; box-shadow:0 24rpx 70rpx rgba(15,23,42,0.18); } .modal-title { font-size:30rpx; font-weight:900; color:#17244e; display:block; margin-bottom:12rpx; } .modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; } .ma-cancel { background:#f3f7ff; color:#315bff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; } .ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
</style>
