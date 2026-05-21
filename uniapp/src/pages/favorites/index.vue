<template>
  <view class="fav-page">
    <view class="header">
      <text class="title">收藏地址</text>
      <text class="sub">保存的地址，可随时发起分析</text>
    </view>

    <!-- Summary card — 对齐 Web -->
    <view class="summary-card">
      <text class="sc-text">你已收藏 {{ favorites.length }} 个地址</text>
      <text class="sc-sub">点击卡片可快速开始分析</text>
      <button class="sc-add">＋ 新增地址</button>
    </view>

    <!-- Filter tabs — 对齐 Web -->
    <view class="tabs">
      <view v-for="tab in filterTabs" :key="tab.key" class="tab" :class="{ active: activeFilter === tab.key }" @tap="activeFilter = tab.key">
        {{ tab.label }} {{ counts[tab.key] }}
      </view>
    </view>

    <!-- Loading state -->
    <LoadingRow v-if="loading" />

    <!-- Empty state — 对齐 Web empty card -->
    <EmptyState v-if="!loading && filteredFavorites.length === 0" icon="☆" title="暂无收藏地址" desc="把待评估铺位加入收藏，后续可快速生成报告" />

    <!-- Favorite cards — 对齐 Web FavoriteCard -->
    <view class="list" v-if="!loading && filteredFavorites.length">
      <view class="card" v-for="f in filteredFavorites" :key="f.id">
        <view class="card-body" @tap="onSelect(f)">
          <view class="card-top">
            <text class="card-title">{{ f.title }}</text>
            <text class="badge" :class="f.analyzed ? 'done' : 'pending'">{{ f.analyzed ? '已分析' : '待分析' }}</text>
          </view>
          <view class="card-addr">📍 {{ f.address }}</view>
          <view class="card-time">{{ f.analyzed ? '分析时间' : '收藏时间' }}：{{ f.time }}</view>
        </view>
        <view class="card-actions">
          <button v-if="f.analyzed" class="act" @tap="onViewReport(f)">▤ 查看报告</button>
          <button v-else class="act primary" @tap="onAnalyze(f)">✎ 评估赚钱潜力</button>
          <button class="act danger" @tap="onRemove(f)">删除地址</button>
        </view>
      </view>
    </view>

    <!-- Delete confirm -->
    <view class="modal-mask" v-if="delTarget" @tap="delTarget = null">
      <view class="modal-box" @tap.stop>
        <text class="modal-title">确认删除该收藏地址？</text>
        <text class="modal-body">删除后将从收藏列表移除，已生成的分析记录不会被删除。</text>
        <view class="modal-actions">
          <button class="ma-cancel" @tap="delTarget = null">取消删除</button>
          <button class="ma-confirm" @tap="confirmRemove">确认删除</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import EmptyState from '../../components/empty-state/index.vue'
export default {
  components: { EmptyState },
  data () {
    return {
      loading: false,
      activeFilter: 'all',
      filterTabs: [{ key: 'all', label: '全部' }, { key: 'pending', label: '待分析' }, { key: 'done', label: '已分析' }],
      favorites: [
        { id: 1, title: '北京市朝阳区建国路88号SOHO现代城', address: '北京市朝阳区建国路88号', analyzed: true, time: '2026-05-20', reportId: 60 },
        { id: 2, title: '广州市天河区天河路208号', address: '广州市天河区天河路208号', analyzed: true, time: '2026-05-19', reportId: 65 },
        { id: 3, title: '成都市锦江区春熙路1号', address: '成都市锦江区春熙路1号', analyzed: false, time: '2026-05-18' }
      ],
      delTarget: null
    }
  },
  computed: {
    filteredFavorites () {
      if (this.activeFilter === 'done') return this.favorites.filter(f => f.analyzed)
      if (this.activeFilter === 'pending') return this.favorites.filter(f => !f.analyzed)
      return this.favorites
    },
    counts () {
      const f = this.favorites
      return { all: f.length, pending: f.filter(x => !x.analyzed).length, done: f.filter(x => x.analyzed).length }
    }
  },
  methods: {
    onSelect (f) { uni.navigateTo({ url: '/pages/home/index?addr=' + encodeURIComponent(f.address) }) },
    onViewReport (f) { if (f.reportId) uni.navigateTo({ url: '/pages/report-detail/index?id=' + f.reportId }) },
    onAnalyze () { uni.showToast({ title: '分析功能接入中', icon: 'none' }) },
    onRemove (f) { this.delTarget = f },
    confirmRemove () {
      const idx = this.favorites.indexOf(this.delTarget)
      if (idx >= 0) this.favorites.splice(idx, 1)
      this.delTarget = null
    }
  }
}
</script>

<style scoped>
.fav-page { min-height:100vh; padding:24rpx; background:#eef3f9; }
.header { margin-bottom:20rpx; }
.title { font-size:40rpx; font-weight:800; color:#111827; display:block; }
.sub { font-size:24rpx; color:#667085; }
.summary-card { background:linear-gradient(135deg,#0f172a,#1e40af); border-radius:20rpx; padding:28rpx; color:#fff; margin-bottom:20rpx; }
.sc-text { font-size:30rpx; font-weight:700; display:block; }
.sc-sub { font-size:24rpx; color:rgba(255,255,255,0.7); display:block; margin-top:6rpx; }
.sc-add { margin-top:18rpx; background:rgba(255,255,255,0.15); color:#fff; border-radius:14rpx; font-size:26rpx; padding:14rpx 0; }
.tabs { display:flex; gap:10rpx; margin-bottom:18rpx; }
.tab { padding:12rpx 22rpx; border-radius:20rpx; background:#f1f5f9; font-size:26rpx; color:#475569; }
.tab.active { background:#0f172a; color:#fff; }
.card { background:#fff; border-radius:20rpx; padding:28rpx; margin-bottom:16rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.card-body { margin-bottom:16rpx; }
.card-top { display:flex; justify-content:space-between; align-items:center; }
.card-title { font-size:30rpx; font-weight:700; color:#1e293b; flex:1; }
.badge { font-size:22rpx; padding:4rpx 14rpx; border-radius:12rpx; }
.badge.done { background:#dcfce7; color:#166534; } .badge.pending { background:#fef3c7; color:#92400e; }
.card-addr { font-size:24rpx; color:#64748b; margin-top:8rpx; }
.card-time { font-size:22rpx; color:#94a3b8; margin-top:4rpx; }
.card-actions { display:flex; gap:12rpx; border-top:1rpx solid #f1f5f9; padding-top:14rpx; }
.act { flex:1; font-size:24rpx; border-radius:12rpx; padding:14rpx 0; background:#f1f5f9; color:#475569; }
.act.primary { background:#246bff; color:#fff; }
.act.danger { background:#fef2f2; color:#dc2626; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:20rpx; padding:40rpx; width:560rpx; }
.modal-title { font-size:30rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:12rpx; }
.modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; }
.ma-cancel { background:#f1f5f9; color:#475569; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
.ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
</style>
