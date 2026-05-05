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
export async function exportDataToPDF(reportData, meta = {}, qrcodeUrl = '') {
  const { address = '', brandName = '', businessType = '', storeSize = '', date = '' } = meta

  const container = document.createElement('div')
  container.style.cssText =
    'position:fixed;left:-9999px;top:0;width:800px;background:#fff;' +
    'font-family:"Microsoft YaHei","PingFang SC","Noto Sans SC",sans-serif;' +
    'color:#1e293b;padding:0;z-index:-1;'
  container.innerHTML = buildFullReportHTML(reportData, { address, brandName, businessType, storeSize, date }, qrcodeUrl)
  document.body.appendChild(container)

  try {
    const safeName = (brandName || businessType || 'report').replace(/[\\/:*?"<>|]/g, '').slice(0, 30)
    const safeLoc = (address || '').slice(0, 20).replace(/[\\/:*?"<>|]/g, '')
    const d = date?.slice(0, 10) || new Date().toISOString().slice(0, 10)
    await domToPDF(container, `选址分析报告_${safeName}_${safeLoc}_${d}.pdf`)
  } finally {
    document.body.removeChild(container)
  }
}

// ============================================================
// 完整报告 HTML 模板（含评分环、所有维度、Footer）
// ============================================================
function buildFullReportHTML(data, meta, qrcodeUrl = '') {
  const { address, brandName, businessType, storeSize, date } = meta
  const { advantages = [], disadvantages = [], summary = '', warning = '', details = {}, score } = data

  const scoreColor = score >= 75 ? '#16a34a' : score >= 60 ? '#ca8a04' : '#dc2626'

  const dims = [
    { key: 'population_density', label: '人口密集度' },
    { key: 'traffic_accessibility', label: '交通可达性' },
    { key: 'traffic_flow', label: '客流特征' },
    { key: 'consumer_profile', label: '消费人群' },
    { key: 'competition', label: '竞争环境' },
    { key: 'complementary_businesses', label: '互补业态' },
    { key: 'category_advantage', label: '品类优势' },
    { key: 'cost_estimate', label: '成本预估' },
  ]

  // 提取分数
  const extractScore = (key) => {
    const txt = String(details[key] || '')
    const m = txt.match(/(\d{1,3})\s*分/)
    return m ? parseInt(m[1]) : 0
  }

  // 内联雷达图 SVG
  const radarSvg = buildInlineRadarSVG(dims.map(d => ({ ...d, score: extractScore(d.key) })))

  // 评分环
  const ringSize = 120
  const strokeW = 10
  const r2 = (ringSize - strokeW) / 2
  const circumference = 2 * Math.PI * r2
  const offset = circumference * (1 - (score || 0) / 100)

  // 各维度详细分析
  const detailLabels = {
    population_density: '人口密集度', traffic_accessibility: '交通与可达性', traffic_flow: '客流特征',
    consumer_profile: '消费人群属性', competition: '竞争环境', complementary_businesses: '周边互补业态',
    category_advantage: '品类优势与差异化', cost_estimate: '房租成本预估',
    revenue_estimation: '营收测算模型', site_suggestion: '选址分析与运营策略',
  }

  const detailBlocks = Object.entries(detailLabels)
    .filter(([k]) => details[k])
    .map(([k, label]) =>
      `<div style="margin-bottom:8px;padding:10px 14px;background:#f8fafc;border-radius:8px;border-left:3px solid #3b82f6">
         <strong style="font-size:13px;color:#1e293b">${label}</strong>
         <p style="font-size:12px;color:#475569;line-height:1.7;margin:6px 0 0;white-space:pre-wrap">${String(details[k])}</p>
       </div>`
    ).join('')

  return `<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:40px 44px;background:#fff;">

<!-- 页眉 -->
<div style="text-align:center;padding-bottom:16px;margin-bottom:20px;border-bottom:3px solid #1e40af">
  <div style="font-size:11px;color:#93c5fd;letter-spacing:4px;margin-bottom:4px">AI LOCATION INTELLIGENCE</div>
  <h1 style="font-size:20px;color:#1e40af;margin:0;font-weight:900;letter-spacing:2px">址得选 AI选址分析报告</h1>
  <p style="font-size:10px;color:#94a3b8;margin:6px 0 0">AI-Powered Location Intelligence Report · ${date || ''}</p>
</div>

<h2 style="font-size:18px;color:#0f172a;text-align:center;margin:0 0 16px;font-weight:700">
  ${brandName ? `${brandName} · ` : ''}选址分析报告
</h2>

<!-- 元信息 -->
<div style="background:linear-gradient(135deg,#eff6ff,#f0f9ff);border-radius:10px;padding:14px 18px;margin-bottom:18px;font-size:12px;line-height:2;color:#334155;border:1px solid #bfdbfe">
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="width:56px;color:#64748b;padding:2px 0">地  址</td><td style="font-weight:600">${address || '-'}</td></tr>
    ${brandName ? `<tr><td style="color:#64748b;padding:2px 0">品  牌</td><td style="font-weight:600">${brandName}</td></tr>` : ''}
    ${businessType ? `<tr><td style="color:#64748b;padding:2px 0">业  态</td><td style="font-weight:600">${businessType}</td></tr>` : ''}
    ${storeSize ? `<tr><td style="color:#64748b;padding:2px 0">面  积</td><td style="font-weight:600">${storeSize}㎡</td></tr>` : ''}
  </table>
</div>

<!-- 综合评分 -->
${score != null ? `<div style="text-align:center;margin:12px 0 20px">
  <div style="display:flex;align-items:center;justify-content:center;gap:24px">
    <svg width="${ringSize}" height="${ringSize}" viewBox="0 0 ${ringSize} ${ringSize}">
      <circle cx="${ringSize/2}" cy="${ringSize/2}" r="${r2}" fill="none" stroke="#e5e7eb" stroke-width="${strokeW}"/>
      <circle cx="${ringSize/2}" cy="${ringSize/2}" r="${r2}" fill="none" stroke="${scoreColor}" stroke-width="${strokeW}"
        stroke-dasharray="${circumference}" stroke-dashoffset="${offset}" stroke-linecap="round"
        transform="rotate(-90 ${ringSize/2} ${ringSize/2})"/>
      <text x="${ringSize/2}" y="${ringSize/2-4}" text-anchor="middle" font-size="34" font-weight="900" fill="${scoreColor}">${score}</text>
      <text x="${ringSize/2}" y="${ringSize/2+14}" text-anchor="middle" font-size="10" fill="#9ca3af">/ 100</text>
    </svg>
    <div style="text-align:left;font-size:12px">
      <div style="font-size:32px;font-weight:900;color:${scoreColor};line-height:1">${score}</div>
      <div style="font-size:11px;color:#94a3b8">综合评分</div>
    </div>
  </div>
</div>` : ''}

<!-- 雷达图 -->
${details ? `<div style="text-align:center;margin-bottom:18px">${radarSvg}</div>` : ''}

<!-- 警告 -->
${warning ? `<div style="padding:12px 16px;margin-bottom:16px;background:#fef2f2;border:1px solid #fecaca;border-radius:8px;font-size:12px;color:#991b1b;font-weight:600">⚠️ ${warning}</div>` : ''}

<!-- 分析摘要 -->
${summary ? `<div style="padding:14px 18px;margin-bottom:16px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0">
  <h3 style="font-size:14px;color:#1e293b;margin:0 0 8px">📋 分析摘要</h3>
  <p style="font-size:12px;color:#475569;line-height:1.9;margin:0">${summary}</p>
</div>` : ''}

<!-- 优势 -->
${advantages.length ? `<div style="margin-bottom:16px">
  <h3 style="font-size:14px;color:#16a34a;border-left:4px solid #16a34a;padding-left:10px;margin:0 0 10px">✅ 优势</h3>
  <ul style="font-size:12px;line-height:2;padding-left:20px;margin:0;color:#334155">${advantages.map(a => `<li style="margin-bottom:4px">${a}</li>`).join('')}</ul>
</div>` : ''}

<!-- 劣势 -->
${disadvantages.length ? `<div style="margin-bottom:16px">
  <h3 style="font-size:14px;color:#dc2626;border-left:4px solid #dc2626;padding-left:10px;margin:0 0 10px">⚠️ 劣势与风险</h3>
  <ul style="font-size:12px;line-height:2;padding-left:20px;margin:0;color:#334155">${disadvantages.map(d => `<li style="margin-bottom:4px">${d}</li>`).join('')}</ul>
</div>` : ''}

<!-- 各维度详细分析 -->
${detailBlocks ? `<div style="margin-bottom:16px">
  <h3 style="font-size:14px;color:#1e293b;border-left:4px solid #1e40af;padding-left:10px;margin:0 0 10px">📊 各维度详细分析</h3>
  ${detailBlocks}
</div>` : ''}

<!-- ====== 引流 Footer ====== -->
<div style="display:flex;align-items:center;gap:28px;margin-top:24px;padding:20px 24px;
  background:linear-gradient(135deg,#f8fafc,#eff6ff);border-radius:12px;
  border:1px solid #bfdbfe;border-top:3px solid #1e40af;">
  <div style="flex:1;min-width:0">
    <div style="font-size:15px;font-weight:900;color:#1e40af;letter-spacing:2px;margin-bottom:8px">址得选 AI选址分析报告</div>
    <div style="font-size:11px;color:#64748b;line-height:1.7">本报告由址得选 AI 选址分析平台自动生成，仅供参考。</div>
    <div style="font-size:10px;color:#94a3b8;margin-top:6px;line-height:1.6">数据底座：全网多维度商业POI聚合数据库<br/>不构成投资建议 · 请结合实地考察做出最终决策</div>
  </div>
  <div style="flex-shrink:0;text-align:center;width:110px">
    ${qrcodeUrl
      ? `<img src="${qrcodeUrl}" width="110" height="110" alt="公众号二维码" style="display:block;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.08);object-fit:contain"/>`
      : `<img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='110' height='110'%3E%3Crect width='110' height='110' fill='%23f1f5f9' rx='8'/%3E%3Crect x='4' y='4' width='102' height='102' fill='none' stroke='%23cbd5e1' stroke-width='2' rx='7' stroke-dasharray='6,4'/%3E%3Ctext x='55' y='45' text-anchor='middle' font-size='11' fill='%2394a3b8'%3E二维码%3C/text%3E%3Ctext x='55' y='61' text-anchor='middle' font-size='11' fill='%2394a3b8'%3E占位图%3C/text%3E%3C/svg%3E" width="110" height="110" style="display:block;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.08)"/>`
    }
    <div style="font-size:10px;font-weight:700;color:#dc2626;margin-top:6px;line-height:1.4">扫码关注<br/>免费获取您的专属选址测算</div>
  </div>
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
