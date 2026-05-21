<template>
  <view class="result-page">
    <!-- Disclaimer -->
    <view class="disclaimer">本工具不提供推荐/不推荐结论，各维度评分仅供参考，最终决策请结合实地考察与多方因素综合判断。</view>

    <!-- Warning -->
    <view class="warning" v-if="mockData.warning">
      <text>⚠️ {{ mockData.warning }}</text>
    </view>

    <!-- Overall score -->
    <ScorePanel :score="mockData.score" :dimensions="mockDims" />

    <!-- Key advantages -->
    <view class="section">
      <view class="section-title green">✅ 关键机会</view>
      <view class="item" v-for="(a, i) in mockData.advantages" :key="'a'+i">{{ i + 1 }}. {{ a }}</view>
    </view>

    <!-- Key risks -->
    <view class="section">
      <view class="section-title red">⚠️ 主要风险</view>
      <view class="item" v-for="(d, i) in mockData.disadvantages" :key="'d'+i">{{ i + 1 }}. {{ d }}</view>
    </view>

    <!-- Direct/Sub/Anchor mock -->
    <view class="section">
      <view class="section-title">🎯 竞品分析</view>
      <view class="stats-row">
        <view class="stat"><text class="stat-val">6 / 29 / 29</text><text class="stat-label">直接竞品</text></view>
        <view class="stat"><text class="stat-val">4 / 15 / 15</text><text class="stat-label">替代消费</text></view>
        <view class="stat"><text class="stat-val">17 / 32 / 55</text><text class="stat-label">客流锚点</text></view>
      </view>
    </view>

    <!-- Data quality -->
    <view class="section">
      <view class="section-title">📊 数据质量</view>
      <view class="qual-item">🏥 医院归并去重：原始 5 条POI合并为 1 家医院</view>
      <view class="qual-item">🧹 名称脱水剔除 54 个POI</view>
      <view class="qual-item">🔬 严谨度规则剔除 4 个无关POI</view>
    </view>

    <!-- Action plan -->
    <view class="section">
      <view class="section-title">📋 行动建议</view>
      <view class="item" v-for="(ap, i) in mockData.actionPlan" :key="'ap'+i">{{ i + 1 }}. {{ ap }}</view>
    </view>

    <!-- Footer -->
    <view class="footer-note">以上分析仅供参考，不构成投资建议。最终选址决策请结合实地考察、商务谈判等多方面因素综合判断。</view>
  </view>
</template>

<script>
import ScorePanel from '../../components/score-panel/index.vue'

export default {
  components: { ScorePanel },
  data () {
    return {
      mockData: {
        score: 62,
        warning: '周边住宿供给高度饱和，新进入者面临激烈竞争',
        advantages: [
          '200米步行圈内同类竞品为0家，品类空白红利显著',
          '500米覆盖范围内有4所学校，学区客群基数庞大',
          '500米内4个地铁站，公共交通便利'
        ],
        disadvantages: [
          '500米内仅1个住宅小区，常住人口基数薄弱',
          '500米内无公交站，非地铁覆盖区域的客群导入受限',
          '选址场景为大学城/学区，寒暑假期间客流可能回落'
        ],
        actionPlan: [
          '开业前验证动作：实地蹲点统计学校放学时段家长停留时长及消费意愿',
          '定价/产品动作：推出学区专属套餐，锁定学校流量',
          '获客动作：与周边学校建立合作，通过家长群发放体验券'
        ]
      },
      mockDims: [
        { key: 'pop', label: '人口密集度', value: 20 },
        { key: 'traffic', label: '交通可达性', value: 85 },
        { key: 'flow', label: '客流特征', value: 40 },
        { key: 'consumer', label: '消费人群', value: 35 },
        { key: 'competition', label: '竞争环境', value: 90 },
        { key: 'complement', label: '互补业态', value: 30 },
        { key: 'category', label: '品类优势', value: 65 },
        { key: 'cost', label: '成本压力', value: 45 }
      ]
    }
  }
}
</script>

<style scoped>
.result-page { padding: 24rpx; padding-bottom: 80rpx; }
.disclaimer {
  background: #fefce8; border: 1rpx solid #fde68a; border-radius: 14rpx;
  padding: 20rpx; font-size: 24rpx; color: #92400e; margin-bottom: 16rpx;
}
.warning {
  background: #fef2f2; border: 1rpx solid #fecaca; border-radius: 14rpx;
  padding: 20rpx; font-size: 26rpx; color: #dc2626; margin-bottom: 16rpx;
}
.section { background: #fff; border-radius: 20rpx; padding: 28rpx; margin-bottom: 20rpx; box-shadow: 0 2rpx 16rpx rgba(0,0,0,0.04); }
.section-title { font-size: 28rpx; font-weight: 700; margin-bottom: 16rpx; color: #1e293b; }
.section-title.green { color: #16a34a; }
.section-title.red { color: #dc2626; }
.item { font-size: 26rpx; color: #475569; line-height: 1.8; padding-left: 8rpx; }
.stats-row { display: flex; justify-content: space-around; text-align: center; }
.stat-val { display: block; font-size: 30rpx; font-weight: 800; color: #1e293b; }
.stat-label { display: block; font-size: 22rpx; color: #94a3b8; margin-top: 4rpx; }
.qual-item { font-size: 24rpx; color: #64748b; padding: 8rpx 0; }
.footer-note { text-align: center; font-size: 22rpx; color: #94a3b8; padding: 24rpx 0; }
</style>
