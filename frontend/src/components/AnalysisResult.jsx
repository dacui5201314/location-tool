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
  if (totalScore >= 75) text += '，整体选址条件良好'
  else if (totalScore >= 60) text += '，整体条件尚可但需权衡利弊'
  else text += '，整体条件需谨慎评估'
  return text + '。'
}

function formatCount(num) {
  if (num === undefined || num === null) return '—'
  return num
}

function ScoreRing({ score }) {
  const scoreColor = score >= 75 ? '#0f8a5f' : score >= 60 ? '#d79c31' : '#dc2626'
  const ringSize = 112
  const strokeW = 10
  const radius = (ringSize - strokeW) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - score / 100)
  const cx = ringSize / 2
  const cy = ringSize / 2
  return (
    <div className="mb-4 flex flex-col items-center">
      <div className="mb-2 text-xs font-medium text-slate-400">综合评分</div>
      <svg width={ringSize} height={ringSize} viewBox={`0 0 ${ringSize} ${ringSize}`}>
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke="#e7ece8" strokeWidth={strokeW} />
        <circle cx={cx} cy={cy} r={radius} fill="none" stroke={scoreColor} strokeWidth={strokeW}
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }} />
        <text x={cx} y={cy - 4} textAnchor="middle" dominantBaseline="central"
          fontSize="28" fontWeight="800" fill={scoreColor}>
          {score}
        </text>
        <text x={cx} y={cy + 16} textAnchor="middle" dominantBaseline="central"
          fontSize="10" fill="#9ca3af" fontWeight="500">
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
    <div className={`min-w-0 rounded-lg p-2.5 ${bgMap[highlight] || 'border border-slate-100 bg-slate-50'}`}>
      <div className="mb-1 flex items-center gap-1.5">
        <span className="text-sm">{icon}</span>
        <p className="truncate text-xs text-slate-500">{label}</p>
      </div>
      <div className="min-w-0">
        <p className={`truncate text-sm font-bold ${textMap[highlight] || 'text-slate-700'}`}>
          {val}
          {showDual && <span className="ml-1 text-[10px] font-normal text-slate-400">(共:{raw})</span>}
        </p>
        {sub && <p className="mt-0.5 text-[10px] text-slate-400">{sub}</p>}
      </div>
    </div>
  )
}

export default function AnalysisResult({ data }) {
  if (!data) return null

  const { advantages, disadvantages, summary, details, warning, real_data } = data

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

  const totalScore = Math.round(Object.keys(WEIGHTS).reduce((sum, key) => {
    return sum + (radarScores[key] || 0) * WEIGHTS[key]
  }, 0))

  const summaryText = generateRadarSummary(radarScores, totalScore)

  return (
    <div className="space-y-3 animate-in">
      {/* Disclaimer */}
      <div className="rounded-lg border border-amber-100 bg-amber-50 p-3 text-center">
        <p className="text-xs font-medium leading-5 text-amber-700">
          本工具不提供"推荐/不推荐"结论，各维度评分仅供参考，最终决策请结合实地考察
        </p>
      </div>

      {/* Summary Card */}
      <div className="report-card p-4">
        {warning && (
          <div className="mb-3 rounded-lg border border-red-100 bg-red-50 p-3 text-xs font-medium leading-5 text-red-700">
            风险提示：{warning}
          </div>
        )}

        {totalScore > 0 && (
          <>
            <ScoreRing score={totalScore} />
            {summaryText && (
              <p className="mx-auto mb-4 max-w-sm text-center text-xs leading-5 text-slate-500">
                {summaryText}
              </p>
            )}
          </>
        )}

        {summary && (
          <p className="report-soft mb-4 p-3 text-sm leading-6 text-slate-700">{summary}</p>
        )}

        <RadarChart scores={radarScores} />
      </div>

      {/* Real Data Card */}
      {real_data && (
        <div className="report-card p-4">
          <SectionHeader title="周边真实数据" color="blue" />
          <p className="-mt-1 mb-3 text-xs text-slate-400">200m / 500m / 1000m 三层半径实时采集</p>

          <div className="mb-4 grid grid-cols-2 gap-2 sm:grid-cols-3">
            <MetricBadge icon="🏘️" label="住宅小区"
              val={`${formatCount(real_data.stats_200m?.residential)} / ${formatCount(real_data.stats_500m?.residential)} / ${formatCount(real_data.stats_1000m?.residential)}`}
              sub="200m/500m/1000m" highlight="info"
              raw={real_data.raw_stats_1000m?.residential} />
            <MetricBadge icon="🏢" label="写字楼"
              val={`${formatCount(real_data.stats_200m?.office)} / ${formatCount(real_data.stats_500m?.office)} / ${formatCount(real_data.stats_1000m?.office)}`}
              sub="200m/500m/1000m" highlight="info"
              raw={real_data.raw_stats_1000m?.office} />
            <MetricBadge icon="🍽️" label="餐饮门店"
              val={`${formatCount(real_data.stats_200m?.restaurants)} / ${formatCount(real_data.stats_500m?.restaurants)} / ${formatCount(real_data.stats_1000m?.restaurants)}`}
              sub="200m/500m/1000m" highlight={real_data.stats_1000m?.restaurants > 100 ? 'high' : 'info'} />
            <MetricBadge icon="☕" label="咖啡茶饮"
              val={`${formatCount(real_data.stats_200m?.cafe_tea)} / ${formatCount(real_data.stats_500m?.cafe_tea)} / ${formatCount(real_data.stats_1000m?.cafe_tea)}`}
              sub="200m/500m/1000m" />
            <MetricBadge icon="🛍️" label="购物商场"
              val={`${formatCount(real_data.stats_200m?.shopping)} / ${formatCount(real_data.stats_500m?.shopping)} / ${formatCount(real_data.stats_1000m?.shopping)}`}
              sub="200m/500m/1000m"
              raw={real_data.raw_stats_1000m?.shopping} />
            <MetricBadge icon="🏫" label="学校"
              val={`${formatCount(real_data.stats_200m?.schools)} / ${formatCount(real_data.stats_500m?.schools)} / ${formatCount(real_data.stats_1000m?.schools)}`}
              sub="200m/500m/1000m"
              highlight={real_data.poi_counts?.schools > 5 ? 'good' : undefined}
              raw={real_data.raw_stats_1000m?.schools} />
            <MetricBadge icon="🏥" label="医院/诊所"
              val={`${formatCount(real_data.stats_200m?.hospitals)} / ${formatCount(real_data.stats_500m?.hospitals)} / ${formatCount(real_data.stats_1000m?.hospitals)}`}
              sub="200m/500m/1000m"
              highlight={real_data.poi_counts?.hospitals > 10 ? 'good' : 'info'}
              raw={real_data.raw_stats_1000m?.hospitals} />
            <MetricBadge icon="🚇" label="地铁站"
              val={`${formatCount(real_data.stats_200m?.subway)} / ${formatCount(real_data.stats_500m?.subway)} / ${formatCount(real_data.stats_1000m?.subway)}`}
              sub="200m/500m/1000m"
              highlight={!real_data.poi_counts?.subway ? 'high' : 'good'}
              raw={real_data.raw_stats_1000m?.subway} />
            <MetricBadge icon="🚌" label="公交站"
              val={`${formatCount(real_data.stats_200m?.bus)} / ${formatCount(real_data.stats_500m?.bus)} / ${formatCount(real_data.stats_1000m?.bus)}`}
              sub="200m/500m/1000m"
              highlight={real_data.poi_counts?.bus > 10 ? 'good' : undefined}
              raw={real_data.raw_stats_1000m?.bus} />
            <MetricBadge icon="🏨" label="酒店住宿"
              val={`${formatCount(real_data.stats_200m?.hotels)} / ${formatCount(real_data.stats_500m?.hotels)} / ${formatCount(real_data.stats_1000m?.hotels)}`}
              sub="200m/500m/1000m"
              raw={real_data.raw_stats_1000m?.hotels} />
            <MetricBadge icon="🏦" label="银行"
              val={`${formatCount(real_data.poi_counts?.banks)} 个`}
              raw={real_data.raw_poi_counts?.banks} />
            <MetricBadge icon="🅿️" label="停车场"
              val={`${formatCount(real_data.poi_counts?.parking)} 个`}
              raw={real_data.raw_poi_counts?.parking} />
          </div>
          <p className="mb-4 text-[10px] leading-4 text-slate-400">注：括号外为系统判定的有效商机数，已自动过滤诊所、培训机构、公司厂房等低关联干扰项</p>

          {/* Competitors */}
          {real_data.competitors_1000m > 0 && (
            <div className="mb-4 rounded-lg border border-orange-100 bg-orange-50 p-3">
              <p className="mb-1 text-sm font-bold text-orange-700">同类店铺密度</p>
              <div className="mb-2 space-y-0.5 text-xs leading-5 text-orange-600">
                <div>· 周边 200m 共 <strong className="text-base">{formatCount(real_data.competitors_200m)}</strong> 家</div>
                <div>· 周边 500m 共 <strong className="text-base">{formatCount(real_data.competitors_500m)}</strong> 家</div>
                <div>· 周边 1km 共 <strong className="text-base">{formatCount(real_data.competitors_1000m)}</strong> 家</div>
              </div>
              {real_data.competitor_list?.length > 0 && (
                <div className="mt-1 space-y-0.5 border-t border-orange-200 pt-2 text-xs leading-5 text-orange-600">
                  {real_data.competitor_list.slice(0, 10).map((c, i) => (
                    <div key={i}>· {c.name}（{c.distance}m）</div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Hot Brands */}
          {real_data.hot_brands?.length > 0 && (
            <div className="mb-4 rounded-lg border border-emerald-100 bg-emerald-50 p-3">
              <p className="mb-2 text-sm font-semibold text-emerald-700">周边连锁品牌</p>
              <div className="flex flex-wrap gap-1.5">
                {real_data.hot_brands.map((b, i) => (
                  <span key={i} className="inline-flex items-center gap-1 rounded-full border border-emerald-100 bg-white px-2 py-1 text-xs text-slate-600">
                    {b.name}
                    <span className="text-slate-400">x{b.count}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Location Info */}
          <div className="space-y-1 text-xs leading-5 text-slate-400">
            {real_data.city && real_data.district && (
              <div>{real_data.city} {real_data.district} {real_data.township || ''}</div>
            )}
            {real_data.business_areas?.length > 0 && (
              <div>商圈：{real_data.business_areas.join('、')}</div>
            )}
            {real_data.nearby_roads?.length > 0 && (
              <div>道路：{real_data.nearby_roads.join('、')}</div>
            )}
          </div>
        </div>
      )}

      {/* Adv/Disadv */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="report-card border-emerald-100 p-4">
          <SectionHeader title="优势" color="green" />
          {advantages && advantages.length > 0 ? (
            <ul className="space-y-2">
              {advantages.map((item, i) => (
                <li key={i} className="flex items-start text-sm leading-6 text-slate-700">
                  <span className="mr-2 mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500" />
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400">暂无数据</p>
          )}
        </div>

        <div className="report-card border-red-100 p-4">
          <SectionHeader title="劣势与风险" color="red" />
          {disadvantages && disadvantages.length > 0 ? (
            <ul className="space-y-2">
              {disadvantages.map((item, i) => (
                <li key={i} className="flex items-start text-sm leading-6 text-slate-700">
                  <span className="mr-2 mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-red-500" />
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-slate-400">暂无数据</p>
          )}
        </div>
      </div>

      {/* Detail Analysis */}
      {details && Object.keys(details).length > 0 && (
        <div className="report-card p-4">
          <SectionHeader title="各维度详细分析" color="gray" />
          <p className="-mt-1 mb-4 text-xs text-slate-400">各维度独立分析，综合评分展示于上方雷达图</p>
          <div className="space-y-3">
            {Object.entries(detailLabels).map(([key, label]) => {
              if (!details[key]) return null
              const pd = parsedDetails[key] || { score: 0, text: String(details[key]) }
              return (
                <div key={key} className="border-b border-slate-100 pb-3 last:border-b-0">
                  <h4 className="mb-1 text-sm font-semibold text-slate-800">
                    {label}
                  </h4>
                  <p className="whitespace-pre-wrap text-sm leading-6 text-slate-600">{pd.text}</p>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Footer Disclaimer */}
      <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-center">
        <p className="text-xs leading-5 text-slate-500">
          以上分析仅供参考，不构成投资建议。最终选址决策请结合实地考察、商务谈判等多方面因素综合判断。
        </p>
      </div>
    </div>
  )
}
