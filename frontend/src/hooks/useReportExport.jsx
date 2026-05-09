/**
 * 全局统一 PDF 导出 Hook
 *
 * 统一入口：系统中所有"导出 PDF 报告"按钮均通过此 Hook 触发。
 *
 * 计费流程:
 *   1. GET /api/user/profile → 检查 membership
 *   2. 会员有效 → 直接导出（免费）
 *   3. 非会员 + reportUuid 已解锁 → 直接导出
 *   4. 非会员 + 未解锁 → 弹出确认 Modal → POST /api/records/{id}/unlock-pdf
 *   5. 扣点成功 → 导出
 *
 * 导出引擎: utils/exportToPDF.js (800ms wait + Canvas/SVG freeze + html2canvas @ 2x)
 *
 * 用法:
 *   const { exportPdf, ExportModal } = useReportExport()
 *   <button onClick={() => exportPdf({ el: ref.current })}>导出 PDF</button>
 *   <ExportModal />
 */
import { useState, useCallback, useRef } from 'react'
import { createPortal } from 'react-dom'
import { ensureToken, getToken, getAssetUrl } from '../services/api'

// 获取公众号二维码
async function fetchQrcode() {
  try {
    const r = await fetch('/api/admin/qrcode-slot/brand')
    const d = await r.json()
    return getAssetUrl(d.url || '')
  } catch { return '' }
}

async function fetchPdfConfig() {
  try {
    const r = await fetch('/api/admin/pdf-config')
    if (!r.ok) return {}
    return await r.json()
  } catch { return {} }
}

export default function useReportExport() {
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState('unlock') // 'unlock' | 'confirm'
  const [modalTitle, setModalTitle] = useState('')
  const [modalBody, setModalBody] = useState('')
  const [loading, setLoading] = useState(false)
  const [toast, setToast] = useState('')
  const pendingRef = useRef(null) // 存储待执行的导出参数

  const showToast = useCallback((msg) => { setToast(msg); setTimeout(() => setToast(''), 2500) }, [])

  const cancelPending = useCallback(() => {
    if (pendingRef.current?.resolve) {
      pendingRef.current.resolve({ ok: false, cancelled: true })
    }
    pendingRef.current = null
    setShowModal(false)
  }, [])

  /**
   * 核心导出流程
   *
   * @param {Object} opts
   *   - el?: HTMLElement         模式A: 直接截取 live DOM
   *   - data?: object            模式B: 从 JSON 构建报告
   *   - meta?: {address, brandName, businessType, storeSize, date}
   *   - reportUuid?: number        历史记录 ID（用于解锁校验）
   *   - isPdfUnlocked?: boolean  是否已解锁
   *   - filename?: string
   */
  const exportPdf = useCallback(async (opts = {}) => {
    const { el, data, meta, reportUuid, isPdfUnlocked, filename } = opts
    if (loading) return

    setLoading(true)
    try {
      await ensureToken()
      // 1. 检查会员状态
      const profile = await fetch(`/api/user/profile`, {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      }).then(r => r.ok ? r.json() : null)
      const isMember = profile?.membership?.is_member

      // 2. 会员 → 直接放行
      if (isMember) {
        showToast('会员有效期内，免费导出')
        const didExport = await doExport({ el, data, meta, filename })
        return { ok: didExport, didExport, unlocked: false }
      }

      // 3. 非会员 + 已解锁 → 直接放行
      if (reportUuid && isPdfUnlocked) {
        const didExport = await doExport({ el, data, meta, filename })
        return { ok: didExport, didExport, unlocked: false }
      }

      // 4. 非会员 + 未解锁 + 有 reportUuid → 弹窗确认
      if (reportUuid && !isPdfUnlocked) {
        setLoading(false)
        return await new Promise((resolve) => {
          setModalMode('unlock')
          setModalTitle('解锁 PDF 导出')
          setModalBody('确认消耗 1 个分析点数解锁并下载本报告的 PDF 版本吗？')
          pendingRef.current = { el, data, meta, reportUuid, filename, type: 'unlock', resolve }
          setShowModal(true)
        })
      }

      // 5. 无 reportUuid（新鲜报告）→ 分析时已扣费，直接导出
      showToast('正在生成高清报告...')
      const didExport = await doExport({ el, data, meta, filename })
      return { ok: didExport, didExport, unlocked: false }

    } catch (e) {
      showToast('网络错误，请重试')
      return { ok: false, error: e }
    } finally {
      setLoading(false)
    }
  }, [loading])

  /**
   * 确认弹窗的回调
   */
  const handleConfirm = useCallback(async () => {
    const pending = pendingRef.current
    if (!pending) return
    setShowModal(false)
    setLoading(true)

    try {
      if (pending.type === 'unlock') {
        // 调用解锁 API
        const r = await fetch(`/api/records/${pending.reportUuid}/unlock-pdf`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` },
        })
        const d = await r.json()
        if (!r.ok || !d.ok) {
          showToast(d.detail || '解锁失败')
          pending.resolve?.({ ok: false, error: d.detail || '解锁失败' })
          return
        }
        showToast(d.message || '解锁成功，正在准备下载...')
      }

      const didExport = await doExport({
        el: pending.el,
        data: pending.data,
        meta: pending.meta,
        filename: pending.filename,
      })
      pending.resolve?.({ ok: didExport, didExport, unlocked: pending.type === 'unlock' })
    } catch (e) {
      const msg = e?.response?.status === 402 ? (await e.response.json()).detail : '操作失败'
      showToast(typeof msg === 'string' ? msg : '操作失败，请重试')
      pending.resolve?.({ ok: false, error: msg })
    } finally {
      setLoading(false)
      pendingRef.current = null
    }
  }, [])

  /**
   * 实际执行导出
   */
  const doExport = async ({ el, data, meta, filename }) => {
    showToast('正在生成高清报告，请稍候...')
    try {
      if (el) {
        // 模式 A: 截取 live DOM
        const name = filename || `选址分析报告_${new Date().toISOString().slice(0, 10)}.pdf`
        const { exportElementToPDF } = await import('../utils/exportToPDF')
        await exportElementToPDF(el, name)
      } else if (data) {
        // 模式 B: 从 JSON 构建
        const [qrcodeUrl, pdfConfig] = await Promise.all([fetchQrcode(), fetchPdfConfig()])
        const { exportDataToPDF } = await import('../utils/exportToPDF')
        await exportDataToPDF(data, meta || {}, qrcodeUrl, pdfConfig, filename)
      }
      showToast('PDF 下载完成')
      return true
    } catch (e) {
      console.error('Export failed:', e)
      showToast('导出失败，请重试')
      return false
    }
  }

  /**
   * 确认弹窗 Modal
   */
  const ExportModal = useCallback(() => {
    if (!showModal) return null
    return createPortal(
      <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 px-4"
        onClick={cancelPending}>
        <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
          <div className="text-center text-3xl mb-3">{modalMode === 'unlock' ? '🔐' : '📄'}</div>
          <h3 className="text-base font-bold text-slate-900 text-center">{modalTitle}</h3>
          <p className="mt-3 text-sm leading-6 text-slate-600 text-center">{modalBody}</p>
          {modalMode === 'unlock' && (
            <p className="mt-2 text-xs text-slate-400 text-center">解锁后，本报告的 PDF 导出将永久免费</p>
          )}
          <div className="mt-5 flex gap-3">
            <button onClick={cancelPending}
              disabled={loading}
              className="flex-1 rounded-xl border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50">
              取消
            </button>
            <button onClick={handleConfirm}
              disabled={loading}
              className="flex-1 rounded-xl bg-amber-500 py-2.5 text-sm font-bold text-white hover:bg-amber-600 disabled:opacity-50 transition-colors">
              {loading ? '处理中...' : modalMode === 'unlock' ? '确认解锁（-1 点）' : '确认导出（-1 点）'}
            </button>
          </div>
        </div>
      </div>,
      document.body
    )
  }, [showModal, modalMode, modalTitle, modalBody, loading, handleConfirm, cancelPending])

  return {
    exportPdf,
    ExportModal,
    loading,
    toast,
    showToast,
  }
}
