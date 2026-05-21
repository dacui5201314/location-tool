/** 脱敏 openid */
export function maskOpenid (openid) {
  if (!openid || openid.length < 4) return '***'
  return openid.slice(0, 1) + '****' + openid.slice(-3)
}

/** 评分颜色 */
export function scoreColor (s) {
  if (s >= 60) return '#10b981'
  if (s >= 40) return '#f59e0b'
  return '#ef4444'
}

/** 格式化时间 */
export function formatTime (iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

export default { maskOpenid, scoreColor, formatTime }
