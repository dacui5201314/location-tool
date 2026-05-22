<template>
  <view class="profile-page">
    <!-- Top section — 对齐 Web ProfileView -->
    <view class="top">
      <text class="avatar-fb">👤</text>
      <text class="uname">{{ loggedIn ? (userName || '用户') : '未登录' }}</text>
      <text class="uid" v-if="loggedIn && uidText">{{ uidText }}</text>
      <button v-if="!loggedIn" class="top-login" @tap="onLogin">{{ loginLoading ? '登录中...' : '微信一键登录' }}</button>
      <text class="login-err" v-if="loginErr">{{ loginErr }}</text>
      <view class="top-hints" v-if="loggedIn">
        <text class="th-text">微信头像/昵称需用户主动授权填写</text>
        <text class="th-text">手机号需用户授权绑定</text>
      </view>
    </view>

    <!-- Stats panel -->
    <view class="stats">
      <view class="stat" v-for="s in stats" :key="s.label">
        <text class="sv">{{ s.value }}</text>
        <text class="sl">{{ s.label }}</text>
        <text class="ss">{{ s.sub }}</text>
      </view>
    </view>

    <!-- VIP card -->
    <view class="vip-card">
      <view class="vc-top">
        <view>
          <text class="vc-title">VIP会员 {{ memberDays > 0 ? memberDays+'天' : '未开通' }}</text>
          <text class="vc-desc">{{ memberDays > 0 ? '有效期至 '+memberExpiry : '开通会员，解锁全部高级功能' }}</text>
        </view>
        <button class="vc-btn" @tap="onUpgrade">{{ memberDays > 0 ? '立即续费' : '立即开通' }}</button>
      </view>
      <view class="vc-benefits">
        <view class="vb" v-for="b in benefits" :key="b.label">
          <text class="vb-icon">{{ b.icon }}</text>
          <text class="vb-label">{{ b.label }}</text>
          <text class="vb-desc">{{ b.desc }}</text>
        </view>
      </view>
    </view>

    <!-- Points card -->
    <view class="points-card">
      <view class="pc-head">
        <text class="pc-title">● 我的点数</text>
        <view class="pc-actions">
          <text class="pca" @tap="onCDK">兑换码</text>
          <text class="pca primary" @tap="onBuy">获取点数</text>
        </view>
      </view>
      <view class="pc-body">
        <text class="pc-num">{{ points }}</text>
        <text class="pc-unit">点</text>
        <text class="pc-desc">当前剩余点数 · 可用于生成选址分析报告</text>
      </view>
      <view class="pc-flow">
        <view class="pf" v-for="s in flowSteps" :key="s.label">
          <text class="pf-icon">{{ s.icon }}</text>
          <text class="pf-label">{{ s.label }}</text>
        </view>
      </view>
      <view class="pc-warn" v-if="!memberDays && points <= 3">
        <text>点数即将用完，建议充值或开通会员</text>
      </view>
    </view>

    <!-- Menu card -->
    <view class="menu-card">
      <view class="menu-item" @tap="onUpgrade">
        <text class="mi-icon">◇</text>
        <view class="mi-body"><text class="mi-label">会员权益</text><text class="mi-desc">了解会员特权</text></view>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" @tap="onCS">
        <text class="mi-icon">☎</text>
        <view class="mi-body"><text class="mi-label">联系客服</text><text class="mi-desc">专属客服支持</text></view>
        <text class="mi-arrow">›</text>
      </view>
      <view class="menu-item" v-if="loggedIn" @tap="onLogout">
        <text class="mi-icon">🚪</text>
        <view class="mi-body"><text class="mi-label">退出登录</text></view>
        <text class="mi-arrow">›</text>
      </view>
    </view>

    <view class="footer">(c) 2026 AI 选址初筛参考工具</view>
  </view>
</template>

<script>
import auth from '../../utils/auth'
import api from '../../utils/api'
import { maskOpenid } from '../../utils/format'

export default {
  data () {
    return {
      loggedIn: false,
      loginLoading: false,
      loginErr: '',
      userName: '',
      uidText: '',
      points: 3,
      memberDays: 0,
      memberExpiry: '',
      reportCount: 0,
      favCount: 0,
      benefits: [
        { icon:'∞',label:'无限分析',desc:'次数不限' },{ icon:'PDF',label:'PDF导出',desc:'高清报告' },
        { icon:'⌁',label:'盈利预测',desc:'精准估算' },{ icon:'◎',label:'高级模型',desc:'多维评估' },
        { icon:'▥',label:'数据对比',desc:'深度分析' },{ icon:'☎',label:'专属客服',desc:'优先服务' }
      ],
      flowSteps: [{ icon:'⌖',label:'选地址' },{ icon:'✚',label:'AI分析' },{ icon:'▤',label:'生成报告' },{ icon:'↓',label:'导出使用' }]
    }
  },
  computed: {
    stats () {
      return [
        { value: this.points, label: '剩余点数', sub: '可用点数' },
        { value: this.reportCount, label: '已生成报告', sub: '累计分析' },
        { value: this.favCount, label: '收藏地址', sub: '机会池' }
      ]
    }
  },
  onShow () { this.refreshState() },
  methods: {
    refreshState () {
      const token = auth.getToken()
      if (token) {
        const user = auth.getUser() || {}
        this.loggedIn = true
        this.points = user.balance_credits ?? 3
        this.userName = user.nickname || user.name || ''
        this.uidText = user.id ? '用户编号：' + user.id : ''
        this.memberDays = user.membership_days_left || 0
        this.memberExpiry = user.membership_expiry || ''
        // fetch最新 profile
        api.fetchProfile().then(r => {
          if (r.ok && r.data) {
            const p = r.data
            this.points = p.balance_credits ?? this.points
            this.memberDays = p.membership_days_left ?? this.memberDays
            this.memberExpiry = p.membership_expiry || this.memberExpiry
            this.reportCount = p.total_reports ?? 0
            this.favCount = p.favorite_count ?? 0
            auth.setUser(p)
          }
        }).catch(() => {})
      } else {
        this.loggedIn = false
      }
    },
    onLogin () {
      this.loginLoading = true; this.loginErr = ''
      auth.wechatLogin().then(r => {
        this.loginLoading = false
        if (r.ok) {
          this.refreshState()
        } else {
          const sc = r.statusCode
          if (sc === 503) this.loginErr = '小程序登录未配置，请先在管理后台配置小程序凭据'
          else if (sc === 400) this.loginErr = '微信登录参数无效，请重新尝试'
          else if (sc === 409) this.loginErr = '微信身份已绑定其他账号'
          else if (sc) this.loginErr = '登录失败 (HTTP ' + sc + ')，请重试'
          else this.loginErr = '登录失败，未收到服务端状态码，请确认后端日志'
        }
      }).catch(() => {
        this.loginLoading = false
        this.loginErr = '网络异常，请确认后端服务 http://127.0.0.1:8000 可访问'
      })
    },
    onLogout () {
      auth.clearToken()
      this.loggedIn = false; this.points = 3; this.reportCount = 0; this.favCount = 0
    },
    onUpgrade () { uni.showToast({ title: '会员充值接入中', icon: 'none' }) },
    onCDK () { uni.showToast({ title: '兑换码接入中', icon: 'none' }) },
    onBuy () { uni.showToast({ title: '点数购买接入中', icon: 'none' }) },
    onCS () { uni.showToast({ title: '客服接入中', icon: 'none' }) }
  }
}
</script>

<style scoped>
.profile-page { min-height:100vh; background:#eef3f9; padding-bottom:60rpx; }
.top { background:linear-gradient(135deg,#02091d,#071843); padding:60rpx 32rpx 40rpx; text-align:center; color:#fff; }
.avatar-fb { font-size:80rpx; }
.uname { display:block; font-size:36rpx; font-weight:700; margin-top:12rpx; }
.uid { display:block; font-size:24rpx; color:rgba(255,255,255,0.6); margin-top:4rpx; }
.top-login { margin-top:28rpx; width:400rpx; background:#07c160; color:#fff; border-radius:40rpx; font-size:32rpx; font-weight:600; padding:20rpx 0; }
.login-err { display:block; margin-top:14rpx; font-size:24rpx; color:#fca5a5; }
.top-hints { margin-top:18rpx; } .th-text { display:block; font-size:22rpx; color:rgba(255,255,255,0.5); text-align:center; padding:4rpx 0; }

.stats { display:flex; background:#fff; margin:-30rpx 24rpx 24rpx; border-radius:20rpx; padding:24rpx 0; box-shadow:0 4rpx 24rpx rgba(0,0,0,0.06); }
.stat { flex:1; text-align:center; }
.sv { display:block; font-size:36rpx; font-weight:800; color:#1e293b; } .sl { display:block; font-size:24rpx; color:#334155; font-weight:600; margin-top:4rpx; } .ss { display:block; font-size:20rpx; color:#94a3b8; margin-top:2rpx; }

.vip-card { background:linear-gradient(135deg,#1e293b,#0f172a); margin:0 24rpx 20rpx; border-radius:20rpx; padding:28rpx; color:#fff; }
.vc-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:24rpx; }
.vc-title { font-size:30rpx; font-weight:700; display:block; } .vc-desc { font-size:24rpx; color:rgba(255,255,255,0.7); display:block; margin-top:4rpx; }
.vc-btn { background:#d6a84f; color:#1e293b; border-radius:14rpx; font-size:26rpx; font-weight:700; padding:14rpx 28rpx; }
.vc-benefits { display:flex; flex-wrap:wrap; gap:16rpx; }
.vb { width:calc(33.3% - 12rpx); text-align:center; } .vb-icon { font-size:36rpx; display:block; } .vb-label { font-size:22rpx; display:block; margin-top:4rpx; } .vb-desc { font-size:20rpx; color:rgba(255,255,255,0.5); display:block; }

.points-card { background:#fff; margin:0 24rpx 20rpx; border-radius:20rpx; padding:28rpx; box-shadow:0 2rpx 16rpx rgba(0,0,0,0.04); }
.pc-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:20rpx; }
.pc-title { font-size:28rpx; font-weight:700; color:#1e293b; }
.pc-actions { display:flex; gap:12rpx; } .pca { font-size:24rpx; padding:8rpx 20rpx; border-radius:14rpx; background:#f1f5f9; color:#475569; } .pca.primary { background:#246bff; color:#fff; }
.pc-body { text-align:center; margin-bottom:24rpx; }
.pc-num { font-size:80rpx; font-weight:900; color:#1e293b; } .pc-unit { font-size:28rpx; color:#667085; }
.pc-desc { display:block; font-size:24rpx; color:#94a3b8; margin-top:8rpx; }
.pc-flow { display:flex; justify-content:space-around; padding:16rpx 0; border-top:1rpx solid #f1f5f9; }
.pf { text-align:center; } .pf-icon { font-size:32rpx; display:block; } .pf-label { font-size:20rpx; color:#667085; margin-top:4rpx; display:block; }
.pc-warn { margin-top:16rpx; padding:16rpx; background:#fef2f2; border-radius:12rpx; } .pc-warn text { font-size:24rpx; color:#dc2626; }

.menu-card { background:#fff; margin:0 24rpx 24rpx; border-radius:20rpx; }
.menu-item { display:flex; align-items:center; padding:28rpx; border-bottom:1rpx solid #f1f5f9; }
.mi-icon { font-size:36rpx; margin-right:16rpx; } .mi-body { flex:1; } .mi-label { font-size:28rpx; color:#1e293b; display:block; } .mi-desc { font-size:22rpx; color:#94a3b8; }
.mi-arrow { font-size:32rpx; color:#cbd5e1; }
.footer { text-align:center; font-size:20rpx; color:#cbd5e1; padding:24rpx; }
</style>
