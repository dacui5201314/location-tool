# 址得选 uni-app 多端客户端

AI 选址初筛参考工具 · 未来主客户端（Vue3 + Vite）

## 目录说明

- `uniapp/` — **未来主客户端**。基于 uni-app (Vue3 + Vite)，覆盖微信小程序、抖音小程序、App 三端
- `frontend/` — **Web 母版**。React 前端，当前产品的功能参照和体验基准
- `miniprogram/` — **登录联调参考**。原生微信小程序脚手架，`wx.login` → `/api/auth/wechat/mini` 调用方式已验证，不继续开发新功能

## 当前阶段

**Phase 23A：页面骨架 parity**

- 6 个页面、4 项 TabBar（首页/记录/收藏/我的）、6 个组件
- 使用 mock 数据填充 UI，不调用真实 API
- 分析按钮、登录按钮、会员按钮均为占位

## 启动方式

**推荐：使用 HBuilderX 打开项目（自动管理 uni-app alpha 依赖）**

1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html)
2. 文件 → 导入 → 从本地目录导入 → 选择 `uniapp/` 目录
3. HBuilderX 自动安装依赖
4. 运行 → 运行到小程序模拟器 → 微信开发者工具

**命令行方式（依赖安装可能需手动对齐 alpha 版本）：**

```bash
cd uniapp
npm install
npm run dev:mp-weixin    # 微信小程序开发
npm run build:mp-weixin  # 微信小程序构建
npm run dev:mp-toutiao   # 抖音小程序开发
npm run dev:h5           # H5 开发
```

> `@dcloudio/*` 包使用 alpha 版号，HBuilderX 自动管理版本对齐。纯命令行安装时如遇版本冲突，请使用 HBuilderX 导入项目。`package.json` 中的依赖声明和脚本配置是正确且可用的。

## 微信测试号 AppID 配置

**不提交 AppID 到 Git。**

在 HBuilderX 中：
- `manifest.json` → 微信小程序配置 → 填写你的测试号 AppID

或在微信开发者工具中：
- 导入 `uniapp/dist/dev/mp-weixin` 目录
- 工具界面填写 AppID

## 注意事项

- 不提交真实 AppID/AppSecret/API key
- 当前 Phase 23A 不调用 `/api/analyze`（会扣点/生成报告）
- 不调用支付接口
- Web 母版 `frontend/` 保持不动
