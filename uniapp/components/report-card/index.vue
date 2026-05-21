<template>
  <view class="report-card" @tap="onTap">
    <view class="card-top">
      <view class="card-title">{{ title }}</view>
      <view class="card-badge" v-if="status">{{ status }}</view>
    </view>
    <view class="card-addr">📍 {{ address }}</view>
    <view class="card-tags" v-if="tags.length">
      <text class="tag" v-for="t in tags" :key="t">{{ t }}</text>
    </view>
    <view class="card-bottom" v-if="score !== null || time">
      <text v-if="score !== null" class="score" :style="{ color: scoreColor(score) }">评分 {{ score }}</text>
      <text class="time">{{ time }}</text>
    </view>
    <view class="card-actions" v-if="showActions">
      <slot name="actions"></slot>
    </view>
  </view>
</template>

<script>
import { scoreColor } from '../../utils/format'
export default {
  name: 'ReportCard',
  props: {
    title: { type: String, default: '' },
    address: { type: String, default: '' },
    status: { type: String, default: '' },
    tags: { type: Array, default: () => [] },
    score: { type: Number, default: null },
    time: { type: String, default: '' },
    showActions: { type: Boolean, default: false }
  },
  methods: {
    scoreColor,
    onTap () { this.$emit('click') }
  }
}
</script>

<style scoped>
.report-card {
  background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 16rpx;
  box-shadow: 0 2rpx 16rpx rgba(0,0,0,0.04);
}
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10rpx; }
.card-title { font-size: 30rpx; font-weight: 700; color: #1e293b; flex: 1; }
.card-badge { font-size: 22rpx; padding: 4rpx 14rpx; border-radius: 12rpx; background: #dbeafe; color: #1e40af; }
.card-addr { font-size: 24rpx; color: #64748b; margin-bottom: 10rpx; }
.card-tags { margin-bottom: 10rpx; }
.tag { display: inline-block; font-size: 20rpx; padding: 4rpx 12rpx; border-radius: 10rpx; background: #f1f5f9; color: #475569; margin-right: 8rpx; }
.card-bottom { display: flex; justify-content: space-between; font-size: 24rpx; color: #94a3b8; }
.score { font-weight: 700; }
</style>
