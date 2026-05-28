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
.cat-scroll { width:100%; height:130rpx; white-space:nowrap; display:block; }
.cat-tile { display: inline-flex; flex-direction: column; align-items: center; width: 126rpx; min-height: 96rpx; padding: 18rpx 8rpx; margin-right: 14rpx; border-radius: 20rpx; background: linear-gradient(180deg,#ffffff,#fbfdff); border: 1px solid rgba(219,230,255,0.95); box-shadow: 0 10rpx 22rpx rgba(74,111,172,0.07); flex-shrink:0; box-sizing:border-box; vertical-align:top; }
.cat-tile.active { background: linear-gradient(180deg,#ffffff,#f4f7ff); border-color: rgba(13,75,220,0.60); box-shadow: 0 14rpx 30rpx rgba(13,75,220,0.16); }
.cat-icon { position: relative; width: 58rpx; height: 58rpx; line-height: 58rpx; text-align: center; border-radius: 18rpx; background: linear-gradient(145deg,#f6f9ff,#ffffff); color: transparent; font-size: 0; box-shadow: inset 0 0 0 1px rgba(13,75,220,0.10),0 8rpx 18rpx rgba(74,111,172,0.06); overflow: hidden; }
.cat-icon::before,.cat-icon::after { content: ''; position: absolute; box-sizing: border-box; }
.cat-icon::before { left: 16rpx; top: 16rpx; width: 26rpx; height: 26rpx; border-radius: 8rpx; border: 4rpx solid #0d4bdc; }
.cat-icon::after { left: 22rpx; top: 22rpx; width: 14rpx; height: 14rpx; border-radius: 50%; background: rgba(13,75,220,0.16); }
.cat-tile.active .cat-icon { background: linear-gradient(135deg,#0d4bdc,#5b4be6); box-shadow: 0 12rpx 24rpx rgba(13,75,220,0.24); }
.cat-tile.active .cat-icon::before { border-color: #fff; }
.cat-tile.active .cat-icon::after { background: rgba(255,255,255,0.30); }
.cat-tile:nth-child(1) .cat-icon::before { left: 15rpx; top: 25rpx; width: 28rpx; height: 14rpx; border-radius: 0 0 16rpx 16rpx; border-top: 0; }
.cat-tile:nth-child(1) .cat-icon::after { left: 20rpx; top: 15rpx; width: 18rpx; height: 14rpx; border-radius: 50%; background: rgba(13,75,220,0.18); }
.cat-tile:nth-child(2) .cat-icon::before { left: 15rpx; top: 18rpx; width: 24rpx; height: 22rpx; border-radius: 0 0 14rpx 14rpx; }
.cat-tile:nth-child(2) .cat-icon::after { left: 38rpx; top: 22rpx; width: 8rpx; height: 12rpx; border: 3rpx solid #0d4bdc; border-left: 0; background: transparent; border-radius: 0 8rpx 8rpx 0; }
.cat-tile:nth-child(3) .cat-icon::before { left: 15rpx; top: 18rpx; width: 28rpx; height: 24rpx; border-radius: 5rpx; }
.cat-tile:nth-child(3) .cat-icon::after { left: 19rpx; top: 14rpx; width: 20rpx; height: 8rpx; border-radius: 8rpx 8rpx 0 0; background: #0d4bdc; }
.cat-tile:nth-child(4) .cat-icon::before { left: 14rpx; top: 14rpx; width: 30rpx; height: 32rpx; border-radius: 4rpx; background: repeating-linear-gradient(90deg,transparent 0 8rpx,rgba(13,75,220,0.14) 8rpx 11rpx); }
.cat-tile:nth-child(4) .cat-icon::after { left: 24rpx; top: 36rpx; width: 10rpx; height: 10rpx; border-radius: 2rpx 2rpx 0 0; background: #0d4bdc; }
.cat-tile:nth-child(5) .cat-icon::before { left: 17rpx; top: 17rpx; width: 24rpx; height: 24rpx; border-radius: 50%; }
.cat-tile:nth-child(5) .cat-icon::after { left: 27rpx; top: 11rpx; width: 4rpx; height: 36rpx; border-radius: 999rpx; background: #0d4bdc; transform: rotate(45deg); }
.cat-tile:nth-child(6) .cat-icon::before { left: 14rpx; top: 21rpx; width: 30rpx; height: 18rpx; border-radius: 10rpx; }
.cat-tile:nth-child(6) .cat-icon::after { left: 22rpx; top: 18rpx; width: 14rpx; height: 8rpx; border-radius: 8rpx 8rpx 0 0; background: #0d4bdc; }
.cat-tile.active:nth-child(1) .cat-icon::after,.cat-tile.active:nth-child(3) .cat-icon::after,.cat-tile.active:nth-child(4) .cat-icon::after,.cat-tile.active:nth-child(5) .cat-icon::after,.cat-tile.active:nth-child(6) .cat-icon::after { background:#fff; }
.cat-tile.active:nth-child(2) .cat-icon::after { border-color:#fff; }
.cat-name { font-size: 22rpx; font-weight: 900; color: #17244e; margin-top: 10rpx; }
.cat-tile.active .cat-name { color: #0d4bdc; }
.sub-panel { margin-top: 16rpx; display: flex; flex-wrap: wrap; gap: 12rpx; padding: 16rpx; border-radius: 16rpx; background: linear-gradient(180deg,#f8fbff,#ffffff); border: 1px solid rgba(219,230,255,0.78); }
.chip { padding: 12rpx 24rpx; border-radius: 16rpx; background: #fff; font-size: 26rpx; font-weight: 700; color: #5c677d; border: 1px solid rgba(219,230,255,0.95); box-shadow: 0 8rpx 18rpx rgba(74,111,172,0.05); }
.chip.selected { background: #f3f7ff; color: #315bff; border-color: rgba(88,105,255,0.44); box-shadow: 0 10rpx 20rpx rgba(68,84,255,0.11); }
</style>
