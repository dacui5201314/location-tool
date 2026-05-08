import { useRef, useEffect, useCallback } from 'react'

export default function MapView({ position, onPositionChange, mapLoaded, mapError, selectedAddress }) {
  const containerRef = useRef(null)
  const mapRef = useRef(null)
  const markerRef = useRef(null)

  // 逆地理编码 + 通知父组件
  const geocodeAndNotify = useCallback((lng, lat) => {
    const newPos = { lng, lat }
    if (window.AMap?.Geocoder) {
      try {
        new window.AMap.Geocoder().getAddress([lng, lat], (status, result) => {
          if (status === 'complete' && result?.info === 'OK') {
            newPos.address = result.regeocode.formattedAddress
          }
          onPositionChange?.(newPos)
        })
      } catch { onPositionChange?.(newPos) }
    } else {
      onPositionChange?.(newPos)
    }
  }, [onPositionChange])

  // 初始化地图 + 绑定事件
  useEffect(() => {
    if (!mapLoaded || !containerRef.current) return

    const timer = setTimeout(() => {
      if (!containerRef.current || !window.AMap) return
      const map = new window.AMap.Map(containerRef.current, {
        zoom: 15,
        center: position ? [position.lng, position.lat] : [116.397428, 39.90923],
        resizeEnable: true,
      })
      mapRef.current = map

      // 地图点击 → 移动标记 + 逆地理编码
      map.on('click', (e) => {
        const lng = e.lnglat.getLng()
        const lat = e.lnglat.getLat()
        if (markerRef.current) {
          markerRef.current.setPosition([lng, lat])
        } else {
          const m = new window.AMap.Marker({
            position: [lng, lat], draggable: true, animation: 'AMAP_ANIMATION_DROP',
          })
          map.add(m)
          markerRef.current = m
          // 拖拽结束 → 逆地理编码
          m.on('dragend', () => {
            const pos = m.getPosition()
            geocodeAndNotify(pos.lng, pos.lat)
          })
        }
        map.setCenter([lng, lat], true)
        geocodeAndNotify(lng, lat)
      })
    }, 100)

    return () => {
      clearTimeout(timer)
      if (markerRef.current) {
        try { markerRef.current.setMap(null) } catch {}
        markerRef.current = null
      }
      if (mapRef.current) {
        try { mapRef.current.clearMap() } catch {}
        try { mapRef.current.destroy() } catch {}
        mapRef.current = null
      }
    }
  }, [mapLoaded])

  // 外部位置变更 → 更新标记
  useEffect(() => {
    if (!mapRef.current || !position || !window.AMap) return
    if (markerRef.current) {
      try { markerRef.current.setMap(null) } catch {}
    }
    const m = new window.AMap.Marker({
      position: [position.lng, position.lat],
      draggable: true, animation: 'AMAP_ANIMATION_DROP',
    })
    mapRef.current.add(m)
    mapRef.current.setZoomAndCenter(16, [position.lng, position.lat], true)
    markerRef.current = m
    m.on('dragend', () => {
      const pos = m.getPosition()
      geocodeAndNotify(pos.lng, pos.lat)
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
    <div className="relative h-full w-full overflow-hidden rounded-lg">
      <div ref={containerRef} className="h-full min-h-[220px] w-full" />
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
