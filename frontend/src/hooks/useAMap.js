import { useEffect, useRef, useCallback, useState } from 'react'
import { AMAP_KEY, AMAP_VERSION, AMAP_SECURITY_CODE } from '../utils/constants'

// JS API 2.0 必须在加载脚本前配置安全密钥
if (AMAP_SECURITY_CODE) {
  window._AMapSecurityConfig = {
    securityJsCode: AMAP_SECURITY_CODE,
  }
}

let loadPromise = null

function loadAMap() {
  if (window.AMap) return Promise.resolve(window.AMap)
  if (loadPromise) return loadPromise

  // Key 未配置时直接拒绝，不发起无效请求
  if (!AMAP_KEY) {
    return Promise.reject(new Error('高德地图 Key 未配置，请在 frontend/.env.local 中设置 VITE_AMAP_KEY'))
  }

  const plugin = 'AMap.AutoComplete,AMap.Geocoder,AMap.Geolocation,AMap.PlaceSearch'
  const url = `https://webapi.amap.com/maps?v=${AMAP_VERSION}&key=${AMAP_KEY}&plugin=${plugin}`

  loadPromise = new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = url
    script.onload = () => {
      if (window.AMap) {
        resolve(window.AMap)
      } else {
        loadPromise = null
        reject(new Error('地图 SDK 加载异常，请刷新页面重试'))
      }
    }
    script.onerror = () => {
      loadPromise = null
      reject(new Error('地图服务加载失败，请检查网络连接'))
    }
    document.head.appendChild(script)
  })
  return loadPromise
}

export default function useAMap() {
  const [AMap, setAMap] = useState(null)
  const [loaded, setLoaded] = useState(false)
  const [error, setError] = useState(null)
  const autoCompleteRef = useRef(null)

  useEffect(() => {
    loadAMap()
      .then((amap) => {
        setAMap(amap)
        setLoaded(true)
      })
      .catch(setError)
  }, [])

  const createMap = useCallback((container, center = [116.397428, 39.90923]) => {
    if (!window.AMap) return null
    const map = new window.AMap.Map(container, {
      zoom: 15,
      center,
      resizeEnable: true,
    })
    return map
  }, [])

  const createAutoComplete = useCallback((inputEl, cb) => {
    if (!window.AMap) return null
    const auto = new window.AMap.AutoComplete({
      input: inputEl,
    })
    window.AMap.Event.addListener(auto, 'select', (e) => {
      if (e.poi && e.poi.location) {
        cb({
          name: e.poi.name,
          address: e.poi.district + e.poi.address,
          location: {
            lng: e.poi.location.lng,
            lat: e.poi.location.lat,
          },
        })
      }
    })
    autoCompleteRef.current = auto
    return auto
  }, [])

  const geocode = useCallback(async (address) => {
    if (!window.AMap) return null
    return new Promise((resolve, reject) => {
      const geocoder = new window.AMap.Geocoder()
      geocoder.getLocation(address, (status, result) => {
        if (status === 'complete' && result.info === 'OK') {
          const { lng, lat } = result.geocodes[0].location
          resolve({
            address: result.geocodes[0].formattedAddress,
            location: { lng, lat },
          })
        } else {
          reject(new Error('地址解析失败'))
        }
      })
    })
  }, [])

  const addMarker = useCallback((map, position, draggable = true) => {
    if (!window.AMap || !map) return null
    const marker = new window.AMap.Marker({
      position: [position.lng, position.lat],
      draggable,
      animation: 'AMAP_ANIMATION_DROP',
    })
    map.add(marker)
    map.setCenter([position.lng, position.lat], true)
    return marker
  }, [])

  const locateMe = useCallback(() => {
    return new Promise((resolve, reject) => {
      // Use browser Geolocation API for accuracy
      if (!navigator.geolocation) {
        reject(new Error('浏览器不支持定位功能'))
        return
      }

      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { longitude: lng, latitude: lat } = position.coords
          // Reverse geocode to get address
          if (window.AMap) {
            const geocoder = new window.AMap.Geocoder()
            geocoder.getAddress([lng, lat], (status, result) => {
              if (status === 'complete' && result.info === 'OK') {
                const addr = result.regeocode.formattedAddress
                resolve({
                  name: addr,
                  address: addr,
                  location: { lng, lat },
                })
              } else {
                // Geocoding failed, but we still have coordinates
                resolve({
                  name: `${lng.toFixed(4)}, ${lat.toFixed(4)}`,
                  address: `${lng.toFixed(4)}, ${lat.toFixed(4)}`,
                  location: { lng, lat },
                })
              }
            })
          } else {
            resolve({
              name: `${lng.toFixed(4)}, ${lat.toFixed(4)}`,
              address: `${lng.toFixed(4)}, ${lat.toFixed(4)}`,
              location: { lng, lat },
            })
          }
        },
        (err) => {
          let msg = '定位失败'
          switch (err.code) {
            case err.PERMISSION_DENIED: msg = '定位权限被拒绝，请在浏览器设置中允许定位'; break
            case err.POSITION_UNAVAILABLE: msg = '无法获取位置信息'; break
            case err.TIMEOUT: msg = '获取位置超时，请重试'; break
          }
          reject(new Error(msg))
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
      )
    })
  }, [])

  return { AMap, loaded, error, createMap, createAutoComplete, geocode, addMarker, locateMe }
}
