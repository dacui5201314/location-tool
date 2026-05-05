import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import useReportExport from '../hooks/useReportExport'
import AnalysisResult from '../components/AnalysisResult'
import { fetchRecordDetail } from '../services/api'

export default function RecordDetail() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [report, setReport] = useState(null)
  const [loading, setLoading] = useState(true)

  const { exportPdf, ExportModal, loading: exporting, toast, showToast } = useReportExport()

  // 拉取报告详情
  useEffect(() => {
    if (!id) { setLoading(false); return }
    setLoading(true)
    let cancelled = false
    const run = async () => {
      try {
        const d = await fetchRecordDetail(id)
        if (cancelled) return
        setData(d)
        if (d.report_json) {
          try { setReport(JSON.parse(d.report_json)) } catch { setReport(null) }
        }
      } catch {
        if (!cancelled) showToast('加载失败，请刷新重试')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [id, showToast])

  // 统一导出
  const triggerDownload = useCallback(async () => {
    const result = await exportPdf({
      data: report || {},
      meta: {
        address: data?.address || '',
        brandName: data?.brand_desc || '',
        businessType: data?.business_type || '',
        storeSize: String(data?.store_size || ''),
        date: data?.created_at?.slice(0, 10),
      },
      recordId: data?.id,
      isPdfUnlocked: data?.is_pdf_unlocked,
    })
    if (result?.ok && result?.unlocked) {
      setData(prev => prev ? { ...prev, is_pdf_unlocked: true } : prev)
    }
  }, [report, data, exportPdf])

  const handleUnlockThenDownload = useCallback(async () => {
    const result = await exportPdf({
      data: report || {},
      meta: {
        address: data?.address || '',
        brandName: data?.brand_desc || '',
        businessType: data?.business_type || '',
        storeSize: String(data?.store_size || ''),
        date: data?.created_at?.slice(0, 10),
      },
      recordId: data?.id,
      isPdfUnlocked: false,
    })
    if (result?.ok && result?.unlocked) {
      setData(prev => prev ? { ...prev, is_pdf_unlocked: true } : prev)
    }
  }, [report, data, exportPdf])

  // ---------- Loading ----------
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--page-bg)' }}>
        <div className="text-center">
          <div className="flex justify-center gap-2 mb-3">
            <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
            <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
            <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
          </div>
          <div className="text-sm text-slate-400">加载中...</div>
        </div>
      </div>
    )
  }

  // ---------- Error / Not Found ----------
  if (!data || data.error) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--page-bg)' }}>
        <div className="text-center">
          <div className="text-3xl mb-3">📭</div>
          <div className="text-sm text-slate-500">{data?.error || '记录不存在'}</div>
          <button onClick={() => navigate('/records', { replace: true })}
            className="mt-4 rounded-lg bg-blue-600 text-white text-xs font-semibold px-4 py-2">
            返回记录列表
          </button>
        </div>
      </div>
    )
  }

  const isUnlocked = data.is_pdf_unlocked || false

  // 老数据兼容：是否有完整的 report_json 结构
  const hasRichReport = report && (report.details || report.summary || report.advantages?.length || report.disadvantages?.length)
  const isLegacy = !hasRichReport && !loading

  // ---------- Main View ----------
  return (
    <div className="min-h-screen" style={{ background: 'var(--page-bg)', paddingBottom: '80px' }}>
      {toast && (
        <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[300] rounded-full bg-slate-800 text-white text-xs px-5 py-2.5 shadow-xl"
          style={{ whiteSpace: 'nowrap' }}>
          {toast}
        </div>
      )}

      <ExportModal />

      {/* Header */}
      <header style={{ background: 'rgba(255,255,255,0.96)', borderBottom: '1px solid var(--line)' }}
        className="sticky top-0 z-40 px-4 py-3">
        <div className="flex items-center gap-3 max-w-lg mx-auto">
          <button onClick={() => navigate(-1)}
            className="text-lg text-slate-500 hover:text-slate-700">&larr;</button>
          <h1 className="flex-1 text-base font-bold text-slate-900 truncate">
            {data.brand_desc || data.business_type || '报告详情'}
          </h1>
          <button
            onClick={triggerDownload}
            disabled={exporting}
            className={`flex items-center gap-1 text-xs font-semibold rounded-lg px-3 py-1.5 border transition-colors disabled:opacity-40 ${
              isUnlocked
                ? 'text-blue-600 bg-blue-50 border-blue-200 hover:bg-blue-100'
                : 'text-amber-600 bg-amber-50 border-amber-200 hover:bg-amber-100'
            }`}
          >
            {exporting ? (
              <><span className="inline-block w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />生成中</>
            ) : isUnlocked ? (
              <><span className="text-sm">⬇️</span> 下载 PDF</>
            ) : (
              <><span className="text-sm">🔒</span> 导出</>
            )}
          </button>
        </div>
      </header>

      <main className="px-4 pb-6 max-w-lg mx-auto pt-4 space-y-3">
        {/* Meta Card */}
        <div className="report-card p-4">
          <div className="grid grid-cols-2 gap-3">
            <div><div className="text-[10px] text-slate-400">地址</div><div className="text-xs font-semibold text-slate-900 mt-0.5">{data.address || '-'}</div></div>
            <div><div className="text-[10px] text-slate-400">品牌/业态</div><div className="text-xs font-semibold text-slate-900 mt-0.5">{data.brand_desc || data.business_type || '-'}</div></div>
            <div><div className="text-[10px] text-slate-400">门店面积</div><div className="text-xs font-semibold text-slate-900 mt-0.5">{data.store_size > 0 ? `${data.store_size}㎡` : '-'}</div></div>
            <div><div className="text-[10px] text-slate-400">分析时间</div><div className="text-xs text-slate-500 mt-0.5">{data.created_at?.slice(0, 16)?.replace('T', ' ')}</div></div>
          </div>
          {data.overall_score > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-50 flex items-center gap-3">
              <div className="text-[10px] text-slate-400">综合评分</div>
              <div className="text-xl font-black" style={{ color: data.overall_score >= 75 ? '#16a34a' : data.overall_score >= 60 ? '#ca8a04' : '#dc2626' }}>
                {data.overall_score}
              </div>
              <span className={`ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                isUnlocked ? 'bg-emerald-50 text-emerald-600' : 'bg-amber-50 text-amber-600'
              }`}>
                {isUnlocked ? 'PDF 已解锁' : 'PDF 未解锁'}
              </span>
            </div>
          )}
        </div>

        {/* 旧版数据降级提示 */}
        {isLegacy && (
          <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
            <div className="flex items-start gap-3">
              <span className="text-xl flex-shrink-0">⚠️</span>
              <div>
                <div className="text-sm font-bold text-amber-800 mb-1">此为旧版格式报告</div>
                <div className="text-xs text-amber-600 leading-5">
                  该报告生成于系统升级前，不支持高级图表展示（雷达图、评分环等）。
                  如需查看完整多维度数据，请重新发起分析。
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ===== 统一高保真报告渲染 ===== */}
        {report && !isLegacy && <AnalysisResult data={report} />}
        {report && isLegacy && (
          <div className="report-card p-4">
            <h3 className="mb-3 text-base font-bold text-slate-900">报告内容</h3>
            <pre className="whitespace-pre-wrap break-words rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">
              {JSON.stringify(report, null, 2)}
            </pre>
          </div>
        )}
      </main>

      {/* Bottom Bar */}
      <div className="fixed bottom-0 left-0 right-0 z-50" style={{ background: 'rgba(255,255,255,0.97)', borderTop: '1px solid #e2e8f0', paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}>
        <div className="max-w-lg mx-auto px-4 py-3 flex items-center gap-3">
          {isUnlocked ? (
            <button onClick={triggerDownload} disabled={exporting}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-lg shadow-blue-200">
              {exporting ? (
                <><span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />正在生成高清报告...</>
              ) : (
                <><span className="text-base">⬇️</span> 下载 PDF 报告</>
              )}
            </button>
          ) : (
            <button onClick={handleUnlockThenDownload} disabled={exporting}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-amber-500 py-3 text-sm font-bold text-white hover:bg-amber-600 disabled:opacity-50 transition-colors shadow-lg shadow-amber-200">
              {exporting ? (
                <><span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />处理中...</>
              ) : (
                <><span className="text-base">🔒</span> 消耗 1 点数导出 PDF</>
              )}
            </button>
          )}
          <button onClick={() => navigate('/records')}
            className="flex-shrink-0 rounded-xl border border-slate-200 bg-white py-3 px-4 text-sm font-semibold text-slate-500 hover:bg-slate-50 transition-colors">
            返回
          </button>
        </div>
      </div>
    </div>
  )
}
