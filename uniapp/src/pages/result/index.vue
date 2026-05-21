<template>
  <view class="result-page">
    <!-- Disclaimer — 对齐 Web AnalysisResult -->
    <view class="disc">💡 本工具不提供"推荐/不推荐"结论，各维度评分仅供参考，最终决策请结合实地考察与多方因素综合判断。</view>

    <!-- Warning -->
    <view class="warn" v-if="mock.warning">⚠️ <text class="warn-bold">风险提示：</text>{{ mock.warning }}</view>

    <!-- Overall score + summary -->
    <view class="score-section">
      <view class="ss-left">
        <text class="ss-num" :style="{ color: sc(mock.score) }">{{ mock.score }}</text>
        <text class="ss-sub">/ 100</text>
        <text class="ss-label">8 维度平均</text>
      </view>
      <view class="ss-right">
        <text class="ss-title">📋 分析摘要</text>
        <text class="ss-text">{{ mock.summary }}</text>
      </view>
    </view>

    <!-- Advantages — 对齐 Web "关键优势" -->
    <view class="section">
      <view class="sec-title green">✅ 关键优势</view>
      <view class="item" v-for="(a, i) in mock.advantages" :key="'a'+i">{{ i+1 }}. {{ a }}</view>
    </view>

    <!-- Disadvantages — 对齐 Web "主要风险" -->
    <view class="section">
      <view class="sec-title red">⚠️ 主要风险</view>
      <view class="item" v-for="(d, i) in mock.disadvantages" :key="'d'+i">{{ i+1 }}. {{ d }}</view>
    </view>

    <!-- Dimension scores — 对齐 Web -->
    <view class="section">
      <view class="sec-title">📈 维度评分</view>
      <view class="dim-grid">
        <view class="dim-cell" v-for="d in mockDims" :key="d.key">
          <text class="dim-label">{{ d.label }}</text>
          <text class="dim-val" :style="{ color: sc(d.val) }">{{ d.val }}</text>
          <view class="dim-bar"><view class="dim-fill" :style="{ width: d.val+'%', background: sc(d.val) }" /></view>
        </view>
      </view>
    </view>

    <!-- Real data metrics — 对齐 Web -->
    <view class="section">
      <view class="sec-title">📊 周边真实数据</view>
      <view class="sec-sub">200m / 500m / 1000m 三层半径实时采集</view>
      <view class="metrics">
        <view class="metric" v-for="m in metrics" :key="m.label">
          <text class="m-icon">{{ m.icon }}</text>
          <text class="m-label">{{ m.label }}</text>
          <text class="m-val">{{ m.val }}</text>
        </view>
      </view>
    </view>

    <!-- Direct competitors — 对齐 Web -->
    <view class="section">
      <view class="sec-title">🎯 直接竞品（同类业态 · 严谨口径）</view>
      <view class="comp-row">
        <text>200m: 6 · 500m: 29 · 1km: 29</text>
      </view>
    </view>

    <!-- Substitute — 对齐 Web -->
    <view class="section" v-if="true">
      <view class="sec-title orange">🔶 替代消费压力（非同业态，不计入直接竞品）</view>
      <view class="comp-row"><text>200m: 4 · 500m: 15 · 1km: 15</text></view>
    </view>

    <!-- Traffic anchors — 对齐 Web -->
    <view class="section" v-if="true">
      <view class="sec-title green">🟢 客流锚点（商业活跃度参考 · 非竞品）</view>
      <view class="comp-row"><text>200m: 17 · 500m: 32 · 1km: 55</text></view>
    </view>

    <!-- Hot brands — 对齐 Web -->
    <view class="section">
      <view class="sec-title">🏪 周边连锁品牌（含客流锚点品牌）</view>
      <view class="brands">
        <text class="brand" v-for="b in mock.hotBrands" :key="b.name">{{ b.name }} ×{{ b.count }}</text>
      </view>
    </view>

    <!-- Data quality — 对齐 Web -->
    <view class="section">
      <view class="sec-title">📊 数据质量</view>
      <view class="qual-list">
        <text class="ql" v-for="q in mock.qualNotes" :key="q">{{ q }}</text>
      </view>
    </view>

    <!-- Action plan -->
    <view class="section">
      <view class="sec-title">📝 各维度详细分析</view>
      <view class="dim-detail" v-for="dp in detailPlans" :key="dp.key">
        <text class="dd-label">{{ dp.label }}</text>
        <text class="dd-text">{{ dp.text }}</text>
      </view>
    </view>

    <!-- Footer disclaimer -->
    <view class="footer">以上分析仅供参考，不构成投资建议。最终选址决策请结合实地考察、商务谈判等多方面因素综合判断。</view>
  </view>
</template>

<script>
import { scoreColor } from '../../utils/format'
export default {
  data () {
    return {
      mock: {
        score: 62,
        warning: '周边住宿供给高度饱和，新进入者面临激烈竞争',
        summary: '该位置具备学区+交通优势，但常住人口严重不足，适合教育培训业态依托学校客流生存，洗衣、诊所等社区刚需业态面临客源挑战。',
        advantages: [
          '周边500米内分布4所学校，学区客群基数庞大，午间及放学时段需求旺盛',
          '200米步行圈内同类竞品为0家，品类空白红利显著，切入窗口期明显',
          '500米内4个地铁站，公共交通极为便利，可有效导入外部客流'
        ],
        disadvantages: [
          '500米内仅1个住宅小区，常住人口基数严重不足，社区消费基本盘薄弱',
          '500米内无公交站，公共交通方式单一，对非地铁覆盖区域的客群吸引力有限',
          '选址场景为大学城/学区，寒暑假期间学生客群流失明显，需提前准备淡季预案'
        ],
        qualNotes: [
          '医院归并去重：原始 5 条POI合并为 1 家医院',
          '名称脱水剔除 54 个POI（公司/厂房/建材/培训/养生/中介等）',
          '严谨度规则剔除 4 个无关POI（会计/律所/广告/中介/SPA等）',
          '原始抓取 576 个POI，有效保留 426 个'
        ],
        hotBrands: [{ name: '全季', count: 4 }, { name: '瑞幸', count: 2 }, { name: '如家', count: 2 }, { name: '蜜雪冰城', count: 1 }, { name: '肯德基', count: 1 }]
      },
      mockDims: [
        { key: 'pop', label: '人口密度', val: 20 }, { key: 'traffic', label: '交通可达性', val: 85 },
        { key: 'flow', label: '客流特征', val: 40 }, { key: 'consumer', label: '消费人群', val: 35 },
        { key: 'competition', label: '竞争环境', val: 90 }, { key: 'complement', label: '互补业态', val: 30 },
        { key: 'category', label: '品类优势', val: 65 }, { key: 'cost', label: '成本预估', val: 45 }
      ],
      metrics: [
        { icon:'🏘️',label:'住宅小区',val:'1 / 1 / 1'},{ icon:'🏢',label:'写字楼',val:'0 / 0 / 0'},
        { icon:'🍽️',label:'餐饮门店',val:'46 / 73 / 74'},{ icon:'☕',label:'咖啡茶饮',val:'2 / 8 / 8'},
        { icon:'🛍️',label:'购物商场',val:'0 / 0 / 0'},{ icon:'🏫',label:'学校',val:'1 / 4 / 11'},
        { icon:'🏥',label:'医院/诊所',val:'0 / 0 / 0'},{ icon:'🚇',label:'地铁站',val:'2 / 4 / 8'},
        { icon:'🚌',label:'公交站',val:'0 / 0 / 0'},{ icon:'🏨',label:'酒店住宿',val:'5 / 25 / 71'},
        { icon:'🏦',label:'银行',val:'4 / 12 / 38'},{ icon:'🅿️',label:'停车场',val:'34 / 75 / 75'}
      ],
      detailPlans: [
        { key:'pop',label:'人口密集度',text:'500米步行圈内仅1个住宅小区，常住人口基数非常薄弱。依赖学校潮汐客流，缺乏稳定的社区日常人流。评分: 20' },
        { key:'traffic',label:'交通与可达性',text:'200米步行圈内设有2个地铁站，500米内增至4个，属双地铁覆盖核心区。500米内无公交站，但200米内停车场高达34个。评分: 85' },
        { key:'flow',label:'客流特征',text:'工作日早7:30-8:30、午11:30-13:00、晚16:30-18:00为学生上下学及接送高峰。周末及寒暑假客流预计下降60%-70%。评分: 40' },
        { key:'consumer',label:'消费人群属性',text:'客群以学生及接送家长为主，消费力中等偏下，注重性价比。办公人群缺失，缺乏高客单价商务客群。评分: 35' },
        { key:'competition',label:'竞争环境',text:'200米、500米、1公里内直接竞品均为0家，品类完全空白。当前为极佳的进入窗口期。评分: 90' },
        { key:'complement',label:'周边互补业态',text:'1公里内无购物商场、超市，商业配套严重缺失。周边餐饮业态丰富但缺乏零售、生活服务类互补业态。评分: 30' }
      ]
    }
  },
  methods: { sc: scoreColor }
}
</script>

<style scoped>
.result-page { padding:24rpx; padding-bottom:80rpx; background:#eef3f9; }
.disc { background:#fefce8; border:1rpx solid #fde68a; border-radius:14rpx; padding:20rpx; font-size:24rpx; color:#92400e; margin-bottom:16rpx; }
.warn { background:#fef2f2; border:1rpx solid #fecaca; border-radius:14rpx; padding:20rpx; font-size:26rpx; color:#dc2626; margin-bottom:16rpx; }
.warn-bold { font-weight:700; }
.score-section { background:#fff; border-radius:20rpx; padding:32rpx; display:flex; gap:28rpx; margin-bottom:20rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.ss-left { text-align:center; min-width:140rpx; }
.ss-num { font-size:72rpx; font-weight:900; } .ss-sub { font-size:24rpx; color:#94a3b8; display:block; } .ss-label { font-size:22rpx; color:#64748b; margin-top:4rpx; }
.ss-right { flex:1; } .ss-title { font-size:26rpx; font-weight:700; color:#1e293b; margin-bottom:8rpx; display:block; } .ss-text { font-size:26rpx; color:#475569; line-height:1.7; }
.section { background:#fff; border-radius:20rpx; padding:28rpx; margin-bottom:20rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.sec-title { font-size:28rpx; font-weight:700; color:#1e293b; margin-bottom:16rpx; }
.sec-title.green { color:#047857; } .sec-title.red { color:#b91c1c; } .sec-title.orange { color:#d97706; }
.sec-sub { font-size:22rpx; color:#94a3b8; margin-bottom:16rpx; }
.item { font-size:26rpx; color:#475569; line-height:1.9; padding-left:4rpx; }
.dim-grid { display:flex; flex-wrap:wrap; gap:16rpx; }
.dim-cell { width:calc(50% - 8rpx); }
.dim-label { font-size:24rpx; color:#64748b; display:block; } .dim-val { font-size:32rpx; font-weight:700; display:block; margin:4rpx 0; }
.dim-bar { height:10rpx; background:#f1f5f9; border-radius:5rpx; } .dim-fill { height:100%; border-radius:5rpx; }
.metrics { display:flex; flex-wrap:wrap; gap:12rpx; }
.metric { width:calc(33.3% - 8rpx); text-align:center; padding:12rpx 0; }
.m-icon { font-size:28rpx; display:block; } .m-label { font-size:22rpx; color:#64748b; display:block; } .m-val { font-size:26rpx; font-weight:700; color:#1e293b; display:block; }
.comp-row { font-size:26rpx; color:#475569; }
.brands { display:flex; flex-wrap:wrap; gap:10rpx; }
.brand { font-size:24rpx; padding:8rpx 16rpx; background:#f1f5f9; border-radius:12rpx; color:#334155; }
.qual-list { } .ql { font-size:24rpx; color:#64748b; display:block; padding:6rpx 0; }
.dim-detail { margin-bottom:16rpx; } .dd-label { font-size:26rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:6rpx; } .dd-text { font-size:26rpx; color:#475569; line-height:1.7; }
.footer { text-align:center; font-size:22rpx; color:#94a3b8; padding:24rpx 16rpx; line-height:1.6; }
</style>
