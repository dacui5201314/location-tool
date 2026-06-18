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

      <!-- ── 评分卡：移动端先给用户结论锚点 ── -->
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
          <text class="sc-time">{{ rptGeneratedAt || fmtTime(record.created_at) || '' }}</text>
        </view>
      </view>

      <!-- P0-A: fallback 标识（分享页也展示，但文案使用用户可理解表述） -->
      <view class="fb-badge" v-if="rptFallbackNote">
        <text class="fb-badge-icon">📋</text>
        <text class="fb-badge-text">保守版数据摘要 — 基于地图数据生成，深度分析未展开。建议结合现场核验。</text>
      </view>

      <!-- P0-B: 决策卡片（优先展示，缺字段时降级到评分卡） -->
      <view class="decision-card" v-if="rptDecisionSnapshot">
        <view class="dc-verdict-row">
          <text class="dc-verdict" :class="verdictClass">{{ rptDecisionSnapshot.verdict || '待核验' }}</text>
          <text class="dc-score" v-if="rptScore > 0">{{ scorePct }} 分</text>
        </view>
        <text class="dc-one-sentence">{{ rptDecisionSnapshot.one_sentence || '' }}</text>
        <view class="dc-pills">
          <view class="dc-pill strength" v-if="rptDecisionSnapshot.top_strength">
            <text class="dc-pill-label">最大优势</text>
            <text class="dc-pill-text">{{ rptDecisionSnapshot.top_strength }}</text>
          </view>
          <view class="dc-pill risk" v-if="rptDecisionSnapshot.top_risk">
            <text class="dc-pill-label">最大风险</text>
            <text class="dc-pill-text">{{ rptDecisionSnapshot.top_risk }}</text>
          </view>
        </view>
        <view class="dc-next" v-if="rptDecisionSnapshot.next_action">
          <text class="dc-next-label">下一步：</text>
          <text class="dc-next-text">{{ rptDecisionSnapshot.next_action }}</text>
        </view>
        <view class="dc-cond fit" v-if="rptDecisionSnapshot.fit_condition">
          <text class="dc-cond-label">成立条件：</text>
          <text class="dc-cond-text">{{ rptDecisionSnapshot.fit_condition }}</text>
        </view>
        <view class="dc-cond stop" v-if="rptDecisionSnapshot.stop_condition">
          <text class="dc-cond-label">降级条件：</text>
          <text class="dc-cond-text">{{ rptDecisionSnapshot.stop_condition }}</text>
        </view>
      </view>

      <view class="read-path" v-if="hasContent">
        <view class="rp-step">
          <text class="rp-index">1</text>
          <text class="rp-title">先看结论</text>
          <text class="rp-desc">评分与一句话判断</text>
        </view>
        <view class="rp-step">
          <text class="rp-index">2</text>
          <text class="rp-title">再看依据</text>
          <text class="rp-desc">地点与周边数据</text>
        </view>
        <view class="rp-step">
          <text class="rp-index">3</text>
          <text class="rp-title">识别风险</text>
          <text class="rp-desc">优势、风险与条件</text>
        </view>
        <view class="rp-step">
          <text class="rp-index">4</text>
          <text class="rp-title">现场核验</text>
          <text class="rp-desc">任务清单与边界</text>
        </view>
      </view>

      <!-- P0-B: 数据充分度标签 -->
      <!-- P1: 地点基本面 -->
      <view class="section" v-if="rptLocationFundamentals">
        <view class="sec-title">📍 地点基本面</view>
        <view class="loc-fund-box">
          <text class="loc-fund-type">{{ rptLocationFundamentals.label || rptLocationFundamentals.type || '' }}</text>
          <text class="loc-fund-summary">{{ rptLocationFundamentals.summary || '' }}</text>
        </view>
        <view class="split-mini" v-if="(rptLocationFundamentals.strengths && rptLocationFundamentals.strengths.length) || (rptLocationFundamentals.risks && rptLocationFundamentals.risks.length)">
          <view class="sm-item good" v-if="rptLocationFundamentals.strengths && rptLocationFundamentals.strengths.length">
            <text class="sm-title sm-green">位置优势</text>
            <text class="sm-text" v-for="(s,i) in rptLocationFundamentals.strengths" :key="'ls'+i">✓ {{ s }}</text>
          </view>
          <view class="sm-item bad" v-if="rptLocationFundamentals.risks && rptLocationFundamentals.risks.length">
            <text class="sm-title sm-red">位置风险</text>
            <text class="sm-text" v-for="(r,i) in rptLocationFundamentals.risks" :key="'lr'+i">⚠ {{ r }}</text>
          </view>
        </view>
      </view>

      <view class="ds-tag" v-if="rptDataSufficiency" :class="'ds-' + rptDataSufficiency.level">
        <text class="ds-icon">{{ suffIcon }}</text>
        <text class="ds-label">{{ rptDataSufficiency.label }}</text>
        <text class="ds-summary" v-if="rptDataSufficiency.summary">{{ rptDataSufficiency.summary }}</text>
      </view>

      <!-- ── 维度雷达 ── -->
      <view class="section radar-card" v-if="rptDims.length">
        <view class="radar-head">
          <view class="radar-title-row">
            <text class="radar-mark">📈</text>
            <text class="radar-main">关键维度评分</text>
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
      <view class="section" v-if="rptDemandContradiction">
        <view class="sec-title" style="color:#92400e">🔍 客源来源待核验</view>
        <view class="contradiction-note" style="background:#fffbeb;padding:10px 14px;border-radius:8px;border:1px solid #fde68a;color:#92400e;font-size:14px;line-height:1.8">{{ rptDemandContradiction }}</view>
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
          <text class="comp-chip" v-for="(n,i) in rptDirList" :key="'d'+i">{{ n }}</text>
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

      <!-- P0.5-final: 营收模型免责（优先使用后端 revenue_disclaimer） -->
      <view class="section disc-section" v-if="rptDetailTexts.length">
        <view class="sec-title">📌 营收测算说明</view>
        <text class="sec-text">{{ rptRevenueDisclaimer || '以上为模型估算，不代表实际经营结果；需结合现场客流、租金和实际经营条件复核。' }}</text>
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
        <text class="ql" v-if="rptIrr > 0">严谨度规则剔除 {{ rptIrr }} 个无关点位</text>
        <text class="ql" v-for="(q,i) in rptQual" :key="'q'+i">{{ q }}</text>
        <view class="item-sm" v-for="(n,i) in rptIrrList" :key="'irr'+i">{{ n }}</view>
      </view>

      <!-- P1: 生意模型快照 -->
      <view class="section" v-if="rptBusinessModelSnapshot">
        <view class="sec-title">🏪 行业生意模型：{{ record.business_type || '选址' }}</view>
        <view class="biz-snap-box">
          <text class="biz-snap-core" v-if="rptBusinessModelSnapshot.core_logic">{{ rptBusinessModelSnapshot.core_logic }}</text>
          <text class="biz-snap-comp" v-if="rptBusinessModelSnapshot.competitor_note">{{ rptBusinessModelSnapshot.competitor_note }}</text>
        </view>
        <view class="biz-must-verify" v-if="rptBusinessModelSnapshot.must_verify && rptBusinessModelSnapshot.must_verify.length">
          <text class="bmv-title">📋 必核验项</text>
          <view class="bmv-item" v-for="(v,i) in rptBusinessModelSnapshot.must_verify" :key="'bmv'+i">
            <text class="bmv-num">{{ i+1 }}</text>
            <text class="bmv-text">{{ v }}</text>
          </view>
        </view>
        <view class="biz-cond fit" v-if="rptBusinessModelSnapshot.fit_condition">
          <text class="biz-cond-label">成立条件：</text>
          <text class="biz-cond-text">{{ rptBusinessModelSnapshot.fit_condition }}</text>
        </view>
        <view class="biz-cond stop" v-if="rptBusinessModelSnapshot.stop_condition">
          <text class="biz-cond-label">降级条件：</text>
          <text class="biz-cond-text">{{ rptBusinessModelSnapshot.stop_condition }}</text>
        </view>
      </view>

      <!-- ── 经营建议（仅当没有 field_checklist 或两者都有时展示）── -->
      <view class="section" v-if="rptAction.length">
        <view class="sec-title">💡 经营建议</view>
        <view class="item" v-for="(ap,i) in rptAction" :key="'ap'+i">{{ i+1 }}. {{ ap }}</view>
      </view>

      <!-- P0-B: 现场核验清单（优先新旧兼容） -->
      <view class="section checklist-section" v-if="rptFieldChecklist.length">
        <view class="sec-title">📋 现场核验清单</view>
        <view class="cl-hint">以下为建议的现场核验任务，以观察和记录为主，不输出绝对开店阈值。</view>
        <view class="cl-item" v-for="(item, i) in rptFieldChecklist" :key="'cl'+i">
          <view class="cl-head">
            <text class="cl-num">{{ checklistIndexIcon(i) }}</text>
            <text class="cl-title">{{ item.title }}</text>
          </view>
          <view class="cl-body" v-if="item.risk_type || item.time_window || item.action">
            <view class="cl-row cl-row-danger" v-if="item.risk_type">
              <text class="cl-row-label">风险</text>
              <text class="cl-row-text danger">{{ item.risk_type }}</text>
            </view>
            <view class="cl-row" v-if="item.time_window">
              <text class="cl-row-label">建议时间</text>
              <text class="cl-row-text">{{ item.time_window }}</text>
            </view>
            <view class="cl-row" v-if="item.action">
              <text class="cl-row-label">核验动作</text>
              <text class="cl-row-text">{{ item.action }}</text>
            </view>
            <view class="cl-row" v-if="item.record_method && item.record_method.length">
              <text class="cl-row-label">记录方式</text>
              <view class="cl-tags">
                <text class="cl-tag" v-for="rm in item.record_method" :key="rm">{{ rm }}</text>
              </view>
            </view>
            <view class="cl-row" v-if="item.pass_hint">
              <text class="cl-row-label">通过信号</text>
              <text class="cl-row-text hint">{{ item.pass_hint }}</text>
            </view>
            <view class="cl-row" v-if="item.eliminate_hint">
              <text class="cl-row-label danger-label">淘汰信号</text>
              <text class="cl-row-text danger-text">{{ item.eliminate_hint }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- P0-B: 竞品口径说明 -->
      <view class="section" v-if="rptCaliberExplanation">
        <view class="sec-title">📖 竞品口径说明</view>
        <text class="sec-text">{{ rptCaliberExplanation }}</text>
        <view class="ev-table" v-if="evidenceRows.length">
          <view class="ev-head">
            <text>范围</text><text>直接竞品</text><text>替代消费</text><text>客流锚点</text>
          </view>
          <view class="ev-row" v-for="row in evidenceRows" :key="row.radius">
            <text class="ev-radius">{{ row.radius }}</text>
            <text>{{ row.direct }}</text>
            <text>{{ row.substitute }}</text>
            <text>{{ row.anchor }}</text>
          </view>
          <text class="ev-note">用于说明不同距离内的竞争、替代消费和客流设施分布，需结合现场动线继续核验。</text>
        </view>
      </view>

      <!-- P0-B: 数据说明与风险边界 -->
      <view class="section disc-section" v-if="rptDataBoundary">
        <view class="sec-title">📌 数据说明与风险提示</view>
        <text class="sec-text">{{ rptDataBoundary }}</text>
      </view>

        <!-- Bottom bar -->
        <view class="bottom-bar">
          <button class="bb-feedback" v-if="!isShared" @tap="goFeedback">提交报告反馈</button>
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
import config from '../../utils/config'
import { scoreColor, formatTime } from '../../utils/format'

export default {
  data () {
    return {
      loading: true, errorMsg: '', record: {}, isShared: false, shareConfig: {},
      reportShareImageLocal: '',
      _reportShareImageRemote: '',
      poiExpanded: false,
      rptScore: 0, rptDisclaimer: '', rptWarning: '', rptSummary: '',
      rptAdv: [], rptDis: [], rptDims: [], rptAction: [],
      rptDemandContradiction: '',
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
      rptDirMore: 0, rptSubMore: 0, rptAncMore: 0,
      // P0-B: 新报告结构
      rptType: '',  // normal / retry / fallback
      rptGeneratedAt: '',  // P0.5: 统一北京时间
      rptDecisionSnapshot: null,
      rptFieldChecklist: [],
      rptCaliberExplanation: '',
      rptDataSufficiency: null,
      rptEvidenceSummary: null,
      rptDataBoundary: '',
      rptFallbackNote: false,
      // P1: 地点基本面与生意模型快照
      rptLocationFundamentals: null,
      rptBusinessModelSnapshot: null,
      rptRevenueDisclaimer: '',
    }
  },
  computed: {
    recordTitle () { return this.record.brand_desc || this.record.business_type || '报告详情' },
    hasCompetition () { return this.rptDir200 + this.rptDir500 + this.rptDir1000 > 0 },
    hasContent () { return this.rptScore > 0 || this.rptSummary || this.rptAdv.length || this.rptDims.length || this.rptQual.length || this.rptBrands.length || this.rptIrr > 0 || this.rptCity || this.hasStats || this.rptDirList.length || this.rptDetailTexts.length || this.rptPoiCats.length },
    hasStats () { return this.rptStats.length > 0 },
    visiblePoiCats () { return this.poiExpanded ? this.rptPoiCats : this.rptPoiCats.slice(0, 10) },
    evidenceRows () {
      if (!this.rptEvidenceSummary) return []
      return ['200m', '500m', '1000m'].map(radius => ({
        radius,
        direct: this.evVal('direct_competitors', radius),
        substitute: this.evVal('substitute_consumption', radius),
        anchor: this.evVal('traffic_anchors', radius)
      }))
    },
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
    },
    verdictClass () {
      const v = (this.rptDecisionSnapshot && this.rptDecisionSnapshot.verdict) || ''
      if (v.includes('继续考察') || v.includes('可优先现场核验')) return 'verdict-ok'
      if (v.includes('谨慎')) return 'verdict-warn'
      if (v.includes('低优先级') || v.includes('不建议') || v.includes('优先推进')) return 'verdict-no'
      return ''
    },
    suffIcon () {
      const level = (this.rptDataSufficiency && this.rptDataSufficiency.level) || ''
      if (level === 'sufficient') return '✅'
      if (level === 'insufficient') return '⚠️'
      return '📊'
    }
  },
  mounted () {
    if (typeof wx !== 'undefined' && wx.showShareMenu) {
      wx.showShareMenu({ menus: ['shareAppMessage', 'shareTimeline'] })
    }
  },
  onLoad (options) {
    // 加载分享配置 — 下载分享图到本地临时路径
    api.fetchShareConfig().then(c => {
      if (c.ok && c.data) {
        this.shareConfig = c.data
        const imgUrl = this.resolveShareImage(c.data.report_share_image_url || c.data.share_image_url || '')
        if (imgUrl) {
          this._reportShareImageRemote = imgUrl
          this._downloadShareImage(imgUrl)
        }
      }
    }).catch(() => {})
    const shareToken = options.share
    const recordId = options.id
    this.isShared = !!shareToken

    if (shareToken) {
      // ★ 分享入口：保存 token 供二次转发使用
      this._shareToken = shareToken
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
  onShareTimeline () {
    const cfg = this.shareConfig || {}
    const imageUrl = this.reportShareImageLocal || this.resolveShareImage(cfg.report_share_image_url || cfg.share_image_url || '') || this._reportShareImageRemote
    const token = this._shareToken || ''
    const q = token ? 'share=' + token + '&from=timeline' : 'from=timeline'
    const title = this.buildReportShareTitle()
    const payload = { title, query: q }
    if (imageUrl) payload.imageUrl = imageUrl
    return payload
  },
  onShareAppMessage () {
    const imageUrl = this.getReportShareImageUrl()
    const token = this._shareToken || ''
    const title = this.buildReportShareTitle()
    const payload = token
      ? { title, path: `/pages/report-detail/index?share=${token}` }
      : { title, path: '/pages/home/index' }
    if (imageUrl) payload.imageUrl = imageUrl
    return payload
  },
  onShow () {
    // 重新拉取分享配置，确保后台修改后小程序不用旧缓存
    api.fetchShareConfig().then(c => {
      if (c.ok && c.data) {
        this.shareConfig = c.data
        const imgUrl = this.resolveShareImage(c.data.report_share_image_url || c.data.share_image_url || '')
        if (imgUrl) {
          this._reportShareImageRemote = imgUrl
          this._downloadShareImage(imgUrl)
        }
      }
    }).catch(() => {})
  },
  methods: {
    sc: scoreColor, fmtTime: formatTime,
    maskProviderText (text) {
      if (typeof text !== 'string') return text
      return text
        .replace(/高德地图POI采集/g, '地图数据采集')
        .replace(/高德地图\s*POI/g, '地图数据')
        .replace(/高德地图/g, '地图数据')
        .replace(/高德/g, '地图服务')
        .replace(/POI数据采集/g, '周边数据采集')
        .replace(/POI/g, '点位数据')
    },
    maskDeep (value) {
      if (typeof value === 'string') return this.maskProviderText(value)
      if (Array.isArray(value)) return value.map(v => this.maskDeep(v))
      if (value && typeof value === 'object') {
        const out = {}
        Object.keys(value).forEach(k => { out[k] = this.maskDeep(value[k]) })
        return out
      }
      return value
    },
    applyReportDisplayMask () {
      ;['rptDisclaimer','rptWarning','rptSummary','rptCaliberExplanation','rptDataBoundary','rptRevenueDisclaimer','rptBizAreas','rptRoads'].forEach(k => {
        this[k] = this.maskProviderText(this[k])
      })
      ;['rptAdv','rptDis','rptAction','rptQual','rptDirList','rptSubList','rptAncList','rptIrrList','rptDetailTexts','rptPoiCats','rptFieldChecklist','rptBrands','rptStats'].forEach(k => {
        this[k] = this.maskDeep(this[k])
      })
      this.rptDecisionSnapshot = this.maskDeep(this.rptDecisionSnapshot)
      this.rptDataSufficiency = this.maskDeep(this.rptDataSufficiency)
      this.rptLocationFundamentals = this.maskDeep(this.rptLocationFundamentals)
      this.rptBusinessModelSnapshot = this.maskDeep(this.rptBusinessModelSnapshot)
    },
    resolveShareImage (url) {
      if (!url) return ''
      if (url.startsWith('/assets/')) return config.API_BASE_URL + url
      return url
    },
    getReportShareImageUrl () {
      const cfg = this.shareConfig || {}
      const raw = cfg.report_share_image_url || cfg.share_image_url || ''
      const resolved = this.resolveShareImage(raw) || this._reportShareImageRemote
      return this.reportShareImageLocal || resolved
    },
    _downloadShareImage (url) {
      uni.downloadFile({
        url,
        success: (res) => {
          if (res.statusCode === 200 && res.tempFilePath) {
            this.reportShareImageLocal = res.tempFilePath
          }
        },
        fail: (err) => { console.warn('[share-report] downloadFile failed:', (err && err.errMsg) || err) }
      })
    },
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
    goFeedback () {
      const token = uni.getStorageSync('token')
      if (!token) {
        uni.showToast({ title: '登录后才能提交反馈', icon: 'none' })
        return
      }
      const params = [
        'source=report_detail',
        'report_uuid=' + encodeURIComponent(this.record.report_uuid || ''),
        'report_title=' + encodeURIComponent(this.recordTitle || '选址报告'),
        'report_address=' + encodeURIComponent(this.record.address || '')
      ].join('&')
      uni.navigateTo({ url: '/pages/profile/feedback?' + params })
    },
    goBack () { uni.navigateBack({ delta: 1 }).catch(() => uni.reLaunch({ url: '/pages/home/index?tab=records' })) },
    goToHome () { uni.reLaunch({ url: '/pages/home/index' }) },
    evVal (group, radius) {
      const es = this.rptEvidenceSummary
      if (!es || !es[group] || typeof es[group] !== 'object') return 0
      const v = es[group][radius]
      return (v !== undefined && v !== null) ? v : 0
    },
    checklistIndexIcon (i) {
      return ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣'][i] || String(i + 1)
    },
    compactAddress (addr, maxLen = 18) {
      if (!addr) return '门店'
      return addr.length > maxLen ? addr.slice(0, maxLen) + '...' : addr
    },
    buildReportShareTitle () {
      const cfg = this.shareConfig || {}
      const tpl = cfg.report_share_title_template || '{address}选址初筛：{verdict}'
      const address = this.compactAddress(this.record.address || this.record.brand_desc || '门店', 18)
      const businessType = this.record.business_type || ''
      const brandDesc = this.record.brand_desc || ''
      const verdict = (this.rptDecisionSnapshot && this.rptDecisionSnapshot.verdict) || '初筛参考'
      const score = this.rptScore > 0 ? String(this.scorePct) : ''
      return tpl
        .replace(/\{address\}/g, address)
        .replace(/\{business_type\}/g, businessType)
        .replace(/\{brand_desc\}/g, brandDesc)
        .replace(/\{verdict\}/g, verdict)
        .replace(/\{score\}/g, score)
    },
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
      // P0-B: 重置新字段
      this.rptType = ''; this.rptGeneratedAt = ''; this.rptDecisionSnapshot = null; this.rptFieldChecklist = []
      this.rptCaliberExplanation = ''; this.rptDataSufficiency = null
      this.rptEvidenceSummary = null; this.rptDataBoundary = ''; this.rptFallbackNote = false
      this.rptLocationFundamentals = null; this.rptBusinessModelSnapshot = null
      this.rptRevenueDisclaimer = ''
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
      this.rptDemandContradiction = rpt.demand_contradiction_note || ''
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

      // ═══ P0-B: 新报告结构解析 ═══
      this.rptType = rpt.report_type || ''
      this.rptFallbackNote = (this.rptType === 'fallback')
      this.rptGeneratedAt = rpt.generated_at || ''

      // decision_snapshot
      const ds = rpt.decision_snapshot
      if (ds && typeof ds === 'object') {
        this.rptDecisionSnapshot = {
          verdict: ds.verdict || '',
          one_sentence: ds.one_sentence || '',
          score: ds.score ?? this.rptScore,
          top_strength: ds.top_strength || '',
          top_risk: ds.top_risk || '',
          next_action: ds.next_action || '',
          fit_condition: ds.fit_condition || '',
          stop_condition: ds.stop_condition || ''
        }
      }

      // field_checklist (兼容新旧格式)
      const fc = rpt.field_checklist
      if (Array.isArray(fc) && fc.length) {
        this.rptFieldChecklist = fc.map(item => {
          if (typeof item === 'string') {
            return { title: item, time_window: '', action: '', record_method: [], risk_type: '', pass_hint: '', eliminate_hint: '' }
          }
          if (typeof item === 'object' && item !== null) {
            return {
              title: item.title || item.text || '',
              time_window: item.time_window || '',
              action: item.action || '',
              record_method: Array.isArray(item.record_method) ? item.record_method : [],
              risk_type: item.risk_type || '',
              pass_hint: item.pass_hint || '',
              eliminate_hint: item.eliminate_hint || ''
            }
          }
          return null
        }).filter(Boolean)
      }

      // caliber_explanation
      this.rptCaliberExplanation = rpt.caliber_explanation || ''

      // data_sufficiency
      const suff = rpt.data_sufficiency
      if (suff && typeof suff === 'object') {
        this.rptDataSufficiency = {
          level: suff.level || 'moderate',
          label: suff.label || '数据一般',
          summary: suff.summary || '',
          reasons: Array.isArray(suff.reasons) ? suff.reasons : [],
          flags: suff.flags || {}
        }
      }

      // evidence_summary (安全归一化，避免缺子字段崩模板)
      const ev = rpt.evidence_summary || {}
      this.rptEvidenceSummary = {
        direct_competitors: (ev.direct_competitors && typeof ev.direct_competitors === 'object') ? ev.direct_competitors : {},
        substitute_consumption: (ev.substitute_consumption && typeof ev.substitute_consumption === 'object') ? ev.substitute_consumption : {},
        traffic_anchors: (ev.traffic_anchors && typeof ev.traffic_anchors === 'object') ? ev.traffic_anchors : {}
      }

      // data_boundary
      this.rptDataBoundary = rpt.data_boundary || ''

      // report_type fallback 提示
      if (this.rptFallbackNote && !this.rptDataBoundary) {
        this.rptDataBoundary = '本报告为保守版数据摘要，仅基于地图数据生成，不包含完整深度分析。建议结合现场核验。'
      }

      // P1: 地点基本面与生意模型快照
      if (rpt.location_fundamentals && typeof rpt.location_fundamentals === 'object') {
        this.rptLocationFundamentals = rpt.location_fundamentals
      }
      if (rpt.business_model_snapshot && typeof rpt.business_model_snapshot === 'object') {
        this.rptBusinessModelSnapshot = rpt.business_model_snapshot
      }
      // P1: 营收免责（按业态区分）
      this.rptRevenueDisclaimer = rpt.revenue_disclaimer || ''
      this.applyReportDisplayMask()
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
.err-btn::after, .bb-back::after, .bb-feedback::after, .share-cta-btn::after { border:none; }

.header { margin:0 0 16rpx; padding:30rpx 28rpx 34rpx; background:linear-gradient(180deg,#0b3fbd 0%,#1236a3 58%,#172554 100%); position:relative; overflow:hidden; }
.header::before { content:''; position:absolute; left:26rpx; right:26rpx; bottom:-72rpx; height:120rpx; border-radius:24rpx; background:rgba(255,255,255,0.08); transform:skewY(-4deg); }
.header-nav { position:relative; z-index:1; display:flex; align-items:center; justify-content:space-between; margin-bottom:24rpx; }
.back { width:64rpx; height:64rpx; border-radius:18rpx; background:rgba(255,255,255,0.18); border:1rpx solid rgba(255,255,255,0.24); color:#fff; font-size:40rpx; font-weight:800; line-height:60rpx; text-align:center; display:block; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.18); }
.hd-pill { height:50rpx; line-height:50rpx; padding:0 22rpx; border-radius:999rpx; background:rgba(255,255,255,0.14); border:1rpx solid rgba(255,255,255,0.26); color:#eaf0ff; font-size:24rpx; font-weight:700; }
.hd-text { position:relative; z-index:1; }
.hd-brand { display:block; font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; }
.hd-title { display:block; font-size:38rpx; font-weight:900; color:#fff; margin-top:8rpx; line-height:1.2; }
.hd-name { display:block; font-size:29rpx; font-weight:800; color:#f7d77b; margin-top:14rpx; line-height:1.38; word-break:break-all; }
.hd-sub { display:block; font-size:26rpx; color:rgba(232,240,255,0.84); margin-top:8rpx; line-height:1.55; word-break:break-all; }

.score-card { background:#fff; margin:0 24rpx 22rpx; border-radius:22rpx; padding:30rpx 28rpx; box-shadow:0 18rpx 42rpx rgba(36,70,128,0.10); border:1rpx solid rgba(213,224,246,0.95); display:flex; align-items:center; }
.sc-left { flex-shrink:0; width:154rpx; margin-right:30rpx; display:flex; flex-direction:column; align-items:center; }
.sc-right { flex:1; min-width:0; }
.score-title { display:block; width:150rpx; height:36rpx; line-height:36rpx; margin:0 0 12rpx; color:#17244e; font-size:25rpx; font-weight:900; text-align:center; }
.score-ring { width:150rpx; height:150rpx; border-radius:50%; display:flex; align-items:center; justify-content:center; }
.sr-inner { width:112rpx; height:112rpx; border-radius:50%; background:#fff; display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:inset 0 0 0 1rpx #edf2f7; }
.sr-num { font-size:46rpx; font-weight:900; line-height:1.02; }
.sr-unit { font-size:20rpx; font-weight:700; color:#8b99b6; line-height:1; margin-top:3rpx; }
.sc-verdict { font-size:30rpx; font-weight:900; display:block; line-height:1.2; }
.sc-caption { font-size:23rpx; color:#8b99b6; display:block; margin:5rpx 0 12rpx; }
.sc-addr { font-size:26rpx; color:#4b5872; display:block; margin-bottom:14rpx; line-height:1.58; word-break:break-all; }
.sc-tags { display:flex; flex-wrap:wrap; gap:8rpx; margin-bottom:10rpx; }
.sct { font-size:24rpx; font-weight:800; background:#f3f7ff; color:#315bff; border:1rpx solid rgba(49,91,255,0.14); border-radius:999rpx; padding:7rpx 16rpx; }
.sc-time { font-size:24rpx; color:#9aa6bd; }

.section, .content-box { background:rgba(255,255,255,0.96); margin:22rpx 24rpx 0; border-radius:22rpx; padding:30rpx 28rpx; box-shadow:0 12rpx 30rpx rgba(61,88,135,0.07); border:1rpx solid rgba(213,224,246,0.86); }
.sec-title { font-size:30rpx; font-weight:900; color:#17244e; margin-bottom:20rpx; line-height:1.3; }
.sec-title::before { content:''; display:inline-block; width:8rpx; height:24rpx; border-radius:6rpx; background:#315bff; margin-right:12rpx; vertical-align:-3rpx; }
.sec-green { color:#047857; }
.sec-green::before { background:#16a34a; }
.sec-red { color:#b91c1c; }
.sec-red::before { background:#ef4444; }
.sec-text, .item, .dt-text, .ql, .cb-text { font-size:27rpx; color:#4b5872; line-height:1.78; word-break:break-all; }
.item { padding:8rpx 0; }
.item-sm { font-size:27rpx; color:#64748b; padding:7rpx 0; line-height:1.62; word-break:break-all; }
.more-hint { font-size:25rpx; color:#8b99b6; display:block; margin-top:10rpx; line-height:1.55; }

.disc { background:#fff9e6; border:1rpx solid #f3d38a; border-radius:18rpx; padding:24rpx 26rpx; margin:22rpx 24rpx 0; font-size:26rpx; line-height:1.72; color:#8a5a12; box-shadow:0 10rpx 24rpx rgba(141,96,18,0.05); }
.warn { background:#fff1f2; border:1rpx solid #fecdd3; border-radius:18rpx; padding:24rpx 26rpx; margin:22rpx 24rpx 0; font-size:26rpx; line-height:1.72; color:#be123c; }
.warn-bold { font-weight:900; }
.cb-title { font-size:30rpx; font-weight:900; color:#17244e; display:block; margin-bottom:10rpx; }

.adv-item { display:flex; padding:18rpx 0; border-bottom:1rpx solid #edf2f7; }
.adv-item:last-child { border-bottom:0; padding-bottom:2rpx; }
.adv-num { width:44rpx; height:44rpx; border-radius:14rpx; background:#dcfce7; color:#047857; font-size:22rpx; font-weight:900; line-height:44rpx; text-align:center; flex-shrink:0; margin-right:16rpx; }
.adv-num.risk { background:#fff1f2; color:#be123c; }
.adv-text { font-size:27rpx; color:#344256; line-height:1.72; flex:1; word-break:break-all; }

.radar-card { background:linear-gradient(180deg,#ffffff,#f8fbff); }
.radar-head { margin-bottom:12rpx; }
.radar-title-row { display:flex; align-items:center; margin-bottom:8rpx; }
.radar-mark { width:42rpx; height:42rpx; line-height:42rpx; border-radius:12rpx; background:#eef4ff; text-align:center; font-size:24rpx; margin-right:12rpx; }
.radar-main { color:#17244e; font-size:30rpx; font-weight:900; line-height:1.25; }
.radar-sub { display:block; padding-left:54rpx; font-size:26rpx; color:#8b99b6; line-height:1.55; }
.radar-bars { padding:8rpx 0 2rpx; }
.rb-row { display:flex; align-items:center; padding:16rpx 0; }
.rb-label { width:170rpx; font-size:26rpx; color:#4b5872; flex-shrink:0; line-height:1.35; }
.rb-track { flex:1; height:16rpx; background:#e5ebf4; border-radius:10rpx; overflow:hidden; margin:0 16rpx; box-shadow:inset 0 1rpx 2rpx rgba(23,36,78,0.05); }
.rb-fill { height:100%; border-radius:10rpx; min-width:4rpx; transition:width 0.3s; }
.rb-val { width:58rpx; font-size:27rpx; font-weight:900; text-align:right; flex-shrink:0; }
.dim-compact { display:flex; flex-wrap:wrap; gap:10rpx; margin-top:20rpx; padding-top:18rpx; border-top:1rpx solid #edf2f7; }
.dc-chip { display:flex; align-items:center; padding:9rpx 14rpx; border-radius:14rpx; border:2rpx solid #e2e8f0; background:#f8fafc; }
.dc-chip-label { font-size:25rpx; color:#4b5872; margin-right:8rpx; }
.dc-chip-val { font-size:27rpx; font-weight:900; }

.comp-cols { display:flex; gap:14rpx; margin-bottom:18rpx; }
.cc-item { flex:1; text-align:center; padding:18rpx 8rpx; background:#f8fafc; border-radius:16rpx; border:1rpx solid #edf2f7; }
.cc-num { display:block; font-size:42rpx; font-weight:900; line-height:1.05; }
.cc-label { font-size:25rpx; color:#8b99b6; margin-top:6rpx; display:block; }
.comp-list { display:flex; flex-wrap:wrap; gap:10rpx; margin-top:12rpx; }
.comp-chip { font-size:26rpx; color:#4b5872; background:#f3f7ff; padding:9rpx 16rpx; border-radius:999rpx; border:1rpx solid rgba(49,91,255,0.12); max-width:100%; word-break:break-all; }
.comp-sub { margin-top:16rpx; padding-top:16rpx; border-top:1rpx solid #edf2f7; font-size:26rpx; color:#64748b; line-height:1.65; }
.cs-label { font-weight:900; color:#344256; }

.stats-grid { display:grid; grid-template-columns:repeat(3, minmax(0, 1fr)); gap:12rpx; }
.sg { width:auto; min-width:0; min-height:142rpx; text-align:center; padding:16rpx 8rpx 18rpx; box-sizing:border-box; border-radius:18rpx; background:linear-gradient(180deg,#fbfdff,#f4f7fc); border:1rpx solid #dde7f3; box-shadow:0 8rpx 18rpx rgba(40,76,130,0.05); display:flex; flex-direction:column; align-items:center; justify-content:center; overflow:hidden; }
.sg-icon { width:46rpx; height:46rpx; line-height:46rpx; border-radius:14rpx; background:#fff; box-shadow:0 6rpx 16rpx rgba(40,76,130,0.07); font-size:26rpx; display:block; margin-bottom:8rpx; }
.sg-label { font-size:25rpx; color:#7a879e; display:block; line-height:1.4; }
.sg-val { font-size:30rpx; font-weight:900; color:#17244e; display:block; margin-top:8rpx; line-height:1.22; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:100%; }
.sg.high .sg-val { color:#dc2626; }
.sg.good .sg-val { color:#16a34a; }
.sg.info .sg-val { color:#2563eb; }
.sg.high { background:linear-gradient(180deg,#fffafa,#fff1f2); border-color:#fecdd3; }
.sg.good { background:linear-gradient(180deg,#fbfffd,#ecfdf5); border-color:#bbf7d0; }
.sg.info { background:linear-gradient(180deg,#fbfdff,#eff6ff); border-color:#bfdbfe; }

.loc-row { font-size:27rpx; color:#344256; line-height:1.72; word-break:break-all; }
.loc-sub { font-size:26rpx; color:#64748b; margin-top:10rpx; line-height:1.65; word-break:break-all; }
.poi-cat { padding:18rpx 0; border-bottom:1rpx solid #edf2f7; }
.poi-cat:last-child { border-bottom:0; padding-bottom:2rpx; }
.poi-cat-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:8rpx; gap:16rpx; }
.poi-cat-label { font-size:28rpx; font-weight:900; color:#17244e; flex:1; }
.poi-cat-count { font-size:24rpx; color:#315bff; background:#eef4ff; padding:5rpx 15rpx; border-radius:999rpx; font-weight:900; }
.poi-cat-names { font-size:26rpx; color:#64748b; line-height:1.7; display:block; word-break:break-all; }
.poi-toggle { text-align:center; padding:18rpx 0 2rpx; font-size:28rpx; font-weight:900; color:#315bff; }

.dt-item { padding:20rpx 0; border-bottom:1rpx solid #edf2f7; }
.dt-item:last-child { border-bottom:0; padding-bottom:2rpx; }
.dt-head { display:flex; align-items:center; margin-bottom:10rpx; gap:16rpx; }
.dt-label { font-size:28rpx; font-weight:900; color:#17244e; flex:1; line-height:1.38; }
.dt-score { font-size:27rpx; font-weight:900; flex-shrink:0; }
.brands { display:flex; flex-wrap:wrap; gap:10rpx; }
.brand { font-size:26rpx; padding:10rpx 17rpx; background:#f3f7ff; border-radius:999rpx; color:#344256; border:1rpx solid rgba(49,91,255,0.12); max-width:100%; word-break:break-all; }
.brand-count { color:#8b99b6; }
.ql { display:block; padding:6rpx 0; }

.bottom-bar { margin-top:24rpx; padding:16rpx 24rpx 28rpx; display:flex; gap:14rpx; }
.bb-feedback { flex:1.15; height:88rpx; line-height:88rpx; padding:0; background:#fff; color:#315bff; border-radius:18rpx; font-size:29rpx; font-weight:900; border:1rpx solid rgba(49,91,255,0.22); box-shadow:0 10rpx 24rpx rgba(61,88,135,0.08); }
.bb-back { flex:1; height:88rpx; line-height:88rpx; padding:0; background:linear-gradient(135deg,#315bff,#5b4be6); color:#fff; border-radius:18rpx; font-size:30rpx; font-weight:900; box-shadow:0 14rpx 28rpx rgba(49,91,255,0.22), inset 0 1rpx 0 rgba(255,255,255,0.24); }
.share-cta { margin:28rpx 24rpx 40rpx; background:linear-gradient(135deg,#172554,#0b3fbd); border-radius:16rpx; padding:32rpx 24rpx; text-align:center; box-shadow:0 18rpx 38rpx rgba(21,31,143,0.18); }
.share-cta-title { display:block; color:rgba(255,255,255,0.88); font-size:26rpx; margin-bottom:20rpx; }
.share-cta-btn { width:100%; background:#fff; color:#0b3fbd; border-radius:16rpx; font-size:30rpx; font-weight:900; padding:20rpx 0; }

/* P0-A: fallback badge */
.fb-badge { margin:22rpx 24rpx 0; padding:18rpx 22rpx; background:#fff7d6; border:1rpx solid #f5dda2; border-radius:18rpx; display:flex; align-items:center; gap:12rpx; }
.fb-badge-icon { font-size:36rpx; }
.fb-badge-text { font-size:26rpx; color:#92400e; line-height:1.5; flex:1; }

/* P0-B: decision card */
.decision-card { margin:22rpx 24rpx 0; padding:32rpx 28rpx 34rpx; background:#fff; border-radius:22rpx; box-shadow:0 12rpx 30rpx rgba(61,88,135,0.07); border:1rpx solid rgba(213,224,246,0.86); }
.dc-verdict-row { display:flex; justify-content:space-between; align-items:flex-start; gap:18rpx; margin-bottom:20rpx; }
.dc-verdict { font-size:32rpx; font-weight:900; line-height:1.28; flex:1; min-width:0; }
.verdict-ok { color:#16a34a; }
.verdict-warn { color:#d97706; }
.verdict-no { color:#dc2626; }
.dc-score { font-size:42rpx; font-weight:900; color:#1e293b; line-height:1.1; flex-shrink:0; }
.dc-one-sentence { display:block; font-size:27rpx; color:#475569; line-height:1.72; margin:0 0 32rpx; }
.dc-pills { display:flex; flex-direction:column; gap:18rpx; margin-top:0; }
.dc-pill { padding:20rpx 22rpx; border-radius:16rpx; }
.dc-pill.strength { background:#effdf5; border-left:7rpx solid #16a34a; }
.dc-pill.risk { background:#fff5f5; border-left:7rpx solid #ef4444; }
.dc-pill-label { font-size:23rpx; font-weight:900; display:block; margin-bottom:6rpx; color:#64748b; }
.dc-pill.strength .dc-pill-label { color:#047857; }
.dc-pill.risk .dc-pill-label { color:#b91c1c; }
.dc-pill-text { font-size:26rpx; color:#1e293b; line-height:1.68; }
.dc-next { margin-top:20rpx; padding:16rpx; background:#eff6ff; border-radius:12rpx; }
.dc-next-label { font-size:24rpx; color:#3b82f6; font-weight:700; }
.dc-next-text { font-size:25rpx; color:#1e40af; line-height:1.58; }
.dc-cond { margin-top:12rpx; padding:12rpx 16rpx; border-radius:10rpx; }
.dc-cond.fit { background:#f0fdf4; }
.dc-cond.stop { background:#fef2f2; }
.dc-cond-label { font-size:22rpx; font-weight:700; }
.dc-cond.fit .dc-cond-label { color:#16a34a; }
.dc-cond.stop .dc-cond-label { color:#dc2626; }
.dc-cond-text { font-size:25rpx; color:#475569; line-height:1.58; }

.read-path { margin:22rpx 24rpx 0; padding:14rpx 12rpx; border-radius:20rpx; background:rgba(255,255,255,0.96); border:1rpx solid rgba(213,224,246,0.88); box-shadow:0 10rpx 24rpx rgba(61,88,135,0.06); display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:8rpx; }
.rp-step { min-width:0; min-height:112rpx; padding:12rpx 6rpx; border-radius:14rpx; background:#f8fbff; border:1rpx solid #edf2f7; text-align:center; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; }
.rp-index { width:38rpx; height:38rpx; line-height:38rpx; border-radius:12rpx; background:#315bff; color:#fff; font-size:21rpx; font-weight:900; text-align:center; flex-shrink:0; }
.rp-title { display:block; width:100%; margin-top:8rpx; font-size:22rpx; font-weight:900; color:#17244e; line-height:1.2; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.rp-desc { display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:2; overflow:hidden; margin-top:5rpx; font-size:19rpx; line-height:1.32; color:#7a879e; word-break:break-all; }

/* P0-B: data sufficiency tag */
.ds-tag { margin:22rpx 24rpx 0; padding:16rpx 20rpx; border-radius:12rpx; display:flex; align-items:center; gap:10rpx; flex-wrap:wrap; }
.ds-sufficient { background:#f0fdf4; }
.ds-moderate { background:#f8fafc; }
.ds-insufficient { background:#fef2f2; }
.ds-icon { font-size:28rpx; }
.ds-label { font-size:24rpx; font-weight:700; }
.ds-sufficient .ds-label { color:#16a34a; }
.ds-moderate .ds-label { color:#64748b; }
.ds-insufficient .ds-label { color:#dc2626; }
.ds-summary { font-size:24rpx; color:#64748b; }

/* P0-B: checklist */
.checklist-section { margin:22rpx 24rpx 0; padding:30rpx 28rpx; background:#fff; border-radius:22rpx; }
.cl-hint { font-size:25rpx; color:#7a879e; margin-bottom:24rpx; line-height:1.65; }
.cl-item { margin-bottom:20rpx; padding:24rpx 22rpx 24rpx; border-radius:20rpx; background:linear-gradient(180deg,#f9fbff,#ffffff); border:1rpx solid #dbe7fb; box-shadow:0 10rpx 22rpx rgba(61,88,135,0.06); }
.cl-item:last-child { margin-bottom:0; }
.cl-head { display:flex; align-items:flex-start; gap:14rpx; margin-bottom:18rpx; }
.cl-num { width:46rpx; min-width:46rpx; height:38rpx; line-height:38rpx; color:#315bff; font-size:34rpx; font-weight:900; text-align:left; flex-shrink:0; }
.cl-head-body { flex:1; min-width:0; padding-top:1rpx; }
.cl-title { flex:1; min-width:0; font-size:28rpx; font-weight:900; color:#17244e; display:block; line-height:1.42; word-break:break-all; padding-top:2rpx; }
.cl-risk { font-size:22rpx; color:#b91c1c; background:#fff1f2; padding:5rpx 12rpx; border-radius:999rpx; margin-top:9rpx; display:inline-block; line-height:1.25; }
.cl-body { padding-left:0; }
.cl-row { display:flex; gap:14rpx; margin-bottom:14rpx; align-items:flex-start; padding-left:0; box-sizing:border-box; }
.cl-row:last-child { margin-bottom:0; }
.cl-row-label { font-size:23rpx; color:#8795ad; width:116rpx; flex-shrink:0; line-height:1.62; font-weight:900; text-align:left; }
.cl-row-text { font-size:25rpx; color:#475569; line-height:1.62; flex:1; word-break:break-all; }
.cl-row-text.hint { color:#315bff; font-style:normal; }
.cl-row-text.danger,.danger-text { color:#b91c1c; }
.danger-label { color:#dc2626 !important; }
.cl-row-danger .cl-row-label { color:#dc2626; }
.cl-tags { display:flex; gap:8rpx; flex-wrap:wrap; }
.cl-tag { font-size:22rpx; padding:4rpx 12rpx; background:#eef4ff; color:#315bff; border-radius:999rpx; line-height:1.3; }

/* P0-B: evidence table */
.ev-table { margin-top:20rpx; overflow:hidden; border-radius:16rpx; border:1rpx solid #dbe7fb; background:#f8fbff; }
.ev-head,.ev-row { display:grid; grid-template-columns:1fr 1fr 1fr 1fr; align-items:center; }
.ev-head { background:#eef4ff; }
.ev-head text { padding:14rpx 6rpx; text-align:center; font-size:22rpx; color:#66758f; font-weight:900; }
.ev-row text { padding:16rpx 6rpx; text-align:center; font-size:26rpx; color:#334155; font-weight:800; border-top:1rpx solid #e6eefb; }
.ev-radius { color:#315bff !important; }
.ev-note { display:block; padding:16rpx 18rpx; border-top:1rpx solid #e6eefb; font-size:24rpx; line-height:1.58; color:#7a879e; }

.disc-section { margin:20rpx 24rpx; }

/* P1: 地点基本面 */
.loc-fund-box { background:#f8fafc; border:1rpx solid #e2e8f0; border-radius:12rpx; padding:18rpx 20rpx; margin-bottom:18rpx; }
.loc-fund-type { display:block; font-size:26rpx; font-weight:900; color:#1f4aa8; margin-bottom:8rpx; }
.loc-fund-summary { font-size:26rpx; color:#475569; line-height:1.72; }
.split-mini { display:flex; flex-direction:column; gap:14rpx; }
.sm-item { width:100%; box-sizing:border-box; border-radius:16rpx; padding:18rpx 20rpx; }
.sm-item.good { background:#effdf5; border:1rpx solid #bbf7d0; }
.sm-item.bad { background:#fff5f5; border:1rpx solid #fecaca; }
.sm-title { display:block; font-size:24rpx; font-weight:900; margin-bottom:10rpx; }
.sm-title.sm-green { color:#047857; }
.sm-title.sm-red { color:#b91c1c; }
.sm-text { display:block; font-size:24rpx; color:#475569; line-height:1.7; }

/* P1: 生意模型快照 */
.biz-snap-box { background:#f0fdf4; border:1rpx solid #bbf7d0; border-radius:12rpx; padding:18rpx 20rpx; margin-bottom:18rpx; }
.biz-snap-core { font-size:26rpx; color:#334155; line-height:1.75; display:block; }
.biz-snap-comp { font-size:24rpx; color:#64748b; line-height:1.75; display:block; margin-top:10rpx; }
.biz-must-verify { margin-bottom:18rpx; }
.bmv-title { font-size:26rpx; font-weight:900; color:#0f172a; display:block; margin-bottom:10rpx; }
.bmv-item { display:flex; gap:10rpx; padding:10rpx 0; border-bottom:1rpx solid #f1f5f9; }
.bmv-num { width:40rpx; height:40rpx; background:#dbeafe; border-radius:50%; text-align:center; line-height:40rpx; font-size:22rpx; font-weight:900; color:#1f4aa8; flex-shrink:0; }
.bmv-text { font-size:25rpx; color:#475569; line-height:1.6; flex:1; }
.biz-cond { padding:14rpx 16rpx; border-radius:10rpx; margin-top:10rpx; }
.biz-cond.fit { background:#f0fdf4; border:1rpx solid #bbf7d0; }
.biz-cond.stop { background:#fff5f5; border:1rpx solid #fecaca; }
.biz-cond-label { font-size:23rpx; font-weight:900; }
.biz-cond.fit .biz-cond-label { color:#16a34a; }
.biz-cond.stop .biz-cond-label { color:#dc2626; }
.biz-cond-text { font-size:24rpx; color:#475569; line-height:1.7; }
</style>
