import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import useFetch from '../hooks/useFetch'
import { clearToken, getToken, getAssetUrl } from '../services/api'

export default function ProfileView() {
  const navigate = useNavigate()
  const [toast, setToast] = useState('')
  const [rechargeOpen, setRechargeOpen] = useState(false)
  const [rechargeTab, setRechargeTab] = useState('points')
  const [cdkOpen, setCdkOpen] = useState(false)
  const [cdkInput, setCdkInput] = useState('')
  const [countdown, setCountdown] = useState('')
  const [csWechat, setCsWechat] = useState('')
  const [csPhone, setCsPhone] = useState('')
  const [csQrUrl, setCsQrUrl] = useState('')
  const countdownRef = useRef(null)

  const showToast = (msg, duration = 2000) => {
    setToast(msg)
    setTimeout(() => setToast(''), duration)
  }

  const retryProfile = () => {
    clearToken()
    refetch()
  }

  const { data: profileResp, loading, error: profileError, refetch } = useFetch('/api/user/profile')
  const { data: uiData } = useFetch('/api/admin/ui-config')
  const { data: csQrData } = useFetch('/api/admin/qrcode-slot/cs')
  const { data: skuData } = useFetch('/api/user/skus')

  const profile = profileResp || {}
  const membership = profileResp?.membership || {}
  const points = profileResp?.points ?? 0
  const skus = Array.isArray(skuData?.skus) ? skuData.skus : []
  const membershipSkus = skus.filter(s => s.type === 'membership').slice(0, 3)
  const pointSkus = skus.filter(s => s.type !== 'membership').slice(0, 4)

  useEffect(() => {
    try {
      const d = uiData || {}
      setCsWechat(d?.cs_wechat || '')
      setCsPhone(d?.cs_phone || '')
    } catch { /* silent */ }
  }, [uiData])

  useEffect(() => {
    setCsQrUrl(csQrData?.url || '')
  }, [csQrData])

  const freePointExpireAt = profileResp?.user?.free_point_expire_at
  const freePointActive = profileResp?.user?.free_point_active

  useEffect(() => {
    if (!freePointExpireAt || !freePointActive) return undefined
    const tick = () => {
      const diff = new Date(freePointExpireAt).getTime() - Date.now()
      if (diff <= 0) {
        setCountdown('已过期')
        return
      }
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      setCountdown(`${h}小时${m}分`)
    }
    tick()
    countdownRef.current = setInterval(tick, 30000)
    return () => {
      if (countdownRef.current) clearInterval(countdownRef.current)
    }
  }, [freePointExpireAt, freePointActive])

  if (loading) {
    return (
      <div className="profile-page-v2">
        <div className="profile-loading-card">
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

  if (profileError || !profile?.user) {
    return (
      <div className="profile-page-v2">
        <div className="profile-loading-card">
          <div className="text-sm text-red-500 mb-3">{profileError || '加载失败'}</div>
          <button onClick={retryProfile} className="profile-primary-mini">点击重试</button>
        </div>
      </div>
    )
  }

  const u = profile?.user || {}
  const tierLabel = membership?.tier_label || '非会员'
  const isMember = membership?.is_member || false
  const daysLeft = membership?.days_left || 0
  const favoriteCount = profile?.favorite_count ?? 0
  const username = u?.nickname || u?.name || `用户${u?.id || '—'}`
  const rawPhone = u?.phone || u?.phone_number || u?.mobile || ''
  const accountLine = rawPhone
    ? `手机号码：${String(rawPhone).replace(/^(\d{3})\d{4}(\d+)/, '$1****$2')}`
    : `用户编号：${u?.id || '—'}`

  const menuRows = [
    { icon: '◇', title: '会员权益', sub: '了解会员特权', onClick: () => setRechargeOpen(true) },
  ]

  return (
    <div className="profile-page-v2">
      {toast && <div className="profile-toast">{toast}</div>}

      <section className="profile-top-v2">
        <div className="profile-user-row">
          <img src="/brand-logo-transparent.png" alt="址得选" className="profile-avatar-v2" />
          <div className="profile-user-main">
            <div className="profile-name-line">
              <strong>{username}</strong>
              <em>{isMember ? tierLabel : 'VIP'}</em>
            </div>
            <span className="profile-phone">
              {accountLine}
            </span>
          </div>
        </div>

        <div className="profile-stat-panel">
          <button type="button" onClick={() => setRechargeOpen(true)}>
            <strong>{points}</strong>
            <span>剩余点数</span>
            <small>可用点数</small>
          </button>
          <button type="button" onClick={() => navigate('/records')}>
            <strong>{profile.total_reports}</strong>
            <span>已生成报告</span>
            <small>累计分析</small>
          </button>
          <button type="button" onClick={() => navigate('/favorites')}>
            <strong>{favoriteCount}</strong>
            <span>收藏地址</span>
            <small>机会池</small>
          </button>
          <button type="button" className="profile-report-ring" onClick={() => navigate('/records')}>
            <i>▤</i>
            <span>查看报告</span>
          </button>
        </div>
      </section>

      <main className="profile-content-v2">
        <section className="profile-vip-card-v2">
          <div className="profile-vip-head">
            <div>
              <h3>VIP会员 <span>{isMember ? `${daysLeft}天` : '未开通'}</span></h3>
              <p>{isMember ? `有效期至 ${membership?.expiry?.slice(0, 10) || '-'}` : '开通会员，解锁全部高级功能'}</p>
            </div>
            <button type="button" onClick={() => setRechargeOpen(true)}>{isMember ? '立即续费' : '立即开通'}</button>
          </div>
          <div className="profile-benefits">
            {[
              ['∞', '无限分析', '次数不限'],
              ['PDF', 'PDF导出', '高清报告'],
              ['⌁', '盈利预测', '精准估算'],
              ['◎', '高级模型', '多维评估'],
              ['▥', '数据对比', '深度分析'],
              ['☎', '专属客服', '优先服务'],
            ].map(([icon, title, desc]) => (
              <div key={title}>
                <i>{icon}</i>
                <strong>{title}</strong>
                <span>{desc}</span>
              </div>
            ))}
          </div>
        </section>

        {freePointActive && countdown && (
          <div className="profile-expire-tip">
            免费分析额度还有 <strong>{countdown}</strong> 过期，请尽快使用
          </div>
        )}

        <section className="profile-points-card-v2">
          <div className="profile-card-title">
            <h3><span>●</span> 我的点数</h3>
            <div>
              <button type="button" className="profile-code-btn" onClick={() => setCdkOpen(true)}>兑换码</button>
              <button type="button" className="profile-buy-btn" onClick={() => setRechargeOpen(true)}>获取点数</button>
            </div>
          </div>
          <div className="profile-points-body">
            <div className="profile-points-num">
              <strong>{points}</strong>
              <span>点</span>
              <small>当前剩余点数</small>
            </div>
            <div className="profile-flow">
              <p>点数可用于生成选址分析报告</p>
              <div>
                {['选地址', 'AI分析', '生成报告', '导出使用'].map((item, index) => (
                  <span key={item}>
                    <i>{['⌖', '✚', '▤', '↓'][index]}</i>
                    <small>{item}</small>
                  </span>
                ))}
              </div>
            </div>
          </div>
          {!isMember && points <= 3 && (
            <div className="profile-low-points">点数即将用完，建议充值或开通会员</div>
          )}
        </section>

        <section className="profile-menu-card-v2">
          {menuRows.map(row => (
            <button type="button" key={row.title} onClick={row.onClick}>
              <i>{row.icon}</i>
              <strong>{row.title}</strong>
              <span>{row.sub}</span>
              <em>›</em>
            </button>
          ))}
          {(csWechat || csPhone) && (
            <button type="button" onClick={async () => {
              if (csWechat) {
                try {
                  await navigator.clipboard.writeText(csWechat)
                  showToast('微信号已复制，请前往微信添加')
                } catch {
                  showToast(`客服微信：${csWechat}`)
                }
              } else {
                window.location.href = `tel:${csPhone}`
              }
            }}>
              <i>☎</i>
              <strong>联系客服</strong>
              <span>{csWechat ? '复制客服微信' : '拨打客服电话'}</span>
              <em>›</em>
            </button>
          )}
        </section>

        <div className="profile-copyright">© 2026 AI 选址分析决策平台</div>
      </main>

      {rechargeOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setRechargeOpen(false)}>
          <div className="recharge-sheet mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-bold text-slate-900 text-center">获取更多点数</h3>
            <p className="mt-2 text-sm text-slate-500 text-center leading-relaxed">
              开通会员或购买点数，请扫码添加专属客服微信，<br/>或使用兑换码激活。
            </p>

            <div className="recharge-tabs">
              <button
                type="button"
                className={rechargeTab === 'points' ? 'is-active' : ''}
                onClick={() => setRechargeTab('points')}
              >
                点数包
              </button>
              <button
                type="button"
                className={rechargeTab === 'membership' ? 'is-active' : ''}
                onClick={() => setRechargeTab('membership')}
              >
                会员套餐
              </button>
            </div>

            {(membershipSkus.length > 0 || pointSkus.length > 0) && (
              <div className="mt-4 space-y-3">
                {rechargeTab === 'membership' && membershipSkus.length > 0 && (
                  <div>
                    <div className="mb-2 text-[11px] font-bold text-slate-500">会员套餐</div>
                    <div className="grid grid-cols-3 gap-2">
                      {membershipSkus.map(item => (
                        <button key={item.id} type="button"
                          onClick={() => showToast(`已选择 ${item.label}，请扫码联系客服开通`, 3000)}
                          className="relative rounded-xl border border-amber-100 bg-amber-50/70 px-2 py-3 text-center hover:border-amber-300">
                          {item.badge && <em className="absolute -top-2 right-2 rounded-full bg-amber-500 px-1.5 py-0.5 text-[9px] not-italic font-bold text-white">{item.badge}</em>}
                          <strong className="block text-xs text-slate-800">{item.label}</strong>
                          <span className="mt-1 block text-sm font-black text-amber-600">¥{item.price}</span>
                          <em className="mt-0.5 block not-italic text-[10px] text-slate-400">{item.duration_days || 0}天不限次分析和导出</em>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {rechargeTab === 'points' && pointSkus.length > 0 && (
                  <div>
                    <div className="mb-2 text-[11px] font-bold text-slate-500">点数包</div>
                    <div className="grid grid-cols-2 gap-2">
                      {pointSkus.map(item => (
                        <button key={item.id} type="button"
                          onClick={() => showToast(`已选择 ${item.label}，请扫码联系客服充值`, 3000)}
                          className="relative rounded-xl border border-blue-100 bg-blue-50/60 px-3 py-2 text-left hover:border-blue-300">
                          {item.badge && <em className="absolute -top-2 right-2 rounded-full bg-blue-600 px-1.5 py-0.5 text-[9px] not-italic font-bold text-white">{item.badge}</em>}
                          <span className="block text-xs font-bold text-slate-800">{item.label}</span>
                          <span className="mt-0.5 block text-[11px] text-slate-500">{item.credits || 0} 次分析</span>
                          <strong className="mt-1 block text-sm text-blue-600">¥{item.price}</strong>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="mt-4 flex flex-col items-center rounded-xl bg-slate-50 border border-slate-100 p-4">
              {csQrUrl ? (
                <img src={getAssetUrl(csQrUrl)} alt="客服二维码"
                  className="w-36 h-36 object-contain rounded-lg mb-2 border border-slate-200" />
              ) : (
                <div className="w-36 h-36 rounded-lg bg-slate-200 flex items-center justify-center mb-2">
                  <span className="text-4xl text-slate-400">♟</span>
                </div>
              )}
              <span className="text-xs font-semibold text-slate-600">扫码联系专属客服</span>
              <span className="text-[10px] text-slate-400 mt-0.5">如需充值点数或开通会员，请添加官方客服微信。</span>
            </div>

            <div className="mt-4 pt-4 border-t border-slate-100">
              <p className="text-xs text-slate-500 text-center mb-3">已有兑换码？直接激活</p>
              <div className="flex gap-2">
                <input value={cdkInput} onChange={e => setCdkInput(e.target.value.toUpperCase())}
                  placeholder="AI-XXXXXXXX"
                  className="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm font-mono text-center tracking-widest focus:outline-none focus:border-blue-400" />
                <button onClick={async () => {
                  const code = cdkInput.trim()
                  if (!code) { showToast('请输入兑换码', 3000); return }
                  try {
                    const token = getToken()
                    const headers = { 'Content-Type': 'application/json' }
                    if (token) headers['Authorization'] = `Bearer ${token}`
                    const r = await fetch('/api/admin/cdk/activate', { method: 'POST', headers, body: JSON.stringify({ code }) })
                    const d = await r.json()
                    if (r.ok) {
                      showToast(`兑换成功！+${d.credits_added} 点已到账`, 3500)
                      setCdkInput('')
                      setRechargeOpen(false)
                      refetch()
                    } else {
                      showToast(d.detail || '兑换失败，请检查兑换码', 4000)
                    }
                  } catch {
                    showToast('网络异常，请检查网络后重试', 4000)
                  }
                }} className="flex-shrink-0 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700">激活</button>
              </div>
            </div>

            <button onClick={() => setRechargeOpen(false)} className="mt-4 w-full rounded-lg border border-slate-200 py-2 text-sm text-slate-500">关闭</button>
          </div>
        </div>
      )}

      {cdkOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setCdkOpen(false)}>
          <div className="mx-4 w-full max-w-sm rounded-xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
            <h3 className="text-base font-bold text-slate-900">兑换码激活</h3>
            <p className="mt-1 text-xs text-slate-400">输入兑换码，点数将自动充值到您的账户</p>
            <input value={cdkInput} onChange={e => setCdkInput(e.target.value.toUpperCase())}
              placeholder="如：AI-XXXXXXXX" className="mt-4 w-full rounded-lg border border-slate-200 px-3 py-3 text-sm font-mono text-center tracking-widest focus:outline-none focus:border-blue-400" />
            <div className="mt-4 flex gap-3">
              <button onClick={() => setCdkOpen(false)} className="flex-1 rounded-lg border border-slate-200 py-2 text-sm text-slate-500">取消</button>
              <button onClick={async () => {
                const code = cdkInput.trim()
                if (!code) { showToast('请输入兑换码', 3000); return }
                try {
                  const token = getToken()
                  const headers = { 'Content-Type': 'application/json' }
                  if (token) headers['Authorization'] = `Bearer ${token}`
                  const r = await fetch('/api/admin/cdk/activate', { method: 'POST', headers, body: JSON.stringify({ code }) })
                  const d = await r.json()
                  if (r.ok) {
                    showToast(`兑换成功！+${d.credits_added} 点已到账`, 3500)
                    setCdkOpen(false)
                    setCdkInput('')
                    refetch()
                  } else {
                    showToast(d.detail || '兑换失败，请检查兑换码', 4000)
                  }
                } catch {
                  showToast('网络异常，请检查网络后重试', 4000)
                }
              }} className="flex-1 rounded-lg bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-700">激活</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
