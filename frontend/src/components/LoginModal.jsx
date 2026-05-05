import { useState, useRef, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { setToken, setCurrentUser, getToken } from '../services/api'

const API_BASE = '/api'

export function hasPhoneBinding() {
  // 无法从 token 直接判断，通过 profile 接口检查；此函数仅做快速客户端预检
  return !!getToken()
}

export default function LoginModal({ open, onSuccess, onClose }) {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const phoneRef = useRef(null)

  useEffect(() => {
    if (open && phoneRef.current) phoneRef.current.focus()
    if (!open) { setError(''); setPhone(''); setPassword('') }
  }, [open])

  const handleSubmit = async (e) => {
    e?.preventDefault()
    setError('')

    const p = phone.trim()
    const pw = password.trim()
    if (!p || p.length < 11) { setError('请输入有效的手机号'); return }
    if (!pw || pw.length < 6) { setError('密码至少 6 位'); return }

    setLoading(true)
    try {
      const endpoint = mode === 'register' ? '/auth/register' : '/auth/login'
      const r = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: p, password: pw }),
      })
      const d = await r.json()
      if (!r.ok) throw new Error(d.detail || `${mode === 'register' ? '注册' : '登录'}失败`)
      setToken(d.token)
      setCurrentUser(d.user)
      onSuccess?.(d)
    } catch (err) {
      setError(err.message || '操作失败，请重试')
    } finally {
      setLoading(false)
    }
  }

  if (!open) return null

  return createPortal(
    <div className="fixed inset-0 z-[250] flex items-center justify-center bg-black/50 px-4"
      onClick={onClose}>
      <div className="w-full max-w-sm rounded-2xl bg-white p-6 shadow-2xl" onClick={e => e.stopPropagation()}>
        <div className="text-center mb-5">
          <div className="text-3xl font-black text-blue-600 mb-1">AI</div>
          <h2 className="text-base font-bold text-slate-900">
            {mode === 'register' ? '注册账号' : '登录账号'}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            {mode === 'register' ? '注册即送分析点数' : '登录以继续使用分析服务'}
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="space-y-3">
            <div>
              <label className="text-xs font-semibold text-slate-500">手机号</label>
              <input
                ref={phoneRef}
                type="tel"
                value={phone}
                onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
                placeholder="请输入手机号"
                maxLength={11}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:border-blue-400"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-500">密码</label>
              <input
                type="password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder={mode === 'register' ? '至少 6 位密码' : '请输入密码'}
                className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2.5 text-sm focus:outline-none focus:border-blue-400"
              />
            </div>
          </div>

          {error && (
            <div className="mt-3 rounded-lg bg-red-50 border border-red-100 px-3 py-2 text-xs text-red-600">{error}</div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 rounded-xl bg-blue-600 py-3 text-sm font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? '处理中...' : mode === 'register' ? '注册并领取奖励' : '登录'}
          </button>
        </form>

        <div className="mt-4 text-center">
          <button
            onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}
            className="text-xs text-blue-600 hover:text-blue-700 font-semibold"
          >
            {mode === 'login' ? '没有账号？立即注册' : '已有账号？去登录'}
          </button>
        </div>

        <button
          onClick={onClose}
          className="w-full mt-3 rounded-lg border border-slate-200 py-2 text-sm text-slate-500 hover:bg-slate-50"
        >
          暂不登录，先看看
        </button>
      </div>
    </div>,
    document.body
  )
}
