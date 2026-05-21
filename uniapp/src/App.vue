<script>
export default {
  onLaunch () {
    // uni-app 启动时不强制登录。首页公开，我的页按需登录。
  }
}
</script>

<style>
/* 全局主题变量 — 对齐 Web index.css */
page {
  --page-bg: #eef3f9;
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
</style>
