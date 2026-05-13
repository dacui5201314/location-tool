import { useState, useRef, useCallback, useEffect } from 'react'
import RadarChart from './RadarChart'
import useReportExport from '../hooks/useReportExport'
import { getAssetUrl } from '../services/api'

function formatDate() {
  const d = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

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

const detailColors = {
  population_density: '#6366f1',
  traffic_accessibility: '#0891b2',
  traffic_flow: '#2563eb',
  consumer_profile: '#7c3aed',
  competition: '#dc2626',
  complementary_businesses: '#059669',
  category_advantage: '#ea580c',
  cost_estimate: '#0891b2',
  revenue_estimation: '#4f46e5',
  site_suggestion: '#1e40af',
}

const detailEmoji = {
  population_density: '🏘️',
  traffic_accessibility: '🚇',
  traffic_flow: '🚶',
  consumer_profile: '👥',
  competition: '⚔️',
  complementary_businesses: '🔗',
  category_advantage: '🎯',
  cost_estimate: '💰',
  revenue_estimation: '💵',
  site_suggestion: '📋',
}

function parseDetail(text) {
  if (!text) return { score: 0, text: '' }
  const s = String(text)
  const m = s.match(/评分[：:]\s*(\d{1,3})|(\d{1,3})\s*分\s*$/)
  const score = m ? parseInt(m[1] || m[2]) : 0
  const clean = s.replace(/[，,]?\s*评分[：:]\s*\d{1,3}\s*分?\s*$/, '').replace(/\d{1,3}\s*分\s*$/, '').trim()
  return { score, text: clean }
}

function buildRadarScores(dimensionScores) {
  // ★ 直接从后端 dimension_scores 数组读取，不再从 details 文本正则解析
  const scores = {}
  if (Array.isArray(dimensionScores)) {
    dimensionScores.forEach(d => { if (d.key) scores[d.key] = Number(d.score || 0) })
  }
  return scores
}

function formatCount(num) {
  if (num === undefined || num === null) return '—'
  return num
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

const REPORT_WIDTH = 800

function MetaItem({ icon, label, value, dim, accent, highlight, span }) {
  return (
    <div style={{
      padding: '12px 18px',
      borderBottom: '1px solid #f1f5f9',
      borderRight: '1px solid #f1f5f9',
      ...(span ? { gridColumn: '1 / -1' } : {}),
    }}>
      <div style={{ fontSize: 11, color: '#8b9cb3', marginBottom: 4, display: 'flex', alignItems: 'center', gap: 4 }}>
        {icon} {label}
      </div>
      <div style={{
        fontSize: 15, fontWeight: highlight ? 800 : 600,
        color: highlight ? '#dc2626' : accent ? '#1e3a5f' : dim ? '#5a6d80' : '#1a1a2e',
        wordBreak: 'break-all', overflowWrap: 'break-word', lineHeight: 1.5,
      }}>
        {value || '—'}
      </div>
    </div>
  )
}

function SectionBox({ children, style }) {
  return (
    <div data-section style={{ breakInside: 'avoid', marginBottom: 22, ...style }}>
      {children}
    </div>
  )
}

export default function PdfExport({ selectedLocation, result, businessType, brandName }) {
  const reportRef = useRef(null)
  const { exportPdf, ExportModal, loading: exporting, toast, showToast } = useReportExport()
  const [pdfConfig, setPdfConfig] = useState({ logo_url: '', footer_text: '' })

  // ★ 拉取管理员自定义的 PDF 品牌配置和二维码，确保预览与导出 PDF 一致
  useEffect(() => {
    fetch('/api/admin/pdf-config')
      .then(r => r.ok ? r.json() : {})
      .then(cfg => setPdfConfig({ logo_url: cfg.logo_url || '', footer_text: cfg.footer_text || '' }))
      .catch(() => {})
  }, [])

  if (!result) return null

  const { advantages, disadvantages, summary, details, warning, real_data } = result
  const hasRealData = real_data && Object.keys(real_data).length > 0

  // ★ 严谨度：仅认 rigor_enabled
  const hasRigor = real_data?.rigor_enabled === true
  const dc200 = hasRigor ? (real_data.direct_competitors_200m ?? 0) : (real_data?.competitors_200m ?? 0)
  const dc500 = hasRigor ? (real_data.direct_competitors_500m ?? 0) : (real_data?.competitors_500m ?? 0)
  const dc1000 = hasRigor ? (real_data.direct_competitors_1000m ?? 0) : (real_data?.competitors_1000m ?? 0)
  const dcList = hasRigor ? (real_data.direct_competitor_list || []) : (real_data?.competitor_list || [])

  const sectionH2 = (color = '#1a1a2e') => ({
    fontSize: 17, color, borderLeft: `4px solid ${color}`, paddingLeft: 12,
    margin: '0 0 16px 0', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8,
  })

  const handleExport = useCallback(async () => {
    const filename = `选址分析报告_${selectedLocation?.name || 'report'}_${new Date().toISOString().slice(0, 10)}.pdf`
    await exportPdf({
      data: result,
      meta: {
        address: selectedLocation?.address || selectedLocation?.name || '',
        brandName,
        businessType,
        storeSize: '',
        date: new Date().toISOString(),
      },
      filename,
    })
  }, [selectedLocation, exportPdf, result, brandName, businessType])

  const report = (
    <div ref={reportRef} style={{
      fontFamily: '"Microsoft YaHei", "PingFang SC", "SimHei", "Noto Sans SC", sans-serif',
      color: '#1a1a2e', width: `${REPORT_WIDTH}px`, padding: '40px 44px', background: '#fff',
      position: 'relative',
    }}>
      {/* ===== HEADER (not a section - combined with meta) ===== */}
      <div data-section style={{ breakInside: 'avoid', marginBottom: 20 }}>
        <div style={{
          textAlign: 'center', borderBottom: '3px solid #1e40af', paddingBottom: 22, marginBottom: 24,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 12, marginBottom: 8 }}>
            {pdfConfig.logo_url ? (
              <img src={getAssetUrl(pdfConfig.logo_url)} alt="品牌标识" style={{ width: 38, height: 38, objectFit: 'contain', borderRadius: 4 }} />
            ) : null}
            <h1 style={{ fontSize: 28, color: '#1e40af', margin: 0, fontWeight: 700, letterSpacing: 3 }}>
              📍 址得选 AI选址分析报告
            </h1>
          </div>
          <p style={{ fontSize: 13, color: '#888', margin: 0 }}>
            址得选 | 基于实时 POI 数据 + AI 多维度分析 | {formatDate()}
          </p>
        </div>

        {/* META — 现代化信息卡片 */}
        <div style={{
          background: '#fff', borderRadius: 10, padding: 0,
          border: '1px solid #e8ecf1', overflow: 'hidden',
        }}>
          <div style={{
            background: 'linear-gradient(135deg, #f8fafd 0%, #eef2ff 100%)',
            padding: '12px 18px', borderBottom: '1px solid #e8ecf1',
            fontSize: 14, fontWeight: 700, color: '#1e3a5f',
            display: 'flex', alignItems: 'center', gap: 8,
          }}>
            📋 选址信息概要
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 0, fontSize: 13 }}>
            <MetaItem icon="📍" label="分析地址" value={selectedLocation.name} />
            <MetaItem icon="📌" label="详细地址" value={selectedLocation.address || selectedLocation.name} dim />
            {businessType && (
              <MetaItem icon="🏪" label="选址业态" value={businessType} accent />
            )}
            {brandName && (
              <MetaItem icon="🏷️" label="分析品牌" value={brandName} accent highlight />
            )}
            {hasRealData && real_data.city && (
              <MetaItem icon="🏙️" label="所属区域" value={`${real_data.city} ${real_data.district || ''} ${real_data.township || ''}`} dim />
            )}
            <MetaItem icon="🌐" label="经纬度" value={`${selectedLocation?.location?.lng?.toFixed(6) ?? '—'}, ${selectedLocation?.location?.lat?.toFixed(6) ?? '—'}`} dim />
            {hasRealData && real_data.business_areas?.length > 0 && (
              <MetaItem icon="🏬" label="周边商圈" value={real_data.business_areas.join('、')} span />
            )}
            {hasRealData && real_data.nearby_roads?.length > 0 && (
              <MetaItem icon="🛣️" label="周边道路" value={real_data.nearby_roads.join('、')} span />
            )}
          </div>
        </div>
      </div>

      {/* ===== DISCLAIMER ===== */}
      <div data-section style={{ breakInside: 'avoid', marginBottom: 14 }}>
        <div style={{
          display: 'flex', alignItems: 'flex-start', gap: 8,
          padding: '10px 14px', borderRadius: 8,
          background: '#fffbeb', border: '1px solid #fde68a',
          fontSize: 12, lineHeight: 1.6, color: '#92400e',
        }}>
          <span style={{ flexShrink: 0, fontSize: 14 }}>💡</span>
          <span>本工具不提供"推荐/不推荐"结论，各维度评分仅供参考，最终决策请结合实地考察与多方因素综合判断。</span>
        </div>
      </div>

      {warning && (
        <div data-section style={{ breakInside: 'avoid', marginBottom: 14 }}>
          <div style={{
            display: 'flex', alignItems: 'flex-start', gap: 8,
            padding: '10px 14px', borderRadius: 8,
            background: '#fef2f2', border: '1px solid #fecaca',
            fontSize: 12, lineHeight: 1.6, color: '#991b1b',
          }}>
            <span style={{ flexShrink: 0, fontSize: 14 }}>⚠️</span>
            <span><strong style={{ fontWeight: 800 }}>风险提示：</strong>{warning}</span>
          </div>
        </div>
      )}

      {/* ===== SUMMARY + SCORE ===== */}
      {summary && (() => {
        const ts = result.score || result.overall_score || 0
        const scores = buildRadarScores(result.dimension_scores)
        const scoreColor = ts >= 60 ? '#16a34a' : ts >= 40 ? '#ca8a04' : '#dc2626'
        const ringSize = 140
        const strokeW = 12
        const radius = (ringSize - strokeW) / 2
        const circumference = 2 * Math.PI * radius
        const offset = circumference * (1 - ts / 100)
        const cx = ringSize / 2
        const cy = ringSize / 2
        const summaryText = generateRadarSummary(scores, ts)
        return (
          <SectionBox>
            <div style={{
              padding: '20px 24px', borderRadius: 8,
              background: '#f7f8fa', border: '1px solid #e2e8f0',
            }}>
              {/* Score + Summary side by side */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 32, marginBottom: 16 }}>
                {ts > 0 && (
                  <div style={{ flexShrink: 0, textAlign: 'center' }}>
                    <div style={{ fontSize: 18, fontWeight: 700, color: '#1a1a2e', marginBottom: 18 }}>
                      📊 综合评分
                    </div>
                    <svg width={ringSize} height={ringSize} viewBox={`0 0 ${ringSize} ${ringSize}`}>
                      <circle cx={cx} cy={cy} r={radius} fill="none" stroke="#e5e7eb" strokeWidth={strokeW} />
                      <circle cx={cx} cy={cy} r={radius} fill="none" stroke={scoreColor} strokeWidth={strokeW}
                        strokeDasharray={circumference} strokeDashoffset={offset}
                        strokeLinecap="round" transform={`rotate(-90 ${cx} ${cy})`} />
                      <text x={cx} y={cy - 6} textAnchor="middle" dominantBaseline="central"
                        fontSize="38" fontWeight="900" fill={scoreColor}>{ts}</text>
                      <text x={cx} y={cy + 18} textAnchor="middle" dominantBaseline="central"
                        fontSize="11" fill="#9ca3af" fontWeight="600">/ 100</text>
                    </svg>
                  </div>
                )}
                <div style={{ flex: 1 }}>
                  {summaryText && (
                    <p style={{ fontSize: 14, color: '#555', lineHeight: 2, textAlign: 'center', margin: '0 0 12px 0' }}>
                      {summaryText}
                    </p>
                  )}
                  <div style={{ fontWeight: 700, color: '#1a1a2e', marginBottom: 6, fontSize: 16 }}>
                    📋 分析摘要
                  </div>
                  <div style={{ fontSize: 13, color: '#334155', lineHeight: 1.9, textAlign: 'justify' }}>{summary}</div>
                </div>
              </div>
            </div>
          </SectionBox>
        )
      })()}

      {/* ===== RADAR CHART ===== */}
      {details && (
        <SectionBox style={{ textAlign: 'center' }}>
          <RadarChart scores={buildRadarScores(result.dimension_scores)} />
        </SectionBox>
      )}

      {/* ===== REAL DATA ===== */}
      {hasRealData && (
        <SectionBox>
          <h2 style={sectionH2('#2563eb')}>📊 周边真实数据（200m / 500m / 1000m 三层半径采集）</h2>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
            {[
              ['🏘️', '住宅小区', `${formatCount(real_data.stats_200m?.residential)} / ${formatCount(real_data.stats_500m?.residential)} / ${formatCount(real_data.stats_1000m?.residential)}`, '200m / 500m / 1000m', '#2563eb', real_data.raw_stats_1000m?.residential],
              ['🏢', '写字楼', `${formatCount(real_data.stats_200m?.office)} / ${formatCount(real_data.stats_500m?.office)} / ${formatCount(real_data.stats_1000m?.office)}`, '200m / 500m / 1000m', '#2563eb', real_data.raw_stats_1000m?.office],
              ['🍽️', '餐饮门店', `${formatCount(real_data.stats_200m?.restaurants)} / ${formatCount(real_data.stats_500m?.restaurants)} / ${formatCount(real_data.stats_1000m?.restaurants)}`, '200m / 500m / 1000m', (real_data.stats_1000m?.restaurants || 0) > 100 ? '#dc2626' : '#2563eb'],
              ['☕', '咖啡茶饮', `${formatCount(real_data.stats_200m?.cafe_tea)} / ${formatCount(real_data.stats_500m?.cafe_tea)} / ${formatCount(real_data.stats_1000m?.cafe_tea)}`, '200m / 500m / 1000m', '#334155'],
              ['🛍️', '购物商场', `${formatCount(real_data.stats_200m?.shopping)} / ${formatCount(real_data.stats_500m?.shopping)} / ${formatCount(real_data.stats_1000m?.shopping)}`, '200m / 500m / 1000m', '#334155', real_data.raw_stats_1000m?.shopping],
              ['🏫', '学校', `${formatCount(real_data.stats_200m?.schools)} / ${formatCount(real_data.stats_500m?.schools)} / ${formatCount(real_data.stats_1000m?.schools)}`, '200m / 500m / 1000m', (real_data.poi_counts?.schools || 0) > 5 ? '#16a34a' : '#334155', real_data.raw_stats_1000m?.schools],
              ['🏥', '医院/诊所', `${formatCount(real_data.stats_200m?.hospitals)} / ${formatCount(real_data.stats_500m?.hospitals)} / ${formatCount(real_data.stats_1000m?.hospitals)}`, '200m / 500m / 1000m', (real_data.poi_counts?.hospitals || 0) > 10 ? '#16a34a' : '#2563eb', real_data.raw_stats_1000m?.hospitals],
              ['🚇', '地铁站', `${formatCount(real_data.stats_200m?.subway)} / ${formatCount(real_data.stats_500m?.subway)} / ${formatCount(real_data.stats_1000m?.subway)}`, '200m / 500m / 1000m', !real_data.poi_counts?.subway ? '#dc2626' : '#16a34a', real_data.raw_stats_1000m?.subway],
              ['🚌', '公交站', `${formatCount(real_data.stats_200m?.bus)} / ${formatCount(real_data.stats_500m?.bus)} / ${formatCount(real_data.stats_1000m?.bus)}`, '200m / 500m / 1000m', '#334155', real_data.raw_stats_1000m?.bus],
              ['🏨', '酒店住宿', `${formatCount(real_data.stats_200m?.hotels)} / ${formatCount(real_data.stats_500m?.hotels)} / ${formatCount(real_data.stats_1000m?.hotels)}`, '200m / 500m / 1000m', '#334155', real_data.raw_stats_1000m?.hotels],
              ['🏦', '银行', `${formatCount(real_data.poi_counts?.banks)} 个`, null, '#334155', real_data.raw_poi_counts?.banks],
              ['🅿️', '停车场', `${formatCount(real_data.poi_counts?.parking)} 个`, null, '#334155', real_data.raw_poi_counts?.parking],
            ].map(([icon, label, val, sub, color, raw], i) => {
              const showRaw = raw !== undefined && raw !== null && raw !== val
              return (
              <div key={i} style={{
                flex: '0 0 auto', width: 'calc(25% - 6px)', padding: '12px 8px',
                background: color === '#dc2626' ? '#fef2f2' : color === '#16a34a' ? '#f0fdf4' : color === '#2563eb' ? '#eff6ff' : '#f7f8fa',
                borderRadius: 8, textAlign: 'center', boxSizing: 'border-box',
              }}>
                <div style={{ fontSize: 11, color: '#888', marginBottom: 3 }}>{icon} {label}</div>
                <div style={{ fontSize: 15, fontWeight: 700, color }}>{val}{showRaw ? <span style={{ fontSize: 9, fontWeight: 400, color: '#aaa', marginLeft: 2 }}>(共:{raw})</span> : ''}</div>
                {sub && <div style={{ fontSize: 10, color: '#aaa', marginTop: 2 }}>{sub}</div>}
              </div>
            )})}
          </div>
          <div style={{ fontSize: 9, color: '#aaa', textAlign: 'center', marginBottom: 14, lineHeight: 1.6 }}>
            注：括号外为系统判定的有效商机数，已自动过滤诊所、培训机构、公司厂房等低关联干扰项
          </div>

          {/* ★ 严谨度提示 */}
          {!hasRigor && (
            <div style={{ background: '#fffbeb', borderRadius: 8, padding: '10px 16px', marginBottom: 12, border: '1px solid #fde68a', fontSize: 12, color: '#92400e', textAlign: 'center', lineHeight: 1.6 }}>
              ⚠️ 该业态暂无完整严谨分类规则，竞品结果仅供兼容参考。如需精准竞品分析，请联系管理员补充业态规则。
            </div>
          )}

          {/* ★ 严谨度：直接竞品 */}
          {(hasRigor || dc1000 > 0) && (
            <div style={{ background: hasRigor ? '#fef2f2' : '#f8fafc', borderRadius: 8, padding: '14px 20px', marginBottom: 12, border: hasRigor ? '1px solid #fecaca' : '1px solid #e2e8f0' }}>
              <div style={{ fontSize: 14, fontWeight: 700, color: hasRigor ? '#dc2626' : '#64748b', marginBottom: 8, textAlign: 'center' }}>
                {hasRigor ? '🎯 直接竞品（同类业态 · 严谨口径）' : '📋 旧口径竞品参考（非严谨直接竞品）'}
              </div>
              <div style={{ fontSize: 13, color: hasRigor ? '#9a3412' : '#64748b', lineHeight: 2.2, marginBottom: 6, textAlign: 'center' }}>
                200m: <strong style={{ fontSize: 18, color: hasRigor ? '#dc2626' : '#475569' }}>{formatCount(dc200)}</strong> ·
                500m: <strong style={{ fontSize: 18, color: hasRigor ? '#dc2626' : '#475569' }}>{formatCount(dc500)}</strong> ·
                1km: <strong style={{ fontSize: 18, color: hasRigor ? '#dc2626' : '#475569' }}>{formatCount(dc1000)}</strong>
              </div>
              {dcList.length > 0 ? (
                <div style={{ fontSize: 11, color: hasRigor ? '#9a3412' : '#64748b', lineHeight: 2, borderTop: '1px solid #e2e8f0', paddingTop: 8, textAlign: 'center' }}>
                  {dcList.slice(0, 12).map((c, i) => (
                    <span key={i} style={{ marginRight: 14 }}>· {c.name}（{c.distance}m）</span>
                  ))}
                </div>
              ) : hasRigor && (
                <div style={{ fontSize: 11, color: '#9a3412', lineHeight: 2, borderTop: '1px solid #fecaca', paddingTop: 8, textAlign: 'center' }}>
                  1km内暂无直接竞品
                </div>
              )}
              {!hasRigor && (
                <div style={{ fontSize: 10, color: '#b45309', textAlign: 'center', marginTop: 4, lineHeight: 1.5 }}>
                  ⚠️ 旧口径统计，仅供兼容参考，需人工核验直接竞品。
                </div>
              )}
            </div>
          )}

          {/* ★ 严谨度：替代消费压力 */}
          {(real_data.substitute_competitors_1000m || 0) > 0 && (
            <div style={{ background: '#fff7ed', borderRadius: 8, padding: '12px 20px', marginBottom: 12, border: '1px solid #fed7aa' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#c2410c', marginBottom: 6, textAlign: 'center' }}>🔶 替代消费压力（非同业态）</div>
              <div style={{ fontSize: 11, color: '#9a3412', lineHeight: 1.8, textAlign: 'center' }}>
                200m: {formatCount(real_data.substitute_competitors_200m)} · 500m: {formatCount(real_data.substitute_competitors_500m)} · 1km: {formatCount(real_data.substitute_competitors_1000m)}
              </div>
              {real_data.substitute_list?.length > 0 && (
                <div style={{ fontSize: 10, color: '#9a3412', lineHeight: 1.8, borderTop: '1px solid #fed7aa', paddingTop: 6, marginTop: 4, textAlign: 'center' }}>
                  {real_data.substitute_list.slice(0, 6).map((s, i) => (
                    <span key={i} style={{ marginRight: 8 }}>· {s.name}（{s.distance}m）</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* ★ 严谨度：客流锚点 */}
          {(real_data.traffic_anchors_1000m || 0) > 0 && (
            <div style={{ background: '#f0fdf4', borderRadius: 8, padding: '12px 20px', marginBottom: 12, border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#166534', marginBottom: 6, textAlign: 'center' }}>🟢 客流锚点（商业活跃度 · 非竞品）</div>
              <div style={{ fontSize: 11, color: '#15803d', lineHeight: 1.8, textAlign: 'center' }}>
                200m: {formatCount(real_data.traffic_anchors_200m)} · 500m: {formatCount(real_data.traffic_anchors_500m)} · 1km: {formatCount(real_data.traffic_anchors_1000m)}
              </div>
              {real_data.traffic_anchor_list?.length > 0 && (
                <div style={{ fontSize: 10, color: '#15803d', lineHeight: 1.8, borderTop: '1px solid #bbf7d0', paddingTop: 6, marginTop: 4, textAlign: 'center' }}>
                  {real_data.traffic_anchor_list.slice(0, 8).map((a, i) => (
                    <span key={i} style={{ marginRight: 8 }}>· {a.name}（{a.distance}m）</span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Hot Brands (客流锚点品牌标记) */}
          {real_data.hot_brands?.length > 0 && (
            <div style={{ background: '#f8fafc', borderRadius: 8, padding: '12px 20px', marginBottom: 12, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#475569', marginBottom: 8, textAlign: 'center' }}>🏪 周边连锁品牌（含客流锚点品牌）</div>
              <div style={{ fontSize: 11, lineHeight: 2.2, textAlign: 'center' }}>
                {real_data.hot_brands.map((b, i) => (
                  <span key={i} style={{ marginRight: 16, color: '#333', whiteSpace: 'nowrap' }}>
                    <strong>{b.name}</strong> ×{b.count}
                    {b.min_distance != null && <span style={{ color: '#888' }}>（最近{b.min_distance}m）</span>}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* 数据质量摘要 */}
          {real_data.data_quality_notes?.length > 0 && (
            <div style={{ background: '#f8fafc', borderRadius: 6, padding: '6px 12px', marginBottom: 10, border: '1px solid #e2e8f0', fontSize: 10, color: '#64748b', textAlign: 'center', lineHeight: 1.6 }}>
              📊 数据质量：{real_data.data_quality_notes.map((note, i) => (
                <span key={i}>{note}{i < real_data.data_quality_notes.length - 1 ? ' · ' : ''}</span>
              ))}
            </div>
          )}

          {/* Location Info */}
          <div style={{ fontSize: 12, color: '#888', lineHeight: 2, textAlign: 'center' }}>
            {real_data.city && real_data.district && (
              <span style={{ marginRight: 16 }}>📍 {real_data.city} {real_data.district} {real_data.township || ''}</span>
            )}
            {real_data.business_areas?.length > 0 && (
              <span style={{ marginRight: 16 }}>🏬 商圈：{real_data.business_areas.join('、')}</span>
            )}
            {real_data.nearby_roads?.length > 0 && (
              <span>🛣️ 道路：{real_data.nearby_roads.join('、')}</span>
            )}
          </div>

          {/* POI Detail Lists — 周边各类POI名称与距离明细（独立页，卡片式） */}
          {real_data.poi_lists && Object.keys(real_data.poi_lists).length > 0 && (
            <div data-section style={{ breakBefore: 'page', breakInside: 'avoid', marginBottom: 20, paddingTop: 10 }}>
              <h2 style={sectionH2('#1a1a2e')}>📋 周边业态明细（名称 + 距离）</h2>
              <p style={{ fontSize: 10, color: '#94a3b8', textAlign: 'center', margin: '0 0 10px' }}>
                以下为高德地图实时采集的各类 POI 详细清单 · 最多展示前 8 条
              </p>
              {[
                ['🏘️ 住宅小区', 'residential'], ['🏢 写字楼', 'office'], ['🏫 学校', 'schools'],
                ['🏥 医院', 'hospitals'], ['🛍️ 购物商场', 'shopping'], ['🍽️ 餐厅', 'restaurants'],
                ['☕ 咖啡茶饮', 'cafe_tea'], ['🍔 快餐', 'fast_food'], ['🥢 中餐厅', 'chinese_restaurants'],
                ['🍝 异国料理', 'foreign_restaurants'], ['🏨 酒店', 'hotels'], ['🚇 地铁站', 'subway'],
                ['🚌 公交站', 'bus'], ['🅿️ 停车场', 'parking'], ['🏦 银行', 'banks'],
                ['🏪 便利店', 'convenience'], ['💊 药店', 'pharmacy'], ['💅 美容', 'beauty'], ['🐾 宠物', 'pets'], ['🍺 酒吧', 'bars'],
              ].map(([iconLabel, key]) => {
                const items = real_data.poi_lists[key]
                if (!items || items.length === 0) return null
                return (
                  <div key={key} style={{ marginBottom: 6 }}>
                    <span style={{ fontSize: 12, fontWeight: 700, color: '#334155' }}>{iconLabel} ×{items.length}</span>
                    <div style={{ fontSize: 11, color: '#475569', lineHeight: 1.7, wordBreak: 'break-all', overflowWrap: 'break-word' }}>
                      {items.slice(0, 8).map((poi, i) => (
                        <span key={i}>
                          {poi.name}
                          {poi.distance != null ? <span style={{ color: '#94a3b8' }}>（{poi.distance}m）</span> : null}
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
        </SectionBox>
      )}

      {/* ===== ADVANTAGES ===== */}
      <SectionBox>
        <h2 style={sectionH2('#16a34a')}>✅ 优势</h2>
        {(advantages || []).length > 0 ? (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {advantages.map((a, i) => (
              <li key={i} style={{
                padding: '8px 14px', fontSize: 13, lineHeight: 1.8,
                background: i % 2 === 0 ? '#fafafa' : 'transparent', borderRadius: 6,
              }}>
                <span style={{ color: '#16a34a', fontWeight: 700, marginRight: 8 }}>&#9656;</span> {a}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ fontSize: 13, color: '#999', textAlign: 'center' }}>暂无数据</p>
        )}
      </SectionBox>

      {/* ===== DISADVANTAGES ===== */}
      <SectionBox>
        <h2 style={sectionH2('#dc2626')}>⚠️ 劣势与风险</h2>
        {(disadvantages || []).length > 0 ? (
          <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
            {disadvantages.map((d, i) => (
              <li key={i} style={{
                padding: '8px 14px', fontSize: 13, lineHeight: 1.8,
                background: i % 2 === 0 ? '#fafafa' : 'transparent', borderRadius: 6,
              }}>
                <span style={{ color: '#dc2626', fontWeight: 700, marginRight: 8 }}>&#9656;</span> {d}
              </li>
            ))}
          </ul>
        ) : (
          <p style={{ fontSize: 13, color: '#999', textAlign: 'center' }}>暂无数据</p>
        )}
      </SectionBox>

      {/* ===== DETAILS ===== */}
      {details && Object.keys(details).length > 0 && (
        <SectionBox>
          <h2 style={sectionH2('#1a1a2e')}>📋 各维度详细分析</h2>
          {Object.entries(detailLabels).map(([key, label]) => {
            const val = details[key]
            if (!val) return null
            const pd = parseDetail(val)
            const color = detailColors[key] || '#6b7280'
            const emoji = detailEmoji[key] || ''
            return (
              <div key={key} style={{
                marginBottom: 12, padding: '14px 18px',
                background: '#fafafa', borderRadius: 8,
                borderLeft: `4px solid ${color}`,
              }}>
                <h3 style={{ fontSize: 14, color, margin: '0 0 8px 0', fontWeight: 700 }}>
                  {emoji} {label}
                  {pd.score > 0 && (
                    <span style={{
                      marginLeft: 10, fontSize: 13, fontWeight: 800,
                      color: pd.score >= 60 ? '#16a34a' : pd.score >= 40 ? '#ca8a04' : '#dc2626',
                    }}>
                      {pd.score} 分
                    </span>
                  )}
                </h3>
                <p style={{ fontSize: 13, color: '#4b5563', lineHeight: 1.8, margin: 0, whiteSpace: 'pre-wrap' }}>
                  {pd.text}
                </p>
              </div>
            )
          })}
        </SectionBox>
      )}

      {/* ===== FOOTER DISCLAIMER ===== */}
      <div data-section style={{ breakInside: 'avoid', marginBottom: 14 }}>
        <div style={{
          display: 'flex', justifyContent: 'center', alignItems: 'center',
          textAlign: 'center', padding: '12px 18px',
          background: '#f7f8fa', borderRadius: 8, border: '1px solid #e5e7eb',
          fontSize: 11, color: '#888', lineHeight: 2,
        }}>
          ⚠️ 以上分析仅供参考，不构成投资建议。最终选址决策请结合实地考察、商务谈判等多方面因素综合判断。
        </div>
      </div>

      {/* ===== FOOTER — 品牌自定义页脚 ===== */}
      <div data-section style={{ breakInside: 'avoid' }}>
        <div style={{
          textAlign: 'center', fontSize: 11, color: '#aaa',
          borderTop: '1px solid #e5e7eb', paddingTop: 16, marginTop: 12,
          lineHeight: 2,
        }}>
          <p style={{ margin: 0, fontWeight: 600, color: '#334155' }}>
            {pdfConfig.footer_text || 'AI 选址分析 · 商业选址初筛参考'}
          </p>
          <p style={{ margin: '4px 0 0', fontSize: 10, color: '#94a3b8' }}>
            📄 本报告由 AI 选址分析工具基于实时 POI 数据自动生成 | 仅供参考
          </p>
        </div>
      </div>
    </div>
  )

  return (
    <>
      {/* Toast */}
      {toast && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[300] rounded-full bg-slate-800 text-white text-xs px-5 py-2.5 shadow-xl"
          style={{ whiteSpace: 'nowrap' }}>
          {toast}
        </div>
      )}

      {/* 统一计费 Modal */}
      <ExportModal />

      <button
        onClick={handleExport}
        disabled={exporting}
        className="w-full py-3 rounded-xl font-semibold text-sm border
          border-gray-300 text-gray-700 bg-white
          hover:bg-gray-50 hover:border-gray-400
          active:bg-gray-100
          disabled:opacity-50 disabled:cursor-not-allowed
          transition-colors duration-150 flex items-center justify-center gap-2"
      >
        {exporting ? (
          <>
            <span className="inline-block w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
            正在生成 PDF...
          </>
        ) : (
          <>📄 导出 PDF 报告</>
        )}
      </button>
    </>
  )
}
