# 址得选 微信小程序（原生脚手架）

> **注意**：此为登录联调参考项目，功能开发已全面迁移至 `uniapp/`，此处不再继续开发。

## 当前维护口径（2026-06-18）

- 小程序主工程是 `uniapp/`，微信开发者工具应导入 `uniapp/dist/build/mp-weixin`。
- 本目录只保留原生微信登录调用参考，不同步报告详情、首页、反馈、充值、订单等新功能。
- 不在本目录修复 UI、报告预览或审核文案；相关问题统一改 `uniapp/`。

## 导入微信开发者工具

1. 下载[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开工具 → 导入项目
3. 目录选择 `miniprogram/`
4. AppID 使用默认 `touristappid`（游客模式）
5. 点击确定

> `touristappid` 仅支持开发者工具游客模式。微信登录联调必须替换为正式小程序 AppID。

## 项目配置

### `project.config.json`
```json
"appid": "你的小程序AppID"
```

### `utils/config.js`
```js
const API_BASE_URL = 'http://127.0.0.1:8000'
```

## 文件结构

```
miniprogram/
├── app.json / app.js / app.wxss
├── project.config.json
├── sitemap.json
├── utils/config.js          # API_BASE_URL
├── utils/api.js             # 封装的 wx.request
├── pages/login/             # 微信登录页
├── pages/index/             # 首页
└── pages/profile/           # 个人中心
```
