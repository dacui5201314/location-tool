/**
 * 设备指纹 — Canvas Fingerprinting + Browser Attributes + localStorage 兜底
 *
 * 三层策略（按优先级）：
 *   1. Canvas 指纹：渲染隐藏画布，对像素数据取 hash。
 *      同一设备/OS/浏览器组合产出稳定指纹，清除 localStorage 无法绕过。
 *   2. Browser 属性：User-Agent + 屏幕分辨率 + 平台 + 语言 + 时区。
 *   3. localStorage UUID 兜底：Canvas 不可用时回退。
 *
 * 最终 device_id = hash(CanvasHash + BrowserHash)，同时持久化到 localStorage
 * 作为匹配索引键（后端通过此键查找已注册用户）。
 */

const DEVICE_KEY = '_device_fp'

/**
 * djb2 字符串哈希（32-bit，同步，跨浏览器稳定）
 */
function djb2(str) {
  let hash = 5381
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) + hash + str.charCodeAt(i)) | 0
  }
  return (hash >>> 0).toString(36)
}

/**
 * Canvas 指纹：渲染文本+几何图形，导出 dataURL 后取 hash。
 * 同一 OS/浏览器/GPU 驱动组合产出稳定结果，不同环境差异显著。
 */
function canvasFingerprint() {
  try {
    const canvas = document.createElement('canvas')
    canvas.width = 280
    canvas.height = 60
    canvas.style.display = 'none'
    const ctx = canvas.getContext('2d')

    // 背景色块
    ctx.fillStyle = '#f7a800'
    ctx.fillRect(0, 0, 120, 22)

    // 第一行文字
    ctx.textBaseline = 'top'
    ctx.font = '14px "Arial", sans-serif'
    ctx.fillStyle = '#1a3a5c'
    ctx.fillText('Device Fingerprint', 4, 3)

    // 第二行文字（含全字母 pangram，覆盖字体渲染差异）
    ctx.font = '11px "Courier New", monospace'
    ctx.fillStyle = '#333'
    ctx.fillText('Cwm fjord bank glyphs vext quiz', 4, 28)

    // 小圆点几何
    ctx.beginPath()
    ctx.arc(250, 40, 8, 0, Math.PI * 2)
    ctx.fillStyle = '#0a8'
    ctx.fill()

    // 导出并哈希 — PNG 编码差异即设备指纹
    const dataUrl = canvas.toDataURL('image/png')
    return djb2(dataUrl)
  } catch (e) {
    return null
  }
}

/**
 * 浏览器属性指纹：收集稳定但难伪造的浏览器环境特征
 */
function browserFingerprint() {
  try {
    const attrs = [
      navigator.userAgent || '',
      navigator.platform || '',
      navigator.language || '',
      screen.width || 0,
      screen.height || 0,
      screen.colorDepth || 0,
      new Intl.DateTimeFormat().resolvedOptions().timeZone || '',
      !!navigator.hardwareConcurrency ? navigator.hardwareConcurrency : 0,
    ]
    return djb2(attrs.join('|'))
  } catch (e) {
    return null
  }
}

/**
 * 生成复合设备指纹，持久化到 localStorage 作为匹配键
 */
function generateFingerprint() {
  const canvasHash = canvasFingerprint()
  const browserHash = browserFingerprint()

  // 组合指纹源
  const parts = []
  if (canvasHash) parts.push('c:' + canvasHash)
  if (browserHash) parts.push('b:' + browserHash)
  if (parts.length === 0) {
    // 终极兜底：纯随机 UUID（刷新即丢失匹配）
    const s4 = () => Math.floor((1 + Math.random()) * 0x10000).toString(16).substring(1)
    return `${s4()}${s4()}-${s4()}-${s4()}-${s4()}-${s4()}${s4()}${s4()}`
  }

  const raw = parts.join('_')
  const fp = djb2(raw)
  // 格式化为可读 UUID-like 字符串
  const padded = fp.padStart(12, '0')
  return `fp-${padded.slice(0, 4)}-${padded.slice(4, 8)}-${padded.slice(8, 12)}`
}

/**
 * 获取设备指纹。优先返回持久化值（确保同一设备跨会话匹配），
 * 不存在则生成新指纹并持久化。
 */
export function getDeviceId() {
  let id = null
  try {
    id = localStorage.getItem(DEVICE_KEY)
  } catch (e) {
    // localStorage 不可用（隐私模式等）
  }

  if (!id) {
    id = generateFingerprint()
    try {
      localStorage.setItem(DEVICE_KEY, id)
    } catch (e) {
      // 静默失败
    }
  }

  return id
}
