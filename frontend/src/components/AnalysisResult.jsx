import RadarChart from './RadarChart'

const detailLabels = {
  population_density: '人口密集度',
  traffic_accessibility: '交通与可达性',
  traffic_flow: '客流特征',
  consumer_profile: '消费人群属性',
  competition: '竞争环境',
  complementary_businesses: '周边互补业态',
  category_advantage: '品类优势与差异化',
  cost_estimate: '房租成本预估',
  revenue_estimation: '营收测算模型',
  site_suggestion: '选址分析与运营策略',
}

const dimLabel = {
  population_density: '人口密度', traffic_accessibility: '交通可达性',
  traffic_flow: '客流特征', consumer_profile: '消费人群',
  competition: '竞争环境', complementary_businesses: '互补业态',
  category_advantage: '品类优势', cost_estimate: '成本预估',
}

const WEIGHTS = {
  population_density: 0.15,
  traffic_accessibility: 0.12,
  traffic_flow: 0.18,
  consumer_profile: 0.15,
  competition: 0.20,
  complementary_businesses: 0.10,
  category_advantage: 0.10,
  cost_estimate: 0.00,
}

function parseDetail(text) {
  if (!text) return { score: 0, text: '' }
  const s = String(text)
  const m = s.match(/评分[：:]\s*(\d{1,3})|(\d{1,3})\s*分\s*$/)
  const score = m ? parseInt(m[1] || m[2]) : 0
  const clean = s.replace(/[，,]?\s*评分[：:]\s*\d{1,3}\s*分?\s*$/, '').replace(/\d{1,3}\s*分\s*$/, '').trim()
  return { score, text: clean }
}

function generateRadarSummary(scores, totalScore) {
  const valid = Object.entries(scores)
    .filter(([k, v]) => v > 0 && k !== 'cost_estimate')
    .sort((a, b) => b[1] - a[1])
  if (valid.length === 0) return ''
  const strong = valid.slice(0, 2).map(([k]) => dimLabel[k])
  const weak = valid.filter(([, v]) => v < 50).slice(-2).map(([k]) => dimLabel[k])
  let text = `该位置在${strong.join('、')}方面表现较为突出`
  if (weak.length > 0) text += `，但${weak.join('、')}方面需重点关注`
  if (totalScore >= 65) text += '，整体选址条件良好'
  else if (totalScore >= 45) text += '，整体条件尚可但需权衡利弊'
  else text += '，整体条件需谨慎评估'
  return text + '。'
}

function formatCount(num) {
  if (num === undefined || num === null) return '—'
  return num
}

function ScoreRing({ score }) {
  const scoreColor = score >= 60 ? '#10b981' : score >= 40 ? '#f59e0b' : '#ef4444'
  const ringSize = 112
  const strokeW = 10
  const radius = (ringSize - strokeW) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score / 100)
  const cx = ringSize / 2
  const cy = ringSize / 2
  return (
    <div className="mb-4 flex flex-col items-center">
      <svg width={ringSize} height={ringSize} viewBox={`0 0 ${ringSize} ${ringSize}`}>
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke="#e7ece8" strokeWidth={strokeW} />
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke={scoreColor} strokeWidth={strokeW}
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }} />
        <text x={cx} y={cy - 4} textAnchor="middle" dominantBaseline="central"
          fontSize="32" fontWeight="800" fill={scoreColor}>
          {score}
        </text>
        <text x={cx} y={cy + 16} textAnchor="middle" dominantBaseline="central"
          fontSize="11" fill="#9ca3af" fontWeight="500">
          / 100
        </text>
      </svg>
    </div>
  )
}

function SectionHeader({ title, color = 'blue' }) {
  const colors = {
    blue: 'before:bg-blue-500',
    green: 'before:bg-emerald-600',
    red: 'before:bg-red-500',
    gray: 'before:bg-slate-400',
  }
  return (
    <h3 className={`relative mb-3 pl-3 text-base font-bold text-slate-900 before:absolute before:left-0 before:top-1 before:h-4 before:w-1 before:rounded-full ${colors[color] || colors.blue}`}>
      {title}
    </h3>
  )
}

function MetricBadge({ icon, label, val, sub, highlight, raw }) {
  const bgMap = {
    high: 'bg-red-50 border border-red-100',
    good: 'bg-emerald-50 border border-emerald-100',
    info: 'bg-blue-50 border border-blue-100',
  }
  const textMap = {
    high: 'text-red-600',
    good: 'text-emerald-700',
    info: 'text-blue-600',
  }
  const showDual = raw !== undefined && raw !== null && raw !== val
  return (
    <div className={`min-w-0 rounded-lg p-3 ${bgMap[highlight] || 'border border-slate-100 bg-slate-50'}`}>
      <div className="mb-1 flex items-center gap-1.5">
        <span className="text-base">{icon}</span>
        <p className="truncate text-sm text-slate-500">{label}</p>
      </div>
      <div className="min-w-0">
        <p className={`truncate text-base font-bold ${textMap[highlight] || 'text-slate-700'}`}>
          {val}
          {showDual && <span className="ml-1 text-xs font-normal text-slate-400">(共:{raw})</span>}
        </p>
        {sub && <p className="mt-0.5 text-[9px] text-slate-400">{sub}</p>}
      </div>
    </div>
  )
}

export default function AnalysisResult({ data }) {
  if (!data) return null

  const _stripScore = (v) => String(v || '').replace(/[，,]?\s*评分[：:]\s*\d{1,3}\s*分?\s*$/, '').trim()

  const { advantages, disadvantages, summary, details, warning, real_data, executive_summary = {}, dimension_scores = [], action_plan = [] } = data

  // ★ 严谨度：仅认 rigor_enabled
  const hasRigor = real_data?.rigor_enabled === true
  const dc200 = hasRigor ? (real_data.direct_competitors_200m ?? 0) : (real_data?.competitors_200m ?? 0)
  const dc500 = hasRigor ? (real_data.direct_competitors_500m ?? 0) : (real_data?.competitors_500m ?? 0)
  const dc1000 = hasRigor ? (real_data.direct_competitors_1000m ?? 0) : (real_data?.competitors_1000m ?? 0)
  const dcList = hasRigor ? (real_data.direct_competitor_list || []) : (real_data?.competitor_list || [])

  if (data.error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-600">
        分析出错：{data.error}
      </div>
    )
  }

  // Parse scores
  const radarScores = {}
  const parsedDetails = {}
  Object.keys(detailLabels).forEach((key) => {
    if (key === 'revenue_estimation' || key === 'site_suggestion') {
      parsedDetails[key] = { score: 0, text: details?.[key] ? String(details[key]) : '' }
      return
    }
    const pd = parseDetail(details?.[key])
    radarScores[key] = pd.score
    parsedDetails[key] = pd
  })
  if (dimension_scores?.length) {
    dimension_scores.forEach((item) => {
      if (!item?.key) return
      radarScores[item.key] = Number(item.score || 0)
      parsedDetails[item.key] = {
        score: Number(item.score || 0),
        text: item.text || parsedDetails[item.key]?.text || String(details?.[item.key] || ''),
      }
    })
  }

  // ★ 以后端加权后的总分（data.score）为准，全局唯一
  const totalScore = Number(data.score || data.overall_score || 0)

  const summaryText = generateRadarSummary(radarScores, totalScore)
  const topStrengths = (advantages && advantages.length > 0) ? advantages.filter(Boolean) : (executive_summary?.top_strengths || [])
  const topRisks = (disadvantages && disadvantages.length > 0) ? disadvantages.filter(Boolean) : (executive_summary?.top_risks || [])
  const scoreColor = totalScore >= 60 ? '#10b981' : totalScore >= 40 ? '#f59e0b' : '#ef4444'
  const primaryDims = (dimension_scores?.length ? dimension_scores : Object.keys(dimLabel).map(key => ({ key, label: dimLabel[key], score: radarScores[key] || 0 }))).slice(0, 8)

  const dimEmoji = { population_density: '🏘️', traffic_accessibility: '🚇', traffic_flow: '🚶', consumer_profile: '🛍️', competition: '⚔️', complementary_businesses: '🤝', category_advantage: '🌟', cost_estimate: '💰', revenue_estimation: '💵', site_suggestion: '📋' }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', background: '#f8fafc', padding: '16px 0' }}>

      {/* ═══════════ 免责声明 ═══════════ */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 12, lineHeight: 1.6, color: '#92400e' }}>
        <span style={{ flexShrink: 0, fontSize: 14 }}>💡</span>
        <span>本工具不提供"推荐/不推荐"结论，各维度评分仅供参考，最终决策请结合实地考察与多方因素综合判断。</span>
      </div>

      {/* ═══════════ 风险提示 ═══════════ */}
      {warning && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '10px 14px', marginBottom: 16, fontSize: 12, lineHeight: 1.6, color: '#991b1b' }}>
          <span style={{ flexShrink: 0, fontSize: 14 }}>⚠️</span>
          <span><strong>风险提示：</strong>{warning}</span>
        </div>
      )}

      {/* ═══════════ 第一块：综合评分 + 分析摘要 ═══════════ */}
      <div style={{ background: '#fff', borderRadius: 6, border: '1px solid #e2e8f0', padding: 24, marginBottom: 16, boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: 20 }}>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#1e293b', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            📊 综合评分
          </div>
          <ScoreRing score={totalScore} />
          <div style={{ fontSize: 13, color: '#94a3b8', marginTop: 4 }}>8 维度平均</div>
        </div>
        <div>
          <div style={{ fontSize: 16, fontWeight: 900, color: '#1e293b', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
            📋 分析摘要
          </div>
          <p style={{ fontSize: 15, color: '#475569', lineHeight: 1.7, margin: 0 }}>
            {summary || executive_summary?.summary || summaryText}
          </p>
        </div>
      </div>

      {/* ═══════════ 第二块：关键优势 + 主要风险（上下排列）═══════════ */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
        <section style={{ border: '1px solid #bbf7d0', borderRadius: 6, padding: '16px 20px', background: '#f0fdf4' }}>
          <h2 style={{ fontSize: 17, fontWeight: 900, margin: '0 0 12px', color: '#047857' }}>✅ 关键优势</h2>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, fontWeight: 400, color: '#475569', lineHeight: 1.7, textAlign: 'justify' }}>
            {topStrengths.map((item, i) => <li key={i} style={{ marginBottom: i === topStrengths.length - 1 ? 0 : 6 }}>{item}</li>)}
          </ul>
        </section>
        <section style={{ border: '1px solid #fecaca', borderRadius: 6, padding: '16px 20px', background: '#fff5f5' }}>
          <h2 style={{ fontSize: 17, fontWeight: 900, margin: '0 0 12px', color: '#b91c1c' }}>⚠️ 主要风险</h2>
          <ul style={{ margin: 0, paddingLeft: 20, fontSize: 14, fontWeight: 400, color: '#475569', lineHeight: 1.7, textAlign: 'justify' }}>
            {topRisks.map((item, i) => <li key={i} style={{ marginBottom: i === topRisks.length - 1 ? 0 : 6 }}>{item}</li>)}
          </ul>
        </section>
      </div>

      {/* ═══════════ 第三块：指标雷达图 ═══════════ */}
      <div style={{ background: '#fff', borderRadius: 6, border: '1px solid #e2e8f0', padding: 24, marginBottom: 16, boxShadow: '0 1px 2px rgba(0,0,0,0.04)' }}>
        <h2 style={{ fontSize: 17, fontWeight: 900, margin: '0 0 16px', color: '#0f172a', textAlign: 'center' }}>📊 指标雷达图</h2>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <RadarChart scores={(() => {
            const ORDER = ['人口密集度', '交通可达性', '客流特征', '消费人群', '竞争环境', '互补业态', '品类优势', '成本压力']
            const KEY_MAP = { '人口密集度': 'population_density', '交通可达性': 'traffic_accessibility', '客流特征': 'traffic_flow', '消费人群': 'consumer_profile', '竞争环境': 'competition', '互补业态': 'complementary_businesses', '品类优势': 'category_advantage', '成本压力': 'cost_estimate' }
            const locked = {}
            ORDER.forEach(label => { locked[KEY_MAP[label]] = radarScores[KEY_MAP[label]] || 0 })
            return locked
          })()} />
        </div>
      </div>

      {/* ═══════════ 第四块：维度评分卡片 ═══════════ */}
      <div style={{ background: '#fff', borderRadius: 6, border: '1px solid #e2e8f0', padding: 24, marginBottom: 16 }}>
        <h2 style={{ fontSize: 17, fontWeight: 900, margin: '0 0 12px', color: '#0f172a' }}>📈 维度评分</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {primaryDims.map((d) => {
            const s = Number(d.score || 0)
            const sc = s >= 60 ? '#10b981' : s >= 40 ? '#f59e0b' : '#ef4444'
            return (
              <div key={d.key} style={{ padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 6, background: '#fff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                  <strong style={{ fontSize: 13, color: '#334155' }}>{d.label || dimLabel[d.key]}</strong>
                  <span style={{ fontSize: 16, fontWeight: 900, color: sc }}>{s || '-'}</span>
                </div>
                <div style={{ height: 5, background: '#e5e7eb', borderRadius: 99, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${Math.max(0, Math.min(100, s))}%`, background: sc }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* ═══════════ 第五块：周边真实数据 ═══════════ */}
      {real_data && (
        <div style={{ background: '#fff', borderRadius: 6, border: '1px solid #e2e8f0', padding: 24, marginBottom: 16 }}>
          <h2 style={{ fontSize: 17, fontWeight: 900, margin: '0 0 4px', color: '#0f172a' }}>📊 周边真实数据</h2>
          <p style={{ fontSize: 12, color: '#94a3b8', margin: '0 0 12px' }}>200m / 500m / 1000m 三层半径实时采集</p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginBottom: 12 }}>
            <MetricBadge icon="🏘️" label="住宅小区"
              val={`${formatCount(real_data.stats_200m?.residential)} / ${formatCount(real_data.stats_500m?.residential)} / ${formatCount(real_data.stats_1000m?.residential)}`}
              sub="200m/500m/1000m" highlight="info" raw={real_data.raw_stats_1000m?.residential} />
            <MetricBadge icon="🏢" label="写字楼"
              val={`${formatCount(real_data.stats_200m?.office)} / ${formatCount(real_data.stats_500m?.office)} / ${formatCount(real_data.stats_1000m?.office)}`}
              sub="200m/500m/1000m" highlight="info" raw={real_data.raw_stats_1000m?.office} />
            <MetricBadge icon="🍽️" label="餐饮门店"
              val={`${formatCount(real_data.stats_200m?.restaurants)} / ${formatCount(real_data.stats_500m?.restaurants)} / ${formatCount(real_data.stats_1000m?.restaurants)}`}
              sub="200m/500m/1000m" highlight={real_data.stats_1000m?.restaurants > 100 ? 'high' : 'info'} />
            <MetricBadge icon="☕" label="咖啡茶饮"
              val={`${formatCount(real_data.stats_200m?.cafe_tea)} / ${formatCount(real_data.stats_500m?.cafe_tea)} / ${formatCount(real_data.stats_1000m?.cafe_tea)}`}
              sub="200m/500m/1000m" />
            <MetricBadge icon="🛍️" label="购物商场"
              val={`${formatCount(real_data.stats_200m?.shopping)} / ${formatCount(real_data.stats_500m?.shopping)} / ${formatCount(real_data.stats_1000m?.shopping)}`}
              sub="200m/500m/1000m" raw={real_data.raw_stats_1000m?.shopping} />
            <MetricBadge icon="🏫" label="学校"
              val={`${formatCount(real_data.stats_200m?.schools)} / ${formatCount(real_data.stats_500m?.schools)} / ${formatCount(real_data.stats_1000m?.schools)}`}
              sub="200m/500m/1000m" highlight={real_data.poi_counts?.schools > 5 ? 'good' : undefined} raw={real_data.raw_stats_1000m?.schools} />
            <MetricBadge icon="🏥" label="医院/诊所"
              val={`${formatCount(real_data.stats_200m?.hospitals)} / ${formatCount(real_data.stats_500m?.hospitals)} / ${formatCount(real_data.stats_1000m?.hospitals)}`}
              sub="200m/500m/1000m" highlight={real_data.poi_counts?.hospitals > 10 ? 'good' : 'info'} raw={real_data.raw_stats_1000m?.hospitals} />
            <MetricBadge icon="🚇" label="地铁站"
              val={`${formatCount(real_data.stats_200m?.subway)} / ${formatCount(real_data.stats_500m?.subway)} / ${formatCount(real_data.stats_1000m?.subway)}`}
              sub="200m/500m/1000m" highlight={!real_data.poi_counts?.subway ? 'high' : 'good'} raw={real_data.raw_stats_1000m?.subway} />
            <MetricBadge icon="🚌" label="公交站"
              val={`${formatCount(real_data.stats_200m?.bus)} / ${formatCount(real_data.stats_500m?.bus)} / ${formatCount(real_data.stats_1000m?.bus)}`}
              sub="200m/500m/1000m" highlight={real_data.poi_counts?.bus > 10 ? 'good' : undefined} raw={real_data.raw_stats_1000m?.bus} />
            <MetricBadge icon="🏨" label="酒店住宿"
              val={`${formatCount(real_data.stats_200m?.hotels)} / ${formatCount(real_data.stats_500m?.hotels)} / ${formatCount(real_data.stats_1000m?.hotels)}`}
              sub="200m/500m/1000m" raw={real_data.raw_stats_1000m?.hotels} />
            <MetricBadge icon="🏦" label="银行"
              val={`${formatCount(real_data.poi_counts?.banks)} 个`} raw={real_data.raw_poi_counts?.banks} />
            <MetricBadge icon="🅿️" label="停车场"
              val={`${formatCount(real_data.poi_counts?.parking)} 个`} raw={real_data.raw_poi_counts?.parking} />
          </div>
          <p style={{ fontSize: 11, color: '#94a3b8', marginBottom: 12, lineHeight: 1.4 }}>注：括号外为系统判定的有效商机数，已自动过滤诊所、培训机构、公司厂房等低关联干扰项</p>

          {/* ★ 严谨度提示：未启用时明确告知用户 */}
          {!hasRigor && (
            <div style={{ background: '#fffbeb', borderRadius: 6, padding: '8px 12px', marginBottom: 8, border: '1px solid #fde68a', fontSize: 11, color: '#92400e', textAlign: 'center', lineHeight: 1.5 }}>
              ⚠️ 该业态暂无完整严谨分类规则，竞品结果仅供兼容参考。如需精准竞品分析，请联系管理员补充业态规则或使用严谨分类已覆盖的业态重新分析。
            </div>
          )}

          {/* ★ 竞品参考：严谨框架/旧口径 */}
          {(hasRigor || dc1000 > 0) && (
            <div style={{ background: hasRigor ? '#fef2f2' : '#f8fafc', borderRadius: 6, padding: '12px 14px', marginBottom: 8, border: hasRigor ? '1px solid #fecaca' : '1px solid #e2e8f0' }}>
              <p style={{ fontSize: 14, fontWeight: 700, color: hasRigor ? '#dc2626' : '#64748b', margin: '0 0 4px', textAlign: 'center' }}>
                {hasRigor ? '🎯 直接竞品（同类业态 · 严谨口径）' : '📋 旧口径竞品参考（非严谨直接竞品）'}
              </p>
              <div style={{ fontSize: 13, color: hasRigor ? '#9a3412' : '#64748b', lineHeight: 2, textAlign: 'center' }}>
                200m: <strong style={{ fontSize: 17, color: hasRigor ? '#dc2626' : '#475569' }}>{formatCount(dc200)}</strong> ·
                500m: <strong style={{ fontSize: 17, color: hasRigor ? '#dc2626' : '#475569' }}>{formatCount(dc500)}</strong> ·
                1km: <strong style={{ fontSize: 17, color: hasRigor ? '#dc2626' : '#475569' }}>{formatCount(dc1000)}</strong>
              </div>
              {dcList.length > 0 ? (
                <div style={{ fontSize: 12, color: hasRigor ? '#9a3412' : '#64748b', lineHeight: 1.8, borderTop: '1px solid #e2e8f0', paddingTop: 6, marginTop: 4, textAlign: 'center' }}>
                  {dcList.slice(0, 10).map((c, i) => (
                    <span key={i} style={{ marginRight: 8 }}>· {c.name}（{c.distance}m）</span>
                  ))}
                </div>
              ) : hasRigor && (
                <div style={{ fontSize: 12, color: '#9a3412', lineHeight: 1.8, borderTop: '1px solid #fecaca', paddingTop: 6, marginTop: 4, textAlign: 'center' }}>
                  1km内暂无直接竞品
                </div>
              )}
              {!hasRigor && (
                <div style={{ fontSize: 10, color: '#b45309', textAlign: 'center', marginTop: 4, lineHeight: 1.5 }}>
                  ⚠️ 该业态暂无完整严谨分类规则。以上为旧口径统计，仅供兼容参考，需人工核验直接竞品。
                </div>
              )}
            </div>
          )}

          {/* ★ 严谨度框架：替代消费压力 */}
          {(real_data.substitute_competitors_1000m || 0) > 0 && (
            <div style={{ background: '#fff7ed', borderRadius: 6, padding: '10px 14px', marginBottom: 8, border: '1px solid #fed7aa' }}>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#c2410c', margin: '0 0 4px', textAlign: 'center' }}>🔶 替代消费压力（非同业态，不计入直接竞品）</p>
              <div style={{ fontSize: 11, color: '#9a3412', lineHeight: 1.6, textAlign: 'center' }}>
                200m: {formatCount(real_data.substitute_competitors_200m)} · 500m: {formatCount(real_data.substitute_competitors_500m)} · 1km: {formatCount(real_data.substitute_competitors_1000m)}
              </div>
              {real_data.substitute_list?.length > 0 && (
                <div style={{ fontSize: 11, color: '#9a3412', lineHeight: 1.6, borderTop: '1px solid #fed7aa', paddingTop: 4, marginTop: 4, textAlign: 'center' }}>
                  {real_data.substitute_list.slice(0, 6).map((s, i) => (
                    <span key={i} style={{ marginRight: 6 }}>· {s.name}（{s.distance}m）</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ★ 严谨度框架：客流锚点 */}
          {(real_data.traffic_anchors_1000m || 0) > 0 && (
            <div style={{ background: '#f0fdf4', borderRadius: 6, padding: '10px 14px', marginBottom: 8, border: '1px solid #bbf7d0' }}>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#166534', margin: '0 0 4px', textAlign: 'center' }}>🟢 客流锚点（商业活跃度参考 · 非竞品）</p>
              <div style={{ fontSize: 11, color: '#15803d', lineHeight: 1.6, textAlign: 'center' }}>
                200m: {formatCount(real_data.traffic_anchors_200m)} · 500m: {formatCount(real_data.traffic_anchors_500m)} · 1km: {formatCount(real_data.traffic_anchors_1000m)}
              </div>
              {real_data.traffic_anchor_list?.length > 0 && (
                <div style={{ fontSize: 11, color: '#15803d', lineHeight: 1.6, borderTop: '1px solid #bbf7d0', paddingTop: 4, marginTop: 4, textAlign: 'center' }}>
                  {real_data.traffic_anchor_list.slice(0, 8).map((a, i) => (
                    <span key={i} style={{ marginRight: 6 }}>· {a.name}（{a.distance}m）</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {real_data.hot_brands?.length > 0 && (
            <div style={{ background: '#f8fafc', borderRadius: 6, padding: '10px 14px', marginBottom: 8, border: '1px solid #e2e8f0' }}>
              <p style={{ fontSize: 13, fontWeight: 700, color: '#475569', margin: '0 0 4px', textAlign: 'center' }}>🏪 周边连锁品牌（含客流锚点品牌）</p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center' }}>
                {real_data.hot_brands.map((b, i) => (
                  <span key={i} style={{ background: '#fff', borderRadius: 4, padding: '3px 10px', fontSize: 12, color: '#334155', border: '1px solid #e2e8f0' }}>
                    <strong>{b.name}</strong> <span style={{ color: '#94a3b8' }}>×{b.count}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 数据质量摘要 */}
          {real_data.data_quality_notes?.length > 0 && (
            <div style={{ background: '#f8fafc', borderRadius: 6, padding: '8px 12px', marginBottom: 8, border: '1px solid #e2e8f0', fontSize: 11, color: '#64748b', lineHeight: 1.6, textAlign: 'center' }}>
              📊 数据质量：{real_data.data_quality_notes.map((note, i) => (
                <span key={i}>{note}{i < real_data.data_quality_notes.length - 1 ? ' · ' : ''}</span>
              ))}
            </div>
          )}

          <div style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.6, textAlign: 'center' }}>
            {real_data.city && real_data.district && <span>{real_data.city} {real_data.district} {real_data.township || ''}</span>}
            {real_data.business_areas?.length > 0 && <span style={{ marginLeft: 12 }}>商圈：{real_data.business_areas.join('、')}</span>}
            {real_data.nearby_roads?.length > 0 && <span style={{ marginLeft: 12 }}>道路：{real_data.nearby_roads.join('、')}</span>}
          </div>

          {/* POI Detail Lists — 周边各类POI名称与距离明细 */}
          {real_data.poi_lists && Object.keys(real_data.poi_lists).length > 0 && (
            <div style={{ marginTop: 12, borderTop: '1px solid #e2e8f0', paddingTop: 12 }}>
              <p style={{ fontSize: 15, fontWeight: 700, color: '#1e293b', margin: '0 0 8px', textAlign: 'center' }}>📋 周边业态明细</p>
              {[
                ['🏘️ 住宅', 'residential'], ['🏢 写字楼', 'office'], ['🏫 学校', 'schools'],
                ['🏥 医院', 'hospitals'], ['🛍️ 商场', 'shopping'], ['🍽️ 餐厅', 'restaurants'],
                ['☕ 茶饮', 'cafe_tea'], ['🍔 快餐', 'fast_food'], ['🥢 中餐', 'chinese_restaurants'],
                ['🍝 异国料理', 'foreign_restaurants'], ['🏨 酒店', 'hotels'], ['🚇 地铁', 'subway'],
                ['🚌 公交', 'bus'], ['🅿️ 停车', 'parking'], ['🏦 银行', 'banks'],
                ['🏪 便利店', 'convenience'], ['💊 药店', 'pharmacy'], ['💅 美容', 'beauty'], ['🐾 宠物', 'pets'], ['🍺 酒吧', 'bars'],
              ].map(([iconLabel, key]) => {
                const items = real_data.poi_lists[key]
                if (!items || items.length === 0) return null
                return (
                  <div key={key} style={{ marginBottom: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: '#334155' }}>{iconLabel} ×{items.length}</span>
                    <div style={{ fontSize: 12, color: '#475569', lineHeight: 1.7, marginTop: 2, wordBreak: 'break-all', overflowWrap: 'break-word' }}>
                      {items.slice(0, 8).map((poi, i) => (
                        <span key={i}>
                          {poi.name}
                          {poi.distance != null ? <span style={{ color: '#94a3b8' }}>({poi.distance}m)</span> : null}
                          {i < Math.min(items.length, 8) - 1 ? '、' : ''}
                        </span>
                      ))}
                      {items.length > 8 && <span style={{ color: '#94a3b8' }}> 等{items.length}个</span>}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* ═══════════ 第六块：各维度详细分析 ═══════════ */}
      {details && Object.keys(details).length > 0 && (
        <div style={{ background: '#fff', borderRadius: 6, border: '1px solid #e2e8f0', padding: 24, marginBottom: 16 }}>
          <h2 style={{ fontSize: 17, fontWeight: 900, margin: '0 0 12px', color: '#0f172a' }}>📝 各维度详细分析</h2>
          {Object.entries(detailLabels).map(([key, label]) => {
            if (!details[key]) return null
            const ds = dimension_scores?.find(d => d.key === key)
            const dimScore = ds ? Number(ds.score || 0) : 0
            const sc = dimScore >= 60 ? '#10b981' : dimScore >= 40 ? '#f59e0b' : '#ef4444'
            return (
              <div key={key} style={{ padding: '14px 16px', background: '#f8fafc', borderRadius: 8, borderLeft: `4px solid ${sc}`, marginBottom: 12 }}>
                <div style={{ marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span style={{ fontSize: 18 }}>{dimEmoji[key] || ''}</span>
                  <strong style={{ fontSize: 16, color: '#0f172a' }}>{label}</strong>
                  {dimScore > 0 && <span style={{ fontSize: 15, fontWeight: 900, color: sc, marginLeft: 12 }}>{dimScore} 分</span>}
                </div>
                <p style={{ fontSize: 15, color: '#475569', lineHeight: 1.7, textAlign: 'justify', whiteSpace: 'pre-wrap', margin: 0 }}>{_stripScore(details[key])}</p>
              </div>
            )
          })}
        </div>
      )}

      {/* ═══════════ 页脚 ═══════════ */}
      <div style={{ textAlign: 'center', padding: '12px 16px', background: '#fff', borderRadius: 8, border: '1px solid #e2e8f0', fontSize: 12, color: '#94a3b8' }}>
        以上分析仅供参考，不构成投资建议。最终选址决策请结合实地考察、商务谈判等多方面因素综合判断。
      </div>
    </div>
  )
}
