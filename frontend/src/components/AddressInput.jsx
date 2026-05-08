import { useRef, useEffect, useState } from 'react'

export default function AddressInput({ onSelect, disabled, mapLoaded, externalAddress, onToast, city }) {
  const inputRef = useRef(null)
  const autoRef = useRef(null)
  const [busy, setBusy] = useState(false)
  const [hasText, setHasText] = useState(false)
  const busyRef = useRef(false)  // ★ 避免 AutoComplete 回调中的闭包过期
  const userInteracted = useRef(false)  // ★ 用户手动操作后，禁止定位结果覆盖
  const searchIdRef = useRef(0)  // ★ 防并发回调乱序：只应用最新一次搜索的结果

  // AutoComplete 下拉提示
  useEffect(() => {
    if (!mapLoaded || !inputRef.current) return
    if (!window.AMap?.AutoComplete) return
    const auto = new window.AMap.AutoComplete({ input: inputRef.current })
    const onSelectHandler = (e) => {
      if (!e.poi) return
      if (e.poi.location) {
        const address = (e.poi.district || '') + (e.poi.address || '')
        userInteracted.current = true
        onSelect({ name: e.poi.name, address, location: { lng: e.poi.location.lng, lat: e.poi.location.lat } })
        setHasText(true)
        return
      }
      // 关键词补全 → PlaceSearch 兜底（加锁 + 城市上下文）
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
              userInteracted.current = true
              onSelect({ name: p.name, address, location: { lng: p.location.lng, lat: p.location.lat } })
              if (inputRef.current) inputRef.current.value = p.name
              setHasText(true)
            }
          }
        })
      }
    }
    const listener = window.AMap.Event.addListener(auto, 'select', onSelectHandler)
    autoRef.current = auto
    return () => {
      try { window.AMap?.Event?.removeListener?.(listener) } catch {}
      autoRef.current = null
    }
  }, [mapLoaded, onSelect])

  // 外部地址同步
  useEffect(() => {
    if (externalAddress && inputRef.current) {
      inputRef.current.value = externalAddress
      setHasText(true)
    }
  }, [externalAddress])

  const handleClick = async () => {
    if (busy || disabled || busyRef.current) return
    const keyword = inputRef.current?.value?.trim()

    // 情景 A：有文本 → PlaceSearch
    if (keyword) {
      setBusy(true)
      busyRef.current = true
      const thisSearchId = ++searchIdRef.current  // ★ 递增 ID，回调只认最新
      try {
        const result = await new Promise((resolve, reject) => {
          if (!window.AMap?.PlaceSearch) return reject(new Error('搜索插件未加载'))
          const ps = new window.AMap.PlaceSearch({ pageSize: 1, pageIndex: 1, ...(city ? { city, citylimit: true } : {}) })
          ps.search(keyword, (status, res) => {
            // ★ 忽略旧搜索的回调（并发乱序防护）
            if (thisSearchId !== searchIdRef.current) return
            if (status === 'complete' && res?.info === 'OK' && res.poiList?.pois?.length > 0) {
              const p = res.poiList.pois[0]
              resolve({ name: p.name, address: (p.district || '') + (p.address || ''), location: { lng: p.location.lng, lat: p.location.lat } })
            } else { reject(new Error('未搜索到相关地址')) }
          })
        })
        if (thisSearchId !== searchIdRef.current) return  // ★ 后续搜索已发起，丢弃此结果
        if (inputRef.current) inputRef.current.value = result.name
        userInteracted.current = true  // ★ 标记用户已手动搜索
        onSelect(result)
      } catch (err) { onToast?.(err.message || '搜索失败') }
      finally { setBusy(false); busyRef.current = false }
      return
    }

    // 情景 B：空文本 → Geolocation + Geocoder 逆地理编码
    if (!window.AMap?.Geolocation) { onToast?.('定位插件未加载'); return }
    setBusy(true)
    busyRef.current = true
    onToast?.('正在获取精确位置...')
    const geo = new window.AMap.Geolocation({ enableHighAccuracy: true, timeout: 8000, maximumAge: 0, panToLocation: false, zoomToAccuracy: false })
    geo.getCurrentPosition((status, result) => {
      // ★ 用户已手动操作 → 忽略迟到的定位回调，防止地图幽灵跳转
      if (userInteracted.current) { setBusy(false); busyRef.current = false; return }
      if (status !== 'complete' || !result?.position) {
        setBusy(false); busyRef.current = false
        onToast?.('定位失败，请直接输入目标地址进行搜索')
        return
      }
      const { lng, lat } = result.position
      const accuracy = result.accuracy || 9999

      // 逆地理编码：坐标 → 结构化地址
      const applyAddress = (addrText) => {
        onSelect({ name: addrText, address: addrText, location: { lng, lat } })
        if (inputRef.current) {
          inputRef.current.value = addrText
          setHasText(true)
        }
      }

      if (window.AMap?.Geocoder) {
        const geocoder = new window.AMap.Geocoder()
        geocoder.getAddress([lng, lat], (gcStatus, gcResult) => {
          setBusy(false); busyRef.current = false
          if (gcStatus === 'complete' && gcResult?.info === 'OK') {
            const addr = gcResult.regeocode.formattedAddress
            applyAddress(addr)
          } else {
            // Geocoder 失败，用 Geolocation 自带的地址兜底
            applyAddress(result.formattedAddress || `${lng.toFixed(4)}, ${lat.toFixed(4)}`)
          }
          // 精度 Toast
          if (accuracy <= 50) {
            onToast?.('精准定位成功')
          } else if (accuracy < 2000) {
            onToast?.('已获取大致位置。受设备限制可能存在偏差，请手动拖动大头针进行精准微调')
          } else {
            onToast?.('定位精度较低，建议手动输入地址')
          }
        })
      } else {
        // 无 Geocoder 插件 → 用 Geolocation 自带地址
        setBusy(false)
        applyAddress(result.formattedAddress || `${lng.toFixed(4)}, ${lat.toFixed(4)}`)
        if (accuracy <= 50) onToast?.('精准定位成功')
        else onToast?.('已获取大致位置。受设备限制可能存在偏差，请手动拖动大头针进行精准微调')
      }
    })
  }

  return (
    <div className="w-full">
      <div className="flex gap-2">
        <input ref={inputRef} type="text"
          placeholder={mapLoaded ? "输入地址，或点击定位" : "地图服务加载中，请稍后..."}
          disabled={disabled || busy || !mapLoaded} autoComplete="off"
          className="text-input min-w-0 flex-1 px-3.5 py-3"
          onChange={(e) => setHasText(!!e.target.value.trim())} />
        <button type="button" onClick={handleClick} disabled={disabled || busy}
          title={hasText ? '搜索地址' : '获取当前位置'}
          className="icon-button px-3"
          style={{ minWidth: 46, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', transition: 'all 0.3s ease' }}>
          {busy ? (
            <span className="inline-block h-5 w-5 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
          ) : hasText ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="3" />
              <line x1="12" y1="2" x2="12" y2="6" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="2" y1="12" x2="6" y2="12" />
              <line x1="18" y1="12" x2="22" y2="12" />
            </svg>
          )}
          {!busy && <span className="address-action-label">{hasText ? '搜索' : '定位'}</span>}
        </button>
      </div>
    </div>
  )
}
