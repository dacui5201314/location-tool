<template>
  <view class="detail-page">
    <!-- Meta card -->
    <view class="meta-card">
      <view class="meta-row"><text class="meta-label">地址</text><text class="meta-val">{{ meta.address }}</text></view>
      <view class="meta-row"><text class="meta-label">业态</text><text class="meta-val">{{ meta.businessType }}</text></view>
      <view class="meta-row" v-if="meta.brand"><text class="meta-label">品牌</text><text class="meta-val">{{ meta.brand }}</text></view>
      <view class="meta-row" v-if="meta.storeSize"><text class="meta-label">面积</text><text class="meta-val">{{ meta.storeSize }} ㎡</text></view>
      <view class="meta-row"><text class="meta-label">分析时间</text><text class="meta-val">{{ meta.time }}</text></view>
      <view class="meta-score" v-if="meta.score > 0">
        <text class="score-big" :style="{ color: scoreColor(meta.score) }">{{ meta.score }}</text>
        <text class="score-label">综合评分</text>
      </view>
    </view>

    <!-- Report content placeholder -->
    <view class="section">
      <view class="section-header">报告内容</view>
      <ScorePanel :score="meta.score" :dimensions="mockDims" />
      <view class="placeholder-box">
        <text class="ph-text">📊 完整的 direct / substitute / anchor / 数据质量 区块将在 Phase 23D 接入真实报告数据后展示。</text>
      </view>
    </view>

    <!-- PDF toolbar -->
    <view class="pdf-bar">
      <button class="pdf-btn locked">🔒 消耗 1 点数导出 PDF</button>
    </view>
  </view>
</template>

<script>
import ScorePanel from '../../components/score-panel/index.vue'
import { scoreColor } from '../../utils/format'

export default {
  components: { ScorePanel },
  data () {
    return {
      meta: {
        address: '广州市天河区天河路208号',
        businessType: '民宿青旅',
        brand: '',
        storeSize: '',
        time: '2026-05-19 17:38',
        score: 62
      },
      mockDims: [
        { key: 'population', label: '人口密集度', value: 20 },
        { key: 'traffic', label: '交通可达性', value: 85 },
        { key: 'flow', label: '客流特征', value: 40 },
        { key: 'consumer', label: '消费人群', value: 35 },
        { key: 'competition', label: '竞争环境', value: 90 },
        { key: 'complement', label: '互补业态', value: 30 },
        { key: 'category', label: '品类优势', value: 65 },
        { key: 'cost', label: '成本压力', value: 45 }
      ]
    }
  },
  methods: { scoreColor }
}
</script>

<style scoped>
.detail-page { padding: 24rpx; padding-bottom: 140rpx; }
.meta-card {
  background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 24rpx;
  box-shadow: 0 2rpx 16rpx rgba(0,0,0,0.04);
}
.meta-row { display: flex; justify-content: space-between; padding: 12rpx 0; border-bottom: 1rpx solid #f1f5f9; }
.meta-label { color: #94a3b8; font-size: 26rpx; }
.meta-val { color: #1e293b; font-size: 26rpx; font-weight: 500; }
.meta-score { text-align: center; margin-top: 20rpx; }
.score-big { font-size: 72rpx; font-weight: 900; }
.score-label { display: block; font-size: 24rpx; color: #94a3b8; }
.section { margin-bottom: 24rpx; }
.section-header { font-size: 30rpx; font-weight: 700; color: #1e293b; margin-bottom: 16rpx; }
.placeholder-box { background: #fefce8; border: 1rpx solid #fde68a; border-radius: 14rpx; padding: 24rpx; margin-top: 16rpx; }
.ph-text { font-size: 26rpx; color: #92400e; }
.pdf-bar { position: fixed; bottom: 0; left: 0; right: 0; padding: 20rpx 24rpx; background: #fff; border-top: 1rpx solid #e2e8f0; }
.pdf-btn { width: 100%; border-radius: 14rpx; font-size: 30rpx; padding: 20rpx 0; }
.pdf-btn.locked { background: #f59e0b; color: #fff; }
</style>
