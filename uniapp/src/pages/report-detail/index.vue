<template>
  <view class="detail-page">
    <!-- Loading -->
    <view class="loading" v-if="loading"><text class="ld-dots">...</text><text class="ld-text">加载中...</text></view>

    <!-- Error -->
    <view class="error" v-if="!loading && errorMsg">
      <text class="err-icon">📭</text>
      <text class="err-text">{{ errorMsg }}</text>
      <button class="err-btn" @tap="goBack">返回记录列表</button>
    </view>

    <!-- Content -->
    <view v-if="!loading && !errorMsg">
      <!-- Top bar -->
      <view class="top-bar">
        <text class="back" @tap="goBack">←</text>
        <text class="top-title">{{ recordTitle }}</text>
        <text class="top-export" :class="record.is_pdf_unlocked ? 'free' : 'locked'">
          PDF 联调未开放
        </text>
      </view>

      <!-- Meta card -->
      <view class="meta-card">
        <view class="meta-grid">
          <view class="mg-item"><text class="mgl">地址</text><text class="mgv">{{ record.address || '-' }}</text></view>
          <view class="mg-item"><text class="mgl">品牌/业态</text><text class="mgv">{{ record.brand_desc || record.business_type || '-' }}</text></view>
          <view class="mg-item"><text class="mgl">门店面积</text><text class="mgv">{{ record.store_size ? record.store_size + '㎡' : '-' }}</text></view>
          <view class="mg-item"><text class="mgl">分析时间</text><text class="mgv">{{ fmtTime(record.created_at) || '-' }}</text></view>
        </view>
        <view class="meta-score" v-if="rptScore > 0">
          <text class="ms-num" :style="{ color: sc(rptScore) }">{{ rptScore }}</text>
          <text class="ms-label">综合评分</text>
          <text class="ms-badge" :class="record.is_pdf_unlocked ? 'free' : 'locked'">{{ record.is_pdf_unlocked ? 'PDF 已解锁' : 'PDF 未解锁' }}</text>
        </view>
      </view>

      <!-- Location info -->
      <view class="section" v-if="rptCity">
        <view class="sec-title">📍 位置范围</view>
        <view class="loc-row"><text>{{ rptCity }}{{ rptDistrict ? ' · ' + rptDistrict : '' }}</text></view>
      </view>

      <!-- Stats triple-radius metrics -->
      <view class="section" v-if="hasStats">
        <view class="sec-title">📊 周边数据（200m / 500m / 1km）</view>
        <view class="stats-grid">
          <view class="sg" v-for="m in rptStats" :key="m.key">
            <text class="sg-label">{{ m.label }}</text>
            <text class="sg-val">{{ m.s200 === '' ? '-' : m.s200 }} / {{ m.s500 === '' ? '-' : m.s500 }} / {{ m.s1000 === '' ? '-' : m.s1000 }}</text>
          </view>
        </view>
      </view>

      <!-- Competitor names (poi_lists) -->
      <view class="section" v-if="rptDirList.length">
        <view class="sec-title">🎯 直接竞品列表</view>
        <view class="item-sm" v-for="(n,i) in rptDirList" :key="'d'+i">{{ n }}</view>
        <text class="more-hint" v-if="rptDirMore > 0">还有 {{ rptDirMore }} 条未展开</text>
      </view>
      <view class="section" v-if="rptSubList.length">
        <view class="sec-title orange">🔶 替代竞品列表</view>
        <view class="item-sm" v-for="(n,i) in rptSubList" :key="'s'+i">{{ n }}</view>
        <text class="more-hint" v-if="rptSubMore > 0">还有 {{ rptSubMore }} 条未展开</text>
      </view>
      <view class="section" v-if="rptAncList.length">
        <view class="sec-title green">🟢 客流锚点列表</view>
        <view class="item-sm" v-for="(n,i) in rptAncList" :key="'a'+i">{{ n }}</view>
        <text class="more-hint" v-if="rptAncMore > 0">还有 {{ rptAncMore }} 条未展开</text>
      </view>

      <!-- Empty content -->
      <view class="content-box" v-if="!hasContent">
        <text class="cb-title">📊 报告内容</text>
        <text class="cb-text">暂无完整报告内容。该记录可能是旧版格式或报告数据尚未生成。</text><text class="cb-hint">元数据（地址/业态/评分）可正常查看</text>
      </view>

      <!-- Disclaimer -->
      <view class="disc" v-if="rptDisclaimer">💡 {{ rptDisclaimer }}</view>

      <!-- Warning -->
      <view class="warn" v-if="rptWarning">⚠️ <text class="warn-bold">风险提示：</text>{{ rptWarning }}</view>

      <!-- Summary -->
      <view class="section" v-if="rptSummary">
        <view class="sec-title">📋 分析摘要</view>
        <text class="sec-text">{{ rptSummary }}</text>
      </view>

      <!-- Advantages -->
      <view class="section" v-if="rptAdv.length">
        <view class="sec-title green">✅ 关键优势</view>
        <view class="item" v-for="(a,i) in rptAdv" :key="'a'+i">{{ i+1 }}. {{ a }}</view>
      </view>

      <!-- Disadvantages -->
      <view class="section" v-if="rptDis.length">
        <view class="sec-title red">⚠️ 主要风险</view>
        <view class="item" v-for="(d,i) in rptDis" :key="'d'+i">{{ i+1 }}. {{ d }}</view>
      </view>

      <!-- Dimension scores -->
      <view class="section" v-if="rptDims.length">
        <view class="sec-title">📈 维度评分</view>
        <view class="dim-grid">
          <view class="dim-cell" v-for="d in rptDims" :key="d.key">
            <text class="dl">{{ d.label }}</text>
            <text class="dv" :style="{ color: sc(d.value) }">{{ d.value }}</text>
            <view class="db"><view class="df" :style="{ width: d.value+'%', background: sc(d.value) }" /></view>
          </view>
        </view>
      </view>

      <!-- Competition data -->
      <view class="section" v-if="hasCompetition">
        <view class="sec-title">🎯 直接竞品（同类业态 · 严谨口径）</view>
        <view class="comp-row">
          <text>200m: {{ rptDir200 }} · 500m: {{ rptDir500 }} · 1km: {{ rptDir1000 }}</text>
        </view>
      </view>

      <view class="section" v-if="rptSub500 > 0 || rptSub1000 > 0">
        <view class="sec-title orange">🔶 替代消费压力（非同业态，不计入直接竞品）</view>
        <view class="comp-row"><text>200m: {{ rptSub200 }} · 500m: {{ rptSub500 }} · 1km: {{ rptSub1000 }}</text></view>
      </view>

      <view class="section" v-if="rptAnc500 > 0 || rptAnc1000 > 0">
        <view class="sec-title green">🟢 客流锚点（商业活跃度参考 · 非竞品）</view>
        <view class="comp-row"><text>200m: {{ rptAnc200 }} · 500m: {{ rptAnc500 }} · 1km: {{ rptAnc1000 }}</text></view>
      </view>

      <!-- Irrelevant excluded -->
      <view class="section" v-if="rptIrr > 0">
        <view class="sec-title">🔬 严谨度剔除</view>
        <view class="comp-row"><text>{{ rptIrr }} 个无关 POI 已被严谨度规则剔除</text></view>
        <view class="item-sm" v-for="(n,i) in rptIrrList" :key="'irr'+i">{{ n }}</view>
      </view>

      <!-- Hot brands -->
      <view class="section" v-if="rptBrands.length">
        <view class="sec-title">🏪 周边连锁品牌</view>
        <view class="brands">
          <text class="brand" v-for="b in rptBrands" :key="b.name">{{ b.name }} ×{{ b.count }}</text>
        </view>
      </view>

      <!-- Data quality -->
      <view class="section" v-if="rptQual.length">
        <view class="sec-title">📊 数据质量</view>
        <text class="ql" v-for="(q,i) in rptQual" :key="'q'+i">{{ q }}</text>
      </view>

      <!-- Action plan -->
      <view class="section" v-if="rptAction.length">
        <view class="sec-title">📋 行动建议</view>
        <view class="item" v-for="(ap,i) in rptAction" :key="'ap'+i">{{ i+1 }}. {{ ap }}</view>
      </view>

      <!-- Bottom bar -->
      <view class="bottom-bar">
        <button v-if="record.is_pdf_unlocked" class="bb-export">PDF 下载联调未开放</button>
        <button v-else class="bb-unlock" @tap="onExport">PDF 解锁联调未开放</button>
        <button class="bb-back" @tap="goBack">返回</button>
      </view>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'
import { scoreColor, formatTime } from '../../utils/format'

export default {
  data () {
    return {
      loading: true, errorMsg: '', record: {},
      // Parsed report_json fields
      rptScore: 0, rptDisclaimer: '', rptWarning: '', rptSummary: '',
      rptAdv: [], rptDis: [], rptDims: [], rptAction: [],
      rptDir200: 0, rptDir500: 0, rptDir1000: 0,
      rptSub200: 0, rptSub500: 0, rptSub1000: 0,
      rptAnc200: 0, rptAnc500: 0, rptAnc1000: 0,
      rptIrr: 0, rptBrands: [],
      rptQual: [],
      rptCity: '', rptDistrict: '',
      rptStats: [],
      rptDirList: [], rptSubList: [], rptAncList: [],
      rptIrrList: [],
      rptDirMore: 0, rptSubMore: 0, rptAncMore: 0
    }
  },
  computed: {
    recordTitle () { return this.record.brand_desc || this.record.business_type || '报告详情' },
    hasCompetition () { return this.rptDir200 + this.rptDir500 + this.rptDir1000 > 0 },
    hasContent () { return this.rptScore > 0 || this.rptSummary || this.rptAdv.length || this.rptDims.length || this.rptQual.length || this.rptBrands.length || this.rptIrr > 0 || this.rptCity || this.hasStats || this.rptDirList.length },
    hasStats () { return this.rptStats.length > 0 }
  },
  onLoad (options) {
    const id = options.id
    if (!id) { this.loading = false; this.errorMsg = '缺少记录 ID'; return }
    api.fetchRecordDetail(id).then(r => {
      this.loading = false
      if (r.ok && r.data && !r.data.error) {
        this.record = r.data
        this.parseReport(r.data.report_json)
      } else {
        const detail = r.data?.detail || r.data?.error || ''
        if (r.statusCode === 404 || detail.includes('not found') || detail.includes('不存在')) this.errorMsg = '记录不存在'
        else if (r.statusCode === 401) this.errorMsg = '请先登录后查看'
        else this.errorMsg = detail || '记录加载失败'
      }
    }).catch(() => { this.loading = false; this.errorMsg = '网络异常，请重试' })
  },
  methods: {
    sc: scoreColor, fmtTime: formatTime,
    goBack () { uni.navigateBack({ delta: 1 }).catch(() => uni.switchTab({ url: '/pages/records/index' })) },
    onExport () {
      uni.showToast({ title: 'PDF / 下载 / 解锁联调未开放', icon: 'none' })
    },
    parseReport (raw) {
      // 重置所有派生字段，避免旧报告残留
      ['rptScore','rptDisclaimer','rptWarning','rptSummary','rptAdv','rptDis','rptDims','rptAction',
       'rptDir200','rptDir500','rptDir1000','rptSub200','rptSub500','rptSub1000',
       'rptAnc200','rptAnc500','rptAnc1000','rptIrr','rptBrands','rptQual',
       'rptCity','rptDistrict','rptStats','rptDirList','rptSubList','rptAncList','rptIrrList',
       'rptDirMore','rptSubMore','rptAncMore'
      ].forEach(k => { this[k] = Array.isArray(this[k]) ? [] : (typeof this[k] === 'number' ? 0 : '') })

      let rpt = null
      if (typeof raw === 'string') { try { rpt = JSON.parse(raw) } catch (e) { return } } else if (raw && typeof raw === 'object') { rpt = raw } else { return }

      const rd = rpt.real_data || {}
      const exec = rpt.executive_summary || {}
      const dimScores = Array.isArray(rpt.dimension_scores) ? rpt.dimension_scores : []

      // 安全转字符串：数组内对象 → title/text/description/content → JSON 兜底
      const _sa = (arr) => {
        if (!Array.isArray(arr)) return []
        return arr.map(x => {
          if (typeof x === 'string') return x
          if (typeof x === 'object' && x !== null) return x.title || x.text || x.description || x.content || x.message || JSON.stringify(x)
          return String(x)
        })
      }

      this.rptScore = rpt.score ?? rpt.overall_score ?? 0
      this.rptDisclaimer = rpt.disclaimer || ''
      this.rptWarning = rpt.warning || ''
      this.rptSummary = rpt.summary || exec.summary || ''

      this.rptAdv = _sa(rpt.advantages)
      this.rptDis = _sa(rpt.disadvantages)
      this.rptAction = _sa(rpt.action_plan)

      this.rptDims = dimScores.map(d => ({
        key: d.key || d.name || '', label: d.label || d.title || d.key || '', value: d.score ?? d.value ?? 0
      }))

      this.rptQual = _sa(rd.data_quality_notes)

      this.rptDir200 = rd.direct_competitors_200m ?? 0
      this.rptDir500 = rd.direct_competitors_500m ?? 0
      this.rptDir1000 = rd.direct_competitors_1000m ?? 0
      this.rptSub200 = rd.substitute_competitors_200m ?? 0
      this.rptSub500 = rd.substitute_competitors_500m ?? 0
      this.rptSub1000 = rd.substitute_competitors_1000m ?? 0
      this.rptAnc200 = rd.traffic_anchors_200m ?? 0
      this.rptAnc500 = rd.traffic_anchors_500m ?? 0
      this.rptAnc1000 = rd.traffic_anchors_1000m ?? 0

      this.rptIrr = rd.irrelevant_excluded ?? 0
      // hot_brands alias: hot_brands / brands / chain_brands / brand_list
      const hb = rd.hot_brands || rd.brands || rd.chain_brands || rd.brand_list
      this.rptBrands = Array.isArray(hb) ? hb.map(b => {
        if (typeof b === 'string') return { name: b, count: 1 }
        return { name: b.name || b.title || b.brand_name || '', count: b.count ?? 1 }
      }).filter(b => b.name) : []

      // irrelevant list alias
      const irrList = rd.irrelevant_excluded_list || rd.irrelevant_list || rd.excluded_pois || rd.irrelevant_pois
      if (Array.isArray(irrList) && irrList.length) {
        this.rptIrrList = irrList.map(d => d.name || d.title || d.poi_name || '').filter(Boolean).slice(0, 5)
      }

      // city / district: real_data first, then top-level report_json
      this.rptCity = rd.city || rpt.city || ''
      this.rptDistrict = rd.district || rpt.district || ''

      // stats triple-radius: alias-aware key lookup
      const s2 = rd.stats_200m || {}
      const s5 = rd.stats_500m || {}
      const s10 = rd.stats_1000m || {}
      const _val = (stats, aliases) => {
        for (const a of aliases) { const v = stats[a]; if (v !== undefined && v !== null) return v }
        return ''
      }
      const metricAliases = {
        residential: ['residential','residences','communities','residential_areas'],
        office: ['office','offices','office_buildings'],
        restaurants: ['restaurants','restaurant','dining'],
        cafe_tea: ['cafe_tea','cafes','cafe','tea','coffee'],
        shopping: ['shopping','malls','shopping_malls'],
        schools: ['schools','school'],
        hospitals: ['hospitals','hospital','clinics','clinic'],
        subway: ['subway','subways','subway_stations','metro'],
        bus: ['bus','buses','bus_stops'],
        hotels: ['hotels','hotel'],
        banks: ['banks','bank'],
        parking: ['parking','parking_lots']
      }
      const metricLabels = { residential:'住宅小区',office:'写字楼',restaurants:'餐饮',cafe_tea:'咖啡茶饮',shopping:'购物商场',schools:'学校',hospitals:'医院',subway:'地铁站',bus:'公交站',hotels:'酒店',banks:'银行',parking:'停车场' }
      this.rptStats = Object.keys(metricAliases).map(key => ({
        key, label: metricLabels[key],
        s200: _val(s2, metricAliases[key]), s500: _val(s5, metricAliases[key]), s1000: _val(s10, metricAliases[key])
      })).filter(m => m.s200 !== '' || m.s500 !== '' || m.s1000 !== '')

      // poi_lists with field/name aliases
      const _names = (arr) => {
        if (!Array.isArray(arr)) return []
        return arr.map(d => d.name || d.title || d.poi_name || '').filter(Boolean)
      }
      const dirList = rd.direct_competitor_list || rd.direct_competitors || rd.direct_pois
      const subList = rd.substitute_list || rd.substitute_competitors || rd.substitute_pois
      const ancList = rd.traffic_anchor_list || rd.traffic_anchors || rd.anchor_pois
      const dl = _names(dirList); const sl = _names(subList); const al = _names(ancList)
      this.rptDirList = dl.slice(0, 5); this.rptDirMore = dl.length > 5 ? dl.length - 5 : 0
      this.rptSubList = sl.slice(0, 5); this.rptSubMore = sl.length > 5 ? sl.length - 5 : 0
      this.rptAncList = al.slice(0, 5); this.rptAncMore = al.length > 5 ? al.length - 5 : 0
    }
  }
}
</script>

<style scoped>
.detail-page { min-height:100vh; background:#eef3f9; padding-bottom:140rpx; }
.loading { text-align:center; padding:120rpx 0; } .ld-dots { font-size:60rpx; letter-spacing:12rpx; color:#94a3b8; } .ld-text { display:block; font-size:26rpx; color:#94a3b8; margin-top:16rpx; }
.error { text-align:center; padding:120rpx 32rpx; } .err-icon { font-size:80rpx; display:block; } .err-text { font-size:28rpx; color:#64748b; display:block; margin:16rpx 0; } .err-btn { margin-top:20rpx; background:#f1f5f9; color:#475569; border-radius:14rpx; padding:16rpx 40rpx; font-size:28rpx; }
.top-bar { display:flex; align-items:center; padding:20rpx 24rpx; background:#fff; border-bottom:1rpx solid #e2e8f0; }
.back { font-size:36rpx; color:#475569; padding-right:16rpx; } .top-title { flex:1; font-size:30rpx; font-weight:700; color:#1e293b; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.top-export { font-size:24rpx; padding:8rpx 18rpx; border-radius:12rpx; } .top-export.free { background:#dbeafe; color:#1e40af; } .top-export.locked { background:#fef3c7; color:#92400e; }
.meta-card { background:#fff; margin:20rpx 24rpx; border-radius:20rpx; padding:28rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.meta-grid { display:flex; flex-wrap:wrap; } .mg-item { width:50%; padding:12rpx 0; }
.mgl { font-size:24rpx; color:#94a3b8; display:block; } .mgv { font-size:26rpx; color:#1e293b; font-weight:500; }
.meta-score { text-align:center; margin-top:16rpx; padding-top:16rpx; border-top:1rpx solid #f1f5f9; }
.ms-num { font-size:64rpx; font-weight:900; } .ms-label { display:block; font-size:24rpx; color:#94a3b8; }
.ms-badge { display:inline-block; margin-top:6rpx; font-size:22rpx; padding:4rpx 14rpx; border-radius:10rpx; } .ms-badge.free { background:#dcfce7; color:#166534; } .ms-badge.locked { background:#fef3c7; color:#92400e; }
.disc { background:#fefce8; border:1rpx solid #fde68a; border-radius:14rpx; padding:20rpx; margin:20rpx 24rpx 0; font-size:24rpx; color:#92400e; }
.warn { background:#fef2f2; border:1rpx solid #fecaca; border-radius:14rpx; padding:20rpx; margin:16rpx 24rpx 0; font-size:26rpx; color:#dc2626; } .warn-bold { font-weight:700; }
.content-box { background:#fff; margin:20rpx 24rpx 0; border-radius:20rpx; padding:32rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); } .cb-title { font-size:28rpx; font-weight:700; color:#1e293b; display:block; margin-bottom:12rpx; } .cb-text { font-size:26rpx; color:#64748b; line-height:1.8; } .cb-hint { font-size:24rpx; color:#94a3b8; display:block; }
.section { background:#fff; margin:20rpx 24rpx 0; border-radius:20rpx; padding:28rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.sec-title { font-size:28rpx; font-weight:700; color:#1e293b; margin-bottom:16rpx; } .sec-title.green { color:#047857; } .sec-title.red { color:#b91c1c; } .sec-title.orange { color:#d97706; }
.sec-text { font-size:26rpx; color:#475569; line-height:1.7; }
.item { font-size:26rpx; color:#475569; line-height:1.9; padding-left:4rpx; }
.dim-grid { display:flex; flex-wrap:wrap; gap:16rpx; } .dim-cell { width:calc(50% - 8rpx); }
.dl { font-size:24rpx; color:#64748b; display:block; } .dv { font-size:32rpx; font-weight:700; display:block; margin:4rpx 0; }
.db { height:10rpx; background:#f1f5f9; border-radius:5rpx; } .df { height:100%; border-radius:5rpx; }
.comp-row { font-size:26rpx; color:#475569; }
.ql { font-size:24rpx; color:#64748b; display:block; padding:6rpx 0; }
.brands { display:flex; flex-wrap:wrap; gap:10rpx; } .brand { font-size:24rpx; padding:8rpx 16rpx; background:#f1f5f9; border-radius:12rpx; color:#334155; }
.loc-row { font-size:26rpx; color:#475569; }
.stats-grid { display:flex; flex-wrap:wrap; } .sg { width:33.3%; text-align:center; padding:12rpx 0; } .sg-label { font-size:22rpx; color:#64748b; display:block; } .sg-val { font-size:24rpx; font-weight:700; color:#1e293b; display:block; }
.item-sm { font-size:24rpx; color:#475569; padding:6rpx 0; } .more-hint { font-size:22rpx; color:#94a3b8; display:block; margin-top:4rpx; }
.bottom-bar { position:fixed; bottom:0; left:0; right:0; padding:20rpx 24rpx; background:#fff; border-top:1rpx solid #e2e8f0; display:flex; gap:14rpx; }
.bb-export { flex:1; background:#246bff; color:#fff; border-radius:14rpx; font-size:28rpx; padding:20rpx 0; font-weight:600; }
.bb-unlock { flex:1; background:#f59e0b; color:#fff; border-radius:14rpx; font-size:28rpx; padding:20rpx 0; font-weight:600; }
.bb-back { background:#f1f5f9; color:#475569; border-radius:14rpx; font-size:28rpx; padding:20rpx 32rpx; }
</style>
