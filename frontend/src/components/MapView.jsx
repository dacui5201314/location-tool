import { useRef, useEffect, useCallback } from 'react'

// ★ 全局 Map 实例缓存 — 避开路由切换时的 WebGL 销毁/重建
let _cachedMap = null        // AMap.Map 实例
let _cachedMarker = null     // AMap.Marker 实例
let _cachedContainer = null  // 原生 DOM 容器节点
let _cachedCenter = null     // {lng, lat}
let _clickBound = false      // ★ 防 click handler 重复绑定叠加

export default function MapView({ position, onPositionChange, mapLoaded, mapError, selectedAddress }) {
  const mountRef = useRef(null)    // React ref 挂载点
  const mapRef = useRef(null)
  const markerRef = useRef(null)
  const geoRef = useRef(null)      // ★ 始终保持最新 geocodeAndNotify 引用
  const onPosRef = useRef(null)    // ★ 始终保持最新 onPositionChange 引用
  // ★ 每次 render 更新 latestProps，地图 click 回调通过它访问最新引用，解陈旧闭包
  const latestProps = useRef({ onPositionChange, geoRef, markerRef, mapRef })
  latestProps.current = { onPositionChange, geoRef, markerRef, mapRef }

  // 逆地理编码 + 通知父组件
  const geocodeAndNotify = useCallback((lng, lat) => {
    const cb = onPosRef.current
    const newPos = { lng, lat }
    if (window.AMap?.Geocoder) {
      try {
        new window.AMap.Geocoder().getAddress([lng, lat], (status, result) => {
          if (status === 'complete' && result?.info === 'OK') {
            newPos.address = result.regeocode.formattedAddress
          }
          cb?.(newPos)
        })
      } catch { cb?.(newPos) }
    } else {
      cb?.(newPos)
    }
  }, [])
  geoRef.current = geocodeAndNotify

  // 绑定地图点击事件（全局仅绑定一次，路由切回不重复叠加）
  const bindClickHandler = useCallback(() => {
    if (!mapRef.current || !window.AMap || _clickBound) return
    const map = mapRef.current
    _clickBound = true
    map.on('click', (e) => {
      const lng = e.lnglat.getLng()
      const lat = e.lnglat.getLat()
      // ★ 通过 latestProps.current 访问最新 ref，解除首次挂载时的陈旧闭包
      const props = latestProps.current
      if (props.markerRef.current) {
        props.markerRef.current.setPosition([lng, lat])
      } else {
        const m = new window.AMap.Marker({
          position: [lng, lat], draggable: true,         })
        map.add(m)
        props.markerRef.current = m
        _cachedMarker = m
        m.on('dragend', () => {
          const pos = m.getPosition()
          props.geoRef.current?.(pos.lng, pos.lat)
        })
      }
      map.setCenter([lng, lat], true)
      _cachedCenter = { lng, lat }
      props.onPositionChange?.({ lng, lat })
    })
  }, [])

  // 初始化地图（全局缓存复用）
  useEffect(() => {
    if (!mapLoaded || !mountRef.current) return

    // ★ 缓存命中：复用已存在的 Map 实例和 DOM 节点
    if (_cachedMap && _cachedContainer) {
      mountRef.current.appendChild(_cachedContainer)
      mapRef.current = _cachedMap
      markerRef.current = _cachedMarker
      bindClickHandler() // 重新绑定最新回调的 click 事件
      return () => {
        if (_cachedContainer && mountRef.current) {
          try { mountRef.current.removeChild(_cachedContainer) } catch {}
        }
      }
    }

    // 首次创建
    const timer = setTimeout(() => {
      if (!mountRef.current || !window.AMap) return
      const container = document.createElement('div')
      container.style.width = '100%'
      container.style.height = '100%'
      container.style.minHeight = '220px'
      mountRef.current.appendChild(container)

      const center = position
        ? [position.lng, position.lat]
        : [116.397428, 39.90923]
      const map = new window.AMap.Map(container, {
        zoom: 15, center, resizeEnable: true,
      })
      mapRef.current = map
      _cachedMap = map
      _cachedContainer = container
      _cachedCenter = { lng: center[0], lat: center[1] }
      bindClickHandler()
    }, 100)

    return () => {
      clearTimeout(timer)
      if (_cachedContainer && mountRef.current) {
        try { mountRef.current.removeChild(_cachedContainer) } catch {}
      }
    }
  }, [mapLoaded, bindClickHandler])

  // 外部位置变更 → 更新标记
  useEffect(() => {
    if (!mapRef.current || !position || !window.AMap) return
    const { lng, lat } = position
    if (_cachedCenter && _cachedCenter.lng === lng && _cachedCenter.lat === lat) return
    // ★ 清理旧 marker 的 dragend 事件监听，防止泄漏
    if (markerRef.current) {
      try { markerRef.current.off('dragend') } catch {}
      try { markerRef.current.setMap(null) } catch {}
    }
    const m = new window.AMap.Marker({
      position: [lng, lat],
      draggable: true,     })
    mapRef.current.add(m)
    mapRef.current.setZoomAndCenter(16, [lng, lat], true)
    markerRef.current = m
    _cachedMarker = m
    _cachedCenter = { lng, lat }
    m.on('dragend', () => {
      const pos = m.getPosition()
      geoRef.current?.(pos.lng, pos.lat)
    })
  }, [position?.lng, position?.lat])

  if (!mapLoaded) {
    if (mapError) {
      return (
        <div className="flex h-full min-h-[220px] w-full flex-col items-center justify-center gap-2 rounded-lg bg-red-50 border border-red-100">
          <span className="text-2xl">🗺️</span>
          <p className="text-sm font-semibold text-red-600">地图服务暂不可用</p>
          <p className="text-xs text-red-400 max-w-[280px] text-center">{String(mapError?.message || mapError)}</p>
        </div>
      )
    }
    return (
      <div className="flex h-full min-h-[220px] w-full items-center justify-center rounded-lg bg-slate-100">
        <p className="text-sm text-slate-400">地图加载中...</p>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      <div ref={mountRef} className="h-full min-h-[220px] w-full" style={{ borderRadius: 8, overflow: 'hidden', willChange: 'transform' }} />
      {selectedAddress && (
        <div className="selected-location-card pointer-events-none absolute left-4 right-4 z-10 rounded-lg bg-white/95 px-4 py-3 shadow-lg backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-blue-50 text-lg text-blue-600">📍</span>
            <div className="min-w-0">
              <div className="text-sm font-bold text-slate-900">已选择位置</div>
              <div className="selected-location-address mt-0.5 text-xs text-slate-500">{selectedAddress}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
