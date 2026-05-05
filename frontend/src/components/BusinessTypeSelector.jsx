import { useState } from 'react'

const CATEGORIES = [
  { label: '餐饮', icon: '♨', accent: 'blue', types: ['小餐饮', '大餐饮', '中餐', '日餐', '西餐', '火锅店', '烧烤店', '小吃店', '烘焙店', '快餐店'] },
  { label: '茶饮咖啡', icon: '☕', accent: 'navy', types: ['奶茶店', '咖啡店', '甜品店', '饮品店'] },
  { label: '零售商业', icon: '▣', accent: 'indigo', types: ['零售店', '便利店', '超市', '服装店', '数码店', '药店'] },
  { label: '酒吧夜店', icon: '♢', accent: 'violet', types: ['酒吧', 'KTV'] },
  { label: '生活服务', icon: '✂', accent: 'mint', types: ['美容美发', '健身房', '宠物店', '洗衣店'] },
  { label: '休闲娱乐', icon: '🎮', accent: 'violet', types: ['剧本杀', '网吧', '台球厅'] },
  { label: '酒店住宿', icon: '▦', accent: 'green', types: ['酒店', '民宿', '青年旅舍'] },
  { label: '教育培训', icon: '◆', accent: 'blue', types: ['教育培训'] },
  { label: '医疗健康', icon: '+', accent: 'cyan', types: ['诊所'] },
]

export default function BusinessTypeSelector({ selected, onChange, disabled, error, hideLabel = false }) {
  // 展开的面板（独立于已选中的值）
  const [expandedLabel, setExpandedLabel] = useState(null)
  const expandedCat = CATEGORIES.find(c => c.label === expandedLabel)

  const handleMainClick = (cat) => {
    if (disabled) return
    // 点击已激活项 → 反选收起
    if (cat.types.includes(selected) || expandedLabel === cat.label) {
      onChange('')
      setExpandedLabel(null)
      return
    }
    // 排他单选：切换主业态前，先清空旧选择
    onChange('')
    setExpandedLabel(null)
    if (cat.types.length === 1) {
      onChange(cat.types[0])
      return
    }
    // 多子类 → 展开面板
    setExpandedLabel(cat.label)
  }

  const handleSubClick = (type) => {
    if (disabled) return
    if (selected === type) {
      // 反选
      onChange('')
    } else {
      onChange(type)
    }
  }

  return (
    <div className="w-full">
      {!hideLabel && (
        <div className="field-label">
          <span>选址业态</span>
          <span className="text-xs font-semibold text-red-500">必填</span>
        </div>
      )}

      <div className="business-grid">
        {CATEGORIES.map((cat) => {
          // 仅当：该业态的子类被选中，或该业态面板正在展开（且没有其他业态的子类被选中）
          const active = cat.types.includes(selected) || (expandedLabel === cat.label && !selected)
          return (
            <button key={cat.label} type="button" disabled={disabled}
              onClick={() => handleMainClick(cat)}
              className={`business-tile ${active ? 'is-active' : ''}`}>
              <span className={`business-icon ${cat.accent}`}>{cat.icon}</span>
              <span style={cat.label.length === 2 ? { letterSpacing: '0.5em', marginRight: '-0.5em' } : undefined}>{cat.label}</span>
            </button>
          )
        })}
      </div>

      {expandedCat && expandedCat.types.length > 1 && (
        <div className="business-subpanel">
          <div className="business-subtitle">细分业态（请手动选择）</div>
          <div className="flex flex-wrap gap-2">
            {expandedCat.types.map((type) => (
              <button key={type} type="button" disabled={disabled}
                onClick={() => handleSubClick(type)}
                className={`chip-button ${selected === type ? 'is-active' : ''}`}>
                {type}
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
