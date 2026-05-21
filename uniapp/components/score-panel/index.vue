<template>
  <view class="score-panel">
    <view class="overall">
      <text class="score-num" :style="{ color: scoreColor(score) }">{{ score }}</text>
      <text class="score-label">综合评分</text>
    </view>
    <view class="bars">
      <view class="bar-row" v-for="d in dimensions" :key="d.key">
        <text class="bar-label">{{ d.label }}</text>
        <view class="bar-track">
          <view class="bar-fill" :style="{ width: d.value + '%', background: scoreColor(d.value) }"></view>
        </view>
        <text class="bar-val">{{ d.value }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import { scoreColor } from '../../utils/format'
export default {
  name: 'ScorePanel',
  props: {
    score: { type: Number, default: 0 },
    dimensions: { type: Array, default: () => [] }
  },
  methods: { scoreColor }
}
</script>

<style scoped>
.score-panel { background: #fff; border-radius: 20rpx; padding: 32rpx; margin-bottom: 24rpx; }
.overall { text-align: center; margin-bottom: 32rpx; }
.score-num { font-size: 80rpx; font-weight: 900; }
.score-label { display: block; font-size: 24rpx; color: #94a3b8; margin-top: 4rpx; }
.bar-row { display: flex; align-items: center; margin-bottom: 16rpx; }
.bar-label { width: 160rpx; font-size: 24rpx; color: #475569; text-align: right; padding-right: 16rpx; }
.bar-track { flex: 1; height: 16rpx; background: #f1f5f9; border-radius: 8rpx; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 8rpx; min-width: 4rpx; transition: width 0.3s; }
.bar-val { width: 60rpx; font-size: 22rpx; color: #94a3b8; text-align: center; }
</style>
