# 址得选 微信小程序

AI 选址助手 · 小程序版 MVP

## 导入微信开发者工具

1. 下载[微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 打开工具 → 导入项目
3. 目录选择 `miniprogram/`
4. AppID 使用默认 `touristappid`（可用于游客模式/测试导入，无需注册）
5. 点击确定

> **注意**：`touristappid` 仅支持开发者工具游客模式。微信登录联调（`wx.login` 获取真实 openid）必须替换为正式小程序 AppID。在 `project.config.json` 中将 `"appid": "touristappid"` 改为你的实际 AppID。

## 修改项目配置

### 1. `project.config.json`
```json
"appid": "你的小程序AppID"
```

### 2. `utils/config.js`
```js
const API_BASE_URL = 'http://127.0.0.1:8000'
```

## 管理后台配置（服务端）

1. 登录管理后台 → 系统参数
2. 填入 `wx_mini_appid`（小程序 AppID）
3. 填入 `wx_mini_secret`（小程序 AppSecret）
4. 保存

## 开发者工具调试（跳过 HTTPS）

1. 开发者工具右上角 → 详情 → 本地设置
2. 勾选 **"不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书"**
3. 此时可以直接调通 `wx.login()` → `/api/auth/wechat/mini`

## 真机预览（需 HTTPS）

1. 服务器 Nginx 必须配置 SSL 证书（Let's Encrypt 或付费证书）
2. 微信公众平台 → 开发管理 → 开发设置 → 服务器域名
3. `request 合法域名` 添加 `https://你的域名.com`
4. 上传代码 → 设为体验版 → 手机扫码测试

## 常见错误

| 错误 | 原因 | 解决 |
|---|---|---|
| 503 小程序未配置 | 管理后台未填 wx_mini_appid/secret | 管理后台→系统参数 填写 |
| 400 code 无效 | code 已过期或重复使用 | 重新调用 `wx.login()` |
| 409 身份冲突 | openid 已被其他账号绑定 | 联系客服处理 |
| 网络请求失败 | 域名未配置或非 HTTPS | 检查 request 合法域名 + HTTPS |
| `wx.login` 失败 | 开发者工具未登录 | 工具右上角扫码登录 |

## 文件结构

```
miniprogram/
├── app.json / app.js / app.wxss
├── project.config.json
├── sitemap.json
├── utils/config.js          # API_BASE_URL 占位
├── utils/api.js             # 封装的 wx.request
├── pages/login/             # 微信登录页
└── pages/index/             # 首页（用户信息 + 测试按钮）
```
