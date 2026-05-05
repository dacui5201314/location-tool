import { useState, useEffect, useRef, useCallback } from 'react'
import { getToken, ensureToken } from '../services/api'

/**
 * 安全数据请求 Hook — 自动门控 Token 就绪 + JWT Header
 * - await ensureToken() 确保 Token 就绪后才发起请求（消除抢跑 401）
 * - AbortController 取消上一次请求
 * - isMounted 守卫防止卸载后 setState
 * - 页面切换时自动清理
 * - 401 时自动清除 Token
 */
export default function useFetch(url, options = {}) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const mountedRef = useRef(true)
  const abortRef = useRef(null)

  const fetchData = useCallback(() => {
    if (abortRef.current) abortRef.current.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setLoading(true)
    setError('')

    const doFetch = async () => {
      // ★ 门控：确保 Token 就绪后再发起请求
      try { await ensureToken() } catch (e) { /* 失败也继续，交由后端返回 401 */ }

      // 请求发出前再次确认组件未卸载
      if (!mountedRef.current || controller.signal.aborted) return

      const token = getToken()
      const headers = { ...options.headers }
      if (token) {
        headers['Authorization'] = `Bearer ${token}`
      }

      return fetch(url, { ...options, headers, signal: controller.signal })
        .then(r => {
          if (r.status === 401) {
            try { localStorage.removeItem('_auth_token') } catch (e) { /* */ }
          }
          if (!r.ok) throw new Error(`HTTP ${r.status}`)
          return r.json()
        })
        .then(d => {
          if (mountedRef.current && !controller.signal.aborted) {
            setData(d)
            setLoading(false)
          }
        })
        .catch(err => {
          if (mountedRef.current && !controller.signal.aborted && err.name !== 'AbortError') {
            setError('数据加载失败，点击重试')
            setLoading(false)
          }
        })
    }

    doFetch()

    return () => controller.abort()
  }, [url, JSON.stringify(options)])

  useEffect(() => {
    mountedRef.current = true
    const cleanup = fetchData()
    return () => {
      mountedRef.current = false
      if (abortRef.current) abortRef.current.abort()
      if (typeof cleanup === 'function') cleanup()
    }
  }, [fetchData])

  return { data, loading, error, refetch: fetchData }
}
