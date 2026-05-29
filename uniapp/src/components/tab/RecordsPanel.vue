<template>
  <view class="rp-panel" :class="{ guest: !isLoggedIn && !loading }">
    <view class="header">
      <text class="brand">址得选</text>
      <text class="title">分析记录</text>
      <text class="sub">历史分析报告 · 辅助参考</text>
    </view>

    <view class="login-guide" v-if="!isLoggedIn && !loading">
      <view class="lg-visual records">
        <text class="lg-doc">▤</text>
      </view>
      <text class="lg-title">登录后可查看分析记录</text>
      <button class="lg-btn" @tap="$emit('go-tab','profile')">去登录</button>
      <text class="lg-text">登录后同步你的历史报告，重要分析不丢失</text>
    </view>

    <view class="login-benefits" v-if="!isLoggedIn && !loading">
      <text class="lb-title">分析记录 · 持续沉淀判断</text>
      <view class="lb-grid">
        <view class="lb-item">
          <text class="lb-icon rec-archive">▤</text>
          <text class="lb-name">保存历史报告</text>
          <text class="lb-desc">复盘选址判断</text>
        </view>
        <view class="lb-item">
          <text class="lb-icon rec-compare">⌁</text>
          <text class="lb-name">快速对比铺位</text>
          <text class="lb-desc">辅助横向筛选</text>
        </view>
        <view class="lb-item">
          <text class="lb-icon rec-sync">↻</text>
          <text class="lb-name">多端同步查看</text>
          <text class="lb-desc">报告随时可查</text>
        </view>
      </view>
    </view>

    <view class="tabs" v-if="isLoggedIn">
      <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @tap="activeTab = tab.key">
        <text>{{ tab.label }} {{ counts[tab.key] || '' }}</text>
      </view>
    </view>

    <view class="loading" v-if="loading"><text class="ld-dots">...</text><text class="ld-text">加载中...</text></view>

    <view v-if="!loading && isLoggedIn && displayList.length === 0" class="empty">
      <text class="emp-icon">📋</text>
      <text class="emp-title">暂无分析记录</text>
      <text class="emp-desc">完成一次选址分析后自动保存</text>
      <button class="emp-btn" @tap="$emit('go-tab','home')">去生成第一份报告</button>
    </view>

    <view class="list" v-if="!loading && displayList.length">
      <view class="card report-card" v-for="r in displayList" :key="r.report_uuid || r.id || ''" @tap="onDetail(r)">
        <view class="card-top">
          <text class="card-title">{{ cardTitle(r) }}</text>
          <text class="status-pill">已完成</text>
          <view class="score-block" v-if="r.overall_score > 0">
            <text class="score-num" :style="{ color: sc(r.overall_score) }">{{ r.overall_score }}</text>
            <text class="score-unit">分</text>
            <text class="stars">{{ stars(r.overall_score) }}</text>
          </view>
        </view>
        <view class="card-body-row">
          <view class="map-thumb"><text class="mt-icon">📍</text></view>
          <view class="card-mid">
            <text class="card-addr">{{ displayAddress(r.address) }}</text>
            <text class="card-time" v-if="r.created_at">{{ fmtTime(r.created_at) }}</text>
          </view>
        </view>
        <view class="card-tags">
          <text class="tag" v-if="r.business_type">{{ r.business_type }}</text>
          <text class="tag" v-if="r.brand_desc && r.brand_desc !== r.business_type">{{ r.brand_desc }}</text>
          <text class="tag" v-if="r.store_size > 0">{{ r.store_size }}㎡</text>
        </view>
        <view class="card-footer">
          <view class="actions">
            <text class="act primary" @tap.stop="onDetail(r)">查看完整报告</text>
            <text class="act danger" @tap.stop="onDelete(r)">删除</text>
          </view>
        </view>
      </view>
    </view>

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
  name: 'RecordsPanel',
  emits: ['go-tab'],
  data () {
    return {
      loading: false, isLoggedIn: false,
      activeTab: 'all',
      tabs: [{ key:'all',label:'全部' },{ key:'done',label:'已完成' }],
      records: [], delTarget: null, delLoading: false
    }
  },
  computed: {
    displayList () { return this.records },
    counts () {
      const r = this.records
      return { all: r.length, done: r.length }
    }
  },
  mounted () {
    this.isLoggedIn = auth.isLoggedIn()
    if (this.isLoggedIn) this.loadRecords()
  },
  methods: {
    sc: scoreColor, fmtTime: formatTime,
    stars (score) {
      const v = Math.max(0, Math.min(5, Math.round(Number(score || 0) / 20)))
      return '★'.repeat(v) + '☆'.repeat(5 - v)
    },
    cardTitle (r) {
      const parts = [r.brand_desc, r.business_type, r.address?.slice(0, 20)].filter(Boolean)
      return parts[0] || '未命名'
    },
    displayAddress (addr) {
      return addr || '-'
    },
    refresh () {
      this.isLoggedIn = auth.isLoggedIn()
      if (this.isLoggedIn) this.loadRecords()
    },
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
      if (r.report_uuid) {
        uni.navigateTo({ url: '/pages/report-detail/index?id=' + r.report_uuid })
      } else if (r.id) {
        uni.showToast({ title: '历史记录缺少报告编号，请在 Web 端查看', icon: 'none' })
      } else {
        uni.showToast({ title: '记录数据异常', icon: 'none' })
      }
    },
    onDelete (r) { this.delTarget = r },
    async confirmDelete () {
      const r = this.delTarget; if (!r) return
      this.delLoading = true
      try {
        const res = await api.deleteRecord(r.report_uuid || String(r.id))
        if (res.ok) {
          this.records = this.records.filter(x => (x.report_uuid || String(x.id)) !== (r.report_uuid || String(r.id)))
          uni.showToast({ title: '已删除', icon: 'none' })
        } else { uni.showToast({ title: api.normalizeError(res), icon: 'none' }) }
      } catch (e) { uni.showToast({ title: '网络异常，请重试', icon: 'none' }) }
      this.delLoading = false; this.delTarget = null
    }
  }
}
</script>

<style scoped>
.rp-panel { min-height:100vh; background:linear-gradient(180deg,#dce4f2,#e0e8f6 42%,#dce4f2); padding:0 24rpx 40rpx; }
.rp-panel.guest { min-height:calc(100vh - 88rpx - env(safe-area-inset-bottom)); background:#dce4f2; }
.header { margin:0 -24rpx 22rpx; padding:62rpx 48rpx 82rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.22),transparent 26%),radial-gradient(circle at 58% 58%,rgba(248,200,97,0.10),transparent 22%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); position:relative; overflow:hidden; }
.rp-panel.guest .header { margin-bottom:0; padding:78rpx 48rpx 178rpx; }
.header::before { content:''; position:absolute; left:-120rpx; top:-150rpx; width:660rpx; height:320rpx; border-radius:0 0 56% 56%; background:linear-gradient(180deg,rgba(255,255,255,0.16),rgba(255,255,255,0.02)); transform:rotate(8deg); }
.header::after { content:''; position:absolute; right:56rpx; bottom:0; width:38rpx; height:154rpx; border-radius:9rpx 9rpx 0 0; background:linear-gradient(180deg,rgba(219,234,254,0.56),rgba(37,99,235,0.08)); box-shadow:-54rpx 30rpx 0 rgba(191,219,254,0.34),-108rpx 66rpx 0 rgba(191,219,254,0.24),54rpx 20rpx 0 rgba(191,219,254,0.28),106rpx 54rpx 0 rgba(191,219,254,0.18); opacity:0.58; }
.brand { font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; text-transform:uppercase; position:relative; z-index:1; display:block; }
.title { font-size:42rpx; font-weight:900; color:#fff; display:block; position:relative; z-index:1; margin-top:2rpx; }
.sub { font-size:26rpx; color:rgba(232,240,255,0.82); margin-top:8rpx; position:relative; z-index:1; line-height:1.45; }
.login-guide { position:relative; z-index:2; text-align:center; padding:72rpx 32rpx 56rpx; margin-top:-46rpx; background:linear-gradient(180deg,rgba(255,255,255,0.99),rgba(255,255,255,0.95)); border:1px solid rgba(255,255,255,0.86); border-radius:28rpx; box-shadow:0 24rpx 52rpx rgba(45,78,145,0.13),inset 0 1rpx 0 rgba(255,255,255,0.72); overflow:hidden; }
.rp-panel.guest .login-guide { margin-top:-96rpx; padding:88rpx 32rpx 68rpx; background:linear-gradient(180deg,rgba(255,255,255,0.99),rgba(255,255,255,0.95)); border:1px solid rgba(255,255,255,0.86); border-radius:28rpx; box-shadow:0 24rpx 52rpx rgba(5,22,88,0.18),inset 0 1rpx 0 rgba(255,255,255,0.72); }
.login-guide::before { content:''; position:absolute; left:50%; top:68rpx; width:280rpx; height:150rpx; transform:translateX(-50%); border-radius:50%; background:radial-gradient(circle,rgba(49,91,255,0.14),rgba(49,91,255,0)); }
.lg-visual { position:relative; z-index:1; width:150rpx; height:128rpx; margin:0 auto 22rpx; display:flex; align-items:center; justify-content:center; }
.lg-visual::before { content:''; position:absolute; left:14rpx; right:14rpx; bottom:8rpx; height:30rpx; border-radius:50%; background:rgba(49,91,255,0.10); filter:blur(2rpx); }
.lg-doc { position:relative; z-index:1; display:flex; align-items:center; justify-content:center; width:104rpx; height:116rpx; border-radius:24rpx; background:linear-gradient(145deg,#8fb7ff 0%,#315bff 72%,#1f37c8 100%); color:#fff; font-size:43rpx; line-height:1; box-shadow:0 18rpx 34rpx rgba(49,91,255,0.24),inset 0 2rpx 0 rgba(255,255,255,0.35); }
.lg-doc::after { content:''; position:absolute; right:16rpx; top:16rpx; width:26rpx; height:26rpx; border-top:8rpx solid rgba(255,255,255,0.36); border-right:8rpx solid rgba(255,255,255,0.36); border-radius:4rpx; }
.lg-title { position:relative; z-index:1; display:block; font-size:34rpx; color:#17244e; font-weight:900; line-height:1.35; margin-bottom:24rpx; }
.lg-text { position:relative; z-index:1; display:block; font-size:25rpx; color:#6b7a99; line-height:1.55; margin-top:24rpx; }
.lg-btn { position:relative; z-index:1; width:280rpx; height:76rpx; line-height:76rpx; margin:0 auto; padding:0; background:linear-gradient(135deg,#fff0bd 0%,#f8c861 54%,#dba640 100%); color:#4a2600; border:1px solid rgba(255,255,255,0.70); border-radius:999rpx; font-size:29rpx; font-weight:900; box-shadow:0 18rpx 34rpx rgba(248,200,97,0.28),inset 0 2rpx 0 rgba(255,255,255,0.62); }
.lg-btn::after { border:none; }
.login-benefits { margin-top:22rpx; padding:30rpx 28rpx; background:rgba(255,255,255,0.82); border:1px solid rgba(255,255,255,0.78); border-radius:24rpx; box-shadow:0 18rpx 42rpx rgba(79,119,186,0.08),inset 0 1rpx 0 rgba(255,255,255,0.66); }
.rp-panel.guest .login-benefits { margin-top:24rpx; min-height:0; padding:36rpx 28rpx 64rpx; background:linear-gradient(180deg,rgba(255,255,255,0.96),rgba(255,255,255,0.90)); border:1px solid rgba(255,255,255,0.78); border-radius:24rpx; box-shadow:0 18rpx 42rpx rgba(5,22,88,0.14),inset 0 1rpx 0 rgba(255,255,255,0.66); }
.lb-title { display:block; text-align:center; font-size:28rpx; font-weight:900; color:#17244e; margin-bottom:24rpx; }
.lb-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); align-items:stretch; }
.lb-item { position:relative; text-align:center; padding:0 14rpx; min-width:0; }
.lb-item + .lb-item { border-left:1rpx solid rgba(185,204,237,0.82); }
.lb-icon { display:flex; align-items:center; justify-content:center; width:74rpx; height:74rpx; margin:0 auto 14rpx; border-radius:50%; background:linear-gradient(145deg,#eff5ff,#dfeaff); color:#315bff; font-size:32rpx; line-height:1; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.78); }
.lb-name { display:block; font-size:25rpx; color:#17244e; font-weight:900; line-height:1.3; }
.lb-desc { display:block; font-size:22rpx; color:#7b8aa8; line-height:1.35; margin-top:8rpx; }
.tabs { display:flex; gap:12rpx; margin-bottom:18rpx; }
.tab { padding:14rpx 26rpx; border-radius:999rpx; background:rgba(255,255,255,0.90); border:1px solid rgba(219,230,255,0.95); font-size:26rpx; font-weight:800; color:#5c677d; box-shadow:0 8rpx 18rpx rgba(74,111,172,0.05); }
.tab.active { background:#f3f7ff; color:#315bff; border-color:rgba(88,105,255,0.44); }
.loading { text-align:center; padding:72rpx 0; background:rgba(255,255,255,0.72); border:1rpx solid rgba(219,230,255,0.72); border-radius:22rpx; }
.ld-dots { font-size:60rpx; letter-spacing:12rpx; color:#94a3b8; display:block; }
.ld-text { font-size:26rpx; color:#64748b; display:block; margin-top:8rpx; }
.empty { text-align:center; padding:86rpx 28rpx; background:rgba(255,255,255,0.96); border:1px solid rgba(219,230,255,0.92); border-radius:22rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.08); }
.emp-icon { font-size:72rpx; display:block; }
.emp-title { font-size:32rpx; font-weight:900; color:#17244e; display:block; margin:16rpx 0 8rpx; }
.emp-desc { display:block; font-size:26rpx; line-height:1.45; color:#64748b; }
.emp-btn { width:300rpx; height:72rpx; line-height:72rpx; margin:28rpx auto 0; padding:0; border-radius:999rpx; background:linear-gradient(135deg,#315bff,#0b3fbd); color:#fff; font-size:27rpx; font-weight:900; box-shadow:0 12rpx 26rpx rgba(49,91,255,0.18); }
.emp-btn::after { border:none; }
.list { padding-top:8rpx; }
.card { background:rgba(255,255,255,0.96); border-radius:22rpx; padding:28rpx; margin-bottom:18rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.10); border:1px solid rgba(219,230,255,0.92); }
.report-card { position:relative; overflow:hidden; }
.report-card::before { content:''; position:absolute; left:0; top:0; width:8rpx; height:100%; background:linear-gradient(180deg,#315bff,#5b4be6); }
.card-top { display:flex; justify-content:space-between; align-items:center; gap:10rpx; margin-bottom:14rpx; }
.card-title { font-size:30rpx; font-weight:900; color:#17244e; flex:1; line-height:1.32; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.status-pill { flex-shrink:0; font-size:23rpx; font-weight:900; color:#166534; background:#dcfce7; border-radius:999rpx; padding:7rpx 15rpx; }
.score-block { display:flex; align-items:baseline; gap:4rpx; }
.score-num { font-size:34rpx; font-weight:900; }
.score-unit { font-size:22rpx; color:#94a3b8; }
.stars { font-size:23rpx; color:#f8c861; letter-spacing:2rpx; }
.card-body-row { display:flex; align-items:center; margin-bottom:10rpx; }
.map-thumb { width:84rpx; height:84rpx; background:linear-gradient(135deg,#eef3ff,#dce4f2); border-radius:16rpx; flex-shrink:0; display:flex; align-items:center; justify-content:center; margin-right:16rpx; border:1rpx solid rgba(219,230,255,0.92); }
.mt-icon { font-size:36rpx; opacity:0.7; }
.card-mid { flex:1; min-width:0; }
.card-addr { font-size:26rpx; color:#475569; line-height:1.5; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:2; overflow:hidden; word-break:break-all; }
.card-time { font-size:23rpx; color:#8b99b6; display:block; margin-top:6rpx; }
.card-tags { display:flex; flex-wrap:wrap; gap:8rpx; margin:14rpx 0 10rpx; }
.tag { font-size:23rpx; font-weight:800; background:#f1f5f9; color:#475569; border-radius:999rpx; padding:7rpx 14rpx; }
.card-footer { border-top:1rpx solid rgba(219,230,255,0.78); padding-top:16rpx; }
.actions { display:grid; grid-template-columns:1fr 160rpx; gap:12rpx; }
.act { height:76rpx; line-height:76rpx; text-align:center; font-size:26rpx; font-weight:900; padding:0 20rpx; border-radius:15rpx; }
.act.primary { background:linear-gradient(135deg,#315bff,#5b4be6); color:#fff; box-shadow:0 10rpx 22rpx rgba(49,91,255,0.18); }
.act.danger { background:#fff5f5; color:#dc2626; border:1rpx solid #fee2e2; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:22rpx; padding:40rpx; width:560rpx; box-shadow:0 24rpx 70rpx rgba(15,23,42,0.18); }
.modal-title { font-size:30rpx; font-weight:900; color:#17244e; display:block; margin-bottom:12rpx; }
.modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; }
.ma-cancel { background:#f3f7ff; color:#315bff; border-radius:14rpx; padding:16rpx 32rpx; font-size:27rpx; font-weight:800; }
.ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:27rpx; font-weight:800; }
.ma-confirm[disabled] { background:#eef2f7; color:#94a3b8; }
</style>
