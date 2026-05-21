<template>
  <view class="fav-page">
    <view class="summary-card">
      <text class="summary-text">你已收藏 {{ favorites.length }} 个地址</text>
      <text class="summary-sub">点击卡片可快速开始分析</text>
    </view>

    <view class="toolbar">
      <view class="filter-tabs">
        <view
          v-for="tab in filterTabs" :key="tab.key"
          class="ftab" :class="{ active: activeFilter === tab.key }"
          @tap="activeFilter = tab.key"
        >{{ tab.label }}</view>
      </view>
    </view>

    <view class="list" v-if="filteredFavorites.length">
      <ReportCard
        v-for="f in filteredFavorites" :key="f.id"
        :title="f.title" :address="f.address" :status="f.status" :time="f.time"
        @click="onSelect(f)"
      />
    </view>
    <EmptyState v-else icon="⭐" title="暂无收藏" desc="在首页搜索地址后可收藏" />
  </view>
</template>

<script>
import ReportCard from '../../components/report-card/index.vue'
import EmptyState from '../../components/empty-state/index.vue'

export default {
  components: { ReportCard, EmptyState },
  data () {
    return {
      activeFilter: 'all',
      filterTabs: [
        { key: 'all', label: '全部' },
        { key: 'pending', label: '待分析' },
        { key: 'done', label: '已分析' }
      ],
      favorites: [
        { id: 1, title: '北京市朝阳区建国路88号', address: '北京市朝阳区建国路88号SOHO现代城', status: '已分析', time: '2026-05-20 收集' },
        { id: 2, title: '广州市天河路208号', address: '广州市天河区天河路208号', status: '已分析', time: '2026-05-19 收集' },
        { id: 3, title: '上海市淮海中路999号', address: '上海市徐汇区淮海中路999号', status: '待分析', time: '2026-05-18 收集' }
      ]
    }
  },
  computed: {
    filteredFavorites () {
      if (this.activeFilter === 'all') return this.favorites
      if (this.activeFilter === 'done') return this.favorites.filter(f => f.status === '已分析')
      if (this.activeFilter === 'pending') return this.favorites.filter(f => f.status === '待分析')
      return this.favorites
    }
  },
  methods: {
    onSelect (f) {
      uni.navigateTo({ url: `/pages/home/index?addr=${encodeURIComponent(f.address)}` })
    }
  }
}
</script>

<style scoped>
.fav-page { min-height: 100vh; padding: 16rpx 24rpx; }
.summary-card {
  background: linear-gradient(135deg, #0f172a, #1e40af);
  border-radius: 20rpx; padding: 32rpx; color: #fff; margin-bottom: 20rpx;
}
.summary-text { display: block; font-size: 30rpx; font-weight: 700; }
.summary-sub { display: block; font-size: 24rpx; color: rgba(255,255,255,0.7); margin-top: 8rpx; }
.toolbar { margin-bottom: 16rpx; }
.filter-tabs { display: flex; gap: 8rpx; }
.ftab {
  padding: 12rpx 24rpx; border-radius: 20rpx; background: #f1f5f9;
  font-size: 26rpx; color: #475569;
}
.ftab.active { background: #0f172a; color: #fff; }
</style>
