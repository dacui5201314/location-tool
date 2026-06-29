import config from './config'

/**
 * 分享图片 URL 解析 — 从 home/index.vue 和 report-detail/index.vue 提取
 */
export function resolveShareImage (url) {
  if (!url) return ''
  if (url.startsWith('/assets/')) return config.API_BASE_URL + url
  return url
}

/**
 * 下载分享图到本地临时路径
 */
export function downloadShareImage (url, onSuccess) {
  uni.downloadFile({
    url,
    success: (res) => {
      if (res.statusCode === 200 && res.tempFilePath && onSuccess) {
        onSuccess(res.tempFilePath)
      }
    },
    fail: (err) => { console.warn('[share] downloadFile failed:', (err && err.errMsg) || err) }
  })
}
