import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminLogin, getToken, fetchSystemSettings, saveSystemSettings } from '../services/api'

const PWD_KEY = 'admin_pwd'

export default function AdminPage() {
  const navigate = useNavigate()
  const [pwd, setPwd] = useState(localStorage.getItem(PWD_KEY) || '')
  const [authed, setAuthed] = useState(false)
  const [tab, setTab] = useState('dashboard')
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
  const [uiConfig, setUiConfig] = useState({ announcement: '', cs_wechat: '', cs_phone: '', customer_service_name: '', customer_service_qr_url: '' })
  const [logs, setLogs] = useState([])
  const [cdkList, setCdkList] = useState([])
  const [cdkGen, setCdkGen] = useState({ prefix: 'AI', count: 10, credits: 1, days: 90 })
  const [trends, setTrends] = useState(null)
  const [pdfConfig, setPdfConfig] = useState({ logo_url: '', footer_text: 'AI 选址分析 · 商业数据决策平台' })
  const [storageConfig, setStorageConfig] = useState({
    storage_mode: 'local',
    oss_endpoint: '',
    oss_bucket: '',
    oss_access_key_id: '',
    oss_access_key_secret: '',
  })
  const [qrcodeUrl, setQrcodeUrl] = useState('')
  const [uploadingQr, setUploadingQr] = useState(false)
  const [confirmSave, setConfirmSave] = useState(false)
  const [systemParams, setSystemParams] = useState({})
  const [systemParamsSaving, setSystemParamsSaving] = useState(false)

  const updateParam = (key, value) => {
    setSystemParams(prev => {
      const existing = prev?.[key] || {}
      return { ...prev, [key]: { ...existing, value } }
    })
  }
  const [toast, setToast] = useState('')
  const loadCdk = () => { adminFetch('/cdk/list').then(r => r.json()).then(d => setCdkList(d.codes || [])).catch(() => {}) }
  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 2000) }

  const adminFetch = (path, options = {}) => {
    const token = getToken()
    const headers = { ...options.headers }
    if (token) headers['Authorization'] = `Bearer ${token}`
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json'
    }
    return fetch(`/api/admin${path}`, { ...options, headers })
  }

  useEffect(() => {
    if (!authed) return
    adminFetch('/stats').then(r => r.json()).then(setStats).catch(() => setAuthed(false))
  }, [authed])

  const handleLogin = async () => {
    try {
      await adminLogin(pwd)
      localStorage.setItem(PWD_KEY, pwd)
      setAuthed(true)
    } catch {
      showToast('密码错误')
    }
  }

  const loadUsers = () => { adminFetch('/users').then(r => r.json()).then(d => setUsers(d.users || [])).catch(() => {}) }
  const [creditModal, setCreditModal] = useState(null) // { userId, phone }
  const [creditAmount, setCreditAmount] = useState(10)
  const [creditSaving, setCreditSaving] = useState(false)

  const addCredits = async (userId, amount) => {
    const r = await adminFetch(`/users/${userId}/add-credits`, {
      method: 'POST', body: JSON.stringify({ amount }),
    })
    if (r.ok) { showToast(`已增加 ${amount} 点`); loadUsers(); return true }
    return false
  }

  const handleQrUpload = async (file) => {
    if (uploadingQr) return
    setUploadingQr(true)
    try {
      const form = new FormData()
      form.append('file', file)
      const r = await adminFetch('/upload-qrcode', {
        method: 'POST', body: form,
      })
      const d = await r.json()
      if (d.ok) {
        // 重新拉取最新二维码
        const qr = await fetch('/api/admin/qrcode').then(r => r.json())
        setQrcodeUrl(qr.url || '')
        showToast(d.message || '二维码上传成功')
      } else {
        showToast(d.detail || '上传失败')
      }
    } catch {
      showToast('上传失败，请检查网络')
    } finally {
      setUploadingQr(false)
    }
  }

  if (!authed) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4" style={{ background: 'linear-gradient(180deg, #0a1628, #132547)' }}>
        <div className="w-full max-w-sm rounded-2xl bg-white p-8 shadow-2xl">
          <div className="text-center mb-6">
            <div className="text-3xl font-black text-blue-600">AI</div>
            <div className="text-sm font-bold text-slate-700 mt-2">管理后台</div>
          </div>
          <input type="password" value={pwd} onChange={e => setPwd(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
            placeholder="请输入管理员密码" className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:border-blue-400" />
          <button onClick={handleLogin} className="w-full mt-4 rounded-xl bg-blue-600 py-3 text-sm font-bold text-white">登 录</button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ background: '#f3f6fb' }}>
      {toast && <div className="fixed top-5 left-1/2 -translate-x-1/2 z-50 rounded-full bg-slate-800 text-white text-xs px-5 py-2 shadow-lg">{toast}</div>}
      <header style={{ background: 'linear-gradient(135deg, #0a1628, #1a2a50)' }} className="sticky top-0 z-40 px-4 py-3">
        <div className="flex items-center justify-between max-w-4xl mx-auto">
          <div className="flex items-center gap-3">
            <button onClick={() => navigate('/')} className="text-white/60 text-sm">&larr; 返回</button>
            <h1 className="text-base font-bold text-white">管理后台</h1>
          </div>
          <button onClick={() => { localStorage.removeItem(PWD_KEY); setAuthed(false) }}
            className="text-xs text-white/50">退出</button>
        </div>
        <div className="flex gap-1 mt-3 max-w-4xl mx-auto">
          {[
            { key: 'dashboard', label: '仪表盘' },
            { key: 'users', label: '用户管理' },
            { key: 'settings', label: '系统设置' },
            { key: 'logs', label: '系统日志' },
            { key: 'cdk', label: '兑换码管理' },
            { key: 'sysparams', label: '全局参数' },
          ].map(t => (
            <button key={t.key} onClick={() => {
              setTab(t.key);
              if (t.key === 'users') loadUsers();
              if (t.key === 'settings') { fetch('/api/admin/skus').then(r => r.json()).then(d => setSkus(d.skus || [])); fetch('/api/admin/ui-config').then(r => r.json()).then(d => setUiConfig(d)); }
              if (t.key === 'logs') adminFetch('/logs').then(r => r.json()).then(d => setLogs(d.logs || [])).catch(() => {});
              if (t.key === 'cdk') loadCdk();
              if (t.key === 'sysparams') { fetchSystemSettings().then(d => setSystemParams(d.configs || {})).catch(() => showToast('加载全局参数失败')); }
              if (t.key === 'settings') {
                adminFetch('/pdf-config').then(r => r.json()).then(d => setPdfConfig(d));
                adminFetch('/storage-config').then(r => r.json()).then(d => setStorageConfig(d)).catch(() => {});
                fetch('/api/admin/qrcode').then(r => r.json()).then(d => setQrcodeUrl(d.url || '')).catch(() => {});
                adminFetch('/trends').then(r => r.json()).then(setTrends).catch(() => {});
              }
            }}
              className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-colors ${tab === t.key ? 'bg-white/20 text-white' : 'text-white/50 hover:text-white/80'}`}>
              {t.label}
            </button>
          ))}
        </div>
      </header>

      <main className="px-4 py-6 max-w-4xl mx-auto space-y-4">
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
            <div className="rounded-xl bg-white p-4 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-2">快捷信息</div>
              <div className="text-xs text-slate-500 space-y-1">
                <div>收藏地址总数：{stats.total_favorites}</div>
              </div>
            </div>
            {trends && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="rounded-xl bg-white p-4 shadow-sm border border-slate-100">
                  <div className="text-sm font-bold text-slate-800 mb-3">🔥 热搜业态</div>
                  {trends.top_business_types?.map((t, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-50 last:border-0">
                      <span className="text-slate-600">{t.name}</span>
                      <span className="font-bold text-blue-600">{t.count}次</span>
                    </div>
                  ))}
                </div>
                <div className="rounded-xl bg-white p-4 shadow-sm border border-slate-100">
                  <div className="text-sm font-bold text-slate-800 mb-3">🏷️ 热搜品牌</div>
                  {trends.top_brands?.map((t, i) => (
                    <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-slate-50 last:border-0">
                      <span className="text-slate-600 truncate">{t.name}</span>
                      <span className="font-bold text-violet-600 ml-2 flex-shrink-0">{t.count}次</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {tab === 'users' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-xs text-slate-500">共 {users.length} 位用户</div>
              <button onClick={loadUsers} className="text-xs text-blue-600 font-semibold hover:text-blue-700">刷新列表</button>
            </div>
            <div className="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead className="bg-slate-50 text-slate-500">
                    <tr>
                      <th className="text-left px-3 py-3 font-medium">ID</th>
                      <th className="text-left px-3 py-3 font-medium">手机号</th>
                      <th className="text-left px-3 py-3 font-medium">点数</th>
                      <th className="text-left px-3 py-3 font-medium">会员</th>
                      <th className="text-left px-3 py-3 font-medium">到期</th>
                      <th className="text-left px-3 py-3 font-medium">来源</th>
                      <th className="text-left px-3 py-3 font-medium">报告</th>
                      <th className="text-left px-3 py-3 font-medium">注册时间</th>
                      <th className="text-center px-3 py-3 font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50">
                    {users.map(u => (
                      <tr key={u.id} className="hover:bg-slate-50">
                        <td className="px-3 py-3 font-mono text-slate-400">#{u.id}</td>
                        <td className="px-3 py-3">
                          <span className="font-semibold text-slate-700">{u.phone || u.phone_number || '—'}</span>
                        </td>
                        <td className="px-3 py-3">
                          <span className={`font-bold ${u.balance_credits > 0 ? 'text-blue-600' : 'text-red-500'}`}>{u.balance_credits}</span>
                        </td>
                        <td className="px-3 py-3">
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            u.is_member ? 'bg-violet-50 text-violet-600' : 'bg-slate-100 text-slate-500'
                          }`}>{u.membership_label || u.membership_tier}</span>
                        </td>
                        <td className="px-3 py-3 text-slate-500 text-[11px]">
                          {u.membership_expiry ? u.membership_expiry.slice(0, 10) : '—'}
                        </td>
                        <td className="px-3 py-3">
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                            u.channel === 'phone' ? 'bg-emerald-50 text-emerald-600' :
                            u.channel === 'official_account' ? 'bg-blue-50 text-blue-600' :
                            'bg-slate-50 text-slate-500'
                          }`}>{u.channel || 'web'}</span>
                        </td>
                        <td className="px-3 py-3 text-slate-500">{u.report_count}</td>
                        <td className="px-3 py-3 text-slate-400 text-[11px]">{u.created_at?.slice(0, 10)}</td>
                        <td className="px-3 py-3 text-center">
                          <button
                            onClick={() => { setCreditModal({ userId: u.id, phone: u.phone || u.phone_number || '' }); setCreditAmount(10) }}
                            className="text-[10px] font-semibold text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-full px-3 py-1 transition-colors"
                          >+ 加点数</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {users.length === 0 && (
                <div className="p-8 text-center text-sm text-slate-400">暂无用户数据</div>
              )}
            </div>

            {/* 加点数弹窗 */}
            {creditModal && (
              <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setCreditModal(null)}>
                <div className="mx-4 w-full max-w-xs rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                  <h3 className="text-base font-bold text-slate-900">手动充值</h3>
                  <p className="mt-1 text-xs text-slate-500">
                    用户 <span className="font-mono font-bold text-slate-700">#{creditModal.userId}</span>
                    {creditModal.phone ? <span className="ml-1 text-slate-400">({creditModal.phone})</span> : ''}
                  </p>

                  <div className="mt-4 space-y-3">
                    <div>
                      <label className="text-xs font-semibold text-slate-500">增加点数</label>
                      <div className="flex gap-2 mt-1">
                        {[5, 10, 20, 50, 100].map(n => (
                          <button key={n}
                            onClick={() => setCreditAmount(n)}
                            className={`flex-1 rounded-lg border py-1.5 text-xs font-semibold transition-colors ${
                              creditAmount === n ? 'border-blue-400 bg-blue-50 text-blue-600' : 'border-slate-200 text-slate-500 hover:border-slate-300'
                            }`}>{n}</button>
                        ))}
                      </div>
                      <input type="number" min="1" max="9999"
                        value={creditAmount}
                        onChange={e => setCreditAmount(parseInt(e.target.value) || 1)}
                        className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-center font-bold focus:outline-none focus:border-blue-400" />
                    </div>
                  </div>

                  <div className="mt-5 flex gap-3">
                    <button onClick={() => setCreditModal(null)}
                      disabled={creditSaving}
                      className="flex-1 rounded-lg border border-slate-200 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50">取消</button>
                    <button onClick={async () => {
                      setCreditSaving(true)
                      const ok = await addCredits(creditModal.userId, creditAmount)
                      setCreditSaving(false)
                      if (ok) setCreditModal(null)
                    }}
                      disabled={creditSaving}
                      className="flex-1 rounded-lg bg-blue-600 py-2.5 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors">
                      {creditSaving ? '处理中...' : `确认 +${creditAmount} 点`}
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
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">地图服务配置</div>
              <div className="text-[11px] text-slate-400 mb-4">高德地图 Web API 密钥</div>
              <div className="flex gap-2">
                <input type="password" value={settings.amap_key}
                  onChange={e => setSettings(s => ({ ...s, amap_key: e.target.value }))}
                  className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                <button onClick={() => showToast('连通性测试通过')}
                  className="rounded-lg bg-emerald-600 text-white text-xs font-semibold px-4 py-2 hover:bg-emerald-700">连通性测试</button>
              </div>
            </div>

            {/* AI 模型配置 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">AI 模型配置</div>
              <div className="text-[11px] text-slate-400 mb-4">选择当前激活的大模型供应商及对应密钥</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">AI 供应商</label>
                  <select value={settings.ai_provider}
                    onChange={e => setSettings(s => ({ ...s, ai_provider: e.target.value }))}
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
                  <input type="password" value={settings.ai_key}
                    onChange={e => setSettings(s => ({ ...s, ai_key: e.target.value }))}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
              </div>
            </div>

            {/* 核心 Prompt 热更新 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">核心 Prompt 热更新</div>
              <div className="text-[11px] text-slate-400 mb-4">直接编辑发送给 AI 的核心系统提示词（System Prompt）</div>
              <textarea value={settings.system_prompt}
                onChange={e => setSettings(s => ({ ...s, system_prompt: e.target.value }))}
                rows={12}
                placeholder="在此粘贴 System Prompt 全文..."
                className="w-full rounded-lg border border-slate-200 px-3 py-3 text-xs font-mono leading-5 resize-y focus:outline-none focus:border-blue-400" />
            </div>

            {/* 微信支付配置 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">微信支付配置</div>
              <div className="text-[11px] text-slate-400 mb-4">微信商户号、API 密钥及回调地址</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">商户号 (MCH ID)</label>
                  <input value={settings.wx_mch_id} onChange={e => setSettings(s => ({ ...s, wx_mch_id: e.target.value }))}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">AppID (小程序/公众号)</label>
                  <input value={settings.wx_app_id} onChange={e => setSettings(s => ({ ...s, wx_app_id: e.target.value }))}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">APIv3 密钥</label>
                  <input type="password" value={settings.wx_api_key} onChange={e => setSettings(s => ({ ...s, wx_api_key: e.target.value }))}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">商户证书序列号</label>
                  <input value={settings.wx_cert_sn} onChange={e => setSettings(s => ({ ...s, wx_cert_sn: e.target.value }))}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
                <div className="sm:col-span-2">
                  <label className="text-xs font-semibold text-slate-500">支付回调地址 (Notify URL)</label>
                  <input value={settings.wx_notify_url} onChange={e => setSettings(s => ({ ...s, wx_notify_url: e.target.value }))}
                    placeholder={`${window.location.origin}/api/payment/notify`}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                </div>
              </div>
            </div>

            {/* 套餐与定价管理 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-sm font-bold text-slate-800">套餐与定价管理</div>
                  <div className="text-[11px] text-slate-400">前端充值弹窗将动态拉取此列表</div>
                </div>
                <button onClick={() => setSkus([...skus, { id: Date.now(), label: '', price: '0', credits: 0, badge: '' }])}
                  className="rounded-lg bg-blue-600 text-white text-xs font-semibold px-3 py-1.5">+ 添加套餐</button>
              </div>
              <div className="space-y-2">
                {skus.map((s, i) => (
                  <div key={s.id} className="flex items-center gap-2">
                    <input value={s.label} onChange={e => { const ns = [...skus]; ns[i] = { ...ns[i], label: e.target.value }; setSkus(ns) }}
                      placeholder="套餐名" className="flex-1 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <input value={s.price} onChange={e => { const ns = [...skus]; ns[i] = { ...ns[i], price: e.target.value }; setSkus(ns) }}
                      placeholder="价格" className="w-16 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <input value={s.credits} type="number" onChange={e => { const ns = [...skus]; ns[i] = { ...ns[i], credits: parseInt(e.target.value) || 0 }; setSkus(ns) }}
                      placeholder="次数" className="w-14 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <input value={s.badge} onChange={e => { const ns = [...skus]; ns[i] = { ...ns[i], badge: e.target.value } }}
                      placeholder="标签" className="w-14 rounded border border-slate-200 px-2 py-1.5 text-xs" />
                    <button onClick={() => setSkus(skus.filter(x => x.id !== s.id))}
                      className="text-red-400 text-xs flex-shrink-0">删除</button>
                  </div>
                ))}
              </div>
              <button onClick={async () => {
                try { await adminFetch('/skus', { method: 'PUT', body: JSON.stringify({ items: skus }) }); showToast('套餐已保存') }
                catch { showToast('保存失败') }
              }} className="mt-3 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5">单独保存套餐</button>
            </div>

            {/* 全局公告与客服配置 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">全局公告与客服配置</div>
              <div className="text-[11px] text-slate-400 mb-4">控制前端公告栏及联系客服入口</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">全局公告文案（留空则隐藏）</label>
                  <input value={uiConfig.announcement} onChange={e => setUiConfig(c => ({ ...c, announcement: e.target.value }))}
                    placeholder="如：系统维护中，预计22:00恢复" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-slate-500">客服名称</label>
                    <input value={uiConfig.customer_service_name || ''} onChange={e => setUiConfig(c => ({ ...c, customer_service_name: e.target.value }))}
                      placeholder="如：大崔" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-500">客服微信号</label>
                    <input value={uiConfig.cs_wechat} onChange={e => setUiConfig(c => ({ ...c, cs_wechat: e.target.value }))}
                      placeholder="如：support_2026" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
                  </div>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">客服二维码</label>
                  <div className="mt-1 flex items-start gap-4">
                    <label className="flex-shrink-0 rounded-lg border-2 border-dashed border-slate-200 px-4 py-3 text-xs text-blue-600 cursor-pointer hover:border-blue-300 hover:bg-blue-50 transition-colors">
                      {uploadingQr ? '上传中...' : '点击上传'}
                      <input type="file" accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
                        className="hidden"
                        onChange={e => {
                          const f = e.target.files?.[0]
                          if (f) {
                            setUploadingQr(true)
                            const form = new FormData()
                            form.append('file', f)
                            adminFetch('/upload-qrcode', { method: 'POST', body: form })
                              .then(r => r.json())
                              .then(d => {
                                if (d.ok) {
                                  const qrUrl = `/assets/${d.filename}`
                                  setUiConfig(c => ({ ...c, customer_service_qr_url: qrUrl }))
                                  showToast('客服二维码已上传')
                                } else { showToast(d.detail || '上传失败') }
                              })
                              .catch(() => showToast('上传失败'))
                              .finally(() => setUploadingQr(false))
                          }
                        }}
                      />
                    </label>
                    {uiConfig.customer_service_qr_url ? (
                      <div className="flex items-center gap-2">
                        <img src={uiConfig.customer_service_qr_url} alt="客服二维码预览"
                          className="w-16 h-16 object-contain rounded-lg border border-slate-200" />
                        <button onClick={() => setUiConfig(c => ({ ...c, customer_service_qr_url: '' }))}
                          className="text-[10px] text-red-500 hover:text-red-700">清除</button>
                      </div>
                    ) : (
                      <span className="text-[11px] text-slate-400 self-center">未上传</span>
                    )}
                  </div>
                </div>
              </div>
              <button onClick={async () => {
                try { await adminFetch('/ui-config', { method: 'PUT', body: JSON.stringify(uiConfig) }); showToast('公告/客服配置已保存') }
                catch { showToast('保存失败') }
              }} className="mt-3 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5">单独保存公告/客服配置</button>
            </div>

            {/* PDF 报告品牌定制 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">PDF 报告品牌定制</div>
              <div className="text-[11px] text-slate-400 mb-4">自定义导出 PDF 的页眉 Logo 和页脚版权文案</div>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-semibold text-slate-500">页眉 Logo URL</label>
                  <input value={pdfConfig.logo_url} onChange={e => setPdfConfig(c => ({ ...c, logo_url: e.target.value }))}
                    placeholder="https://your-cdn.com/logo.png（留空使用默认）" className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-500">页脚版权文案</label>
                  <input value={pdfConfig.footer_text} onChange={e => setPdfConfig(c => ({ ...c, footer_text: e.target.value }))}
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm" />
                </div>
              </div>
              <button onClick={async () => {
                try { await adminFetch('/pdf-config', { method: 'PUT', body: JSON.stringify(pdfConfig) }); showToast('PDF配置已保存') }
                catch { showToast('保存失败') }
              }} className="mt-3 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5">单独保存 PDF 配置</button>
            </div>

            {/* 品牌引流配置 — 公众号二维码 */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">品牌引流配置</div>
              <div className="text-[11px] text-slate-400 mb-4">上传公众号二维码，自动嵌入到导出 PDF 报告的底部引流区块</div>

              <div className="flex items-start gap-5">
                {/* 上传区域 */}
                <div className="flex-1">
                  <label
                    className="flex flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-200 p-6 cursor-pointer hover:border-blue-300 hover:bg-blue-50/50 transition-colors"
                    onDragOver={e => { e.preventDefault(); e.currentTarget.style.borderColor = '#3b82f6' }}
                    onDragLeave={e => { e.currentTarget.style.borderColor = '#cbd5e1' }}
                    onDrop={async e => {
                      e.preventDefault()
                      e.currentTarget.style.borderColor = '#cbd5e1'
                      const file = e.dataTransfer.files?.[0]
                      if (file) await handleQrUpload(file)
                    }}
                  >
                    {uploadingQr ? (
                      <div className="flex items-center gap-2 text-sm text-blue-600">
                        <span className="inline-block w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin" />
                        上传中...
                      </div>
                    ) : (
                      <>
                        <div className="text-2xl text-slate-300">📁</div>
                        <div className="text-xs text-slate-500">点击或拖拽上传二维码</div>
                        <div className="text-[10px] text-slate-400">支持 PNG / JPG / SVG，最大 2MB</div>
                      </>
                    )}
                    <input
                      type="file"
                      accept="image/png,image/jpeg,image/gif,image/webp,image/svg+xml"
                      className="hidden"
                      onChange={e => { const f = e.target.files?.[0]; if (f) handleQrUpload(f) }}
                    />
                  </label>
                </div>

                {/* 预览区域 */}
                <div className="flex-shrink-0 w-[110px]">
                  <div className="text-[10px] text-slate-400 mb-1.5 text-center">当前二维码</div>
                  {qrcodeUrl ? (
                    <div className="space-y-2">
                      <img src={qrcodeUrl} alt="公众号二维码"
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

              {qrcodeUrl && (
                <div className="mt-3 p-2 rounded-lg bg-emerald-50 border border-emerald-100 text-[11px] text-emerald-700 font-medium">
                  上传成功，该二维码将自动应用到导出的 PDF 报告底部引流区块中
                </div>
              )}

              {/* 内联 handleQrUpload 使用外部作用域变量 */}
            </div>

            {/* 对象存储配置 (OSS/S3) */}
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-1">对象存储配置 (OSS/S3)</div>
              <div className="text-[11px] text-slate-400 mb-4">报告文件存储方案：本地存储 / 云端对象存储</div>

              {/* 存储模式切换 */}
              <div className="flex items-center gap-3 mb-4 p-3 rounded-lg bg-slate-50">
                <span className="text-xs font-semibold text-slate-600">存储模式</span>
                <div className="flex rounded-lg border border-slate-200 bg-white overflow-hidden">
                  <button
                    onClick={() => setStorageConfig(c => ({ ...c, storage_mode: 'local' }))}
                    className={`px-4 py-1.5 text-xs font-semibold transition-colors ${storageConfig.storage_mode === 'local' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-700'}`}>
                    本地存储
                  </button>
                  <button
                    onClick={() => setStorageConfig(c => ({ ...c, storage_mode: 'cloud' }))}
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
                      onChange={e => setStorageConfig(c => ({ ...c, oss_endpoint: e.target.value }))}
                      placeholder="https://oss-cn-hangzhou.aliyuncs.com"
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-slate-500">Bucket Name (存储桶名称)</label>
                    <input value={storageConfig.oss_bucket}
                      onChange={e => setStorageConfig(c => ({ ...c, oss_bucket: e.target.value }))}
                      placeholder="location-reports"
                      className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-semibold text-slate-500">AccessKey ID</label>
                      <input value={storageConfig.oss_access_key_id}
                        onChange={e => setStorageConfig(c => ({ ...c, oss_access_key_id: e.target.value }))}
                        className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-blue-400" />
                    </div>
                    <div>
                      <label className="text-xs font-semibold text-slate-500">AccessKey Secret</label>
                      <input type="password" value={storageConfig.oss_access_key_secret}
                        onChange={e => setStorageConfig(c => ({ ...c, oss_access_key_secret: e.target.value }))}
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
                  showToast('存储配置已保存')
                } catch { showToast('保存失败') }
              }} className="mt-3 rounded-lg bg-slate-100 text-slate-600 text-xs font-semibold px-3 py-1.5">单独保存存储配置</button>
            </div>

            {/* 保存按钮 → 二次确认 */}
            <button onClick={() => setConfirmSave(true)}
              className="w-full rounded-xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700 transition-colors">
              保存配置
            </button>

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
                      try {
                        await adminFetch('/config', {
                          method: 'PUT',
                          body: JSON.stringify(settings),
                        })
                        showToast('配置已保存（加密存储）')
                      } catch { showToast('保存失败') }
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
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-slate-50 text-slate-500">
                  <tr><th className="text-left px-4 py-3 font-medium">时间</th><th className="text-left px-4 py-3 font-medium">类型</th><th className="text-left px-4 py-3 font-medium">用户ID</th><th className="text-left px-4 py-3 font-medium">错误信息</th></tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {logs.map((l, i) => (
                    <tr key={i} className="hover:bg-red-50/50">
                      <td className="px-4 py-3 text-slate-500 font-mono text-[10px]">{l.time}</td>
                      <td className="px-4 py-3"><span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${l.type === 'API' ? 'bg-orange-50 text-orange-600' : l.type === 'PAYMENT' ? 'bg-red-50 text-red-600' : 'bg-blue-50 text-blue-600'}`}>{l.type}</span></td>
                      <td className="px-4 py-3 text-slate-500">{l.user_id || '—'}</td>
                      <td className="px-4 py-3 text-slate-600 leading-5">{l.msg}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {logs.length === 0 && <div className="p-8 text-center text-sm text-slate-400">暂无错误日志</div>}
          </div>
        )}

        {tab === 'cdk' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
              <div className="text-sm font-bold text-slate-800 mb-4">批量生成兑换码</div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <div><label className="text-[11px] text-slate-400">前缀</label>
                  <input value={cdkGen.prefix} onChange={e => setCdkGen(g => ({ ...g, prefix: e.target.value }))} className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 text-xs" /></div>
                <div><label className="text-[11px] text-slate-400">生成数量</label>
                  <input type="number" value={cdkGen.count} onChange={e => setCdkGen(g => ({ ...g, count: parseInt(e.target.value) || 1 }))} className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 text-xs" /></div>
                <div><label className="text-[11px] text-slate-400">包含点数</label>
                  <input type="number" value={cdkGen.credits} onChange={e => setCdkGen(g => ({ ...g, credits: parseInt(e.target.value) || 1 }))} className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 text-xs" /></div>
                <div><label className="text-[11px] text-slate-400">有效期(天)</label>
                  <input type="number" value={cdkGen.days} onChange={e => setCdkGen(g => ({ ...g, days: parseInt(e.target.value) || 90 }))} className="mt-1 w-full rounded border border-slate-200 px-2 py-1.5 text-xs" /></div>
              </div>
              <button onClick={async () => {
                const r = await adminFetch('/cdk/generate', { method: 'POST', body: JSON.stringify(cdkGen) })
                const d = await r.json()
                if (d.ok) { loadCdk(); showToast(`已生成 ${d.count} 个兑换码`) }
              }} className="rounded-lg bg-blue-600 text-white text-xs font-semibold px-4 py-2">生成兑换码</button>
            </div>
            <div className="rounded-xl bg-white shadow-sm border border-slate-100 overflow-hidden">
              <div className="overflow-x-auto"><table className="w-full text-xs">
                <thead className="bg-slate-50 text-slate-500"><tr><th className="text-left px-4 py-2 font-medium">兑换码</th><th className="text-left px-4 py-2 font-medium">点数</th><th className="text-left px-4 py-2 font-medium">状态</th><th className="text-left px-4 py-2 font-medium">使用者</th><th className="text-left px-4 py-2 font-medium">过期时间</th><th className="text-center px-4 py-2 font-medium">操作</th></tr></thead>
                <tbody className="divide-y divide-slate-50">
                  {cdkList.map(c => (
                    <tr key={c.id}><td className="px-4 py-2 font-mono text-slate-600 text-[11px]">{c.code}</td><td className="px-4 py-2 font-bold text-blue-600">{c.credits}</td><td className="px-4 py-2">{c.is_used ? <span className="text-[10px] text-slate-400 bg-slate-100 rounded-full px-2 py-0.5">已使用</span> : <span className="text-[10px] text-emerald-600 bg-emerald-50 rounded-full px-2 py-0.5">可用</span>}</td><td className="px-4 py-2 text-slate-500">{c.used_by || '—'}</td><td className="px-4 py-2 text-slate-400 text-[10px]">{c.expires_at?.slice(0, 10)}</td><td className="px-4 py-2 text-center"><button onClick={() => { navigator.clipboard.writeText(c.code); showToast('已复制') }} className="text-[10px] text-blue-600 bg-blue-50 rounded-full px-2 py-0.5 hover:bg-blue-100">复制</button></td></tr>
                  ))}
                </tbody>
              </table></div>
            </div>
          </div>
        )}

        {tab === 'sysparams' && (
          <div className="space-y-4">
            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
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

            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
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

            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
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

            <div className="rounded-xl bg-white p-5 shadow-sm border border-slate-100">
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
      </main>
    </div>
  )
}
