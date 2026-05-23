<template>
  <view class="home-page">
    <!-- Hero -->
    <view class="hero">
      <view class="hero-brand">址得选</view>
      <view class="hero-tagline">AI帮你判断<text class="hl">这个位置能不能</text><text class="gold">开店</text></view>
      <view class="hero-sub">智能选址 · 科学决策 · 降低风险</view>
    </view>

    <!-- 分析面板 -->
    <view class="panel">
      <!-- 地址输入 -->
      <view class="section">
        <view class="section-head">
          <text class="section-title">门店地址</text>
        </view>
        <view class="input-row">
          <input class="field" :value="addressKeyword" placeholder="输入地址搜索或在地图上选点" :disabled="analyzing" @input="onAddressInput" @confirm="onSearch" />
          <button class="s-btn" :disabled="analyzing || !addressKeyword" @tap="onSearch">搜索</button>
        </view>
        <!-- 候选列表 -->
        <view class="suggest-list" v-if="suggestions.length">
          <view class="suggest-item" v-for="(s, i) in suggestions" :key="i" @tap="onSelectSuggestion(s)">
            <text class="sg-name">{{ s.name }}</text>
            <text class="sg-addr">{{ s.address }}</text>
          </view>
        </view>
        <view class="suggest-empty" v-if="suggestErr">{{ suggestErr }}</view>

        <view class="locate-row" v-if="!addressText">
          <button class="locate-btn" @tap="onLocate">📍 定位当前位置</button>
        </view>
        <view class="addr-pick" v-if="addressText">
          <text class="ap-pin">📍</text>
          <view class="ap-mid">
            <text class="ap-text">{{ addressText }}</text>
            <text class="ap-src" v-if="selectedLocationSource">来源：{{ srcLabel }}</text>
          </view>
          <text class="ap-clear" @tap="clearAddress">✕</text>
        </view>
        <text class="field-err" v-if="errors.address">{{ errors.address }}</text>
        <map
          class="map-view"
          :latitude="mapLat"
          :longitude="mapLng"
          scale="15"
          :show-location="showUserLocation"
          :enable-scroll="true"
          :enable-zoom="true"
          :enable-rotate="false"
          @tap="onMapTap"
          @regionchange="onMapRegionChange"
          @updated="onMapUpdated"
        >
          <view class="map-center-marker">
            <view class="mcm-pin">📍</view>
          </view>
        </map>
        <view class="map-hint-bar" v-if="!addressText">
          <text class="mhb-text">点击地图选点 · 或使用上方搜索框输入地址</text>
        </view>
        <view class="map-hint-bar selected" v-if="addressText">
          <text class="mhb-text">已选位置 · 点击地图可重新选点</text>
        </view>
        <view class="map-hint-bar" v-if="mapNotice">
          <text class="mhb-text warn">{{ mapNotice }}</text>
        </view>
      </view>

      <!-- 选择业态 -->
      <view class="section">
        <view class="section-head">
          <text class="section-title">选择业态</text>
        </view>
        <text class="field-err" v-if="industryLoadErr">{{ industryLoadErr }}</text>
        <IndustryPicker :selected="industry" :disabled="analyzing" :industries="industryList" @change="onIndustryChange" />
        <text class="field-err" v-if="errors.industry">{{ errors.industry }}</text>
      </view>

      <!-- 经营画像 -->
      <view class="section">
        <view class="section-head">
          <text class="section-title">经营画像</text>
        </view>
        <view class="dual">
          <view class="dual-half">
            <view class="label">品牌/特色 <text class="req">*</text></view>
            <input class="field" v-model="brandName" placeholder="品牌或主打特色" :disabled="analyzing" @input="onBrandInput" />
            <text class="field-err" v-if="errors.brand">{{ errors.brand }}</text>
          </view>
          <view class="dual-half">
            <view class="label">门店面积 <text class="req">*</text></view>
            <input class="field" v-model="storeSize" type="number" placeholder="㎡" :disabled="analyzing" @input="onSizeInput" />
            <text class="field-err" v-if="errors.size">{{ errors.size }}</text>
          </view>
        </view>
      </view>

      <!-- 分析按钮 -->
      <view class="analyze-zone">
        <button class="analyze-btn" :disabled="analyzing || !canAnalyze" @tap="onAnalyze">
          <text class="ab-mark">{{ analyzing ? '⏳' : '✦' }}</text>
          <view class="ab-text">
            <text class="ab-strong">{{ analyzing ? 'AI 分析中...' : '开始选址分析' }}</text>
            <text class="ab-em">{{ analyzing ? (analyzeStatus || '正在处理...') : '填写完成后点击开始分析' }}</text>
          </view>
        </button>
        <!-- 分析中步骤指示器（对齐 Web AnalysisLoadingPanel） -->
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

      <!-- 信任行 -->
      <view class="trust-row">
        <view class="trust-item" v-for="t in trusts" :key="t.title">
          <text class="ti-title">{{ t.title }}</text>
          <text class="ti-desc">{{ t.desc }}</text>
        </view>
      </view>
    </view>

    <!-- 页脚 -->
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
      suggestTimer: null,
      suggestLoading: false,
      suggestions: [],
      industryLoadErr: '',
      errors: { address: '', industry: '', brand: '', size: '' },
      industryList: [],
      trusts: [
        { title: '真实 POI 数据', desc: '高德地图实时采集' },
        { title: 'AI 商业评估', desc: '大模型多维度分析' },
        { title: '选址初筛参考', desc: '降低实地考察成本' }
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
  onHide () { this.clearAnalyzeTimer() },
  onUnload () { this.clearAnalyzeTimer() },
  mounted () {
    api.fetchIndustries().then(r => {
      if (r.ok && Array.isArray(r.data?.industries)) this.industryList = r.data.industries
    }).catch(() => { this.industryLoadErr = '业态加载失败，请稍后重试' })
  },
  methods: {
    async resolveAddressByLngLat (lng, lat, source) {
      this.selectedLocationSource = source
      try {
        const r = await api.locationRegeocode(lng, lat)
        if (r.ok && r.data?.ok && r.data?.data?.address) {
          this.addressText = r.data.data.address
          this.addressKeyword = r.data.data.address
          this.mapNotice = ''
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
.home-page { min-height:100vh; background:#eef3f9; padding-bottom:60rpx; }
.hero { background:linear-gradient(135deg,#0b1120 0%,#111f3a 50%,#0f1f3d 100%); padding:72rpx 32rpx 80rpx; text-align:center; }
.hero-brand { font-size:42rpx; font-weight:800; color:#fff; }
.hero-tagline { font-size:36rpx; font-weight:700; color:rgba(255,255,255,0.9); margin-top:14rpx; line-height:1.4; }
.hl { color:rgba(255,255,255,0.7); } .gold { color:#60a5fa; }
.hero-sub { font-size:24rpx; color:rgba(255,255,255,0.45); margin-top:10rpx; }

.panel { background:#fff; border-radius:20rpx; padding:32rpx 24rpx; margin:-36rpx 16rpx 28rpx; box-shadow:0 2rpx 24rpx rgba(9,24,54,0.08); }
.section { margin-bottom:28rpx; }
.section:last-child { margin-bottom:0; }
.section-head { margin-bottom:12rpx; }
.section-title { font-size:28rpx; font-weight:700; color:#111827; }
.label { font-size:26rpx; font-weight:600; color:#334155; margin-bottom:8rpx; }
.req { color:#ef4444; font-size:24rpx; }
.field-err { font-size:22rpx; color:#dc2626; margin-top:6rpx; display:block; }
.input-row { display:flex; gap:12rpx; }
.field { flex:1; border:1px solid #e2e8f0; border-radius:12rpx; padding:18rpx 16rpx; font-size:28rpx; background:#fff; color:#1e293b; }
.s-btn { background:#0f172a; color:#fff; border-radius:12rpx; padding:0 28rpx; font-size:28rpx; line-height:80rpx; font-weight:600; }
.s-btn[disabled] { opacity:0.4; }
.suggest-list { background:#fff; border-radius:12rpx; margin-top:8rpx; box-shadow:0 4rpx 20rpx rgba(0,0,0,0.08); max-height:400rpx; overflow-y:auto; } .suggest-item { padding:22rpx 20rpx; border-bottom:1rpx solid #f1f5f9; } .sg-name { font-size:28rpx; color:#1e293b; display:block; } .sg-addr { font-size:22rpx; color:#94a3b8; margin-top:4rpx; display:block; } .suggest-empty { padding:20rpx; font-size:24rpx; color:#94a3b8; text-align:center; }
.locate-row { margin-top:12rpx; } .locate-btn { width:100%; background:#f8fafc; color:#475569; border:1px solid #e2e8f0; border-radius:12rpx; font-size:28rpx; padding:18rpx 0; }
.addr-pick { display:flex; align-items:center; margin-top:12rpx; padding:14rpx 16rpx; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:12rpx; }
.ap-mid { flex:1; display:flex; flex-direction:column; margin-left:4rpx; } .ap-text { font-size:26rpx; color:#166534; } .ap-src { font-size:20rpx; color:#94a3b8; margin-top:2rpx; } .ap-clear { font-size:28rpx; color:#94a3b8; padding:0 4rpx; }
.map-view { width:100%; height:380rpx; border-radius:14rpx; margin-top:12rpx; }
.map-center-marker { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); pointer-events:none; z-index:10; }
.mcm-pin { font-size:40rpx; }
.map-hint-bar { background:#f8fafc; border:1px solid #e2e8f0; border-radius:10rpx; padding:12rpx 16rpx; margin-top:8rpx; text-align:center; }
.map-hint-bar.selected { background:#f0fdf4; border-color:#bbf7d0; }
.mhb-text { font-size:24rpx; color:#64748b; } .mhb-text.warn { color:#dc2626; }
.dual { display:flex; gap:14rpx; } .dual-half { flex:1; }

.analyze-zone { margin-top:4rpx; }
.analyze-btn { width:100%; background:linear-gradient(135deg,#0f172a,#1e3a5f); color:#fff; border-radius:14rpx; padding:22rpx 20rpx; display:flex; align-items:center; justify-content:center; gap:10rpx; border:none; }
.analyze-btn[disabled] { opacity:0.35; }
.analyze-steps { background:#f8fafc; border:1px solid #e2e8f0; border-radius:12rpx; padding:20rpx; margin-top:12rpx; }
.as-step { display:flex; align-items:flex-start; padding:6rpx 0; }
.as-step.pending .as-icon, .as-step.pending .as-label { color:#cbd5e1; }
.as-step.active .as-icon { color:#2563eb; } .as-step.active .as-label { color:#1e293b; font-weight:600; }
.as-step.done .as-icon { color:#16a34a; } .as-step.done .as-label { color:#475569; }
.as-icon { width:44rpx; font-size:28rpx; text-align:center; flex-shrink:0; margin-right:10rpx; line-height:34rpx; }
.as-body { flex:1; } .as-label { font-size:25rpx; color:#475569; display:block; } .as-msg { font-size:22rpx; color:#94a3b8; display:block; }
.ab-mark { font-size:36rpx; } .ab-text { display:flex; flex-direction:column; text-align:left; }
.ab-strong { font-size:28rpx; font-weight:700; }
.ab-em { font-size:22rpx; color:rgba(255,255,255,0.6); margin-top:2rpx; }

.trust-row { display:flex; justify-content:center; gap:48rpx; margin-top:20rpx; padding-top:20rpx; border-top:1px solid #e2e8f0; }
.trust-item { display:flex; flex-direction:column; align-items:center; }
.ti-title { font-size:24rpx; font-weight:600; color:#475569; } .ti-desc { font-size:22rpx; color:#94a3b8; margin-top:2rpx; }
.footer { text-align:center; font-size:22rpx; color:#94a3b8; padding:20rpx 32rpx; line-height:1.6; }
</style>
