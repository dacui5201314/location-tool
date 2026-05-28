<template>
  <view class="result-page">
    <view class="disc">💡 本工具不提供"推荐/不推荐"结论，各维度评分仅供参考，最终决策请结合实地考察与多方因素综合判断。</view>
    <view class="placeholder-box">
      <text class="ph-title">📊 分析结果</text>
      <text class="ph-desc">分析结果页面将在接入 SSE 流式分析接口后启用。当前可从「记录」页面查看已有报告详情。</text>
      <button class="ph-btn" @tap="goRecords">查看记录</button>
    </view>
  </view>
</template>

<script>
export default {
  methods: {
    goRecords () { uni.reLaunch({ url: '/pages/home/index?tab=records' }) }
  }
}
</script>

<style scoped>
.result-page { padding:24rpx; min-height:100vh; background:#eef3f9; display:flex; flex-direction:column; align-items:center; justify-content:center; }
.disc { background:#fefce8; border:1rpx solid #fde68a; border-radius:14rpx; padding:20rpx; font-size:24rpx; color:#92400e; text-align:center; max-width:600rpx; }
.placeholder-box { margin-top:40rpx; text-align:center; background:#fff; border-radius:20rpx; padding:48rpx 32rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); max-width:600rpx; width:100%; }
.ph-title { font-size:32rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:16rpx; }
.ph-desc { font-size:26rpx; color:#64748b; line-height:1.7; display:block; margin-bottom:32rpx; }
.ph-btn { background:#0f172a; color:#fff; border-radius:14rpx; font-size:28rpx; padding:20rpx 48rpx; }
</style>
