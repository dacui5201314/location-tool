import { useState } from 'react'

export default function BrandInput({ value, onChange, onFocus, disabled, error }) {
  const [localValue, setLocalValue] = useState(value || '')

  const handleChange = (e) => {
    const v = e.target.value
    setLocalValue(v)
    onChange(v.trim())  // 每次输入都同步父组件，确保 error 即时清除
  }

  const handleClear = () => {
    setLocalValue('')
    onChange('')
  }

  return (
    <div className="w-full">
      <div className="field-label">
        <span>品牌名称或主营特色</span>
        <span className="text-xs font-semibold text-red-500">必填</span>
      </div>
      <div className="relative">
        <input
          type="text"
          value={localValue}
          onFocus={onFocus}
          onChange={handleChange}
          placeholder="请输入品牌名或主营产品或主营业务"
          disabled={disabled}
          className="text-input px-3.5 py-3 pr-10"
        />
        {localValue && !disabled && (
          <button type="button" onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 border-0 bg-transparent text-sm text-slate-400"
          >
            ✕
          </button>
        )}
      </div>
      <div className="min-h-[20px] mt-2">
        {error
          ? <p className="text-xs leading-5 text-red-500">请输入品牌名称或主营特色</p>
          : <p className="text-xs leading-5 text-slate-400">填写后会结合客单价与调性，测算客群匹配度和差异化策略</p>
        }
      </div>
    </div>
  )
}
