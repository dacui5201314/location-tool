<template>
  <view class="profile-page">
    <ProfilePanel ref="profilePanel" @go-tab="goTab" />
  </view>
</template>

<script>
import ProfilePanel from '../../components/tab/ProfilePanel.vue'

export default {
  components: { ProfilePanel },
  onShow () {
    this.$nextTick(() => {
      if (this.$refs.profilePanel && this.$refs.profilePanel.refresh) {
        this.$refs.profilePanel.refresh()
      }
    })
  },
  async onPullDownRefresh () {
    try {
      await this.$nextTick()
      const panel = this.$refs.profilePanel
      if (panel && panel.refresh) {
        const ret = panel.refresh()
        if (ret && ret.then) await ret.catch(() => {})
      }
    } finally {
      uni.stopPullDownRefresh()
    }
  },
  methods: {
    goTab (tab) {
      uni.reLaunch({ url: '/pages/home/index?tab=' + tab })
    }
  }
}
</script>

<style scoped>
.profile-page {
  min-height:100vh;
  background:#dce4f2;
}
</style>
