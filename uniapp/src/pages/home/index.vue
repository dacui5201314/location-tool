<template>
  <view class="home-page">
    <!-- Hero -->
    <view class="hero">
      <view class="hero-brand">址得选</view>
      <view class="hero-tagline">AI帮你判断<text class="hl">这个位置能不能</text><text class="gold">赚钱</text></view>
      <view class="hero-sub">智能选址 · 科学决策 · 降低风险</view>
    </view>

    <!-- 分析面板 -->
    <view class="panel">
      <!-- 地址输入 -->
      <view class="section">
        <view class="section-head">
          <text class="section-title">门店地址</text>
          <text class="section-hint" v-if="!addressText">选择位置后，可一键收藏地址</text>
        </view>
        <view class="input-row">
          <input class="field" v-model="addressKeyword" placeholder="输入地址搜索或在地图上选点" :disabled="analyzing" @input="onAddressInput" />
          <button class="s-btn" :disabled="analyzing || !addressKeyword" @tap="onSearch">搜索</button>
        </view>
        <!-- 候选列表 -->
        <view class="suggest-diag" v-if="suggestDiag">{{ suggestDiag }}</view>
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
          <text class="ap-star" @tap="toggleFav">{{ isFaved ? '★' : '☆' }}</text>
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
          <text class="mhb-text">已选坐标 · 后续将接入地址解析</text>
        </view>
        <view class="map-diag" v-if="mapDiag">{{ mapDiag }}</view>
      </view>

      <!-- 选择业态 -->
      <view class="section">
        <view class="section-head">
          <text class="section-title">选择业态</text>
          <text class="section-link">全部业态 ›</text>
        </view>
        <text class="field-err" v-if="industryLoadErr">{{ industryLoadErr }}</text>
        <IndustryPicker :selected="industry" :disabled="analyzing" :industries="industryList" @change="onIndustryChange" />
        <text class="field-err" v-if="errors.industry">{{ errors.industry }}</text>
      </view>

      <!-- 经营画像 -->
      <view class="section">
        <view class="section-head">
          <text class="section-title">经营画像</text>
          <text class="section-hint">品牌与面积越清晰，报告越准</text>
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
      <button class="analyze-btn" :disabled="analyzing" @tap="onAnalyze">
        <text class="ab-mark">✦</text>
        <view class="ab-text">
          <text class="ab-strong">分析接口联调未开放</text>
          <text class="ab-em">填写完成后等待分析接口联调</text>
        </view>
      </button>

      <!-- 信任行 -->
      <view class="trust-row">
        <view class="trust-item" v-for="t in trusts" :key="t.title">
          <text class="ti-icon">{{ t.icon }}</text>
          <text class="ti-title">{{ t.title }}</text>
          <text class="ti-desc">{{ t.desc }}</text>
        </view>
      </view>
    </view>

    <!-- 页脚 -->
    <view class="footer">数据底座：全网多维度商业 POI 聚合数据库 | 仅供参考，实际决策请结合实地考察与多方因素</view>
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
      isFaved: false,
      selectedLocationSource: '',
      showUserLocation: false,
      mapDiag: '',
      suggestions: [],
      suggestErr: '',
      suggestDiag: '',
      industryLoadErr: '',
      errors: { address: '', industry: '', brand: '', size: '' },
      industryList: [],
      trusts: [
        { icon: '✓', title: '权威数据来源', desc: '多渠道数据融合' },
        { icon: '◈', title: 'AI智能分析', desc: '多维度模型算法' },
        { icon: '◆', title: '专业团队支持', desc: '7×24小时服务' }
      ]
    }
  },
  computed: {
    canAnalyze () { return !this.analyzing && this.addressText && this.industry && this.brandName && this.storeSize },
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
  mounted () {
    api.fetchIndustries().then(r => {
      if (r.ok && Array.isArray(r.data?.industries)) this.industryList = r.data.industries
    }).catch(() => { this.industryLoadErr = '业态加载失败，请确认后端服务已启动' })
  },
  methods: {
    async resolveAddressByLngLat (lng, lat, source) {
      this.selectedLocationSource = source
      try {
        const r = await api.locationRegeocode(lng, lat)
        if (r.ok && r.data?.ok && r.data?.data?.address) {
          this.addressText = r.data.data.address
          this.addressKeyword = r.data.data.address
          this.mapDiag = `地址解析: ${r.data.data.address}`
        } else {
          const coord = `经度 ${lng.toFixed(4)} · 纬度 ${lat.toFixed(4)}`
          this.addressText = coord; this.addressKeyword = coord
          this.mapDiag = '地址解析失败，可继续手动输入'
        }
      } catch (e) {
        const msg = e.errMsg || e.message || ''
        const coord = `经度 ${lng.toFixed(4)} · 纬度 ${lat.toFixed(4)}`
        this.addressText = coord; this.addressKeyword = coord
        this.mapDiag = msg.includes('timeout') ? '请求超时，请确认后端服务可访问' : '后端服务未连接，请确认 http://127.0.0.1:8000/api/health 可访问'
      }
    },
    onIndustryChange (name) {
      // 安全兼容：字符串直接存；对象取 name/title/label/value 字段
      if (typeof name === 'string') this.industry = name
      else if (name && typeof name === 'object') this.industry = name.name || name.title || name.label || name.value || ''
      else this.industry = ''
      if (this.industry) this.errors.industry = ''
    },
    onAddressInput () {
      this.errors.address = ''
      // 用户手动输入时清空地图旧选点，让候选列表可见
      if (this.addressKeyword && this.addressText && this.selectedLocationSource) {
        this.addressText = ''
        this.selectedLocationSource = ''
        this.showUserLocation = false
      }
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
              ? '定位超时，请检查微信开发者工具定位模拟/系统定位服务，也可直接输入地址搜索。'
              : `错误：${msg || '未知'}\n请检查开发者工具定位模拟/系统定位服务。也可直接输入地址。`
            uni.showModal({ title, content, showCancel: false })
          }
        })
      }

      uni.getSetting({
        success: (res) => {
          const authVal = res.authSetting['scope.userLocation']
          if (authVal === false) {
            uni.showModal({
              title: '定位权限状态：已拒绝',
              content: `authSetting.scope.userLocation = false。请去设置中开启。`,
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
              fail: (err) => {
                uni.showModal({
                  title: '定位授权失败',
                  content: `authorize 失败: ${err.errMsg || '未知'}。也可直接输入地址搜索。`,
                  showCancel: false
                })
              }
            })
          }
        },
        fail: () => doGetLocation()
      })
    },
    async onSearch () {
      const kw = this.addressKeyword.trim()
      if (!kw) return
      this.suggestions = []; this.suggestErr = ''; this.suggestDiag = `搜索中: ${kw}...`
      try {
        const r = await api.locationSuggest(kw)
        this.suggestDiag = `关键词: ${kw} | HTTP ${r.statusCode} | 候选: ${(r.data?.data||[]).length} 条`
        if (!r.ok) {
          const detail = r.data?.detail || r.data?.error || ''
          if (r.statusCode === 503) this.suggestErr = '地图服务未配置，请联系管理员'
          else if (r.statusCode === 502) this.suggestErr = '地图服务暂时不可用，请稍后重试'
          else this.suggestErr = detail || '搜索失败，请重试'
        } else if (r.data?.ok === false) {
          this.suggestErr = r.data.error || '搜索失败'
        } else if (r.data?.data?.length) {
          this.suggestions = r.data.data
        } else {
          this.suggestErr = `未找到匹配地址：${kw}`
        }
      } catch (e) {
        const msg = e.errMsg || e.message || ''
        if (msg.includes('timeout')) {
          this.suggestErr = '请求超时，请确认后端服务可访问'; this.suggestDiag = `timeout: ${msg}`
        } else {
          this.suggestErr = '后端服务未连接，请确认 http://127.0.0.1:8000/api/health 可访问'; this.suggestDiag = `网络错误: ${msg || e}`
        }
      }
    },
    onSelectSuggestion (s) {
      this.addressText = s.name + (s.address ? ' · ' + s.address : '')
      this.addressKeyword = this.addressText
      if (s.location) { this.mapLng = s.location.lng; this.mapLat = s.location.lat }
      this.selectedLocationSource = 'search'
      this.errors.address = ''
      this.suggestions = []
      this.suggestErr = ''
      this.suggestDiag = ''
    },
    onMapRegionChange (e) {
      if (e && e.type === 'end') this.mapDiag = '地图已拖动/缩放 (regionchange end)'
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
    toggleFav () { this.isFaved = !this.isFaved; uni.showToast({ title: this.isFaved ? '收藏成功' : '已取消收藏', icon: 'none' }) },
    clearAddress () {
      this.addressText = ''
      this.addressKeyword = ''
      this.isFaved = false
      this.selectedLocationSource = ''
      this.showUserLocation = false
      this.mapDiag = ''
      this.suggestions = []
      this.suggestErr = ''
      this.suggestDiag = ''
      this.errors.address = ''
    },
    validate () {
      const e = { address: '', industry: '', brand: '', size: '' }; let ok = true
      if (!this.addressText) { e.address = '请选择门店地址'; ok = false }
      if (!this.industry) { e.industry = '请选择业态'; ok = false }
      if (!this.brandName || !this.brandName.trim()) { e.brand = '请输入品牌或特色'; ok = false }
      const sz = parseFloat(this.storeSize)
      if (isNaN(sz) || sz <= 0) { e.size = '面积必须为正数'; ok = false } else if (sz < 5) { e.size = '面积不能小于 5 ㎡'; ok = false } else if (sz > 5000) { e.size = '面积数值较大，请确认'; ok = false }
      this.errors = e; return ok
    },
    onAnalyze () {
      if (!this.validate()) {
        const firstErr = Object.values(this.errors).find(e => e)
        if (firstErr) uni.showToast({ title: firstErr, icon: 'none' })
        return
      }
      uni.showToast({ title: '分析接口联调未开放', icon: 'none', duration: 2000 })
    }
  }
}
</script>

<style scoped>
.home-page { min-height:100vh; background:#eef3f9; padding-bottom:60rpx; }
.hero { background:linear-gradient(135deg,#02091d,#071843); padding:80rpx 32rpx 90rpx; text-align:center; }
.hero-brand { font-size:44rpx; font-weight:800; color:rgba(255,255,255,0.95); }
.hero-tagline { font-size:38rpx; font-weight:800; color:#fff; margin-top:16rpx; line-height:1.4; }
.hl { color:rgba(255,255,255,0.8); } .gold { color:#55e7ff; }
.hero-sub { font-size:24rpx; color:rgba(255,255,255,0.55); margin-top:12rpx; }

.panel { background:#fff; border-radius:24rpx; padding:36rpx 28rpx; margin:-40rpx 20rpx 32rpx; box-shadow:0 4rpx 32rpx rgba(9,24,54,0.10); }
.section { margin-bottom:32rpx; }
.section-head { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:12rpx; }
.section-title { font-size:28rpx; font-weight:700; color:#111827; }
.section-link { font-size:24rpx; color:#246bff; }
.section-hint { font-size:22rpx; color:#667085; }
.label { font-size:26rpx; font-weight:600; color:#334155; margin-bottom:8rpx; }
.req { color:#ef4444; }
.field-err { font-size:22rpx; color:#dc2626; margin-top:6rpx; display:block; }
.input-row { display:flex; gap:10rpx; }
.field { flex:1; border:2rpx solid #e2e8f0; border-radius:14rpx; padding:18rpx 14rpx; font-size:28rpx; background:#fff; }
.s-btn { background:linear-gradient(135deg,#0f172a,#1e40af); color:#fff; border-radius:14rpx; padding:0 28rpx; font-size:28rpx; line-height:80rpx; font-weight:600; }
.suggest-list { background:#fff; border-radius:14rpx; margin-top:8rpx; box-shadow:0 4rpx 20rpx rgba(0,0,0,0.08); max-height:400rpx; overflow-y:auto; } .suggest-item { padding:22rpx 20rpx; border-bottom:1rpx solid #f1f5f9; } .sg-name { font-size:28rpx; color:#1e293b; display:block; } .sg-addr { font-size:22rpx; color:#94a3b8; margin-top:4rpx; display:block; } .suggest-empty { padding:20rpx; font-size:24rpx; color:#94a3b8; text-align:center; }
.locate-row { margin-top:12rpx; } .locate-btn { width:100%; background:#f1f5f9; color:#334155; border-radius:14rpx; font-size:28rpx; padding:18rpx 0; }
.addr-pick { display:flex; align-items:center; margin-top:12rpx; padding:16rpx; background:#f0fdf4; border:1rpx solid #bbf7d0; border-radius:14rpx; }
.ap-mid { flex:1; display:flex; flex-direction:column; margin-left:8rpx; } .ap-text { font-size:26rpx; color:#166534; } .ap-src { font-size:20rpx; color:#94a3b8; margin-top:2rpx; } .ap-star { font-size:36rpx; color:#d6a84f; padding:0 8rpx; } .ap-clear { font-size:28rpx; color:#94a3b8; padding:0 4rpx; }
.map-view { width:100%; height:380rpx; border-radius:16rpx; margin-top:12rpx; }
.map-center-marker { position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); pointer-events:none; z-index:10; }
.mcm-pin { font-size:40rpx; }
.map-hint-bar { background:#f1f5f9; border-radius:12rpx; padding:14rpx 20rpx; margin-top:8rpx; text-align:center; }
.map-hint-bar.selected { background:#f0fdf4; border:1rpx solid #bbf7d0; }
.mhb-text { font-size:24rpx; color:#64748b; }
.map-diag { font-size:20rpx; color:#94a3b8; padding:4rpx 0; text-align:center; }
.suggest-diag { font-size:20rpx; color:#64748b; padding:8rpx 0; }
.dual { display:flex; gap:14rpx; } .dual-half { flex:1; }

.analyze-btn { margin-top:8rpx; width:100%; background:linear-gradient(135deg,#0f172a,#1e40af); color:#fff; border-radius:18rpx; padding:24rpx 20rpx; display:flex; align-items:center; gap:14rpx; }
.analyze-btn[disabled] { opacity:0.45; }
.ab-mark { font-size:40rpx; } .ab-text { display:flex; flex-direction:column; text-align:left; }
.ab-strong { font-size:30rpx; font-weight:800; }
.ab-em { font-size:22rpx; color:rgba(255,255,255,0.7); margin-top:4rpx; }

.trust-row { display:flex; justify-content:space-around; margin-top:28rpx; padding-top:20rpx; border-top:1rpx solid #f1f5f9; }
.trust-item { display:flex; flex-direction:column; align-items:center; }
.ti-icon { font-size:32rpx; color:#246bff; } .ti-title { font-size:22rpx; font-weight:600; color:#334155; margin-top:4rpx; } .ti-desc { font-size:22rpx; color:#667085; margin-top:4rpx; }
.footer { text-align:center; font-size:20rpx; color:#94a3b8; padding:20rpx 32rpx; line-height:1.6; }
</style>
