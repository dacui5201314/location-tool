<template>
  <view class="home-page">
    <!-- ═══ Home Panel: 选址 ═══ -->
    <view class="tab-panel" v-if="activeTab === 'home'">
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
          <input class="sc-field" :value="addressText ? compactAddress : addressKeyword" placeholder="输入地址搜索门店位置" :disabled="analyzing" @input="onAddressInput" @confirm="onSearch" />
          <button class="sc-action" :disabled="analyzing" @tap="onLocate" v-if="!addressText">定位</button>
          <button class="sc-action fav" :class="{ active: favId }" :disabled="favLoading || analyzing" @tap="toggleFav" v-if="addressText">
            <text class="fav-star">{{ favId ? '★' : '☆' }}</text>
            <text>{{ favLoading ? '收藏中' : (favId ? '已收藏' : '收藏地址') }}</text>
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
          <text class="section-sub" v-if="!analyzing">拖动地图将准星对准门店位置 · 或点击地图选点</text>
          <text class="section-sub" v-else>分析完成后可查看完整报告</text>
        </view>
        <text class="section-badge">{{ analyzing ? '分析中' : (addressText ? '已选位置' : '待选择') }}</text>
      </view>
      <view class="addr-bar" v-if="addressText && !analyzing">
        <view class="ab-left">
          <text class="ab-pin">📍</text>
          <view class="ab-mid">
            <text class="ab-name">{{ addressText }}</text>
          </view>
        </view>
        <button class="ab-edit" @tap="clearAddress">重选</button>
      </view>
      <text class="field-err" v-if="errors.address">{{ errors.address }}</text>

      <!-- ═══ 地图三态：互斥渲染，绝不共存 ═══ -->
      <view class="map-wrap">

        <!-- 状态 A：Placeholder（首帧 / welcome 弹窗） -->
        <view class="map-placeholder" v-if="mapMode === 'placeholder'">
          <view class="ph-label">门店位置</view>
          <view class="ph-city">
            <view class="phb phb-a" /><view class="phb phb-b" />
            <view class="phb phb-c" /><view class="phb phb-d" />
          </view>
        </view>

        <!-- 状态 B：真实地图（idle 选点态） -->
        <template v-if="mapMode === 'map'">
          <map id="homeMap" class="map-view" :latitude="mapLat" :longitude="mapLng" :markers="mapMarkers" scale="15" :show-location="showUserLocation" :enable-scroll="true" :enable-zoom="true" :enable-rotate="false" @tap="onMapTap" @regionchange="onMapRegionChange" />
          <cover-view class="crosshair-pin">
            <cover-image class="pin-image" src="/static/map-center-pin.png" />
          </cover-view>
        </template>

        <!-- 状态 C：分析中卡片 -->
        <view class="analyzing-card" v-if="mapMode === 'analyzing'">
          <view class="ac-grid" />
          <view class="ac-code">
            <text>POI_SYNC</text>
            <text>RISK_SCAN</text>
            <text>MODEL_GUARD</text>
          </view>
          <view class="ac-core">
            <view class="ac-pulse" />
            <view>
              <text class="ac-title">商业数据引擎运行中</text>
              <text class="ac-sub">正在交叉校验 POI、竞品、客流与风险线索</text>
            </view>
          </view>
          <view class="ac-meter">
            <view class="ac-meter-top">
              <text>ANALYSIS_PROGRESS</text>
              <text>{{ analyzeProgress }}%</text>
            </view>
            <view class="ac-meter-track">
              <view class="ac-meter-fill" :style="{ width: analyzeProgress + '%' }" />
            </view>
          </view>
          <view class="ac-steps">
            <view class="acs" v-for="s in analyzeStepItems" :key="s.step" :class="s.status">
              <text class="acs-icon">{{ s.icon }}</text>
              <text class="acs-label">{{ s.label }}</text>
            </view>
          </view>
        </view>

      </view>

      <view class="map-hint" v-if="mapMode === 'map'" :class="{ done: addressText, warn: !!mapNotice }">
        <text>{{ mapNotice || (addressText ? '已选位置 · 拖动地图可微调' : '拖动地图将准星对准门店位置 · 或点击地图选点') }}</text>
      </view>
    </view>

    <!-- ── 业态 ── -->
    <view class="biz-card industry-card">
      <view class="biz-head">
        <view class="biz-title-row">
          <text class="section-icon industry-icon">♟</text>
          <view>
          <text class="biz-title">选择业态</text>
          <text class="biz-sub">选择与业务最匹配的业态分类</text>
          </view>
        </view>
        <text class="biz-link">全部业态 ›</text>
      </view>
      <text class="field-err" v-if="industryLoadErr">{{ industryLoadErr }}</text>
      <IndustryPicker :selected="industry" :disabled="analyzing" :industries="industryList" @change="onIndustryChange" />
      <text class="field-err" v-if="errors.industry">{{ errors.industry }}</text>
    </view>

    <!-- ── 经营画像 ── -->
    <view class="biz-card profile-card">
      <view class="biz-fields">
        <view class="field-head">
          <view class="field-head-main">
            <text class="section-icon profile-icon">▥</text>
            <view>
              <text class="field-head-title">经营画像</text>
              <text class="field-head-sub">品牌与面积越清晰，分析越稳定</text>
            </view>
          </view>
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
      <button class="cta-btn" :class="{ dim: !canAnalyze }" :disabled="analyzing" @tap="onAnalyze">
        <text class="cta-icon">▤</text>
        <view class="cta-copy">
          <text class="cta-main">{{ analyzing ? '分析中...' : '生成选址报告' }}</text>
          <text class="cta-sub">{{ ctaSubText }}</text>
        </view>
        <text class="cta-arrow">›</text>
      </button>
      <view class="analyze-steps" v-if="analyzing">
        <view class="as-head">
          <view>
            <text class="as-kicker">MATRIX_ANALYSIS</text>
            <text class="as-title">商业选址模型计算中</text>
          </view>
          <text class="as-percent">{{ analyzeProgress }}%</text>
        </view>
        <view class="as-progress">
          <view class="as-progress-fill" :style="{ width: analyzeProgress + '%' }" />
        </view>
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
    </view><!-- /tab-panel home -->

    <!-- ═══ Records Panel ═══ -->
    <view class="tab-panel sub-tab-panel" v-if="activeTab === 'records'">
      <RecordsPanel ref="recordsPanel" @go-tab="onGoTab" />
    </view>

    <!-- ═══ Favorites Panel ═══ -->
    <view class="tab-panel sub-tab-panel" v-if="activeTab === 'favorites'">
      <FavoritesPanel ref="favoritesPanel" @go-tab="onGoTab" />
    </view>

    <!-- ═══ Profile Panel ═══ -->
    <view class="tab-panel sub-tab-panel" v-if="activeTab === 'profile'">
      <ProfilePanel ref="profilePanel" @go-tab="onGoTab" />
    </view>

    <!-- ═══ 自绘底部导航 ═══ -->
    <view class="custom-tabbar">
      <view class="ctb-item" v-for="t in tabDefs" :key="t.key"
            :class="{ active: activeTab === t.key }" @tap="onSwitchTab(t.key)">
        <view class="ctb-icon-wrap">
          <image class="ctb-icon" :src="activeTab === t.key ? t.iconActive : t.icon" mode="aspectFit" />
        </view>
        <text class="ctb-label">{{ t.label }}</text>
      </view>
    </view>
  </view>
</template>

<script>
import IndustryPicker from '../../components/industry-picker/index.vue'
import RecordsPanel from '../../components/tab/RecordsPanel.vue'
import FavoritesPanel from '../../components/tab/FavoritesPanel.vue'
import ProfilePanel from '../../components/tab/ProfilePanel.vue'
import api from '../../utils/api'
import config from '../../utils/config'

export default {
  components: { IndustryPicker, RecordsPanel, FavoritesPanel, ProfilePanel },
  data () {
    return {
      addressKeyword: '',
      addressText: '',
      mapLat: 39.9087,
      mapLng: 116.3975,
      mapReady: false,  // 延迟渲染 map 避免首次白块
      _favoriteId: null,  // 从收藏发起时关联 favorite_id
      _regionTimer: null,
      activeTab: 'home',
      tabDefs: [
        { key:'home', label:'选址', icon:'/static/tabbar/home.png', iconActive:'/static/tabbar/home-active.png' },
        { key:'records', label:'记录', icon:'/static/tabbar/records.png', iconActive:'/static/tabbar/records-active.png' },
        { key:'favorites', label:'收藏', icon:'/static/tabbar/favorites.png', iconActive:'/static/tabbar/favorites-active.png' },
        { key:'profile', label:'我的', icon:'/static/tabbar/profile.png', iconActive:'/static/tabbar/profile-active.png' }
      ],
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
      homeShareImageLocal: '',
      _homeShareImageRemote: '',
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
    mapMode () {
      if (this.analyzing) return 'analyzing'
      if (!this.mapReady) return 'placeholder'
      return 'map'
    },
    canAnalyze () { return !this.analyzing && this.addressText && this.industry && this.brandName && this.storeSize },
    analyzeStepItems () {
      const steps = [
        { step: 1, label: 'POI 数据采集', icon: '01' },
        { step: 2, label: '数据交叉比对', icon: '02' },
        { step: 3, label: 'AI 商业评估', icon: 'AI' },
        { step: 4, label: '报告生成完毕', icon: 'OK' }
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
    analyzeProgress () {
      const doneSteps = new Set(
        (this.analyzeSteps || [])
          .map(s => Number(s.step))
          .filter(n => Number.isFinite(n) && n > 0)
      )
      if (doneSteps.has(4)) return 100
      const current = Math.max(1, Math.min(4, Number(this.currentStep) || 1))
      const activeProgress = [0, 18, 43, 68, 92][current]
      const doneProgress = Math.min(88, doneSteps.size * 24)
      return Math.max(activeProgress, doneProgress)
    },
    ctaSubText () {
      if (this.analyzing) return this.analyzeStatus || '正在处理...'
      if (!this.addressText) return '请先搜索或定位门店地址'
      if (!this.canAnalyze) return '请完整填写门店位置、业态和经营信息'
      return '客流 · 竞品 · 消费力 · 风险点分析参考'
    },
    ctaHintText () {
      if (!this.addressText) return '请选择门店位置'
      if (!this.industry) return '请选择业态'
      if (!this.brandName || !this.brandName.trim()) return '请填写品牌或特色'
      if (!this.storeSize || this.storeSize.toString().trim() === '') return '请填写门店面积'
      return ''
    },
    mapMarkers () {
      return []
    },
    compactAddress () {
      const raw = (this.addressText || '').replace(/\s+/g, '')
      if (!raw) return ''
      const SUFFIXES = [
        '特别行政区','自治区','自治州','自治县','自治旗',
        '县级市','市辖区',
        '省','市','区','县','旗','街道','镇','乡','地区','盟','林区','特区'
      ]
      let cleaned = raw
      const strippedCities = []
      for (let i = 0; i < 4; i++) {
        let matched = false
        for (const sfx of SUFFIXES) {
          const re = new RegExp('^(.{1,8}' + sfx + ')')
          const m = cleaned.match(re)
          if (m && cleaned.length - m[0].length >= 6) {
            const stripped = m[0]
            if (sfx === '市' && stripped.length <= 6) {
              strippedCities.push(stripped)
            }
            cleaned = cleaned.slice(stripped.length)
            matched = true
            break
          }
        }
        if (!matched) break
      }
      for (const city of strippedCities) {
        cleaned = cleaned.replace(city, '')
      }
      if (cleaned.length > 20) {
        cleaned = cleaned.slice(0, 18) + '...'
      }
      return cleaned || raw
    },
  },
  onLoad (options) {
    // ★ 支持 ?tab=records|favorites|profile 从外部 reLaunch 进入指定 tab
    if (options.tab && ['home','records','favorites','profile'].includes(options.tab)) {
      this.activeTab = options.tab
    }
  },
  onShow () {
    // ★ 确保 map 在 tab 返回时可用：mounted 的 350ms 定时器可能在 onHide 被取消
    if (!this.mapReady && !this.analyzing && !this.welcomeOpen) {
      this.mapReady = true
    }
    // ★ 切换 tab 时刷新对应面板
    this._refreshActivePanel()
    // ★ 外部 reLaunch 回到首页时，消费收藏pending
    this._consumePendingAnalysis()
    // ★ 重新拉取分享配置，确保后台修改后小程序不沿用旧缓存
    api.fetchShareConfig().then(c => {
      if (c.ok && c.data) {
        this.shareConfig = c.data
        const imgUrl = this.resolveShareImage(c.data.home_share_image_url || c.data.share_image_url || '')
        if (imgUrl) {
          this._homeShareImageRemote = imgUrl
          this._downloadShareImage(imgUrl, 'home')
        }
      }
    }).catch(() => {})
  },
  async onPullDownRefresh () {
    try {
      await this.initHomeData().catch(() => {})
      const refMap = { records: 'recordsPanel', favorites: 'favoritesPanel', profile: 'profilePanel' }
      const refName = refMap[this.activeTab]
      if (refName && this.$refs[refName] && this.$refs[refName].refresh) {
        const ret = this.$refs[refName].refresh()
        if (ret && ret.then) await ret.catch(() => {})
      }
    } finally {
      uni.stopPullDownRefresh()
    }
  },
  onHide () {
    this.clearAnalyzeTimer()
    if (this._mapTimer) { clearTimeout(this._mapTimer); this._mapTimer = null }
    if (this._regionTimer) { clearTimeout(this._regionTimer); this._regionTimer = null }
    if (this.countdownTimer) { clearInterval(this.countdownTimer); this.countdownTimer = null }
  },
  onUnload () {
    this.clearAnalyzeTimer()
    if (this._mapTimer) { clearTimeout(this._mapTimer); this._mapTimer = null }
    if (this._regionTimer) { clearTimeout(this._regionTimer); this._regionTimer = null }
    if (this.countdownTimer) { clearInterval(this.countdownTimer); this.countdownTimer = null }
  },
  mounted () {
    api.fetchIndustries().then(r => {
      if (r.ok && Array.isArray(r.data?.industries)) this.industryList = r.data.industries
    }).catch(() => { this.industryLoadErr = '业态加载失败，请稍后重试' })
    this.initHomeData()
    // ★ 延迟渲染 map 避免首次白块闪烁
    this._mapTimer = setTimeout(() => { this.mapReady = true }, 350)
  },
  onShareAppMessage () {
    const cfg = this.shareConfig || {}
    const imageUrl = this.homeShareImageLocal
      || this.resolveShareImage(cfg.home_share_image_url || cfg.share_image_url || '')
      || this._homeShareImageRemote
    console.log('[share-home] cfg.home_share_image_url:', cfg.home_share_image_url || '(empty)')
    console.log('[share-home] homeShareImageLocal:', this.homeShareImageLocal || '(empty)')
    console.log('[share-home] final imageUrl:', imageUrl || '(empty)')
    return {
      title: cfg.share_title || '址得选 - 商铺选址分析工具',
      path: '/pages/home/index',
      ...(imageUrl ? { imageUrl } : {})
    }
  },
  methods: {
    resolveShareImage (url) {
      if (!url) return ''
      if (url.startsWith('/assets/')) return config.API_BASE_URL + url
      return url
    },
    _downloadShareImage (url, type) {
      uni.downloadFile({
        url,
        success: (res) => {
          if (res.statusCode === 200 && res.tempFilePath) {
            if (type === 'home') this.homeShareImageLocal = res.tempFilePath
            else if (type === 'report') this.reportShareImageLocal = res.tempFilePath
          }
        },
        fail: (err) => { console.warn('[share] download image failed', (err && err.errMsg) || err) }
      })
    },
    onSwitchTab (key) {
      const sameTab = this.activeTab === key
      this._scrollPageTop()
      if (!sameTab) this.activeTab = key
      this.$nextTick(() => {
        this._scrollPageTop()
        if (!sameTab) this._refreshActivePanel()
        if (key === 'home') this._consumePendingAnalysis()
      })
    },
    onGoTab (key) {
      this.onSwitchTab(key)
    },
    _scrollPageTop () {
      setTimeout(() => {
        uni.pageScrollTo({ scrollTop: 0, duration: 0 })
      }, 0)
    },
    _consumePendingAnalysis () {
      const pending = uni.getStorageSync('pending_analysis_address')
      if (!pending) return
      this.addressText = pending
      this.addressKeyword = pending
      this.selectedLocationSource = 'favorite'
      const favLat = uni.getStorageSync('pending_analysis_lat')
      const favLng = uni.getStorageSync('pending_analysis_lng')
      const favId = uni.getStorageSync('pending_analysis_fav_id')
      if (favLat && favLng) {
        this._setLocation(Number(favLat), Number(favLng), 'favorite')
      }
      // 严格清洗：只接受有效正整数
      const favIdNum = Number(favId)
      if (Number.isSafeInteger(favIdNum) && favIdNum > 0) {
        this.favId = favIdNum
        this._favoriteId = favIdNum
      } else {
        this._favoriteId = null
      }
      uni.removeStorageSync('pending_analysis_address')
      uni.removeStorageSync('pending_analysis_lat')
      uni.removeStorageSync('pending_analysis_lng')
      uni.removeStorageSync('pending_analysis_fav_id')
      uni.showToast({ title: '已加载收藏地址', icon: 'none' })
    },
    _refreshActivePanel () {
      const refMap = { records:'recordsPanel', favorites:'favoritesPanel', profile:'profilePanel' }
      const refName = refMap[this.activeTab]
      if (refName && this.$refs[refName] && this.$refs[refName].refresh) {
        this.$refs[refName].refresh()
      }
    },
    async initHomeData () {
      // 分享配置 — 下载分享图到本地临时路径
      api.fetchShareConfig().then(c => {
        if (c.ok && c.data) {
          this.shareConfig = c.data
          const imgUrl = this.resolveShareImage(c.data.home_share_image_url || c.data.share_image_url || '')
          if (imgUrl) {
            this._homeShareImageRemote = imgUrl
            this._downloadShareImage(imgUrl, 'home')
          }
        }
      }).catch(() => {})
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
            this._setLocation(res.latitude, res.longitude, 'locate')
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
      if (s.location) { this._setLocation(s.location.lat, s.location.lng, 'search') }
      this.selectedLocationSource = 'search'
      this.checkFavStatus()
      this.errors.address = ''
      this.suggestions = []
      this.suggestErr = ''
    },
    onMapRegionChange (e) {
      // ★ 拖动/缩放结束后，读取地图中心点 → 反查地址
      if (e.type !== 'end') return
      if (this._regionTimer) clearTimeout(this._regionTimer)
      this._regionTimer = setTimeout(() => {
        this._regionTimer = null
        const ctx = uni.createMapContext('homeMap', this)
        ctx.getCenterLocation({
          success: (res) => {
            if (res.latitude && res.longitude) {
              this._setLocation(res.latitude, res.longitude, 'drag')
            }
          },
          fail: () => {}
        })
      }, 400)
    },
    _setLocation (lat, lng, source) {
      // ★ 统一位置更新：lat/lng + 反查地址
      this.mapLat = lat
      this.mapLng = lng
      this.errors.address = ''
      this.resolveAddressByLngLat(lng, lat, source)
    },
    async onMapTap (e) {
      // ★ 点击地图某处 → 更新位置并反查地址（mapLat/mapLng state 变化自动移动地图中心）
      const lat = e.detail && e.detail.latitude
      const lng = e.detail && e.detail.longitude
      if (lat !== undefined && lng !== undefined) {
        this._setLocation(lat, lng, 'map')
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
        store_size: Math.max(0, Number(this.storeSize) || 0)
      }
      if (industryId !== undefined && Number.isFinite(industryId)) payload.industry_id = Number(industryId)
      // ★ favorite_id 只在有效正整数时传入
      if (typeof this._favoriteId === 'number' && Number.isSafeInteger(this._favoriteId) && this._favoriteId > 0) {
        payload.favorite_id = this._favoriteId
      }

      // ═══ 最终兜底：delete 任何非法 optional 字段 ═══
      for (const opt of ['favorite_id', 'industry_id']) {
        const v = payload[opt]
        if (v === undefined) continue
        const n = Number(v)
        if (!Number.isSafeInteger(n) || n <= 0) {
          delete payload[opt]
        } else {
          payload[opt] = n
        }
      }
      // ★ 坐标一致性保护：有地址但坐标为默认北京时阻止
      if (this.addressText && this.mapLat === 39.9087 && this.mapLng === 116.3975) {
        this.analyzeErr = '请重新确认门店位置（当前坐标为默认值）'
        uni.showToast({ title: '请在地图上重新选择门店位置', icon: 'none' })
        return
      }

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
            this.analyzeErr = this.friendlyAnalyzeError(r.error)
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
          const msg = typeof e === 'string' ? e : (e.message || e.errMsg || '分析服务暂不可用，请稍后重试')
          this.analyzeErr = this.friendlyAnalyzeError(msg)
        }
        this.analyzing = false
      }
    },
    friendlyAnalyzeError (msg) {
      const text = typeof msg === 'string' ? msg : ''
      if (text.includes('事实校验') || text.includes('FACT_GUARD')) return text
      if (text.includes('数据解析异常') || text.includes('JSON')) return text
      if (text.includes('保存失败') || text.includes('DB')) return text
      if (text.includes('数据采集失败') || text.includes('AMAP')) return text
      return text || '分析服务异常，请稍后重试'
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
.home-page { min-height:100vh; background:radial-gradient(circle at 50% -8%,rgba(49,91,255,0.12),transparent 34%),linear-gradient(180deg,#f8fbff 0%,#e8eef7 42%,#dce4f2 100%); padding-bottom:calc(64rpx + env(safe-area-inset-bottom)); }

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
.hero-desc { display:block; font-size:26rpx; color:rgba(232,240,255,0.84); margin-top:18rpx; line-height:1.55; }
.hero-tags { display:flex; gap:10rpx; position:relative; z-index:2; }
.htag { font-size:23rpx; color:rgba(255,255,255,0.90); background:rgba(255,255,255,0.10); border:1px solid rgba(255,255,255,0.22); border-radius:999rpx; padding:10rpx 17rpx; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.18); }
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
.search-card { background:rgba(255,255,255,0.98); border-radius:22rpx; padding:22rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.12); position:relative; border:1px solid rgba(219,230,255,0.92); }
.sc-label-row { display:flex; justify-content:space-between; align-items:center; margin-bottom:14rpx; }
.sc-label { font-size:28rpx; font-weight:900; color:#0f172a; }
.sc-state { font-size:23rpx; color:#64748b; background:#f1f5f9; border-radius:999rpx; padding:6rpx 14rpx; }
.sc-state.ready { color:#047857; background:#dcfce7; }
.sc-input-row { display:flex; align-items:center; }
.sc-icon { position:relative; width:56rpx; height:58rpx; text-align:center; font-size:0; color:transparent; flex-shrink:0; display:block; }
.sc-icon::before { content:''; position:absolute; left:13rpx; top:7rpx; width:30rpx; height:30rpx; border-radius:18rpx 18rpx 18rpx 4rpx; transform:rotate(-45deg); background:linear-gradient(145deg,#ff6b6b,#ef4444); box-shadow:0 8rpx 18rpx rgba(239,68,68,0.22); }
.sc-icon::after { content:''; position:absolute; left:24rpx; top:18rpx; width:8rpx; height:8rpx; border-radius:50%; background:#fff; box-shadow:0 0 0 5rpx rgba(255,255,255,0.24); }
.sc-field { flex:1; height:76rpx; font-size:29rpx; color:#0f172a; padding:0 8rpx; border:none; background:transparent; font-weight:700; }
.sc-action { width:96rpx; height:66rpx; min-width:96rpx; padding:0; margin:0; border-radius:999rpx; background:linear-gradient(135deg,#315bff,#0b3fbd); color:#fff; font-size:25rpx; font-weight:900; line-height:66rpx; display:flex; align-items:center; justify-content:center; flex-shrink:0; box-shadow:0 10rpx 22rpx rgba(49,91,255,0.20); }
.sc-action::after { border:none; }
.sc-action[disabled] { background:#eef2f7; color:#94a3b8; box-shadow:none; opacity:1; }
.sc-action.fav { width:168rpx; min-width:168rpx; gap:6rpx; background:linear-gradient(180deg,#fffdf5,#fff6df); color:#ad7a12; box-shadow:0 10rpx 22rpx rgba(216,162,61,0.12),inset 0 1rpx 0 rgba(255,255,255,0.8); border:1px solid #f8d98a; }
.sc-action.fav.active { background:linear-gradient(135deg,#fff3c4,#f8c861 58%,#dba640); color:#17244e; border-color:rgba(255,255,255,0.56); box-shadow:0 12rpx 26rpx rgba(216,162,61,0.20); }
.fav-star { font-size:28rpx; line-height:1; }
.sc-hint { margin-top:10rpx; padding:12rpx 14rpx; background:#f8fbff; border-radius:12rpx; color:#64748b; font-size:24rpx; line-height:1.45; border:1px solid rgba(219,230,255,0.64); }
.suggest-list { background:#fff; border-radius:18rpx; margin:12rpx -2rpx -2rpx; box-shadow:0 12rpx 28rpx rgba(79,119,186,0.10); border:1rpx solid rgba(219,230,255,0.92); max-height:340rpx; overflow-y:auto; }
.suggest-item { padding:22rpx 20rpx; border-top:1px solid #f1f5f9; }
.sg-name { font-size:28rpx; color:#1e293b; display:block; } .sg-addr { font-size:22rpx; color:#94a3b8; margin-top:4rpx; display:block; }
.suggest-empty { padding:20rpx; font-size:24rpx; color:#94a3b8; text-align:center; }

/* ── Map section ── */
.map-section { margin:24rpx 20rpx 0; padding:26rpx 22rpx 24rpx; background:rgba(255,255,255,0.96); border:1rpx solid rgba(219,230,255,0.92); border-radius:22rpx; box-shadow:0 16rpx 34rpx rgba(79,119,186,0.10); }
.section-line { display:flex; justify-content:space-between; align-items:flex-end; margin:0 4rpx 14rpx; }
.section-title { display:block; font-size:32rpx; font-weight:900; color:#0f172a; }
.section-sub { display:block; margin-top:4rpx; font-size:24rpx; color:#64748b; line-height:1.45; }
.section-badge { font-size:23rpx; color:#315bff; background:#eef3ff; border-radius:999rpx; padding:8rpx 16rpx; }
.addr-bar { display:flex; align-items:center; background:linear-gradient(180deg,#ffffff,#f8fbff); border-radius:18rpx; padding:20rpx 22rpx; margin-bottom:14rpx; box-shadow:0 8rpx 18rpx rgba(74,111,172,0.05); border:1px solid rgba(219,230,255,0.92); }
.ab-left { display:flex; align-items:center; flex:1; min-width:0; }
.ab-pin { font-size:28rpx; margin-right:12rpx; flex-shrink:0; }
.ab-mid { flex:1; min-width:0; }
.ab-name { font-size:26rpx; color:#1e293b; font-weight:500; display:block; word-break:break-all; display:-webkit-box; -webkit-box-orient:vertical; -webkit-line-clamp:2; overflow:hidden; }
.ab-src { font-size:22rpx; color:#8b99b6; line-height:1.35; }
.ab-edit { width:auto; min-width:92rpx; margin:0; padding:8rpx 16rpx; background:#eef3ff; border-radius:999rpx; color:#315bff; font-size:25rpx; line-height:36rpx; font-weight:800; flex-shrink:0; }
.ab-edit::after { border:none; }
.map-wrap { position:relative; border-radius:18rpx; overflow:hidden; box-shadow:none; border:1rpx solid rgba(219,230,255,0.92); background:#dce4f2; min-height:360rpx; }
.map-view { width:100%; height:360rpx; }

/* State A: Placeholder card */
.map-placeholder { height:360rpx; background:linear-gradient(180deg,#e8edf5,#dce4f2); display:flex; flex-direction:column; align-items:center; justify-content:center; position:relative; overflow:hidden; }
.ph-label { font-size:26rpx; color:#94a3b8; font-weight:600; position:relative; z-index:1; }
.ph-city { position:absolute; bottom:0; left:0; right:0; height:120rpx; display:flex; justify-content:center; gap:16rpx; align-items:flex-end; padding-bottom:20rpx; }
.phb { width:40rpx; border-radius:8rpx 8rpx 0 0; background:rgba(148,163,184,0.25); }
.phb-a { height:60rpx; } .phb-b { height:96rpx; } .phb-c { height:78rpx; } .phb-d { height:48rpx; }

/* State B: Map center pin */
.crosshair-pin { position:absolute; left:50%; top:50%; width:96rpx; height:128rpx; margin-left:-48rpx; margin-top:-116rpx; z-index:10; pointer-events:none; display:flex; align-items:center; justify-content:center; }
.pin-image { width:72rpx; height:96rpx; display:block; }

/* State C: Analyzing card */
.analyzing-card { height:360rpx; background:radial-gradient(circle at 16% 20%,rgba(91,141,255,0.32),transparent 31%),radial-gradient(circle at 86% 82%,rgba(28,105,255,0.22),transparent 36%),linear-gradient(135deg,#061946 0%,#0b2c71 48%,#08225e 100%); display:flex; flex-direction:column; justify-content:center; padding:28rpx; position:relative; overflow:hidden; box-sizing:border-box; box-shadow:inset 0 1rpx 0 rgba(197,221,255,0.18),0 16rpx 34rpx rgba(10,35,92,0.18); }
.analyzing-card::after { content:''; position:absolute; left:-20%; right:-20%; top:-45%; height:120rpx; background:linear-gradient(180deg,transparent,rgba(116,173,255,0.16),transparent); transform:rotate(8deg); animation:matrixScan 2.8s linear infinite; }
.ac-grid { position:absolute; inset:0; opacity:0.36; background:linear-gradient(rgba(116,173,255,0.11) 1rpx,transparent 1rpx),linear-gradient(90deg,rgba(116,173,255,0.11) 1rpx,transparent 1rpx); background-size:34rpx 34rpx; }
.ac-code { position:absolute; right:20rpx; top:18rpx; display:flex; flex-direction:column; align-items:flex-end; gap:6rpx; color:rgba(141,190,255,0.76); font-size:18rpx; font-weight:900; line-height:1.1; letter-spacing:0; }
.ac-core { position:relative; z-index:1; display:flex; align-items:center; gap:20rpx; margin-bottom:18rpx; }
.ac-pulse { width:72rpx; height:72rpx; border-radius:50%; background:radial-gradient(circle,#8ec5ff 0 23%,rgba(80,139,255,0.46) 24% 42%,rgba(80,139,255,0.12) 43% 100%); box-shadow:0 0 30rpx rgba(80,139,255,0.30),0 14rpx 30rpx rgba(37,99,235,0.22), inset 0 2rpx 0 rgba(255,255,255,0.28); position:relative; animation:pulse 1.5s ease-in-out infinite; flex-shrink:0; }
.ac-pulse::before { content:''; position:absolute; inset:-10rpx; border-radius:50%; border:2rpx solid rgba(142,197,255,0.28); box-sizing:border-box; }
.ac-pulse::after { content:''; position:absolute; inset:12rpx; border-radius:50%; border:2rpx solid rgba(198,221,255,0.56); box-sizing:border-box; }
@keyframes pulse { 0%,100% { transform:scale(1); opacity:0.86; } 50% { transform:scale(1.06); opacity:1; } }
@keyframes matrixScan { 0% { transform:translateY(-60rpx) rotate(8deg); opacity:0; } 20% { opacity:1; } 100% { transform:translateY(500rpx) rotate(8deg); opacity:0; } }
.ac-title { display:block; font-size:31rpx; font-weight:900; color:#ffffff; line-height:1.25; }
.ac-sub { display:block; font-size:22rpx; color:rgba(205,225,255,0.78); margin-top:7rpx; line-height:1.45; }
.ac-meter { position:relative; z-index:1; margin-bottom:14rpx; }
.ac-meter-top { display:flex; align-items:center; justify-content:space-between; color:rgba(168,207,255,0.82); font-size:18rpx; font-weight:900; line-height:1; }
.ac-meter-track { margin-top:10rpx; height:10rpx; border-radius:999rpx; overflow:hidden; background:rgba(11,36,88,0.86); border:1rpx solid rgba(116,173,255,0.24); }
.ac-meter-fill { height:100%; border-radius:999rpx; background:linear-gradient(90deg,#4f8cff,#8ec5ff,#c6ddff); box-shadow:0 0 22rpx rgba(80,139,255,0.34); transition:width 0.25s ease; }
.ac-steps { position:relative; z-index:1; width:100%; display:grid; grid-template-columns:1fr 1fr; gap:12rpx; }
.acs { display:flex; align-items:center; gap:10rpx; min-height:54rpx; padding:0 14rpx; border-radius:14rpx; font-size:22rpx; color:rgba(205,225,255,0.52); background:rgba(6,25,70,0.54); border:1rpx solid rgba(116,173,255,0.18); box-sizing:border-box; }
.acs.active { color:#ffffff; border-color:rgba(80,139,255,0.68); background:rgba(49,91,255,0.28); box-shadow:0 0 24rpx rgba(80,139,255,0.18); font-weight:900; }
.acs.done { color:#c6ddff; border-color:rgba(116,173,255,0.34); background:rgba(80,139,255,0.16); }
.acs-icon { width:34rpx; height:34rpx; line-height:34rpx; border-radius:10rpx; text-align:center; font-size:18rpx; font-weight:900; background:rgba(198,221,255,0.12); color:inherit; flex-shrink:0; }
.map-hint { text-align:center; padding:12rpx 0 4rpx; font-size:24rpx; color:#94a3b8; }
.map-hint.done { color:#16a34a; } .map-hint.warn { color:#dc2626; }

/* ── Biz card ── */
.biz-card { background:linear-gradient(180deg,#ffffff 0%,#fbfdff 100%); margin:24rpx 28rpx 0; border-radius:24rpx; padding:30rpx 26rpx 28rpx; box-shadow:0 22rpx 48rpx rgba(64,98,160,0.12),inset 0 1rpx 0 rgba(255,255,255,0.88); border:1rpx solid rgba(218,229,250,0.92); position:relative; overflow:hidden; }
.biz-card::before { display:none; }
.industry-card { margin-top:28rpx; }
.profile-card { margin-top:24rpx; }
.biz-head { margin-bottom:24rpx; display:flex; justify-content:space-between; align-items:flex-start; gap:18rpx; }
.biz-title-row,.field-head-main { display:flex; align-items:flex-start; gap:16rpx; min-width:0; }
.section-icon { width:38rpx; height:38rpx; margin-top:2rpx; border-radius:12rpx; display:flex; align-items:center; justify-content:center; color:#fff; font-size:22rpx; line-height:38rpx; font-weight:900; flex-shrink:0; background:linear-gradient(135deg,#1e6bff,#5b4be6); box-shadow:0 10rpx 22rpx rgba(49,91,255,0.22); }
.industry-icon { font-size:20rpx; }
.profile-icon { font-size:22rpx; }
.biz-title { display:block; font-size:34rpx; font-weight:900; color:#0f172a; line-height:1.22; }
.biz-sub { display:block; margin-top:7rpx; font-size:25rpx; color:#7a8aa8; line-height:1.45; }
.biz-link { color:#8ba0bf; font-size:25rpx; margin-top:4rpx; flex-shrink:0; }
.biz-fields { display:flex; flex-direction:column; gap:24rpx; margin-top:0; padding:0; border-radius:0; background:transparent; border:0; }
.field-head { width:100%; padding:0 0 2rpx; }
.field-head-title { display:block; color:#0f172a; font-weight:900; font-size:34rpx; line-height:1.22; }
.field-head-sub { display:block; margin-top:7rpx; color:#7a8aa8; font-size:25rpx; line-height:1.45; }
.bf-item { width:100%; min-width:0; padding:22rpx 22rpx 24rpx; border-radius:18rpx; background:linear-gradient(180deg,#ffffff,#fbfdff); border:1rpx solid rgba(205,220,248,0.96); box-shadow:0 10rpx 24rpx rgba(74,111,172,0.06); box-sizing:border-box; }

:deep(.industry-picker) { margin:0; }
:deep(.industry-picker .label) { display:none; }
:deep(.cat-wrap) { padding-bottom:28rpx; }
:deep(.cat-scroll) { height:158rpx; padding:0; box-sizing:border-box; }
:deep(.cat-row) { display:inline-flex; gap:18rpx; padding-right:60rpx; }
:deep(.cat-tile) { width:166rpx; height:148rpx; min-height:148rpx; padding:18rpx 12rpx; margin-right:0; border-radius:18rpx; background:linear-gradient(180deg,#ffffff,#f9fbff); border:1rpx solid rgba(209,222,249,0.98); box-shadow:0 14rpx 30rpx rgba(74,111,172,0.08); color:#17244e; }
:deep(.cat-tile.active) { background:linear-gradient(180deg,#ffffff,#f4f7ff); border-color:rgba(74,117,255,0.56); box-shadow:0 14rpx 28rpx rgba(68,84,255,0.16); }
:deep(.cat-icon) { width:64rpx; height:64rpx; min-width:64rpx; min-height:64rpx; border-radius:18rpx; flex-shrink:0; }
:deep(.cat-name) { display:block; width:100%; text-align:center; font-size:24rpx; font-weight:900; color:#17244e; margin-top:16rpx; line-height:1.18; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
:deep(.cat-tile.active .cat-name) { color:#315bff; }
:deep(.sub-panel) { margin-top:20rpx; padding:18rpx; border-radius:18rpx; background:linear-gradient(180deg,#f8fbff,#ffffff); gap:13rpx; border:1rpx solid rgba(219,230,255,0.86); }
:deep(.chip) { padding:13rpx 24rpx; border-radius:16rpx; background:#fff; font-size:25rpx; font-weight:800; color:#5c677d; border:1rpx solid rgba(219,230,255,0.95); box-shadow:0 8rpx 18rpx rgba(74,111,172,0.05); }
:deep(.chip.selected) { background:#f3f7ff; color:#315bff; border-color:rgba(88,105,255,0.44); box-shadow:0 10rpx 20rpx rgba(68,84,255,0.11); }

/* ── Shared ── */
.label { font-size:26rpx; font-weight:900; color:#1f2d4f; margin-bottom:14rpx; }
.req { color:#ef4444; font-size:24rpx; }
.field-err { font-size:24rpx; color:#dc2626; margin-top:8rpx; display:block; line-height:1.45; }
.analyze-err { text-align:left; margin:16rpx auto 0; line-height:1.55; max-width:640rpx; padding:18rpx 22rpx; border-radius:16rpx; background:#fff1f2; border:1rpx solid #fecdd3; color:#be123c; box-sizing:border-box; }
.field { width:100%; height:76rpx; border:1rpx solid rgba(199,215,246,0.95); border-radius:15rpx; padding:0 22rpx; font-size:29rpx; font-weight:700; background:#fff; color:#1e293b; box-sizing:border-box; box-shadow:inset 0 1rpx 0 rgba(255,255,255,0.9),0 8rpx 18rpx rgba(74,111,172,0.04); }
.field:disabled { background:#f9fafb; color:#9ca3af; }

/* ── CTA ── */
.cta-zone { padding:0 28rpx; margin-top:28rpx; }
.cta-btn { width:100%; min-height:104rpx; background:radial-gradient(circle at 84% 26%,rgba(255,255,255,0.18),transparent 26%),linear-gradient(135deg,#0b4eff 0%,#1f57ff 50%,#315bff 100%); color:#fff; border-radius:18rpx; padding:18rpx 22rpx; display:flex; flex-direction:row; align-items:center; border:none; box-shadow:0 18rpx 38rpx rgba(49,91,255,0.28),inset 0 1rpx 0 rgba(255,255,255,0.26); text-align:left; }
.cta-btn::after { border:none; }
.cta-btn[disabled] { opacity:1; }
.cta-btn.dim { background:radial-gradient(circle at 84% 26%,rgba(255,255,255,0.16),transparent 26%),linear-gradient(135deg,#0b4eff 0%,#1f57ff 50%,#315bff 100%); color:#fff; box-shadow:0 18rpx 38rpx rgba(49,91,255,0.22),inset 0 1rpx 0 rgba(255,255,255,0.22); border:0; }
.cta-icon { width:64rpx; height:64rpx; margin-right:20rpx; border-radius:16rpx; display:flex; align-items:center; justify-content:center; background:rgba(255,255,255,0.20); color:#fff; font-size:35rpx; line-height:64rpx; box-shadow:inset 0 0 0 1rpx rgba(255,255,255,0.32); flex-shrink:0; text-align:center; }
.cta-copy { flex:1; min-width:0; display:flex; flex-direction:column; align-items:flex-start; justify-content:center; }
.cta-main { display:block; font-size:31rpx; font-weight:900; line-height:1.22; color:#fff; }
.cta-sub { display:block; font-size:23rpx; color:rgba(255,255,255,0.78); margin-top:6rpx; line-height:1.35; }
.cta-arrow { width:54rpx; height:54rpx; line-height:50rpx; border-radius:50%; background:rgba(255,255,255,0.92); color:#315bff; font-size:54rpx; font-weight:300; text-align:center; flex-shrink:0; }
.cta-btn.dim .cta-sub { color:rgba(255,255,255,0.74); }

/* ── Analyze steps ── */
.analyze-steps { background:radial-gradient(circle at 12% 8%,rgba(91,141,255,0.30),transparent 32%),radial-gradient(circle at 86% 86%,rgba(28,105,255,0.20),transparent 32%),linear-gradient(135deg,#061946,#0b2c71 54%,#08225e); border:1rpx solid rgba(116,173,255,0.24); border-radius:20rpx; padding:22rpx 22rpx 18rpx; margin-top:16rpx; box-shadow:0 16rpx 34rpx rgba(8,21,39,0.20),inset 0 1rpx 0 rgba(197,221,255,0.14); position:relative; overflow:hidden; }
.analyze-steps::before { content:''; position:absolute; inset:0; opacity:0.22; background:linear-gradient(rgba(116,173,255,0.12) 1rpx,transparent 1rpx),linear-gradient(90deg,rgba(116,173,255,0.12) 1rpx,transparent 1rpx); background-size:32rpx 32rpx; }
.analyze-steps::after { content:''; position:absolute; left:-24%; right:-24%; top:-60rpx; height:90rpx; background:linear-gradient(180deg,transparent,rgba(116,173,255,0.16),transparent); transform:rotate(7deg); animation:matrixScan 2.8s linear infinite; }
.as-head { position:relative; z-index:1; display:flex; align-items:flex-start; justify-content:space-between; gap:18rpx; margin-bottom:14rpx; }
.as-kicker { display:block; color:rgba(168,207,255,0.82); font-size:18rpx; line-height:1; font-weight:900; }
.as-title { display:block; margin-top:8rpx; color:#ffffff; font-size:28rpx; line-height:1.2; font-weight:900; }
.as-percent { color:#8ec5ff; font-size:42rpx; line-height:1; font-weight:900; text-shadow:0 0 18rpx rgba(80,139,255,0.28); flex-shrink:0; }
.as-progress { position:relative; z-index:1; height:12rpx; margin-bottom:14rpx; border-radius:999rpx; overflow:hidden; background:rgba(11,36,88,0.86); border:1rpx solid rgba(116,173,255,0.26); }
.as-progress-fill { height:100%; border-radius:999rpx; background:linear-gradient(90deg,#4f8cff,#8ec5ff,#c6ddff); box-shadow:0 0 24rpx rgba(80,139,255,0.36); transition:width 0.25s ease; }
.as-step { position:relative; z-index:1; display:flex; align-items:flex-start; padding:10rpx 0; }
.as-step.pending .as-icon,.as-step.pending .as-label { color:rgba(205,225,255,0.42); }
.as-step.active .as-icon { color:#ffffff; background:#4f8cff; box-shadow:0 0 18rpx rgba(80,139,255,0.32); }
.as-step.active .as-label { color:#ffffff; font-weight:900; }
.as-step.done .as-icon { color:#ffffff; background:#315bff; }
.as-step.done .as-label { color:#c6ddff; }
.as-icon { width:42rpx; height:42rpx; line-height:42rpx; border-radius:12rpx; font-size:18rpx; font-weight:900; text-align:center; flex-shrink:0; margin-right:14rpx; background:rgba(198,221,255,0.12); color:rgba(205,225,255,0.62); }
.as-body { flex:1; min-width:0; }
.as-label { font-size:26rpx; color:rgba(205,225,255,0.72); display:block; line-height:1.35; }
.as-msg { font-size:22rpx; color:rgba(168,207,255,0.60); display:block; margin-top:4rpx; line-height:1.35; }

/* ── Features ── */
.features { display:flex; gap:0; margin:24rpx 28rpx 0; padding:24rpx 12rpx; background:linear-gradient(180deg,#ffffff,#fbfdff); border:1rpx solid rgba(219,230,255,0.92); border-radius:22rpx; box-shadow:0 18rpx 38rpx rgba(79,119,186,0.10); }
.ft { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:flex-start; gap:9rpx; text-align:center; background:transparent; border-radius:0; padding:8rpx 10rpx; box-shadow:none; border-right:1rpx solid rgba(219,230,255,0.78); min-width:0; }
.ft:last-child { border-right:0; }
.ft-mark { display:block; width:54rpx; height:54rpx; line-height:54rpx; text-align:center; border-radius:16rpx; color:#fff; background:linear-gradient(135deg,#2f6dff,#5b4be6); font-size:28rpx; flex-shrink:0; box-shadow:0 10rpx 20rpx rgba(88,105,255,0.16); }
.ft:nth-child(3) .ft-mark { background:linear-gradient(135deg,#f8c861,#d8a23d); box-shadow:0 10rpx 20rpx rgba(216,162,61,0.18); }
.ft-title { font-size:25rpx; font-weight:900; color:#17244e; display:block; white-space:nowrap; line-height:1.15; }
.ft-desc { display:block; font-size:22rpx; color:#8b99b6; line-height:1.3; }
.footer { text-align:center; font-size:22rpx; color:#8b99b6; padding:44rpx 44rpx 44rpx; line-height:1.65; }

/* ── Welcome modal ── */
.welcome-mask { position:fixed; inset:0; background:rgba(0,0,0,0.5); z-index:500; display:flex; align-items:center; justify-content:center; }
.welcome-modal { width:580rpx; background:#fff; border-radius:20rpx; padding:48rpx 32rpx; text-align:center; }
.wm-icon { font-size:80rpx; } .wm-title { font-size:32rpx; font-weight:800; color:#1e293b; margin-top:16rpx; } .wm-body { font-size:26rpx; color:#64748b; margin-top:12rpx; line-height:1.5; }
.wm-btn { width:100%; background:linear-gradient(135deg,#315bff,#0b3fbd); color:#fff; border-radius:16rpx; font-size:30rpx; font-weight:900; padding:22rpx 0; margin-top:28rpx; }

/* ── Banners ── */
.free-banner { background:#fef3c7; padding:16rpx 24rpx; text-align:center; font-size:24rpx; color:#92400e; }
.ann-banner { background:#dbeafe; padding:16rpx 24rpx; text-align:center; font-size:24rpx; color:#1e40af; }

/* ── Tab panels ── */
.tab-panel { min-height:100vh; background:#dce4f2; }
.sub-tab-panel { min-height:100vh; background:#dce4f2; padding-bottom:0; }
.tab-panel[style*="display: none"] { background:#dce4f2; }

/* ── Custom tabbar ── */
.custom-tabbar { position:fixed; bottom:0; left:0; right:0; height:88rpx; background:#fff; display:flex; border-top:1rpx solid #dbe5f2; padding-bottom:env(safe-area-inset-bottom); z-index:100; box-shadow:0 -6rpx 18rpx rgba(51,83,139,0.07); }
.ctb-item { flex:1; position:relative; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:3rpx; min-width:0; }
.ctb-item.active::before { content:''; position:absolute; top:0; left:50%; width:38rpx; height:4rpx; margin-left:-19rpx; border-radius:0 0 999rpx 999rpx; background:#315bff; }
.ctb-icon-wrap { width:40rpx; height:38rpx; display:flex; align-items:center; justify-content:center; }
.ctb-icon { width:36rpx; height:36rpx; display:block; }
.ctb-label { font-size:22rpx; color:#8b99b6; line-height:1; font-weight:800; }
.ctb-item.active .ctb-label { color:#315bff; font-weight:900; }
</style>

<style>
page { height: auto; background-color:#dce4f2; }
</style>
