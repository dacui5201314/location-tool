<template>
  <view class="fp-panel" :class="{ guest: !isLoggedIn && !loading }">
    <view class="header">
      <text class="brand">址得选</text>
      <text class="title">收藏地址</text>
      <text class="sub">保存的地址，可随时发起分析</text>
    </view>

    <view class="login-guide" v-if="!isLoggedIn && !loading">
      <view class="lg-visual fav">
        <text class="lg-bookmark">★</text>
      </view>
      <text class="lg-title">登录后可查看收藏地址</text>
      <button class="lg-btn" @tap="$emit('go-tab','profile')">去登录</button>
      <text class="lg-text">登录后同步你的收藏地址，方便随时发起分析</text>
    </view>

    <view class="login-benefits" v-if="!isLoggedIn && !loading">
      <text class="lb-title">收藏地址 · 让选址更高效</text>
      <view class="lb-grid">
        <view class="lb-item">
          <text class="lb-icon fav-save">★</text>
          <text class="lb-name">保存常用地址</text>
          <text class="lb-desc">重要地址不丢失</text>
        </view>
        <view class="lb-item">
          <text class="lb-icon fav-fast">⌁</text>
          <text class="lb-name">一键发起分析</text>
          <text class="lb-desc">快速开启选址分析</text>
        </view>
        <view class="lb-item">
          <text class="lb-icon fav-sync">↻</text>
          <text class="lb-name">跨设备同步</text>
          <text class="lb-desc">多端同步随时查看</text>
        </view>
      </view>
    </view>

    <view class="summary-card" v-if="isLoggedIn">
      <text class="sc-text">你已收藏 {{ list.length }} 个地址</text>
      <text class="sc-sub" v-if="list.length">点击卡片可快速开始分析</text>
    </view>

    <view class="controls" v-if="isLoggedIn">
      <view class="tabs">
        <view v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @tap="activeTab = tab.key">
          {{ tab.label }} {{ counts[tab.key] || '' }}
        </view>
      </view>
      <view class="sort-row">
        <text class="sort-label">排序：</text>
        <text class="sort-opt" :class="{ active: sortBy === 'newest' }" @tap="sortBy = 'newest'">最新</text>
        <text class="sort-opt" :class="{ active: sortBy === 'analyzed' }" @tap="sortBy = 'analyzed'">已分析优先</text>
        <text class="batch-toggle" @tap="batchMode = !batchMode">{{ batchMode ? '完成' : '批量管理' }}</text>
      </view>
    </view>

    <view class="loading" v-if="loading"><text class="ld-dots">...</text><text class="ld-text">加载中...</text></view>

    <view class="error-box" v-if="!loading && errMsg && isLoggedIn">
      <text>⚠️ {{ errMsg }}</text>
      <button class="err-btn" @tap="loadFavorites">点击重试</button>
    </view>

    <view class="empty" v-if="!loading && !errMsg && isLoggedIn && filteredList.length === 0">
      <text class="emp-icon">☆</text>
      <text class="emp-title">暂无收藏地址</text>
      <text class="emp-desc">把待评估铺位加入收藏，后续可快速生成报告</text>
      <button class="emp-btn" @tap="$emit('go-tab','home')">去收藏一个地址</button>
    </view>

    <view class="batch-bar" v-if="batchMode && selectedIds.length">
      <text>已选 {{ selectedIds.length }} 项</text>
      <button class="batch-del" @tap="batchDelete">批量删除</button>
    </view>

    <view class="list" v-if="!loading && !errMsg && filteredList.length">
      <view class="card" v-for="f in sortedList" :key="f.id" :class="{ batch: batchMode, checked: selectedIds.includes(f.id), analyzed: f.is_analyzed, pending: !f.is_analyzed }">
        <view class="card-check" v-if="batchMode" @tap="toggleSelect(f.id)"><text>{{ selectedIds.includes(f.id) ? '◉' : '○' }}</text></view>
        <view class="card-body" @tap="batchMode ? toggleSelect(f.id) : onSelect(f)">
          <view class="card-top">
            <text class="card-title">{{ favTitle(f) }}</text>
            <text class="badge" :class="f.is_analyzed ? 'done' : 'pending'">{{ f.is_analyzed ? '已分析' : '待分析' }}</text>
          </view>
          <view class="card-addr">
            <text class="addr-pin">定位</text>
            <text class="addr-text">{{ displayAddress(f.address || f.report_address) }}</text>
          </view>
          <view class="card-time">{{ f.is_analyzed ? '分析时间' : '收藏时间' }}：{{ fmtTime(f.created_at) }}</view>
        </view>
        <view class="card-actions">
          <button v-if="f.is_analyzed && f.report_uuid" class="act report" @tap="onViewReport(f)">查看完整报告</button>
          <button v-else-if="f.is_analyzed && !f.report_uuid" class="act" disabled>报告编号缺失</button>
          <button v-else class="act primary" @tap="onAnalyze(f)">开始分析</button>
          <button class="act danger" @tap="onRemove(f)">删除地址</button>
        </view>
      </view>
    </view>

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
  name: 'FavoritesPanel',
  emits: ['go-tab','start-analysis'],
  data () {
    return {
      loading: false, errMsg: '', isLoggedIn: false,
      activeTab: 'all',
      tabs: [{ key:'all',label:'全部' },{ key:'pending',label:'待分析' },{ key:'done',label:'已分析' }],
      list: [], delTarget: null, delLoading: false,
      sortBy: 'newest', batchMode: false, selectedIds: []
    }
  },
  computed: {
    sortedList () {
      let items = [...this.filteredList]
      if (this.sortBy === 'analyzed') {
        items.sort((a, b) => (b.is_analyzed ? 1 : 0) - (a.is_analyzed ? 1 : 0) || new Date(b.created_at || 0) - new Date(a.created_at || 0))
      } else {
        items.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
      }
      return items
    },
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
  mounted () {
    this.isLoggedIn = auth.isLoggedIn()
    if (this.isLoggedIn) this.loadFavorites()
    else { this.list = []; this.errMsg = '' }
  },
  methods: {
    fmtTime: formatTime,
    favTitle (f) {
      const title = f.custom_name || f.address || f.report_address || ''
      return this.compactAddress(title, 22) || f.report_brand_desc || '收藏地址'
    },
    displayAddress (addr) {
      return addr || '-'
    },
    compactAddress (value, maxLen = 0) {
      const raw = String(value || '').replace(/\s+/g, '')
      if (!raw) return ''
      const suffixes = [
        '特别行政区','自治区','自治州','自治县','自治旗',
        '县级市','市辖区',
        '省','市','区','县','旗','街道','镇','乡','地区','盟','林区','特区'
      ]
      let cleaned = raw
      const strippedCities = []
      for (let i = 0; i < 4; i++) {
        let matched = false
        for (const sfx of suffixes) {
          const re = new RegExp('^(.{1,8}' + sfx + ')')
          const m = cleaned.match(re)
          if (m && cleaned.length - m[0].length >= 6) {
            const stripped = m[0]
            if (sfx === '市' && stripped.length <= 6) {
              strippedCities.push(stripped)
            }
            cleaned = cleaned.slice(stripped.length)
            matched = true
            break
          }
        }
        if (!matched) break
      }
      for (const city of strippedCities) {
        cleaned = cleaned.replace(city, '')
      }
      const result = cleaned || raw
      if (maxLen > 0 && result.length > maxLen) return result.slice(0, maxLen - 2) + '...'
      return result
    },
    refresh () {
      this.isLoggedIn = auth.isLoggedIn()
      if (this.isLoggedIn) this.loadFavorites()
      else { this.list = []; this.errMsg = '' }
    },
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
      if (addr) {
        uni.setStorageSync('pending_analysis_address', addr)
        uni.setStorageSync('pending_analysis_lat', f.latitude || 0)
        uni.setStorageSync('pending_analysis_lng', f.longitude || 0)
        // ★ 仅有效正整数才写入 storage，避免 422
        if (typeof f.id === 'number' && Number.isSafeInteger(f.id) && f.id > 0) {
          uni.setStorageSync('pending_analysis_fav_id', f.id)
        } else {
          uni.removeStorageSync('pending_analysis_fav_id')
        }
      }
      this.$emit('go-tab', 'home')
    },
    onViewReport (f) {
      if (f.report_uuid) {
        uni.navigateTo({ url: '/pages/report-detail/index?id=' + f.report_uuid })
      } else {
        uni.showToast({ title: '该记录缺少报告编号，无法查看', icon: 'none' })
      }
    },
    onAnalyze (f) {
      const addr = f.address || f.report_address || ''
      if (addr) {
        uni.setStorageSync('pending_analysis_address', addr)
        uni.setStorageSync('pending_analysis_lat', f.latitude || 0)
        uni.setStorageSync('pending_analysis_lng', f.longitude || 0)
        // ★ 仅有效正整数才写入 storage，避免 422
        if (typeof f.id === 'number' && Number.isSafeInteger(f.id) && f.id > 0) {
          uni.setStorageSync('pending_analysis_fav_id', f.id)
        } else {
          uni.removeStorageSync('pending_analysis_fav_id')
        }
      }
      this.$emit('go-tab', 'home')
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
        } else { uni.showToast({ title: api.normalizeError(r), icon: 'none' }) }
      } catch (e) { uni.showToast({ title: '网络异常', icon: 'none' }) }
      this.delLoading = false; this.delTarget = null
    },
    toggleSelect (id) {
      const idx = this.selectedIds.indexOf(id)
      if (idx >= 0) this.selectedIds.splice(idx, 1)
      else this.selectedIds.push(id)
    },
    async batchDelete () {
      if (!this.selectedIds.length) return
      const confirmed = await new Promise(resolve => {
        uni.showModal({ title: '确认批量删除', content: `将删除 ${this.selectedIds.length} 个收藏地址，不可恢复`, success: r => resolve(r.confirm) })
      })
      if (!confirmed) return
      this.delLoading = true
      const okIds = []; let failed = 0
      for (const id of this.selectedIds) {
        try {
          const r = await api.deleteFavorite(id)
          if (r.ok || r.statusCode === 404) okIds.push(id)
          else failed++
        } catch (e) { failed++ }
      }
      this.list = this.list.filter(x => !okIds.includes(x.id))
      this.selectedIds = this.selectedIds.filter(x => !okIds.includes(x))
      this.batchMode = false; this.delLoading = false
      if (okIds.length && !failed) uni.showToast({ title: `已删除 ${okIds.length} 条`, icon: 'none' })
      else if (okIds.length) uni.showToast({ title: `已删除 ${okIds.length} 条，${failed} 条失败`, icon: 'none' })
      else uni.showToast({ title: '删除失败，请重试', icon: 'none' })
    }
  }
}
</script>

<style scoped>
.fp-panel { min-height:100vh; background:linear-gradient(180deg,#dce4f2,#e0e8f6 42%,#dce4f2); padding:0 24rpx 40rpx; }
.fp-panel.guest { min-height:calc(100vh - 88rpx - env(safe-area-inset-bottom)); background:#dce4f2; }
.header { margin:0 -24rpx 22rpx; padding:62rpx 48rpx 82rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.22),transparent 26%),radial-gradient(circle at 58% 58%,rgba(248,200,97,0.10),transparent 22%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); position:relative; overflow:hidden; }
.fp-panel.guest .header { margin-bottom:0; padding:78rpx 48rpx 178rpx; }
.header::before { content:''; position:absolute; left:-120rpx; top:-150rpx; width:660rpx; height:320rpx; border-radius:0 0 56% 56%; background:linear-gradient(180deg,rgba(255,255,255,0.16),rgba(255,255,255,0.02)); transform:rotate(8deg); }
.header::after { content:''; position:absolute; right:56rpx; bottom:0; width:38rpx; height:154rpx; border-radius:9rpx 9rpx 0 0; background:linear-gradient(180deg,rgba(219,234,254,0.56),rgba(37,99,235,0.08)); box-shadow:-54rpx 30rpx 0 rgba(191,219,254,0.34),-108rpx 66rpx 0 rgba(191,219,254,0.24),54rpx 20rpx 0 rgba(191,219,254,0.28),106rpx 54rpx 0 rgba(191,219,254,0.18); opacity:0.58; }
.brand { font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; position:relative; z-index:1; display:block; }
.title { font-size:42rpx; font-weight:900; color:#fff; display:block; position:relative; z-index:1; margin-top:2rpx; }
.sub { font-size:26rpx; color:rgba(232,240,255,0.82); margin-top:8rpx; position:relative; z-index:1; line-height:1.45; }
.login-guide { position:relative; z-index:2; text-align:center; padding:72rpx 32rpx 56rpx; margin-top:-46rpx; background:linear-gradient(180deg,rgba(255,255,255,0.99),rgba(255,255,255,0.95)); border:1px solid rgba(255,255,255,0.86); border-radius:28rpx; box-shadow:0 24rpx 52rpx rgba(45,78,145,0.13),inset 0 1rpx 0 rgba(255,255,255,0.72); overflow:hidden; }
.fp-panel.guest .login-guide { margin-top:-96rpx; padding:88rpx 32rpx 68rpx; background:linear-gradient(180deg,rgba(255,255,255,0.99),rgba(255,255,255,0.95)); border:1px solid rgba(255,255,255,0.86); border-radius:28rpx; box-shadow:0 24rpx 52rpx rgba(5,22,88,0.18),inset 0 1rpx 0 rgba(255,255,255,0.72); }
.login-guide::before { content:''; position:absolute; left:50%; top:68rpx; width:280rpx; height:150rpx; transform:translateX(-50%); border-radius:50%; background:radial-gradient(circle,rgba(49,91,255,0.14),rgba(49,91,255,0)); }
.lg-visual { position:relative; z-index:1; width:150rpx; height:128rpx; margin:0 auto 22rpx; display:flex; align-items:center; justify-content:center; }
.lg-visual::before { content:''; position:absolute; left:14rpx; right:14rpx; bottom:8rpx; height:30rpx; border-radius:50%; background:rgba(49,91,255,0.10); filter:blur(2rpx); }
.lg-bookmark { position:relative; z-index:1; display:flex; align-items:center; justify-content:center; width:96rpx; height:116rpx; border-radius:24rpx 24rpx 16rpx 16rpx; background:linear-gradient(145deg,#8fb7ff 0%,#315bff 72%,#1f37c8 100%); color:#fff; font-size:42rpx; line-height:1; box-shadow:0 18rpx 34rpx rgba(49,91,255,0.24),inset 0 2rpx 0 rgba(255,255,255,0.35); }
.lg-bookmark::after { content:''; position:absolute; left:30rpx; bottom:-1rpx; width:36rpx; height:28rpx; background:#fff; clip-path:polygon(0 100%,50% 40%,100% 100%); opacity:0.28; }
.lg-title { position:relative; z-index:1; display:block; font-size:34rpx; color:#17244e; font-weight:900; line-height:1.35; margin-bottom:24rpx; }
.lg-text { position:relative; z-index:1; display:block; font-size:25rpx; color:#6b7a99; line-height:1.55; margin-top:24rpx; }
.lg-btn { position:relative; z-index:1; width:280rpx; height:76rpx; line-height:76rpx; margin:0 auto; padding:0; background:linear-gradient(135deg,#fff0bd 0%,#f8c861 54%,#dba640 100%); color:#4a2600; border:1px solid rgba(255,255,255,0.70); border-radius:999rpx; font-size:29rpx; font-weight:900; box-shadow:0 18rpx 34rpx rgba(248,200,97,0.28),inset 0 2rpx 0 rgba(255,255,255,0.62); }
.lg-btn::after { border:none; }
.login-benefits { margin-top:22rpx; padding:30rpx 28rpx; background:rgba(255,255,255,0.82); border:1px solid rgba(255,255,255,0.78); border-radius:24rpx; box-shadow:0 18rpx 42rpx rgba(79,119,186,0.08),inset 0 1rpx 0 rgba(255,255,255,0.66); }
.fp-panel.guest .login-benefits { margin-top:24rpx; min-height:0; padding:36rpx 28rpx 64rpx; background:linear-gradient(180deg,rgba(255,255,255,0.96),rgba(255,255,255,0.90)); border:1px solid rgba(255,255,255,0.78); border-radius:24rpx; box-shadow:0 18rpx 42rpx rgba(5,22,88,0.14),inset 0 1rpx 0 rgba(255,255,255,0.66); }
.lb-title { display:block; text-align:center; font-size:28rpx; font-weight:900; color:#17244e; margin-bottom:24rpx; }
.lb-grid { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); align-items:stretch; }
.lb-item { position:relative; text-align:center; padding:0 14rpx; min-width:0; }
.lb-item + .lb-item { border-left:1rpx solid rgba(185,204,237,0.82); }
.lb-icon { display:flex; align-items:center; justify-content:center; width:74rpx; height:74rpx; margin:0 auto 14rpx; border-radius:50%; background:linear-gradient(145deg,#eff5ff,#dfeaff); color:#315bff; font-size:32rpx; line-height:1; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.78); }
.lb-name { display:block; font-size:25rpx; color:#17244e; font-weight:900; line-height:1.3; }
.lb-desc { display:block; font-size:22rpx; color:#7b8aa8; line-height:1.35; margin-top:8rpx; }
.summary-card { background:linear-gradient(135deg,#0b3fbd,#151f8f 58%,#5b3fd9); border-radius:22rpx; padding:30rpx; color:#fff; margin-bottom:20rpx; box-shadow:0 18rpx 42rpx rgba(21,31,143,0.24),inset 0 1rpx 0 rgba(248,200,97,0.22); }
.sc-text { font-size:32rpx; font-weight:900; display:block; }
.sc-sub { font-size:25rpx; color:rgba(255,255,255,0.78); display:block; margin-top:6rpx; line-height:1.45; }
.controls { margin-bottom:14rpx; }
.tabs { display:flex; gap:12rpx; margin-bottom:14rpx; }
.tab { padding:14rpx 26rpx; border-radius:999rpx; background:rgba(255,255,255,0.90); border:1px solid rgba(219,230,255,0.95); font-size:26rpx; font-weight:800; color:#5c677d; box-shadow:0 8rpx 18rpx rgba(74,111,172,0.05); }
.tab.active { background:#f3f7ff; color:#315bff; border-color:rgba(88,105,255,0.44); }
.sort-row { display:flex; align-items:center; gap:8rpx; padding:8rpx 0; }
.sort-label { font-size:24rpx; color:#8b99b6; }
.sort-opt { font-size:24rpx; color:#64748b; padding:7rpx 14rpx; border-radius:10rpx; }
.sort-opt.active { background:#f3f7ff; color:#315bff; font-weight:700; }
.batch-toggle { font-size:24rpx; color:#315bff; font-weight:800; margin-left:auto; padding:7rpx 14rpx; }
.batch-bar { display:flex; align-items:center; justify-content:space-between; background:#fff3cd; border-radius:14rpx; padding:16rpx 20rpx; margin-bottom:14rpx; font-size:24rpx; color:#92400e; }
.batch-del { background:#ef4444; color:#fff; border-radius:10rpx; font-size:24rpx; padding:10rpx 20rpx; }
.loading { text-align:center; padding:72rpx 0; background:rgba(255,255,255,0.72); border:1rpx solid rgba(219,230,255,0.72); border-radius:22rpx; }
.ld-dots { font-size:60rpx; letter-spacing:12rpx; color:#94a3b8; display:block; }
.ld-text { font-size:26rpx; color:#64748b; display:block; margin-top:8rpx; }
.error-box { text-align:center; padding:76rpx 28rpx; background:rgba(255,255,255,0.96); border:1px solid rgba(254,202,202,0.9); border-radius:22rpx; box-shadow:0 16rpx 34rpx rgba(127,29,29,0.06); }
.error-box text { display:block; font-size:26rpx; color:#dc2626; margin-bottom:16rpx; }
.err-btn { background:#f3f7ff; color:#315bff; border-radius:14rpx; padding:16rpx 40rpx; font-size:28rpx; font-weight:800; }
.empty { text-align:center; padding:86rpx 28rpx; background:rgba(255,255,255,0.96); border:1px solid rgba(219,230,255,0.92); border-radius:22rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.08); }
.emp-icon { font-size:72rpx; display:block; }
.emp-title { font-size:32rpx; font-weight:900; color:#17244e; display:block; margin:16rpx 0 8rpx; }
.emp-desc { display:block; font-size:26rpx; line-height:1.45; color:#64748b; }
.emp-btn { width:300rpx; height:72rpx; line-height:72rpx; margin:28rpx auto 0; padding:0; border-radius:999rpx; background:linear-gradient(135deg,#315bff,#0b3fbd); color:#fff; font-size:27rpx; font-weight:900; box-shadow:0 12rpx 26rpx rgba(49,91,255,0.18); }
.emp-btn::after { border:none; }
.list { padding-top:8rpx; }
.card { background:rgba(255,255,255,0.96); border-radius:22rpx; padding:28rpx; margin-bottom:18rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.10); border:1px solid rgba(219,230,255,0.92); position:relative; overflow:hidden; }
.card::before { content:''; position:absolute; left:0; top:0; width:8rpx; height:100%; background:#f8c861; }
.card.analyzed::before { background:linear-gradient(180deg,#22c55e,#16a34a); }
.card.pending::before { background:linear-gradient(180deg,#f8c861,#f59e0b); }
.card.analyzed { border-color:rgba(187,247,208,0.95); }
.card.pending { border-color:rgba(254,215,170,0.95); }
.card-check { position:absolute; left:22rpx; top:30rpx; width:42rpx; height:42rpx; line-height:42rpx; text-align:center; font-size:28rpx; color:#315bff; flex-shrink:0; }
.card-body { margin-bottom:16rpx; }
.card-top { display:flex; justify-content:space-between; align-items:center; gap:12rpx; }
.card-title { font-size:30rpx; font-weight:900; color:#17244e; flex:1; line-height:1.32; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.badge { font-size:23rpx; font-weight:900; padding:7rpx 15rpx; border-radius:999rpx; flex-shrink:0; }
.badge.done { background:#dcfce7; color:#166534; }
.badge.pending { background:#fff7ed; color:#c2410c; }
.card-addr { display:flex; align-items:flex-start; gap:10rpx; margin-top:14rpx; }
.addr-pin { flex-shrink:0; font-size:0; width:32rpx; height:32rpx; position:relative; margin-top:4rpx; }
.addr-pin::before { content:''; position:absolute; left:7rpx; top:2rpx; width:18rpx; height:18rpx; border-radius:12rpx 12rpx 12rpx 3rpx; transform:rotate(-45deg); background:linear-gradient(145deg,#ff6b6b,#ef4444); box-shadow:0 6rpx 14rpx rgba(239,68,68,0.16); }
.addr-pin::after { content:''; position:absolute; left:14rpx; top:9rpx; width:4rpx; height:4rpx; border-radius:50%; background:#fff; }
.addr-text { flex:1; min-width:0; font-size:26rpx; color:#475569; line-height:1.55; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:2; overflow:hidden; word-break:break-all; }
.card-time { font-size:23rpx; color:#8b99b6; margin-top:6rpx; }
.card-actions { display:grid; grid-template-columns:minmax(0,1fr) 168rpx; gap:12rpx; border-top:1rpx solid rgba(219,230,255,0.78); padding-top:16rpx; align-items:stretch; }
.act { width:100%; height:76rpx; line-height:76rpx; min-width:0; margin:0; padding:0 12rpx; box-sizing:border-box; text-align:center; font-size:26rpx; font-weight:900; border-radius:15rpx; background:#f3f7ff; color:#315bff; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.act.report { background:linear-gradient(135deg,#315bff,#5b4be6); color:#fff; box-shadow:0 10rpx 22rpx rgba(49,91,255,0.20); }
.act.primary { background:linear-gradient(135deg,#4a75ff,#315bff); color:#fff; }
.act.danger { background:#fff5f5; color:#dc2626; border:1rpx solid #fee2e2; }
.act[disabled] { background:#eef2f7; color:#94a3b8; box-shadow:none; }
.act::after { border:none; }
.modal-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:999; }
.modal-box { background:#fff; border-radius:22rpx; padding:40rpx; width:560rpx; box-shadow:0 24rpx 70rpx rgba(15,23,42,0.18); }
.modal-title { font-size:30rpx; font-weight:900; color:#17244e; display:block; margin-bottom:12rpx; }
.modal-body { font-size:26rpx; color:#64748b; display:block; margin-bottom:24rpx; }
.modal-actions { display:flex; gap:16rpx; justify-content:flex-end; }
.ma-cancel { background:#f3f7ff; color:#315bff; border-radius:14rpx; padding:16rpx 32rpx; font-size:27rpx; font-weight:800; }
.ma-confirm { background:#ef4444; color:#fff; border-radius:14rpx; padding:16rpx 32rpx; font-size:27rpx; font-weight:800; }
.ma-confirm[disabled] { background:#eef2f7; color:#94a3b8; }
.card.batch { position:relative; border-color:rgba(219,230,255,0.6); padding-left:76rpx; }
.card.checked { border-color:#315bff; background:rgba(243,247,255,0.98); }
</style>
