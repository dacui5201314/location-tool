import { useState, useCallback, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import useFetch from '../hooks/useFetch'
import useReportExport from '../hooks/useReportExport'
import { getToken } from '../services/api'

function LoadingCard() {
  return (
    <div className="records-state-card">
      <div className="flex justify-center gap-2 mb-3">
        <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
        <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
        <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
      </div>
      <div className="text-sm text-slate-400">加载中...</div>
    </div>
  )
}

function ErrorCard({ msg, onRetry }) {
  return (
    <div className="records-state-card">
      <div className="text-2xl mb-2">⚠️</div>
      <div className="text-sm text-red-500 mb-3">{msg}</div>
      <button onClick={onRetry} className="rounded-lg bg-blue-600 text-white text-xs font-semibold px-4 py-2">点击重试</button>
    </div>
  )
}

function EmptyCard() {
  return (
    <div className="records-state-card">
      <div className="text-4xl mb-3">📋</div>
      <div className="text-sm font-semibold text-slate-600">暂无分析记录</div>
      <div className="text-xs text-slate-400 mt-1">完成一次选址分析后自动保存</div>
    </div>
  )
}

function parseReport(record) {
  if (!record?.report_json) return {}
  try {
    return JSON.parse(record.report_json) || {}
  } catch {
    return {}
  }
}

function scoreTone(score = 0) {
  if (score >= 78) return 'green'
  if (score >= 70) return 'amber'
  return 'blue'
}

function stars(score = 0) {
  const active = Math.max(1, Math.min(5, Math.round(score / 20)))
  return Array.from({ length: 5 }, (_, i) => i < active)
}

function formatDate(value) {
  if (!value) return '未知时间'
  try { return new Date(value + 'Z').toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) } catch { return value.slice(0, 16).replace('T', ' ') }
}

function RecordCard({ record, exportingId, onDownload, onDelete, onOpen }) {
  const report = parseReport(record)
  const score = Number(record.overall_score || report?.overall_score || 0)
  const tone = scoreTone(score)
  const tags = [
    { type: 'type', text: record.business_type || '选址' },
    record.brand_desc && record.brand_desc !== record.business_type ? { type: 'brand', text: record.brand_desc } : null,
    record.store_size > 0 ? { type: 'size', text: `${record.store_size}m²` } : null,
  ].filter(Boolean).slice(0, 3)

  return (
    <article className="record-card" onClick={onOpen}>
      <div className="record-card-main">
        <div className="record-map-thumb">
          <span className="record-thumb-pin" />
        </div>

        <div className="record-info">
          <div className="record-title-row">
            <h3>{record.brand_desc || record.business_type || '未命名商铺'}</h3>
            <span className={`record-star ${record.is_pdf_unlocked ? 'is-active' : ''}`}>★</span>
          </div>
          <p className="record-address">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M20 10c0 4.99-5.54 10.19-7.4 11.79a.95.95 0 0 1-1.2 0C9.54 20.19 4 14.99 4 10a8 8 0 0 1 16 0Z" />
              <circle cx="12" cy="10" r="3" />
            </svg>
            {record.address || '暂无地址'}
          </p>
          <div className="record-tags">
            {tags.map(tag => <span key={`${tag.type}-${tag.text}`} className={tag.type}>{tag.text}</span>)}
          </div>
        </div>

        {score > 0 && (
          <div className={`record-score ${tone}`}>
            <strong>{score}</strong><span>分</span>
            <em>综合评分</em>
            <div className="record-stars">
              {stars(score).map((active, index) => <i key={index} className={active ? 'active' : ''}>★</i>)}
            </div>
          </div>
        )}
      </div>

      <div className="record-footer">
        <span>分析时间：{formatDate(record.created_at)}</span>
        <div className="record-actions">
          <button
            type="button"
            className="record-delete"
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            aria-label="删除记录"
          >
            删除
          </button>
          <button type="button" className="record-secondary" onClick={(e) => { e.stopPropagation(); onOpen() }}>
            查看报告
          </button>
          <button
            type="button"
            onClick={(e) => onDownload(record, e)}
            disabled={exportingId === record.report_uuid}
            className={`record-primary ${record.is_pdf_unlocked ? '' : 'is-locked'}`}
          >
            {exportingId === record.report_uuid ? '导出中' : record.is_pdf_unlocked ? '导出PDF' : '导出PDF 🔒'}
          </button>
        </div>
      </div>
    </article>
  )
}

export default function RecordsView() {
  const navigate = useNavigate()
  const [localRecords, setLocalRecords] = useState(null)
  const [deleteConfirmUuid, setDeleteConfirmUuid] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [activeFilter, setActiveFilter] = useState('all')

  const { exportPdf, ExportModal, loading: exportingPdf, toast, showToast } = useReportExport()
  const [exportingId, setExportingId] = useState(null)

  const { data, loading, error, refetch } = useFetch(`/api/records?page=1&page_size=50`)
  const rawRecords = data?.records || []
  const records = localRecords !== null ? localRecords : rawRecords

  const filters = useMemo(() => [
    { key: 'all', label: '全部', count: records.length },
    { key: 'completed', label: '已完成', count: records.length },
    { key: 'analyzing', label: '分析中', count: 0 },
    { key: 'exported', label: '已导出', count: records.filter(r => r.is_pdf_unlocked).length },
  ], [records])

  const visibleRecords = useMemo(() => {
    if (activeFilter === 'exported') return records.filter(r => r.is_pdf_unlocked)
    if (activeFilter === 'analyzing') return []
    return records
  }, [activeFilter, records])

  const handleDownload = useCallback(async (record, e) => {
    e.stopPropagation()
    if (exportingPdf) return
    setExportingId(record.report_uuid)

    try {
      let reportData = {}
      if (record.report_json) {
        try { reportData = JSON.parse(record.report_json) } catch {}
      } else {
        try {
          const r = await fetch(`/api/records/${record.report_uuid}`, {
            headers: { 'Authorization': `Bearer ${getToken()}` }
          }).then(r => r.json())
          if (r?.report_json) { try { reportData = JSON.parse(r.report_json) } catch {} }
        } catch {}
      }

      const result = await exportPdf({
        data: reportData,
        meta: {
          address: record.address || '',
          brandName: record.brand_desc || '',
          businessType: record.business_type || '',
          storeSize: String(record.store_size || ''),
          date: record.created_at?.slice(0, 10),
        },
        reportUuid: record.report_uuid,
        isPdfUnlocked: record.is_pdf_unlocked,
      })

      if (result?.ok && result?.unlocked) {
        const updated = records.map(r => r.report_uuid === record.report_uuid ? { ...r, is_pdf_unlocked: true } : r)
        setLocalRecords(updated)
      }
    } catch {
      showToast('导出失败，请重试')
    } finally {
      setExportingId(null)
    }
  }, [exportPdf, exportingPdf, records, showToast])

  const handleDeleteConfirm = async () => {
    if (deleting || !deleteConfirmUuid) return
    setDeleting(true)
    try {
      const r = await fetch(`/api/records/${deleteConfirmUuid}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` },
      })
      const d = await r.json()
      if (d.ok) {
        setLocalRecords(prev => (prev !== null ? prev : rawRecords).filter(item => item.report_uuid !== deleteConfirmUuid))
        showToast('已删除')
      } else {
        showToast(d.error || d.detail || '删除失败')
      }
    } catch { showToast('网络异常，请重试') }
    finally { setDeleting(false); setDeleteConfirmUuid(null) }
  }

  return (
    <div className="records-page">
      {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-[300] rounded-full bg-slate-800 text-white text-xs px-5 py-2 shadow-lg">{toast}</div>}
      <ExportModal />

      <header className="records-header">
        <div>
          <h2>分析记录</h2>
          <p>历史分析，助力决策</p>
        </div>
      </header>

      <div className="records-filter-tabs">
        {filters.map(item => (
          <button
            key={item.key}
            type="button"
            className={activeFilter === item.key ? 'is-active' : ''}
            onClick={() => setActiveFilter(item.key)}
          >
            <span>{item.label}</span>
            <em>{item.count}</em>
          </button>
        ))}
      </div>

      <main className="records-list">
        {loading ? <LoadingCard /> :
         error ? <ErrorCard msg={error} onRetry={() => { setLocalRecords(null); refetch() }} /> :
         visibleRecords.length === 0 ? <EmptyCard /> : (
          visibleRecords.map(r => (
            <RecordCard
              key={r.id}
              record={r}
              exportingId={exportingId}
              onDownload={handleDownload}
              onDelete={() => setDeleteConfirmUuid(r.report_uuid)}
              onOpen={() => navigate(`/record/${r.report_uuid}`)}
            />
          ))
        )}
      </main>

      {deleteConfirmUuid && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setDeleteConfirmId(null)}>
          <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-bold text-slate-900">确定要删除该条分析记录吗？</h3>
            <p className="mt-2 text-sm leading-5 text-slate-500">删除后将无法恢复，报告文件也将一并销毁。</p>
            <div className="mt-5 flex gap-3">
              <button onClick={() => setDeleteConfirmId(null)} disabled={deleting}
                className="flex-1 rounded-lg border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">取消</button>
              <button onClick={handleDeleteConfirm} disabled={deleting}
                className="flex-1 rounded-lg bg-red-600 py-2.5 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-50">
                {deleting ? '删除中...' : '确定删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
