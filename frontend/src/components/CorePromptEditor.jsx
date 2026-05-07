import { useState, useCallback, memo } from 'react'

const CorePromptEditor = memo(function CorePromptEditor({ systemPrompt, settingsLoaded, adminFetch, showToast, onSaved }) {
  const [showPrompt, setShowPrompt] = useState(false)
  const [promptImported, setPromptImported] = useState(false)
  const [promptConfirm, setPromptConfirm] = useState(false)
  const [localPrompt, setLocalPrompt] = useState(systemPrompt)

  // Sync when parent re-mounts with new value
  const promptValue = promptImported ? localPrompt : systemPrompt

  const handleImport = useCallback((e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = (ev) => {
      setLocalPrompt(ev.target.result)
      setPromptImported(true)
      showToast('检测到新提示词导入，请点击【保存更新】将修改应用到 AI 模型')
    }
    reader.readAsText(file)
    e.target.value = ''
  }, [showToast])

  const handleExport = useCallback(() => {
    const content = promptValue
    if (!content || !content.trim()) { showToast('内容为空，无法导出'); return }
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `core_prompt_${new Date().getTime()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    showToast(`已导出 ${content.length} 字符`)
  }, [promptValue, showToast])

  const handleSave = useCallback(async () => {
    setPromptConfirm(false)
    const r = await adminFetch('/config/prompt', {
      method: 'POST',
      body: JSON.stringify({ system_prompt: promptValue }),
    })
    if (r.ok) {
      showToast('Prompt 已保存并生效')
      setPromptImported(false)
      onSaved?.()
    } else {
      const d = await r.json().catch(() => ({}))
      showToast(d.detail || '保存失败')
    }
  }, [promptValue, adminFetch, showToast, onSaved])

  return (
    <>
      <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm font-bold text-slate-800">核心 Prompt 热更新 🔒</div>
            <div className="text-[11px] text-slate-400">保险柜模式：禁止手动编辑，仅支持 TXT 文件导入后覆盖更新</div>
          </div>
          <div className="flex items-center gap-2">
            {!settingsLoaded ? <span className="text-xs text-slate-400">配置加载中...</span> : <>
              <button onClick={() => setShowPrompt(!showPrompt)}
                className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50">
                {showPrompt ? '🙈 隐藏' : '👁 显示'}
              </button>
              <button onClick={handleExport}
                className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50">
                📥 导出 TXT
              </button>
              <label className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50 cursor-pointer">
                📤 导入 TXT
                <input type="file" accept=".txt" className="hidden" onChange={handleImport} />
              </label>
              <button onClick={() => setPromptConfirm(true)}
                disabled={!promptImported}
                className="rounded-lg px-4 py-2 text-xs font-bold text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                style={{ background: promptImported ? '#dc2626' : '#94a3b8' }}>
                保存更新
              </button>
            </>}
          </div>
        </div>
        {promptImported && (
          <div className="mb-3 rounded-lg border border-amber-200 bg-amber-50 px-4 py-2 text-xs font-semibold text-amber-700">
            ⚠️ 检测到新提示词导入，请点击【保存更新】将修改应用到 AI 模型
          </div>
        )}
        {!showPrompt && settingsLoaded ? (
          <div className="relative rounded-lg border border-slate-200 bg-slate-100 px-4 py-6 text-center cursor-pointer"
            onClick={() => setShowPrompt(true)}>
            <div className="text-slate-400 text-sm font-medium">🔒 提示词内容已隐藏（点击显示）</div>
            <div className="text-slate-300 text-xs mt-1">{promptValue?.length || 0} 字符</div>
          </div>
        ) : (
          <textarea id="system-prompt-editor" value={promptValue}
            readOnly={true}
            rows={14}
            style={{ fontSize: 13, fontFamily: "'JetBrains Mono','Fira Code','Courier New',monospace", lineHeight: 1.7 }}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 resize-y focus:outline-none cursor-not-allowed text-slate-600" />
        )}
      </div>

      {promptConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setPromptConfirm(false)}>
          <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
            <div className="text-center text-2xl mb-3">⚠️</div>
            <h3 className="text-base font-bold text-slate-900 text-center">确认更新核心 Prompt？</h3>
            <p className="mt-2 text-sm text-slate-500 text-center leading-5">此操作将改变系统的 AI 核心逻辑，影响所有后续分析报告的质量和风格。是否确认更新？</p>
            <div className="mt-5 flex gap-3">
              <button onClick={() => setPromptConfirm(false)}
                className="flex-1 rounded-lg border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">取消</button>
              <button onClick={handleSave}
                className="flex-1 rounded-lg bg-red-600 py-2.5 text-sm font-bold text-white hover:bg-red-700">确认更新</button>
            </div>
          </div>
        </div>
      )}
    </>
  )
})

export default CorePromptEditor
