<template>
  <view class="home-page">
    <!-- 欢迎弹层 -->
    <view class="welcome-mask" v-if="welcomeOpen" @tap="dismissWelcome">
      <view class="welcome-modal" @tap.stop>
        <view class="wm-icon">🎁</view>
        <view class="wm-title">欢迎使用址得选</view>
        <view class="wm-body">系统已赠送免费初筛额度，请尽快使用</view>
        <button class="wm-btn" @tap="dismissWelcome">开始体验</button>
      </view>
    </view>

    <!-- 免费额度倒计时 -->
    <view class="free-banner" v-if="freePointBanner">
      <text>免费初筛额度剩余 {{ freePointBanner }} · 请尽快使用</text>
    </view>

    <!-- 全局公告 -->
    <view class="ann-banner" v-if="announcement">
      <text>{{ announcement }}</text>
    </view>

    <!-- ── Hero（Web 对齐：logo lockup + hero copy + search card）── -->
    <view class="hero">
      <view class="hero-top">
        <image class="hero-logo" src="/static/brand-logo.png" mode="aspectFit" />
        <view class="hero-lockup">
          <text class="hero-brand">址得选</text>
          <text class="hero-slogan">AI 智能选址</text>
        </view>
      </view>
      <view class="hero-copy">
        <text class="hero-title">商铺选址<text class="hero-hl">先做一次初筛</text></text>
        <text class="hero-desc">用周边 POI、业态与经营信息生成商业选址初筛参考</text>
      </view>
      <view class="hero-tags">
        <text class="htag">全国城市适用</text>
        <text class="htag">POI 周边洞察</text>
        <text class="htag">需线下验证</text>
      </view>

      <!-- 搜索卡片（浮在 hero/map 上的主入口） -->
      <view class="search-card">
        <view class="sc-input-row">
          <view class="sc-icon">⌖</view>
          <input class="sc-field" :value="addressKeyword" placeholder="输入地址搜索门店位置" :disabled="analyzing" @input="onAddressInput" @confirm="onSearch" />
          <view class="sc-locate" @tap="onLocate" v-if="!addressText">
            <text class="scl-icon">◎</text>
          </view>
          <view class="sc-fav" @tap="toggleFav" v-if="addressText && !analyzing">
            <text :style="{ color: favId ? '#d6a84f' : '#94a3b8' }">{{ favId ? '★' : '☆' }}</text>
          </view>
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
      <view class="addr-bar" v-if="addressText">
        <view class="ab-left">
          <text class="ab-pin">📍</text>
          <view class="ab-mid">
            <text class="ab-name">{{ addressText }}</text>
            <text class="ab-src" v-if="selectedLocationSource">来源：{{ srcLabel }}</text>
          </view>
        </view>
        <text class="ab-edit" @tap="clearAddress">重选</text>
      </view>
      <text class="field-err" v-if="errors.address">{{ errors.address }}</text>

      <view class="map-wrap">
        <map class="map-view" :latitude="mapLat" :longitude="mapLng" scale="15" :show-location="showUserLocation" :enable-scroll="!analyzing" :enable-zoom="!analyzing" :enable-rotate="false" @tap="onMapTap" @regionchange="onMapRegionChange" @updated="onMapUpdated">
          <cover-view class="map-marker">
            <cover-view class="mm-outer" />
            <cover-view class="mm-inner" />
          </cover-view>
        </map>
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
        <text class="biz-title">选择业态</text>
      </view>
      <text class="field-err" v-if="industryLoadErr">{{ industryLoadErr }}</text>
      <IndustryPicker :selected="industry" :disabled="analyzing" :industries="industryList" @change="onIndustryChange" />
      <text class="field-err" v-if="errors.industry">{{ errors.industry }}</text>

      <view class="biz-fields">
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
        <text class="cta-main">{{ analyzing ? '分析中...' : '生成初筛报告' }}</text>
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
      <text class="field-err" v-if="analyzeErr">{{ analyzeErr }}</text>
    </view>

    <!-- ── Feature tiles ── -->
    <view class="features">
      <view class="ft" v-for="t in trusts" :key="t.title">
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
      welcomeOpen: false,
      freePointBanner: '',
      countdownTimer: null,
      announcement: '',
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
        { title: '多维初筛', desc: '竞品客流消费力' },
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
      return '客流 · 竞品 · 消费力 · 风险点初筛参考'
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
    if (this.countdownTimer) { clearInterval(this.countdownTimer); this.countdownTimer = null }
  },
  onUnload () {
    this.clearAnalyzeTimer()
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
            this.mapLat = res.latitude; this.mapLng = res.longitude
            this.showUserLocation = true
            this.errors.address = ''
            this.resolveAddressByLngLat(res.longitude, res.latitude, 'locate')
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
      if (s.location) { this.mapLng = s.location.lng; this.mapLat = s.location.lat }
      this.selectedLocationSource = 'search'
      this.checkFavStatus()
      this.errors.address = ''
      this.suggestions = []
      this.suggestErr = ''
    },
    onMapRegionChange (e) {
      // regionchange handled internally by map component
    },
    async onMapTap (e) {
      if (e.detail && e.detail.latitude) {
        this.mapLat = e.detail.latitude; this.mapLng = e.detail.longitude
        this.errors.address = ''
        this.resolveAddressByLngLat(this.mapLng, this.mapLat, 'map')
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
          this.analyzing = false
        }
      } catch (e) {
        this.clearAnalyzeTimer()
        this.analyzeErr = typeof e === 'string' ? e : (e.message || e.errMsg || '分析服务暂不可用，请稍后重试')
        this.analyzing = false
      }
    },
    clearAnalyzeTimer () {
      if (this.stepTimer) { clearTimeout(this.stepTimer); this.stepTimer = null }
    }
  }
}
</script>

<style scoped>
.home-page { min-height:100vh; background:#f0f2f5; padding-bottom:80rpx; }

/* ── Hero ── */
.hero { background:linear-gradient(170deg,#0a0f1e 0%,#111d3a 40%,#152244 100%); padding:48rpx 28rpx 68rpx; position:relative; overflow:hidden; }
.hero::after { content:''; position:absolute; top:-80rpx; right:-60rpx; width:300rpx; height:300rpx; border-radius:50%; background:rgba(59,130,246,0.06); pointer-events:none; }
.hero-top { display:flex; align-items:center; margin-bottom:28rpx; }
.hero-logo { width:52rpx; height:52rpx; border-radius:12rpx; margin-right:14rpx; }
.hero-lockup { display:flex; flex-direction:column; }
.hero-brand { font-size:34rpx; font-weight:800; color:#fff; line-height:1.2; }
.hero-slogan { font-size:22rpx; color:rgba(255,255,255,0.5); }
.hero-copy { text-align:left; margin-bottom:24rpx; padding-right:40rpx; }
.hero-title { display:block; font-size:38rpx; font-weight:800; color:#fff; line-height:1.35; }
.hero-hl { color:#60a5fa; }
.hero-desc { display:block; font-size:24rpx; color:rgba(255,255,255,0.5); margin-top:10rpx; line-height:1.5; }
.hero-tags { display:flex; gap:12rpx; margin-bottom:32rpx; }
.htag { font-size:20rpx; color:rgba(255,255,255,0.4); border:1px solid rgba(255,255,255,0.15); border-radius:6rpx; padding:4rpx 14rpx; }

/* ── Search card ── */
.search-card { background:#fff; border-radius:16rpx; padding:8rpx; box-shadow:0 8rpx 32rpx rgba(0,0,0,0.18); position:relative; z-index:10; }
.sc-input-row { display:flex; align-items:center; }
.sc-icon { width:56rpx; text-align:center; font-size:28rpx; color:#94a3b8; flex-shrink:0; }
.sc-field { flex:1; height:80rpx; font-size:28rpx; color:#1e293b; padding:0 4rpx; border:none; background:transparent; }
.sc-locate { width:56rpx; height:56rpx; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.scl-icon { font-size:28rpx; color:#64748b; }
.sc-fav { width:56rpx; text-align:center; font-size:30rpx; flex-shrink:0; }
.suggest-list { background:#fff; border-radius:0 0 14rpx 14rpx; margin:4rpx -8rpx -8rpx; box-shadow:0 8rpx 24rpx rgba(0,0,0,0.08); max-height:340rpx; overflow-y:auto; }
.suggest-item { padding:22rpx 20rpx; border-top:1px solid #f1f5f9; }
.sg-name { font-size:28rpx; color:#1e293b; display:block; } .sg-addr { font-size:22rpx; color:#94a3b8; margin-top:4rpx; display:block; }
.suggest-empty { padding:20rpx; font-size:24rpx; color:#94a3b8; text-align:center; }

/* ── Map section ── */
.map-section { padding:0 20rpx; margin-top:24rpx; }
.addr-bar { display:flex; align-items:center; background:#fff; border-radius:12rpx; padding:16rpx 20rpx; margin-bottom:12rpx; box-shadow:0 1px 8rpx rgba(0,0,0,0.04); }
.ab-left { display:flex; align-items:center; flex:1; min-width:0; }
.ab-pin { font-size:28rpx; margin-right:12rpx; flex-shrink:0; }
.ab-mid { flex:1; min-width:0; }
.ab-name { font-size:26rpx; color:#1e293b; font-weight:500; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; display:block; }
.ab-src { font-size:20rpx; color:#94a3b8; }
.ab-edit { font-size:26rpx; color:#64748b; padding:4rpx 12rpx; flex-shrink:0; }
.map-wrap { position:relative; border-radius:14rpx; overflow:hidden; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.08); }
.map-view { width:100%; height:420rpx; }
.map-overlay { position:absolute; inset:0; background:rgba(0,0,0,0.3); display:flex; align-items:center; justify-content:center; }
.mo-text { color:#fff; font-size:28rpx; font-weight:600; }
.map-marker { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); pointer-events:none; z-index:10; }
.mm-outer { width:32rpx; height:32rpx; background:rgba(220,38,38,0.2); border-radius:50%; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); }
.mm-inner { width:16rpx; height:16rpx; background:#dc2626; border:3rpx solid #fff; border-radius:50%; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); box-shadow:0 2rpx 10rpx rgba(0,0,0,0.3); }
.map-hint { text-align:center; padding:12rpx 0 4rpx; font-size:24rpx; color:#94a3b8; }
.map-hint.done { color:#16a34a; } .map-hint.warn { color:#dc2626; }

/* ── Biz card ── */
.biz-card { background:#fff; margin:20rpx 20rpx 0; border-radius:16rpx; padding:28rpx 24rpx; box-shadow:0 1px 8rpx rgba(0,0,0,0.04); }
.biz-head { margin-bottom:16rpx; }
.biz-title { font-size:28rpx; font-weight:700; color:#111827; }
.biz-fields { display:flex; gap:14rpx; margin-top:24rpx; padding-top:20rpx; border-top:1px solid #f1f5f9; }
.bf-item { flex:1; }

/* ── Shared ── */
.label { font-size:26rpx; font-weight:600; color:#334155; margin-bottom:8rpx; }
.req { color:#ef4444; font-size:24rpx; }
.field-err { font-size:22rpx; color:#dc2626; margin-top:8rpx; display:block; }
.field { width:100%; border:1px solid #d1d5db; border-radius:10rpx; padding:16rpx 14rpx; font-size:28rpx; background:#fff; color:#1e293b; box-sizing:border-box; }
.field:disabled { background:#f9fafb; color:#9ca3af; }

/* ── CTA ── */
.cta-zone { padding:0 20rpx; margin-top:20rpx; }
.cta-btn { width:100%; background:linear-gradient(135deg,#0f172a,#1e3a5f); color:#fff; border-radius:14rpx; padding:32rpx 24rpx; display:flex; flex-direction:column; align-items:center; border:none; }
.cta-btn[disabled] { opacity:0.35; background:#64748b; }
.cta-main { font-size:34rpx; font-weight:700; }
.cta-sub { font-size:24rpx; color:rgba(255,255,255,0.55); margin-top:6rpx; }

/* ── Analyze steps ── */
.analyze-steps { background:#f8fafc; border:1px solid #e2e8f0; border-radius:12rpx; padding:20rpx; margin-top:16rpx; }
.as-step { display:flex; align-items:flex-start; padding:6rpx 0; }
.as-step.pending .as-icon,.as-step.pending .as-label { color:#cbd5e1; }
.as-step.active .as-icon { color:#2563eb; } .as-step.active .as-label { color:#1e293b; font-weight:600; }
.as-step.done .as-icon { color:#16a34a; } .as-step.done .as-label { color:#475569; }
.as-icon { width:44rpx; font-size:28rpx; text-align:center; flex-shrink:0; margin-right:10rpx; line-height:34rpx; }
.as-body { flex:1; } .as-label { font-size:25rpx; color:#475569; display:block; } .as-msg { font-size:22rpx; color:#94a3b8; display:block; }

/* ── Features ── */
.features { display:flex; justify-content:center; gap:40rpx; padding:28rpx 20rpx 12rpx; }
.ft { text-align:center; }
.ft-title { font-size:24rpx; font-weight:600; color:#475569; display:block; }
.ft-desc { font-size:22rpx; color:#94a3b8; margin-top:2rpx; display:block; }
.footer { text-align:center; font-size:22rpx; color:#94a3b8; padding:24rpx 32rpx; line-height:1.6; }

/* ── Welcome modal ── */
.welcome-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:500; display:flex; align-items:center; justify-content:center; }
.welcome-modal { width:580rpx; background:#fff; border-radius:20rpx; padding:48rpx 32rpx; text-align:center; }
.wm-icon { font-size:80rpx; } .wm-title { font-size:32rpx; font-weight:800; color:#1e293b; margin-top:16rpx; } .wm-body { font-size:26rpx; color:#64748b; margin-top:12rpx; line-height:1.5; }
.wm-btn { width:100%; background:#0f172a; color:#fff; border-radius:14rpx; font-size:30rpx; font-weight:700; padding:22rpx 0; margin-top:28rpx; }

/* ── Banners ── */
.free-banner { background:#fef3c7; padding:16rpx 24rpx; text-align:center; font-size:24rpx; color:#92400e; }
.ann-banner { background:#dbeafe; padding:16rpx 24rpx; text-align:center; font-size:24rpx; color:#1e40af; }
</style>
