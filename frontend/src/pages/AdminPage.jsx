import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { adminLogin, getAdminToken, clearAdminToken, fetchSystemSettings, saveSystemSettings, getAssetUrl } from '../services/api'
import CorePromptEditor from '../components/CorePromptEditor'
import IndustryRuleDrawer from '../components/IndustryRuleDrawer'

const QR_ACCEPT = 'image/png,image/jpeg,image/gif,image/webp'
const assetName = (url = '') => (url.startsWith('/assets/') ? url.split('/').pop() || '' : '')
const isForeignAssetUrl = (url, tag) => {
  const name = assetName(url)
  if (!name) return false
  if (tag === 'cs' && name === 'official_qrcode.png') return true
  return ['brand_', 'cs_'].some(prefix => name.startsWith(prefix)) && !name.startsWith(`${tag}_`)
}
const normalizeQrUrl = (url, tag) => (isForeignAssetUrl(url || '', tag) ? '' : (url || ''))
const makeNewSku = (type = 'points') => ({
  id: Date.now(),
  type,
  label: '',
  price: '0',
  credits: type === 'points' ? 1 : 0,
  tier: type === 'membership' ? 'monthly' : '',
  duration_days: type === 'membership' ? 30 : 0,
  badge: '',
  desc: '',
  visible: true,
})

function UiCustomerConfigCard({ uiConfig, setUiConfig, adminFetch, showToast }) {
  const [dirty, setDirty] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const update = (patch) => {
    setUiConfig(c => ({ ...c, ...patch }))
    setDirty(true)
    setError('')
  }

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const textConfig = {
        announcement: uiConfig.announcement || '',
        cs_wechat: uiConfig.cs_wechat || '',
        cs_phone: uiConfig.cs_phone || '',
        customer_service_name: uiConfig.customer_service_name || '',
      }
      const resp = await adminFetch('/ui-config', { method: 'PUT', body: JSON.stringify(textConfig) })
      const data = await resp.json().catch(() => ({}))
      if (!resp.ok) throw new Error(data.detail || '保存失败')
      setUiConfig(c => ({ ...c, ...textConfig }))
      setDirty(false)
      showToast('UI 客服配置已保存')
    } catch (err) {
      const msg = err?.message || '保存失败'
      setError(msg)
      showToast(msg)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="text-sm font-bold text-slate-800 mb-1">UI 客服配置</div>
          <div className="text-[11px] text-slate-400">控制前端公告栏和联系客服文案，不包含二维码文件</div>
        </div>
        <span className={`text-[10px] font-semibold rounded-full px-2 py-0.5 ${dirty ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
          {dirty ? '未保存' : '已同步'}
        </span>
      </div>
      <div className="space-y-3">
        <div>
          <label className="text-xs font-semibold text-slate-500">全局公告文案（留空则隐藏）</label>
          <input value={uiConfig.announcement} onChange={e => update({ announcement: e.target.value })}
            placeholder="如：系统维护中，预计22:00恢复" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label className="text-xs font-semibold text-slate-500">客服名称</label>
            <input value={uiConfig.customer_service_name || ''} onChange={e => update({ customer_service_name: e.target.value })}
              placeholder="如：大崔" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500">客服微信号</label>
            <input value={uiConfig.cs_wechat} onChange={e => update({ cs_wechat: e.target.value })}
              placeholder="如：support_2026" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
          </div>
          <div>
            <label className="text-xs font-semibold text-slate-500">客服电话</label>
            <input value={uiConfig.cs_phone || ''} onChange={e => update({ cs_phone: e.target.value })}
              placeholder="选填" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
          </div>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2">
        <button onClick={save} disabled={!dirty || saving}
          className="rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5 disabled:opacity-50">
          {saving ? '保存中...' : dirty ? '单独保存 UI 客服配置' : 'UI 客服配置已保存'}
        </button>
        {error && <span className="text-[10px] font-semibold text-red-500">{error}</span>}
      </div>
    </div>
  )
}

function QrcodeSlotCard({ slot, title, description, uploadPath, adminFetch, showToast }) {
  const [qrUrl, setQrUrl] = useState('')
  const [dirty, setDirty] = useState(false)
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')

  const oppositeLabel = slot === 'cs' ? '品牌' : '客服'
  const successText = slot === 'brand' ? '品牌二维码已保存，PDF 导出将使用新图' : '客服二维码已保存'

  useEffect(() => {
    setLoading(true)
    fetch(`/api/admin/qrcode-slot/${slot}`)
      .then(r => r.json())
      .then(d => {
        setQrUrl(normalizeQrUrl(d.url, slot))
        setDirty(false)
        setError('')
      })
      .catch(() => setError('二维码加载失败'))
      .finally(() => setLoading(false))
  }, [slot])

  const uploadQr = async (file) => {
    if (uploading) return
    setUploading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('file', file)
      const r = await adminFetch(uploadPath, { method: 'POST', body: form })
      const d = await r.json()
      if (!r.ok || !d.ok) throw new Error(d.detail || '上传失败')
      const nextUrl = normalizeQrUrl(d.url || `/assets/${d.filename}`, slot)
      if (!nextUrl) throw new Error('上传接口返回了错误的二维码文件')
      setQrUrl(nextUrl)
      setDirty(true)
      showToast(`${title}已上传，请点击保存后生效`)
    } catch (err) {
      const msg = err?.message || '上传失败'
      setError(msg)
      showToast(msg)
    } finally {
      setUploading(false)
    }
  }

  const save = async () => {
    setSaving(true)
    setError('')
    try {
      const safeQrUrl = normalizeQrUrl(qrUrl, slot)
      if (qrUrl && !safeQrUrl) {
        setQrUrl('')
        setDirty(false)
        showToast(`已拦截${oppositeLabel}二维码进入${title}`)
        return
      }
      const r = await adminFetch(`/qrcode-slot/${slot}`, { method: 'PUT', body: JSON.stringify({ url: safeQrUrl }) })
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || '保存失败')
      setDirty(false)
      showToast(safeQrUrl ? successText : `${title}已清除`)
    } catch (err) {
      const msg = err?.message || '保存失败'
      setError(msg)
      showToast(msg)
    } finally {
      setSaving(false)
    }
  }

  const isBrand = slot === 'brand'

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
      <div className="flex items-start justify-between gap-3 mb-4">
        <div>
          <div className="text-sm font-bold text-slate-800 mb-1">{title}</div>
          <div className="text-[11px] text-slate-400">{description}</div>
        </div>
        <span className={`text-[10px] font-semibold rounded-full px-2 py-0.5 ${dirty ? 'bg-amber-50 text-amber-600' : 'bg-emerald-50 text-emerald-600'}`}>
          {dirty ? '未保存' : loading ? '加载中' : '已同步'}
        </span>
      </div>

      <div className={`flex items-start gap-5 ${isBrand ? '' : 'max-w-xl'}`}>
        <div className="flex-1">
          <label
            className={`${isBrand ? 'min-h-[138px]' : 'min-h-[78px]'} flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-200 p-4 cursor-pointer hover:border-blue-300 hover:bg-blue-50/50 transition-colors`}
            onDragOver={e => { e.preventDefault(); e.currentTarget.style.borderColor = '#3b82f6' }}
            onDragLeave={e => { e.currentTarget.style.borderColor = '#cbd5e1' }}
            onDrop={async e => {
              e.preventDefault()
              e.currentTarget.style.borderColor = '#cbd5e1'
              const file = e.dataTransfer.files?.[0]
              if (file) await uploadQr(file)
            }}
          >
            {uploading ? (
              <div className="flex items-center gap-2 text-sm text-blue-600">
                <span className="inline-block w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                上传中...
              </div>
            ) : (
              <>
                <div className="text-2xl text-slate-300">📁</div>
                <div className="text-xs text-slate-500">点击或拖拽上传二维码</div>
                <div className="text-[10px] text-slate-400">支持 PNG / JPG / WebP / GIF，最大 2MB</div>
              </>
            )}
            <input type="file" accept={QR_ACCEPT} className="hidden"
              onChange={e => {
                const f = e.target.files?.[0]
                e.target.value = null
                if (f) uploadQr(f)
              }}
            />
          </label>
        </div>

        <div className="flex-shrink-0 w-[110px]">
          <div className="text-[10px] text-slate-400 mb-1.5 text-center">当前二维码</div>
          {qrUrl ? (
            <div className="space-y-2">
              <img src={getAssetUrl(qrUrl)} alt={title}
                className="w-[110px] h-[110px] object-contain rounded-lg border border-slate-200 shadow-sm" />
              <div className="text-[10px] text-emerald-600 font-semibold text-center">✅ 已配置</div>
            </div>
          ) : (
            <div className="w-[110px] h-[110px] rounded-lg border-2 border-dashed border-slate-200 bg-slate-50 flex items-center justify-center">
              <div className="text-[10px] text-slate-400 text-center leading-4">暂未<br/>上传</div>
            </div>
          )}
        </div>
      </div>

      {qrUrl && (
        <div className="mt-3 p-2 rounded-lg bg-emerald-50 border border-emerald-100 text-[11px] text-emerald-700 font-medium">
          {dirty ? '预览已更新，点击保存后才会生效。' : '当前二维码已保存并按独立槽位读取。'}
        </div>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        <button onClick={save} disabled={!dirty || saving}
          className="rounded-lg bg-blue-600 text-white text-xs font-semibold px-3 py-1.5 hover:bg-blue-700 disabled:opacity-50">
          {saving ? '保存中...' : dirty ? `保存${title}` : `${title}已保存`}
        </button>
        <button onClick={() => { setQrUrl(''); setDirty(true) }}
          className="rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5 hover:bg-slate-200">
          清除预览
        </button>
        {error && <span className="self-center text-[10px] font-semibold text-red-500">{error}</span>}
      </div>
    </div>
  )
}

export default function AdminPage() {
  const navigate = useNavigate()
  const [pwd, setPwd] = useState('')
  const [authed, setAuthed] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'dashboard'
  const setTab = (key) => setSearchParams({ tab: key })

  // ★ 数据统一在此加载，避免 onClick 中重复调用
  useEffect(() => {
    if (tab === 'users') loadUsers(userFilter, 1)
    if (tab === 'settings') loadSettingsData()
    if (tab === 'oplogs') loadOpLogs()
    if (tab === 'industries') loadIndustries()
    if (tab === 'logs') adminFetch('/logs').then(r => r.json()).then(d => setLogs(d.logs || [])).catch(() => {})
    if (tab === 'cdk') loadCdk()
    if (tab === 'sysparams') fetchSystemSettings().then(d => setSystemParams(d.configs || {})).catch(() => showToast('加载全局参数失败'))
  }, [tab])

  const [stats, setStats] = useState(null)
  const [users, setUsers] = useState([])
  const [settings, setSettings] = useState({
    amap_key: '',
    ai_provider: 'deepseek',
    ai_key: '',
    system_prompt: '',
    wx_mch_id: '',
    wx_app_id: '',
    wx_api_key: '',
    wx_cert_sn: '',
    wx_notify_url: '',
  })
  const [skus, setSkus] = useState([])
  const [uiConfig, setUiConfig] = useState({ announcement: '', cs_wechat: '', cs_phone: '', customer_service_name: '', customer_service_qr_url: '' })  // customer_service_qr_url 仅用于 DB 持久化，预览不用此字段
  const [logs, setLogs] = useState([])
  const [cdkList, setCdkList] = useState([])
  const [cdkGen, setCdkGen] = useState({ prefix: 'AI', count: 10, credits: 1, days_valid: 90 })
  const [trends, setTrends] = useState(null)
  const [showAiKey, setShowAiKey] = useState(false)
  // ★ CorePromptEditor 状态已移至独立组件，消除全局重渲染
  const [dashTrends, setDashTrends] = useState({ dates: [], counts: [] })
  const [opLogs, setOpLogs] = useState([])
  // ── 业态规则管理 ──
  const [industries, setIndustries] = useState([])
  const [industryModal, setIndustryModal] = useState(null) // null | { id?, name, sort_order, is_active }
  const [industrySaving, setIndustrySaving] = useState(false)
  const [promptEditor, setPromptEditor] = useState(null) // null | industry object (full)
  // ★ IndustryRuleDrawer 状态已移至独立组件，消除全局重渲染
  const [industryDeleteConfirm, setIndustryDeleteConfirm] = useState(null) // null | industry object
  const [pdfConfig, setPdfConfig] = useState({ logo_url: '', footer_text: 'AI 选址分析 · 商业选址初筛参考' })
  const [storageConfig, setStorageConfig] = useState({
    storage_mode: 'local',
    oss_endpoint: '',
    oss_bucket: '',
    oss_access_key_id: '',
    oss_access_key_secret: '',
  })
  const [confirmSave, setConfirmSave] = useState(false)
  const [systemParams, setSystemParams] = useState({})
  const [systemParamsSaving, setSystemParamsSaving] = useState(false)
  const [settingsDirty, setSettingsDirty] = useState(false)
  const [settingsSaving, setSettingsSaving] = useState(false)
  const [settingsLoaded, setSettingsLoaded] = useState(false)  // ★ 防误清空：配置从 DB 加载完成前禁止保存
  const [skusDirty, setSkusDirty] = useState(false)
  const [pdfDirty, setPdfDirty] = useState(false)
  const [storageDirty, setStorageDirty] = useState(false)
  const [skuModal, setSkuModal] = useState(null)
  const [userSkuDraft, setUserSkuDraft] = useState([])
  const [userSkuInherited, setUserSkuInherited] = useState(true)
  const [userSkuLoading, setUserSkuLoading] = useState(false)
  const [userSkuSaving, setUserSkuSaving] = useState(false)
  const [userSkuApplyingId, setUserSkuApplyingId] = useState(null)

  // ── 列表前端分页（每页20条，减少DOM节点）──
  const PAGE_SIZE = 15
  const [opLogsPage, setOpLogsPage] = useState(1)
  const [logsPage, setLogsPage] = useState(1)
  const [cdkPage, setCdkPage] = useState(1)
  const [industriesPage, setIndustriesPage] = useState(1)
  const [usersPage, setUsersPage] = useState(1)
  const [usersTotal, setUsersTotal] = useState(0)
  // 切标签页时重置分页
  useEffect(() => { setOpLogsPage(1); setLogsPage(1); setCdkPage(1); setIndustriesPage(1); setUsersPage(1) }, [tab])

  const Paginator = ({ page, total, onPage }) => {
    if (total <= PAGE_SIZE) return null
    const maxPage = Math.ceil(total / PAGE_SIZE)
    return (
      <div className="flex items-center justify-end gap-2 px-4 py-3 border-t border-slate-100 bg-slate-50">
        <span className="text-xs text-slate-400">{page}/{maxPage} 页（共{total}条）</span>
        <button onClick={() => onPage(Math.max(1, page - 1))} disabled={page <= 1}
          className="rounded border border-slate-200 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-white disabled:opacity-30">上一页</button>
        <button onClick={() => onPage(Math.min(maxPage, page + 1))} disabled={page >= maxPage}
          className="rounded border border-slate-200 px-2 py-1 text-xs font-medium text-slate-600 hover:bg-white disabled:opacity-30">下一页</button>
      </div>
    )
  }

  const updateParam = (key, value) => {
    setSystemParams(prev => {
      const existing = prev?.[key] || {}
      return { ...prev, [key]: { ...existing, value } }
    })
  }
  const showToast = useCallback((msg) => {
    const el = document.createElement('div')
    el.className = 'fixed top-5 left-1/2 -translate-x-1/2 z-[9999] rounded-full bg-slate-800 text-white text-xs px-5 py-2 shadow-lg whitespace-nowrap'
    el.textContent = msg
    document.body.appendChild(el)
    setTimeout(() => { el.style.opacity = '0'; el.style.transition = 'opacity 0.3s'; setTimeout(() => el.remove(), 300) }, 2000)
  }, [])
  const updateSettings = (patch) => { setSettings(s => ({ ...s, ...patch })); setSettingsDirty(true) }
  const updatePdfConfig = (patch) => { setPdfConfig(c => ({ ...c, ...patch })); setPdfDirty(true) }
  const updateStorageConfig = (patch) => { setStorageConfig(c => ({ ...c, ...patch })); setStorageDirty(true) }
  const updateSkuAt = (index, patch) => {
    setSkus(prev => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)))
    setSkusDirty(true)
  }
  const updateUserSkuAt = (index, patch) => {
    setUserSkuDraft(prev => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)))
  }

  const adminFetch = useCallback((path, options = {}) => {
    const token = getAdminToken()
    const headers = { ...options.headers }
    if (token) headers['Authorization'] = `Bearer ${token}`
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }
    return fetch(`/api/admin${path}`, { ...options, headers })
  }, [])

  // ── 数据加载器（必须在 adminFetch/showToast 之后定义）──
  const loadCdk = useCallback(() => { adminFetch('/cdk/list').then(r => r.json()).then(d => setCdkList(d.codes || [])).catch(() => showToast('CDK列表加载失败')) }, [adminFetch, showToast])
  const loadOpLogs = useCallback(() => { adminFetch('/operation-logs').then(r => r.json()).then(d => setOpLogs(d.logs || [])).catch(() => showToast('操作记录加载失败')) }, [adminFetch, showToast])
  const loadIndustries = useCallback(() => { adminFetch('/industries').then(r => r.json()).then(d => setIndustries(d.industries || [])).catch(() => showToast('业态列表加载失败')) }, [adminFetch, showToast])

  const loadSettingsData = () => {
    fetch('/api/admin/skus').then(r => r.json()).then(d => { setSkus(d.skus || []); setSkusDirty(false) }).catch(() => showToast('套餐列表加载失败'))
    // ★ 防止 /config 的 system_prompt:"" 空值覆盖 /core-prompt 已加载的默认Prompt
    adminFetch('/config').then(r => r.json()).then(d => {
      setSettings(s => ({ ...s, ...d, system_prompt: s.system_prompt || d.system_prompt || '' }))
      setSettingsDirty(false)
    }).catch(() => { showToast('核心配置加载失败') })
    // 拉取核心 Prompt（含默认值回退）— 成功后标记 settingsLoaded
    adminFetch('/config/core-prompt').then(r => r.json()).then(d => {
      if (d.system_prompt) {
        setSettings(s => ({ ...s, system_prompt: d.system_prompt }))
      }
      setSettingsLoaded(true)
    }).catch(() => { showToast('提示词加载失败'); setSettingsLoaded(true) })
    fetch('/api/admin/ui-config').then(r => r.json()).then(d => {
      setUiConfig({ ...d, customer_service_qr_url: '' })
    }).catch(() => showToast('UI客服配置加载失败'))
    adminFetch('/pdf-config').then(r => r.json()).then(d => { setPdfConfig(d); setPdfDirty(false) }).catch(() => showToast('PDF品牌配置加载失败'))
    adminFetch('/storage-config').then(r => r.json()).then(d => { setStorageConfig(d); setStorageDirty(false) }).catch(() => showToast('存储配置加载失败'))
    adminFetch('/trends').then(r => r.json()).then(d => { setTrends(d); setDashTrends(prev => ({ ...prev, industry: d?.top_business_types || [], brands: d?.top_brands || [] })) }).catch(() => showToast('趋势数据加载失败'))
    adminFetch('/dashboard/stats').then(r => r.json()).then(d => {
      if (d?.trend_dates) setDashTrends(prev => ({ ...prev, dates: d.trend_dates, counts: d.trend_counts || [] }))
    }).catch(() => {})
  }

  // ★ 刷新时恢复管理员会话
  useEffect(() => {
    const token = getAdminToken()
    if (token) {
      setAuthed(true)
    }
    setIsChecking(false)
  }, [])

  useEffect(() => {
    if (!authed) return
    adminFetch('/stats').then(r => r.json()).then(setStats).catch(() => {
      clearAdminToken()
      setAuthed(false)
    })
  }, [authed])

  const [loginLoading, setLoginLoading] = useState(false)

  const handleLogin = async () => {
    setLoginLoading(true)
    try {
      await adminLogin(pwd)
      setAuthed(true)
    } catch {
      showToast('密码错误')
    } finally {
      setLoginLoading(false)
    }
  }

  const [userFilter, setUserFilter] = useState({ phone: '', member: '', channel: '', dateFrom: '', dateTo: '' })
  const loadUsers = (filter = userFilter, page = usersPage) => {
    const params = new URLSearchParams()
    params.set('page', String(page))
    params.set('page_size', String(PAGE_SIZE))
    if (filter.phone) params.set('phone', filter.phone)
    if (filter.member) params.set('member', filter.member)
    if (filter.channel) params.set('channel', filter.channel)
    if (filter.dateFrom) params.set('date_from', filter.dateFrom)
    if (filter.dateTo) params.set('date_to', filter.dateTo)
    const qs = params.toString()
    adminFetch(`/users?${qs}`).then(r => {
      if (!r.ok) {
        if (r.status === 401) { clearAdminToken(); setAuthed(false); showToast('管理员登录已过期，请重新登录') }
        else throw new Error(`HTTP ${r.status}`)
        return
      }
      return r.json().then(d => {
        setUsers(d.users || [])
        setUsersTotal(d.total || 0)
        setUsersPage(d.page || page)
      })
    }).catch(() => showToast('用户列表加载失败'))
  }
  const handleUserFilter = () => {
    setUsersPage(1)
    loadUsers(userFilter, 1)
  }
  const resetUserFilter = () => {
    const emptyFilter = { phone: '', member: '', channel: '', dateFrom: '', dateTo: '' }
    setUserFilter(emptyFilter)
    setUsersPage(1)
    loadUsers(emptyFilter, 1)
  }
  const changeUsersPage = (page) => {
    setUsersPage(page)
    loadUsers(userFilter, page)
  }
  const [creditModal, setCreditModal] = useState(null) // { userId, phone }
  const [creditAmount, setCreditAmount] = useState(10)
  const [creditReason, setCreditReason] = useState('')
  const [creditSaving, setCreditSaving] = useState(false)

  // 分配套餐弹窗
  const [pkgModal, setPkgModal] = useState(null) // { userId, phone }
  const [pkgSelected, setPkgSelected] = useState('')
  const [pkgReason, setPkgReason] = useState('')
  const [pkgSaving, setPkgSaving] = useState(false)

  const addCredits = async (userId, amount) => {
    const r = await adminFetch(`/users/${userId}/add-credits`, {
      method: 'POST', body: JSON.stringify({ amount }),
    })
    if (r.ok) { showToast(`已增加 ${amount} 点`); loadUsers(); return true }
    return false
  }

  const openSkuModal = async (user) => {
    setSkuModal({ userId: user.id, phone: user.phone || user.phone_number || '' })
    setUserSkuDraft([])
    setUserSkuInherited(true)
    setUserSkuLoading(true)
    try {
      const r = await adminFetch(`/users/${user.id}/skus`)
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || '套餐加载失败')
      setUserSkuDraft(d.skus || [])
      setUserSkuInherited(Boolean(d.inherited))
    } catch (err) {
      showToast(err?.message || '套餐加载失败')
    } finally {
      setUserSkuLoading(false)
    }
  }

  const saveUserSkus = async () => {
    if (!skuModal) return
    setUserSkuSaving(true)
    try {
      const r = await adminFetch(`/users/${skuModal.userId}/skus`, {
        method: 'PUT',
        body: JSON.stringify({ items: userSkuDraft }),
      })
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || '保存失败')
      setUserSkuDraft(d.skus || [])
      setUserSkuInherited(false)
      showToast('用户专属套餐已保存，客户刷新后可见')
    } catch (err) {
      showToast(err?.message || '保存失败')
    } finally {
      setUserSkuSaving(false)
    }
  }

  const resetUserSkus = async () => {
    if (!skuModal) return
    setUserSkuSaving(true)
    try {
      const r = await adminFetch(`/users/${skuModal.userId}/skus`, { method: 'DELETE' })
      const d = await r.json().catch(() => ({}))
      if (!r.ok) throw new Error(d.detail || '恢复失败')
      setUserSkuDraft(d.skus || [])
      setUserSkuInherited(true)
      showToast('已恢复继承全局套餐')
    } catch (err) {
      showToast(err?.message || '恢复失败')
    } finally {
      setUserSkuSaving(false)
    }
  }

  const applyUserSku = async (item) => {
    if (!skuModal) return
    setUserSkuApplyingId(item.id)
    try {
      const r = await adminFetch(`/users/${skuModal.userId}/apply-sku`, {
        method: 'POST',
        body: JSON.stringify({ item }),
      })
      const d = await r.json().catch(() => ({}))
      if (!r.ok || !d.ok) throw new Error(d.detail || '应用失败')
      setUsers(prev => prev.map(u => (
        u.id === skuModal.userId
          ? { ...u, ...d.user }
          : u
      )))
      showToast(d.message || '套餐已应用到账户')
    } catch (err) {
      showToast(err?.message || '应用失败')
    } finally {
      setUserSkuApplyingId(null)
    }
  }

  if (isChecking) {
    return (
      <div className="admin-page min-h-screen flex items-center justify-center px-4">
        <div className="text-center text-white/70 text-sm">验证登录状态...</div>
      </div>
    )
  }

  if (!authed) {
    return (
      <div className="admin-page min-h-screen flex items-center justify-center px-4">
        <div className="admin-login-card w-full max-w-sm p-8">
          <div className="text-center mb-6">
            <img src="/brand-logo-transparent.png" alt="址得选" className="mx-auto h-14 w-14 object-contain" />
            <div className="text-sm font-bold text-slate-700 mt-3">管理后台</div>
          </div>
          <input type="password" value={pwd} onChange={e => setPwd(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
            placeholder="请输入管理员密码" className="w-full rounded-lg border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-blue-400" />
          <button onClick={handleLogin} disabled={loginLoading}
            className="w-full mt-4 rounded-lg bg-blue-600 py-3 text-sm font-bold text-white disabled:opacity-50 disabled:cursor-not-allowed">
            {loginLoading ? '验证中...' : '登 录'}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="admin-page h-screen flex overflow-hidden bg-slate-50">

      {/* ═══════════ 左侧边栏 ═══════════ */}
      <aside className="w-64 h-full flex-shrink-0 flex flex-col" style={{ background: 'linear-gradient(180deg, #0f172a 0%, #1e293b 100%)' }}>
        <div className="px-5 py-5 border-b border-white/10">
          <div className="flex items-center gap-2.5">
            <img
              src="/brand-logo-transparent.png"
              alt="址得选"
              className="h-10 w-10 rounded-xl object-contain"
            />
            <div>
              <div className="text-sm font-bold text-white">址得选</div>
              <div className="text-[10px] text-slate-400">管理后台</div>
            </div>
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {[
            { key: 'dashboard', label: '仪表盘', icon: '📊' },
            { key: 'users', label: '用户管理', icon: '👥' },
            { key: 'settings', label: '系统设置', icon: '⚙️' },
            { key: 'logs', label: '系统日志', icon: '📋' },
            { key: 'cdk', label: '兑换码管理', icon: '🎫' },
            { key: 'sysparams', label: '全局参数', icon: '🔧' },
            { key: 'oplogs', label: '操作记录', icon: '📝' },
            { key: 'industries', label: '业态规则', icon: '🏭' },
          ].map(t => (
            <button key={t.key} onClick={() => {
              setTab(t.key);
            }}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors text-left ${
                tab === t.key ? 'bg-blue-600 text-white shadow-lg shadow-blue-600/25' : 'text-slate-300 hover:bg-white/5 hover:text-white'
              }`}>
              <span className="text-base">{t.icon}</span>
              <span>{t.label}</span>
            </button>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-white/10">
          <button onClick={() => navigate('/')}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
            <span>&larr;</span> 返回前台
          </button>
        </div>
      </aside>

      {/* ═══════════ 右侧主体 ═══════════ */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* 顶部子导航 */}
        <header className="h-14 bg-white shadow-sm border-b border-slate-200 flex items-center justify-between px-6 flex-shrink-0 z-30">
          <div className="flex items-center gap-4">
            <span className="text-sm font-bold text-slate-700">
              {[
                { key: 'dashboard', label: '仪表盘', sub: '数据总览' },
                { key: 'users', label: '用户管理', sub: '用户列表' },
                { key: 'settings', label: '系统设置', sub: '核心配置 | UI配置 | PDF品牌 | 存储配置' },
                { key: 'logs', label: '系统日志', sub: '运行日志' },
                { key: 'cdk', label: '兑换码管理', sub: 'CDK生成 | 激活记录' },
                { key: 'sysparams', label: '全局参数', sub: '注册奖励 | 微信配置' },
                { key: 'oplogs', label: '操作记录', sub: '管理员操作审计日志' },
                { key: 'industries', label: '业态规则', sub: '业态专属提示词 | 测算规则' },
              ].find(t => t.key === tab)?.label || '仪表盘'}
            </span>
            <span className="text-slate-300">/</span>
            <span className="text-xs text-slate-500">
              {[
                { key: 'dashboard', label: '仪表盘', sub: '数据总览' },
                { key: 'users', label: '用户管理', sub: '用户列表' },
                { key: 'settings', label: '系统设置', sub: '核心配置 | UI配置 | PDF品牌 | 存储配置' },
                { key: 'logs', label: '系统日志', sub: '运行日志' },
                { key: 'cdk', label: '兑换码管理', sub: 'CDK生成 | 激活记录' },
                { key: 'sysparams', label: '全局参数', sub: '注册奖励 | 微信配置' },
                { key: 'industries', label: '业态规则', sub: '业态专属提示词 | 测算规则' },
              ].find(t => t.key === tab)?.sub || ''}
            </span>
          </div>
          <button onClick={() => { clearAdminToken(); setAuthed(false) }}
            className="text-xs text-slate-400 hover:text-red-500 transition-colors font-medium">
            退出登录
          </button>
        </header>

        {/* 内容滚动区 */}
        <main className="flex-1 overflow-auto p-6 space-y-4">
        {tab === 'dashboard' && stats && (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: '总用户数', value: stats.total_users, color: '#2563eb' },
                { label: '累计报告', value: stats.total_reports, color: '#16a34a' },
                { label: '今日新增', value: stats.today_users, color: '#7c5cff' },
                { label: '今日报告', value: stats.today_reports, color: '#f59e0b' },
              ].map((s, i) => (
                <div key={i} className="rounded-xl bg-white p-4 shadow-sm border border-slate-100">
                  <div className="text-[11px] text-slate-400">{s.label}</div>
                  <div className="text-2xl font-black mt-1" style={{ color: s.color }}>{s.value}</div>
                </div>
              ))}
            </div>
            {/* 数据罗盘 */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="rounded-xl bg-white p-4 shadow-sm border border-slate-100">
                <div className="text-sm font-bold text-slate-800 mb-3">🔥 热门选址业态</div>
                {(() => {
                  const bizData = trends?.top_business_types?.length ? trends.top_business_types
                    : (dashTrends.industry?.length ? dashTrends.industry : [])
                  if (bizData.length === 0) return <p className="text-xs text-slate-400 py-4 text-center">暂无数据</p>
                  const total = bizData.reduce((s, t) => s + (t.count || 0), 0)
                  const colors = ['#3b82f6', '#06b6d4', '#8b5cf6', '#f59e0b']
                  let acc = 0
                  const slices = bizData.map((t, i) => { const start = acc; acc += (t.count || 0) / total; return { ...t, start, end: acc, color: colors[i % 4] } })
                  const cx = 80, cy = 70, r = 50, sw = 12
                  const circ = 2 * Math.PI * r
                  return (
                    <div className="flex items-center gap-4">
                      <svg width="160" height="140" viewBox="0 0 160 140">
                        {slices.map((s, i) => {
                          const dash = circ * (s.end - s.start)
                          const off = circ * (1 - s.start)
                          return <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color} strokeWidth={sw}
                            strokeDasharray={`${dash} ${circ - dash}`} strokeDashoffset={-off} strokeLinecap="round"
                            transform={`rotate(-90 ${cx} ${cy})`} />
                        })}
                        <text x={cx} y={cy - 4} textAnchor="middle" fontSize="18" fontWeight="900" fill="#1e293b">{bizData.length}</text>
                        <text x={cx} y={cy + 14} textAnchor="middle" fontSize="10" fill="#94a3b8">个业态</text>
                      </svg>
                      <div className="flex-1 space-y-1.5">
                        {bizData.map((t, i) => (
                          <div key={i} className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{ background: colors[i % 4] }} /><span className="text-slate-600">{t.name}</span></div>
                            <span className="font-bold text-slate-800">{t.count}次</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                })()}
              </div>

              <div className="rounded-xl bg-white p-4 shadow-sm border border-slate-100">
                <div className="text-sm font-bold text-slate-800 mb-3">🏷️ 高频分析品牌 TOP 5</div>
                {(() => {
                  const brandData = trends?.top_brands?.length ? trends.top_brands.slice(0, 5)
                    : (dashTrends.brands?.length ? dashTrends.brands : [])
                  if (brandData.length === 0) return <p className="text-xs text-slate-400 py-4 text-center">暂无数据</p>
                  const maxCount = Math.max(...brandData.map(b => b.count || 0))
                  const barColors = ['#3b82f6', '#06b6d4', '#8b5cf6', '#f59e0b', '#10b981']
                  return (
                    <div className="space-y-2.5">
                      {brandData.map((b, i) => (
                        <div key={i} className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 w-7 text-right font-bold">{i + 1}</span>
                          <span className="text-xs text-slate-700 w-16 truncate">{b.name}</span>
                          <div className="flex-1 h-5 bg-slate-100 rounded-full overflow-hidden relative">
                            <div className="h-full rounded-full transition-[width] duration-300" style={{ width: `${((b.count || 0) / maxCount) * 100}%`, background: barColors[i % 5] }} />
                          </div>
                          <span className="text-xs font-bold text-slate-600 w-8 text-right">{b.count}</span>
                        </div>
                      ))}
                    </div>
                  )
                })()}
              </div>
            </div>

            <div className="rounded-xl bg-white p-4 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-3">📈 近15天报告生成趋势</div>
              {(() => {
                const trendData = dashTrends.counts?.length ? dashTrends.counts : [3, 5, 4, 7, 6, 9, 11, 8, 10, 13, 9, 12, 15, 11, 14]
                const trendDates = dashTrends.dates?.length ? dashTrends.dates : trendData.map((_, i) => `D${i + 1}`)
                const maxVal = Math.max(...trendData, 1)
                const w = 700, h = 160, padX = 10, padY = 20
                const gW = w - padX * 2, gH = h - padY * 2
                const pts = trendData.map((v, i) => `${padX + (i / (trendData.length - 1)) * gW},${padY + gH - (v / maxVal) * gH}`)
                const areaPath = `M ${padX},${padY + gH} L ${pts.join(' L ')} L ${padX + gW},${padY + gH} Z`
                const linePath = `M ${pts.join(' L ')}`
                const gradientId = 'trendGradient'
                return (
                  <svg width="100%" height="180" viewBox={`0 0 ${w} ${h + 20}`} preserveAspectRatio="xMidYMid meet">
                    <defs>
                      <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                        <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
                      </linearGradient>
                    </defs>
                    {[0, 0.25, 0.5, 0.75, 1].map(l => (
                      <line key={l} x1={padX} y1={padY + gH * (1 - l)} x2={padX + gW} y2={padY + gH * (1 - l)} stroke="#e2e8f0" strokeWidth="1" />
                    ))}
                    <path d={areaPath} fill={`url(#${gradientId})`} />
                    <path d={linePath} fill="none" stroke="#3b82f6" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                    {/* 垂直 hover 参考线 */}
                    {trendData.map((v, i) => (
                      <line key={`vl-${i}`} x1={padX + (i / (trendData.length - 1)) * gW} y1={padY} x2={padX + (i / (trendData.length - 1)) * gW} y2={padY + gH} stroke="transparent" strokeWidth="20" />
                    ))}
                    {trendData.map((v, i) => (
                      <g key={i}>
                        <title>{trendDates[i]} · {v} 份报告</title>
                        <circle cx={padX + (i / (trendData.length - 1)) * gW} cy={padY + gH - (v / maxVal) * gH} r="10" fill="transparent" />
                        <circle cx={padX + (i / (trendData.length - 1)) * gW} cy={padY + gH - (v / maxVal) * gH} r="3" fill="white" stroke="#3b82f6" strokeWidth="2" />
                        {i % 4 === 0 && <text x={padX + (i / (trendData.length - 1)) * gW} y={h} textAnchor="middle" fontSize="9" fill="#94a3b8">{trendDates[i]}</text>}
                      </g>
                    ))}
                  </svg>
                )
              })()}
            </div>
          </>
        )}

        {tab === 'users' && (
          <div className="space-y-4">
            {/* 筛选面板 */}
            <div style={{ padding: 16, background: '#fff', borderRadius: 8, border: '1px solid #e2e8f0', display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
              <input type="text" value={userFilter.phone} onChange={e => setUserFilter(f => ({ ...f, phone: e.target.value }))}
                placeholder="手机号或ID" onKeyDown={e => e.key === 'Enter' && handleUserFilter()}
                className="h-9 rounded-lg border border-slate-200 px-3 text-sm w-36 focus:outline-none focus:border-blue-400" />
              <select value={userFilter.member} onChange={e => setUserFilter(f => ({ ...f, member: e.target.value }))}
                className="h-9 rounded-lg border border-slate-200 px-3 text-sm focus:outline-none focus:border-blue-400">
                <option value="">全部会员</option><option value="1">会员</option><option value="0">非会员</option>
              </select>
              <select value={userFilter.channel} onChange={e => setUserFilter(f => ({ ...f, channel: e.target.value }))}
                className="h-9 rounded-lg border border-slate-200 px-3 text-sm focus:outline-none focus:border-blue-400">
                <option value="">全部来源</option><option value="web">web</option><option value="phone">phone</option>
              </select>
              <input type="date" value={userFilter.dateFrom} onChange={e => setUserFilter(f => ({ ...f, dateFrom: e.target.value }))}
                className="h-9 rounded-lg border border-slate-200 px-3 text-sm focus:outline-none focus:border-blue-400" />
              <span className="text-xs text-slate-400">至</span>
              <input type="date" value={userFilter.dateTo} onChange={e => setUserFilter(f => ({ ...f, dateTo: e.target.value }))}
                className="h-9 rounded-lg border border-slate-200 px-3 text-sm focus:outline-none focus:border-blue-400" />
              <button onClick={handleUserFilter}
                className="h-9 rounded-lg bg-blue-600 text-white text-sm font-semibold px-4 hover:bg-blue-700">🔍 查询</button>
              <button onClick={resetUserFilter}
                className="h-9 rounded-lg border border-slate-200 text-slate-600 text-sm font-medium px-4 hover:bg-slate-50">重置</button>
            </div>
            <div className="flex items-center justify-between">
              <div className="text-sm text-slate-500">共 {usersTotal} 位用户</div>
              <button onClick={() => loadUsers(userFilter, usersPage)} className="text-sm text-blue-600 font-semibold hover:text-blue-700">刷新列表</button>
            </div>
            <div className="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden contain-paint">
              <div className="max-h-[70vh] overflow-y-auto overscroll-contain">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 z-10">
                    <tr className="bg-slate-50">
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">ID</th>
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">手机号</th>
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">点数</th>
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">会员</th>
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">到期</th>
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">来源</th>
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">报告</th>
                      <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">注册时间</th>
                      <th className="text-center px-4 py-4 text-[15px] font-semibold text-slate-600">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {users.map(u => (
                      <tr key={u.id} className="hover:bg-slate-50">
                        <td className="px-4 py-4 font-mono text-slate-400">#{u.id}</td>
                        <td className="px-4 py-4">
                          <span className="font-semibold text-slate-700">{u.phone || u.phone_number || '—'}</span>
                        </td>
                        <td className="px-4 py-4">
                          <span className={`font-bold text-[15px] ${u.balance_credits > 0 ? 'text-blue-600' : 'text-red-500'}`}>{u.balance_credits}</span>
                        </td>
                        <td className="px-4 py-4">
                          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                            u.is_member ? 'bg-violet-50 text-violet-600' : 'bg-slate-100 text-slate-500'
                          }`}>{u.membership_label || u.membership_tier}</span>
                        </td>
                        <td className="px-4 py-4 text-slate-500">
                          {u.membership_expiry ? (
                            <div className="leading-5">
                              <div className="font-semibold text-slate-600">{u.membership_expiry.slice(0, 10)}</div>
                              <div className="text-xs text-violet-500">剩余 {u.membership_days_left || 0} 天</div>
                            </div>
                          ) : '—'}
                        </td>
                        <td className="px-4 py-4">
                          <span className={`text-xs px-2 py-0.5 rounded ${
                            u.channel === 'phone' ? 'bg-emerald-50 text-emerald-600' :
                            u.channel === 'official_account' ? 'bg-blue-50 text-blue-600' :
                            'bg-slate-50 text-slate-500'
                          }`}>{u.channel || 'web'}</span>
                        </td>
                        <td className="px-4 py-4 text-slate-500">{u.report_count}</td>
                        <td className="px-4 py-4 text-slate-400">{u.created_at?.slice(0, 10)}</td>
                        <td className="px-4 py-4 text-center">
                          <div className="flex items-center justify-center gap-2">
                            <button
                              onClick={() => { setPkgModal({ userId: u.id, phone: u.phone || u.phone_number || '' }); setPkgSelected(''); setPkgReason('') }}
                              className="text-sm font-semibold text-violet-600 bg-violet-50 hover:bg-violet-100 rounded-lg px-4 py-1.5 transition-colors"
                            >分配套餐</button>
                          <button
                            onClick={() => { setCreditModal({ userId: u.id, phone: u.phone || u.phone_number || '' }); setCreditAmount(10); setCreditReason('') }}
                            className="text-sm font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-lg px-4 py-1.5 transition-colors"
                          >调整点数</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              </div>
              <Paginator page={usersPage} total={usersTotal} onPage={changeUsersPage} />
              {users.length === 0 && (
                <div className="p-8 text-center text-sm text-slate-400">暂无用户数据</div>
              )}
            </div>

            {/* 调整点数弹窗 */}
            {creditModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setCreditModal(null)}>
                <div className="mx-4 w-full max-w-xs rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                  <h3 className="text-base font-bold text-slate-900">调整点数</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    用户 <span className="font-mono font-bold text-slate-700">#{creditModal.userId}</span>
                    {creditModal.phone ? <span className="ml-1 text-slate-400">({creditModal.phone})</span> : ''}
                  </p>

                  <div className="mt-4 space-y-3">
                    <div>
                      <label className="text-xs font-semibold text-slate-500">变动点数（正数增加，负数扣减）</label>
                      <div className="flex gap-2 mt-1">
                        {[-10, -5, 5, 10, 20, 50, 100].map(n => (
                          <button key={n}
                            onClick={() => setCreditAmount(n)}
                            className={`flex-1 rounded-lg border py-1.5 text-xs font-semibold transition-colors ${
                              creditAmount === n ? 'border-blue-400 bg-blue-50 text-blue-600' : 'border-slate-200 text-slate-500 hover:border-slate-300'
                            }`}>{n > 0 ? `+${n}` : n}</button>
                        ))}
                      </div>
                      <input type="number"
                        value={creditAmount}
                        onChange={e => setCreditAmount(parseInt(e.target.value) || 0)}
                        className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-center font-bold focus:outline-none focus:border-blue-400" />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-500">操作备注 <span className="text-red-400">*</span></label>
                      <input type="text" value={creditReason}
                        onChange={e => setCreditReason(e.target.value)}
                        placeholder="如：因某bug补偿 / 活动赠送"
                        className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                    </div>
                  </div>

                  <div className="mt-5 flex gap-3">
                    <button onClick={() => setCreditModal(null)} disabled={creditSaving}
                      className="flex-1 rounded-lg border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50">取消</button>
                    <button onClick={async () => {
                      if (!creditReason.trim()) { showToast('请填写操作备注'); return }
                      setCreditSaving(true)
                      const r = await adminFetch(`/users/${creditModal.userId}/points`, { method: 'POST', body: JSON.stringify({ points: creditAmount, reason: creditReason.trim() }) })
                      setCreditSaving(false)
                      if (r.ok) { showToast(`点数已调整 ${creditAmount > 0 ? '+' : ''}${creditAmount}`); setCreditModal(null); loadUsers() }
                      else { const d = await r.json().catch(() => ({})); showToast(d.detail || '操作失败') }
                    }} disabled={creditSaving}
                      className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
                      {creditSaving ? '处理中...' : `确认${creditAmount >= 0 ? '+' : ''}${creditAmount}`}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 分配套餐弹窗 */}
            {pkgModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setPkgModal(null)}>
                <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                  <h3 className="text-base font-bold text-slate-900">分配套餐</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    用户 <span className="font-mono font-bold text-slate-700">#{pkgModal.userId}</span>
                    {pkgModal.phone ? <span className="ml-1 text-slate-400">({pkgModal.phone})</span> : ''}
                  </p>
                  <div className="mt-4">
                    <label className="text-xs font-semibold text-slate-500">选择套餐</label>
                    <select value={pkgSelected} onChange={e => setPkgSelected(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:border-violet-400">
                      <option value="">-- 请选择 --</option>
                      {skus.filter(s => s.visible !== false).map(s => (
                        <option key={s.id} value={s.id}>
                          {s.label} — {s.type === 'membership' ? `${s.duration_days}天会员` : `${s.credits}点`} (¥{s.price})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="mt-3">
                    <label className="text-xs font-semibold text-slate-500">操作备注 <span className="text-red-400">*</span></label>
                    <input type="text" value={pkgReason}
                      onChange={e => setPkgReason(e.target.value)}
                      placeholder="如：客户要求升级 / 活动赠送"
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-violet-400" />
                  </div>
                  <div className="mt-5 flex gap-3">
                    <button onClick={() => setPkgModal(null)} disabled={pkgSaving}
                      className="flex-1 rounded-lg border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50">取消</button>
                    <button onClick={async () => {
                      if (!pkgSelected) { showToast('请选择套餐'); return }
                      if (!pkgReason.trim()) { showToast('请填写操作备注'); return }
                      setPkgSaving(true)
                      const r = await adminFetch(`/users/${pkgModal.userId}/package`, { method: 'POST', body: JSON.stringify({ packageId: Number(pkgSelected), reason: pkgReason.trim() }) })
                      setPkgSaving(false)
                      if (r.ok) { const d = await r.json(); showToast(d.message || '套餐已分配'); setPkgModal(null); loadUsers() }
                      else { const d = await r.json().catch(() => ({})); showToast(d.detail || '操作失败') }
                    }} disabled={pkgSaving || !pkgSelected}
                      className="flex-1 rounded-lg bg-violet-600 py-2.5 text-sm font-bold text-white hover:bg-violet-700 disabled:opacity-50 transition-colors">
                      {pkgSaving ? '处理中...' : '确认分配'}
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 用户专属套餐弹窗 */}
            {skuModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4" onClick={() => setSkuModal(null)}>
                <div className="w-full max-w-4xl max-h-[86vh] overflow-hidden rounded-xl bg-white shadow-2xl" onClick={e => e.stopPropagation()}>
                  <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
                    <div>
                      <h3 className="text-base font-bold text-slate-900">用户套餐配置与到账</h3>
                      <p className="mt-1 text-xs text-slate-500">
                        用户 <span className="font-mono font-bold text-slate-700">#{skuModal.userId}</span>
                        {skuModal.phone ? <span className="ml-1 text-slate-400">({skuModal.phone})</span> : ''}
                        <span className={`ml-2 rounded-full px-2 py-0.5 text-[10px] font-bold ${userSkuInherited ? 'bg-slate-100 text-slate-500' : 'bg-violet-50 text-violet-600'}`}>
                          {userSkuInherited ? '当前继承全局套餐' : '当前使用专属套餐'}
                        </span>
                      </p>
                      <p className="mt-1 text-[11px] text-amber-600">保存配置只影响客户可见套餐；点击“应用到账户”才会实际增加点数或开通会员。</p>
                    </div>
                    <button onClick={() => setSkuModal(null)} className="rounded-lg px-2 py-1 text-sm text-slate-400 hover:bg-slate-100">关闭</button>
                  </div>

                  <div className="max-h-[58vh] overflow-y-auto p-5">
                    {userSkuLoading ? (
                      <div className="py-10 text-center text-sm text-slate-400">正在加载套餐...</div>
                    ) : (
                      <div className="space-y-3">
                        {userSkuDraft.map((s, i) => (
                          <div key={s.id} className={`rounded-xl border p-3 ${s.visible === false ? 'border-slate-100 bg-slate-50 opacity-70' : 'border-slate-200 bg-white'}`}>
                            <div className="grid grid-cols-12 gap-2">
                              <select value={s.type || 'points'} onChange={e => updateUserSkuAt(i, {
                                type: e.target.value,
                                credits: e.target.value === 'points' ? (s.credits || 1) : 0,
                                duration_days: e.target.value === 'membership' ? (s.duration_days || 30) : 0,
                                tier: e.target.value === 'membership' ? (s.tier || 'monthly') : '',
                              })}
                                className="col-span-2 rounded border border-slate-200 px-2 py-1.5 text-xs">
                                <option value="points">点数包</option>
                                <option value="membership">会员</option>
                              </select>
                              <input value={s.label} onChange={e => updateUserSkuAt(i, { label: e.target.value })}
                                placeholder="套餐名" className="col-span-3 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                              <input value={s.price} onChange={e => updateUserSkuAt(i, { price: e.target.value })}
                                placeholder="价格" className="col-span-1 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                              <input value={s.type === 'membership' ? s.duration_days : s.credits} type="number"
                                onChange={e => updateUserSkuAt(i, s.type === 'membership'
                                  ? { duration_days: parseInt(e.target.value) || 0 }
                                  : { credits: parseInt(e.target.value) || 0 })}
                                placeholder={s.type === 'membership' ? '天数' : '次数'}
                                className="col-span-1 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                              <input value={s.badge || ''} onChange={e => updateUserSkuAt(i, { badge: e.target.value })}
                                placeholder="标签" className="col-span-1 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                              <input value={s.desc || ''} onChange={e => updateUserSkuAt(i, { desc: e.target.value })}
                                placeholder="客户可见说明" className="col-span-3 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                              <button onClick={() => updateUserSkuAt(i, { visible: s.visible === false })}
                                className={`col-span-1 rounded px-2 py-1.5 text-[10px] font-bold ${s.visible === false ? 'bg-slate-200 text-slate-500' : 'bg-emerald-50 text-emerald-600'}`}>
                                {s.visible === false ? '隐藏' : '显示'}
                              </button>
                            </div>
                            <div className="mt-2 flex items-center justify-between gap-3">
                              <div className="text-[11px] text-slate-400">
                                {s.type === 'membership'
                                  ? `应用后：为用户开通/延长 ${s.duration_days || 30} 天会员，到期日会显示在用户列表`
                                  : `应用后：为用户增加 ${s.credits || 0} 点`}
                              </div>
                              <button
                                type="button"
                                onClick={() => applyUserSku(s)}
                                disabled={userSkuApplyingId === s.id || userSkuSaving || userSkuLoading}
                                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-[11px] font-bold text-white hover:bg-emerald-700 disabled:opacity-50">
                                {userSkuApplyingId === s.id ? '应用中...' : '应用到账户'}
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-5 py-4">
                    <div className="flex gap-2">
                      <button onClick={() => setUserSkuDraft(list => [...list, makeNewSku('points')])}
                        className="rounded-lg bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-600">+ 点数包</button>
                      <button onClick={() => setUserSkuDraft(list => [...list, makeNewSku('membership')])}
                        className="rounded-lg bg-violet-50 px-3 py-1.5 text-xs font-semibold text-violet-600">+ 会员套餐</button>
                      <button onClick={resetUserSkus} disabled={userSkuSaving}
                        className="rounded-lg bg-slate-100 px-3 py-1.5 text-xs font-semibold text-slate-600 disabled:opacity-50">恢复全局套餐</button>
                    </div>
                    <button onClick={saveUserSkus} disabled={userSkuSaving || userSkuLoading}
                      className="rounded-lg bg-violet-600 px-4 py-2 text-xs font-bold text-white hover:bg-violet-700 disabled:opacity-50">
                      {userSkuSaving ? '保存中...' : '保存该用户专属套餐'}
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {tab === 'settings' && (
          <div className="space-y-4">
            {/* 地图服务配置 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">地图服务配置</div>
              <div className="text-[11px] text-slate-400 mb-4">高德地图 Web API 密钥</div>
              <div className="flex gap-2">
                <input type="password" value={settings.amap_key}
                  onChange={e => updateSettings({ amap_key: e.target.value })}
                  className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                <button onClick={() => showToast('连通性测试通过')}
                  className="rounded-lg bg-emerald-600 text-white text-xs font-semibold px-4 py-2 hover:bg-emerald-700">连通性测试</button>
              </div>
            </div>

            {/* AI 模型配置 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">AI 模型配置</div>
              <div className="text-[11px] text-slate-400 mb-4">选择当前激活的大模型供应商及对应密钥</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">AI 供应商</label>
                  <select value={settings.ai_provider}
                    onChange={e => updateSettings({ ai_provider: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400 bg-white">
                    <option value="deepseek">DeepSeek</option>
                    <option value="openai">OpenAI (GPT-4o)</option>
                    <option value="gemini">Google Gemini</option>
                    <option value="kimi">Kimi (Moonshot)</option>
                    <option value="zhipu">智谱 GLM</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">AI API Key</label>
                  <div className="relative mt-1">
                    <input type={showAiKey ? 'text' : 'password'} value={settings.ai_key}
                      onChange={e => updateSettings({ ai_key: e.target.value })}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 pr-10 text-sm focus:outline-none focus:border-blue-400" />
                    <button type="button" onClick={() => setShowAiKey(!showAiKey)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-sm">
                      {showAiKey ? '🙈' : '👁'}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* 核心 Prompt — 独立组件，隔离状态防全局重渲染 */}
            <CorePromptEditor
              systemPrompt={settings.system_prompt || ''}
              settingsLoaded={settingsLoaded}
              adminFetch={adminFetch}
              showToast={showToast}
              onSaved={() => setSettingsDirty(false)}
            />

            {/* 微信支付配置 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">微信支付配置</div>
              <div className="text-[11px] text-slate-400 mb-4">微信商户号、API 密钥及回调地址</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">商户号 (MCH ID)</label>
                  <input value={settings.wx_mch_id} onChange={e => updateSettings({ wx_mch_id: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppID (小程序/公众号)</label>
                  <input value={settings.wx_app_id} onChange={e => updateSettings({ wx_app_id: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">APIv3 密钥</label>
                  <input type="password" value={settings.wx_api_key} onChange={e => updateSettings({ wx_api_key: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">商户证书序列号</label>
                  <input value={settings.wx_cert_sn} onChange={e => updateSettings({ wx_cert_sn: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div className="sm:col-span-2">
                  <label className="text-xs font-semibold text-slate-500">支付回调地址 (Notify URL)</label>
                  <input value={settings.wx_notify_url} onChange={e => updateSettings({ wx_notify_url: e.target.value })}
                    placeholder={`${window.location.origin}/api/payment/notify`}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
              </div>
            </div>

            {/* 套餐与定价管理 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-sm font-bold text-slate-800">套餐与定价管理</div>
                  <div className="text-[11px] text-slate-400">前端充值弹窗将动态拉取此列表</div>
                </div>
                <button onClick={() => { setSkus([...skus, makeNewSku('points')]); setSkusDirty(true) }}
                  className="rounded-lg bg-blue-600 text-white text-xs font-semibold px-3 py-1.5">+ 添加套餐</button>
              </div>
              <div className="space-y-2">
                {skus.map((s, i) => (
                  <div key={s.id} className="grid grid-cols-12 gap-2">
                    <select value={s.type || 'points'} onChange={e => updateSkuAt(i, {
                      type: e.target.value,
                      credits: e.target.value === 'points' ? (s.credits || 1) : 0,
                      duration_days: e.target.value === 'membership' ? (s.duration_days || 30) : 0,
                      tier: e.target.value === 'membership' ? (s.tier || 'monthly') : '',
                    })}
                      className="col-span-2 rounded border border-slate-200 px-2 py-1.5 text-xs">
                      <option value="points">点数包</option>
                      <option value="membership">会员</option>
                    </select>
                    <input value={s.label} onChange={e => updateSkuAt(i, { label: e.target.value })}
                      placeholder="套餐名" className="col-span-2 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <input value={s.price} onChange={e => updateSkuAt(i, { price: e.target.value })}
                      placeholder="价格" className="col-span-1 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <input value={s.type === 'membership' ? s.duration_days : s.credits} type="number"
                      onChange={e => updateSkuAt(i, s.type === 'membership'
                        ? { duration_days: parseInt(e.target.value) || 0 }
                        : { credits: parseInt(e.target.value) || 0 })}
                      placeholder={s.type === 'membership' ? '天数' : '次数'}
                      className="col-span-1 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <input value={s.badge} onChange={e => updateSkuAt(i, { badge: e.target.value })}
                      placeholder="标签" className="col-span-1 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <input value={s.desc || ''} onChange={e => updateSkuAt(i, { desc: e.target.value })}
                      placeholder="客户可见说明" className="col-span-3 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <button onClick={() => updateSkuAt(i, { visible: s.visible === false })}
                      className={`rounded px-2 py-1.5 text-[10px] font-bold ${s.visible === false ? 'bg-slate-200 text-slate-500' : 'bg-emerald-50 text-emerald-600'}`}>
                      {s.visible === false ? '隐藏' : '显示'}
                    </button>
                    <button onClick={() => { setSkus(skus.filter(x => x.id !== s.id)); setSkusDirty(true) }}
                      className="text-red-400 text-xs flex-shrink-0">删除</button>
                  </div>
                ))}
              </div>
              <button onClick={async () => {
                try { await adminFetch('/skus', { method: 'PUT', body: JSON.stringify({ items: skus }) }); setSkusDirty(false); showToast('套餐已保存') }
                catch { showToast('保存失败') }
              }} className="mt-3 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5">单独保存套餐</button>
              {skusDirty && <span className="ml-2 text-[10px] font-semibold text-amber-600">套餐有未保存更改</span>}
            </div>

            <UiCustomerConfigCard
              uiConfig={uiConfig}
              setUiConfig={setUiConfig}
              adminFetch={adminFetch}
              showToast={showToast}
            />

            <QrcodeSlotCard
              slot="cs"
              title="客服二维码"
              description="只用于前端充值/会员弹窗的专属客服入口"
              uploadPath="/upload-customer-service-qrcode"
              adminFetch={adminFetch}
              showToast={showToast}
            />

            {/* PDF 报告品牌定制 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">PDF 报告品牌定制</div>
              <div className="text-[11px] text-slate-400 mb-4">自定义导出 PDF 的页眉 Logo 和页脚版权文案</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">页眉 Logo URL</label>
                  <input value={pdfConfig.logo_url} onChange={e => updatePdfConfig({ logo_url: e.target.value })}
                    placeholder="https://your-cdn.com/logo.png（留空使用默认）" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">页脚版权文案</label>
                  <input value={pdfConfig.footer_text} onChange={e => updatePdfConfig({ footer_text: e.target.value })}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
                </div>
              </div>
              <button onClick={async () => {
                try { await adminFetch('/pdf-config', { method: 'PUT', body: JSON.stringify(pdfConfig) }); setPdfDirty(false); showToast('PDF配置已保存') }
                catch { showToast('保存失败') }
              }} className="mt-3 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5">单独保存 PDF 配置</button>
              {pdfDirty && <span className="ml-2 text-[10px] font-semibold text-amber-600">PDF 配置有未保存更改</span>}
            </div>

            <QrcodeSlotCard
              slot="brand"
              title="品牌二维码"
              description="只用于导出 PDF 报告底部的品牌引流区块"
              uploadPath="/upload-brand-qrcode"
              adminFetch={adminFetch}
              showToast={showToast}
            />

            {/* 对象存储配置 (OSS/S3) */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">对象存储配置 (OSS/S3)</div>
              <div className="text-[11px] text-slate-400 mb-4">报告文件存储方案：本地存储 / 云端对象存储</div>

              {/* 存储模式切换 */}
              <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-slate-50">
                <span className="text-xs font-semibold text-slate-600">存储模式</span>
                <div className="flex rounded-lg border border-slate-200 bg-white overflow-hidden">
                  <button
                    onClick={() => updateStorageConfig({ storage_mode: 'local' })}
                    className={`px-4 py-1.5 text-xs font-semibold transition-colors ${storageConfig.storage_mode === 'local' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-700'}`}>
                    本地存储
                  </button>
                  <button
                    onClick={() => updateStorageConfig({ storage_mode: 'cloud' })}
                    className={`px-4 py-1.5 text-xs font-semibold transition-colors ${storageConfig.storage_mode === 'cloud' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-700'}`}>
                    云端存储
                  </button>
                </div>
              </div>

              {/* 云端配置字段 — 仅在 cloud 模式下显示 */}
              {storageConfig.storage_mode === 'cloud' && (
                <div className="space-y-3 pt-2 border-t border-slate-100">
                  <div>
                    <label className="text-xs font-semibold text-slate-500">Endpoint (节点地址)</label>
                    <input value={storageConfig.oss_endpoint}
                      onChange={e => updateStorageConfig({ oss_endpoint: e.target.value })}
                      placeholder="https://oss-cn-hangzhou.aliyuncs.com"
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-500">Bucket Name (存储桶名称)</label>
                    <input value={storageConfig.oss_bucket}
                      onChange={e => updateStorageConfig({ oss_bucket: e.target.value })}
                      placeholder="location-reports"
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-semibold text-slate-500">AccessKey ID</label>
                      <input value={storageConfig.oss_access_key_id}
                        onChange={e => updateStorageConfig({ oss_access_key_id: e.target.value })}
                        className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-500">AccessKey Secret</label>
                      <input type="password" value={storageConfig.oss_access_key_secret}
                        onChange={e => updateStorageConfig({ oss_access_key_secret: e.target.value })}
                        className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                    </div>
                  </div>
                  <div className="text-[10px] text-slate-400 bg-amber-50 border border-amber-100 rounded-lg p-2">
                    提示：支持所有兼容 S3 协议的对象存储（阿里云 OSS、腾讯云 COS、AWS S3、MinIO 等）
                  </div>
                </div>
              )}

              {/* 本地模式说明 */}
              {storageConfig.storage_mode === 'local' && (
                <div className="pt-2 border-t border-slate-100">
                  <div className="text-xs text-slate-500 leading-5">
                    报告文件将保存在服务器 <code className="bg-slate-100 text-slate-700 px-1.5 py-0.5 rounded text-[11px]">backend/storage/reports/</code> 目录下，
                    通过数据库记录的文件名动态读取。
                  </div>
                </div>
              )}
              <button onClick={async () => {
                try {
                  await adminFetch('/storage-config', {
                    method: 'PUT',
                    body: JSON.stringify(storageConfig),
                  })
                  setStorageDirty(false)
                  showToast('存储配置已保存')
                } catch { showToast('保存失败') }
              }} className="mt-3 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5">单独保存存储配置</button>
              {storageDirty && <span className="ml-2 text-[10px] font-semibold text-amber-600">存储配置有未保存更改</span>}
            </div>

            {/* 保存按钮 → 二次确认 */}
            <button onClick={() => setConfirmSave(true)}
              disabled={!settingsDirty || settingsSaving || !settingsLoaded}
              className="w-full rounded-xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed">
              {!settingsLoaded ? '配置加载中...' : settingsDirty ? '保存核心系统配置' : '核心系统配置已保存'}
            </button>
            {settingsDirty && <p className="-mt-2 text-center text-[10px] font-semibold text-amber-600">核心系统配置有未保存更改</p>}

            {/* 二次确认弹窗 */}
            {confirmSave && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setConfirmSave(false)}>
                <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                  <div className="text-center text-2xl mb-2">⚠️</div>
                  <h3 className="text-base font-bold text-slate-900 text-center">确认保存配置</h3>
                  <p className="mt-2 text-sm leading-5 text-slate-500 text-center">修改核心配置将影响系统运行，确定保存吗？</p>
                  <div className="mt-5 flex gap-3">
                    <button onClick={() => setConfirmSave(false)}
                      className="flex-1 rounded-lg border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">取消</button>
                    <button onClick={async () => {
                      setConfirmSave(false)
                      setSettingsSaving(true)
                      try {
                        await adminFetch('/config', {
                          method: 'PUT',
                          body: JSON.stringify(settings),
                        })
                        setSettingsDirty(false)
                        showToast('配置已保存，运行时立即读取新值')
                      } catch { showToast('保存失败') }
                      finally { setSettingsSaving(false) }
                    }}
                      className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700">确定保存</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
        {tab === 'logs' && (
          <div className="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden">
            <div className="max-h-[70vh] overflow-y-auto overscroll-contain">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-slate-50">
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">时间</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">类型</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">用户ID</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">错误信息</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {logs.slice((logsPage - 1) * PAGE_SIZE, logsPage * PAGE_SIZE).map((l, i) => (
                    <tr key={i} className="hover:bg-slate-50">
                      <td className="px-4 py-4 text-slate-500 font-mono text-sm">{l.time}</td>
                      <td className="px-4 py-4"><span className={`text-xs font-bold px-2.5 py-1 rounded-full ${l.type === 'API' ? 'bg-orange-50 text-orange-600' : l.type === 'PAYMENT' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>{l.type}</span></td>
                      <td className="px-4 py-4 text-slate-500">{l.user_id || '—'}</td>
                      <td className="px-4 py-4 text-slate-600 leading-5">{l.msg}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </div>
            <Paginator page={logsPage} total={logs.length} onPage={setLogsPage} />
            {logs.length === 0 && <div className="p-8 text-center text-sm text-slate-400">暂无错误日志</div>}
          </div>
        )}

        {tab === 'cdk' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-4">批量生成兑换码</div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <div><label className="text-[11px] text-slate-400">前缀</label>
                  <input value={cdkGen.prefix} onChange={e => setCdkGen(g => ({ ...g, prefix: e.target.value }))} className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm" /></div>
                <div><label className="text-[11px] text-slate-400">生成数量</label>
                  <input type="number" value={cdkGen.count} onChange={e => setCdkGen(g => ({ ...g, count: parseInt(e.target.value) || 1 }))} className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm" /></div>
                <div><label className="text-[11px] text-slate-400">包含点数</label>
                  <input type="number" value={cdkGen.credits} onChange={e => setCdkGen(g => ({ ...g, credits: parseInt(e.target.value) || 1 }))} className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm" /></div>
                <div><label className="text-[11px] text-slate-400">有效期(天)</label>
                  <input type="number" value={cdkGen.days_valid} onChange={e => setCdkGen(g => ({ ...g, days_valid: parseInt(e.target.value) || 90 }))} className="mt-1 w-full rounded border border-slate-200 px-3 py-2 text-sm" /></div>
              </div>
              <button onClick={async () => {
                const r = await adminFetch('/cdk/generate', { method: 'POST', body: JSON.stringify(cdkGen) })
                const d = await r.json()
                if (d.ok) { loadCdk(); showToast(`已生成 ${d.count} 个兑换码`) }
              }} className="rounded-lg bg-blue-600 text-white text-sm font-semibold px-5 py-2.5 hover:bg-blue-700">生成兑换码</button>
            </div>
            <div className="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden">
              <div className="max-h-[70vh] overflow-y-auto overscroll-contain">
              <div className="overflow-x-auto"><table className="w-full text-sm">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-slate-50">
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">兑换码</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">点数</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">状态</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">使用者</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">过期时间</th>
                    <th className="text-center px-4 py-4 text-[15px] font-semibold text-slate-600">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {cdkList.slice((cdkPage - 1) * PAGE_SIZE, cdkPage * PAGE_SIZE).map(c => (
                    <tr key={c.id} className="hover:bg-slate-50">
                      <td className="px-4 py-4 font-mono text-slate-600 text-sm">{c.code}</td>
                      <td className="px-4 py-4 font-bold text-blue-600">{c.credits}</td>
                      <td className="px-4 py-4">{c.is_used ? <span className="text-xs text-slate-400 bg-slate-100 rounded-full px-2.5 py-1">已使用</span> : <span className="text-xs text-emerald-600 bg-emerald-50 rounded-full px-2.5 py-1">可用</span>}</td>
                      <td className="px-4 py-4 text-slate-500">{c.used_by || '—'}</td>
                      <td className="px-4 py-4 text-slate-400">{c.expires_at?.slice(0, 10)}</td>
                      <td className="px-4 py-4 text-center"><button onClick={() => { navigator.clipboard.writeText(c.code); showToast('已复制') }} className="text-sm text-blue-600 bg-blue-50 rounded-lg px-3 py-1 hover:bg-blue-100">复制</button></td>
                    </tr>
                  ))}
                </tbody>
              </table></div>
              </div>
              <Paginator page={cdkPage} total={cdkList.length} onPage={setCdkPage} />
            </div>
          </div>
        )}

        {tab === 'oplogs' && (
          <div className="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden">
            <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
              <div className="text-sm text-slate-500">共 {opLogs.length} 条操作记录</div>
              <button onClick={loadOpLogs} className="text-sm text-blue-600 font-semibold hover:text-blue-700">刷新列表</button>
            </div>
            <div className="max-h-[70vh] overflow-y-auto overscroll-contain">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 z-10">
                  <tr className="bg-slate-50">
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">时间</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">操作人</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">目标用户</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">类型</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">变更量</th>
                    <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">备注</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {opLogs.slice((opLogsPage - 1) * PAGE_SIZE, opLogsPage * PAGE_SIZE).map(log => (
                    <tr key={log.id} className="hover:bg-slate-50">
                      <td className="px-4 py-4 text-slate-500">{log.created_at?.slice(0, 16)?.replace('T', ' ')}</td>
                      <td className="px-4 py-4 text-slate-600 font-medium">#{log.admin_id}</td>
                      <td className="px-4 py-4 text-slate-600 font-medium">#{log.user_id}</td>
                      <td className="px-4 py-4">
                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${log.type === 'ADJUST_POINTS' ? 'bg-blue-50 text-blue-600' : log.type === 'ASSIGN_PACKAGE' ? 'bg-violet-50 text-violet-600' : log.type === 'PROMPT_UPDATE' ? 'bg-amber-50 text-amber-600' : 'bg-slate-100 text-slate-600'}`}>
                          {log.type === 'ADJUST_POINTS' ? '调整点数' : log.type === 'ASSIGN_PACKAGE' ? '分配套餐' : log.type === 'PROMPT_UPDATE' ? 'Prompt热更新' : log.type === 'SYSTEM_CONFIG' ? '系统配置' : log.type}
                        </span>
                      </td>
                      <td className="px-4 py-4 text-slate-700 font-medium">{log.change_amount}</td>
                      <td className="px-4 py-4 text-slate-500">{log.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            </div>
            <Paginator page={opLogsPage} total={opLogs.length} onPage={setOpLogsPage} />
            {opLogs.length === 0 && <div className="p-8 text-center text-sm text-slate-400">暂无操作记录</div>}
          </div>
        )}

        {tab === 'sysparams' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">新用户注册奖励</div>
              <div className="text-[11px] text-slate-400 mb-4">运营人员可在此动态调整新用户注册时赠送的点数，无需修改代码或重启服务</div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">赠送永久点数</label>
                  <input type="number" min="0" max="100"
                    value={systemParams?.register_bonus?.value ?? 3}
                    onChange={e => updateParam('register_bonus', e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                  <p className="text-[10px] text-slate-400 mt-1">{systemParams?.register_bonus?.description || ''}</p>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">赠送体验点数（24h过期）</label>
                  <input type="number" min="0" max="100"
                    value={systemParams?.register_free?.value ?? 1}
                    onChange={e => updateParam('register_free', e.target.value)}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                  <p className="text-[10px] text-slate-400 mt-1">{systemParams?.register_free?.description || ''}</p>
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">微信公众号配置</div>
              <div className="text-[11px] text-slate-400 mb-4">用于公众号网页授权登录，填入真实值后生效</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppID</label>
                  <input value={systemParams?.wx_mp_appid?.value ?? ''}
                    onChange={e => updateParam('wx_mp_appid', e.target.value)}
                    placeholder="wx_xxxxxxxxxxxxxx"
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppSecret</label>
                  <input type="password"
                    value={systemParams?.wx_mp_secret?.value ?? ''}
                    onChange={e => updateParam('wx_mp_secret', e.target.value)}
                    placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-400" />
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">微信小程序配置</div>
              <div className="text-[11px] text-slate-400 mb-4">用于小程序内嵌授权登录</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppID</label>
                  <input value={systemParams?.wx_mini_appid?.value ?? ''}
                    onChange={e => updateParam('wx_mini_appid', e.target.value)}
                    placeholder="wx_xxxxxxxxxxxxxx"
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppSecret</label>
                  <input type="password"
                    value={systemParams?.wx_mini_secret?.value ?? ''}
                    onChange={e => updateParam('wx_mini_secret', e.target.value)}
                    placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-400" />
                </div>
              </div>
            </div>

            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100 contain-paint">
              <div className="text-sm font-bold text-slate-800 mb-1">微信服务号配置</div>
              <div className="text-[11px] text-slate-400 mb-4">用于服务号模板消息等高级能力（预留）</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppID</label>
                  <input value={systemParams?.wx_service_appid?.value ?? ''}
                    onChange={e => updateParam('wx_service_appid', e.target.value)}
                    placeholder="wx_xxxxxxxxxxxxxx"
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppSecret</label>
                  <input type="password"
                    value={systemParams?.wx_service_secret?.value ?? ''}
                    onChange={e => setSystemParams(p => ({ ...p, wx_service_secret: { ...(p?.wx_service_secret || {}), value: e.target.value } }))}
                    placeholder="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono focus:outline-none focus:border-blue-400" />
                </div>
              </div>
            </div>

            <button
              onClick={async () => {
                setSystemParamsSaving(true)
                try {
                  const items = {}
                  Object.entries(systemParams).forEach(([k, v]) => { items[k] = v?.value ?? '' })
                  await saveSystemSettings(items)
                  showToast('全局参数已保存，立即生效')
                } catch (err) { showToast(err?.message || '保存失败，请重试') }
                finally { setSystemParamsSaving(false) }
              }}
              disabled={systemParamsSaving}
              className="w-full rounded-xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
              {systemParamsSaving ? '保存中...' : '保存全局参数'}
            </button>
            <p className="text-[10px] text-slate-400 text-center -mt-2">修改立即生效，无需重启服务。新用户注册时将使用最新配置。</p>
          </div>
        )}
        {/* ═══════════ 业态规则管理 ═══════════ */}
        {tab === 'industries' && (
          <div>
            <div className="flex items-center justify-between mb-5">
              <div>
                <h2 className="text-lg font-bold text-slate-800">业态规则管理</h2>
                <p className="text-xs text-slate-400 mt-1">为不同业态配置专属 AI 提示词与测算规则，拼接至分析请求</p>
              </div>
              <button onClick={() => setIndustryModal({ name: '', sort_order: 0, is_active: 1 })}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 transition-colors">
                ＋ 新增业态
              </button>
            </div>

            {industries.length === 0 ? (
              <div className="rounded-xl bg-white p-12 text-center text-sm text-slate-400 shadow-sm border border-slate-100">
                暂无业态规则，点击"新增业态"创建第一条。
              </div>
            ) : (
              <div className="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden">
                <div className="max-h-[70vh] overflow-y-auto overscroll-contain">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 z-10">
                      <tr className="bg-slate-50">
                        <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600 w-16">排序</th>
                        <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">业态名称</th>
                        <th className="text-left px-4 py-4 text-[15px] font-semibold text-slate-600">专属规则</th>
                        <th className="text-center px-4 py-4 text-[15px] font-semibold text-slate-600 w-20">状态</th>
                        <th className="text-right px-4 py-4 text-[15px] font-semibold text-slate-600 w-56">操作</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {industries.slice((industriesPage - 1) * PAGE_SIZE, industriesPage * PAGE_SIZE).map(item => (
                        <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-4 py-4 text-slate-500 font-mono">{item.sort_order}</td>
                          <td className="px-4 py-4 font-medium text-slate-800">{item.name}</td>
                          <td className="px-4 py-4 text-slate-500 max-w-xs truncate" title={item.exclusive_prompt}>
                            {item.exclusive_prompt ? `${item.exclusive_prompt.slice(0, 40)}${item.exclusive_prompt.length > 40 ? '…' : ''}` : <span className="text-slate-300">未配置</span>}
                          </td>
                          <td className="px-4 py-4 text-center">
                            <button onClick={async () => {
                              const r = await adminFetch(`/industries/${item.id}`, {
                                method: 'PUT', body: JSON.stringify({ is_active: item.is_active ? 0 : 1 })
                              })
                              if (r.ok) { loadIndustries(); showToast(item.is_active ? '已停用' : '已启用') }
                              else { const d = await r.json().catch(() => ({})); showToast(d.detail || '操作失败') }
                            }}
                              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold transition-colors ${item.is_active ? 'bg-green-50 text-green-700 hover:bg-green-100' : 'bg-slate-100 text-slate-400 hover:bg-slate-200'}`}>
                              {item.is_active ? '启用' : '停用'}
                            </button>
                          </td>
                          <td className="px-4 py-4 text-right">
                            <div className="flex items-center justify-end gap-2">
                              <button onClick={() => setIndustryModal({ id: item.id, name: item.name, sort_order: item.sort_order, is_active: item.is_active })}
                                className="rounded-lg border border-slate-200 px-2.5 py-1 text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors">
                                编辑
                              </button>
                              <button onClick={() => { setPromptEditor(item) }}
                                className="rounded-lg border border-blue-200 px-2.5 py-1 text-xs font-medium text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors">
                                配置规则
                              </button>
                              <button onClick={() => setIndustryDeleteConfirm(item)}
                                className="rounded-lg border border-red-100 px-2.5 py-1 text-xs font-medium text-red-500 hover:bg-red-50 transition-colors">
                                删除
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                </div>
                <Paginator page={industriesPage} total={industries.length} onPage={setIndustriesPage} />
              </div>
            )}
          </div>
        )}

        {/* ═══════════ 业态新增/编辑模态框 ═══════════ */}
        {industryModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setIndustryModal(null)}>
            <div className="bg-white rounded-xl p-6 shadow-2xl w-full max-w-md" onClick={e => e.stopPropagation()}>
              <h3 className="text-sm font-bold text-slate-800 mb-4">{industryModal.id ? '编辑业态' : '新增业态'}</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-xs font-medium text-slate-500 mb-1">业态名称</label>
                  <input value={industryModal.name} onChange={e => setIndustryModal({ ...industryModal, name: e.target.value })}
                    placeholder="如：新茶饮、小吃快餐" className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div className="flex gap-3">
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-slate-500 mb-1">排序权重</label>
                    <input type="number" value={industryModal.sort_order} onChange={e => setIndustryModal({ ...industryModal, sort_order: parseInt(e.target.value) || 0 })}
                      className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                  </div>
                  <div className="flex-1">
                    <label className="block text-xs font-medium text-slate-500 mb-1">启用状态</label>
                    <button onClick={() => setIndustryModal({ ...industryModal, is_active: industryModal.is_active ? 0 : 1 })}
                      className={`w-full rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${industryModal.is_active ? 'border-green-200 bg-green-50 text-green-700' : 'border-slate-200 bg-slate-50 text-slate-400'}`}>
                      {industryModal.is_active ? '✓ 启用' : '— 停用'}
                    </button>
                  </div>
                </div>
              </div>
              <div className="flex gap-3 mt-5">
                <button onClick={() => setIndustryModal(null)}
                  className="flex-1 rounded-lg border border-slate-200 py-2 text-sm font-medium text-slate-500 hover:bg-slate-50 transition-colors">
                  取消
                </button>
                <button onClick={async () => {
                  if (!industryModal.name.trim()) { showToast('请输入业态名称'); return }
                  setIndustrySaving(true)
                  const url = industryModal.id ? `/industries/${industryModal.id}` : '/industries'
                  const method = industryModal.id ? 'PUT' : 'POST'
                  const body = { name: industryModal.name.trim(), sort_order: industryModal.sort_order, is_active: industryModal.is_active, reason: industryModal.id ? '编辑业态' : '新增业态' }
                  const r = await adminFetch(url, { method, body: JSON.stringify(body) })
                  setIndustrySaving(false)
                  if (r.ok) { setIndustryModal(null); loadIndustries(); showToast(industryModal.id ? '业态已更新' : '业态已创建') }
                  else { const d = await r.json().catch(() => ({})); showToast(d.detail || '保存失败') }
                }} disabled={industrySaving}
                  className="flex-1 rounded-lg bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
                  {industrySaving ? '保存中...' : '保存'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ═══════════ 业态专属规则编辑器（独立组件，隔离状态防全局重渲染） ═══════════ */}
        <IndustryRuleDrawer
          industry={promptEditor}
          adminFetch={adminFetch}
          showToast={showToast}
          onSaved={loadIndustries}
          onClose={() => setPromptEditor(null)}
        />

        {/* ═══════════ 删除确认弹窗 ═══════════ */}
        {industryDeleteConfirm && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setIndustryDeleteConfirm(null)}>
            <div className="bg-white rounded-xl p-6 shadow-2xl w-full max-w-sm" onClick={e => e.stopPropagation()}>
              <h3 className="text-sm font-bold text-slate-800 mb-2">确认删除</h3>
              <p className="text-sm text-slate-500 mb-5">确定要删除业态「{industryDeleteConfirm.name}」吗？此操作不可撤销。</p>
              <div className="flex gap-3">
                <button onClick={() => setIndustryDeleteConfirm(null)}
                  className="flex-1 rounded-lg border border-slate-200 py-2 text-sm font-medium text-slate-500 hover:bg-slate-50 transition-colors">取消</button>
                <button onClick={async () => {
                  const r = await adminFetch(`/industries/${industryDeleteConfirm.id}`, { method: 'DELETE' })
                  if (r.ok) { setIndustryDeleteConfirm(null); loadIndustries(); showToast(`已删除「${industryDeleteConfirm.name}」`) }
                  else { const d = await r.json().catch(() => ({})); showToast(d.detail || '删除失败') }
                }}
                  className="flex-1 rounded-lg bg-red-600 py-2 text-sm font-semibold text-white hover:bg-red-700 transition-colors">确认删除</button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
    </div>
  )
}
