# 址得选 微信小程序（历史参考目录）

> **⚠️ 历史废弃目录，不可发布、不可继续开发。**
>
> 小程序主工程是 `uniapp/`，唯一发布路径为 `uniapp/dist/build/mp-weixin`。
> 本目录仅保留早期微信原生登录调用参考，不同步任何新功能。

## 当前维护口径

- 唯一发布路径：`uniapp/dist/build/mp-weixin`（微信开发者工具导入此路径）
- 本目录不再作为发布/联调入口
- AppID 使用 `uniapp/src/manifest.json` 中配置的正式 AppID

## 文件结构（仅参考）

```
miniprogram/
├── app.json / app.js / app.wxss
├── project.config.json
├── sitemap.json
├── utils/config.js          # API_BASE_URL（已过时）
├── utils/api.js             # 封装的 wx.request（已过时）
├── pages/login/             # 微信登录参考
├── pages/index/             # 首页（已过时）
└── pages/profile/           # 个人中心（已过时）
```
