/**
 * 递归脱敏工具 — 防止报告 JSON 中含供应商名称、过深嵌套、循环引用
 * 从 pages/report-detail/index.vue 提取为独立模块
 */

const MAX_DEPTH = 12

const DEFAULT_MASK_TEXT = (text) => {
  if (typeof text !== 'string') return text
  return text
    .replace(/高德地图POI采集/g, '地图数据采集')
    .replace(/高德地图\s*POI/g, '地图数据')
    .replace(/高德地图/g, '地图数据')
    .replace(/高德/g, '地图服务')
    .replace(/POI数据采集/g, '周边数据采集')
    .replace(/POI/g, '点位数据')
}

export function createMaskDeep (maskText) {
  const mask = maskText || DEFAULT_MASK_TEXT

  function maskDeep (value, depth, seen) {
    if (depth === undefined) depth = 0
    if (depth > MAX_DEPTH) return '[深度超限]'
    if (typeof value === 'string') return mask(value)
    if (Array.isArray(value)) return value.map(v => maskDeep(v, depth + 1, seen))
    if (value && typeof value === 'object') {
      if (!seen) seen = new WeakSet()
      if (seen.has(value)) return '[循环引用]'
      seen.add(value)
      const out = {}
      Object.keys(value).forEach(k => { out[k] = maskDeep(value[k], depth + 1, seen) })
      return out
    }
    return value
  }

  return maskDeep
}

export { DEFAULT_MASK_TEXT, MAX_DEPTH }
