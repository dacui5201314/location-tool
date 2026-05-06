/**
 * 高保真 PDF 导出引擎 — 统一出口
 *
 * 捕获策略:
 *   - 模式 A: 传入 live DOM element → 直接截取
 *   - 模式 B: 传入 reportData + meta → 动态构建完整报告 DOM 再截取
 *
 * 前置处理:
 *   1. 800ms 渲染等待 (ensure fonts / charts / CSS)
 *   2. Canvas → toDataURL('png') → <img> 静态替换
 *   3. SVG   → XMLSerializer + base64 → <img> 静态替换
 *   4. 等待全部替换图片解码
 *   5. html2canvas 全量截取
 *   6. jsPDF A4 分页输出
 */
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'

// ============================================================
// 静态化图形：Canvas + SVG → <img>
// ============================================================
function freezeGraphics(root) {
  const imgs = []

  root.querySelectorAll('canvas').forEach((c) => {
    try {
      const dataUrl = c.toDataURL('image/png')
      const img = document.createElement('img')
      img.src = dataUrl
      img.width = c.width || c.clientWidth
      img.height = c.height || c.clientHeight
      img.setAttribute('data-frozen', 'canvas')
      if (c.style.cssText) img.style.cssText = c.style.cssText
      c.replaceWith(img)
      imgs.push(img)
    } catch { /* cross-origin — skip */ }
  })

  root.querySelectorAll('svg').forEach((svg) => {
    try {
      const w = svg.clientWidth || parseInt(svg.getAttribute('width')) || 200
      const h = svg.clientHeight || parseInt(svg.getAttribute('height')) || 200
      if (w < 10 || h < 10) return
      const clone = svg.cloneNode(true)
      const svgStr = new XMLSerializer().serializeToString(clone)
      const encoded = btoa(String.fromCharCode(...new TextEncoder().encode(svgStr)))
      const img = document.createElement('img')
      img.src = `data:image/svg+xml;base64,${encoded}`
      img.width = w
      img.height = h
      img.setAttribute('data-frozen', 'svg')
      if (svg.style.cssText) img.style.cssText = svg.style.cssText
      svg.replaceWith(img)
      imgs.push(img)
    } catch { /* leave as-is */ }
  })

  return imgs
}

// ============================================================
// 等待图片全部解码
// ============================================================
async function waitForImages(imgs) {
  await Promise.all(imgs.map((img) =>
    new Promise((resolve) => {
      if (img.complete) resolve()
      else { img.onload = resolve; img.onerror = resolve }
    })
  ))
}

// ============================================================
// 等待图表就绪 — 替换脆弱的 setTimeout(800) 硬等待
// ============================================================
async function waitForChartsReady(root, timeoutMs = 3000) {
  const deadline = Date.now() + timeoutMs

  while (Date.now() < deadline) {
    await new Promise((r) => requestAnimationFrame(r))

    // 检查关键图形元素是否已渲染
    const hasCanvas = root.querySelector('canvas')
    const hasSvg = root.querySelector('svg')
    const hasScore = root.querySelector('.score-badge, [class*="score"]')

    if (hasSvg || hasCanvas || hasScore) {
      // 图表已就绪，额外等一帧确保布局稳定
      await new Promise((r) => requestAnimationFrame(r))
      return true
    }
  }

  // 超时兜底：未检测到图表，直接用当前 DOM 状态
  console.warn('[PDF Export] Chart render timeout — exporting DOM as-is')
  return false
}

// ============================================================
// DOM → Canvas → PDF
// ============================================================
async function domToPDF(el, filename) {
  // 等待图表渲染就绪（替换原 setTimeout(800) 硬等待）
  await waitForChartsReady(el)

  // 冻结图形
  const frozen = freezeGraphics(el)
  await waitForImages(frozen)
  await new Promise((r) => requestAnimationFrame(r))

  // 高保真截取
  const canvas = await html2canvas(el, {
    scale: 2,
    useCORS: true,
    allowTaint: true,
    backgroundColor: '#ffffff',
    logging: false,
    windowWidth: el.scrollWidth,
    windowHeight: el.scrollHeight,
  })

  // A4 分页
  const pdf = new jsPDF({ unit: 'px', format: 'a4', orientation: 'portrait' })
  const pw = pdf.internal.pageSize.getWidth()
  const ph = pdf.internal.pageSize.getHeight()
  const margin = 24
  const contentW = pw - margin * 2
  const maxH = ph - margin * 2
  const scale = contentW / canvas.width
  const sliceHpx = Math.round(maxH / scale)

  let srcY = 0
  let page = 0
  while (srcY < canvas.height) {
    if (page > 0) pdf.addPage()
    const h = Math.min(sliceHpx + 50, canvas.height - srcY)
    const slice = document.createElement('canvas')
    slice.width = canvas.width
    slice.height = h
    slice.getContext('2d').drawImage(canvas, 0, srcY, canvas.width, h, 0, 0, canvas.width, h)
    pdf.addImage(slice.toDataURL('image/jpeg', 0.92), 'JPEG', margin, margin, contentW, h * scale)
    srcY += sliceHpx
    page++
  }

  pdf.save(filename)
}

// ============================================================
// 模式 A: 截取已有 DOM 元素
// ============================================================
export async function exportElementToPDF(element, filename) {
  if (!element) throw new Error('No DOM element to export')
  await domToPDF(element, filename)
}

// ============================================================
// 模式 B: 从原始数据构建完整报告 DOM 再导出
// ============================================================
export async function exportDataToPDF(reportData, meta = {}, qrcodeUrl = '', pdfConfig = {}, filename = '') {
  const { address = '', brandName = '', businessType = '', storeSize = '', date = '' } = meta

  const container = document.createElement('div')
  container.style.cssText =
    'position:fixed;left:-9999px;top:0;width:800px;background:#fff;' +
    'font-family:"Microsoft YaHei","PingFang SC","Noto Sans SC",sans-serif;' +
    'color:#1e293b;padding:0;z-index:-1;'
  container.innerHTML = buildFullReportHTML(reportData, { address, brandName, businessType, storeSize, date }, qrcodeUrl, pdfConfig)
  document.body.appendChild(container)

  try {
    const safeName = (brandName || businessType || 'report').replace(/[\\/:*?"<>|]/g, '').slice(0, 30)
    const safeLoc = (address || '').slice(0, 20).replace(/[\\/:*?"<>|]/g, '')
    const d = date?.slice(0, 10) || new Date().toISOString().slice(0, 10)
    await domToPDF(container, filename || `选址分析报告_${safeName}_${safeLoc}_${d}.pdf`)
  } finally {
    document.body.removeChild(container)
  }
}

// ============================================================
// 完整报告 HTML 模板（咨询报告式版式）
// ============================================================
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
  return String(value).split(/[；;\n]/).map(s => s.trim()).filter(Boolean).slice(0, limit)
}

function stripScore(value = '') {
  return String(value).replace(/[，,]?\s*评分[：:]\s*\d{1,3}\s*分?\s*$/, '').trim()
}

function scoreTone(score = 0) {
  if (score >= 75) return { color: '#0f8a5f', bg: '#ecfdf5', label: '高潜力' }
  if (score >= 60) return { color: '#b7791f', bg: '#fffbeb', label: '可验证' }
  return { color: '#dc2626', bg: '#fef2f2', label: '高风险' }
}

function buildFullReportHTML(data, meta, qrcodeUrl = '', pdfConfig = {}) {
  const { address, brandName, businessType, storeSize, date } = meta
  const { advantages = [], disadvantages = [], summary = '', warning = '', details = {}, score = 0 } = data
  const tone = scoreTone(score)
  const reportDate = date?.slice(0, 10) || new Date().toISOString().slice(0, 10)
  const footerText = pdfConfig.footer_text || 'AI 选址分析 · 商业数据决策平台'
  const logoUrl = pdfConfig.logo_url || ''
  const exec = data.executive_summary || {}

  const fallbackDims = [
    { key: 'population_density', label: '人口密集度' },
    { key: 'traffic_accessibility', label: '交通可达性' },
    { key: 'traffic_flow', label: '客流特征' },
    { key: 'consumer_profile', label: '消费人群' },
    { key: 'competition', label: '竞争环境' },
    { key: 'complementary_businesses', label: '互补业态' },
    { key: 'category_advantage', label: '品类优势' },
    { key: 'cost_estimate', label: '成本预估' },
  ]
  const extractScore = (key) => {
    const txt = String(details[key] || '')
    const m = txt.match(/(\d{1,3})\s*分/)
    return m ? parseInt(m[1]) : 0
  }
  const dims = Array.isArray(data.dimension_scores) && data.dimension_scores.length
    ? data.dimension_scores
    : fallbackDims.map(d => ({ ...d, score: extractScore(d.key), text: stripScore(details[d.key] || '') }))
  const radarSvg = buildInlineRadarSVG(dims.map(d => ({ key: d.key, label: d.label, score: Number(d.score || 0) })))
  const detailLabels = {
    population_density: '人口密集度', traffic_accessibility: '交通与可达性', traffic_flow: '客流特征',
    consumer_profile: '消费人群属性', competition: '竞争环境', complementary_businesses: '周边互补业态',
    category_advantage: '品类优势与差异化', cost_estimate: '房租成本预估',
    revenue_estimation: '营收测算模型', site_suggestion: '选址分析与运营策略',
  }
  const metricCards = dims.slice(0, 8).map(d => {
    const s = Number(d.score || 0)
    const t = scoreTone(s)
    return `<div style="padding:12px 14px;border:1px solid #e2e8f0;border-radius:8px;background:#fff">
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:center">
        <strong style="font-size:12px;color:#334155">${escapeHtml(d.label)}</strong>
        <span style="font-size:15px;font-weight:900;color:${t.color}">${s || '-'}</span>
      </div>
      <div style="height:6px;background:#e5e7eb;border-radius:99px;margin-top:8px;overflow:hidden">
        <i style="display:block;height:100%;width:${Math.max(0, Math.min(100, s))}%;background:${t.color}"></i>
      </div>
    </div>`
  }).join('')
  const detailBlocks = Object.entries(detailLabels)
    .filter(([k]) => details[k])
    .map(([k, label]) =>
      `<div style="break-inside:avoid;margin-bottom:10px;padding:12px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #2563eb">
         <strong style="font-size:13px;color:#0f172a">${escapeHtml(label)}</strong>
         <p style="font-size:12px;color:#475569;line-height:1.75;margin:6px 0 0;white-space:pre-wrap">${escapeHtml(stripScore(details[k]))}</p>
       </div>`
    ).join('')
  const strengths = asList(exec.top_strengths?.length ? exec.top_strengths : advantages, 3)
  const risks = asList(exec.top_risks?.length ? exec.top_risks : disadvantages, 3)
  const actions = asList(data.action_plan, 5)
  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"></head>
<body style="margin:0;background:#fff;color:#1e293b;font-family:Microsoft YaHei,PingFang SC,Noto Sans SC,sans-serif">
<div style="padding:38px 44px 28px;background:#0f172a;color:white">
  <div style="display:flex;align-items:center;justify-content:space-between;gap:24px">
    <div>
      <div style="font-size:10px;letter-spacing:4px;color:#93c5fd;margin-bottom:10px">AI LOCATION INTELLIGENCE</div>
      <h1 style="font-size:26px;line-height:1.25;margin:0;font-weight:900">${escapeHtml(brandName || businessType || '选址分析报告')}</h1>
      <p style="font-size:12px;line-height:1.7;color:#cbd5e1;margin:10px 0 0">${escapeHtml(address || '-')}</p>
    </div>
    ${logoUrl ? `<img src="${escapeHtml(logoUrl)}" style="width:54px;height:54px;object-fit:contain;border-radius:8px;background:white;padding:6px"/>` : '<div style="width:54px;height:54px;border-radius:8px;background:#2563eb;display:flex;align-items:center;justify-content:center;font-weight:900">址</div>'}
  </div>
  <div style="display:grid;grid-template-columns:1.15fr .85fr;gap:18px;margin-top:28px">
    <div style="background:white;color:#0f172a;border-radius:12px;padding:20px">
      <div style="font-size:11px;color:#64748b">综合评分</div>
      <div style="display:flex;align-items:flex-end;gap:12px;margin-top:4px">
        <strong style="font-size:52px;line-height:.9;color:${tone.color}">${score || '-'}</strong>
        <span style="font-size:13px;font-weight:800;color:${tone.color};background:${tone.bg};padding:5px 9px;border-radius:999px">${tone.label}</span>
      </div>
      <p style="font-size:13px;line-height:1.8;color:#334155;margin:16px 0 0">${escapeHtml(exec.summary || summary || '暂无摘要')}</p>
    </div>
    <div style="border:1px solid rgba(255,255,255,.18);border-radius:12px;padding:16px;color:#cbd5e1;font-size:12px;line-height:2">
      <div>生成日期：${escapeHtml(reportDate)}</div>
      ${businessType ? `<div>目标业态：${escapeHtml(businessType)}</div>` : ''}
      ${storeSize ? `<div>预计面积：${escapeHtml(storeSize)}㎡</div>` : ''}
      <div>结论：${escapeHtml(exec.verdict || tone.label)}</div>
    </div>
  </div>
</div>
<div style="padding:26px 44px 36px">
  ${warning ? `<div style="padding:12px 16px;margin-bottom:18px;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;font-size:12px;color:#991b1b;font-weight:700">风险提示：${escapeHtml(warning)}</div>` : ''}
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:22px">
    <section style="border:1px solid #dcfce7;border-radius:10px;padding:16px;background:#f8fffb">
      <h2 style="font-size:14px;margin:0 0 10px;color:#047857">关键机会</h2>
      <ol style="margin:0;padding-left:18px;font-size:12px;color:#334155;line-height:1.85">${strengths.map(x => `<li>${escapeHtml(x)}</li>`).join('')}</ol>
    </section>
    <section style="border:1px solid #fee2e2;border-radius:10px;padding:16px;background:#fffafa">
      <h2 style="font-size:14px;margin:0 0 10px;color:#b91c1c">主要风险</h2>
      <ol style="margin:0;padding-left:18px;font-size:12px;color:#334155;line-height:1.85">${risks.map(x => `<li>${escapeHtml(x)}</li>`).join('')}</ol>
    </section>
  </div>
  <h2 style="font-size:15px;margin:0 0 12px;color:#0f172a">指标雷达与维度评分</h2>
  <div style="display:grid;grid-template-columns:360px 1fr;gap:18px;align-items:center;margin-bottom:22px">
    <div style="text-align:center">${radarSvg}</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">${metricCards}</div>
  </div>
  ${actions.length ? `<section style="break-inside:avoid;border:1px solid #dbeafe;border-radius:10px;background:#f8fbff;padding:16px;margin-bottom:22px">
    <h2 style="font-size:15px;margin:0 0 10px;color:#1d4ed8">落地行动清单</h2>
    <ol style="margin:0;padding-left:18px;font-size:12px;color:#334155;line-height:1.85">${actions.map(x => `<li>${escapeHtml(x)}</li>`).join('')}</ol>
  </section>` : ''}
  <h2 style="font-size:15px;margin:0 0 12px;color:#0f172a">详细分析</h2>
  ${detailBlocks}
  <section style="break-inside:avoid;margin-top:24px;display:flex;align-items:center;gap:24px;border-top:3px solid #0f172a;background:#f8fafc;border-radius:10px;padding:20px">
    <div style="flex:1">
      <div style="font-size:15px;font-weight:900;color:#0f172a;margin-bottom:6px">址得选 AI 选址分析报告</div>
      <div style="font-size:11px;color:#64748b;line-height:1.8">${escapeHtml(footerText)}</div>
      <div style="font-size:10px;color:#94a3b8;margin-top:6px">本报告由系统自动生成，仅供商业决策参考，不构成投资建议。</div>
    </div>
    <div style="width:112px;text-align:center;flex-shrink:0">
      ${qrcodeUrl ? `<img src="${escapeHtml(qrcodeUrl)}" width="112" height="112" style="display:block;border-radius:8px;object-fit:contain;background:white;border:1px solid #e2e8f0"/>` : '<div style="width:112px;height:112px;border:1px dashed #cbd5e1;border-radius:8px;background:white"></div>'}
      <div style="font-size:10px;font-weight:800;color:#1d4ed8;margin-top:7px;line-height:1.4">扫码获取更多测算</div>
    </div>
  </section>
</div>
</body></html>`
}

// ============================================================
// 内联雷达图 SVG（8 维度，纯静态，零动画）
// ============================================================
function buildInlineRadarSVG(dims) {
  const cx = 180, cy = 180, r = 140, levels = 5
  const total = dims.length

  const getPoint = (value, index, radius) => {
    const angle = (Math.PI * 2 * index) / total - Math.PI / 2
    return { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) }
  }

  // 网格
  let gridPaths = ''
  for (let l = 1; l <= levels; l++) {
    const pts = dims.map((_, i) => getPoint(100, i, (l / levels) * r))
    gridPaths += `<path d="${pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')} Z" fill="none" stroke="#e2e8f0" stroke-width="1"/>`
  }

  // 轴线
  let axisLines = dims.map((_, i) => {
    const p = getPoint(100, i, r)
    return `<path d="M ${cx} ${cy} L ${p.x.toFixed(1)} ${p.y.toFixed(1)}" stroke="#e2e8f0" stroke-width="1"/>`
  }).join('')

  // 数据区域
  const dataPts = dims.map((d, i) => getPoint(d.score || 0, i, r))
  const dataPath = dataPts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ') + ' Z'

  // 数据点
  let dataDots = dims.map((d, i) => {
    const p = getPoint(d.score || 0, i, r)
    const color = (d.score || 0) < 50 ? '#ef4444' : '#3b82f6'
    return `<circle cx="${p.x.toFixed(1)}" cy="${p.y.toFixed(1)}" r="4" fill="${color}" stroke="white" stroke-width="2"/>`
  }).join('')

  // 标签
  let labelTexts = dims.map((d, i) => {
    const p = getPoint(100, i, r + 24)
    return `<text x="${p.x.toFixed(1)}" y="${p.y.toFixed(1)}" text-anchor="middle" dominant-baseline="middle" font-size="12" fill="#475569" font-weight="500">${d.label}</text>`
  }).join('')

  // 分值标签
  let scoreLabels = dims.map((d, i) => {
    if (!d.score) return ''
    const p = getPoint(d.score || 0, i, r)
    const offsetR = (d.score / 100) * r + 18
    const sp = getPoint(100, i, offsetR)
    const color = d.score < 50 ? '#ef4444' : '#1e40af'
    return `<g><rect x="${sp.x.toFixed(1)-14}" y="${sp.y.toFixed(1)-9}" width="28" height="18" rx="3" fill="white" fill-opacity="0.85"/><text x="${sp.x.toFixed(1)}" y="${sp.y.toFixed(1)+4}" text-anchor="middle" font-size="12" font-weight="700" fill="${color}">${d.score}</text></g>`
  }).join('')

  return `<svg width="360" height="360" viewBox="0 0 360 360" xmlns="http://www.w3.org/2000/svg">
    ${gridPaths}${axisLines}
    <path d="${dataPath}" fill="rgba(59,130,246,0.15)" stroke="#3b82f6" stroke-width="2"/>
    ${dataDots}${scoreLabels}${labelTexts}
  </svg>`
}
