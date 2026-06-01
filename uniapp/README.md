# 址得选 uni-app 多端客户端

AI 选址初筛参考工具 · 主力客户端（Vue3 + Vite）

## 目录说明

- `uniapp/` — **主力客户端**。基于 uni-app (Vue3 + Vite)，覆盖微信小程序、抖音小程序、App 三端
- `miniprogram/` — 原生微信小程序脚手架，仅保留登录调用参考，不继续开发新功能
- `backend/` — FastAPI 后端，所有 API 由此提供

## 当前阶段

- **地址自动联想** — `@input` 显式绑定 + 400ms debounce + 竞态守卫，Timeout 三级降级
- **SSE 分析接口** — `/api/analyze` 流式集成：401/402/5xx/成功 → 跳转 `report-detail?id=<record_id>`
- **登录/充值/CDK** — 快捷登录、密码登录、注册、兑换码、充值中心均已独立页面化
- **微信支付** — JSAPI v3 prepay + notify 后端已就绪，前端已接入真实支付含 queryOrder 确认闭环，待公网 HTTPS 真机验收
- 未接：PDF unlock/download

## 构建方式

**推荐使用 HBuilderX**

1. 下载 [HBuilderX](https://www.dcloud.io/hbuilderx.html)（推荐 4.0+）
2. 文件 → 导入 → 从本地目录导入 → 选择 `uniapp/` 目录
3. HBuilderX 自动安装依赖
4. 运行 → 运行到小程序模拟器 → 微信开发者工具

**命令行方式**

```bash
cd uniapp
npm install --legacy-peer-deps
npm run build:mp-weixin
```

## 微信开发者工具导入

### 1. 构建

```bash
cd uniapp
npm run build:mp-weixin
```

成功后输出目录：`dist/build/mp-weixin`

### 2. 导入微信开发者工具

1. 打开微信开发者工具 → 点击「导入」
2. 目录选择：`uniapp/dist/build/mp-weixin`
3. AppID 填入你的测试号或正式小程序 AppID
4. 点击确定

### 3. 开发者工具设置

- 详情 → 本地设置 → 勾选「不校验合法域名、web-view、TLS 版本以及 HTTPS 证书」

### 4. 真机联调前提

- 后端运行在公网 HTTPS 域名下
- 管理后台已配置小程序 AppID / Secret
- 微信公众平台 request 合法域名已添加后端域名

## 项目结构

```
uniapp/
├── index.html                    # Vite 入口
├── vite.config.js                # Vite + uni-app 插件配置
├── package.json                  # 依赖声明
├── src/
│   ├── manifest.json             # uni-app 应用配置 (AppID: wx3e2e1bbabfa164dd)
│   ├── pages.json                # 路由 + TabBar (13 页面)
│   ├── App.vue                   # 根组件
│   ├── main.js                   # Vue3 createSSRApp 入口
│   ├── components/               # 组件
│   │   ├── app-header/
│   │   ├── industry-picker/      # 业态选择器（滚动+触摸手势）
│   │   ├── address-input/        # 地址联想输入
│   │   ├── report-card/          # 报告卡片
│   │   ├── score-panel/          # 评分面板
│   │   ├── empty-state/          # 空状态占位
│   │   └── tab/                  # 底部 Tab 面板
│   ├── pages/                    # 页面
│   │   ├── home/                 # 首页（分析入口+地图）
│   │   ├── records/              # 分析记录
│   │   ├── favorites/            # 收藏
│   │   ├── report-detail/        # 报告详情
│   │   ├── result/               # 分析结果
│   │   ├── profile/              # 个人中心
│   │   │   ├── index.vue
│   │   │   ├── login.vue         # 登录/注册
│   │   │   ├── recharge.vue      # 充值中心
│   │   │   ├── redeem.vue        # CDK 兑换
│   │   │   ├── contact.vue       # 客服
│   │   │   └── edit.vue          # 编辑资料
│   │   └── legal/                # 法律页面
│   │       ├── user-agreement.vue
│   │       └── privacy-policy.vue
│   └── utils/
│       ├── api.js                # HTTP 客户端
│       ├── auth.js               # Token 管理
│       ├── config.js             # API_BASE_URL
│       └── format.js             # 格式化工具 (compactAddress 等)
```

## 注意事项

- 不提交 AppID / Secret / 密钥到 Git
- `src/manifest.json` 中的小程序 AppID 仅用于本地联调
