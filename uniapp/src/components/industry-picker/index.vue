<template>
  <view class="industry-picker">
    <view class="label" v-if="!hideLabel">选择业态</view>
    <scroll-view scroll-x class="cat-scroll">
      <view
        v-for="cat in categories"
        :key="cat.key"
        class="cat-tile"
        :class="{ active: activeCat === cat.key }"
        @tap="selectCat(cat.key)"
      >
        <text class="cat-icon">{{ cat.icon }}</text>
        <text class="cat-name">{{ cat.label }}</text>
      </view>
    </scroll-view>
    <view class="sub-panel" v-if="activeCat && subTypes.length">
      <view
        v-for="st in subTypes"
        :key="st.name"
        class="chip"
        :class="{ selected: selected === st.name }"
        @tap="onSelect(st.name)"
      >{{ st.name }}</view>
    </view>
  </view>
</template>

<script>
export default {
  name: 'IndustryPicker',
  props: {
    selected: { type: String, default: '' },
    hideLabel: { type: Boolean, default: false },
    disabled: { type: Boolean, default: false }
  },
  data () {
    return {
      activeCat: '',
      // Phase 23A: mock 业态数据（对齐 Web CAT_META）
      categories: [
        { key: 'food', icon: '🍽️', label: '餐饮' },
        { key: 'drink', icon: '☕', label: '茶饮咖啡' },
        { key: 'retail', icon: '🛍️', label: '零售商业' },
        { key: 'hotel', icon: '🏨', label: '酒店住宿' },
        { key: 'service', icon: '💇', label: '生活服务' },
        { key: 'entertainment', icon: '🎮', label: '休闲娱乐' }
      ],
      subTypes: []
    }
  },
  methods: {
    selectCat (key) {
      if (this.disabled) return
      this.activeCat = key
      // Phase 23A: mock 子业态（后续从 /api/industries/active 动态加载）
      const mock = {
        food: ['小餐饮', '大餐饮', '中餐', '日餐', '西餐', '火锅店', '烧烤店', '小吃店', '烘焙店', '快餐店'],
        drink: ['奶茶店', '咖啡店', '甜品店', '饮品店'],
        retail: ['零售店', '便利店', '超市', '服装店', '数码店', '药店'],
        hotel: ['酒店', '民宿', '青年旅舍'],
        service: ['美容美发', '健身房', '教育培训', '宠物店', '洗衣店', '诊所'],
        entertainment: ['酒吧', 'KTV', '剧本杀', '网吧', '台球厅']
      }
      this.subTypes = (mock[key] || []).map(name => ({ name }))
    },
    onSelect (name) {
      if (this.disabled) return
      this.$emit('change', name)
    }
  }
}
</script>

<style scoped>
.industry-picker { margin: 24rpx 0; }
.label { font-size: 28rpx; font-weight: 600; color: #334155; margin-bottom: 16rpx; }
.cat-scroll { white-space: nowrap; padding-bottom: 8rpx; }
.cat-tile {
  display: inline-flex; flex-direction: column; align-items: center;
  width: 120rpx; padding: 16rpx 8rpx; margin-right: 12rpx;
  border-radius: 14rpx; background: #f8fafc; transition: all 0.2s;
}
.cat-tile.active { background: #0f172a; }
.cat-tile.active .cat-name { color: #fff; }
.cat-icon { font-size: 36rpx; }
.cat-name { font-size: 22rpx; color: #475569; margin-top: 6rpx; }
.sub-panel { margin-top: 16rpx; display: flex; flex-wrap: wrap; gap: 12rpx; }
.chip {
  padding: 12rpx 24rpx; border-radius: 20rpx; background: #f1f5f9;
  font-size: 26rpx; color: #475569; border: 2rpx solid transparent;
}
.chip.selected { background: #0f172a; color: #fff; border-color: #0f172a; }
</style>
