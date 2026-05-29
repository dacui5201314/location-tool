<script>
export default {
  onLaunch () {
    // uni-app 启动时不强制登录。首页公开，我的页按需登录。
  }
}
</script>

<style>
/* 全局主题变量 + 首页关键容器防白闪兜底 */
page {
  --page-bg: #dce4f2;
  --ink: #111827;
  --muted: #667085;
  --blue: #246bff;
  --brand-navy: #071836;
  --brand-royal: #0f56e8;
  --green: #16c79a;
  --gold: #d6a84f;
  --coral: #ff876c;

  background-color: var(--page-bg);
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: 28rpx;
  color: var(--ink);
}

page,
uni-page-body {
  height: auto;
  min-height: 100vh;
  background-color: var(--page-bg);
}

/* 热更新防白闪：home 页关键容器纯色兜底（scoped wxss 卸载时生效） */
.home-page { background: #dce4f2; }
.map-wrap { background: #dce4f2; }
.map-placeholder { background: #dce4f2; }
.analyzing-card { background: #dce4f2; }
.hero { background: #0d35ad; }
</style>
