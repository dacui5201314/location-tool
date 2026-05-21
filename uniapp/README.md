# 址得选 uni-app 多端客户端

AI 选址初筛参考工具 · 未来主客户端

## 目录说明

- `uniapp/` — **未来主客户端**。基于 uni-app，覆盖微信小程序、抖音小程序、App 三端
- `frontend/` — **Web 母版**。React 前端，当前产品的功能参照和体验基准
- `miniprogram/` — **登录联调参考**。原生微信小程序脚手架，仅保留 `wx.login` → `/api/auth/wechat/mini` 调用方式作为参考，不继续开发新功能

## 当前阶段

**Phase 23A：页面骨架 parity**

- 所有 6 个页面已建立
- TabBar：首页 / 记录 / 收藏 / 我的
- 使用 mock 数据填充 UI，不调用真实 API
- 分析按钮、登录按钮、会员按钮均为占位

## 后续阶段

| Phase | 内容 |
|---|---|
| 23B | 登录/用户/records parity — 接真实 API |
| 23C | 分析表单 parity — 业态选择+地址搜索+品牌/面积 |
| 23D | 分析结果/详情 parity — SSE 流式+报告展示 |
| 23E | PDF 解锁/下载 |
| 23F | 微信支付（如需要） |
| 23G | 抖音小程序适配 |
| 23H | App 适配 |

## 启动方式

```bash
cd uniapp
npm install
npm run dev:mp-weixin   # 微信小程序
npm run dev:mp-toutiao   # 抖音小程序
npm run dev:app-plus     # App
```

## 注意事项

- 不提交真实 AppID/AppSecret
- 当前不调用 `/api/analyze`（会扣点/生成报告）
- Web 母版 `frontend/` 保持不动
