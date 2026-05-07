export default function RadarChart({ scores }) {
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

  const cx = 180, cy = 180, r = 110, levels = 5

  const getPoint = (value, index, total, radius) => {
    const angle = (Math.PI * 2 * index) / total - Math.PI / 2
    const r2 = (value / 100) * radius
    return { x: cx + r2 * Math.cos(angle), y: cy + r2 * Math.sin(angle) }
  }

  const getGridPoint = (level, index, total) => {
    const angle = (Math.PI * 2 * index) / total - Math.PI / 2
    const r2 = (level / levels) * r
    return { x: cx + r2 * Math.cos(angle), y: cy + r2 * Math.sin(angle) }
  }

  const dataPoints = dims.map((d, i) => {
    const score = scores?.[d.key] || 0
    return getPoint(score, i, dims.length, r)
  })
  const dataPath = dataPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ') + ' Z'

  // Grid
  const gridLines = []
  for (let l = 1; l <= levels; l++) {
    const pts = dims.map((_, i) => getGridPoint(l, i, dims.length))
    gridLines.push(pts.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(' ') + ' Z')
  }

  // Axis
  const axisLines = dims.map((_, i) => {
    const p = getGridPoint(levels, i, dims.length)
    return `M ${cx} ${cy} L ${p.x.toFixed(2)} ${p.y.toFixed(2)}`
  })

  // Dimension labels — pushed further out
  const labelGap = r + 40
  const labels = dims.map((d, i) => {
    const angle = (Math.PI * 2 * i) / dims.length - Math.PI / 2
    return { x: cx + labelGap * Math.cos(angle), y: cy + labelGap * Math.sin(angle), label: d.label, key: d.key }
  })

  return (
    <div className="flex justify-center">
      <svg width="360" height="360" viewBox="0 0 360 360" className="max-w-full" role="img" aria-label="选址维度雷达图">
        <title>选址维度雷达图</title>
        <desc>展示人口密集度、交通可达性、客流特征、消费人群、竞争环境、互补业态、品类优势、成本预估共八个维度的综合评分</desc>
        {/* Grid */}
        {gridLines.map((path, i) => (
          <path key={`grid-${i}`} d={path} fill="none" stroke="#e2e8f0" strokeWidth="1" />
        ))}
        {/* Axis */}
        {axisLines.map((path, i) => (
          <path key={`axis-${i}`} d={path} stroke="#e2e8f0" strokeWidth="1" />
        ))}
        {/* Data area */}
        <path d={dataPath} fill="rgba(59, 130, 246, 0.15)" stroke="#3b82f6" strokeWidth="2" />
        {/* Data points */}
        {dims.map((d, i) => {
          const score = scores?.[d.key] || 0
          const p = getPoint(score, i, dims.length, r)
          const isWeak = score < 50
          return (
            <g key={`pt-${i}`}>
              <circle cx={p.x.toFixed(2)} cy={p.y.toFixed(2)} r="4"
                fill={isWeak ? '#ef4444' : '#3b82f6'} stroke="white" strokeWidth="2" />
            </g>
          )
        })}
        {/* Dimension labels — name + score 分两行, 绝不重叠 */}
        {labels.map((l) => {
          const s = scores?.[l.key] || 0
          const scoreColor = s >= 70 ? '#10b981' : s >= 60 ? '#f59e0b' : '#ef4444'
          return (
            <text key={`label-${l.key}`} x={l.x.toFixed(2)} y={l.y.toFixed(2)} textAnchor="middle" dominantBaseline="middle" fontSize="11" fill="#475569" fontWeight="500">
              <tspan x={l.x.toFixed(2)} dy="-0.6em">{l.label}</tspan>
              <tspan x={l.x.toFixed(2)} dy="1.4em" fontSize="10" fontWeight="700" fill={scoreColor}>{s || '-'}</tspan>
            </text>
          )
        })}
      </svg>
    </div>
  )
}
