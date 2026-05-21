<template>
  <view class="detail-page">
    <!-- Loading state -->
    <view class="loading" v-if="loading">
      <text class="ld-dots">...</text>
      <text class="ld-text">加载中...</text>
    </view>

    <!-- Error state -->
    <view class="error" v-if="!loading && errorMsg">
      <text class="err-icon">📭</text>
      <text class="err-text">{{ errorMsg }}</text>
      <button class="err-btn" @tap="goBack">返回记录列表</button>
    </view>

    <!-- Content state -->
    <view v-if="!loading && !errorMsg">
      <!-- Header -->
      <view class="top-bar">
        <text class="back" @tap="goBack">←</text>
        <text class="top-title">{{ meta.brand || meta.businessType || '报告详情' }}</text>
        <text class="top-export" :class="unlocked ? 'free' : 'locked'" @tap="onExport">{{ unlocked ? '⬇️ 下载 PDF' : '🔒 导出' }}</text>
      </view>

      <!-- Meta card -->
      <view class="meta-card">
        <view class="meta-grid">
          <view class="mg-item"><text class="mgl">地址</text><text class="mgv">{{ meta.address || '-' }}</text></view>
          <view class="mg-item"><text class="mgl">品牌/业态</text><text class="mgv">{{ meta.brand || meta.businessType || '-' }}</text></view>
          <view class="mg-item"><text class="mgl">门店面积</text><text class="mgv">{{ meta.storeSize ? meta.storeSize + '㎡' : '-' }}</text></view>
          <view class="mg-item"><text class="mgl">分析时间</text><text class="mgv">{{ meta.time || '-' }}</text></view>
        </view>
        <view class="meta-score" v-if="meta.score > 0">
          <text class="ms-num" :style="{ color: sc(meta.score) }">{{ meta.score }}</text>
          <text class="ms-label">综合评分</text>
          <text class="ms-badge" :class="unlocked ? 'free' : 'locked'">{{ unlocked ? 'PDF 已解锁' : 'PDF 未解锁' }}</text>
        </view>
      </view>

      <!-- Legacy warning -->
      <view class="warn-legacy" v-if="isLegacy">
        <text class="wl-title">⚠️ 此为旧版格式报告</text>
        <text class="wl-body">该报告生成于系统升级前，不支持高级图表展示。如需完整数据，请重新发起分析。</text>
      </view>

      <!-- Report content placeholder -->
      <view class="content-placeholder">
        <text class="cp-title">📊 报告内容</text>
        <text class="cp-text">完整的 direct / substitute / anchor / data quality 区块将在 Phase 23E 接入真实 API 后展示。当前为 Web 同款结构占位。</text>
      </view>

      <!-- Bottom bar -->
      <view class="bottom-bar">
        <button v-if="unlocked" class="bb-export">⬇️ 下载 PDF 报告</button>
        <button v-else class="bb-unlock">🔒 消耗 1 点数导出 PDF</button>
        <button class="bb-back" @tap="goBack">返回</button>
      </view>
    </view>
  </view>
</template>

<script>
import { scoreColor, formatTime } from '../../utils/format'
export default {
  data () {
    return {
      loading: false,
      errorMsg: '',
      isLegacy: false,
      unlocked: false,
      meta: {
        address: '广州市天河区天河路208号',
        businessType: '民宿青旅',
        brand: '',
        storeSize: '',
        time: '2026-05-19 17:38',
        score: 62
      }
    }
  },
  methods: {
    sc: scoreColor,
    goBack () { uni.navigateBack({ delta: 1 }).catch(() => uni.switchTab({ url: '/pages/records/index' })) },
    onExport () { uni.showToast({ title: this.unlocked ? 'PDF 下载接入中' : '需消耗 1 点数，接入中', icon: 'none' }) }
  }
}
</script>

<style scoped>
.detail-page { min-height:100vh; background:#eef3f9; padding-bottom:140rpx; }
.loading { text-align:center; padding:120rpx 0; }
.ld-dots { font-size:60rpx; letter-spacing:12rpx; color:#94a3b8; } .ld-text { display:block; font-size:26rpx; color:#94a3b8; margin-top:16rpx; }
.error { text-align:center; padding:120rpx 32rpx; } .err-icon { font-size:80rpx; display:block; } .err-text { font-size:28rpx; color:#64748b; display:block; margin:16rpx 0; } .err-btn { margin-top:20rpx; background:#f1f5f9; color:#475569; border-radius:14rpx; padding:16rpx 40rpx; font-size:28rpx; }

.top-bar { display:flex; align-items:center; padding:20rpx 24rpx; background:#fff; border-bottom:1rpx solid #e2e8f0; }
.back { font-size:36rpx; color:#475569; padding-right:16rpx; }
.top-title { flex:1; font-size:30rpx; font-weight:700; color:#1e293b; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.top-export { font-size:24rpx; padding:8rpx 18rpx; border-radius:12rpx; }
.top-export.free { background:#dbeafe; color:#1e40af; } .top-export.locked { background:#fef3c7; color:#92400e; }

.meta-card { background:#fff; margin:20rpx 24rpx; border-radius:20rpx; padding:28rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.meta-grid { display:flex; flex-wrap:wrap; }
.mg-item { width:50%; padding:12rpx 0; }
.mgl { font-size:24rpx; color:#94a3b8; display:block; } .mgv { font-size:26rpx; color:#1e293b; font-weight:500; }
.meta-score { text-align:center; margin-top:16rpx; padding-top:16rpx; border-top:1rpx solid #f1f5f9; }
.ms-num { font-size:64rpx; font-weight:900; } .ms-label { display:block; font-size:24rpx; color:#94a3b8; } .ms-badge { display:inline-block; margin-top:6rpx; font-size:22rpx; padding:4rpx 14rpx; border-radius:10rpx; }
.ms-badge.free { background:#dcfce7; color:#166534; } .ms-badge.locked { background:#fef3c7; color:#92400e; }

.warn-legacy { background:#fefce8; border:1rpx solid #fde68a; border-radius:14rpx; margin:0 24rpx 20rpx; padding:20rpx; }
.wl-title { font-size:26rpx; font-weight:700; color:#92400e; display:block; } .wl-body { font-size:24rpx; color:#92400e; display:block; margin-top:6rpx; }

.content-placeholder { background:#fff; margin:0 24rpx; border-radius:20rpx; padding:32rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.cp-title { font-size:28rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:12rpx; } .cp-text { font-size:26rpx; color:#64748b; line-height:1.7; }

.bottom-bar { position:fixed; bottom:0; left:0; right:0; padding:20rpx 24rpx; background:#fff; border-top:1rpx solid #e2e8f0; display:flex; gap:14rpx; }
.bb-export { flex:1; background:#246bff; color:#fff; border-radius:14rpx; font-size:28rpx; padding:20rpx 0; font-weight:600; }
.bb-unlock { flex:1; background:#f59e0b; color:#fff; border-radius:14rpx; font-size:28rpx; padding:20rpx 0; font-weight:600; }
.bb-back { background:#f1f5f9; color:#475569; border-radius:14rpx; font-size:28rpx; padding:20rpx 32rpx; }
</style>
