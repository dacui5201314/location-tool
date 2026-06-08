<template>
  <view class="page">
    <view class="header">
      <text class="brand">址得选</text>
      <text class="title">订单详情</text>
      <text class="subtitle">查看订单、支付与退款处理进度</text>
    </view>

    <view class="loading" v-if="loading && !hasOrder">
      <text>加载中...</text>
    </view>

    <view class="content" v-if="hasOrder">
      <view class="summary-card">
        <view class="summary-top">
          <view>
            <text class="summary-label">当前状态</text>
            <text class="summary-title" :class="statusClass">{{ statusText }}</text>
          </view>
          <text class="status-pill" :class="statusClass">{{ statusText }}</text>
        </view>
        <text class="summary-desc">{{ statusDesc }}</text>
      </view>

      <view class="info-card">
        <view class="card-title">订单信息</view>
        <view class="info-row">
          <text class="label">套餐</text>
          <text class="value">{{ order.sku_label || '套餐' }}</text>
        </view>
        <view class="info-row">
          <text class="label">金额</text>
          <text class="value price">¥{{ order.amount_yuan || '0.00' }}</text>
        </view>
        <view class="info-row">
          <text class="label">权益</text>
          <text class="value" :class="{ closed: isClosed, warn: isRefundPending }">{{ benefitText }}</text>
        </view>
        <view class="info-row">
          <text class="label">支付方式</text>
          <text class="value">微信支付</text>
        </view>
        <view class="info-row">
          <text class="label">订单号</text>
          <text class="value mono">{{ orderNo }}</text>
        </view>
        <view class="info-row">
          <text class="label">创建时间</text>
          <text class="value">{{ fmt(order.created_at) }}</text>
        </view>
        <view class="info-row">
          <text class="label">支付时间</text>
          <text class="value">{{ fmt(order.paid_at) }}</text>
        </view>
      </view>

      <view class="action-card">
        <view class="card-title">操作</view>
        <button v-if="order.status === 'CREATED'" class="primary-btn" :disabled="loading" @tap="onContinuePay">
          {{ loading ? '处理中...' : '继续支付' }}
        </button>
        <button v-else-if="order.status === 'PAID'" class="refund-btn" :disabled="loading" @tap="onRefund">
          {{ loading ? '处理中...' : '申请退款' }}
        </button>
        <view v-else class="state-note" :class="{ closed: isClosed }">
          <text>{{ actionHint }}</text>
        </view>
        <text class="err" v-if="errMsg">{{ errMsg }}</text>
      </view>
    </view>

    <view class="empty" v-if="!loading && !hasOrder && errMsg">
      <text>{{ errMsg }}</text>
    </view>
  </view>
</template>

<script>
import api from '../../utils/api'

const STATUS_MAP = {
  CREATED: '待支付',
  PAID: '已完成',
  REFUND_REQUESTED: '退款申请中',
  REFUNDING: '退款处理中',
  REFUNDED: '已退款 / 权益已关闭',
  CANCELLED: '已取消',
  TIMEOUT: '已关闭',
  FAILED: '已关闭'
}

export default {
  data () {
    return {
      order: {},
      loading: false,
      errMsg: ''
    }
  },
  computed: {
    hasOrder () {
      return !!(this.order.order_no || this.order.out_trade_no)
    },
    orderNo () {
      return this.order.out_trade_no || this.order.order_no || '-'
    },
    statusText () {
      return STATUS_MAP[this.order.status] || this.order.status || '-'
    },
    isRefundPending () {
      return ['REFUND_REQUESTED', 'REFUNDING'].includes(this.order.status)
    },
    isClosed () {
      return ['REFUNDED', 'CANCELLED', 'TIMEOUT', 'FAILED'].includes(this.order.status)
    },
    statusClass () {
      const s = this.order.status
      if (s === 'PAID') return 'paid'
      if (s === 'CREATED') return 'created'
      if (this.isRefundPending) return 'warn'
      if (this.isClosed) return 'closed'
      return ''
    },
    benefitText () {
      if (this.order.status === 'REFUNDED') return '权益已关闭'
      if (this.isClosed) return '权益已关闭'
      if (this.isRefundPending) return '退款处理中'
      const parts = []
      if (this.order.credits) parts.push('+' + this.order.credits + '点')
      if (this.order.membership_days) parts.push(this.order.membership_days + '天会员')
      return parts.join(' / ') || '-'
    },
    statusDesc () {
      const map = {
        CREATED: '订单已创建，请在有效时间内完成支付。',
        PAID: '支付已完成，权益已同步到账。',
        REFUND_REQUESTED: '退款申请已提交，请等待系统处理。',
        REFUNDING: '退款正在处理中，处理完成后权益会同步关闭。',
        REFUNDED: '订单已退款，相关权益已关闭。',
        CANCELLED: '订单已取消，无需继续处理。',
        TIMEOUT: '订单已超时关闭，可返回充值中心重新购买。',
        FAILED: '订单支付失败或已关闭，可返回充值中心重新购买。'
      }
      return map[this.order.status] || '订单状态以系统记录为准。'
    },
    actionHint () {
      if (this.isRefundPending) return '退款处理中，请稍后刷新查看结果'
      if (this.order.status === 'REFUNDED') return '已退款，权益已关闭'
      if (['TIMEOUT', 'FAILED'].includes(this.order.status)) return '订单已关闭，可重新选择套餐'
      if (this.order.status === 'CANCELLED') return '订单已取消'
      return '当前订单暂无可操作项'
    }
  },
  onLoad (opt) {
    const no = (opt.order_no || '').trim()
    if (!no) {
      this.errMsg = '缺少订单号'
      return
    }
    this.fetchOrder(no)
  },
  onPullDownRefresh () {
    Promise.resolve(this.reloadOrder()).finally(() => uni.stopPullDownRefresh())
  },
  methods: {
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
    async fetchOrder (no) {
      this.loading = true
      this.errMsg = ''
      try {
        const r = await api.queryVirtualOrder(no)
        if (r.ok && r.data) {
          this.order = r.data
        } else {
          this.errMsg = (r.data && r.data.detail) || '订单不存在'
        }
      } catch (e) {
        this.errMsg = '加载订单失败'
      } finally {
        this.loading = false
      }
    },
    async reloadOrder () {
      const no = this.orderNo
      if (!no || no === '-') return
      try {
        const r = await api.queryVirtualOrder(no)
        if (r.ok && r.data) this.order = r.data
      } catch (e) {}
    },
    async onContinuePay () {
      if (this.loading || !this.orderNo || this.orderNo === '-') return
      this.loading = true
      this.errMsg = ''
      try {
        const lr = await api.refreshWxLogin()
        if (!lr.ok || !(lr.data && lr.data.token)) {
          uni.showToast({ title: '微信登录态刷新失败，请重新进入小程序后再试', icon: 'none' })
          return
        }
        uni.setStorageSync('token', lr.data.token)
        const r = await api.payExistingOrder(this.orderNo)
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
            wx.requestVirtualPayment({
              mode: pp.mode || 'short_series_goods',
              signData: pp.signData || '',
              paySig: pp.paySig || '',
              signature: pp.signature || '',
              success: resolve,
              fail: reject
            })
          })
        } catch (payErr) {
          const errMsg = (payErr && payErr.errMsg) || ''
          if (errMsg.includes('cancel')) return
          uni.showToast({ title: errMsg || '支付失败', icon: 'none' })
          return
        }
        let paid = false
        for (let i = 0; i < 6; i++) {
          await new Promise(resolve => setTimeout(resolve, 1500))
          try {
            const qr = await api.queryVirtualOrder(this.orderNo)
            if (qr.ok && qr.data) {
              this.order = qr.data
              if (qr.data.status === 'PAID') {
                paid = true
                break
              }
            }
          } catch (e) {}
        }
        if (paid) {
          uni.showToast({ title: '支付成功', icon: 'success' })
        } else {
          uni.showToast({ title: '支付处理中，请稍后刷新', icon: 'none' })
          await this.reloadOrder()
        }
      } catch (e) {
        uni.showToast({ title: '网络异常', icon: 'none' })
      } finally {
        this.loading = false
      }
    },
    async onRefund () {
      if (this.loading || !this.orderNo || this.orderNo === '-') return
      const res = await new Promise(r => uni.showModal({
        title: '确认退款',
        content: '退款后将关闭本订单权益，并扣回对应点数。确认申请退款？',
        success: r
      }))
      if (!res.confirm) return
      this.loading = true
      this.errMsg = ''
      try {
        const r = await api.refundRequestVirtual(this.orderNo)
        if (r.ok) {
          this.order.status = (r.data && r.data.status) || 'REFUNDING'
          const msg = (r.data && r.data.message) || (this.order.status === 'REFUNDED' ? '退款成功，点数已扣回' : '退款已提交，等待系统同步')
          uni.showToast({ title: msg, icon: 'none' })
          await this.reloadOrder()
        } else {
          this.errMsg = (r.data && r.data.detail) || '申请失败'
        }
      } catch (e) {
        this.errMsg = '网络异常'
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style scoped>
.page { min-height:100vh; background:linear-gradient(180deg,#dce4f2 0%,#e0e8f6 42%,#dce4f2 100%); padding-bottom:calc(44rpx + env(safe-area-inset-bottom)); }
.header { padding:62rpx 48rpx 82rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),radial-gradient(circle at 66% 60%,rgba(139,92,246,0.22),transparent 26%),linear-gradient(180deg,#0b3fbd 0%,#0d35ad 28%,#151f8f 68%,#241b83 100%); }
.brand { font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; display:block; }
.title { font-size:42rpx; font-weight:900; color:#fff; display:block; margin-top:2rpx; }
.subtitle { display:block; margin-top:10rpx; color:rgba(232,240,255,0.78); font-size:25rpx; line-height:1.45; }
.content { margin-top:-48rpx; padding:0 24rpx; position:relative; z-index:2; }
.loading,.empty { margin:64rpx 34rpx 0; padding:70rpx 24rpx; text-align:center; background:rgba(255,255,255,.78); border:1rpx solid rgba(219,230,255,.95); border-radius:24rpx; color:#64748b; font-size:26rpx; }
.summary-card,.info-card,.action-card { background:linear-gradient(180deg,#fff,#f8fbff); border-radius:22rpx; padding:28rpx; margin-bottom:20rpx; box-shadow:0 14rpx 34rpx rgba(38,73,132,.10); border:1rpx solid rgba(219,230,255,.95); }
.summary-card { overflow:hidden; position:relative; }
.summary-card::after { content:''; position:absolute; right:-110rpx; top:-120rpx; width:300rpx; height:300rpx; border-radius:50%; background:rgba(49,91,255,.08); }
.summary-top { display:flex; justify-content:space-between; gap:18rpx; align-items:flex-start; position:relative; z-index:1; }
.summary-label { display:block; color:#8b99b6; font-size:23rpx; font-weight:800; }
.summary-title { display:block; margin-top:8rpx; color:#315bff; font-size:40rpx; font-weight:900; line-height:1.25; }
.summary-title.paid { color:#059669; }
.summary-title.created,.summary-title.warn { color:#b45309; }
.summary-title.closed { color:#64748b; }
.summary-desc { display:block; margin-top:18rpx; color:#64748b; font-size:25rpx; line-height:1.55; position:relative; z-index:1; }
.status-pill { height:48rpx; line-height:48rpx; padding:0 18rpx; border-radius:999rpx; font-size:23rpx; font-weight:900; background:#eff6ff; color:#315bff; white-space:nowrap; flex-shrink:0; position:relative; z-index:1; }
.status-pill.paid { color:#059669; background:#dcfce7; }
.status-pill.created,.status-pill.warn { color:#b45309; background:#fff7ed; }
.status-pill.closed { color:#64748b; background:#f1f5f9; }
.card-title { color:#17244e; font-size:30rpx; font-weight:900; margin-bottom:10rpx; }
.info-row { display:flex; justify-content:space-between; gap:24rpx; padding:20rpx 0; border-bottom:1rpx solid #eef3fb; }
.info-row:last-child { border-bottom:none; padding-bottom:4rpx; }
.label { color:#8b99b6; font-size:25rpx; flex-shrink:0; }
.value { color:#1e293b; font-size:26rpx; font-weight:800; line-height:1.35; text-align:right; min-width:0; word-break:break-all; }
.value.price { color:#315bff; font-size:32rpx; font-weight:900; }
.value.warn { color:#b45309; }
.value.closed { color:#94a3b8; }
.value.mono { font-size:21rpx; font-family:monospace; }
.primary-btn,.refund-btn { width:100%; height:88rpx; line-height:88rpx; margin:24rpx 0 0; padding:0; border-radius:16rpx; color:#fff; font-size:30rpx; font-weight:900; }
.primary-btn { background:linear-gradient(135deg,#315bff,#5b4be6); box-shadow:0 14rpx 28rpx rgba(49,91,255,.20); }
.refund-btn { background:linear-gradient(135deg,#f59e0b,#ef4444); box-shadow:0 14rpx 28rpx rgba(239,68,68,.16); }
.primary-btn::after,.refund-btn::after { border:none; }
.primary-btn[disabled],.refund-btn[disabled] { opacity:.62; box-shadow:none; }
.state-note { margin-top:22rpx; padding:22rpx; border-radius:16rpx; background:#fff7ed; color:#b45309; font-size:26rpx; line-height:1.45; font-weight:800; text-align:center; }
.state-note.closed { background:#f1f5f9; color:#64748b; }
.err { color:#dc2626; font-size:24rpx; display:block; text-align:center; margin-top:16rpx; line-height:1.45; }
</style>
