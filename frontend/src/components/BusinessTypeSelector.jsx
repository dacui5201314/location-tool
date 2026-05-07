import { useState, useEffect } from 'react'

// category → display config
const CAT_META = {
  '餐饮': { icon: '♨', accent: 'blue' },
  '茶饮咖啡': { icon: '☕', accent: 'navy' },
  '零售商业': { icon: '▣', accent: 'indigo' },
  '酒店住宿': { icon: '▦', accent: 'green' },
  '生活服务': { icon: '✂', accent: 'mint' },
  '休闲娱乐': { icon: '🎮', accent: 'violet' },
}

export default function BusinessTypeSelector({ selected, onChange, disabled, error, hideLabel = false }) {
  const [industries, setIndustries] = useState([])
  const [expandedCat, setExpandedCat] = useState(null)

  // 数据驱动：从 /api/industries/active 拉取业态列表
  useEffect(() => {
    fetch('/api/industries/active')
      .then(r => r.json())
      .then(d => setIndustries(d.industries || []))
      .catch(() => {})
  }, [])

  // 按 category 分组
  const grouped = {}
  for (const item of industries) {
    const cat = item.category || '其他'
    if (!grouped[cat]) grouped[cat] = []
    grouped[cat].push(item)
  }

  const expandedItems = expandedCat ? (grouped[expandedCat] || []) : []

  const isSelected = (item) => selected && selected.id === item.id

  return (
    <div className="w-full">
      {!hideLabel && (
        <div className="field-label">
          <span>选址业态</span>
          <span className="text-xs font-semibold text-red-500">必填</span>
        </div>
      )}

      <div className="business-grid">
        {Object.entries(grouped).map(([cat, items]) => {
          const meta = CAT_META[cat] || { icon: '◆', accent: 'blue' }
          const anySelected = items.some(isSelected)
          const isExpanded = expandedCat === cat
          const active = anySelected || isExpanded
          return (
            <button key={cat} type="button" disabled={disabled}
              onClick={() => {
                if (disabled) return
                // 切换展开/收起
                setExpandedCat(isExpanded ? null : cat)
                // 如果该分类只有1个业态，直接选中
                if (items.length === 1 && !anySelected) {
                  onChange(items[0])
                  setExpandedCat(null)
                }
              }}
              className={`business-tile ${active ? 'is-active' : ''}`}>
              <span className={`business-icon ${meta.accent}`}>{meta.icon}</span>
              <span>{cat}</span>
            </button>
          )
        })}
      </div>

      {expandedItems.length > 1 && (
        <div className="business-subpanel">
          <div className="business-subtitle">细分业态（请选择一项）</div>
          <div className="flex flex-wrap gap-2">
            {expandedItems.map((item) => (
              <button key={item.id} type="button" disabled={disabled}
                onClick={() => {
                  if (disabled) return
                  onChange(isSelected(item) ? null : item)
                }}
                className={`chip-button ${isSelected(item) ? 'is-active' : ''}`}>
                {item.name}
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={{ minHeight: 20, marginTop: 8 }}>
        {error ? (
          <p style={{ fontSize: 12, lineHeight: '20px', color: '#ef4444', fontWeight: 600 }}>
            请完整选择选址业态
          </p>
        ) : (
          <p style={{ fontSize: 12, lineHeight: '20px', color: '#94a3b8' }}>
            选择与您业务最匹配的业态分类
          </p>
        )}
      </div>
    </div>
  )
}
