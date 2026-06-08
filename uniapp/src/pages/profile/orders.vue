<template>
  <view class="page">
    <view class="header">
      <text class="brand">址得选</text>
      <text class="title">充值记录</text>
      <text class="subtitle">订单、支付、退款状态统一在这里查看</text>
    </view>

    <view class="list" v-if="orders.length">
      <view class="order-card" v-for="o in orders" :key="o.out_trade_no" @tap="goDetail(o.out_trade_no)">
        <view class="order-head">
          <view class="order-head-main">
            <text class="order-title">{{ o.sku_label || '套餐' }}</text>
            <text class="order-sub">订单 {{ shortNo(o.out_trade_no) }}</text>
          </view>
          <text class="status-pill" :class="statusClass(o.status)">{{ statusText(o.status) }}</text>
        </view>

        <view class="order-body">
          <view class="benefit-box">
            <text class="benefit-label">权益</text>
            <text class="benefit-value" :class="{ closed: isClosed(o.status), pending: isRefundPending(o.status) }">{{ benefitText(o) }}</text>
          </view>
          <view class="amount-box">
            <text class="amount">¥{{ o.amount_yuan || '0.00' }}</text>
            <text class="channel">{{ channelText(o) }}</text>
          </view>
        </view>

        <view class="order-meta">
          <text>创建 {{ fmt(o.created_at) }}</text>
          <text v-if="o.paid_at">支付 {{ fmt(o.paid_at) }}</text>
        </view>

        <view class="order-foot">
          <text class="detail-link">查看详情</text>
          <view class="actions">
            <button v-if="canContinue(o)" class="action-btn primary" @tap.stop="onContinuePay(o)">继续支付</button>
            <button v-if="canRefund(o)" class="action-btn danger" @tap.stop="onRefund(o)">申请退款</button>
            <text v-if="isRefundPending(o.status)" class="action-note">等待系统处理</text>
            <text v-if="o.status === 'REFUNDED'" class="action-note muted">退款已完成</text>
          </view>
        </view>
      </view>
    </view>

    <view class="empty" v-else>
      <view class="empty-icon">▤</view>
      <text class="empty-title">暂无充值记录</text>
      <text class="empty-desc">购买点数或会员后，订单会显示在这里</text>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'

export default {
  data () {
    return { orders: [] }
  },
  mounted () {
    this.loadOrders()
  },
  onPullDownRefresh () {
    Promise.resolve(this.loadOrders()).finally(() => uni.stopPullDownRefresh())
  },
  methods: {
    async loadOrders () {
      try {
        const r = await api.fetchMyOrders()
        if (r.ok && r.data) this.orders = r.data.orders || []
      } catch (e) {}
    },
    goDetail (no) {
      if (!no) return
      uni.navigateTo({ url: '/pages/profile/order-detail?order_no=' + encodeURIComponent(no) })
    },
    fmt (iso) {
      if (!iso) return '-'
      const text = String(iso).trim()
      const normalized = text.replace(' ', 'T')
      const m = normalized.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})/)
      let utcMs = NaN
      if (m) {
        const hasZone = /(?:Z|[+-]\d{2}:?\d{2})$/.test(normalized)
        utcMs = hasZone
          ? new Date(normalized).getTime()
          : Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]), Number(m[4]), Number(m[5]), Number(m[6]))
      } else {
        utcMs = new Date(normalized).getTime()
      }
      if (Number.isNaN(utcMs)) return text
      const d = new Date(utcMs + 8 * 60 * 60 * 1000)
      const pad = n => String(n).padStart(2, '0')
      return d.getUTCFullYear() + '-' + pad(d.getUTCMonth() + 1) + '-' + pad(d.getUTCDate()) + ' ' + pad(d.getUTCHours()) + ':' + pad(d.getUTCMinutes()) + ':' + pad(d.getUTCSeconds())
    },
    shortNo (no) {
      if (!no) return '-'
      return no.length > 18 ? no.slice(0, 10) + '...' + no.slice(-6) : no
    },
    statusText (status) {
      const map = {
        CREATED: '待支付',
        PAID: '已完成',
        REFUND_REQUESTED: '退款申请中',
        REFUNDING: '退款处理中',
        REFUNDED: '已退款 / 权益已关闭',
        CANCELLED: '已取消',
        TIMEOUT: '已关闭',
        FAILED: '已关闭'
      }
      return map[status] || status || '-'
    },
    statusClass (status) {
      if (status === 'PAID') return 'paid'
      if (status === 'CREATED') return 'created'
      if (this.isRefundPending(status)) return 'pending'
      if (this.isClosed(status)) return 'closed'
      return ''
    },
    isRefundPending (status) {
      return ['REFUND_REQUESTED', 'REFUNDING'].includes(status)
    },
    isClosed (status) {
      return ['REFUNDED', 'CANCELLED', 'TIMEOUT', 'FAILED'].includes(status)
    },
    benefitText (o) {
      if (this.isClosed(o.status)) return '权益已关闭'
      if (this.isRefundPending(o.status)) return '退款处理中'
      const parts = []
      if (o.credits) parts.push('+' + o.credits + '点')
      if (o.membership_days) parts.push(o.membership_days + '天会员')
      return parts.join(' / ') || '-'
    },
    channelText (o) {
      return '微信支付'
    },
    canContinue (o) {
      return o.status === 'CREATED' && o.pay_channel === 'WECHAT_VIRTUAL'
    },
    canRefund (o) {
      return o.status === 'PAID'
    },
    async onRefund (o) {
      const res = await new Promise(r => uni.showModal({ title: '确认退款', content: '退款后将关闭本订单权益，并扣回对应点数。确认申请退款？', success: r }))
      if (!res.confirm) return
      try {
        const r = await api.refundRequestVirtual(o.out_trade_no)
        if (r.ok) {
          const newStatus = (r.data && r.data.status) || 'REFUNDING'
          o.status = newStatus
          const msg = (r.data && r.data.message) || (newStatus === 'REFUNDED' ? '退款成功，点数已扣回' : '退款已提交，等待系统同步')
          uni.showToast({ title: msg, icon: 'none' })
          await this.loadOrders()
        } else {
          const detail = (r.data && r.data.detail) || '申请失败'
          uni.showToast({ title: detail, icon: 'none', duration: 3000 })
        }
      } catch (e) {
        uni.showToast({ title: '网络异常', icon: 'none' })
      }
    },
    async onContinuePay (o) {
      try {
        const lr = await api.refreshWxLogin()
        if (!lr.ok || !(lr.data && lr.data.token)) {
          uni.showToast({ title: '微信登录态刷新失败，请重新进入小程序后再试', icon: 'none' })
          return
        }
        uni.setStorageSync('token', lr.data.token)
        const r = await api.payExistingOrder(o.out_trade_no)
        if (!r.ok) {
          uni.showToast({ title: (r.data && r.data.detail) || '支付失败', icon: 'none' })
          return
        }
        const pp = r.data
        if (!wx.requestVirtualPayment) {
          uni.showToast({ title: '当前微信版本不支持', icon: 'none' })
          return
        }
        try {
          await new Promise((resolve, reject) => {
            wx.requestVirtualPayment({ mode: pp.mode || 'short_series_goods', signData: pp.signData || '', paySig: pp.paySig || '', signature: pp.signature || '', success: resolve, fail: reject })
          })
        } catch (payErr) {
          const errMsg = (payErr && payErr.errMsg) || ''
          if (errMsg.includes('cancel')) return
          uni.showToast({ title: errMsg || '支付失败', icon: 'none' })
          return
        }
        let paid = false
        for (let i = 0; i < 6; i++) {
          await new Promise(r => setTimeout(r, 1500))
          try {
            const qr = await api.queryVirtualOrder(o.out_trade_no)
            if (qr.ok && qr.data && qr.data.status === 'PAID') {
              paid = true
              break
            }
          } catch (e) {}
        }
        if (paid) {
          uni.showToast({ title: '支付成功', icon: 'success' })
          await this.loadOrders()
        } else {
          uni.showToast({ title: '支付处理中，请稍后刷新', icon: 'none' })
        }
      } catch (e) {
        uni.showToast({ title: '网络异常', icon: 'none' })
      }
    }
  }
}
</script>

<style scoped>
.page { min-height:100vh; background:linear-gradient(180deg,#dce4f2 0%,#e0e8f6 42%,#dce4f2 100%); padding-bottom:calc(38rpx + env(safe-area-inset-bottom)); }
.header { padding:58rpx 48rpx 54rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),linear-gradient(180deg,#0b3fbd 0%,#151f8f 68%,#241b83 100%); }
.brand { font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; display:block; }
.title { font-size:42rpx; font-weight:900; color:#fff; display:block; margin-top:4rpx; }
.subtitle { display:block; margin-top:12rpx; color:rgba(232,240,255,0.78); font-size:25rpx; line-height:1.45; }
.list { padding:22rpx 24rpx 44rpx; }
.order-card { background:linear-gradient(180deg,#fff,#f8fbff); border-radius:22rpx; padding:26rpx; margin-bottom:18rpx; box-shadow:0 14rpx 34rpx rgba(38,73,132,.10); border:1rpx solid rgba(219,230,255,.95); }
.order-head { display:flex; justify-content:space-between; gap:18rpx; align-items:flex-start; padding-bottom:18rpx; border-bottom:1rpx solid #eef3fb; }
.order-head-main { min-width:0; flex:1; }
.order-title { font-size:31rpx; font-weight:900; color:#16213a; line-height:1.25; }
.order-sub { display:block; margin-top:8rpx; color:#8b99b6; font-size:22rpx; font-family:monospace; }
.status-pill { height:46rpx; line-height:46rpx; padding:0 18rpx; border-radius:999rpx; font-size:23rpx; font-weight:900; background:#eff6ff; color:#315bff; white-space:nowrap; flex-shrink:0; }
.status-pill.paid { color:#059669; background:#dcfce7; }
.status-pill.created,.status-pill.pending { color:#b45309; background:#fff7ed; }
.status-pill.closed { color:#64748b; background:#f1f5f9; }
.order-body { display:flex; align-items:center; justify-content:space-between; gap:20rpx; padding:24rpx 0 18rpx; }
.benefit-box { min-width:0; flex:1; }
.benefit-label,.channel { display:block; color:#8b99b6; font-size:23rpx; line-height:1.3; }
.benefit-value { display:block; color:#059669; font-size:30rpx; font-weight:900; line-height:1.3; margin-top:8rpx; }
.benefit-value.pending { color:#b45309; }
.benefit-value.closed { color:#94a3b8; }
.amount-box { flex-shrink:0; text-align:right; }
.amount { display:block; color:#315bff; font-size:38rpx; font-weight:900; line-height:1.15; }
.order-meta { display:flex; flex-wrap:wrap; gap:10rpx 24rpx; color:#8b99b6; font-size:23rpx; line-height:1.45; padding-bottom:20rpx; border-bottom:1rpx solid #eef3fb; }
.order-foot { display:flex; align-items:center; justify-content:space-between; gap:18rpx; padding-top:20rpx; }
.detail-link { color:#64748b; font-size:24rpx; font-weight:800; }
.actions { display:flex; align-items:center; gap:12rpx; flex-wrap:wrap; justify-content:flex-end; }
.action-btn { margin:0; height:54rpx; line-height:54rpx; padding:0 22rpx; border-radius:999rpx; font-size:23rpx; font-weight:900; background:#fff; }
.action-btn::after { border:none; }
.action-btn.primary { color:#fff; background:linear-gradient(135deg,#315bff,#5b4be6); box-shadow:0 10rpx 22rpx rgba(49,91,255,.18); }
.action-btn.danger { color:#dc2626; border:1rpx solid rgba(239,68,68,.35); background:#fff; }
.action-note { color:#b45309; font-size:23rpx; font-weight:800; }
.action-note.muted { color:#94a3b8; }
.empty { margin:64rpx 34rpx 0; padding:76rpx 24rpx; text-align:center; background:rgba(255,255,255,.76); border:1rpx solid rgba(219,230,255,.95); border-radius:24rpx; }
.empty-icon { width:86rpx; height:86rpx; line-height:86rpx; margin:0 auto 20rpx; border-radius:28rpx; background:#eff6ff; color:#315bff; font-size:42rpx; }
.empty-title { display:block; color:#16213a; font-size:30rpx; font-weight:900; }
.empty-desc { display:block; color:#8b99b6; font-size:24rpx; margin-top:12rpx; }
</style>
