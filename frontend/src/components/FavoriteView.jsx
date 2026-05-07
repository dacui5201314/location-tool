import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import useFetch from '../hooks/useFetch'
import { getToken } from '../services/api'

function LoadingCard() {
  return (
    <div className="favorites-state-card">
      <div className="flex justify-center gap-2 mb-3">
        <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
        <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
        <div className="w-2 h-2 rounded-full bg-blue-500 pulse-dot" />
      </div>
      <div className="text-sm text-slate-400">加载中...</div>
    </div>
  )
}

function EmptyCard({ onAdd }) {
  return (
    <div className="favorites-state-card">
      <div className="text-4xl mb-3">☆</div>
      <div className="text-sm font-semibold text-slate-600">暂无收藏地址</div>
      <div className="text-xs text-slate-400 mt-1">把待评估铺位加入收藏，后续可快速生成报告</div>
      <button onClick={onAdd} className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-xs font-bold text-white">新增地址</button>
    </div>
  )
}

function ErrorCard({ msg, onRetry }) {
  return (
    <div className="favorites-state-card">
      <div className="text-2xl mb-2">⚠️</div>
      <div className="text-sm text-red-500 mb-3">{msg}</div>
      <button onClick={onRetry} className="rounded-lg bg-blue-600 text-white text-xs font-semibold px-4 py-2">点击重试</button>
    </div>
  )
}

function formatDate(value) {
  if (!value) return '未知时间'
  try { return new Date(value + 'Z').toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) } catch { return value.slice(0, 16).replace('T', ' ') }
}

function scoreFor(item) {
  const score = Number(item.report_overall_score || 0)
  return score > 0 ? score : null
}

function FavoriteCard({ item, manageMode, deleting, onDelete, onAnalyze, onReport }) {
  const score = scoreFor(item)
  const title = item.report_brand_desc || item.custom_name || item.address || '收藏地址'
  const address = item.report_address || item.address || '暂无地址'
  const timeLabel = item.is_analyzed ? '分析时间' : '收藏时间'
  const timeValue = formatDate(item.is_analyzed ? (item.report_created_at || item.created_at) : item.created_at)

  return (
    <article className="favorite-card">
      <div className="favorite-thumb" aria-hidden="true">
        <i className="building building-a" />
        <i className="building building-b" />
        <i className="building building-c" />
        <i className="street-light" />
        <span />
      </div>

      <div className="favorite-body">
        <h3>{title}</h3>

        <p className="favorite-address">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M20 10c0 4.99-5.54 10.19-7.4 11.79a.95.95 0 0 1-1.2 0C9.54 20.19 4 14.99 4 10a8 8 0 0 1 16 0Z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          {address}
        </p>

        <div className="favorite-time-inline">
          {timeLabel}：{timeValue}
        </div>
      </div>

      <div className="favorite-actions">
        <div className="favorite-side-top">
          <span className={`favorite-status ${item.is_analyzed ? 'done' : 'pending'}`}>
            {item.is_analyzed ? '已分析' : '待分析'}
          </span>
          <span className={`favorite-star ${item.is_analyzed ? 'active' : ''}`}>★</span>
        </div>
        {manageMode ? (
          <button type="button" className="favorite-remove" disabled={deleting} onClick={onDelete}>
            {deleting ? '移除中' : '移除'}
          </button>
        ) : item.is_analyzed ? (
          <>
            <button type="button" className="favorite-report" onClick={onReport}>
              <span>▤</span> 查看报告
            </button>
            <button type="button" className="favorite-delete-mini" disabled={deleting} onClick={onDelete}>
              {deleting ? '删除中' : '删除地址'}
            </button>
            {score && <strong>综合评分：<b>{score}</b>分</strong>}
          </>
        ) : (
          <>
            <button type="button" className="favorite-analyze" onClick={onAnalyze}>
              <span>✎</span> 评估赚钱潜力
            </button>
            <button type="button" className="favorite-delete-mini" disabled={deleting} onClick={onDelete}>
              {deleting ? '删除中' : '删除地址'}
            </button>
          </>
        )}
      </div>
    </article>
  )
}

export default function FavoriteView() {
  const navigate = useNavigate()
  const { data, loading, error, refetch } = useFetch('/api/favorites')
  const favorites = data?.favorites || []
  const [deletingId, setDeletingId] = useState(null)
  const [deleteTarget, setDeleteTarget] = useState(null)
  const [manageMode, setManageMode] = useState(false)
  const [activeTab, setActiveTab] = useState('all')
  const [sortMode, setSortMode] = useState('latest')

  const counts = useMemo(() => ({
    all: favorites.length,
    pending: favorites.filter(f => !f.is_analyzed).length,
    analyzed: favorites.filter(f => f.is_analyzed).length,
  }), [favorites])

  const visibleFavorites = useMemo(() => {
    const filtered = favorites.filter(item => {
      if (activeTab === 'pending') return !item.is_analyzed
      if (activeTab === 'analyzed') return item.is_analyzed
      return true
    })
    return [...filtered].sort((a, b) => {
      if (sortMode === 'analyzed') return Number(b.is_analyzed) - Number(a.is_analyzed)
      return String(b.created_at || '').localeCompare(String(a.created_at || ''))
    })
  }, [activeTab, favorites, sortMode])

  const handleDelete = async () => {
    if (deletingId || !deleteTarget) return
    setDeletingId(deleteTarget.id)
    try {
      const r = await fetch(`/api/favorites/${deleteTarget.id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${getToken()}` },
      })
      if (r.ok) {
        setDeleteTarget(null)
        refetch()
      }
    } catch {}
    finally { setDeletingId(null) }
  }

  const requestDelete = (item) => setDeleteTarget(item)

  const handleAdd = () => navigate('/', { replace: true })

  return (
    <div className="favorites-page">
      <header className="favorites-header">
        <div>
          <h2>收藏地址</h2>
          <p>保存的地址，可随时发起分析</p>
        </div>
        <button type="button" className={manageMode ? 'is-active' : ''} onClick={() => setManageMode(v => !v)}>
          <span>✎</span>{manageMode ? '完成' : '批量管理'}
        </button>
      </header>

      <section className="favorites-summary">
        <div className="favorites-summary-icon" aria-hidden="true">
          <span>★</span>
        </div>
        <div>
          <strong>你已收藏 {counts.all} 个地址</strong>
          <p>其中 {counts.pending} 个待分析，{counts.analyzed} 个已完成分析</p>
        </div>
        <button type="button" onClick={handleAdd}>
          <span>＋</span>新增地址
        </button>
      </section>

      <div className="favorites-toolbar">
        <div className="favorites-tabs">
          <button className={activeTab === 'all' ? 'is-active' : ''} onClick={() => setActiveTab('all')}>全部 <em>{counts.all}</em></button>
          <button className={activeTab === 'pending' ? 'is-active' : ''} onClick={() => setActiveTab('pending')}>待分析 <em>{counts.pending}</em></button>
          <button className={activeTab === 'analyzed' ? 'is-active' : ''} onClick={() => setActiveTab('analyzed')}>已分析 <em>{counts.analyzed}</em></button>
        </div>
        <button type="button" className="favorites-sort" onClick={() => setSortMode(v => v === 'latest' ? 'analyzed' : 'latest')}>
          {sortMode === 'latest' ? '最新收藏' : '已分析优先'}⌄
        </button>
      </div>

      <main className="favorites-list">
        {loading ? <LoadingCard /> :
         error ? <ErrorCard msg={error} onRetry={refetch} /> :
         visibleFavorites.length === 0 ? <EmptyCard onAdd={handleAdd} /> : (
          visibleFavorites.map(item => (
            <FavoriteCard
              key={item.id}
              item={item}
              manageMode={manageMode}
              deleting={deletingId === item.id}
              onDelete={() => requestDelete(item)}
              onAnalyze={() => navigate('/', { replace: true, state: { loc: item } })}
              onReport={() => navigate(`/record/${item.report_id}`)}
            />
          ))
        )}
      </main>

      {deleteTarget && (
        <div className="favorite-delete-modal" onClick={() => !deletingId && setDeleteTarget(null)}>
          <div className="favorite-delete-dialog" onClick={e => e.stopPropagation()}>
            <h3>确认删除该收藏地址？</h3>
            <p>{deleteTarget.custom_name || deleteTarget.address || '该地址'} 删除后将从收藏列表移除，已生成的分析记录不会被删除。</p>
            <div>
              <button type="button" className="cancel" disabled={!!deletingId} onClick={() => setDeleteTarget(null)}>
                取消删除
              </button>
              <button type="button" className="confirm" disabled={!!deletingId} onClick={handleDelete}>
                {deletingId ? '删除中...' : '确认删除'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
