import { Suspense, lazy, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import MainLayout from './layouts/MainLayout'
import HomePage from './pages/HomePage'
import RecordsView from './components/RecordsView'
import FavoriteView from './components/FavoriteView'
import ProfileView from './components/ProfileView'
import { ensureToken } from './services/api'

const RecordDetail = lazy(() => import('./pages/RecordDetail'))
const AdminPage = lazy(() => import('./pages/AdminPage'))

function SafeView({ children }) {
  return <ErrorBoundary>{children}</ErrorBoundary>
}

function RouteFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="rounded-lg bg-white px-5 py-3 text-sm font-semibold text-slate-500 shadow-sm border border-slate-100">
        加载中...
      </div>
    </div>
  )
}

function LazyView({ children }) {
  return (
    <Suspense fallback={<RouteFallback />}>
      {children}
    </Suspense>
  )
}

export default function App() {
  // ★ App 级 Token 预热：路由渲染前异步启动 Token 签发
  // 不阻塞渲染 — useFetch/authFetch 内部有门控，会等待此 Promise 完成
  useEffect(() => {
    ensureToken().catch(() => {})
  }, [])

  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route path="/" element={<SafeView><HomePage /></SafeView>} />
        <Route path="/records" element={<SafeView><RecordsView /></SafeView>} />
        <Route path="/favorites" element={<SafeView><FavoriteView /></SafeView>} />
        <Route path="/profile" element={<SafeView><ProfileView /></SafeView>} />
      </Route>
      <Route path="/record/:uuid" element={<SafeView><LazyView><RecordDetail /></LazyView></SafeView>} />
      <Route path="/admin" element={<SafeView><LazyView><AdminPage /></LazyView></SafeView>} />
    </Routes>
  )
}
