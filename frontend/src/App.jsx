import { useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import MainLayout from './layouts/MainLayout'
import HomePage from './pages/HomePage'
import RecordDetail from './pages/RecordDetail'
import AdminPage from './pages/AdminPage'
import RecordsView from './components/RecordsView'
import FavoriteView from './components/FavoriteView'
import ProfileView from './components/ProfileView'
import { ensureToken } from './services/api'

function SafeView({ children }) {
  return <ErrorBoundary>{children}</ErrorBoundary>
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
      <Route path="/record/:uuid" element={<SafeView><RecordDetail /></SafeView>} />
      <Route path="/admin" element={<SafeView><AdminPage /></SafeView>} />
    </Routes>
  )
}
