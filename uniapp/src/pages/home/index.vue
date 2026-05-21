<template>
  <view class="home-page">
    <!-- Hero -->
    <view class="hero">
      <AppHeader />
      <view class="hero-tagline">AI帮你判断这个位置能不能赚钱</view>
    </view>

    <!-- 分析面板 -->
    <view class="panel">
      <AddressInput :disabled="analyzing" :selectedAddress="addressText" />

      <view class="map-placeholder" @tap="onMapPlaceholderTap">
        <text class="map-icon">🗺️</text>
        <text class="map-hint">点击选择位置或使用搜索</text>
      </view>

      <IndustryPicker :selected="industry" :disabled="analyzing" @change="onIndustryChange" />

      <view class="input-row">
        <view class="input-half">
          <view class="label">品牌/特色 <text class="required">*</text></view>
          <input class="field" v-model="brandName" placeholder="品牌或主打特色" :disabled="analyzing" />
        </view>
        <view class="input-half">
          <view class="label">门店面积 <text class="required">*</text></view>
          <input class="field" v-model="storeSize" type="number" placeholder="㎡" :disabled="analyzing" />
        </view>
      </view>

      <button class="analyze-btn" :disabled="!canAnalyze" @tap="onAnalyze">
        {{ analyzing ? '分析中...' : '立即生成选址报告' }}
      </button>

      <!-- Trust row -->
      <view class="trust-row">
        <view class="trust-item" v-for="t in trusts" :key="t.title">
          <text class="trust-icon">{{ t.icon }}</text>
          <text class="trust-title">{{ t.title }}</text>
        </view>
      </view>
    </view>

    <!-- Footer -->
    <view class="footer-note">报告仅作初筛参考，需线下实地核验</view>
  </view>
</template>

<script>
import AppHeader from '../../components/app-header/index.vue'
import AddressInput from '../../components/address-input/index.vue'
import IndustryPicker from '../../components/industry-picker/index.vue'

export default {
  components: { AppHeader, AddressInput, IndustryPicker },
  data () {
    return {
      addressText: '北京市朝阳区建国路88号',
      industry: '',
      brandName: '',
      storeSize: '',
      analyzing: false,
      trusts: [
        { icon: '📊', title: '权威数据来源' },
        { icon: '🤖', title: 'AI智能分析' },
        { icon: '👥', title: '专业团队支持' }
      ]
    }
  },
  computed: {
    canAnalyze () {
      return !this.analyzing && this.addressText && this.industry && this.brandName && this.storeSize
    }
  },
  methods: {
    onIndustryChange (name) { this.industry = name },
    onMapPlaceholderTap () {
      uni.showToast({ title: '地图组件接入中', icon: 'none' })
    },
    onAnalyze () {
      uni.showToast({ title: 'uni-app 端分析接口接入中', icon: 'none', duration: 2000 })
    }
  }
}
</script>

<style scoped>
.home-page { min-height: 100vh; padding-bottom: 60rpx; }
.hero {
  background: linear-gradient(135deg, #02091d 0%, #071843 100%);
  padding: 60rpx 32rpx 80rpx;
  position: relative; overflow: hidden;
}
.hero-tagline {
  color: rgba(255,255,255,0.82); font-size: 34rpx; font-weight: 700;
  text-align: center; margin-top: 16rpx;
}
.panel {
  background: #fff; border-radius: 24rpx; padding: 32rpx; margin: -40rpx 24rpx 32rpx;
  box-shadow: 0 4rpx 32rpx rgba(9,24,54,0.10);
}
.map-placeholder {
  height: 280rpx; background: #f1f5f9; border-radius: 16rpx; margin: 24rpx 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  border: 2rpx dashed #cbd5e1;
}
.map-icon { font-size: 60rpx; margin-bottom: 12rpx; }
.map-hint { font-size: 26rpx; color: #94a3b8; }
.input-row { display: flex; gap: 16rpx; }
.input-half { flex: 1; }
.label { font-size: 26rpx; font-weight: 600; color: #334155; margin-bottom: 10rpx; }
.required { color: #ef4444; }
.field {
  border: 2rpx solid #e2e8f0; border-radius: 14rpx; padding: 18rpx 16rpx;
  font-size: 28rpx; background: #fff; width: 100%; box-sizing: border-box;
}
.analyze-btn {
  margin-top: 32rpx; width: 100%; background: linear-gradient(135deg, #0f172a, #1e40af);
  color: #fff; border-radius: 16rpx; font-size: 32rpx; font-weight: 700; padding: 24rpx 0;
}
.analyze-btn[disabled] { opacity: 0.5; }
.trust-row {
  display: flex; justify-content: space-around; margin-top: 32rpx;
  padding-top: 24rpx; border-top: 1rpx solid #f1f5f9;
}
.trust-item { display: flex; flex-direction: column; align-items: center; }
.trust-icon { font-size: 36rpx; }
.trust-title { font-size: 22rpx; color: #64748b; margin-top: 6rpx; }
.footer-note { text-align: center; font-size: 24rpx; color: #94a3b8; padding: 16rpx; }
</style>
