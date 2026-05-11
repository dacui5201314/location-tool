import { useRef, useEffect, useState } from 'react'

// ★ 全局 Geolocation 缓存（页面级，路由切换不丢失）
let _cachedGeo = null  // {lng, lat, addrText}

export default function AddressInput({ onSelect, disabled, mapLoaded, externalAddress, onToast, city }) {
  const inputRef = useRef(null)
  const [busy, setBusy] = useState(false)
  const [hasText, setHasText] = useState(false)
  const [locateDone, setLocateDone] = useState(!!_cachedGeo)  // ★ 全局缓存命中则直接标记为已定位
  const busyRef = useRef(false)
  const searchIdRef = useRef(0)
  const programmaticInput = useRef(false)
  const locateTriggered = useRef(false)  // ★ 区分外部地址变更是定位触发还是地图点击

  // AutoComplete 下拉提示
  useEffect(() => {
    if (!mapLoaded || !inputRef.current) return
    if (!window.AMap?.AutoComplete) return
    const auto = new window.AMap.AutoComplete({ input: inputRef.current })
    const onSelectHandler = (e) => {
      if (!e.poi || programmaticInput.current) return
      if (e.poi.location) {
        const address = (e.poi.district || '') + (e.poi.address || '')
        setLocateDone(false)  // 用户选了新地址，不再是定位状态
        onSelect({ name: e.poi.name, address, location: { lng: e.poi.location.lng, lat: e.poi.location.lat } })
        setHasText(true)
        return
      }
      // 关键词补全 → PlaceSearch 兜底
      if (window.AMap?.PlaceSearch && e.poi.name && !busyRef.current) {
        busyRef.current = true
        const ps = new window.AMap.PlaceSearch({ pageSize: 1, pageIndex: 1, ...(city ? { city, citylimit: true } : {}) })
        ps.search(e.poi.name, (status, result) => {
          busyRef.current = false
          if (status === 'complete' && result?.info === 'OK') {
            const pois = result.poiList?.pois || []
            if (pois.length > 0) {
              const p = pois[0]
              const address = (p.district || '') + (p.address || '')
              setLocateDone(false)
              onSelect({ name: p.name, address, location: { lng: p.location.lng, lat: p.location.lat } })
              programmaticInput.current = true
              if (inputRef.current) inputRef.current.value = p.name
              setTimeout(() => { programmaticInput.current = false }, 200)
              setHasText(true)
            }
          }
        })
      }
    }
    const listener = window.AMap.Event.addListener(auto, 'select', onSelectHandler)
    return () => {
      try { window.AMap?.Event?.removeListener?.(listener) } catch {}
    }
  }, [mapLoaded, onSelect, city])

  // 外部地址同步（仅写入输入框，不修改 hasText——保留定位按钮可见）
  useEffect(() => {
    if (programmaticInput.current) return
    if (externalAddress && inputRef.current) {
      inputRef.current.value = externalAddress
      // 地图点击/拖拽 → 地址变了但不是定位触发的 → 重置定位状态
      if (!locateTriggered.current) {
        setLocateDone(false)
      }
      locateTriggered.current = false
    }
  }, [externalAddress])

  // ── 定位（独立逻辑，与搜索完全分离）──
  const handleLocate = async () => {
    if (busy || disabled || busyRef.current) return
    // ★ 全局缓存命中 → 直接复用
    if (_cachedGeo) {
      locateTriggered.current = true
      onSelect({ name: _cachedGeo.addrText, address: _cachedGeo.addrText, location: { lng: _cachedGeo.lng, lat: _cachedGeo.lat } })
      onToast?.('已定位')
      return
    }
    if (!window.AMap?.Geolocation) { onToast?.('定位插件未加载'); return }
    setBusy(true)
    busyRef.current = true
    onToast?.('正在获取精确位置...')
    const geo = new window.AMap.Geolocation({ enableHighAccuracy: true, timeout: 8000, maximumAge: 0, panToLocation: false, zoomToAccuracy: false })
    geo.getCurrentPosition((status, result) => {
      setBusy(false)
      busyRef.current = false
      if (status !== 'complete' || !result?.position) {
        onToast?.('定位失败，请直接输入目标地址进行搜索')
        return
      }
      const { lng, lat } = result.position
      const apply = (addrText) => {
        _cachedGeo = { lng, lat, addrText }  // ★ 全局缓存
        setLocateDone(true)
        locateTriggered.current = true  // ★ 标记：这次地址变更是定位触发的
        onSelect({ name: addrText, address: addrText, location: { lng, lat } })
      }
      if (window.AMap?.Geocoder) {
        new window.AMap.Geocoder().getAddress([lng, lat], (gcStatus, gcResult) => {
          if (gcStatus === 'complete' && gcResult?.info === 'OK') {
            apply(gcResult.regeocode.formattedAddress)
          } else {
            apply(result.formattedAddress || `${lng.toFixed(4)}, ${lat.toFixed(4)}`)
          }
        })
      } else {
        apply(result.formattedAddress || `${lng.toFixed(4)}, ${lat.toFixed(4)}`)
      }
    })
  }

  // ── 搜索（独立逻辑）──
  const handleSearch = async () => {
    if (busy || disabled || busyRef.current) return
    const keyword = inputRef.current?.value?.trim()
    if (!keyword) { handleLocate(); return }
    if (!window.AMap?.PlaceSearch) { onToast?.('搜索插件未加载'); return }
    setBusy(true)
    busyRef.current = true
    const thisSearchId = ++searchIdRef.current
    try {
      const result = await new Promise((resolve, reject) => {
        const ps = new window.AMap.PlaceSearch({ pageSize: 1, pageIndex: 1, ...(city ? { city, citylimit: true } : {}) })
        ps.search(keyword, (status, res) => {
          if (thisSearchId !== searchIdRef.current) return
          if (status === 'complete' && res?.info === 'OK' && res.poiList?.pois?.length > 0) {
            const p = res.poiList.pois[0]
            resolve({ name: p.name, address: (p.district || '') + (p.address || ''), location: { lng: p.location.lng, lat: p.location.lat } })
          } else { reject(new Error('未搜索到相关地址')) }
        })
      })
      if (thisSearchId !== searchIdRef.current) return
      setLocateDone(false)
      programmaticInput.current = true
      if (inputRef.current) inputRef.current.value = result.name
      setTimeout(() => { programmaticInput.current = false }, 200)
      onSelect(result)
    } catch (err) { onToast?.(err.message || '搜索失败') }
    finally { setBusy(false); busyRef.current = false }
  }

  return (
    <div className="w-full">
      <div className="flex gap-2">
        <input ref={inputRef} type="text"
          placeholder={mapLoaded ? "输入地址搜索，或点击定位" : "地图服务加载中..."}
          disabled={disabled || busy || !mapLoaded} autoComplete="off"
          className="text-input min-w-0 flex-1 px-3.5 py-3"
          onChange={(e) => setHasText(!!e.target.value.trim())} />
        {hasText ? (
          <button type="button" onClick={handleSearch} disabled={disabled || busy}
            className="icon-button px-3" style={{ minWidth: 46, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}>
            {busy ? (
              <span className="inline-block h-5 w-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            )}
            <span className="address-action-label">搜索</span>
          </button>
        ) : (
          <button type="button" onClick={handleLocate} disabled={disabled || busy || locateDone}
            title={locateDone ? '已定位，输入地址可搜索' : '获取当前位置'}
            className="icon-button px-3" style={{ minWidth: 46, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'colors 0.3s' }}>
            {busy ? (
              <span className="inline-block h-5 w-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
            ) : locateDone ? (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><polyline points="6,12 10,16 18,8" /></svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="3" />
                <line x1="12" y1="2" x2="12" y2="6" /><line x1="12" y1="18" x2="12" y2="22" />
                <line x1="2" y1="12" x2="6" y2="12" /><line x1="18" y1="12" x2="22" y2="12" />
              </svg>
            )}
            <span className="address-action-label">{locateDone ? '已定位' : '定位'}</span>
          </button>
        )}
      </div>
    </div>
  )
}
