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

## 构建方式

**必须使用 HBuilderX（推荐）**

`@dcloudio/*` 系列包使用 alpha 版号，版本对齐由 HBuilderX 内置依赖管理器保证，命令行 `npm install` 可能因 alpha 版本冲突而无法构建。

1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html)（推荐 4.0+）
2. 文件 → 导入 → 从本地目录导入 → 选择 `uniapp/` 目录
3. HBuilderX 自动安装依赖并创建 `package-lock.json`
4. 运行 → 运行到小程序模拟器 → 微信开发者工具

**命令行方式（仅供参考，可能需手动对齐版本）**

```bash
cd uniapp
npm install --legacy-peer-deps
npm run build:mp-weixin    # 如 uni CLI 不可用，改用 HBuilderX
```

## 项目结构

```
uniapp/
├── index.html                    # Vite 入口
├── vite.config.js                # Vite + uni-app 插件配置
├── package.json                  # 依赖声明（HBuilderX 管理实际版本）
├── src/
│   ├── manifest.json             # uni-app 应用配置
│   ├── pages.json                # 路由 + TabBar
│   ├── App.vue                   # 根组件
│   ├── main.js                   # Vue3 createSSRApp 入口
│   ├── uni.scss                  # 主题变量
│   ├── components/               # 复用组件
│   │   ├── app-header/
│   │   ├── industry-picker/
│   │   ├── address-input/
│   │   ├── report-card/
│   │   ├── score-panel/
│   │   └── empty-state/
│   ├── pages/                    # 页面
│   │   ├── home/                 # 首页（分析入口）
│   │   ├── records/              # 分析记录
│   │   ├── favorites/            # 收藏
│   │   ├── report-detail/        # 报告详情
│   │   ├── result/               # 分析结果
│   │   └── profile/              # 我的
│   └── utils/                    # 工具
│       ├── api.js
│       ├── auth.js
│       ├── config.js
│       └── format.js
```

## 微信测试号 AppID 配置

**不提交 AppID 到 Git。**

在 HBuilderX 中：
- `src/manifest.json` → 微信小程序配置 → 填写你的测试号 AppID

或在微信开发者工具中：
- 导入 `uniapp/dist/dev/mp-weixin` 目录
- 工具界面填写 AppID

## 注意事项

- 不提交真实 AppID/AppSecret/API key
- 当前 Phase 23A 不调用 `/api/analyze`（会扣点/生成报告）
- 不调用支付接口
- Web 母版 `frontend/` 保持不动
