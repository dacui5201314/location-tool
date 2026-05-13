import html2pdf from 'html2pdf.js'

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function asList(value, limit = 5) {
  if (Array.isArray(value)) return value.filter(Boolean).slice(0, limit)
  if (!value) return []
  return String(value).split(/[，,\n]/).map(s => s.trim()).filter(Boolean).slice(0, limit)
}

function stripScore(value = '') {
  return String(value).replace(/[，,]?\s*评分[：:]\s*\d{1,3}\s*分?\s*$/, '').replace(/\d{1,3}\s*分\s*$/, '').trim()
}

function scoreColor(score = 0) {
  if (score >= 60) return '#10b981'
  if (score >= 40) return '#f59e0b'
  return '#ef4444'
}

function _fmt(n) { return n === undefined || n === null ? '-' : n }

export async function exportElementToPDF(element, filename) {
  if (!element) throw new Error('No DOM element to export')
  const opt = {
    margin: [0, 0, 0, 0],
    filename,
    image: { type: 'jpeg', quality: 1.0 },
    html2canvas: {
      scale: 3,
      useCORS: true,
      allowTaint: false,
      backgroundColor: '#f8fafc',
      logging: false,
      width: 800,
      windowWidth: 800,
    },
    jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
    pagebreak: { mode: ['css', 'legacy'] },
  }
  await html2pdf().set(opt).from(element).save()
}

export async function exportDataToPDF(reportData, meta = {}, qrcodeUrl = '', pdfConfig = {}, filename = '') {
  const { address = '', brandName = '', businessType = '', storeSize = '', date = '' } = meta
  const htmlString = buildFullReportHTML(reportData, { address, brandName, businessType, storeSize, date }, qrcodeUrl, pdfConfig)

  const iframe = document.createElement('iframe')
  iframe.style.display = 'none'
  document.body.appendChild(iframe)
  const iframeDoc = iframe.contentWindow.document
  iframeDoc.open()
  iframeDoc.write(htmlString)
  iframeDoc.close()

  try {
    await new Promise(r => setTimeout(r, 1500))
    const safeName = (brandName || businessType || 'report').replace(/[\\/:*?"<>|]/g, '').slice(0, 30)
    const d = date?.slice(0, 10) || new Date().toISOString().slice(0, 10)
    const opt = {
      margin: [0, 0, 0, 0],
      filename: filename || `址得选_选址报告_${safeName}_${d}.pdf`,
      image: { type: 'jpeg', quality: 1.0 },
      html2canvas: {
        scale: 3,
        useCORS: true,
        letterRendering: true,
        backgroundColor: '#f8fafc',
        logging: false,
        width: 800,
        windowWidth: 800,
      },
      jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' },
      pagebreak: { mode: ['css', 'legacy'] },
    }
    await html2pdf().set(opt).from(iframeDoc.body).save()
  } catch (error) {
    console.error('PDF 导出失败:', error)
    throw error
  } finally {
    document.body.removeChild(iframe)
  }
}

function buildFullReportHTML(data, meta, qrcodeUrl = '', pdfConfig = {}) {
  const { address, brandName, businessType, storeSize, date } = meta
  const { advantages = [], disadvantages = [], summary = '', warning = '', details = {}, score: legacyScore, real_data } = data
  const hasRealData = real_data && Object.keys(real_data).length > 0
  const exec = data.executive_summary || {}

  const fallbackDims = [
    { key: 'population_density', label: '人口密集度' },
    { key: 'traffic_accessibility', label: '交通可达性' },
    { key: 'traffic_flow', label: '客流特征' },
    { key: 'consumer_profile', label: '消费人群' },
    { key: 'competition', label: '竞争环境' },
    { key: 'complementary_businesses', label: '互补业态' },
    { key: 'category_advantage', label: '品类优势' },
    { key: 'cost_estimate', label: '成本压力' },
  ]
  const extractScore = (key) => {
    const txt = String(details[key] || '')
    const m = txt.match(/(\d{1,3})\s*分/)
    return m ? parseInt(m[1]) : 0
  }
  const dims = (Array.isArray(data.dimension_scores) && data.dimension_scores.length)
    ? data.dimension_scores
    : fallbackDims.map(d => ({ ...d, score: extractScore(d.key), text: stripScore(details[d.key] || '') }))
  const score = Number(legacyScore || (dims.length >= 8 ? Math.round(dims.slice(0, 8).reduce((sum, d) => sum + (Number(d.score) || 0), 0) / 8) : 0))
  const scoreHex = scoreColor(score)

  const reportDate = date?.slice(0, 10) || new Date().toISOString().slice(0, 10)
  const nowStr = new Date().toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  const footerText = pdfConfig.footer_text || 'AI 选址分析 · 商业选址初筛参考'

  const detailLabels = {
    population_density: '人口密集度', traffic_accessibility: '交通与可达性', traffic_flow: '客流特征',
    consumer_profile: '消费人群属性', competition: '竞争环境', complementary_businesses: '周边互补业态',
    category_advantage: '品类优势与差异化', cost_estimate: '房租成本预估',
    revenue_estimation: '营收测算模型', site_suggestion: '选址分析与运营策略',
  }
  const dimEmoji = {
    population_density: '🏘️', traffic_accessibility: '🚇', traffic_flow: '🚶',
    consumer_profile: '🛍️', competition: '⚔️', complementary_businesses: '🤝',
    category_advantage: '🌟', cost_estimate: '💰', revenue_estimation: '💵', site_suggestion: '📋',
  }
  const dimScoreColor = (s) => s >= 60 ? '#10b981' : s >= 40 ? '#f59e0b' : '#ef4444'

  let metricCards = '<table style="width:100%;border-collapse:separate;border-spacing:6px;margin:-6px;">'
  const safeDims = dims.slice(0, 8)
  for (let i = 0; i < safeDims.length; i += 2) {
    metricCards += '<tr>'
    for (let j = 0; j < 2; j++) {
      const d = safeDims[i + j]
      if (d) {
        const s = Number(d.score || 0)
        const sc = scoreColor(s)
        metricCards += '<td style="width:50%;padding:8px 12px;border:1px solid #e2e8f0;border-radius:6px;background:#fff;vertical-align:top;">' +
          '<div style="position:relative;height:20px;margin-bottom:6px;">' +
          '<strong style="position:absolute;left:0;top:0;font-size:13px;color:#334155;">' + escapeHtml(d.label) + '</strong>' +
          '<span style="position:absolute;right:0;top:0;font-size:16px;font-weight:900;color:' + sc + ';">' + (s || '-') + '</span>' +
          '</div><div style="height:5px;background:#e5e7eb;border-radius:99px;overflow:hidden;">' +
          '<div style="height:100%;width:' + Math.max(0, Math.min(100, s)) + '%;background:' + sc + ';"></div></div></td>'
      } else {
        metricCards += '<td style="width:50%;border:none;background:transparent;"></td>'
      }
    }
    metricCards += '</tr>'
  }
  metricCards += '</table>'

  const detailBlockItems = Object.entries(detailLabels).filter(([k]) => details[k]).map(([k, label]) => {
    const ds = dims.find(d => d.key === k)
    const dimScore = ds ? Number(ds.score || 0) : 0
    const sc = dimScoreColor(dimScore)
    return `<div class="pdf-no-break detail-card" style="display:block;width:100%;box-sizing:border-box;margin-bottom:16px;padding:14px 16px;background:#f8fafc;border-radius:8px;border-left:3px solid ${sc};">
      <div style="margin-bottom:8px;"><span style="font-size:16px;vertical-align:middle;">${dimEmoji[k] || ''}</span><strong style="font-size:15px;color:#0f172a;vertical-align:middle;margin-left:6px;">${escapeHtml(label)}</strong>${dimScore > 0 ? `<span style="font-size:15px;font-weight:900;color:${sc};margin-left:12px;vertical-align:middle;">${dimScore} 分</span>` : ''}</div>
      <div style="font-size:13px;color:#475569;line-height:1.6;text-align:justify;white-space:pre-wrap;word-wrap:break-word;margin:0!important;padding:0 0 2px 0;">${escapeHtml(stripScore(details[k]))}</div>
    </div>`
  })
  const detailPageOne = detailBlockItems.slice(0, 6).join('')
  const detailPageTwo = detailBlockItems.slice(6).join('')
  const strengths = (advantages && advantages.length > 0) ? advantages.filter(Boolean) : asList(exec.top_strengths, 99)
  const risks = (disadvantages && disadvantages.length > 0) ? disadvantages.filter(Boolean) : asList(exec.top_risks, 99)

  const ringSize = 140, strokeW = 12, ringR = (ringSize - strokeW) / 2, ringCirc = 2 * Math.PI * ringR
  const ringOffset = ringCirc * Math.max(0, Math.min(1, 1 - score / 100))
  const ringSvg = `<svg width="${ringSize}" height="${ringSize}" viewBox="0 0 ${ringSize} ${ringSize}"><circle cx="${ringSize/2}" cy="${ringSize/2}" r="${ringR}" fill="none" stroke="#e5e7eb" stroke-width="${strokeW}"/><circle cx="${ringSize/2}" cy="${ringSize/2}" r="${ringR}" fill="none" stroke="${scoreHex}" stroke-width="${strokeW}" stroke-dasharray="${ringCirc}" stroke-dashoffset="${ringOffset}" stroke-linecap="round" transform="rotate(-90 ${ringSize/2} ${ringSize/2})"/><text x="${ringSize/2}" y="${ringSize/2 + 6}" text-anchor="middle" font-family="Arial,sans-serif" font-size="46" font-weight="900" fill="${scoreHex}">${score}</text><text x="${ringSize/2}" y="${ringSize/2 + 24}" text-anchor="middle" font-family="Arial,sans-serif" font-size="13" fill="#94a3b8" font-weight="600">/ 100</text></svg>`
  const radarSvg = buildInlineRadarSVG(dims.map(d => ({ key: d.key, label: d.label, score: Number(d.score || 0) })))
  const sortedDims = [...dims].sort((a, b) => Number(b.score) - Number(a.score))
  const bestDims = sortedDims.slice(0, 2).map(d => detailLabels[d.key] || d.label || d.key).join('、')
  const worstKey = sortedDims.length > 0 ? sortedDims[sortedDims.length - 1].key : ''
  const worstLabel = worstKey ? (detailLabels[worstKey] || worstKey) : '部分'
  const shortSummary = data.short_conclusion || `该位置在${bestDims}方面表现较为突出，但${worstLabel}方面需重点关注。整体条件尚可但需权衡利弊。`

  const pageOpen = '<div class="pdf-page" style="width:100%;height:1131px;box-sizing:border-box;padding:0 44px;background:#f8fafc;overflow:hidden;">'
  const pageClose = '</div>'
  let reportHtml = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">'
  reportHtml += '<style>html,body{background:#f8fafc!important;margin:0!important;}.pdf-no-break{break-inside:avoid!important;page-break-inside:avoid!important;}.pdf-page{break-inside:avoid!important;page-break-inside:avoid!important;}.detail-card:last-child{margin-bottom:0!important;}</style></head>'
  reportHtml += '<body style="margin:0 auto;background:#f8fafc;color:#1e293b;font-family:\'Microsoft YaHei\',sans-serif;width:800px;">'

  reportHtml += '<div style="width:100%;box-sizing:border-box;">' + pageOpen
  reportHtml += '<div style="text-align:center;padding:22px 0 16px;background:#f8fafc;border-bottom:1px solid #e2e8f0"><h1 style="font-size:22px;font-weight:900;color:#1e40af;margin:0;letter-spacing:2px">址得选 · AI选址分析报告</h1><p style="font-size:10px;color:#94a3b8;margin:6px 0 0">商业选址初筛参考工具 | 基于实时 POI 数据 + AI 多维度分析 | ' + nowStr + '</p></div>'
  reportHtml += '<div style="padding:16px 0 20px"><div style="background:#eff6ff;border-radius:10px;padding:12px 20px;margin-bottom:24px;font-size:12px;line-height:2.2;color:#334155">'
  reportHtml += '<div><span style="font-weight:700;color:#1e40af;display:inline-block;min-width:80px">📍 分析地址</span>' + escapeHtml(address || '-') + '</div>'
  if (brandName) reportHtml += '<div><span style="font-weight:700;color:#1e40af;display:inline-block;min-width:80px">🏷️ 分析品牌</span>' + escapeHtml(brandName) + '</div>'
  if (businessType) reportHtml += '<div><span style="font-weight:700;color:#1e40af;display:inline-block;min-width:80px">🏪 选址业态</span>' + escapeHtml(businessType) + '</div>'
  if (storeSize) reportHtml += '<div><span style="font-weight:700;color:#1e40af;display:inline-block;min-width:80px">📐 门店面积</span>' + escapeHtml(storeSize) + '㎡</div>'
  reportHtml += '<div><span style="font-weight:700;color:#1e40af;display:inline-block;min-width:80px">📅 生成日期</span>' + escapeHtml(reportDate) + '</div>'
  if (real_data?.city) reportHtml += '<div><span style="font-weight:700;color:#1e40af;display:inline-block;min-width:80px">🗺️ 所属区域</span>' + escapeHtml(real_data.city) + ' ' + escapeHtml(real_data.district || '') + ' ' + escapeHtml(real_data.township || '') + '</div>'
  reportHtml += '</div><div style="padding:8px 14px;margin-bottom:24px;background:#fffbeb;border:1px solid #fde68a;border-radius:6px;font-size:10px;color:#92400e;font-weight:600;text-align:center">⚠️ 本工具不提供&quot;推荐/不推荐&quot;结论，各维度评分仅供参考，最终决策请结合实地考察</div>'
  if (warning) reportHtml += '<div style="padding:8px 14px;margin-bottom:24px;background:#fef2f2;border:1px solid #fecaca;border-radius:6px;font-size:11px;color:#991b1b;font-weight:700;text-align:center">🚨 风险提示：' + escapeHtml(warning) + '</div>'
  reportHtml += '<div class="pdf-no-break" style="margin-bottom:28px;"><div style="display:flex;gap:20px;background:#f8fafc;border-radius:10px;padding:16px 20px;border:1px solid #e2e8f0;box-shadow:0 2px 4px rgba(0,0,0,0.04);"><div style="display:flex;flex-direction:column;align-items:center;min-width:120px;border-right:1px dashed #cbd5e1;padding-right:20px;"><div style="font-size:14px;font-weight:900;color:#1e293b;margin-bottom:10px;">📊 综合评分</div>' + ringSvg + '</div><div style="flex:1;display:flex;flex-direction:column;justify-content:center;"><div style="font-size:12px;color:#475569;line-height:1.5;margin-bottom:10px;padding-bottom:10px;border-bottom:1px dashed #cbd5e1;">' + escapeHtml(shortSummary) + '</div><div><div style="font-size:14px;font-weight:900;color:#1e293b;margin-bottom:6px;">📋 分析摘要</div><div style="font-size:12px;font-weight:400;color:#475569;line-height:1.6;text-align:justify;">' + escapeHtml(summary || exec.summary || shortSummary) + '</div></div></div></div></div>'
  reportHtml += '<div class="pdf-no-break" style="margin-bottom:24px;"><div style="display:flex;gap:16px;align-items:stretch;"><section style="flex:1;border:1px solid #bbf7d0;border-radius:12px;padding:16px 20px;background:#f0fdf4;"><h2 style="font-size:16px;font-weight:900;margin:0 0 8px;color:#047857;">✅ 关键优势</h2><ul style="margin:0;padding-left:20px;font-size:12px;font-weight:400;color:#475569;line-height:1.7;">' + (strengths.length > 0 ? strengths.map((x, idx, arr) => '<li style="margin-bottom:' + (idx === arr.length - 1 ? '0' : '6px') + '">' + escapeHtml(x) + '</li>').join('') : '<li style="margin-bottom:0">暂无明显优势数据</li>') + '</ul></section><section style="flex:1;border:1px solid #fecaca;border-radius:12px;padding:16px 20px;background:#fff5f5;"><h2 style="font-size:16px;font-weight:900;margin:0 0 8px;color:#b91c1c;">⚠️ 主要风险</h2><ul style="margin:0;padding-left:20px;font-size:12px;font-weight:400;color:#475569;line-height:1.7;">' + (risks.length > 0 ? risks.map((x, idx, arr) => '<li style="margin-bottom:' + (idx === arr.length - 1 ? '0' : '6px') + '">' + escapeHtml(x) + '</li>').join('') : '<li style="margin-bottom:0">暂无明显风险数据</li>') + '</ul></section></div></div></div>' + pageClose + '</div>'

  const realDataResult = hasRealData ? _buildRealDataHTML(real_data, pageOpen, pageClose) : { main: '', poiPage: '' }
  reportHtml += '<div style="width:100%;box-sizing:border-box;">' + pageOpen + '<h2 style="font-size:16px;font-weight:900;margin:0 0 16px;color:#0f172a;padding-top:34px;">📊 指标雷达与维度评分</h2><div style="display:table;width:100%;table-layout:fixed;margin-bottom:24px;"><div style="display:table-cell;width:340px;vertical-align:top;text-align:center;padding-right:24px;">' + radarSvg.replace('<svg width="360" height="360"', '<svg width="330" height="330" style="display:block;margin:0 auto"') + '</div><div style="display:table-cell;vertical-align:middle;padding-left:18px;">' + metricCards + '</div></div><div style="margin-bottom:0;">' + realDataResult.main + '</div>' + pageClose + '</div>'
  if (realDataResult.poiPage) {
    reportHtml += '<div style="width:100%;box-sizing:border-box;">' + realDataResult.poiPage + '</div>'
  }
  reportHtml += '<div style="width:100%;box-sizing:border-box;">' + pageOpen + '<h2 style="font-size:16px;font-weight:900;margin:0 0 16px;color:#0f172a;padding-top:34px;">📝 各维度详细分析</h2>' + detailPageOne + pageClose + '</div>'
  reportHtml += '<div style="width:100%;box-sizing:border-box;">' + pageOpen + '<div style="padding-top:34px;">' + detailPageTwo + '</div><section style="clear:both;margin-top:24px;display:flex;align-items:center;gap:20px;border-top:1px solid #e2e8f0;background:#fff;border-radius:8px;padding:14px 18px;"><div style="flex:1"><div style="font-size:15px;font-weight:900;color:#1e40af;margin-bottom:6px">址得选 · AI 选址分析报告</div><div style="font-size:11px;color:#64748b;line-height:1.8">' + escapeHtml(footerText) + '</div><div style="font-size:10px;color:#94a3b8;margin-top:6px">本报告由系统自动生成，仅供商业决策参考，不构成投资建议。</div></div><div style="width:112px;text-align:center;flex-shrink:0">' + (qrcodeUrl ? '<img src="' + escapeHtml(qrcodeUrl) + '" width="112" height="112" style="display:block;border-radius:8px;object-fit:contain;background:white;border:1px solid #e2e8f0"/>' : '<div style="width:112px;height:112px;border:1px dashed #cbd5e1;border-radius:8px;background:white"></div>') + '<div style="font-size:10px;font-weight:800;color:#1d4ed8;margin-top:7px;line-height:1.4">扫码获取更多测算</div></div></section>' + pageClose + '</div>'
  reportHtml += '</body></html>'
  return reportHtml
}

function _buildRealDataHTML(rd, pageOpen, pageClose) {
  if (!rd) return { main: '', poiPage: '' }
  const rows = [
    ['🏘️ 住宅小区', rd.stats_200m?.residential, rd.stats_500m?.residential, rd.stats_1000m?.residential],
    ['🏢 写字楼', rd.stats_200m?.office, rd.stats_500m?.office, rd.stats_1000m?.office],
    ['🍽️ 餐饮门店', rd.stats_200m?.restaurants, rd.stats_500m?.restaurants, rd.stats_1000m?.restaurants, (rd.stats_1000m?.restaurants || 0) > 100 ? '#dc2626' : ''],
    ['☕ 咖啡茶饮', rd.stats_200m?.cafe_tea, rd.stats_500m?.cafe_tea, rd.stats_1000m?.cafe_tea],
    ['🛍️ 购物商场', rd.stats_200m?.shopping, rd.stats_500m?.shopping, rd.stats_1000m?.shopping],
    ['🏫 学校', rd.stats_200m?.schools, rd.stats_500m?.schools, rd.stats_1000m?.schools],
    ['🏥 医院', rd.stats_200m?.hospitals, rd.stats_500m?.hospitals, rd.stats_1000m?.hospitals],
    ['🚇 地铁站', rd.stats_200m?.subway, rd.stats_500m?.subway, rd.stats_1000m?.subway, !rd.poi_counts?.subway ? '#dc2626' : '#16a34a'],
    ['🚌 公交站', rd.stats_200m?.bus, rd.stats_500m?.bus, rd.stats_1000m?.bus],
    ['🏨 酒店', rd.stats_200m?.hotels, rd.stats_500m?.hotels, rd.stats_1000m?.hotels],
    ['🏦 银行', rd.poi_counts?.banks, null, null],
    ['🅿️ 停车场', rd.poi_counts?.parking, null, null],
  ]
  const poiGrid = rows.map(([label, v200, v500, v1000, hiColor]) => {
    const color = hiColor || '#334155'
    return '<div style="flex:0 0 auto;width:calc(25% - 3px);padding:8px 4px;background:' + (color === '#dc2626' ? '#fef2f2' : color === '#16a34a' ? '#f0fdf4' : '#f7f8fa') + ';border-radius:6px;text-align:center;box-sizing:border-box"><div style="font-size:9px;color:#888;margin-bottom:1px">' + label + '</div><div style="font-size:12px;font-weight:700;color:' + color + '">' + (v1000 != null ? _fmt(v200) + ' / ' + _fmt(v500) + ' / ' + _fmt(v1000) : _fmt(v200) + ' 个') + '</div>' + (v1000 != null ? '<div style="font-size:7px;color:#aaa;margin-top:0">200m / 500m / 1000m</div>' : '') + '</div>'
  }).join('')
  // ★ 严谨度 helper：新字段不存在才回退旧口径
  const hasRigor = rd.rigor_enabled === true
  const dc200 = hasRigor ? (rd.direct_competitors_200m ?? 0) : (rd.competitors_200m ?? 0)
  const dc500 = hasRigor ? (rd.direct_competitors_500m ?? 0) : (rd.competitors_500m ?? 0)
  const dc1000 = hasRigor ? (rd.direct_competitors_1000m ?? 0) : (rd.competitors_1000m ?? 0)
  const dcList = hasRigor ? (rd.direct_competitor_list || []) : (rd.competitor_list || [])

  // ★ 严谨度提示（未启用时）
  let rigorWarningHTML = !hasRigor ? '<div style="background:#fffbeb;border-radius:6px;padding:8px 12px;margin-bottom:8px;border:1px solid #fde68a;font-size:10px;color:#92400e;text-align:center;line-height:1.5">⚠️ 该业态暂无完整严谨分类规则，竞品结果仅供兼容参考。</div>' : ''

  // ★ 严谨度：直接竞品
  let compHTML = ''
  if (hasRigor || dc1000 > 0) {
    const clist = dcList.length
      ? '<div style="font-size:10px;color:#9a3412;line-height:1.8;border-top:1px solid #fecaca;padding-top:8px;margin-top:8px;text-align:center">' + dcList.slice(0, 12).map(c => '<span style="margin-right:12px">· ' + escapeHtml(c.name) + '（' + c.distance + 'm）</span>').join('') + '</div>'
      : (hasRigor ? '<div style="font-size:10px;color:#9a3412;line-height:1.8;border-top:1px solid #fecaca;padding-top:8px;margin-top:8px;text-align:center">1km内暂无直接竞品</div>' : '')
    const title = hasRigor ? '🎯 直接竞品（同类业态 · 严谨口径）' : '📋 旧口径竞品参考（非严谨直接竞品）'
    const bg = hasRigor ? '#fef2f2' : '#f8fafc'
    const border = hasRigor ? '#fecaca' : '#e2e8f0'
    const titleColor = hasRigor ? '#dc2626' : '#64748b'
    const bodyColor = hasRigor ? '#9a3412' : '#64748b'
    const numColor = hasRigor ? '#dc2626' : '#475569'
    const legacyNote = !hasRigor ? '<span style="font-size:10px;color:#b45309;display:block;line-height:1.5">⚠️ 旧口径统计，仅供兼容参考，需人工核验直接竞品。</span>' : ''
    compHTML = '<div style="background:' + bg + ';border-radius:6px;padding:10px 14px;margin-bottom:8px;border:1px solid ' + border + '"><div style="font-size:13px;font-weight:700;color:' + titleColor + ';margin-bottom:6px;text-align:center">' + title + '</div><div style="font-size:12px;color:' + bodyColor + ';line-height:2.2;text-align:center">200m: <strong style="font-size:16px;color:' + numColor + '">' + _fmt(dc200) + '</strong> · 500m: <strong style="font-size:16px;color:' + numColor + '">' + _fmt(dc500) + '</strong> · 1km: <strong style="font-size:16px;color:' + numColor + '">' + _fmt(dc1000) + '</strong></div>' + clist + legacyNote + '</div>'
  }
  // ★ 替代消费压力（三层半径）
  let subHTML = ''
  if ((rd.substitute_competitors_1000m || 0) > 0) {
    subHTML = '<div style="background:#fff7ed;border-radius:6px;padding:8px 14px;margin-bottom:8px;border:1px solid #fed7aa"><div style="font-size:12px;font-weight:700;color:#c2410c;margin-bottom:4px;text-align:center">🔶 替代消费压力（非同业态）</div><div style="font-size:10px;color:#9a3412;line-height:1.8;text-align:center">200m: ' + _fmt(rd.substitute_competitors_200m) + ' · 500m: ' + _fmt(rd.substitute_competitors_500m) + ' · 1km: ' + _fmt(rd.substitute_competitors_1000m) + '</div>' + ((rd.substitute_list || []).length > 0 ? '<div style="font-size:9px;color:#9a3412;line-height:1.6;border-top:1px solid #fed7aa;padding-top:4px;margin-top:4px;text-align:center">' + rd.substitute_list.slice(0,6).map(s => '· ' + escapeHtml(s.name) + '（' + s.distance + 'm）').join(' ') + '</div>' : '') + '</div>'
  }
  // ★ 客流锚点（三层半径）
  let anchorHTML = ''
  if ((rd.traffic_anchors_1000m || 0) > 0) {
    anchorHTML = '<div style="background:#f0fdf4;border-radius:6px;padding:8px 14px;margin-bottom:8px;border:1px solid #bbf7d0"><div style="font-size:12px;font-weight:700;color:#166534;margin-bottom:4px;text-align:center">🟢 客流锚点（非竞品）</div><div style="font-size:10px;color:#15803d;line-height:1.8;text-align:center">200m: ' + _fmt(rd.traffic_anchors_200m) + ' · 500m: ' + _fmt(rd.traffic_anchors_500m) + ' · 1km: ' + _fmt(rd.traffic_anchors_1000m) + '</div>' + ((rd.traffic_anchor_list || []).length > 0 ? '<div style="font-size:9px;color:#15803d;line-height:1.6;border-top:1px solid #bbf7d0;padding-top:4px;margin-top:4px;text-align:center">' + rd.traffic_anchor_list.slice(0,8).map(a => '· ' + escapeHtml(a.name) + '（' + a.distance + 'm）').join(' ') + '</div>' : '') + '</div>'
  }
  let brandHTML = ''
  if (rd.hot_brands?.length) {
    brandHTML = '<div style="background:#f8fafc;border-radius:6px;padding:10px 14px;margin-bottom:8px;border:1px solid #e2e8f0"><div style="font-size:12px;font-weight:700;color:#475569;margin-bottom:6px;text-align:center">🏪 周边连锁品牌（含客流锚点品牌）</div><div style="font-size:10px;line-height:2.2;text-align:center">' + rd.hot_brands.map(b => '<span style="margin-right:14px;color:#333;white-space:nowrap"><strong>' + escapeHtml(b.name) + '</strong> ×' + b.count + (b.min_distance != null ? ' <span style="color:#888">（最近' + b.min_distance + 'm）</span>' : '') + '</span>').join('') + '</div></div>'
  }
  // 数据质量摘要
  let qualHTML = ''
  if (rd.data_quality_notes?.length) {
    qualHTML = '<div style="background:#f8fafc;border-radius:6px;padding:6px 12px;margin-bottom:8px;border:1px solid #e2e8f0;font-size:10px;color:#64748b;text-align:center;line-height:1.6">📊 数据质量：' + rd.data_quality_notes.map(n => escapeHtml(n)).join(' · ') + '</div>'
  }
  const infoLines = []
  if (rd.city) infoLines.push('📍 ' + escapeHtml(rd.city) + ' ' + escapeHtml(rd.district || '') + ' ' + escapeHtml(rd.township || ''))
  if (rd.business_areas?.length) infoLines.push('🏬 商圈：' + escapeHtml(rd.business_areas.join('、')))
  if (rd.nearby_roads?.length) infoLines.push('🛣️ 道路：' + escapeHtml(rd.nearby_roads.join('、')))
  let poiListHTML = ''
  if (rd.poi_lists && Object.keys(rd.poi_lists).length > 0) {
    const cats = [
      ['🏘️ 住宅小区', 'residential'], ['🏢 写字楼', 'office'], ['🏫 学校', 'schools'],
      ['🏥 医院', 'hospitals'], ['🛍️ 购物商场', 'shopping'], ['🍽️ 餐厅', 'restaurants'],
      ['☕ 咖啡茶饮', 'cafe_tea'], ['🍔 快餐', 'fast_food'], ['🥢 中餐厅', 'chinese_restaurants'],
      ['🍝 异国料理', 'foreign_restaurants'], ['🏨 酒店', 'hotels'], ['🚇 地铁站', 'subway'],
      ['🚌 公交站', 'bus'], ['🅿️ 停车场', 'parking'], ['🏦 银行', 'banks'],
      ['🏪 便利店', 'convenience'], ['💊 药店', 'pharmacy'], ['💅 美容', 'beauty'], ['🐾 宠物', 'pets'], ['🍺 酒吧', 'bars'],
    ]
    let blocks = ''
    for (const [iconLabel, key] of cats) {
      const items = rd.poi_lists[key]
      if (!items || items.length === 0) continue
      const names = items.slice(0, 8).map(p => escapeHtml(p.name) + (p.distance != null ? '<span style="color:#94a3b8">(' + p.distance + 'm)</span>' : '')).join('、')
      blocks += '<div style="margin-bottom:5px"><span style="font-size:12px;font-weight:700;color:#334155">' + iconLabel + ' ×' + items.length + '</span><div style="font-size:11px;color:#475569;line-height:1.7;word-break:break-all;overflow-wrap:break-word">' + names + (items.length > 8 ? '<span style="color:#94a3b8"> 等' + items.length + '个</span>' : '') + '</div></div>'
    }
    if (blocks) {
      poiListHTML = pageOpen + '<h2 style="font-size:16px;font-weight:900;margin:0 0 8px;color:#0f172a;padding-top:34px;text-align:center">📋 周边业态明细（名称 + 距离）</h2><p style="font-size:9px;color:#94a3b8;text-align:center;margin:0 0 12px">高德地图实时采集 · 最多展示前8条POI</p>' + blocks + pageClose
    }
  }
  return { main: '<section><h2 style="font-size:15px;font-weight:900;margin:0 0 8px;color:#0f172a">📊 周边真实数据（200m / 500m / 1000m 三层半径采集）</h2><div style="display:flex;flex-wrap:wrap;gap:3px;margin-bottom:6px">' + poiGrid + '</div><div style="font-size:7px;color:#aaa;text-align:center;margin-bottom:8px;line-height:1.5">注：以上为系统判定的有效商机数，已自动过滤诊所、培训机构、公司厂房等低关联干扰项</div>' + rigorWarningHTML + compHTML + subHTML + anchorHTML + brandHTML + qualHTML + (infoLines.length ? '<div style="font-size:11px;color:#888;line-height:1.8;text-align:center">' + infoLines.join(' · ') + '</div>' : '') + '</section>', poiPage: poiListHTML }
}

function buildInlineRadarSVG(dims) {
  const cx = 180, cy = 180, r = 110, levels = 5
  const total = dims.length
  const getPoint = (value, index, radius) => {
    const angle = (Math.PI * 2 * index) / total - Math.PI / 2
    const scaledR = radius * (value / 100)
    return { x: cx + scaledR * Math.cos(angle), y: cy + scaledR * Math.sin(angle) }
  }
  let gridPaths = ''
  for (let l = 1; l <= levels; l++) {
    const pts = dims.map((_, i) => getPoint(100, i, (l / levels) * r))
    gridPaths += `<path d="${pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')} Z" fill="none" stroke="#e2e8f0" stroke-width="1"/>`
  }
  const axisLines = dims.map((_, i) => {
    const p = getPoint(100, i, r)
    return `<path d="M ${cx} ${cy} L ${p.x.toFixed(1)} ${p.y.toFixed(1)}" stroke="#e2e8f0" stroke-width="1"/>`
  }).join('')
  const dataPts = dims.map((d, i) => getPoint(d.score || 0, i, r))
  const dataPath = dataPts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ') + ' Z'
  const dataDots = dims.map((d, i) => {
    const p = getPoint(d.score || 0, i, r)
    const color = (d.score || 0) < 50 ? '#ef4444' : '#3b82f6'
    return `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="${color}" stroke="white" stroke-width="2"/>`
  }).join('')
  // 标签：名称上行 + 分数下行，用 tspan 强制换行，绝不重叠
  const labelTexts = dims.map((d, i) => {
    const p = getPoint(100, i, r + 42)
    const sc = (d.score || 0) >= 60 ? '#10b981' : (d.score || 0) >= 40 ? '#f59e0b' : '#ef4444'
    return `<text x="${p.x.toFixed(1)}" y="${p.y.toFixed(1)}" text-anchor="middle" dominant-baseline="middle" font-size="11" fill="#475569" font-weight="500">
      <tspan x="${p.x.toFixed(1)}" dy="-0.5em">${escapeHtml(d.label)}</tspan>
      <tspan x="${p.x.toFixed(1)}" dy="1.3em" font-size="10" font-weight="700" fill="${sc}">${d.score || '-'}</tspan>
    </text>`
  }).join('')
  return `<svg width="360" height="360" viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg">${gridPaths}${axisLines}<path d="${dataPath}" fill="rgba(59,130,246,0.15)" stroke="#3b82f6" stroke-width="2"/>${dataDots}${labelTexts}</svg>`
}
