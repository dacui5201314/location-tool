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
    <view class="report-shell" v-if="!loading && !errorMsg">
      <!-- Header -->
      <view class="header">
        <view class="header-nav">
          <text class="back" @tap="goBack">←</text>
          <text class="hd-pill">初筛参考</text>
        </view>
        <view class="hd-text">
          <text class="hd-brand">址得选</text>
          <text class="hd-title">商业选址初筛报告</text>
          <text class="hd-name">{{ recordTitle }}</text>
          <text class="hd-sub" v-if="record.address">{{ record.address }}</text>
        </view>
      </view>

      <!-- ── 评分卡 ── -->
      <view class="score-card" v-if="rptScore > 0">
        <view class="sc-left">
          <text class="score-title">综合评分</text>
          <view class="score-ring" :style="ringStyle">
            <view class="sr-inner">
              <text class="sr-num" :style="{ color: sc(scorePct) }">{{ scorePct }}</text>
              <text class="sr-unit">分</text>
            </view>
          </view>
        </view>
        <view class="sc-right">
          <text class="sc-verdict" :style="{ color: sc(scorePct) }">{{ scoreLevel }}</text>
          <text class="sc-caption">商业选址初筛参考</text>
          <text class="sc-addr">{{ record.address || '-' }}</text>
          <view class="sc-tags">
            <text class="sct" v-if="record.business_type">{{ record.business_type }}</text>
            <text class="sct" v-if="record.brand_desc && record.brand_desc !== record.business_type">{{ record.brand_desc }}</text>
            <text class="sct" v-if="record.store_size > 0">{{ record.store_size }}㎡</text>
          </view>
          <text class="sc-time">{{ fmtTime(record.created_at) || '' }}</text>
        </view>
      </view>

      <!-- ── 维度雷达 ── -->
      <view class="section radar-card" v-if="rptDims.length">
        <view class="radar-head">
          <view class="radar-title-row">
            <text class="radar-mark">📈</text>
            <text class="radar-main">维度雷达</text>
          </view>
          <text class="radar-sub">从客流、竞争、消费力等维度做初筛参考</text>
        </view>
        <view class="radar-bars">
          <view class="rb-row" v-for="d in radarDims" :key="d.key">
            <text class="rb-label">{{ d.label }}</text>
            <view class="rb-track">
              <view class="rb-fill" :style="{ width: d.value + '%', background: sc(d.value) }" />
            </view>
            <text class="rb-val" :style="{ color: sc(d.value) }">{{ d.value }}</text>
          </view>
        </view>
        <view class="dim-compact" v-if="extraDims.length">
          <view class="dc-chip" v-for="d in extraDims" :key="d.key" :style="{ borderColor: sc(d.value) }">
            <text class="dc-chip-label">{{ d.label || d.key }}</text>
            <text class="dc-chip-val" :style="{ color: sc(d.value) }">{{ d.value }}</text>
          </view>
        </view>
      </view>

      <!-- Old/empty report content -->
      <view class="content-box" v-if="!hasContent">
        <text class="cb-title">暂无完整报告内容</text>
        <text class="cb-text">该记录可能是旧版格式或报告数据尚未生成，元数据可正常查看。</text>
      </view>

      <!-- ── 免责声明 / 风险提示 ── -->
      <view class="disc" v-if="rptDisclaimer">{{ rptDisclaimer }}</view>
      <view class="warn" v-if="rptWarning"><text class="warn-bold">风险提示：</text>{{ rptWarning }}</view>

      <!-- ── 分析摘要 ── -->
      <view class="section" v-if="rptSummary">
        <view class="sec-title">🧭 分析摘要</view>
        <text class="sec-text">{{ rptSummary }}</text>
      </view>

      <!-- ── 优势 + 风险 ── -->
      <view class="section" v-if="rptAdv.length">
        <view class="sec-title sec-green">✓ 关键优势</view>
        <view class="adv-item" v-for="(a,i) in rptAdv" :key="'a'+i">
          <text class="adv-num">{{ i+1 }}</text><text class="adv-text">{{ a }}</text>
        </view>
      </view>
      <view class="section" v-if="rptDis.length">
        <view class="sec-title sec-red">⚠ 主要风险</view>
        <view class="adv-item" v-for="(d,i) in rptDis" :key="'d'+i">
          <text class="adv-num risk">{{ i+1 }}</text><text class="adv-text">{{ d }}</text>
        </view>
      </view>

      <!-- ── 竞争环境 ── -->
      <view class="section" v-if="hasCompetition || rptDirList.length">
        <view class="sec-title">🏪 竞争环境</view>
        <view class="comp-cols" v-if="hasCompetition">
          <view class="cc-item"><text class="cc-num" style="color:#dc2626">{{ rptDir200 }}</text><text class="cc-label">200m</text></view>
          <view class="cc-item"><text class="cc-num" style="color:#dc2626">{{ rptDir500 }}</text><text class="cc-label">500m</text></view>
          <view class="cc-item"><text class="cc-num" style="color:#dc2626">{{ rptDir1000 }}</text><text class="cc-label">1km</text></view>
        </view>
        <view class="comp-list" v-if="rptDirList.length">
          <text class="cl-item" v-for="(n,i) in rptDirList" :key="'d'+i">{{ n }}</text>
          <text class="more-hint" v-if="rptDirMore > 0">还有 {{ rptDirMore }} 条</text>
        </view>
        <view class="comp-sub" v-if="rptSub500 > 0 || rptSub1000 > 0">
          <text class="cs-label">替代消费压力：</text>
          <text>200m {{ rptSub200 }} · 500m {{ rptSub500 }} · 1km {{ rptSub1000 }}</text>
        </view>
        <view class="comp-sub" v-if="rptAnc500 > 0 || rptAnc1000 > 0">
          <text class="cs-label">客流锚点：</text>
          <text>200m {{ rptAnc200 }} · 500m {{ rptAnc500 }} · 1km {{ rptAnc1000 }}</text>
        </view>
      </view>

      <!-- ── 周边数据 ── -->
      <view class="section" v-if="hasStats">
        <view class="sec-title">📊 周边数据（200m / 500m / 1km）</view>
        <view class="stats-grid">
          <view class="sg" v-for="m in rptStats" :key="m.key" :class="m.highlight || ''">
            <text class="sg-icon">{{ statIcon(m.key) }}</text>
            <text class="sg-label">{{ m.label }}</text>
            <text class="sg-val" v-if="m.total !== undefined">{{ m.total }}</text>
            <text class="sg-val" v-else>{{ m.s200 === '' ? '-' : m.s200 }} / {{ m.s500 === '' ? '-' : m.s500 }} / {{ m.s1000 === '' ? '-' : m.s1000 }}</text>
          </view>
        </view>
      </view>

      <!-- ── 位置范围 ── -->
      <view class="section" v-if="rptCity || rptDistrict || rptTownship">
        <view class="sec-title">📍 位置范围</view>
        <view class="loc-row"><text>{{ [rptCity, rptDistrict, rptTownship].filter(Boolean).join(' · ') || '-' }}</text></view>
        <view class="loc-sub" v-if="rptBizAreas">商圈：{{ rptBizAreas }}</view>
        <view class="loc-sub" v-if="rptRoads">周边道路：{{ rptRoads }}</view>
      </view>

      <!-- ── 周边业态明细（核心 10 类默认展示，其余折叠）── -->
      <view class="section" v-if="rptPoiCats.length">
        <view class="sec-title">🧾 周边业态明细</view>
        <view class="poi-cat" v-for="cat in visiblePoiCats" :key="cat.key">
          <view class="poi-cat-head">
            <text class="poi-cat-label">{{ cat.label }}</text>
            <text class="poi-cat-count">{{ cat.total }}</text>
          </view>
          <text class="poi-cat-names">{{ cat.names.slice(0, 5).join(' · ') }}</text>
          <text class="more-hint" v-if="cat.names.length > 5">共 {{ cat.total }} 条，展示前 5 条</text>
        </view>
        <view class="poi-toggle" v-if="rptPoiCats.length > 10" @tap="poiExpanded = !poiExpanded">
          <text>{{ poiExpanded ? '收起' : '展开全部 ' + rptPoiCats.length + ' 类' }}</text>
        </view>
      </view>

      <!-- ── 各维度详细分析 ── -->
      <view class="section" v-if="rptDetailTexts.length">
        <view class="sec-title">🔎 各维度详细分析</view>
        <view class="dt-item" v-for="d in rptDetailTexts" :key="d.key">
          <view class="dt-head">
            <text class="dt-label">{{ d.label }}</text>
            <text class="dt-score" :style="{ color: sc(d.score) }" v-if="d.score > 0">{{ d.score }} 分</text>
          </view>
          <text class="dt-text">{{ d.text }}</text>
        </view>
      </view>

      <!-- ── 连锁品牌 ── -->
      <view class="section" v-if="rptBrands.length">
        <view class="sec-title">🏷️ 周边连锁品牌</view>
        <view class="brands">
          <text class="brand" v-for="b in rptBrands" :key="b.name">{{ b.name }} <text class="brand-count">×{{ b.count }}</text></text>
        </view>
      </view>

      <!-- ── 严谨度 / 数据质量 ── -->
      <view class="section" v-if="rptIrr > 0 || rptQual.length">
        <view class="sec-title">🛡️ 数据质量</view>
        <text class="ql" v-if="rptIrr > 0">严谨度规则剔除 {{ rptIrr }} 个无关 POI</text>
        <text class="ql" v-for="(q,i) in rptQual" :key="'q'+i">{{ q }}</text>
        <view class="item-sm" v-for="(n,i) in rptIrrList" :key="'irr'+i">{{ n }}</view>
      </view>

      <!-- ── 行动建议 ── -->
      <view class="section" v-if="rptAction.length">
        <view class="sec-title">行动建议</view>
        <view class="item" v-for="(ap,i) in rptAction" :key="'ap'+i">{{ i+1 }}. {{ ap }}</view>
      </view>

      <!-- Bottom bar -->
      <view class="bottom-bar">
        <button class="bb-back" @tap="goBack">返回</button>
      </view>

      <!-- Share CTA -->
      <view class="share-cta" v-if="isShared">
        <text class="share-cta-title">这份报告由「址得选」生成</text>
        <button class="share-cta-btn" @tap="goToHome">{{ shareConfig.share_cta_text || '我也要生成选址报告' }}</button>
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
      loading: true, errorMsg: '', record: {}, isShared: false, shareConfig: {},
      poiExpanded: false,
      rptScore: 0, rptDisclaimer: '', rptWarning: '', rptSummary: '',
      rptAdv: [], rptDis: [], rptDims: [], rptAction: [],
      rptDir200: 0, rptDir500: 0, rptDir1000: 0,
      rptSub200: 0, rptSub500: 0, rptSub1000: 0,
      rptAnc200: 0, rptAnc500: 0, rptAnc1000: 0,
      rptIrr: 0, rptBrands: [],
      rptQual: [],
      rptCity: '', rptDistrict: '', rptTownship: '',
      rptBizAreas: '', rptRoads: '',
      rptStats: [],
      rptDetailTexts: [],
      rptPoiCats: [],
      rptDirList: [], rptSubList: [], rptAncList: [],
      rptIrrList: [],
      rptDirMore: 0, rptSubMore: 0, rptAncMore: 0
    }
  },
  computed: {
    recordTitle () { return this.record.brand_desc || this.record.business_type || '报告详情' },
    hasCompetition () { return this.rptDir200 + this.rptDir500 + this.rptDir1000 > 0 },
    hasContent () { return this.rptScore > 0 || this.rptSummary || this.rptAdv.length || this.rptDims.length || this.rptQual.length || this.rptBrands.length || this.rptIrr > 0 || this.rptCity || this.hasStats || this.rptDirList.length || this.rptDetailTexts.length || this.rptPoiCats.length },
    hasStats () { return this.rptStats.length > 0 },
    visiblePoiCats () { return this.poiExpanded ? this.rptPoiCats : this.rptPoiCats.slice(0, 10) },
    scorePct () {
      const v = Number(this.rptScore)
      return (isNaN(v) || v < 0) ? 0 : Math.min(100, Math.round(v))
    },
    scoreLevel () {
      const p = this.scorePct
      if (p >= 60) return '优秀'
      if (p >= 40) return '可考虑'
      return '谨慎'
    },
    radarDims () {
      const order = ['population_density','traffic_accessibility','traffic_flow','consumer_profile','competition','complementary_businesses','category_advantage','cost_estimate']
      const labelMap = { population_density:'人口密集度',traffic_accessibility:'交通可达性',traffic_flow:'客流特征',consumer_profile:'消费人群',competition:'竞争环境',complementary_businesses:'互补业态',category_advantage:'品类优势',cost_estimate:'成本预估' }
      return order.map(key => {
        const d = this.rptDims.find(x => x.key === key)
        return { key, label: labelMap[key] || key, value: d ? d.value : 0 }
      })
    },
    extraDims () {
      const radarKeys = ['population_density','traffic_accessibility','traffic_flow','consumer_profile','competition','complementary_businesses','category_advantage','cost_estimate']
      return this.rptDims.filter(d => !radarKeys.includes(d.key))
    },
    ringStyle () {
      const deg = this.scorePct * 3.6
      const color = this.sc(this.scorePct)
      return { background: `conic-gradient(${color} 0deg ${deg}deg, #e2e8f0 ${deg}deg 360deg)` }
    }
  },
  onLoad (options) {
    // 加载分享配置
    api.fetchShareConfig().then(c => { if (c.ok && c.data) this.shareConfig = c.data }).catch(() => {})
    const shareToken = options.share
    const recordId = options.id
    this.isShared = !!shareToken

    if (shareToken) {
      // 分享入口：通过 share_token 读取
      api.fetchSharedReport(shareToken).then(r => {
        this.loading = false
        if (r.ok && r.data && !r.data.error) {
          this.record = r.data
          this.parseReport(r.data.report_json)
        } else {
          this.errorMsg = '报告不存在或已失效'
        }
      }).catch(() => { this.loading = false; this.errorMsg = '网络异常，请重试' })
      return
    }

    if (!recordId) { this.loading = false; this.errorMsg = '缺少记录 ID'; return }
    api.fetchRecordDetail(recordId).then(r => {
      this.loading = false
      if (r.ok && r.data && !r.data.error) {
        this.record = r.data
        this.parseReport(r.data.report_json)
        // ★ 预生成 share_token，确保分享时可用
        this._prefetchShareToken(r.data.report_uuid)
      } else {
        const detail = r.data?.detail || r.data?.error || ''
        if (r.statusCode === 404 || detail.includes('not found') || detail.includes('不存在')) this.errorMsg = '记录不存在'
        else if (r.statusCode === 401) this.errorMsg = '请先登录后查看'
        else this.errorMsg = detail || '记录加载失败'
      }
    }).catch(() => { this.loading = false; this.errorMsg = '网络异常，请重试' })
  },
  onShareAppMessage () {
    // ★ 同步返回，不依赖 Promise。token 已在 _prefetchShareToken 中预生成
    const cfg = this.shareConfig || {}
    const addr = this.record.address || this.record.brand_desc || '门店'
    const titleTpl = cfg.report_share_title_template || '{address}选址分析报告'
    const title = titleTpl.replace('{address}', addr)
    const imageUrl = cfg.share_image_url || ''
    const token = this._shareToken || ''
    if (token) {
      return { title, path: `/pages/report-detail/index?share=${token}`, ...(imageUrl ? { imageUrl } : {}) }
    }
    // token 未就绪 → 分享首页，不返回 Promise。下次从报告页分享时 token 已准备好
    return { title, path: '/pages/home/index' }
  },
  methods: {
    sc: scoreColor, fmtTime: formatTime,
    statIcon (key) {
      const map = {
        residential: '🏘️',
        office: '🏢',
        restaurants: '🍜',
        cafe_tea: '☕',
        shopping: '🛍️',
        schools: '🎓',
        hospitals: '🏥',
        subway: '🚇',
        bus: '🚌',
        hotels: '🏨',
        banks: '🏦',
        parking: '🅿️'
      }
      return map[key] || '•'
    },
    goBack () { uni.navigateBack({ delta: 1 }).catch(() => uni.reLaunch({ url: '/pages/home/index?tab=records' })) },
    goToHome () { uni.reLaunch({ url: '/pages/home/index' }) },
    _prefetchShareToken (uuid) {
      if (!uuid || this._shareToken) return
      api.createShareToken(uuid).then(r => {
        if (r.ok && r.data && r.data.share_token) {
          this._shareToken = r.data.share_token
        }
      }).catch(() => {})
    },
    parseReport (raw) {
      ['rptScore','rptDisclaimer','rptWarning','rptSummary','rptAdv','rptDis','rptDims','rptAction',
       'rptDir200','rptDir500','rptDir1000','rptSub200','rptSub500','rptSub1000',
       'rptAnc200','rptAnc500','rptAnc1000','rptIrr','rptBrands','rptQual',
       'rptCity','rptDistrict','rptTownship','rptBizAreas','rptRoads',
       'rptStats','rptDirList','rptSubList','rptAncList','rptIrrList',
       'rptDirMore','rptSubMore','rptAncMore','rptDetailTexts','rptPoiCats'
      ].forEach(k => { this[k] = Array.isArray(this[k]) ? [] : (typeof this[k] === 'number' ? 0 : '') })
      this.poiExpanded = false

      let rpt = null
      if (typeof raw === 'string') { try { rpt = JSON.parse(raw) } catch (e) { return } } else if (raw && typeof raw === 'object') { rpt = raw } else { return }

      const rd = rpt.real_data || {}
      const exec = rpt.executive_summary || {}
      const dimScores = Array.isArray(rpt.dimension_scores) ? rpt.dimension_scores : []

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

      this.rptDims = dimScores.map(d => {
        let v = d.score ?? d.value ?? 0
        if (typeof v === 'string') { const p = parseFloat(v); v = isNaN(p) ? 0 : p }
        if (typeof v !== 'number' || isNaN(v)) v = 0
        v = Math.max(0, Math.min(100, Math.round(v)))
        return { key: d.key || d.name || '', label: d.label || d.title || d.key || '', value: v }
      })

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
      const hb = rd.hot_brands || rd.brands || rd.chain_brands || rd.brand_list
      this.rptBrands = Array.isArray(hb) ? hb.map(b => {
        if (typeof b === 'string') return { name: b, count: 1 }
        return { name: b.name || b.title || b.brand_name || '', count: b.count ?? 1 }
      }).filter(b => b.name) : []

      const irrList = rd.irrelevant_excluded_list || rd.irrelevant_list || rd.excluded_pois || rd.irrelevant_pois
      if (Array.isArray(irrList) && irrList.length) {
        this.rptIrrList = irrList.map(d => d.name || d.title || d.poi_name || '').filter(Boolean).slice(0, 5)
      }

      this.rptCity = rd.city || rpt.city || ''
      this.rptDistrict = rd.district || rpt.district || ''
      this.rptTownship = rd.township || rpt.township || ''
      this.rptBizAreas = Array.isArray(rd.business_areas) ? rd.business_areas.join('、') : (rd.business_areas || '')
      this.rptRoads = Array.isArray(rd.nearby_roads) ? rd.nearby_roads.join('、') : (rd.nearby_roads || '')

      // stats
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
      const poiCounts = rd.poi_counts || {}
      const _highlight = (key) => {
        const v1k = parseInt(_val(s10, metricAliases[key])) || 0
        const pc = parseInt(poiCounts[key]) || 0
        if (key === 'restaurants' && v1k > 100) return 'high'
        if (key === 'schools' && pc > 5) return 'good'
        if (key === 'hospitals' && pc > 10) return 'good'
        if (key === 'hospitals' && pc <= 10) return 'info'
        if (key === 'subway' && pc === 0) return 'high'
        if (key === 'subway' && pc > 0) return 'good'
        if (key === 'bus' && pc > 10) return 'good'
        if (key === 'residential' || key === 'office') return 'info'
        return ''
      }
      const tripleKeys = ['residential','office','restaurants','cafe_tea','shopping','schools','hospitals','subway','bus','hotels']
      const singleKeys = ['banks','parking']
      const tripleStats = tripleKeys.map(key => {
        const s200 = _val(s2, metricAliases[key]); const s500 = _val(s5, metricAliases[key]); const s1000 = _val(s10, metricAliases[key])
        if (s200 === '' && s500 === '' && s1000 === '') return null
        return { key, label: metricLabels[key], s200, s500, s1000, highlight: _highlight(key) }
      }).filter(Boolean)
      const singleStats = singleKeys.map(key => {
        const total = parseInt(poiCounts[key]) || 0
        if (total === 0) return null
        return { key, label: metricLabels[key], total, highlight: '' }
      }).filter(Boolean)
      this.rptStats = [...tripleStats, ...singleStats]

      // competitor lists
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

      // dimension detail texts
      const detailLabels = {
        population_density: { label: '人口密集度', hasScore: true },
        traffic_accessibility: { label: '交通可达性', hasScore: true },
        traffic_flow: { label: '客流特征', hasScore: true },
        consumer_profile: { label: '消费人群', hasScore: true },
        competition: { label: '竞争环境', hasScore: true },
        complementary_businesses: { label: '互补业态', hasScore: true },
        category_advantage: { label: '品类优势', hasScore: true },
        cost_estimate: { label: '成本估算', hasScore: true },
        revenue_estimation: { label: '营收预估', hasScore: false },
        site_suggestion: { label: '选址建议', hasScore: false }
      }
      const dimScoreMap = {}
      dimScores.forEach(d => { if (d.key) dimScoreMap[d.key] = d.score ?? d.value ?? 0 })
      const details = rpt.details || {}
      const _stripScore = (t) => {
        if (typeof t !== 'string') return t
        return t.replace(/(?:评分|得分)[：:]\s*\d+\s*分?/g, '').replace(/\d+\s*分/g, '').trim()
      }
      this.rptDetailTexts = Object.keys(detailLabels).map(key => {
        const raw = details[key]
        if (!raw) return null
        const cfg = detailLabels[key]
        let rawText = ''
        if (typeof raw === 'string') rawText = raw
        else if (typeof raw === 'object' && raw !== null) rawText = raw.text || raw.description || raw.content || raw.message || ''
        if (!rawText) return null
        const text = _stripScore(rawText)
        let score = 0
        if (cfg.hasScore) {
          if (dimScoreMap[key] !== undefined) score = parseFloat(dimScoreMap[key]) || 0
          else {
            const m = rawText.match(/(?:评分|得分)[：:]\s*(\d+)/) || rawText.match(/(\d+)\s*分/)
            if (m) score = parseInt(m[1]) || 0
          }
        }
        return { key, label: cfg.label, text, score: cfg.hasScore ? Math.max(0, Math.min(100, Math.round(score))) : 0 }
      }).filter(Boolean)

      // POI category lists
      const poiCats = [
        { key: 'residential', label: '住宅小区' },
        { key: 'office', label: '写字楼' },
        { key: 'schools', label: '学校' },
        { key: 'hospitals', label: '医院/诊所' },
        { key: 'shopping', label: '购物商场' },
        { key: 'restaurants', label: '餐饮门店' },
        { key: 'cafe_tea', label: '咖啡茶饮' },
        { key: 'fast_food', label: '快餐' },
        { key: 'chinese_restaurants', label: '中餐' },
        { key: 'foreign_restaurants', label: '异国料理' },
        { key: 'hotels', label: '酒店' },
        { key: 'subway', label: '地铁站' },
        { key: 'bus', label: '公交站' },
        { key: 'parking', label: '停车场' },
        { key: 'banks', label: '银行' },
        { key: 'convenience', label: '便利店' },
        { key: 'pharmacy', label: '药店' },
        { key: 'beauty', label: '美容美发' },
        { key: 'pets', label: '宠物' },
        { key: 'bars', label: '酒吧' }
      ]
      const poiLists = rd.poi_lists || {}
      this.rptPoiCats = poiCats.map(cat => {
        const items = poiLists[cat.key]
        if (!Array.isArray(items) || !items.length) return null
        const names = items.slice(0, 8).map(d => {
          const name = d.name || d.title || d.poi_name || ''
          if (!name) return null
          const dist = d.distance ?? d.dist
          if (dist !== undefined && dist !== null && dist !== '') return `${name}（${dist}m）`
          return name
        }).filter(Boolean)
        if (!names.length) return null
        return { ...cat, names, total: items.length }
      }).filter(Boolean)
    }
  }
}
</script>

<style scoped>
.detail-page { min-height:100vh; background:#e9edf5; padding-bottom:128rpx; padding-bottom:calc(128rpx + env(safe-area-inset-bottom)); }
.report-shell { padding-bottom:24rpx; }
.loading { text-align:center; padding:120rpx 0; }
.ld-dots { font-size:60rpx; letter-spacing:12rpx; color:#94a3b8; }
.ld-text { display:block; font-size:26rpx; color:#94a3b8; margin-top:16rpx; }
.error { text-align:center; padding:120rpx 32rpx; }
.err-icon { font-size:80rpx; display:block; }
.err-text { font-size:28rpx; color:#64748b; display:block; margin:16rpx 0; }
.err-btn { margin-top:20rpx; background:#f1f5f9; color:#475569; border-radius:16rpx; padding:16rpx 40rpx; font-size:28rpx; }
.err-btn::after, .bb-back::after, .share-cta-btn::after { border:none; }

.header { margin:0 0 20rpx; padding:34rpx 28rpx 38rpx; background:linear-gradient(180deg,#0b3fbd 0%,#1236a3 58%,#172554 100%); position:relative; overflow:hidden; }
.header::before { content:''; position:absolute; left:26rpx; right:26rpx; bottom:-72rpx; height:120rpx; border-radius:24rpx; background:rgba(255,255,255,0.08); transform:skewY(-4deg); }
.header-nav { position:relative; z-index:1; display:flex; align-items:center; justify-content:space-between; margin-bottom:34rpx; }
.back { width:64rpx; height:64rpx; border-radius:16rpx; background:rgba(255,255,255,0.14); color:#fff; font-size:40rpx; font-weight:800; line-height:60rpx; text-align:center; display:block; }
.hd-pill { height:48rpx; line-height:48rpx; padding:0 20rpx; border-radius:999rpx; background:rgba(255,255,255,0.14); border:1rpx solid rgba(255,255,255,0.26); color:#eaf0ff; font-size:22rpx; font-weight:700; }
.hd-text { position:relative; z-index:1; }
.hd-brand { display:block; font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; }
.hd-title { display:block; font-size:42rpx; font-weight:900; color:#fff; margin-top:8rpx; line-height:1.18; }
.hd-name { display:block; font-size:28rpx; font-weight:800; color:#f7d77b; margin-top:16rpx; line-height:1.35; word-break:break-all; }
.hd-sub { display:block; font-size:24rpx; color:rgba(232,240,255,0.82); margin-top:8rpx; line-height:1.55; word-break:break-all; }

.score-card { background:#fff; margin:0 24rpx 20rpx; border-radius:16rpx; padding:30rpx; box-shadow:0 18rpx 42rpx rgba(36,70,128,0.10); border:1rpx solid rgba(213,224,246,0.95); display:flex; align-items:center; }
.sc-left { flex-shrink:0; width:154rpx; margin-right:30rpx; display:flex; flex-direction:column; align-items:center; }
.sc-right { flex:1; min-width:0; }
.score-title { display:block; width:150rpx; height:34rpx; line-height:34rpx; margin:0 0 12rpx; color:#17244e; font-size:24rpx; font-weight:900; text-align:center; }
.score-ring { width:150rpx; height:150rpx; border-radius:50%; display:flex; align-items:center; justify-content:center; }
.sr-inner { width:112rpx; height:112rpx; border-radius:50%; background:#fff; display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:inset 0 0 0 1rpx #edf2f7; }
.sr-num { font-size:42rpx; font-weight:900; line-height:1.02; }
.sr-unit { font-size:18rpx; font-weight:700; color:#8b99b6; line-height:1; margin-top:3rpx; }
.sc-verdict { font-size:30rpx; font-weight:900; display:block; line-height:1.2; }
.sc-caption { font-size:22rpx; color:#8b99b6; display:block; margin:2rpx 0 12rpx; }
.sc-addr { font-size:24rpx; color:#4b5872; display:block; margin-bottom:14rpx; line-height:1.55; word-break:break-all; }
.sc-tags { display:flex; flex-wrap:wrap; gap:8rpx; margin-bottom:10rpx; }
.sct { font-size:21rpx; font-weight:700; background:#f3f7ff; color:#315bff; border:1rpx solid rgba(49,91,255,0.14); border-radius:999rpx; padding:6rpx 14rpx; }
.sc-time { font-size:21rpx; color:#9aa6bd; }

.section, .content-box { background:rgba(255,255,255,0.96); margin:18rpx 24rpx 0; border-radius:16rpx; padding:28rpx; box-shadow:0 12rpx 30rpx rgba(61,88,135,0.07); border:1rpx solid rgba(213,224,246,0.86); }
.sec-title { font-size:28rpx; font-weight:900; color:#17244e; margin-bottom:18rpx; line-height:1.25; }
.sec-title::before { content:''; display:inline-block; width:8rpx; height:24rpx; border-radius:6rpx; background:#315bff; margin-right:12rpx; vertical-align:-3rpx; }
.sec-green { color:#047857; }
.sec-green::before { background:#16a34a; }
.sec-red { color:#b91c1c; }
.sec-red::before { background:#ef4444; }
.sec-text, .item, .dt-text, .ql, .cb-text { font-size:26rpx; color:#4b5872; line-height:1.75; word-break:break-all; }
.item { padding:8rpx 0; }
.item-sm { font-size:24rpx; color:#64748b; padding:6rpx 0; line-height:1.55; word-break:break-all; }
.more-hint { font-size:22rpx; color:#8b99b6; display:block; margin-top:8rpx; line-height:1.5; }

.disc { background:#fff9e6; border:1rpx solid #f3d38a; border-radius:16rpx; padding:22rpx 24rpx; margin:18rpx 24rpx 0; font-size:24rpx; line-height:1.65; color:#8a5a12; box-shadow:0 10rpx 24rpx rgba(141,96,18,0.05); }
.warn { background:#fff1f2; border:1rpx solid #fecdd3; border-radius:16rpx; padding:22rpx 24rpx; margin:18rpx 24rpx 0; font-size:24rpx; line-height:1.65; color:#be123c; }
.warn-bold { font-weight:900; }
.cb-title { font-size:30rpx; font-weight:900; color:#17244e; display:block; margin-bottom:10rpx; }

.adv-item { display:flex; padding:18rpx 0; border-bottom:1rpx solid #edf2f7; }
.adv-item:last-child { border-bottom:0; padding-bottom:2rpx; }
.adv-num { width:44rpx; height:44rpx; border-radius:14rpx; background:#dcfce7; color:#047857; font-size:22rpx; font-weight:900; line-height:44rpx; text-align:center; flex-shrink:0; margin-right:16rpx; }
.adv-num.risk { background:#fff1f2; color:#be123c; }
.adv-text { font-size:25rpx; color:#344256; line-height:1.7; flex:1; word-break:break-all; }

.radar-card { background:linear-gradient(180deg,#ffffff,#f8fbff); }
.radar-head { margin-bottom:12rpx; }
.radar-title-row { display:flex; align-items:center; margin-bottom:8rpx; }
.radar-mark { width:42rpx; height:42rpx; line-height:42rpx; border-radius:12rpx; background:#eef4ff; text-align:center; font-size:24rpx; margin-right:12rpx; }
.radar-main { color:#17244e; font-size:30rpx; font-weight:900; line-height:1.25; }
.radar-sub { display:block; padding-left:54rpx; font-size:23rpx; color:#8b99b6; line-height:1.5; }
.radar-bars { padding:8rpx 0 2rpx; }
.rb-row { display:flex; align-items:center; padding:14rpx 0; }
.rb-label { width:158rpx; font-size:24rpx; color:#4b5872; flex-shrink:0; line-height:1.3; }
.rb-track { flex:1; height:16rpx; background:#e5ebf4; border-radius:10rpx; overflow:hidden; margin:0 16rpx; box-shadow:inset 0 1rpx 2rpx rgba(23,36,78,0.05); }
.rb-fill { height:100%; border-radius:10rpx; min-width:4rpx; transition:width 0.3s; }
.rb-val { width:52rpx; font-size:24rpx; font-weight:900; text-align:right; flex-shrink:0; }
.dim-compact { display:flex; flex-wrap:wrap; gap:10rpx; margin-top:20rpx; padding-top:18rpx; border-top:1rpx solid #edf2f7; }
.dc-chip { display:flex; align-items:center; padding:9rpx 14rpx; border-radius:14rpx; border:2rpx solid #e2e8f0; background:#f8fafc; }
.dc-chip-label { font-size:22rpx; color:#4b5872; margin-right:8rpx; }
.dc-chip-val { font-size:24rpx; font-weight:900; }

.comp-cols { display:flex; gap:14rpx; margin-bottom:18rpx; }
.cc-item { flex:1; text-align:center; padding:18rpx 8rpx; background:#f8fafc; border-radius:16rpx; border:1rpx solid #edf2f7; }
.cc-num { display:block; font-size:38rpx; font-weight:900; line-height:1.05; }
.cc-label { font-size:22rpx; color:#8b99b6; margin-top:6rpx; display:block; }
.comp-list { display:flex; flex-wrap:wrap; gap:10rpx; margin-top:12rpx; }
.cl-item { font-size:23rpx; color:#4b5872; background:#f3f7ff; padding:8rpx 14rpx; border-radius:999rpx; border:1rpx solid rgba(49,91,255,0.12); max-width:100%; word-break:break-all; }
.comp-sub { margin-top:16rpx; padding-top:16rpx; border-top:1rpx solid #edf2f7; font-size:24rpx; color:#64748b; line-height:1.6; }
.cs-label { font-weight:900; color:#344256; }

.stats-grid { display:flex; flex-wrap:wrap; gap:12rpx; }
.sg { width:calc(33.333% - 8rpx); min-height:142rpx; text-align:center; padding:16rpx 8rpx 18rpx; box-sizing:border-box; border-radius:18rpx; background:linear-gradient(180deg,#fbfdff,#f4f7fc); border:1rpx solid #dde7f3; box-shadow:0 8rpx 18rpx rgba(40,76,130,0.05); display:flex; flex-direction:column; align-items:center; justify-content:center; }
.sg-icon { width:46rpx; height:46rpx; line-height:46rpx; border-radius:14rpx; background:#fff; box-shadow:0 6rpx 16rpx rgba(40,76,130,0.07); font-size:26rpx; display:block; margin-bottom:8rpx; }
.sg-label { font-size:22rpx; color:#7a879e; display:block; line-height:1.35; }
.sg-val { font-size:27rpx; font-weight:900; color:#17244e; display:block; margin-top:8rpx; line-height:1.22; word-break:break-all; }
.sg.high .sg-val { color:#dc2626; }
.sg.good .sg-val { color:#16a34a; }
.sg.info .sg-val { color:#2563eb; }
.sg.high { background:linear-gradient(180deg,#fffafa,#fff1f2); border-color:#fecdd3; }
.sg.good { background:linear-gradient(180deg,#fbfffd,#ecfdf5); border-color:#bbf7d0; }
.sg.info { background:linear-gradient(180deg,#fbfdff,#eff6ff); border-color:#bfdbfe; }

.loc-row { font-size:26rpx; color:#344256; line-height:1.65; word-break:break-all; }
.loc-sub { font-size:24rpx; color:#64748b; margin-top:10rpx; line-height:1.6; word-break:break-all; }
.poi-cat { padding:18rpx 0; border-bottom:1rpx solid #edf2f7; }
.poi-cat:last-child { border-bottom:0; padding-bottom:2rpx; }
.poi-cat-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8rpx; gap:16rpx; }
.poi-cat-label { font-size:25rpx; font-weight:900; color:#17244e; flex:1; }
.poi-cat-count { font-size:22rpx; color:#315bff; background:#eef4ff; padding:4rpx 14rpx; border-radius:999rpx; font-weight:900; }
.poi-cat-names { font-size:23rpx; color:#64748b; line-height:1.65; display:block; word-break:break-all; }
.poi-toggle { text-align:center; padding:18rpx 0 2rpx; font-size:25rpx; font-weight:900; color:#315bff; }

.dt-item { padding:20rpx 0; border-bottom:1rpx solid #edf2f7; }
.dt-item:last-child { border-bottom:0; padding-bottom:2rpx; }
.dt-head { display:flex; align-items:center; margin-bottom:10rpx; gap:16rpx; }
.dt-label { font-size:26rpx; font-weight:900; color:#17244e; flex:1; line-height:1.35; }
.dt-score { font-size:24rpx; font-weight:900; flex-shrink:0; }
.brands { display:flex; flex-wrap:wrap; gap:10rpx; }
.brand { font-size:24rpx; padding:9rpx 16rpx; background:#f3f7ff; border-radius:999rpx; color:#344256; border:1rpx solid rgba(49,91,255,0.12); max-width:100%; word-break:break-all; }
.brand-count { color:#8b99b6; }
.ql { display:block; padding:6rpx 0; }

.bottom-bar { margin-top:26rpx; padding:18rpx 24rpx; display:flex; }
.bb-back { flex:1; background:#172554; color:#fff; border-radius:16rpx; font-size:28rpx; font-weight:900; padding:20rpx 0; box-shadow:0 12rpx 26rpx rgba(23,37,84,0.16); }
.share-cta { margin:28rpx 24rpx 40rpx; background:linear-gradient(135deg,#172554,#0b3fbd); border-radius:16rpx; padding:32rpx 24rpx; text-align:center; box-shadow:0 18rpx 38rpx rgba(21,31,143,0.18); }
.share-cta-title { display:block; color:rgba(255,255,255,0.88); font-size:26rpx; margin-bottom:20rpx; }
.share-cta-btn { width:100%; background:#fff; color:#0b3fbd; border-radius:16rpx; font-size:30rpx; font-weight:900; padding:20rpx 0; }
</style>
