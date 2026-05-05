import { useState } from 'react'

export default function StoreSizeInput({ value, onChange, onFocus, disabled }) {
  const [localValue, setLocalValue] = useState(value || '')
  const [error, setError] = useState('')

  const handleChange = (e) => {
    const v = e.target.value
    // 只允许数字和小数点
    if (v === '' || /^\d*\.?\d*$/.test(v)) {
      setLocalValue(v)
      setError(v ? '' : '请输入门店预估面积')
      onChange(v)
    }
  }

  const handleFocus = () => {
    if (!localValue) {
      setError('请输入门店预估面积')
    }
    onFocus?.()
  }

  const handleBlur = () => {
    const num = parseFloat(localValue)
    if (!localValue) {
      setError('请输入门店预估面积')
    } else if (isNaN(num) || num <= 0) {
      setError('面积必须大于 0')
    } else if (num < 5) {
      setError('面积不能小于 5㎡')
    } else if (num > 5000) {
      setError('面积不能超过 5000㎡')
    } else {
      setError('')
    }
  }

  return (
    <div className="w-full">
      <div className="field-label">
        <span>门店预估面积</span>
        <span className="text-xs font-semibold text-red-500">必填</span>
      </div>
      <div className="relative">
        <input
          type="text"
          inputMode="decimal"
          value={localValue}
          onFocus={handleFocus}
          onChange={handleChange}
          onBlur={handleBlur}
          placeholder="请输入具体面积，如：60"
          disabled={disabled}
          className="text-input px-3.5 py-3 pr-14"
        />
        <span className="absolute right-3.5 top-1/2 -translate-y-1/2 text-sm font-medium text-slate-500 select-none">㎡</span>
      </div>
      <div className="min-h-[20px] mt-2">
        {error
          ? <p className="text-xs leading-5 text-red-500">{error}</p>
          : <p className="text-xs leading-5 text-slate-400">用于推算租金成本、人工配置及盈亏平衡单量</p>
        }
      </div>
    </div>
  )
}
