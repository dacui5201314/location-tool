import { useState, useCallback, useEffect, useRef } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import AddressInput from '../components/AddressInput'
import MapView from '../components/MapView'
import AnalysisResult from '../components/AnalysisResult'
import BusinessTypeSelector from '../components/BusinessTypeSelector'
import BrandInput from '../components/BrandInput'
import StoreSizeInput from '../components/StoreSizeInput'
import PdfExport from '../components/PdfExport'
import useAMap from '../hooks/useAMap'
import { ensureToken, fetchProfile, checkFavorite, addFavorite, deleteFavorite, getToken } from '../services/api'
import LoginModal from '../components/LoginModal'

const HERO_POINTS = [
  { title: '数据驱动决策', desc: '多源数据融合' },
  { title: '多维度分析', desc: '全面评估位置价值' },
  { title: '降低开店风险', desc: '科学决策更稳健' },
]

const PANEL_STATS = [
  { label: '已分析商铺', value: '12,856+', hint: '数据持续更新中' },
  { label: '平均回本预测准确率', value: '87%', hint: '基于历史真实数据' },
]

function HeroGraphic() {
  return (
    <div className="hero-graphic" aria-hidden="true">
      <div className="city-grid">
        <span className="tower tower-a" />
        <span className="tower tower-b" />
        <span className="tower tower-c" />
        <span className="tower tower-d" />
        <span className="scan-line" />
      </div>
      <div className="platform">
        <span className="platform-ring ring-one" />
        <span className="platform-ring ring-two" />
        <span className="pin-core" />
      </div>
      <div className="hero-pin">
        <span />
      </div>
    </div>
  )
}

function FeatureTile({ tone, title, desc, icon }) {
  return (
    <div className="feature-tile">
      <span className={`feature-icon ${tone}`}>{icon}</span>
      <div className="min-w-0">
        <div className="text-sm font-bold text-slate-900">{title}</div>
        <div className="mt-0.5 text-xs leading-5 text-slate-500">{desc}</div>
      </div>
    </div>
  )
}

export default function HomePage() {
  const navigate = useNavigate()
  const [selectedLocation, setSelectedLocation] = useState(null)
  const [businessType, setBusinessType] = useState('')
  const [brandName, setBrandName] = useState('')
  const [storeSize, setStoreSize] = useState('')
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [isFavorited, setIsFavorited] = useState(false)
  const [favoriteId, setFavoriteId] = useState(null)
  const [favLoading, setFavLoading] = useState(false)
  const [brandError, setBrandError] = useState(false)
  const [businessError, setBusinessError] = useState(false)
  const [toast, setToast] = useState('')
  const showToast = (msg) => { setToast(msg); setTimeout(() => setToast(''), 2000) }
  const [loginModalOpen, setLoginModalOpen] = useState(false)
  // ── 业态专属规则匹配 ──
  const [matchedIndustryId, setMatchedIndustryId] = useState(null)
  const [announcement, setAnnouncement] = useState('')
  const announceRef = useRef(null)

  // 拉取全局公告
  useEffect(() => {
    fetch('/api/admin/ui-config')
      .then(r => r.json())
      .then(d => { if (d?.announcement) setAnnouncement(d.announcement) })
      .catch(() => {})
  }, [])

  // 公告文字过长时开启跑马灯
  useEffect(() => {
    const el = announceRef.current
    if (!el || !announcement) return
    if (el.scrollWidth > el.clientWidth) {
      el.style.animation = 'marquee 15s linear infinite'
    }
  }, [announcement])

  const location = useLocation()
  const { loaded: mapLoaded, error: mapError, locateMe } = useAMap()
  const [welcomeOpen, setWelcomeOpen] = useState(false)
  const [freePointActive, setFreePointActive] = useState(false)
  const [freePointExpireAt, setFreePointExpireAt] = useState(null)
  const [countdown, setCountdown] = useState('')
  const countdownRef = useRef(null)

  // 新用户欢迎 + 免费点数检测 + JWT 初始化
  useEffect(() => {
    const init = async () => {
      try {
        // 确保 JWT Token 有效（无则自动签发）
        await ensureToken()
        // 拉取完整用户信息
        const profile = await fetchProfile()
        const dismissed = localStorage.getItem('welcome_dismissed')
        if (!dismissed && profile.is_new_user) setWelcomeOpen(true)
        const u = profile.user
        if (u?.free_point_active && u?.free_point_expire_at) {
          setFreePointActive(true)
          setFreePointExpireAt(u.free_point_expire_at)
        }
      } catch (e) {
        // 静默失败，后续请求会触发 401 重试
      }
    }
    init()
  }, [])

  // 每秒更新倒计时
  useEffect(() => {
    if (!freePointExpireAt) return
    const tick = () => {
      const now = Date.now()
      const expire = new Date(freePointExpireAt).getTime()
      const diff = expire - now
      if (diff <= 0) {
        setCountdown('已过期')
        setFreePointActive(false)
        if (countdownRef.current) clearInterval(countdownRef.current)
        return
      }
      const h = Math.floor(diff / 3600000)
      const m = Math.floor((diff % 3600000) / 60000)
      setCountdown(`${h}小时${m}分`)
    }
    tick()
    countdownRef.current = setInterval(tick, 30000) // 30s 更新一次
    return () => { if (countdownRef.current) clearInterval(countdownRef.current) }
  }, [freePointExpireAt])

  const dismissWelcome = () => {
    localStorage.setItem('welcome_dismissed', '1')
    setWelcomeOpen(false)
  }

  // 收藏页跳转过来时，自动填入地址和坐标
  useEffect(() => {
    const loc = location.state?.loc
    if (loc && loc.latitude && loc.longitude) {
      const place = {
        name: loc.custom_name || loc.address,
        address: loc.address,
        location: { lng: loc.longitude, lat: loc.latitude },
      }
      setSelectedLocation(place)
      // 清除 state 防止刷新后重复触发
      window.history.replaceState({}, '')
    }
  }, [])

  const handleSelectAddress = useCallback((place) => {
    setSelectedLocation(place); setResult(null); setError(null)
  }, [])

  const handlePositionChange = useCallback((newPos) => {
    setSelectedLocation((prev) => {
      const addr = newPos.address || ''
      if (!prev) {
        return { name: addr, address: addr, location: { lng: newPos.lng, lat: newPos.lat } }
      }
      return { ...prev, location: { lng: newPos.lng, lat: newPos.lat }, name: addr || prev.name, address: addr || prev.address }
    })
  }, [])

  // 检查收藏状态
  useEffect(() => {
    if (!selectedLocation?.location) { setIsFavorited(false); setFavoriteId(null); return }
    const { lng, lat } = selectedLocation.location
    checkFavorite(lat, lng)
      .then(d => { setIsFavorited(!!d.is_favorited); setFavoriteId(d.favorite_id) })
      .catch(() => {})
  }, [selectedLocation?.location?.lng, selectedLocation?.location?.lat])

  const handleToggleFavorite = async () => {
    if (favLoading || !selectedLocation?.location) return
    setFavLoading(true)
    try {
      if (isFavorited && favoriteId) {
        await deleteFavorite(favoriteId)
        setIsFavorited(false); setFavoriteId(null)
        showToast('已取消收藏')
      } else {
        const d = await addFavorite(
          selectedLocation.name || '',
          selectedLocation.address || '',
          selectedLocation.location.lat,
          selectedLocation.location.lng,
        )
        if (d.ok) { setIsFavorited(true); setFavoriteId(d.favorite.id); showToast('收藏成功，可在底部收藏夹查看') }
      }
    } catch (err) { showToast(err?.message || '操作失败，请重试') }
    finally { setFavLoading(false) }
  }

  const validateForm = () => {
    if (!selectedLocation?.location) { showToast('请先在地图上选择门店位置'); return false }
    if (!businessType) { setBusinessError(true); showToast('请完整选择选址业态'); return false }
    if (!brandName.trim()) { setBrandError(true); showToast('请输入品牌名称或主营特色'); return false }
    if (!storeSize) { showToast('请输入门店预估面积，用于租金与人效精算'); return false }
    const areaNum = parseFloat(storeSize)
    if (isNaN(areaNum) || areaNum <= 0) { showToast('店面面积必须大于 0'); return false }
    if (areaNum > 10000) { showToast('面积数值较大，请确认输入无误'); return false }
    return true
  }

  const [analyzeSteps, setAnalyzeSteps] = useState([])
  const [currentStep, setCurrentStep] = useState(0)

  /**
   * 安全解析 SSE data 行中的 JSON 事件。
   * 返回 null 表示该 segment 不含有效 data 行或 JSON 未完整到达。
   * JSON 解析异常时打印警告便于排查。
   */
  const _parseSseEvent = (segment) => {
    const dataLine = segment.split('\n').find(l => l.startsWith('data: '))
    if (!dataLine) return null
    const jsonStr = dataLine.slice(6)
    try {
      return JSON.parse(jsonStr)
    } catch {
      // JSON 超长跨 chunk → 等待更多数据；纯格式异常 → 记日志
      if (jsonStr.length > 500) {
        console.warn('[SSE] JSON parse failed, likely incomplete chunk, len:', jsonStr.length)
      }
      return null
    }
  }

  const handleAnalyze = useCallback(async () => {
    if (!validateForm()) return

    const token = getToken()
    if (!token) {
      setLoginModalOpen(true)
      showToast('请先注册或登录后再进行分析')
      return
    }

    setAnalyzing(true); setError(null); setResult(null)
    setAnalyzeSteps([]); setCurrentStep(0)

    let reader = null
    try {
      // ═══════════════════════════════════════════
      // ★ 纯血原生 fetch — 彻底绕开任何 XHR/axios 拦截器
      // ═══════════════════════════════════════════
      const resp = await window.fetch('/api/analyze', {
        method: 'POST',
        cache: 'no-store',
        headers: {
          'Accept': 'text/event-stream',
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          address: selectedLocation.address || selectedLocation.name,
          location: { lng: selectedLocation.location.lng, lat: selectedLocation.location.lat },
          provider: 'deepseek',
          business_type: businessType,
          brand_name: brandName,
          store_size: parseInt(storeSize) || 0,
          real_data: null,
          ...(matchedIndustryId ? { industry_id: matchedIndustryId } : {}),
        }),
      })

      if (!resp.ok) {
        let errMsg = `请求失败 (${resp.status})`
        try {
          const errBody = await resp.text()
          if (errBody) {
            const parsed = JSON.parse(errBody)
            errMsg = parsed.detail || parsed.message || errBody.slice(0, 120)
          }
        } catch {}
        throw new Error(errMsg)
      }

      // ═══════════════════════════════════════════
      // ★ 全缓冲读取 — 免疫 Vite 代理 / Nginx / uvicorn 缓冲层
      // 不依赖流式 chunk：把全部数据读完再解析，然后逐行动画播放
      // ═══════════════════════════════════════════
      reader = resp.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let rawBody = ''

      while (true) {
        const { done, value } = await reader.read()
        if (value) {
          rawBody += decoder.decode(value, { stream: true })
        }
        if (done) break
      }

      // ── 一次性切割全部 SSE 事件 ──
      console.log('[SSE DEBUG] rawBody length:', rawBody.length, 'preview:', rawBody.slice(0, 300))
      const allEvents = []
      const segments = rawBody.split('\n\n')
      console.log('[SSE DEBUG] segments after split:', segments.length)
      for (const seg of segments) {
        const event = _parseSseEvent(seg)
        if (event) allEvents.push(event)
      }

      if (allEvents.length === 0) {
        // ★ 纯 JSON 兜底：后端在流启动前抛了异常（如 LLM JSON 解析失败），
        // FastAPI 拦截异常并返回了普通 JSON 错误响应（而非 SSE 格式）。
        const trimmed = rawBody.trim()
        if (trimmed.startsWith('{')) {
          try {
            const jsonResult = JSON.parse(trimmed)
            // 明确携带 error 字段 → 不是正常报告，是后端异常
            if (jsonResult.error) {
              throw new Error(jsonResult.error + (jsonResult.summary ? ' — ' + jsonResult.summary : ''))
            }
            // 不含 error 且包含评分/详情 → 正常的纯 JSON 报告
            if (jsonResult.score !== undefined || jsonResult.details) {
              setResult(jsonResult)
              setCurrentStep(4)
              setAnalyzeSteps([
                { step: 1, msg: 'POI 数据采集完成' },
                { step: 2, msg: '数据脱水与交叉比对完成' },
                { step: 3, msg: 'AI 商业评估完成' },
                { step: 4, msg: '✅ 报告生成完毕！' },
              ])
              await new Promise(r => setTimeout(r, 500))
              reader?.cancel()
              setAnalyzing(false)
              return
            }
          } catch (parseErr) {
            // JSON 解析出来但 check 失败 → 抛出原始错误
            if (parseErr.message && !parseErr.message.startsWith('Unexpected')) {
              throw parseErr
            }
          }
        }
        throw new Error(`分析服务返回异常 (${rawBody.length}字节)，请检查后端日志`)
      }

      // ── 逐步骤动画播放（仿流式效果，每步延迟 300ms）──
      let finalResult = null
      for (const event of allEvents) {
        if (event.step === 'error') {
          throw new Error(event.msg || '分析失败')
        }
        setCurrentStep(event.step)
        setAnalyzeSteps(prev => [...prev, event])
        if (event.step === 4) {
          finalResult = event.result || null
        }
        await new Promise(r => setTimeout(r, 300))
      }

      // ── 平滑收尾 ──
      if (finalResult) {
        setResult(finalResult)
        await new Promise(r => setTimeout(r, 500))
      } else {
        throw new Error('分析未生成有效报告，请重试')
      }
    } catch (err) {
      setError(err.message || '分析失败，请重试')
    } finally {
      // ★ 确保 reader 释放，避免锁死 TCP 连接
      if (reader) {
        try { reader.cancel() } catch {}
      }
      setAnalyzing(false)
    }
  }, [selectedLocation, businessType, brandName, storeSize])

  // ── businessType 变更时调用后端匹配接口 ──
  useEffect(() => {
    if (!businessType) { setMatchedIndustryId(null); return }
    const controller = new AbortController()
    fetch(`/api/industries/match?business_type=${encodeURIComponent(businessType)}`, { signal: controller.signal })
      .then(r => r.json())
      .then(d => setMatchedIndustryId(d.matched ? d.industry_id : null))
      .catch(() => setMatchedIndustryId(null))
    return () => controller.abort()
  }, [businessType])

  const canAnalyze = selectedLocation && !analyzing

  return (
    <div className="home-screen text-slate-900">

      {/* 新用户欢迎弹窗 */}
      {welcomeOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/50 px-4">
          <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl text-center animate-fade-in">
            <div className="text-5xl mb-4">🎁</div>
            <h2 className="text-lg font-black text-slate-900">欢迎使用 AI 选址分析</h2>
            <p className="mt-3 text-sm leading-6 text-slate-600">
              系统已赠送您 <strong className="text-blue-600 text-base">1 个初始点数</strong>
            </p>
            <p className="mt-1 text-xs text-slate-500">
              您可以立即使用址得选开始您的第一次商业选址分析
            </p>
            <div className="mt-2 inline-block rounded-full bg-blue-50 px-3 py-1 text-[11px] font-semibold text-blue-600">
              每个新用户仅赠送一次，请珍惜使用
            </div>
            <button
              onClick={dismissWelcome}
              className="mt-5 w-full rounded-xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700 transition-colors"
            >
              开始体验
            </button>
          </div>
        </div>
      )}

      {/* 地图加载失败提示 */}
      {mapError && (
        <div className="map-error-banner">
          <span className="text-lg">🗺️</span>
          <div>
            <div className="font-bold text-sm">地图服务暂不可用</div>
            <div className="text-xs mt-0.5 opacity-80">{String(mapError?.message || mapError)}</div>
          </div>
        </div>
      )}

      {/* 全局公告栏 */}
      {announcement && (
        <div className="announcement-bar">
          <div className="announcement-inner">
            <span className="announcement-icon">📢</span>
            <span className="announcement-text" ref={announceRef}>{announcement}</span>
          </div>
        </div>
      )}

      {/* 免费点数过期倒计时 Banner */}
      {freePointActive && countdown && (
        <div className="free-point-banner">
          <div className="banner-inner">
            <span className="banner-icon">🎁</span>
            <span className="banner-text">
              您的 <strong>1 次免费专业选址分析额度</strong> 还有 <strong className="countdown-num">{countdown}</strong> 过期，请尽快使用！
            </span>
          </div>
        </div>
      )}

      <header className="commercial-hero">
        <div className="mx-auto max-w-[520px] px-5 pb-7 pt-6">
          <div className="flex items-start justify-between gap-4">
            <div className="brand-lockup">
              <img src="/brand-logo-transparent.png" alt="址得选" className="brand-logo" />
              <div className="min-w-0">
                <h1 className="text-[30px] font-black leading-tight text-white">址得选</h1>
                <p className="mt-1 text-base font-semibold text-blue-100/70">址得选 · AI智能选址</p>
              </div>
            </div>
            <button type="button" className="notification-button" onClick={() => navigate('/records', { replace: true })} aria-label="查看分析记录">
              <span className="notification-dot" />
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
                <path d="M13.73 21a2 2 0 0 1-3.46 0" />
              </svg>
            </button>
          </div>
          {toast && <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 rounded-full bg-slate-800 text-white text-xs px-5 py-2 shadow-lg">{toast}</div>}

          <div className="hero-copy">
            <div className="min-w-0">
              <h2 className="hero-title">
                AI帮你判断<br />这个位置能不能<span>赚钱</span>
              </h2>
              <p className="hero-subtitle">智能选址 · 科学决策 · 降低风险</p>
            </div>
            <HeroGraphic />
          </div>

          <div className="hero-points">
            {HERO_POINTS.map(point => (
              <span key={point.title}>
                <i />
                <strong>{point.title}</strong>
                <small>{point.desc}</small>
              </span>
            ))}
          </div>

          <div className="hero-search">
            <div className="flex-1">
              <AddressInput onSelect={handleSelectAddress} disabled={analyzing} mapLoaded={mapLoaded}
                externalAddress={selectedLocation?.address || selectedLocation?.name} onToast={showToast} />
              <div className={`favorite-hint-line ${selectedLocation ? 'is-ready' : ''}`}>
                <div className="favorite-hint-copy">
                  <span>★</span>
                  <em>{selectedLocation ? '您可以点击旁边按钮收藏该地址' : '选择位置后，可一键收藏地址'}</em>
                </div>
                {selectedLocation && (
                  <button type="button" onClick={handleToggleFavorite} disabled={favLoading}
                    className={`favorite-inline-button ${isFavorited ? 'is-active' : ''}`}
                    aria-label={isFavorited ? '取消收藏该地址' : '收藏该地址'}>
                    <svg width="18" height="18" viewBox="0 0 24 24"
                      fill={isFavorited ? 'currentColor' : 'none'}
                      stroke="currentColor"
                      strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                    </svg>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="home-main mx-auto max-w-[520px] px-5 pb-6 safe-bottom">
        <section className="map-card" style={{ position: 'relative' }}>
          <div className="map-toolbar"><span>当前位置</span><span>{analyzing ? '分析中...' : '可拖动标记微调'}</span></div>
          <div className="map-shell commercial-map">
            <MapView position={selectedLocation?.location} onPositionChange={handlePositionChange} mapLoaded={mapLoaded} mapError={mapError}
              selectedAddress={selectedLocation?.address || selectedLocation?.name} />
          </div>
          {analyzing && (
            <div style={{ position: 'absolute', inset: 0, zIndex: 10, background: 'rgba(255,255,255,0.3)', borderRadius: 8, cursor: 'not-allowed' }} />
          )}
        </section>

        <section className="analysis-panel">
          <div className="section-heading">
            <strong>选择业态</strong>
            <span>全部业态 ›</span>
          </div>
          <BusinessTypeSelector selected={businessType} onChange={(v) => { setBusinessType(v); if (v) setBusinessError(false) }} disabled={analyzing} error={businessError} hideLabel />

          <div className="panel-stats">
            {PANEL_STATS.map(stat => (
              <div key={stat.label}>
                <span>{stat.label}</span>
                <strong>{stat.value}</strong>
                <em>{stat.hint}</em>
              </div>
            ))}
            <div className="trend-line" aria-hidden="true">
              <span />
            </div>
          </div>

          <div className="mt-4 rounded-lg bg-slate-50/70 p-3">
            <div className="section-heading compact"><strong>经营画像</strong><span>品牌与面积越清晰，报告越准</span></div>
          <div className="space-y-3">
            <BrandInput value={brandName} onChange={(v) => { setBrandName(v); setBrandError(!v.trim()) }} onFocus={() => setBrandError(!brandName.trim())} disabled={analyzing} error={brandError} />
            <StoreSizeInput value={storeSize} onChange={setStoreSize} disabled={analyzing} />
          </div>
          </div>

          {error && <div className="mt-4 rounded-lg border border-red-100 bg-red-50 p-3 text-sm leading-6 text-red-700">{error}</div>}

          <button onClick={handleAnalyze} disabled={!canAnalyze} className="analysis-banner">
            <span className="banner-mark">✦</span>
            <span className="min-w-0">
              <strong>{analyzing ? 'AI 选址报告生成中...' : '立即生成选址报告'}</strong>
              <em>{analyzing ? '正在采集周边数据并评估商业可行性' : selectedLocation ? '生成客流、竞品、消费力与风险建议' : '请先搜索或定位门店地址'}</em>
            </span>
          </button>

          <div className="trust-row">
            <FeatureTile tone="blue" icon="✓" title="权威数据来源" desc="多渠道数据融合" />
            <FeatureTile tone="violet" icon="◔" title="AI智能分析" desc="多维度模型算法" />
            <FeatureTile tone="green" icon="◆" title="专业团队支持" desc="7×24小时服务" />
          </div>
        </section>

        {/* ── SSE 实时分析控制台 ── */}
        {analyzing && (
          <div className="analyze-console">
            <div className="console-header">
              <span className="console-dot" />
              <span className="console-title">AI 选址分析引擎 v4.0</span>
              <span className="console-pulse" />
            </div>
            <div className="console-body">
              {[1, 2, 3, 4].map(step => {
                const evt = analyzeSteps.find(s => s.step === step)
                const isDone = !!evt
                const isCurrent = currentStep === step
                const stepLabels = {
                  1: 'POI 数据采集',
                  2: '数据脱水 & 竞品交叉比对',
                  3: 'AI 商业评估模型',
                  4: '生成选址报告',
                }
                return (
                  <div key={step} className={`console-line ${isDone ? 'done' : ''} ${isCurrent ? 'active' : ''}`}>
                    <span className="console-caret">
                      {isDone ? '✅' : isCurrent ? '▸' : '·'}
                    </span>
                    <span className="console-label">{stepLabels[step]}</span>
                    {isDone && <span className="console-msg">{evt.msg}</span>}
                    {isCurrent && !isDone && (
                      <span className="console-msg">
                        {analyzeSteps.find(s => s.step === step)?.msg || '处理中...'}
                        <span className="console-blink">▌</span>
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
            <div className="console-footer">
              {currentStep >= 4 ? '✅ 报告已生成，正在加载...' : '⏳ 请耐心等待，AI 正在深度分析中...'}
            </div>
          </div>
        )}

        {result && !analyzing && (
          <div className="space-y-3 animate-in">
            <AnalysisResult data={result} />
            <PdfExport selectedLocation={selectedLocation} result={result} businessType={businessType} brandName={brandName} />
            <div className="h-28 w-full flex-shrink-0" />
          </div>
        )}

        <footer className="px-3 py-4 text-center text-[11px] leading-5 text-slate-400">
          数据底座：全网多维度商业 POI 聚合数据库 | 仅供参考，实际决策请结合实地考察与多方因素
        </footer>
      </main>

      <LoginModal
        open={loginModalOpen}
        onSuccess={() => { setLoginModalOpen(false); showToast('登录成功，请开始分析') }}
        onClose={() => setLoginModalOpen(false)}
      />
    </div>
  )
}
