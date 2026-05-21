<template>
  <view class="empty-state">
    <text class="icon">{{ icon }}</text>
    <text class="title">{{ title }}</text>
    <text class="desc" v-if="desc">{{ desc }}</text>
    <slot></slot>
  </view>
</template>

<script>
export default {
  name: 'EmptyState',
  props: {
    icon: { type: String, default: '📭' },
    title: { type: String, default: '暂无数据' },
    desc: { type: String, default: '' }
  }
}
</script>

<style scoped>
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 80rpx 32rpx; text-align: center;
}
.icon { font-size: 80rpx; margin-bottom: 24rpx; }
.title { font-size: 30rpx; font-weight: 700; color: #475569; margin-bottom: 12rpx; }
.desc { font-size: 26rpx; color: #94a3b8; }
</style>
