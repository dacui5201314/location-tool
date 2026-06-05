<template>
  <view class="page">
    <view class="header">
      <text class="brand">址得选</text>
      <text class="title">充值记录</text>
    </view>
    <view class="list" v-if="orders.length">
      <view class="item" v-for="o in orders" :key="o.out_trade_no">
        <view class="item-top">
          <text class="sku">{{ o.sku_label || '套餐' }}</text>
          <text class="amount">¥{{ o.amount_yuan }}</text>
        </view>
        <view class="item-mid">
          <text class="detail">{{ o.credits ? '+' + o.credits + '点' : '' }}{{ o.membership_days ? o.membership_days + '天会员' : '' }}</text>
          <text class="channel">{{ o.pay_channel === 'WECHAT_VIRTUAL' ? '虚拟支付' : o.pay_channel === 'WECHAT_JSAPI' ? '微信支付' : o.pay_channel || '-' }}</text>
        </view>
        <view class="item-bottom">
          <text class="time">{{ fmt(o.created_at) }}</text>
          <text class="status" :class="{ paid: o.status === 'PAID', created: o.status === 'CREATED', timeout: o.status === 'TIMEOUT' }">{{ o.status === 'PAID' ? '已到账' : o.status === 'CREATED' ? '待支付' : o.status === 'TIMEOUT' ? '已过期' : o.status }}</text>
        </view>
      </view>
    </view>
    <view class="empty" v-else>
      <text>暂无充值记录</text>
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
    api.fetchMyOrders().then(r => {
      if (r.ok && r.data) this.orders = r.data.orders || []
    }).catch(() => {})
  },
  methods: {
    fmt (iso) {
      if (!iso) return '-'
      return iso.replace('T', ' ').slice(0, 19)
    }
  }
}
</script>

<style scoped>
.page { min-height:100vh; background:linear-gradient(180deg,#dce4f2 0%,#e0e8f6 42%,#dce4f2 100%); padding-bottom:env(safe-area-inset-bottom); }
.header { padding:62rpx 48rpx 48rpx; background:radial-gradient(circle at 78% 32%,rgba(83,137,255,0.42),transparent 24%),linear-gradient(180deg,#0b3fbd 0%,#151f8f 68%,#241b83 100%); }
.brand { font-size:22rpx; color:rgba(255,255,255,0.68); letter-spacing:6rpx; display:block; }
.title { font-size:40rpx; font-weight:900; color:#fff; display:block; margin-top:4rpx; }
.list { padding:20rpx 24rpx; }
.item { background:#fff; border-radius:16rpx; padding:24rpx; margin-bottom:16rpx; box-shadow:0 4rpx 16rpx rgba(0,0,0,0.04); }
.item-top { display:flex; justify-content:space-between; align-items:center; }
.sku { font-size:29rpx; font-weight:800; color:#1e293b; }
.amount { font-size:32rpx; font-weight:900; color:#315bff; }
.item-mid { display:flex; justify-content:space-between; margin-top:8rpx; }
.detail { font-size:24rpx; color:#16a34a; }
.channel { font-size:22rpx; color:#94a3b8; }
.item-bottom { display:flex; justify-content:space-between; margin-top:10rpx; }
.time { font-size:23rpx; color:#94a3b8; }
.status { font-size:23rpx; font-weight:800; }
.status.paid { color:#16a34a; }
.status.created { color:#f59e0b; }
.status.timeout { color:#94a3b8; }
.empty { text-align:center; padding:100rpx 0; font-size:28rpx; color:#94a3b8; }
</style>
