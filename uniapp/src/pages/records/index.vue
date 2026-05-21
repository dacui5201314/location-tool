<template>
  <view class="records-page">
    <!-- Filter tabs -->
    <view class="tabs">
      <view
        v-for="tab in tabs" :key="tab.key"
        class="tab" :class="{ active: activeTab === tab.key }"
        @tap="activeTab = tab.key"
      >
        <text>{{ tab.label }}</text>
        <text class="count" v-if="tab.count !== null"> ({{ tab.count }})</text>
      </view>
    </view>

    <!-- Record list -->
    <view class="list" v-if="filteredRecords.length">
      <ReportCard
        v-for="r in filteredRecords" :key="r.id"
        :title="r.title" :address="r.address" :status="r.status"
        :tags="r.tags" :score="r.score" :time="r.time"
        @click="onDetail(r.id)"
      />
    </view>
    <EmptyState v-else icon="📋" title="暂无分析记录" desc="完成首次选址分析后记录将出现在这里" />
  </view>
</template>

<script>
import ReportCard from '../../components/report-card/index.vue'
import EmptyState from '../../components/empty-state/index.vue'

export default {
  components: { ReportCard, EmptyState },
  data () {
    return {
      activeTab: 'all',
      tabs: [
        { key: 'all', label: '全部', count: 12 },
        { key: 'done', label: '已完成', count: 10 },
        { key: 'analyzing', label: '分析中', count: 0 },
        { key: 'exported', label: '已导出', count: 2 }
      ],
      // Phase 23A: mock 记录
      records: [
        { id: 1, title: '火锅店 · 建国路88号', address: '北京市朝阳区建国路88号', status: '已完成', tags: ['火锅店', '150㎡'], score: 62, time: '2026-05-20 15:30' },
        { id: 2, title: '民宿青旅 · 天河路208号', address: '广州市天河区天河路208号', status: '已导出', tags: ['民宿青旅'], score: 62, time: '2026-05-19 17:38' },
        { id: 3, title: '洗衣店 · 天河路208号', address: '广州市天河区天河路208号', status: '已完成', tags: ['洗衣店'], score: 55, time: '2026-05-20 14:29' },
        { id: 4, title: '诊所 · 建国路88号', address: '北京市朝阳区建国路88号', status: '已完成', tags: ['诊所'], score: 50, time: '2026-05-20 14:30' }
      ]
    }
  },
  computed: {
    filteredRecords () {
      if (this.activeTab === 'all') return this.records
      if (this.activeTab === 'done') return this.records.filter(r => r.status === '已完成')
      if (this.activeTab === 'analyzing') return []
      if (this.activeTab === 'exported') return this.records.filter(r => r.status === '已导出')
      return this.records
    }
  },
  methods: {
    onDetail (id) {
      uni.navigateTo({ url: `/pages/report-detail/index?id=${id}` })
    }
  }
}
</script>

<style scoped>
.records-page { min-height: 100vh; padding: 16rpx 24rpx; }
.tabs { display: flex; gap: 8rpx; padding: 16rpx 0; }
.tab {
  padding: 14rpx 28rpx; border-radius: 24rpx; background: #f1f5f9;
  font-size: 26rpx; color: #475569;
}
.tab.active { background: #0f172a; color: #fff; }
.count { font-size: 22rpx; }
.list { padding-top: 16rpx; }
</style>
