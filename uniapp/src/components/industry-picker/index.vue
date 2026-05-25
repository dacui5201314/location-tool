<template>
  <view class="industry-picker">
    <view class="label" v-if="!hideLabel">选择业态</view>
    <scroll-view scroll-x class="cat-scroll">
      <view v-for="cat in displayCats" :key="cat.key" class="cat-tile" :class="[{ active: activeCat === cat.key }, 'cat-' + cat.key]" @tap="selectCat(cat.key)">
        <text class="cat-icon">{{ cat.icon }}</text>
        <text class="cat-name">{{ cat.label }}</text>
      </view>
    </scroll-view>
    <view class="sub-panel" v-if="activeCat && subTypes.length">
      <view v-for="st in subTypes" :key="st.name" class="chip" :class="{ selected: selected === st.name }" @tap="onSelect(st.name)">{{ st.name }}</view>
    </view>
  </view>
</template>

<script>
const mockIndustries = [
  { key:'food', icon:'🍽️', label:'餐饮', subTypes:['小餐饮','大餐饮','中餐','日餐','西餐','火锅店','烧烤店','小吃店','烘焙店','快餐店'] },
  { key:'drink', icon:'☕', label:'茶饮咖啡', subTypes:['奶茶店','咖啡店','甜品店','饮品店'] },
  { key:'retail', icon:'🛍️', label:'零售商业', subTypes:['零售店','便利店','超市','服装店','数码店','药店'] },
  { key:'hotel', icon:'🏨', label:'酒店住宿', subTypes:['酒店','民宿','青年旅舍'] },
  { key:'service', icon:'💇', label:'生活服务', subTypes:['美容美发','健身房','教育培训','宠物店','洗衣店','诊所'] },
  { key:'entertainment', icon:'🎮', label:'休闲娱乐', subTypes:['酒吧','KTV','剧本杀','网吧','台球厅'] }
]

const CATEGORY_ICON = {
  '餐饮': '☕',
  '茶饮咖啡': '☕',
  '零售商业': '□',
  '酒店住宿': '▦',
  '生活服务': '✂',
  '休闲娱乐': '◇'
}

// 扁平后端数组 → picker 分类结构
function groupIndustries (flat) {
  if (!Array.isArray(flat) || !flat.length) return null
  const catMap = {}
  const seen = new Set()
  flat.forEach(item => {
    const name = item.name; if (!name) return
    const cat = item.category || '其他'
    if (!catMap[cat]) catMap[cat] = { key: cat, label: cat, icon: CATEGORY_ICON[cat] || '◇', subTypes: [] }
    if (!seen.has(name)) { catMap[cat].subTypes.push(name); seen.add(name) }
  })
  const cats = Object.values(catMap)
  return cats.length ? cats : null
}

export default {
  name: 'IndustryPicker',
  props: {
    selected: { type: String, default: '' },
    hideLabel: { type: Boolean, default: false },
    industries: { type: Array, default: () => [] },
    disabled: { type: Boolean, default: false }
  },
  data () { return { activeCat: '', subTypes: [] } },
  computed: {
    displayCats () {
      return groupIndustries(this.industries) || mockIndustries
    }
  },
  methods: {
    selectCat (key) {
      if (this.disabled) return
      this.activeCat = key
      const list = this.displayCats
      const cat = list.find(c => c.key === key)
      this.subTypes = cat && cat.subTypes ? cat.subTypes.map(s => ({ name: s })) : []
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
.cat-tile { display: inline-flex; flex-direction: column; align-items: center; width: 118rpx; padding: 18rpx 8rpx; margin-right: 12rpx; border-radius: 18rpx; background: linear-gradient(180deg,#ffffff,#fbfdff); border: 1px solid rgba(219,230,255,0.95); box-shadow: 0 10rpx 22rpx rgba(74,111,172,0.07); }
.cat-tile.active { background: linear-gradient(180deg,#ffffff,#f3f7ff); border-color: rgba(21,93,255,0.58); box-shadow: 0 14rpx 30rpx rgba(21,93,255,0.16); }
.cat-icon { position: relative; width: 50rpx; height: 50rpx; line-height: 50rpx; text-align: center; border-radius: 16rpx; background: linear-gradient(135deg,#f1f6ff,#ffffff); color: transparent; font-size: 0; box-shadow: inset 0 0 0 1px rgba(21,93,255,0.08); }
.cat-icon::before { content: ''; position: absolute; left: 13rpx; top: 13rpx; width: 22rpx; height: 22rpx; border-radius: 6rpx; border: 3rpx solid #155dff; box-sizing: border-box; }
.cat-tile.active .cat-icon { background: linear-gradient(135deg,#155dff,#6d5cff); box-shadow: 0 10rpx 20rpx rgba(21,93,255,0.24); }
.cat-tile.active .cat-icon::before { border-color: #fff; }
.cat-food .cat-icon::before,.cat-drink .cat-icon::before { border-radius: 50%; border-width: 4rpx; }
.cat-retail .cat-icon::before { border-radius: 4rpx; }
.cat-hotel .cat-icon::before { border-radius: 2rpx; box-shadow: 0 0 0 5rpx rgba(124,85,255,0.10); }
.cat-service .cat-icon::before { width: 22rpx; height: 10rpx; top: 19rpx; border-radius: 999rpx; }
.cat-entertainment .cat-icon::before { transform: rotate(45deg); border-radius: 4rpx; }
.cat-name { font-size: 22rpx; font-weight: 900; color: #17244e; margin-top: 10rpx; }
.cat-tile.active .cat-name { color: #155dff; }
.sub-panel { margin-top: 16rpx; display: flex; flex-wrap: wrap; gap: 12rpx; padding: 16rpx; border-radius: 16rpx; background: linear-gradient(180deg,#f8fbff,#ffffff); border: 1px solid rgba(219,230,255,0.78); }
.chip { padding: 12rpx 24rpx; border-radius: 16rpx; background: #fff; font-size: 26rpx; font-weight: 700; color: #5c677d; border: 1px solid rgba(219,230,255,0.95); box-shadow: 0 8rpx 18rpx rgba(74,111,172,0.05); }
.chip.selected { background: #f3f7ff; color: #315bff; border-color: rgba(88,105,255,0.44); box-shadow: 0 10rpx 20rpx rgba(68,84,255,0.11); }
</style>
