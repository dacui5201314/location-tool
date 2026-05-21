<template>
  <view class="records-page">
    <!-- Header -->
    <view class="header">
      <text class="title">分析记录</text>
      <text class="sub">历史分析，辅助参考</text>
    </view>

    <!-- Filter tabs — 对齐 Web RecordsView -->
    <view class="tabs">
      <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @tap="activeTab = tab.key">
        <text>{{ tab.label }} {{ tab.count }}</text>
      </view>
    </view>

    <!-- Loading state -->
    <LoadingRow v-if="loading" />

    <!-- Empty state — 对齐 Web empty card -->
    <EmptyState v-if="!loading && filteredRecords.length === 0" icon="📋" title="暂无分析记录" desc="完成一次选址分析后自动保存" />

    <!-- Record cards — 对齐 Web RecordCard -->
    <view class="list" v-if="!loading && filteredRecords.length">
      <view class="card" v-for="r in filteredRecords" :key="r.id" @tap="onDetail(r.id)">
        <view class="card-top">
          <text class="card-title">{{ r.title }}</text>
          <view class="score-block" v-if="r.score > 0">
            <text class="score-num" :style="{ color: sc(r.score) }">{{ r.score }}</text>
            <text class="score-unit">分</text>
          </view>
        </view>
        <view class="card-addr">📍 {{ r.address }}</view>
        <view class="card-tags">
          <text class="tag" v-for="t in r.tags" :key="t">{{ t }}</text>
        </view>
        <view class="card-footer">
          <text class="time">分析时间：{{ r.time }}</text>
          <view class="actions">
            <text class="act" @tap.stop="onDelete(r)">删除</text>
            <text class="act" @tap.stop="onDetail(r.id)">查看报告</text>
            <text class="act" v-if="r.exported">导出PDF</text>
            <text class="act lock" v-else>导出PDF 🔒</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Delete confirm modal -- 对齐 Web -->
    <view class="modal-mask" v-if="delTarget" @tap="delTarget = null">
      <view class="modal-box" @tap.stop>
        <text class="modal-title">确定要删除该条分析记录吗？</text>
        <text class="modal-body">删除后将无法恢复，报告文件也将一并销毁。</text>
        <view class="modal-actions">
          <button class="ma-cancel" @tap="delTarget = null">取消</button>
          <button class="ma-confirm" @tap="confirmDelete">确定删除</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import EmptyState from '../../components/empty-state/index.vue'
import { scoreColor } from '../../utils/format'

export default {
  components: { EmptyState },
  data () {
    return {
      loading: false,
      activeTab: 'all',
      tabs: [
        { key: 'all', label: '全部', count: 12 },
        { key: 'done', label: '已完成', count: 10 },
        { key: 'analyzing', label: '分析中', count: 0 },
        { key: 'exported', label: '已导出', count: 2 }
      ],
      records: [
        { id: 65, title: '民宿青旅 · 天河路208号', address: '广州市天河区天河路208号', tags: ['民宿青旅'], score: 62, time: '2026-05-19 17:38', exported: true },
        { id: 71, title: '洗衣店 · 天河路208号', address: '广州市天河区天河路208号', tags: ['洗衣店'], score: 55, time: '2026-05-20 14:29', exported: false },
        { id: 72, title: '诊所 · 建国路88号', address: '北京市朝阳区建国路88号', tags: ['诊所'], score: 50, time: '2026-05-20 14:30', exported: false },
        { id: 74, title: '健身房 · 春熙路1号', address: '成都市锦江区春熙路1号', tags: ['健身房'], score: 40, time: '2026-05-20 14:33', exported: false }
      ],
      delTarget: null
    }
  },
  computed: {
    filteredRecords () {
      const r = this.records
      if (this.activeTab === 'all') return r
      if (this.activeTab === 'exported') return r.filter(x => x.exported)
      if (this.activeTab === 'analyzing') return []
      return r
    }
  },
  methods: {
    sc: scoreColor,
    onDetail (id) { uni.navigateTo({ url: '/pages/report-detail/index?id=' + id }) },
    onDelete (r) { this.delTarget = r },
    confirmDelete () {
      const idx = this.records.indexOf(this.delTarget)
      if (idx >= 0) this.records.splice(idx, 1)
      this.delTarget = null
      uni.showToast({ title: '已删除', icon: 'none' })
    }
  }
}
</script>

<style scoped>
.records-page { min-height:100vh; padding:24rpx; background:#eef3f9; }
.header { margin-bottom:20rpx; }
.title { font-size:40rpx; font-weight:800; color:#111827; display:block; }
.sub { font-size:24rpx; color:#667085; margin-top:4rpx; }
.tabs { display:flex; gap:10rpx; padding-bottom:20rpx; }
.tab { padding:14rpx 24rpx; border-radius:24rpx; background:#f1f5f9; font-size:26rpx; color:#475569; }
.tab.active { background:#0f172a; color:#fff; }
.list { padding-top:8rpx; }
.card { background:#fff; border-radius:20rpx; padding:28rpx; margin-bottom:16rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.card-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8rpx; }
.card-title { font-size:30rpx; font-weight:700; color:#1e293b; flex:1; }
.score-block { text-align:right; }
.score-num { font-size:44rpx; font-weight:900; } .score-unit { font-size:22rpx; color:#94a3b8; }
.card-addr { font-size:24rpx; color:#64748b; margin-bottom:10rpx; }
.card-tags { margin-bottom:12rpx; }
.tag { display:inline-block; font-size:20rpx; padding:4rpx 12rpx; border-radius:10rpx; background:#f1f5f9; color:#475569; margin-right:8rpx; }
.card-footer { display:flex; justify-content:space-between; align-items:center; font-size:22rpx; color:#94a3b8; border-top:1rpx solid #f1f5f9; padding-top:14rpx; }
.actions { display:flex; gap:16rpx; }
.act { color:#246bff; font-size:24rpx; padding:4rpx 0; }
.act.lock { color:#d6a84f; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:20rpx; padding:40rpx; width:560rpx; }
.modal-title { font-size:30rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:12rpx; }
.modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; }
.ma-cancel { background:#f1f5f9; color:#475569; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
.ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
</style>
