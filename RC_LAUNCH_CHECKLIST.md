# 址得选 RC 上线配置与真机验收手册

> 当前 RC Final Freeze commit: `b0ba5bc`
> 文档目的：上线前人工配置清单 + 真机验收路径。
> **本文件不包含任何真实密码、token、AppSecret、API key、PEM、私钥。**

---

## 一、上线前外部配置

### 1.1 服务器/域名

| 配置项 | 变量/位置 | 用途 | 说明 |
|--------|----------|------|------|
| HTTPS API 域名 | `VITE_API_BASE_URL` in `.env.production` | uniapp 请求后端 API | 必须 HTTPS；生产构建时注入 |
| request 合法域名 | 微信小程序后台 → 开发管理 → 服务器域名 | 小程序网络请求白名单 | 填写 HTTPS API 域名 |
| uploadFile 合法域名 | 微信小程序后台 → 服务器域名 | 头像上传等 | 如需可用同域名 |
| assets 静态资源域名 | 同上（同 API 域名） | 头像/分享图等 /assets/ 路径 | HTTPS |
| 后端 health check | `GET /api/health` | 部署后验活 | 返回 `{"status":"ok"}` |

### 1.2 微信小程序后台

| 配置项 | 路径 | 说明 |
|--------|------|------|
| AppID | 开发管理 → 开发设置 | 测试版已配置；生产版确认 AppID |
| 服务器域名 | 开发管理 → 服务器域名 | request/uploadFile/downloadFile 合法域名（HTTPS） |
| 用户隐私保护指引 | 设置 → 用户隐私保护指引 | 必须填写；与 uniapp 隐私弹窗声明一致 |
| 手机号快速验证 | 开发管理 → 能力 | 开通后 getPhoneNumber 才可用（需非游客 AppID） |
| 头像昵称授权 | 无需额外配置 | 微信原生能力，chooseAvatar + nickname input |
| 版本上传 | 开发管理 → 版本管理 | 上传 uniapp/dist/build/mp-weixin → 设为体验版 → 提交审核 |

### 1.3 后端环境配置（.env 文件）

| 变量名 | 用途 | 说明 |
|--------|------|------|
| `AMAP_WEB_KEY` | 高德 Web API Key | POI 搜索/周边采集/地址解析 |
| `LLM_PROVIDER` | 大模型提供商 | deepseek / openai / gemini 等 |
| `LLM_API_KEY` | 大模型 API Key | 与 provider 对应 |
| `LLM_MODEL` | 模型名称 | 如 deepseek-chat |
| `LLM_BASE_URL` | 模型 API 地址 | 如 https://api.deepseek.com/v1 |
| `JWT_SECRET` | JWT 签名密钥 | 随机字符串，生产务必修改默认值 |
| `ADMIN_PASSWORD` | 后台管理密码 | 随机强密码，不要用 admin123 |
| `DATABASE_URL` | 数据库路径 | 默认 sqlite: `sqlite:///./data.db` |
| `CORS_ORIGINS` | 跨域来源 | 生产填写前端域名 |

### 1.4 管理后台配置（Admin Page）

| 配置块 | 内容 | 说明 |
|--------|------|------|
| SKU 管理 | 会员/点数套餐 7 条 | 确认价格和赠送点数 |
| CDK 生成 | 批量生成兑换码 | 运营活动用 |
| 分享设置 | share_title / share_image_url / report_share_title_template / share_cta_text | 控制小程序分享卡片 |
| 客服配置 | 微信号/手机号/名称 | Uni-app 客服入口 |
| 用户管理 | 用户列表/点数/会员 | 确认用户 46 等可见 |
| 微信支付配置 | mch_id / APIv3 key / 私钥PEM / 证书序列号 / 平台证书PEM / notify_url | 支付开通后填写 |

### 1.5 微信支付商户配置（开通后）

| 配置项 | 变量/DB Key | 说明 |
|--------|------------|------|
| 商户号 | `wx_mch_id` | 微信商户平台获取 |
| APIv3 key | `wx_api_key` | 商户平台设置 |
| 商户私钥 PEM | `wx_private_key_pem` | 商户平台下载 |
| 商户证书序列号 | `wx_cert_sn` | 商户平台查看 |
| 平台证书 PEM | `wx_platform_cert_pem` | 微信支付平台证书 |
| 回调通知 URL | `wx_notify_url` | 必须公网 HTTPS |
| JSAPI 支付权限 | 微信商户平台开通 | 小程序支付必需 |
| AppID 绑定 | 商户平台 → AppID 管理 | 小程序 AppID 与商户号绑定 |

---

## 二、真机验收路径

### 2.1 登录与授权

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 1 | 打开小程序 | 首页可见，不白屏（commit c2d92df 已修） |
| 2 | 点击微信登录 | 调用 wx.login，获取 openid，返回 JWT token |
| 3 | 授权头像 | chooseAvatar 弹起，选择后头像更新 |
| 4 | 授权昵称 | nickname input 可用，填写后提交 |
| 5 | 密码登录 fallback | 输入手机号+密码，登录成功拿到 token |
| 6 | 注册 | 输入手机号+密码，注册成功 |
| 7 | 限流 | 连续 5 次错误密码 → 第 6 次提示"尝试次数过多" |

### 2.2 地图选点

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 8 | 搜索地址 | 输入关键词，出现联想列表；选择后 marker 跳到对应位置，地址显示 |
| 9 | 定位 | 点击定位按钮，授权后 marker 跳到当前位置，地址反查显示 |
| 10 | 点击地图 | 点击地图空白处，marker 移动到点击位置，地址反查更新 |
| 11 | 拖动地图 | 拖动/缩放地图结束后，marker 跟随新中心位置，地址反查更新 |

### 2.3 生成选址分析报告

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 12 | 选择业态 | 点击业态分类，选择一个 |
| 13 | 填写品牌和面积 | 输入品牌名和预估面积 |
| 14 | 点击生成 | CTA 按钮变为"分析中..."，Step 1→2→3→4 推进 |
| 15 | 报告生成 | 收到 step 4 "报告生成完毕"，自动跳转 report-detail |
| 16 | 扣点 | Profile 点数减 1（会员不扣） |

### 2.4 报告查看与记录

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 17 | report-detail | 显示评分、优势/风险、雷达图、各维度分析、POI 明细 |
| 18 | records 列表 | tab 切换到记录页，列表出现刚生成的报告 |
| 19 | Profile | 我的页 total_reports 增加，点数更新 |

### 2.5 报告分享

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 20 | Owner 分享 | 在 report-detail 页点击右上角分享 |
| 21 | 分享卡片 | 标题格式 `{地址}选址分析报告`；如有分享图则显示 |
| 22 | 被分享人打开 | 通过 share={token} 打开，无需登录；显示脱敏报告 |
| 23 | CTA | 页面底部显示"我也要生成选址报告"，点击跳转首页 |

### 2.6 商业化

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 24 | CDK 兑换 | 输入有效兑换码，点击兑换 → fetchProfile 刷新点数 |
| 25 | 充值页面 | SKU 列表正常加载，选择套餐 |
| 26 | 支付（未配置） | 点击支付 → 真实失败提示，不假成功 |
| 27 | 支付（已配置） | requestPayment 拉起微信支付，支付后 queryOrder → fetchProfile |

### 2.7 管理后台

| 步骤 | 操作 | 预期结果 |
|------|------|---------|
| 28 | Admin 登录 | 密码登录后台，JWT 签发 |
| 29 | 用户管理 | total 正确，昵称/头像/点数/会员显示正常 |
| 30 | 分享设置 | 修改分享标题 → 小程序端分享卡片标题生效 |

---

## 三、已知非阻塞问题

| # | 问题 | 级别 | 说明 |
|---|------|------|------|
| 1 | 欢迎弹窗/遮罩横向白块闪烁 | P2 | 视觉问题，不影响功能 |
| 2 | DevTools 本地 HTTP 头像警告 | P2 | 生产 HTTPS 域名可解决 |
| 3 | share_token 暂无过期/查看统计 | P2 | 后续可加 expires_at / view_count |
| 4 | analyze 超时兜底 v1（最近记录+时间窗） | P2 | 后续可升级 client_request_id 幂等 |
| 5 | PDF 下载 | 不做 | 报告分享查看替代；/download /unlock-pdf 在 uni-app 已禁止 |

---

## 四、上线 Go/No-Go 标准

### Go 条件（必须全部满足）

- [ ] 微信登录真机通过（获取 openid + JWT）
- [ ] 密码登录/注册 + 限流真机通过
- [ ] 头像昵称授权真机通过
- [ ] 地图搜索/定位/点击/拖动选点真机通过
- [ ] 生成选址分析报告 Step 1-4 真机通过（小于 120s）
- [ ] report-detail 完整渲染通过
- [ ] records 列表 + Profile 点数联动通过
- [ ] 报告分享（owner 分享 + 被分享人打开）通过
- [ ] 分享接口不泄露 user_id/phone/token/openid/billing
- [ ] Admin 用户管理/分享设置生效
- [ ] HTTPS 域名配置完成
- [ ] 微信后台隐私指引配置完成
- [ ] 微信后台服务器域名配置完成
- [ ] 无 AppSecret/API key/PEM/私钥泄露到前端/dist/commit

### No-Go 条件（任一触发禁止上线）

- [ ] analyze 真机超时且兜底恢复失败（用户扣点但拿不到报告）
- [ ] 微信登录失败且密码登录 fallback 也失败
- [ ] 生成的报告无法打开（report-detail 白屏或 404）
- [ ] 扣点异常（重复扣点、会员被扣点、退款失败）
- [ ] 分享接口泄露 user_id/phone/token/openid 等隐私字段
- [ ] 生产环境使用 HTTP（非 HTTPS）API 域名
- [ ] 支付入口出现假成功（未配置商户却提示支付成功）
- [ ] commit / dist / 源代码中发现真实密钥

---

## 五、文档维护

- 本文件随 RC 状态更新，非代码文件，不参与 build。
- 上线后发现新问题，及时追加到"已知非阻塞问题"或升级为阻塞。
- Go/No-Go 条件在每次验证后勾选。
