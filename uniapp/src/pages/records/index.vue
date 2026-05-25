<template>
  <view class="records-page">
    <view class="header">
      <text class="title">分析记录</text>
      <text class="sub">历史分析，辅助参考</text>
    </view>

    <!-- 未登录引导 -->
    <view class="login-guide" v-if="!isLoggedIn && !loading">
      <text class="lg-text">登录后可查看分析记录</text>
      <button class="lg-btn" @tap="goLogin">去登录</button>
    </view>

    <!-- Filter tabs -->
    <view class="tabs" v-if="isLoggedIn">
      <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @tap="activeTab = tab.key">
        <text>{{ tab.label }} {{ counts[tab.key] || '' }}</text>
      </view>
    </view>

    <!-- Loading -->
    <view class="loading" v-if="loading"><text class="ld-dots">...</text><text class="ld-text">加载中...</text></view>

    <!-- Empty state -->
    <view v-if="!loading && isLoggedIn && displayList.length === 0" class="empty">
      <text class="emp-icon">📋</text>
      <text class="emp-title">暂无分析记录</text>
      <text class="emp-desc">完成一次选址分析后自动保存</text>
    </view>

    <!-- Record cards -->
    <view class="list" v-if="!loading && displayList.length">
      <view class="card" v-for="r in displayList" :key="r.uuid || r.id" @tap="onDetail(r)">
        <view class="card-top">
          <text class="card-title">{{ cardTitle(r) }}</text>
          <view class="score-block" v-if="r.overall_score > 0">
            <text class="stars">{{ stars(r.overall_score) }}</text>
            <text class="score-num" :style="{ color: sc(r.overall_score) }">{{ r.overall_score }}</text>
            <text class="score-unit">分</text>
          </view>
        </view>
        <view class="card-body-row">
          <view class="map-thumb" />
          <view class="card-addr">📍 {{ r.address || '-' }}</view>
        </view>
        <view class="card-tags">
          <text class="tag" v-if="r.business_type">{{ r.business_type }}</text>
          <text class="tag" v-if="r.brand_desc && r.brand_desc !== r.business_type">{{ r.brand_desc }}</text>
          <text class="tag" v-if="r.store_size > 0">{{ r.store_size }}㎡</text>
        </view>
        <view class="card-footer">
          <text class="time" v-if="r.created_at">分析时间：{{ fmtTime(r.created_at) }}</text>
          <text class="time" v-else>-</text>
          <view class="actions">
            <text class="act" @tap="onDelete(r)">删除</text>
            <text class="act" @tap="onDetail(r)">查看报告</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Delete confirm -->
    <view class="modal-mask" v-if="delTarget">
      <view class="modal-box">
        <text class="modal-title">确定要删除该条分析记录吗？</text>
        <text class="modal-body">删除后将无法恢复（真实历史记录）。</text>
        <view class="modal-actions">
          <button class="ma-cancel" @tap="delTarget = null">取消</button>
          <button class="ma-confirm" :disabled="delLoading" @tap="confirmDelete">{{ delLoading ? '删除中...' : '确定删除' }}</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import auth from '../../utils/auth'
import { scoreColor, formatTime } from '../../utils/format'

export default {
  data () {
    return {
      loading: false,
      isLoggedIn: false,
      activeTab: 'all',
      tabs: [{ key:'all',label:'全部' },{ key:'done',label:'已完成' }],
      records: [],
      delTarget: null,
      delLoading: false
    }
  },
  computed: {
    displayList () {
      let r = this.records
      return r
    },
    counts () {
      const r = this.records
      return { all: r.length, done: r.length }
    }
  },
  onShow () {
    this.isLoggedIn = auth.isLoggedIn()
    if (this.isLoggedIn) this.loadRecords()
  },
  methods: {
    sc: scoreColor,
    fmtTime: formatTime,
    stars (score) {
      const n = Math.round(score / 20)
      return '★'.repeat(n) + '☆'.repeat(5 - n)
    },
    cardTitle (r) {
      const parts = [r.brand_desc, r.business_type, r.address?.slice(0, 20)].filter(Boolean)
      return parts[0] || '未命名'
    },
    goLogin () { uni.switchTab({ url: '/pages/profile/index' }) },
    async loadRecords () {
      this.loading = true
      try {
        const r = await api.fetchRecords(1, 50)
        if (r.ok && Array.isArray(r.data?.records)) this.records = r.data.records
        else if (r.ok && Array.isArray(r.data)) this.records = r.data
        else {
          if (r.statusCode === 401) { auth.clearToken(); this.isLoggedIn = false }
          else { uni.showToast({ title: api.normalizeError(r), icon: 'none' }) }
        }
      } catch (e) { uni.showToast({ title: '网络异常', icon: 'none' }) }
      finally { this.loading = false }
    },
    onDetail (r) {
      const id = r.uuid || r.id
      uni.navigateTo({ url: '/pages/report-detail/index?id=' + id })
    },
    onDelete (r) { this.delTarget = r },
    async confirmDelete () {
      const r = this.delTarget; if (!r) return
      this.delLoading = true
      try {
        const res = await api.deleteRecord(r.uuid || r.id)
        if (res.ok) {
          this.records = this.records.filter(x => (x.uuid || x.id) !== (r.uuid || r.id))
          uni.showToast({ title: '已删除', icon: 'none' })
        } else {
          uni.showToast({ title: api.normalizeError(res), icon: 'none' })
        }
      } catch (e) { uni.showToast({ title: '网络异常，请重试', icon: 'none' }) }
      this.delLoading = false; this.delTarget = null
    }
  }
}
</script>

<style scoped>
.records-page { min-height:100vh; padding:0 24rpx 118rpx; background:linear-gradient(180deg,#eaf2ff 0%,#f2f6ff 42%,#eef3fb 100%); }
.header { margin:0 -24rpx 22rpx; padding:62rpx 48rpx 82rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.22),transparent 26%),radial-gradient(circle at 58% 58%,rgba(248,200,97,0.10),transparent 22%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); position:relative; overflow:hidden; }
.header::before { content:''; position:absolute; left:-120rpx; top:-150rpx; width:660rpx; height:320rpx; border-radius:0 0 56% 56%; background:linear-gradient(180deg,rgba(255,255,255,0.16),rgba(255,255,255,0.02)); transform:rotate(8deg); }
.header::after { content:''; position:absolute; right:56rpx; bottom:0; width:38rpx; height:154rpx; border-radius:9rpx 9rpx 0 0; background:linear-gradient(180deg,rgba(219,234,254,0.56),rgba(37,99,235,0.08)); box-shadow:-54rpx 30rpx 0 rgba(191,219,254,0.34),-108rpx 66rpx 0 rgba(191,219,254,0.24),54rpx 20rpx 0 rgba(191,219,254,0.28),106rpx 54rpx 0 rgba(191,219,254,0.18); opacity:0.58; }
.title { font-size:42rpx; font-weight:900; color:#fff; display:block; position:relative; z-index:1; } .sub { font-size:24rpx; color:rgba(232,240,255,0.76); margin-top:8rpx; position:relative; z-index:1; }
.login-guide { text-align:center; padding:64rpx 28rpx; background:rgba(255,255,255,0.92); border:1px solid rgba(219,230,255,0.9); border-radius:22rpx; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); }
.lg-text { display:block; font-size:28rpx; color:#64748b; margin-bottom:22rpx; }
.lg-btn { width:236rpx; height:64rpx; line-height:64rpx; margin:0 auto; padding:0; background:linear-gradient(135deg,#fff3c4,#f8c861 58%,#dba640); color:#17244e; border:1px solid rgba(255,255,255,0.48); border-radius:999rpx; font-size:26rpx; font-weight:900; box-shadow:0 14rpx 28rpx rgba(248,200,97,0.16),inset 0 1rpx 0 rgba(255,255,255,0.45); }
.lg-btn::after { border:none; }
.tabs { display:flex; gap:12rpx; padding-bottom:20rpx; }
.tab { padding:14rpx 26rpx; border-radius:999rpx; background:rgba(255,255,255,0.86); border:1px solid rgba(219,230,255,0.95); font-size:25rpx; font-weight:800; color:#5c677d; box-shadow:0 8rpx 18rpx rgba(74,111,172,0.05); }
.tab.active { background:#f3f7ff; color:#315bff; border-color:rgba(88,105,255,0.44); }
.loading { text-align:center; padding:60rpx 0; } .ld-dots { font-size:60rpx; letter-spacing:12rpx; color:#94a3b8; display:block; } .ld-text { font-size:26rpx; color:#94a3b8; display:block; margin-top:8rpx; }
.empty { text-align:center; padding:86rpx 28rpx; background:rgba(255,255,255,0.92); border:1px solid rgba(219,230,255,0.9); border-radius:22rpx; } .emp-icon { font-size:72rpx; display:block; } .emp-title { font-size:30rpx; font-weight:800; color:#17244e; display:block; margin:16rpx 0 8rpx; } .emp-desc { font-size:26rpx; color:#8b99b6; }
.list { padding-top:8rpx; }
.card { background:rgba(255,255,255,0.94); border-radius:22rpx; padding:28rpx; margin-bottom:18rpx; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); border:1px solid rgba(219,230,255,0.92); }
.card-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8rpx; }
.card-title { font-size:30rpx; font-weight:900; color:#17244e; flex:1; }
.score-block { text-align:right; } .stars { font-size:24rpx; color:#d6a84f; letter-spacing:2rpx; display:block; } .score-num { font-size:44rpx; font-weight:900; } .score-unit { font-size:22rpx; color:#94a3b8; }
.card-body-row { display:flex; align-items:flex-start; gap:14rpx; margin-bottom:12rpx; }
.map-thumb { width:80rpx; height:80rpx; background:#e8edf5; border-radius:10rpx; flex-shrink:0; }
.card-addr { font-size:24rpx; color:#64748b; line-height:1.45; flex:1; }
.card-tags { margin-bottom:14rpx; } .tag { display:inline-block; font-size:20rpx; font-weight:700; padding:6rpx 14rpx; border-radius:999rpx; background:#f3f7ff; color:#315bff; margin-right:8rpx; border:1px solid rgba(219,230,255,0.95); }
.card-footer { display:flex; justify-content:space-between; align-items:center; font-size:22rpx; color:#8b99b6; border-top:1rpx solid rgba(219,230,255,0.78); padding-top:16rpx; }
.actions { display:flex; gap:14rpx; } .act { color:#315bff; font-size:24rpx; font-weight:800; } .act.lock { color:#d6a84f; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:22rpx; padding:40rpx; width:560rpx; box-shadow:0 24rpx 70rpx rgba(15,23,42,0.18); }
.modal-title { font-size:30rpx; font-weight:900; color:#17244e; display:block; margin-bottom:12rpx; }
.modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; }
.ma-cancel { background:#f3f7ff; color:#315bff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
.ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
</style>
