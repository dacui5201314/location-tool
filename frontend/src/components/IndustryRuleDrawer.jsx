import { useState, useCallback, memo } from 'react'

const IndustryRuleDrawer = memo(function IndustryRuleDrawer({ industry, adminFetch, showToast, onSaved, onClose }) {
  const [draft, setDraft] = useState(industry?.exclusive_prompt || '')
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)

  const handleClose = useCallback(() => {
    if (dirty && !window.confirm('有未保存的修改，确定关闭？')) return
    setDirty(false)
    onClose?.()
  }, [dirty, onClose])

  const handleImport = useCallback((e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => { setDraft(ev.target.result); setDirty(true); showToast('文件已加载，请点击保存') }
    reader.readAsText(file)
    e.target.value = ''
  }, [showToast])

  const handleExport = useCallback(() => {
    const blob = new Blob([draft], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${industry?.name || '业态'}_专属规则.txt`
    a.click()
    window.URL.revokeObjectURL(url)
  }, [draft, industry?.name])

  const handleChange = useCallback((e) => {
    setDraft(e.target.value)
    setDirty(true)
  }, [])

  const handleSave = useCallback(async () => {
    setSaving(true)
    const r = await adminFetch(`/industries/${industry.id}`, {
      method: 'PUT',
      body: JSON.stringify({ exclusive_prompt: draft, reason: '更新专属规则' }),
    })
    setSaving(false)
    if (r.ok) {
      setDirty(false)
      showToast('专属规则已保存')
      onSaved?.()
    } else {
      const d = await r.json().catch(() => ({}))
      showToast(d.detail || '保存失败')
    }
  }, [draft, industry?.id, adminFetch, showToast, onSaved])

  if (!industry) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={handleClose}>
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <div>
            <h3 className="text-sm font-bold text-slate-800">业态专属规则编辑器</h3>
            <p className="text-xs text-slate-400 mt-0.5">
              业态：{industry.name}
              {dirty && <span className="ml-2 text-amber-600 font-medium">● 未保存</span>}
            </p>
          </div>
          <button onClick={handleClose} className="text-slate-400 hover:text-slate-600 text-xl leading-none">&times;</button>
        </div>

        <div className="flex-1 overflow-y-auto px-6 py-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-xs text-slate-400">专属 Prompt 规则编辑</span>
            <div className="flex-1" />
            <input type="file" accept=".txt,.md" className="hidden" id="promptFileInput" onChange={handleImport} />
            <label htmlFor="promptFileInput"
              className="cursor-pointer rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-500 hover:bg-slate-50 transition-colors">
              导入文件
            </label>
            <button onClick={handleExport}
              className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-500 hover:bg-slate-50 transition-colors">
              导出
            </button>
          </div>
          <textarea value={draft} onChange={handleChange}
            placeholder={`输入「${industry.name}」业态的专属 AI 分析规则...\n\n例如：\n- 重点关注周边 200m 内同类竞品数量与人均消费\n- 年轻客群占比权重提升至 40%\n- 外卖配送覆盖范围需大于 3km\n- ...`}
            className="w-full rounded-xl border border-slate-200 p-4 text-sm font-mono focus:outline-none focus:border-blue-400 min-h-[400px] resize-y"
            spellCheck="false" />
          <div className="text-right text-[10px] text-slate-400 mt-1">{draft.length} 字符</div>
        </div>

        <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-xl">
          <span className="text-[10px] text-slate-400">
            此规则将拼接在系统 Prompt 之后，以「## 业态专属测算规则」章节注入 AI 分析请求
          </span>
          <div className="flex gap-2">
            <button onClick={handleClose}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-500 hover:bg-white transition-colors">
              关闭
            </button>
            <button onClick={handleSave} disabled={!dirty || saving}
              className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
              {saving ? '保存中...' : '保存规则'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
})

export default IndustryRuleDrawer
