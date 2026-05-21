<template>
  <view class="address-input">
    <view class="label">门店地址</view>
    <view class="input-row">
      <input
        class="field"
        v-model="keyword"
        placeholder="输入地址搜索或在地图上选点"
        :disabled="disabled"
        @confirm="onSearch"
      />
      <button class="search-btn" :disabled="disabled || !keyword" @tap="onSearch">搜索</button>
    </view>
    <view class="result" v-if="selectedAddress">
      <text class="pin">📍</text>
      <text class="addr-text">{{ selectedAddress }}</text>
    </view>
  </view>
</template>

<script>
export default {
  name: 'AddressInput',
  props: {
    value: { type: Object, default: () => ({ lng: 0, lat: 0 }) },
    disabled: { type: Boolean, default: false },
    selectedAddress: { type: String, default: '' }
  },
  data () { return { keyword: '' } },
  methods: {
    onSearch () {
      if (!this.keyword) return
      // Phase 23A: 不接地图/地理编码，只提示
      uni.showToast({ title: '地图搜索接入中', icon: 'none' })
    }
  }
}
</script>

<style scoped>
.address-input { margin: 24rpx 0; }
.label { font-size: 28rpx; font-weight: 600; color: #334155; margin-bottom: 12rpx; }
.input-row { display: flex; gap: 12rpx; }
.field { flex: 1; border: 2rpx solid #e2e8f0; border-radius: 14rpx; padding: 20rpx 16rpx; font-size: 28rpx; background: #fff; }
.search-btn {
  background: #0f172a; color: #fff; border-radius: 14rpx; padding: 0 32rpx;
  font-size: 28rpx; line-height: 80rpx; font-weight: 600;
}
.search-btn[disabled] { opacity: 0.5; }
.result {
  margin-top: 16rpx; padding: 20rpx; background: #f0fdf4; border: 1rpx solid #bbf7d0;
  border-radius: 14rpx; font-size: 26rpx; color: #166534;
}
.addr-text { margin-left: 8rpx; }
</style>
