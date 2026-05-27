<template>
  <view class="home-page">
    <!-- 欢迎弹层 -->
    <view class="welcome-mask" v-if="welcomeOpen">
      <view class="welcome-modal">
        <view class="wm-icon">🎁</view>
        <view class="wm-title">欢迎使用址得选</view>
        <view class="wm-body">系统已赠送免费分析额度，请尽快使用</view>
        <button class="wm-btn" @tap="dismissWelcome">开始体验</button>
      </view>
    </view>

    <!-- 免费额度倒计时 -->
    <view class="free-banner" v-if="freePointBanner">
      <text>免费分析额度剩余 {{ freePointBanner }} · 请尽快使用</text>
    </view>

    <!-- 全局公告 -->
    <view class="ann-banner" v-if="announcement">
      <text>{{ announcement }}</text>
    </view>

    <!-- ── Hero（Web 对齐：logo lockup + hero copy）── -->
    <view class="hero">
      <view class="hero-top">
        <view class="hero-logo-box">
          <image class="hero-logo" src="/static/brand-logo.png" mode="aspectFit" />
        </view>
        <view class="hero-lockup">
          <text class="hero-brand">址得选</text>
          <text class="hero-slogan">AI 智能选址</text>
        </view>
      </view>
      <view class="hero-copy">
        <text class="hero-title">商铺选址<text class="hero-hl">先看数据分析</text></text>
        <text class="hero-desc">结合周边 POI、业态与经营信息，生成商业选址分析参考</text>
      </view>
      <view class="hero-tags">
        <text class="htag">全国城市适用</text>
        <text class="htag">POI 周边洞察</text>
        <text class="htag">实地复核建议</text>
      </view>
      <view class="hero-city" aria-hidden="true">
        <view class="hc-building hc-a" />
        <view class="hc-building hc-b" />
        <view class="hc-building hc-c" />
        <view class="hc-building hc-d" />
        <view class="hc-building hc-e" />
      </view>
      <view class="hero-visual" aria-hidden="true">
        <view class="hv-plate">
          <view class="hv-ring ring-a" />
          <view class="hv-ring ring-b" />
        </view>
        <view class="hv-orbit" />
        <view class="hv-pin">
          <view class="hv-pin-core" />
        </view>
      </view>
    </view>

    <!-- 搜索卡片：独立浮层，避免 hero/map 原生层级吞点击 -->
    <view class="search-section">
      <view class="search-card">
        <view class="sc-label-row">
          <text class="sc-label">门店位置</text>
          <text class="sc-state" :class="{ ready: addressText }">{{ addressText ? '已选择' : '先选位置' }}</text>
        </view>
        <view class="sc-input-row">
          <text class="sc-icon">定位</text>
          <input class="sc-field" :value="addressKeyword" placeholder="输入地址搜索门店位置" :disabled="analyzing" @input="onAddressInput" @confirm="onSearch" />
          <button class="sc-action" :disabled="analyzing" @tap="onLocate" v-if="!addressText">定位</button>
          <button class="sc-action fav" :disabled="favLoading || analyzing" @tap="toggleFav" v-if="addressText">
            {{ favLoading ? '·' : (favId ? '★' : '☆') }}
          </button>
        </view>
        <view class="sc-hint">
          <text>{{ addressText ? '可收藏地址，或继续在地图上微调选点' : '搜索地址、定位当前位置，或直接点击地图选点' }}</text>
        </view>
        <view class="suggest-list" v-if="suggestions.length">
          <view class="suggest-item" v-for="(s, i) in suggestions" :key="i" @tap="onSelectSuggestion(s)">
            <text class="sg-name">{{ s.name }}</text>
            <text class="sg-addr">{{ s.address }}</text>
          </view>
        </view>
        <view class="suggest-empty" v-if="suggestErr">{{ suggestErr }}</view>
      </view>
    </view>

    <!-- ── 地图区域 ── -->
    <view class="map-section">
      <view class="section-line">
        <view>
          <text class="section-title">当前位置</text>
          <text class="section-sub">可拖动或点击地图微调门店位置</text>
        </view>
        <text class="section-badge">{{ analyzing ? '分析中' : (addressText ? '可微调' : '待选择') }}</text>
      </view>
      <view class="addr-bar" v-if="addressText">
        <view class="ab-left">
          <text class="ab-pin">📍</text>
          <view class="ab-mid">
            <text class="ab-name">{{ addressText }}</text>
            <text class="ab-src" v-if="selectedLocationSource">来源：{{ srcLabel }}</text>
          </view>
        </view>
        <button class="ab-edit" @tap="clearAddress">重选</button>
      </view>
      <text class="field-err" v-if="errors.address">{{ errors.address }}</text>

      <view class="map-wrap">
        <map id="homeMap" class="map-view" :key="mapKey" :latitude="mapLat" :longitude="mapLng" :markers="mapMarkers" scale="15" :show-location="showUserLocation" :enable-scroll="!analyzing" :enable-zoom="!analyzing" :enable-rotate="false" @tap="onMapTap" @markertap="onMarkerTap" @regionchange="onMapRegionChange" @updated="onMapUpdated" />
        <view class="map-overlay" v-if="analyzing">
          <text class="mo-text">分析中，请稍后...</text>
        </view>
      </view>
      <view class="map-hint" :class="{ done: addressText, warn: !!mapNotice }">
        <text>{{ mapNotice || (addressText ? '已选位置 · 点击地图可重新选点' : '点击地图选点 · 或使用上方搜索框输入地址') }}</text>
      </view>
    </view>

    <!-- ── 业态 + 经营信息 ── -->
    <view class="biz-card">
      <view class="biz-head">
        <view>
          <text class="biz-title">选择业态</text>
          <text class="biz-sub">选择与业务最匹配的业态分类</text>
        </view>
        <text class="biz-link">全部业态 ›</text>
      </view>
      <text class="field-err" v-if="industryLoadErr">{{ industryLoadErr }}</text>
      <IndustryPicker :selected="industry" :disabled="analyzing" :industries="industryList" @change="onIndustryChange" />
      <text class="field-err" v-if="errors.industry">{{ errors.industry }}</text>

      <view class="biz-fields">
        <view class="field-head">
          <text class="field-head-title">经营画像</text>
          <text class="field-head-sub">品牌与面积越清晰，分析越稳定</text>
        </view>
        <view class="bf-item">
          <view class="label">品牌/特色 <text class="req">*</text></view>
          <input class="field" v-model="brandName" placeholder="品牌或主打特色" :disabled="analyzing" @input="onBrandInput" />
        </view>
        <view class="bf-item">
          <view class="label">门店面积 <text class="req">*</text></view>
          <input class="field" v-model="storeSize" type="number" placeholder="平方米" :disabled="analyzing" @input="onSizeInput" />
        </view>
      </view>
      <text class="field-err" v-if="errors.brand">{{ errors.brand }}</text>
      <text class="field-err" v-if="errors.size">{{ errors.size }}</text>
    </view>

    <!-- ── CTA ── -->
    <view class="cta-zone">
      <button class="cta-btn" :disabled="analyzing || !canAnalyze" @tap="onAnalyze">
        <text class="cta-main">{{ analyzing ? '分析中...' : '生成选址报告' }}</text>
        <text class="cta-sub">{{ ctaSubText }}</text>
      </button>
      <view class="analyze-steps" v-if="analyzing">
        <view class="as-step" v-for="(item, i) in analyzeStepItems" :key="i" :class="item.status">
          <text class="as-icon">{{ item.icon }}</text>
          <view class="as-body">
            <text class="as-label">{{ item.label }}</text>
            <text class="as-msg" v-if="item.msg">{{ item.msg }}</text>
          </view>
        </view>
      </view>
      <text class="field-err analyze-err" v-if="analyzeErr">{{ analyzeErr }}</text>
    </view>

    <!-- ── Feature tiles ── -->
    <view class="features">
      <view class="ft" v-for="t in trusts" :key="t.title">
        <text class="ft-mark">✓</text>
        <text class="ft-title">{{ t.title }}</text>
        <text class="ft-desc">{{ t.desc }}</text>
      </view>
    </view>

    <view class="footer">以上分析仅供参考，不构成投资建议。实际决策请结合实地考察与多方因素综合判断。</view>
  </view>
</template>

<script>
import IndustryPicker from '../../components/industry-picker/index.vue'
import api from '../../utils/api'

export default {
  components: { IndustryPicker },
  data () {
    return {
      addressKeyword: '',
      addressText: '',
      mapLat: 39.9087,
      mapLng: 116.3975,
      mapKey: 0,  // 递增以强制 map 重渲染 marker
      _regionTimer: null,  // 拖动结束防抖
      industry: '',
      brandName: '',
      storeSize: '',
      analyzing: false,
      analyzeSteps: [],
      analyzeErr: '',
      analyzeStatus: '',
      currentStep: 0,
      stepTimer: null,
      selectedLocationSource: '',
      showUserLocation: false,
      mapNotice: '',
      regeocoding: false,
      welcomeOpen: false,
      freePointBanner: '',
      countdownTimer: null,
      announcement: '',
      shareConfig: {},
      favId: null,
      favLoading: false,
      suggestTimer: null,
      suggestLoading: false,
      suggestions: [],
      industryLoadErr: '',
      errors: { address: '', industry: '', brand: '', size: '' },
      industryList: [],
      trusts: [
        { title: 'POI 数据', desc: '周边实时采集' },
        { title: '多维分析', desc: '竞品客流消费力' },
        { title: '实地验证', desc: '仅供参考不构成建议' }
      ]
    }
  },
  computed: {
    canAnalyze () { return !this.analyzing && this.addressText && this.industry && this.brandName && this.storeSize },
    analyzeStepItems () {
      const steps = [
        { step: 1, label: 'POI 数据采集', icon: '📍' },
        { step: 2, label: '数据交叉比对', icon: '🧮' },
        { step: 3, label: 'AI 商业评估', icon: '🧠' },
        { step: 4, label: '报告生成完毕', icon: '✅' }
      ]
      return steps.map(s => {
        const evt = this.analyzeSteps.find(e => e.step === s.step)
        if (evt) {
          return { ...s, status: 'done', msg: evt.msg, icon: '✓' }
        }
        if (s.step === this.currentStep) {
          return { ...s, status: 'active', msg: '正在处理...' }
        }
        return { ...s, status: 'pending', icon: '○' }
      })
    },
    ctaSubText () {
      if (this.analyzing) return this.analyzeStatus || '正在处理...'
      if (!this.addressText) return '请先搜索或定位门店地址'
      if (!this.canAnalyze) return '请完整填写门店位置、业态和经营信息'
      return '客流 · 竞品 · 消费力 · 风险点分析参考'
    },
    mapMarkers () {
      return [{
        id: 1,
        latitude: this.mapLat,
        longitude: this.mapLng,
        width: 30,
        height: 30,
        callout: {
          content: '门店位置',
          color: '#ffffff',
          fontSize: 12,
          borderRadius: 8,
          bgColor: '#ef4444',
          padding: 8,
          display: 'ALWAYS'
        }
      }]
    },
    srcLabel () {
      if (this.selectedLocationSource === 'locate') return '当前位置'
      if (this.selectedLocationSource === 'map') return '地图选点'
      if (this.selectedLocationSource === 'search') return '手动输入'
      if (this.selectedLocationSource === 'favorite') return '收藏带入'
      return ''
    }
  },
  onShow () {
    const pending = uni.getStorageSync('pending_analysis_address')
    if (pending) {
      this.addressText = pending
      this.addressKeyword = pending
      this.selectedLocationSource = 'favorite'
      uni.removeStorageSync('pending_analysis_address')
      uni.showToast({ title: '已加载收藏地址', icon: 'none' })
    }
  },
  onHide () {
    this.clearAnalyzeTimer()
    if (this._regionTimer) { clearTimeout(this._regionTimer); this._regionTimer = null }
    if (this.countdownTimer) { clearInterval(this.countdownTimer); this.countdownTimer = null }
  },
  onUnload () {
    this.clearAnalyzeTimer()
    if (this._regionTimer) { clearTimeout(this._regionTimer); this._regionTimer = null }
    if (this.countdownTimer) { clearInterval(this.countdownTimer); this.countdownTimer = null }
  },
  mounted () {
    api.fetchIndustries().then(r => {
      if (r.ok && Array.isArray(r.data?.industries)) this.industryList = r.data.industries
    }).catch(() => { this.industryLoadErr = '业态加载失败，请稍后重试' })
    this.initHomeData()
  },
  methods: {
    async initHomeData () {
      // 分享配置
      api.fetchShareConfig().then(c => { if (c.ok && c.data) this.shareConfig = c.data }).catch(() => {})
      // 公告独立拉取，不依赖 token
      api.fetchUiConfig().then(a => {
        if (a.ok && a.data && a.data.announcement) this.announcement = a.data.announcement
      }).catch(() => {})
      const token = uni.getStorageSync('token')
      if (!token) return
      // Profile + free point (仅已登录)
      try {
        const p = await api.fetchProfile()
        if (p.ok && p.data) {
          const u = p.data.user || {}
          if (u.free_point_active && u.free_point_expire_at) {
            this.startCountdown(u.free_point_expire_at)
          }
          const dismissed = uni.getStorageSync('welcome_dismissed')
          if (!dismissed && (p.data.is_new_user || u.is_new_user)) {
            this.welcomeOpen = true
          }
        }
      } catch (e) { /* silent */ }
    },
    startCountdown (expireAt) {
      const tick = () => {
        const now = Date.now()
        const expire = new Date(expireAt).getTime()
        const diff = expire - now
        if (diff <= 0) {
          this.freePointBanner = ''
          if (this.countdownTimer) { clearInterval(this.countdownTimer); this.countdownTimer = null }
          return
        }
        const h = Math.floor(diff / 3600000)
        const m = Math.floor((diff % 3600000) / 60000)
        this.freePointBanner = `${h}小时${m}分`
      }
      tick()
      if (this.countdownTimer) clearInterval(this.countdownTimer)
      this.countdownTimer = setInterval(tick, 30000)
    },
    dismissWelcome () {
      this.welcomeOpen = false
      uni.setStorageSync('welcome_dismissed', '1')
    },
    async checkFavStatus () {
      if (!this.addressText || !this.selectedLocationSource) { this.favId = null; return }
      const token = uni.getStorageSync('token')
      if (!token) { this.favId = null; return }
      try {
        const r = await api.checkFavorite(this.mapLat, this.mapLng)
        if (r.ok && r.data) {
          this.favId = r.data.favorite_id || null
        } else if (r.statusCode === 401) {
          this.favId = null  // 静默，不弹错误
        } else {
          this.favId = null
        }
      } catch (e) { this.favId = null }
    },
    async toggleFav () {
      if (!this.addressText) return
      const token = uni.getStorageSync('token')
      if (!token) { uni.showToast({ title: '请先登录后收藏', icon: 'none' }); return }
      this.favLoading = true
      try {
        if (this.favId) {
          const r = await api.deleteFavorite(this.favId)
          if (r.ok) { this.favId = null; uni.showToast({ title: '已取消收藏', icon: 'none' }) }
          else if (r.statusCode === 401) { uni.showToast({ title: '请先登录后取消收藏', icon: 'none' }) }
          else { uni.showToast({ title: '取消收藏失败', icon: 'none' }) }
        } else {
          const r = await api.addFavorite({
            custom_name: this.addressText,
            address: this.addressText,
            latitude: this.mapLat,
            longitude: this.mapLng
          })
          if (r.ok) {
            const fav = r.data && r.data.favorite
            if (fav && fav.id) {
              this.favId = fav.id
              uni.showToast({ title: '收藏成功', icon: 'none' })
            } else {
              uni.showToast({ title: '收藏状态同步失败，请稍后重试', icon: 'none' })
            }
          } else if (r.statusCode === 401) { uni.showToast({ title: '请先登录后收藏', icon: 'none' }) }
          else { uni.showToast({ title: '收藏失败', icon: 'none' }) }
        }
      } catch (e) { uni.showToast({ title: '网络异常', icon: 'none' }) }
      finally { this.favLoading = false }
    },
    onMapUpdated () { /* noop — map component内部事件 */ },
    async resolveAddressByLngLat (lng, lat, source) {
      this.selectedLocationSource = source
      this.regeocoding = true
      this.mapNotice = '正在识别地址...'
      try {
        const r = await api.locationRegeocode(lng, lat)
        if (r.ok && r.data?.ok && r.data?.data?.address) {
          this.addressText = r.data.data.address
          this.addressKeyword = r.data.data.address
          this.mapNotice = ''
          this.checkFavStatus()
        } else {
          const coord = `经度 ${lng.toFixed(4)} · 纬度 ${lat.toFixed(4)}`
          this.addressText = coord; this.addressKeyword = coord
          this.mapNotice = '未识别到详细地址，可继续使用当前坐标或手动搜索'
        }
      } catch (e) {
        const msg = e.errMsg || e.message || ''
        const coord = `经度 ${lng.toFixed(4)} · 纬度 ${lat.toFixed(4)}`
        this.addressText = coord; this.addressKeyword = coord
        this.mapNotice = msg.includes('timeout') ? '地址服务暂时不可用，可手动输入地址' : '地址服务暂不可用，可手动输入地址'
      } finally {
        this.regeocoding = false
      }
    },
    onIndustryChange (name) {
      // 安全兼容：字符串直接存；对象取 name/title/label/value 字段
      if (typeof name === 'string') this.industry = name
      else if (name && typeof name === 'object') this.industry = name.name || name.title || name.label || name.value || ''
      else this.industry = ''
      if (this.industry) this.errors.industry = ''
    },
    onAddressInput (e) {
      const value = (e && e.detail) ? String(e.detail.value || '') : ''
      this.addressKeyword = value
      this.errors.address = ''
      this.suggestions = []
      this.suggestErr = ''
      // ★ 用户正在输入 → 清空地图旧选点
      if (this.addressText) {
        this.addressText = ''
        this.selectedLocationSource = ''
        this.showUserLocation = false
      }
      if (this.suggestTimer) { clearTimeout(this.suggestTimer); this.suggestTimer = null }
      const kw = value.trim()
      if (kw.length < 2) {
        this.suggestLoading = false
        return
      }
      this.suggestLoading = true
      this.suggestTimer = setTimeout(() => { this.runSuggest(kw, 'auto') }, 400)
    },
    onBrandInput (e) {
      this.errors.brand = ''
      if (e && typeof e === 'object' && e.detail && typeof e.detail.value === 'string') this.brandName = e.detail.value
      else if (typeof e === 'string') this.brandName = e
    },
    onSizeInput (e) {
      this.errors.size = ''
      if (e && typeof e === 'object' && e.detail && e.detail.value !== undefined) this.storeSize = String(e.detail.value)
      else if (typeof e === 'string') this.storeSize = e
    },
    onLocate () {
      const doGetLocation = () => {
        uni.getLocation({
          type: 'gcj02',
          success: (res) => {
            this.showUserLocation = true
            this._moveMarkerTo(res.latitude, res.longitude, 'locate')
          },
          fail: (err) => {
            const msg = err.errMsg || ''
            const title = msg.includes('timeout') ? '定位超时' : '定位失败'
            const content = msg.includes('timeout')
              ? '定位超时，请检查定位权限或手动输入地址'
              : '定位失败，请检查定位权限或手动输入地址'
            uni.showModal({ title, content, showCancel: false })
          }
        })
      }

      uni.getSetting({
        success: (res) => {
          const authVal = res.authSetting['scope.userLocation']
          if (authVal === false) {
            uni.showModal({
              title: '定位权限已关闭',
              content: '请在设置中允许定位，或手动输入地址',
              cancelText: '取消',
              confirmText: '去设置',
              success: (mRes) => {
                if (mRes.confirm) uni.openSetting()
              }
            })
          } else if (authVal === true) {
            doGetLocation()
          } else {
            // undefined — 从未询问过
            uni.authorize({ scope: 'scope.userLocation',
              success: () => doGetLocation(),
              fail: () => {
                uni.showModal({
                  title: '定位授权失败',
                  content: '请在设置中允许定位，或手动输入地址',
                  showCancel: false
                })
              }
            })
          }
        },
        fail: () => doGetLocation()
      })
    },
    async runSuggest (keyword, mode) {
      if (!keyword) return
      this.suggestions = []; this.suggestErr = ''
      const reqKw = keyword
      const reqMode = mode
      this.suggestLoading = true
      try {
        const r = await api.locationSuggest(keyword)
        // ★ 防旧请求覆盖：当前输入已变，丢弃此次回调结果
        if (keyword !== (this.addressKeyword || '').trim()) return
        if (!r.ok) {
          const detail = r.data?.detail || r.data?.error || ''
          if (r.statusCode === 503) this.suggestErr = '地图服务暂不可用，请稍后重试或手动输入地址'
          else if (r.statusCode === 502) this.suggestErr = '地图服务暂时不可用，请稍后重试'
          else this.suggestErr = detail || '搜索失败，请重试'
        } else if (r.data?.ok === false) {
          this.suggestErr = r.data.error || '搜索失败'
        } else if (r.data?.data?.length) {
          this.suggestions = r.data.data
        } else {
          this.suggestErr = `未找到匹配地址：${keyword}`
        }
      } catch (e) {
        const msg = e.errMsg || e.message || ''
        if (msg.includes('timeout')) {
          this.suggestErr = '地址搜索超时，请稍后重试或手动输入'
        } else {
          this.suggestErr = '地址服务暂不可用，可手动输入地址或在地图上选点'
        }
      } finally {
        this.suggestLoading = false
      }
    },
    onSearch () {
      if (this.suggestTimer) { clearTimeout(this.suggestTimer); this.suggestTimer = null }
      this.runSuggest((this.addressKeyword || '').trim(), 'manual')
    },
    onSelectSuggestion (s) {
      if (this.suggestTimer) { clearTimeout(this.suggestTimer); this.suggestTimer = null }
      this.suggestLoading = false
      this.addressText = s.name + (s.address ? ' · ' + s.address : '')
      this.addressKeyword = this.addressText
      if (s.location) { this._moveMarkerTo(s.location.lat, s.location.lng, 'search') }
      this.selectedLocationSource = 'search'
      this.checkFavStatus()
      this.errors.address = ''
      this.suggestions = []
      this.suggestErr = ''
    },
    onMapRegionChange (e) {
      // ★ 仅在拖动/缩放结束时触发反查
      if (e.type !== 'end') return
      // 防抖：300ms 内只处理最后一次
      if (this._regionTimer) clearTimeout(this._regionTimer)
      this._regionTimer = setTimeout(() => {
        this._regionTimer = null
        const ctx = uni.createMapContext('homeMap', this)
        ctx.getCenterLocation({
          success: (res) => {
            if (res.latitude && res.longitude) {
              this._moveMarkerTo(res.latitude, res.longitude, 'drag')
            }
          },
          fail: () => { /* 获取中心失败不处理 */ }
        })
      }, 300)
    },
    onMarkerTap (e) {
      // ★ 点击已有 marker → 等同于点击地图该位置
      const mid = e.detail && e.detail.markerId
      if (mid !== undefined && this.mapMarkers.length) {
        const m = this.mapMarkers[0]
        // 允许用户确认重新定位
        uni.showToast({ title: '点击地图空白处可将标记移动到新位置', icon: 'none', duration: 2000 })
      }
    },
    _moveMarkerTo (lat, lng, source) {
      this.mapLat = lat
      this.mapLng = lng
      this.mapKey++  // 强制 map 重渲染 marker
      this.errors.address = ''
      this.resolveAddressByLngLat(lng, lat, source)
    },
    async onMapTap (e) {
      // ★ 点击地图某处 → 移动 marker 到点击位置 + 反查地址
      const lat = e.detail && e.detail.latitude
      const lng = e.detail && e.detail.longitude
      if (lat !== undefined && lng !== undefined) {
        this._moveMarkerTo(lat, lng, 'map')
      } else {
        uni.showToast({ title: '点击地图选择门店位置', icon: 'none' })
      }
    },
    clearAddress () {
      if (this.suggestTimer) { clearTimeout(this.suggestTimer); this.suggestTimer = null }
      this.suggestLoading = false
      this.addressText = ''
      this.addressKeyword = ''
      this.selectedLocationSource = ''
      this.showUserLocation = false
      this.mapNotice = ''
      this.suggestions = []
      this.suggestErr = ''
      this.favId = null
      this.favLoading = false
      this.errors.address = ''
    },
    validate () {
      const e = { address: '', industry: '', brand: '', size: '' }; let ok = true
      if (!this.addressText) { e.address = '请选择门店地址'; ok = false }
      if (!this.industry) { e.industry = '请选择业态'; ok = false }
      if (!this.brandName || !this.brandName.trim()) { e.brand = '请输入品牌或特色'; ok = false }
      const sz = parseFloat(this.storeSize)
      if (!this.storeSize || this.storeSize.toString().trim() === '') { e.size = '请输入门店预估面积，用于租金与人效精算'; ok = false }
      else if (isNaN(sz) || sz <= 0) { e.size = '店面面积必须大于 0'; ok = false }
      else if (sz > 10000) { e.size = '面积数值较大，请确认输入无误'; ok = false }
      this.errors = e; return ok
    },
    async onAnalyze () {
      if (this.analyzing) return  // 防重复点击
      if (!this.validate()) {
        const firstErr = Object.values(this.errors).find(e => e)
        if (firstErr) uni.showToast({ title: firstErr, icon: 'none' })
        return
      }
      // 查找 industry_id
      let industryId = undefined
      if (this.industry && this.industryList.length) {
        const match = this.industryList.find(item => item.name === this.industry)
        if (match && match.id) industryId = match.id
      }
      const payload = {
        address: this.addressText,
        location: { lng: this.mapLng, lat: this.mapLat },
        provider: 'deepseek',
        business_type: this.industry,
        brand_name: this.brandName,
        store_size: Number(this.storeSize)
      }
      if (industryId !== undefined) payload.industry_id = industryId

      this.analyzing = true; this.analyzeErr = ''; this.analyzeSteps = []; this.analyzeStatus = '正在连接分析服务...'
      this._analyzeStartTime = Date.now()
      // ★ 乐观步骤推进：step 1 立刻显示 active
      this.currentStep = 1
      if (this.stepTimer) clearTimeout(this.stepTimer)
      this.stepTimer = setTimeout(() => {
        if (this.analyzing && this.currentStep < 2) this.currentStep = 2
        this.stepTimer = setTimeout(() => {
          if (this.analyzing && this.currentStep < 3) this.currentStep = 3
        }, 5000)
      }, 3000)
      try {
        const r = await api.analyzeLocation(payload)
        this.clearAnalyzeTimer()
        if (r.ok && r.result) {
          this.analyzeSteps = r.steps || []
          this.currentStep = 4
          this.analyzeStatus = '报告生成完毕！'
          uni.setStorageSync('latest_analysis', { recordId: r.recordId, result: r.result, steps: r.steps })
          this.stepTimer = setTimeout(() => {
            this.analyzing = false
            uni.navigateTo({ url: `/pages/report-detail/index?id=${r.recordId}` })
          }, 600)
        } else {
          // 以真实 SSE steps 为准
          const steps = r.steps || []
          if (steps.length) {
            this.analyzeSteps = steps
            this.currentStep = Math.max(...steps.map(s => typeof s.step === 'number' ? s.step : 0))
          }
          if (r.statusCode === 401) {
            this.analyzeErr = '登录已过期，请去「我的」页面重新登录后再试'
          } else if (r.statusCode === 402) {
            this.analyzeErr = typeof r.error === 'string' ? r.error : '余额不足，请充值后重试'
          } else {
            this.analyzeErr = r.error || '分析服务异常，请稍后重试'
          }
          // ★ 超时/失败兜底：检查是否有刚生成的报告
          await this._recoverRecentReport()
          this.analyzing = false
        }
      } catch (e) {
        this.clearAnalyzeTimer()
        // ★ 超时兜底：后端可能已落库，查询最近记录
        const recovered = await this._recoverRecentReport()
        if (!recovered) {
          this.analyzeErr = typeof e === 'string' ? e : (e.message || e.errMsg || '分析服务暂不可用，请稍后重试')
        }
        this.analyzing = false
      }
    },
    onShareAppMessage () {
      const cfg = this.shareConfig || {}
      return {
        title: cfg.share_title || '址得选 - 商铺选址分析工具',
        path: '/pages/home/index',
        imageUrl: cfg.share_image_url || ''
      }
    },
    async _recoverRecentReport () {
      // 超时/失败兜底：查询最近一条记录，若在本次分析提交后生成则跳转
      try {
        const recordsRes = await api.fetchRecords(1, 1)
        if (!recordsRes.ok || !recordsRes.data) return false
        const records = recordsRes.data.records || []
        if (!records.length) return false
        const latest = records[0]
        const createdAt = latest.created_at ? new Date(latest.created_at).getTime() : 0
        const startTime = this._analyzeStartTime || 0
        if (createdAt > startTime - 5000 && latest.report_uuid) {
          // 报告在本次提交后生成（允许 5s 时钟偏差）
          this.analyzeStatus = '报告已生成！'
          this.analyzeSteps.push({ step: 4, msg: '报告已在后台生成完毕' })
          this.currentStep = 4
          this.stepTimer = setTimeout(() => {
            this.analyzing = false
            uni.navigateTo({ url: `/pages/report-detail/index?id=${latest.report_uuid}` })
          }, 400)
          return true
        }
      } catch (_) { /* 兜底失败不覆盖原始错误 */ }
      return false
    },
    clearAnalyzeTimer () {
      if (this.stepTimer) { clearTimeout(this.stepTimer); this.stepTimer = null }
    }
  }
}
</script>

<style scoped>
.home-page { min-height:100vh; background:radial-gradient(circle at 50% -8%,rgba(49,91,255,0.12),transparent 34%),linear-gradient(180deg,#f8fbff 0%,#e8eef7 42%,#dce4f2 100%); padding-bottom:108rpx; }

/* ── Hero ── */
.hero { background:radial-gradient(circle at 76% 38%,rgba(83,137,255,0.48),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.24),transparent 26%),radial-gradient(circle at 58% 58%,rgba(248,200,97,0.10),transparent 22%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); padding:46rpx 28rpx 122rpx; position:relative; overflow:hidden; }
.hero::before { content:''; position:absolute; left:-130rpx; top:-236rpx; width:720rpx; height:420rpx; border-radius:0 0 58% 58%; background:linear-gradient(180deg,rgba(255,255,255,0.10),rgba(255,255,255,0.015)); transform:rotate(7deg); }
.hero::after { content:''; position:absolute; left:0; right:0; bottom:0; height:230rpx; background:linear-gradient(180deg,rgba(255,255,255,0),rgba(219,234,254,0.26)); }
.hero-top { display:flex; align-items:center; margin-bottom:28rpx; position:relative; z-index:2; }
.hero-logo-box { width:70rpx; height:70rpx; border-radius:18rpx; margin-right:14rpx; display:flex; align-items:center; justify-content:center; overflow:hidden; background:linear-gradient(135deg,#ffffff 0%,#dbeafe 46%,#2545cb 100%); box-shadow:0 12rpx 30rpx rgba(5,22,88,0.32),0 0 0 1px rgba(248,200,97,0.22); flex-shrink:0; }
.hero-logo { width:62rpx; height:62rpx; display:block; border-radius:16rpx; }
.hero-lockup { display:flex; flex-direction:column; }
.hero-brand { font-size:40rpx; font-weight:900; color:#fff; line-height:1.1; }
.hero-slogan { font-size:24rpx; color:rgba(219,234,254,0.78); margin-top:2rpx; }
.hero-copy { text-align:left; margin-bottom:24rpx; padding-right:210rpx; position:relative; z-index:2; }
.hero-title { display:block; font-size:52rpx; font-weight:900; color:#fff; line-height:1.14; text-shadow:0 8rpx 28rpx rgba(6,20,80,0.28); }
.hero-hl { display:block; color:#d4e5ff; }
.hero-desc { display:block; font-size:24rpx; color:rgba(232,240,255,0.80); margin-top:18rpx; line-height:1.55; }
.hero-tags { display:flex; gap:10rpx; position:relative; z-index:2; }
.htag { font-size:20rpx; color:rgba(255,255,255,0.88); background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.22); border-radius:999rpx; padding:9rpx 16rpx; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.18); }
.htag:nth-child(3) { color:#ffe8b0; background:rgba(248,200,97,0.12); border-color:rgba(248,200,97,0.38); }
.hero-city { position:absolute; right:0; bottom:124rpx; width:330rpx; height:238rpx; z-index:1; opacity:0.54; pointer-events:none; }
.hc-building { position:absolute; bottom:0; width:40rpx; border-radius:9rpx 9rpx 0 0; background:linear-gradient(180deg,rgba(219,234,254,0.78),rgba(37,99,235,0.10)); box-shadow:inset 0 0 0 1px rgba(255,255,255,0.12),0 0 28rpx rgba(147,197,253,0.10); }
.hc-building::after { content:''; position:absolute; inset:15rpx 10rpx; background:repeating-linear-gradient(180deg,rgba(255,255,255,0.36) 0 6rpx,transparent 6rpx 18rpx); }
.hc-a { right:204rpx; height:86rpx; }
.hc-b { right:154rpx; height:138rpx; }
.hc-c { right:104rpx; height:190rpx; }
.hc-d { right:54rpx; height:118rpx; }
.hc-e { right:4rpx; height:154rpx; }
.hero-visual { position:absolute; right:20rpx; top:132rpx; width:260rpx; height:252rpx; pointer-events:none; z-index:2; }
.hv-plate { position:absolute; left:12rpx; right:8rpx; bottom:22rpx; height:92rpx; border-radius:38rpx; transform:skewX(-13deg); background:linear-gradient(135deg,rgba(239,246,255,0.96),rgba(147,197,253,0.60)); box-shadow:0 22rpx 58rpx rgba(6,18,48,0.32),0 0 34rpx rgba(248,200,97,0.14),inset 0 1rpx 0 rgba(255,255,255,0.70); }
.hv-ring { position:absolute; border:3rpx solid rgba(37,99,235,0.34); border-radius:50%; transform:skewX(13deg); }
.ring-a { width:136rpx; height:42rpx; left:48rpx; top:26rpx; }
.ring-b { width:86rpx; height:24rpx; left:72rpx; top:36rpx; opacity:0.78; }
.hv-orbit { position:absolute; left:18rpx; right:22rpx; bottom:88rpx; height:62rpx; border:3rpx solid rgba(248,200,97,0.52); border-radius:50%; transform:rotate(-8deg); box-shadow:0 0 22rpx rgba(248,200,97,0.24); }
.hv-pin { position:absolute; right:66rpx; top:0; width:108rpx; height:146rpx; background:transparent; }
.hv-pin::before { content:''; position:absolute; left:10rpx; top:0; width:88rpx; height:88rpx; border-radius:52rpx 52rpx 52rpx 12rpx; transform:rotate(-45deg); background:linear-gradient(145deg,#66d7ff 0%,#2468ff 48%,#5b4be6 100%); box-shadow:0 18rpx 42rpx rgba(37,99,235,0.46),inset -8rpx -8rpx 18rpx rgba(55,48,163,0.18),inset 8rpx 8rpx 18rpx rgba(255,255,255,0.16); }
.hv-pin::after { content:''; position:absolute; left:48rpx; top:78rpx; width:12rpx; height:40rpx; border-radius:999rpx; background:linear-gradient(180deg,rgba(255,255,255,0.72),rgba(147,197,253,0.18)); box-shadow:0 10rpx 22rpx rgba(37,99,235,0.24); }
.hv-pin-core { position:absolute; top:24rpx; left:36rpx; width:36rpx; height:36rpx; border-radius:50%; background:#fff; box-shadow:0 0 0 10rpx rgba(255,255,255,0.22),inset 0 0 0 7rpx rgba(79,70,229,0.10); z-index:1; }

/* ── Search card ── */
.search-section { position:relative; z-index:30; margin:-72rpx 24rpx 0; }
.search-card { background:rgba(255,255,255,0.98); border-radius:22rpx; padding:20rpx; box-shadow:0 18rpx 54rpx rgba(79,119,186,0.16); position:relative; border:1px solid rgba(219,230,255,0.92); }
.sc-label-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:14rpx; }
.sc-label { font-size:25rpx; font-weight:800; color:#0f172a; }
.sc-state { font-size:21rpx; color:#94a3b8; background:#f1f5f9; border-radius:999rpx; padding:5rpx 14rpx; }
.sc-state.ready { color:#047857; background:#dcfce7; }
.sc-input-row { display:flex; align-items:center; }
.sc-icon { position:relative; width:56rpx; height:58rpx; text-align:center; font-size:0; color:transparent; flex-shrink:0; display:block; }
.sc-icon::before { content:''; position:absolute; left:13rpx; top:7rpx; width:30rpx; height:30rpx; border-radius:18rpx 18rpx 18rpx 4rpx; transform:rotate(-45deg); background:linear-gradient(145deg,#ff6b6b,#ef4444); box-shadow:0 8rpx 18rpx rgba(239,68,68,0.22); }
.sc-icon::after { content:''; position:absolute; left:24rpx; top:18rpx; width:8rpx; height:8rpx; border-radius:50%; background:#fff; box-shadow:0 0 0 5rpx rgba(255,255,255,0.24); }
.sc-field { flex:1; height:76rpx; font-size:30rpx; color:#0f172a; padding:0 8rpx; border:none; background:transparent; font-weight:600; }
.sc-action { width:92rpx; height:64rpx; min-width:92rpx; padding:0; margin:0; border-radius:999rpx; background:linear-gradient(135deg,#1e6bff,#4f46e5); color:#fff; font-size:24rpx; font-weight:900; line-height:64rpx; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 12rpx 28rpx rgba(37,99,235,0.30),0 0 0 1px rgba(248,200,97,0.18); }
.sc-action::after { border:none; }
.sc-action[disabled] { opacity:0.45; }
.sc-action.fav { background:#fff7ed; color:#d6a84f; box-shadow:none; border:1px solid #fed7aa; }
.sc-hint { margin-top:10rpx; padding:10rpx 14rpx; background:#f8fbff; border-radius:12rpx; color:#64748b; font-size:22rpx; line-height:1.45; border:1px solid rgba(219,230,255,0.64); }
.suggest-list { background:#fff; border-radius:0 0 14rpx 14rpx; margin:4rpx -8rpx -8rpx; box-shadow:0 8rpx 24rpx rgba(0,0,0,0.08); max-height:340rpx; overflow-y:auto; }
.suggest-item { padding:22rpx 20rpx; border-top:1px solid #f1f5f9; }
.sg-name { font-size:28rpx; color:#1e293b; display:block; } .sg-addr { font-size:22rpx; color:#94a3b8; margin-top:4rpx; display:block; }
.suggest-empty { padding:20rpx; font-size:24rpx; color:#94a3b8; text-align:center; }

/* ── Map section ── */
.map-section { padding:0 20rpx; margin-top:24rpx; }
.section-line { display:flex; justify-content:space-between; align-items:flex-end; margin:0 4rpx 14rpx; }
.section-title { display:block; font-size:32rpx; font-weight:900; color:#0f172a; }
.section-sub { display:block; margin-top:4rpx; font-size:22rpx; color:#64748b; }
.section-badge { font-size:22rpx; color:#315bff; background:#eef3ff; border-radius:999rpx; padding:8rpx 16rpx; }
.addr-bar { display:flex; align-items:center; background:rgba(255,255,255,0.96); border-radius:16rpx; padding:18rpx 22rpx; margin-bottom:14rpx; box-shadow:0 8rpx 24rpx rgba(79,119,186,0.08); border:1px solid rgba(219,230,255,0.92); }
.ab-left { display:flex; align-items:center; flex:1; min-width:0; }
.ab-pin { font-size:28rpx; margin-right:12rpx; flex-shrink:0; }
.ab-mid { flex:1; min-width:0; }
.ab-name { font-size:26rpx; color:#1e293b; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:block; }
.ab-src { font-size:20rpx; color:#94a3b8; }
.ab-edit { width:auto; min-width:84rpx; margin:0; padding:6rpx 14rpx; background:#f3f7ff; border-radius:999rpx; color:#315bff; font-size:24rpx; line-height:34rpx; flex-shrink:0; }
.ab-edit::after { border:none; }
.map-wrap { position:relative; border-radius:24rpx; overflow:hidden; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.12); border:8rpx solid rgba(255,255,255,0.96); background:#fff; }
.map-view { width:100%; height:360rpx; }
.map-overlay { position:absolute; inset:0; background:rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; }
.mo-text { color:#fff; font-size:28rpx; font-weight:600; }
.map-hint { text-align:center; padding:12rpx 0 4rpx; font-size:24rpx; color:#94a3b8; }
.map-hint.done { color:#16a34a; } .map-hint.warn { color:#dc2626; }

/* ── Biz card ── */
.biz-card { background:rgba(255,255,255,0.96); margin:24rpx 20rpx 0; border-radius:24rpx; padding:30rpx 24rpx 26rpx; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); border:1px solid rgba(219,230,255,0.92); }
.biz-head { margin-bottom:18rpx; display:flex; justify-content:space-between; align-items:flex-start; }
.biz-title { display:block; font-size:32rpx; font-weight:900; color:#0f172a; }
.biz-sub { display:block; margin-top:4rpx; font-size:22rpx; color:#64748b; }
.biz-link { color:#8ba0bf; font-size:22rpx; margin-top:4rpx; }
.biz-fields { display:flex; flex-direction:column; gap:16rpx; margin-top:24rpx; padding:0; border-radius:0; background:transparent; border:0; }
.field-head { width:100%; padding:4rpx 2rpx 2rpx; }
.field-head-title { display:block; color:#0f172a; font-weight:900; font-size:28rpx; }
.field-head-sub { display:block; margin-top:6rpx; color:#8b99b6; font-size:22rpx; line-height:1.45; }
.bf-item { width:100%; min-width:0; padding:18rpx 18rpx 20rpx; border-radius:18rpx; background:linear-gradient(180deg,#ffffff,#f8fbff); border:1px solid rgba(219,230,255,0.90); box-shadow:0 10rpx 22rpx rgba(74,111,172,0.05); box-sizing:border-box; }

:deep(.industry-picker) { margin:18rpx 0 0; }
:deep(.industry-picker .label) { display:none; }
:deep(.cat-scroll) { padding-bottom:12rpx; }
:deep(.cat-tile) { width:126rpx; min-height:96rpx; padding:18rpx 8rpx; margin-right:14rpx; border-radius:18rpx; background:linear-gradient(180deg,#ffffff,#fbfdff); border:1px solid rgba(219,230,255,0.95); box-shadow:0 10rpx 22rpx rgba(74,111,172,0.07); color:#17244e; }
:deep(.cat-tile.active) { background:linear-gradient(180deg,#ffffff,#f4f7ff); border-color:rgba(74,117,255,0.56); box-shadow:0 14rpx 28rpx rgba(68,84,255,0.16); }
:deep(.cat-name) { font-size:22rpx; font-weight:900; color:#17244e; margin-top:10rpx; }
:deep(.cat-tile.active .cat-name) { color:#315bff; }
:deep(.sub-panel) { margin-top:18rpx; padding:16rpx; border-radius:16rpx; background:linear-gradient(180deg,#f8fbff,#ffffff); gap:12rpx; border:1px solid rgba(219,230,255,0.78); }
:deep(.chip) { padding:12rpx 22rpx; border-radius:16rpx; background:#fff; font-size:25rpx; font-weight:700; color:#5c677d; border:1px solid rgba(219,230,255,0.95); box-shadow:0 8rpx 18rpx rgba(74,111,172,0.05); }
:deep(.chip.selected) { background:#f3f7ff; color:#315bff; border-color:rgba(88,105,255,0.44); box-shadow:0 10rpx 20rpx rgba(68,84,255,0.11); }

/* ── Shared ── */
.label { font-size:24rpx; font-weight:900; color:#1f2d4f; margin-bottom:12rpx; }
.req { color:#ef4444; font-size:24rpx; }
.field-err { font-size:22rpx; color:#dc2626; margin-top:8rpx; display:block; }
.analyze-err { text-align:center; margin:14rpx auto 0; line-height:1.45; max-width:640rpx; }
.field { width:100%; height:74rpx; border:1px solid rgba(199,215,246,0.95); border-radius:14rpx; padding:0 20rpx; font-size:28rpx; font-weight:700; background:#fff; color:#1e293b; box-sizing:border-box; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.9),0 8rpx 18rpx rgba(74,111,172,0.04); }
.field:disabled { background:#f9fafb; color:#9ca3af; }

/* ── CTA ── */
.cta-zone { padding:0 20rpx; margin-top:30rpx; }
.cta-btn { width:100%; background:linear-gradient(135deg,#0b3fbd 0%,#151f8f 58%,#5b3fd9 100%); color:#fff; border-radius:16rpx; padding:24rpx 24rpx; display:flex; flex-direction:column; align-items:center; border:none; box-shadow:0 18rpx 38rpx rgba(21,31,143,0.32),0 0 0 1px rgba(248,200,97,0.16); }
.cta-btn::after { border:none; }
.cta-btn[disabled] { opacity:1; background:linear-gradient(180deg,#ffffff,#f5f8ff); color:#315bff; box-shadow:0 10rpx 24rpx rgba(74,111,172,0.08); border:1px dashed rgba(49,91,255,0.34); }
.cta-main { font-size:30rpx; font-weight:900; line-height:1.2; }
.cta-sub { font-size:22rpx; color:rgba(255,255,255,0.78); margin-top:6rpx; line-height:1.35; }
.cta-btn[disabled] .cta-sub { color:#8b99b6; }

/* ── Analyze steps ── */
.analyze-steps { background:#f8fafc; border:1px solid #e2e8f0; border-radius:12rpx; padding:20rpx; margin-top:16rpx; }
.as-step { display:flex; align-items:flex-start; padding:6rpx 0; }
.as-step.pending .as-icon,.as-step.pending .as-label { color:#cbd5e1; }
.as-step.active .as-icon { color:#2563eb; } .as-step.active .as-label { color:#1e293b; font-weight:600; }
.as-step.done .as-icon { color:#16a34a; } .as-step.done .as-label { color:#475569; }
.as-icon { width:44rpx; font-size:28rpx; text-align:center; flex-shrink:0; margin-right:10rpx; line-height:34rpx; }
.as-body { flex:1; } .as-label { font-size:25rpx; color:#475569; display:block; } .as-msg { font-size:22rpx; color:#94a3b8; display:block; }

/* ── Features ── */
.features { display:flex; gap:0; margin:28rpx 28rpx 0; padding:20rpx 10rpx; background:rgba(255,255,255,0.92); border:1px solid rgba(219,230,255,0.86); border-radius:20rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.08); }
.ft { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; gap:8rpx; text-align:center; background:transparent; border-radius:0; padding:8rpx 10rpx; box-shadow:none; border-right:1rpx solid rgba(219,230,255,0.78); min-width:0; }
.ft:last-child { border-right:0; }
.ft-mark { display:block; width:44rpx; height:44rpx; line-height:44rpx; text-align:center; border-radius:14rpx; color:#fff; background:linear-gradient(135deg,#2f6dff,#5b4be6); font-size:26rpx; flex-shrink:0; box-shadow:0 10rpx 20rpx rgba(88,105,255,0.16); }
.ft:nth-child(3) .ft-mark { background:linear-gradient(135deg,#f8c861,#d8a23d); box-shadow:0 10rpx 20rpx rgba(216,162,61,0.18); }
.ft-title { font-size:24rpx; font-weight:900; color:#17244e; display:block; white-space:nowrap; line-height:1.1; }
.ft-desc { display:block; font-size:20rpx; color:#8b99b6; line-height:1.25; }
.footer { text-align:center; font-size:20rpx; color:#94a3b8; padding:18rpx 44rpx 10rpx; line-height:1.65; }

/* ── Welcome modal ── */
.welcome-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:500; display:flex; align-items:center; justify-content:center; }
.welcome-modal { width:580rpx; background:#fff; border-radius:20rpx; padding:48rpx 32rpx; text-align:center; }
.wm-icon { font-size:80rpx; } .wm-title { font-size:32rpx; font-weight:800; color:#1e293b; margin-top:16rpx; } .wm-body { font-size:26rpx; color:#64748b; margin-top:12rpx; line-height:1.5; }
.wm-btn { width:100%; background:#0f172a; color:#fff; border-radius:14rpx; font-size:30rpx; font-weight:700; padding:22rpx 0; margin-top:28rpx; }

/* ── Banners ── */
.free-banner { background:#fef3c7; padding:16rpx 24rpx; text-align:center; font-size:24rpx; color:#92400e; }
.ann-banner { background:#dbeafe; padding:16rpx 24rpx; text-align:center; font-size:24rpx; color:#1e40af; }
</style>

<style>
page { background-color:#eef3f9; }
</style>
