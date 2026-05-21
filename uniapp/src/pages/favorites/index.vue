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
    <view class="loading" v-if="loading"><text>...</text><text>加载中...</text></view>

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
          <button v-else class="act primary" @tap="onAnalyze">✎ 评估赚钱潜力</button>
          <button class="act danger" @tap="onRemove(f)">删除地址</button>
        </view>
      </view>
    </view>

    <!-- Delete confirm -->
    <view class="modal-mask" v-if="delTarget" @tap="delTarget = null">
      <view class="modal-box" @tap.stop>
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
          this.errMsg = api.normalizeError(r)
        }
      } catch (e) { this.errMsg = '网络异常，请重试' }
      this.loading = false
    },
    onSelect (f) { uni.navigateTo({ url: '/pages/home/index?addr=' + encodeURIComponent(f.address || f.report_address || '') }) },
    onViewReport (f) {
      const id = f.report_uuid || f.record_id
      if (id) uni.navigateTo({ url: '/pages/report-detail/index?id=' + id })
    },
    onAnalyze () { uni.showToast({ title: '分析联调未开放', icon: 'none' }) },
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
.fav-page { min-height:100vh; padding:24rpx; background:#eef3f9; }
.header { margin-bottom:20rpx; } .title { font-size:40rpx; font-weight:800; color:#111827; display:block; } .sub { font-size:24rpx; color:#667085; }
.login-guide { text-align:center; padding:80rpx 0; } .lg-text { display:block; font-size:28rpx; color:#64748b; margin-bottom:24rpx; } .lg-btn { width:360rpx; background:#07c160; color:#fff; border-radius:40rpx; font-size:30rpx; font-weight:600; padding:20rpx 0; }
.summary-card { background:linear-gradient(135deg,#0f172a,#1e40af); border-radius:20rpx; padding:28rpx; color:#fff; margin-bottom:20rpx; }
.sc-text { font-size:30rpx; font-weight:700; display:block; } .sc-sub { font-size:24rpx; color:rgba(255,255,255,0.7); display:block; margin-top:6rpx; }
.tabs { display:flex; gap:10rpx; margin-bottom:18rpx; } .tab { padding:12rpx 22rpx; border-radius:20rpx; background:#f1f5f9; font-size:26rpx; color:#475569; } .tab.active { background:#0f172a; color:#fff; }
.loading { text-align:center; padding:60rpx 0; font-size:26rpx; color:#94a3b8; }
.error-box { text-align:center; padding:60rpx 0; } .error-box text { display:block; font-size:26rpx; color:#dc2626; margin-bottom:16rpx; } .err-btn { background:#f1f5f9; color:#475569; border-radius:14rpx; padding:16rpx 40rpx; font-size:28rpx; }
.empty { text-align:center; padding:80rpx 0; } .emp-icon { font-size:72rpx; display:block; } .emp-title { font-size:30rpx; font-weight:700; color:#475569; display:block; margin:16rpx 0 8rpx; } .emp-desc { font-size:26rpx; color:#94a3b8; }
.list { padding-top:8rpx; }
.card { background:#fff; border-radius:20rpx; padding:28rpx; margin-bottom:16rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.card-body { margin-bottom:16rpx; }
.card-top { display:flex; justify-content:space-between; align-items:center; } .card-title { font-size:30rpx; font-weight:700; color:#1e293b; flex:1; }
.badge { font-size:22rpx; padding:4rpx 14rpx; border-radius:12rpx; } .badge.done { background:#dcfce7; color:#166534; } .badge.pending { background:#fef3c7; color:#92400e; }
.card-addr { font-size:24rpx; color:#64748b; margin-top:8rpx; } .card-time { font-size:22rpx; color:#94a3b8; margin-top:4rpx; }
.card-actions { display:flex; gap:12rpx; border-top:1rpx solid #f1f5f9; padding-top:14rpx; }
.act { flex:1; font-size:24rpx; border-radius:12rpx; padding:14rpx 0; background:#f1f5f9; color:#475569; } .act.primary { background:#246bff; color:#fff; } .act.danger { background:#fef2f2; color:#dc2626; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:20rpx; padding:40rpx; width:560rpx; } .modal-title { font-size:30rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:12rpx; } .modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; } .ma-cancel { background:#f1f5f9; color:#475569; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; } .ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
</style>
