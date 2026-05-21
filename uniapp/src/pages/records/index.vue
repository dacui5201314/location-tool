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
    <view class="loading" v-if="loading"><text>...</text><text>加载中...</text></view>

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
            <text class="score-num" :style="{ color: sc(r.overall_score) }">{{ r.overall_score }}</text>
            <text class="score-unit">分</text>
          </view>
        </view>
        <view class="card-addr">📍 {{ r.address || '-' }}</view>
        <view class="card-tags">
          <text class="tag" v-if="r.business_type">{{ r.business_type }}</text>
          <text class="tag" v-if="r.brand_desc && r.brand_desc !== r.business_type">{{ r.brand_desc }}</text>
          <text class="tag" v-if="r.store_size > 0">{{ r.store_size }}㎡</text>
        </view>
        <view class="card-footer">
          <text class="time" v-if="r.created_at">分析时间：{{ fmtTime(r.created_at) }}</text>
          <text class="time" v-else>-</text>
          <view class="actions">
            <text class="act" @tap.stop="onDelete(r)">删除</text>
            <text class="act" @tap.stop="onDetail(r)">查看报告</text>
            <text class="act" :class="r.is_pdf_unlocked ? '' : 'lock'">{{ r.is_pdf_unlocked ? '导出PDF' : '导出PDF 🔒' }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Delete confirm -->
    <view class="modal-mask" v-if="delTarget" @tap="delTarget = null">
      <view class="modal-box" @tap.stop>
        <text class="modal-title">确定要删除该条分析记录吗？</text>
        <text class="modal-body">删除后将无法恢复，报告文件也将一并销毁。</text>
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
      tabs: [{ key:'all',label:'全部' },{ key:'done',label:'已完成' },{ key:'analyzing',label:'分析中' },{ key:'exported',label:'已导出' }],
      records: [],
      delTarget: null,
      delLoading: false
    }
  },
  computed: {
    displayList () {
      let r = this.records
      if (this.activeTab === 'exported') r = r.filter(x => x.is_pdf_unlocked)
      if (this.activeTab === 'analyzing') return []
      return r
    },
    counts () {
      const r = this.records
      return { all: r.length, done: r.length, analyzing: 0, exported: r.filter(x => x.is_pdf_unlocked).length }
    }
  },
  onShow () {
    this.isLoggedIn = auth.isLoggedIn()
    if (this.isLoggedIn) this.loadRecords()
  },
  methods: {
    sc: scoreColor,
    fmtTime: formatTime,
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
      } catch (e) { /* network error — keep mock fallback as empty */ }
      this.loading = false
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
        }
      } catch (e) { uni.showToast({ title: '网络异常，请重试', icon: 'none' }) }
      this.delLoading = false; this.delTarget = null
    }
  }
}
</script>

<style scoped>
.records-page { min-height:100vh; padding:24rpx; background:#eef3f9; }
.header { margin-bottom:20rpx; } .title { font-size:40rpx; font-weight:800; color:#111827; display:block; } .sub { font-size:24rpx; color:#667085; margin-top:4rpx; }
.login-guide { text-align:center; padding:80rpx 0; }
.lg-text { display:block; font-size:28rpx; color:#64748b; margin-bottom:24rpx; }
.lg-btn { width:360rpx; background:#07c160; color:#fff; border-radius:40rpx; font-size:30rpx; font-weight:600; padding:20rpx 0; }
.tabs { display:flex; gap:10rpx; padding-bottom:20rpx; }
.tab { padding:14rpx 24rpx; border-radius:24rpx; background:#f1f5f9; font-size:26rpx; color:#475569; }
.tab.active { background:#0f172a; color:#fff; }
.loading { text-align:center; padding:60rpx 0; font-size:26rpx; color:#94a3b8; }
.empty { text-align:center; padding:80rpx 0; } .emp-icon { font-size:72rpx; display:block; } .emp-title { font-size:30rpx; font-weight:700; color:#475569; display:block; margin:16rpx 0 8rpx; } .emp-desc { font-size:26rpx; color:#94a3b8; }
.list { padding-top:8rpx; }
.card { background:#fff; border-radius:20rpx; padding:28rpx; margin-bottom:16rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.card-top { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:8rpx; }
.card-title { font-size:30rpx; font-weight:700; color:#1e293b; flex:1; }
.score-block { text-align:right; } .score-num { font-size:44rpx; font-weight:900; } .score-unit { font-size:22rpx; color:#94a3b8; }
.card-addr { font-size:24rpx; color:#64748b; margin-bottom:10rpx; }
.card-tags { margin-bottom:12rpx; } .tag { display:inline-block; font-size:20rpx; padding:4rpx 12rpx; border-radius:10rpx; background:#f1f5f9; color:#475569; margin-right:8rpx; }
.card-footer { display:flex; justify-content:space-between; align-items:center; font-size:22rpx; color:#94a3b8; border-top:1rpx solid #f1f5f9; padding-top:14rpx; }
.actions { display:flex; gap:16rpx; } .act { color:#246bff; font-size:24rpx; } .act.lock { color:#d6a84f; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:20rpx; padding:40rpx; width:560rpx; }
.modal-title { font-size:30rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:12rpx; }
.modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; }
.ma-cancel { background:#f1f5f9; color:#475569; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
.ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:26rpx; }
</style>
