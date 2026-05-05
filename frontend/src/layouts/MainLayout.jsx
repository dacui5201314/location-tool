import { useRef, useCallback, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'

const TABS = [
  { path: '/', icon: '⌂', label: '选址分析' },
  { path: '/records', icon: '▤', label: '分析记录' },
  { path: '/favorites', icon: '☆', label: '收藏地址' },
  { path: '/profile', icon: '♙', label: '我的' },
]

const TAB_PATHS = TABS.map(t => t.path)

export default function MainLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const activeTab = TABS.findIndex(t => t.path === location.pathname)
  const lockRef = useRef(false)

  // 返回拦截：在 Tab 子页面按返回 → 回到首页，不退出应用
  useEffect(() => {
    const onPopState = () => {
      const current = window.location.pathname
      // 仅在 Tab 子页面（非首页）拦截
      if (current !== '/' && TAB_PATHS.includes(current)) {
        navigate('/', { replace: true })
      }
    }
    window.addEventListener('popstate', onPopState)
    return () => window.removeEventListener('popstate', onPopState)
  }, [navigate])

  const handleTabClick = useCallback((path) => {
    if (lockRef.current) return
    if (location.pathname === path) return
    lockRef.current = true
    navigate(path, { replace: true })?.catch(() => {})
    setTimeout(() => { lockRef.current = false }, 350)
  }, [navigate, location.pathname])

  return (
    <div className="min-h-screen" style={{ background: 'var(--page-bg)' }}>
      <Outlet />
      <nav className="bottom-nav" aria-label="产品导航">
        {TABS.map((t, i) => (
          <button key={t.path} type="button"
            className={activeTab === i ? 'is-active' : ''}
            onClick={() => handleTabClick(t.path)}>
            <span>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </nav>
    </div>
  )
}
