# 址得选 — AI 驱动的连锁餐饮与零售选址专家系统

## 产品简介

址得选是面向线下实体商业的 AI 选址分析平台。用户在地图上选定门店位置、填写业态与品牌信息后，系统自动采集周边 POI 数据（200m/500m/1000m 三层半径），调用大模型进行 8 维度商业分析，生成包含综合评分、竞争格局、盈亏测算的专业选址报告。

### 核心能力

- **34 种业态深度适配** — 覆盖餐饮、酒店、零售、生活服务、休闲娱乐五大行业，43 个前台入口 → 14 个 Master 业态集群 → 每集群独立 Rigor 规则引擎（direct/substitute/anchor/irrelevant 四层分类），支持子业态精准分流
- **双层 POI 数据采集** — 高德 Web API 后端代理，28 大类别 6 层数据脱水过滤，最大 550 条周边数据
- **AI 选址分析引擎** — 动态 System Prompt 拼接 + 14 套 Master 专属规则 + subtype 子业态分流 + Python 层互斥预判 + 维度加权平均锁定总分
- **报告事实校验 Guard** — P0 POI 名称引用校验 + P2 竞品语境误用检测 + P3 竞品数量膨胀检测 → hard-error → retry → 仍失败退款/不保存
- **SSE 实时流式分析** — 四步进度推送，免疫代理缓冲
- **双重计费系统** — 会员订阅制（月度/季度/年度）+ 点数余额制 + CDK 兑换码激活
- **管理后台** — key 池管理、业态配置热更新、用户管理、SKU 套餐管理、UI 配置、操作审计日志
- **微信支付** — JSAPI v3 完整链路（prepay + notify 验签解密 + PaymentOrder 持久化）+ 小程序虚拟支付（wx.requestVirtualPayment 道具直购）

---

## 技术架构

| 层 | 技术选型 |
|---|---------|
| 客户端 | uni-app (Vue 3 + Vite) → 微信小程序 / 抖音 / App 多端 |
| 后端 | Python FastAPI + SQLAlchemy ORM + SQLite (WAL 高并发模式) |
| 地图 | 高德 Web API v3（后端代理，客户端不暴露 Key） |
| AI | DeepSeek / OpenAI / Gemini / Kimi / MiniMax / 智谱 GLM（`.env` 一键切换） |
| 鉴权 | PyJWT HS256 (168h expiry) + Bearer Token + Admin Role 校验 |
| 实时流 | FastAPI StreamingResponse + SSE (Server-Sent Events) |
| 部署 | 宝塔面板 + Nginx 反向代理 + uvicorn |

---

## 项目结构

```
location-tool/
├── README.md
├── backend/
│   ├── .env.example                   # 环境变量模板
│   ├── requirements.txt               # Python 依赖
│   ├── main.py                        # FastAPI 入口 + SSE 端点 + 全局异常处理
│   ├── auth.py                        # JWT 鉴权
│   ├── config.py                      # 统一配置中心
│   ├── database.py                    # SQLAlchemy 引擎 + WAL 模式
│   ├── report_fact_guard.py           # 报告事实校验（纯函数）
│   ├── ai_providers/                  # 大模型适配层（6 家厂商，统一入口 unified.py）
│   ├── models/                        # Pydantic 请求模型 + SQLAlchemy ORM（9 张表）
│   ├── prompts/                       # AI 提示词系统（14 套 Master 业态规则）
│   ├── routers/                       # RESTful API 路由（11 个模块：admin/auth/user/records/favorites/location/pay/virtual_pay/feedback/industries/cdk）
│   ├── services/                      # 业务服务（amap/billing/runtime_config/storage/poi_name_guard/fallback_report_service）
│   ├── tests/                         # 测试套件（industry 2168 PASS / fact guard 175 PASS）
│   └── storage/                       # 运行时文件存储（reports/assets）
├── uniapp/                            # uni-app 多端客户端（主力产品）
│   ├── src/pages/                     # 13 个页面（home/records/favorites/report-detail/profile/legal）
│   ├── src/components/                # 8 个组件（address-input/industry-picker/report-card/tab panels）
│   ├── src/utils/                     # API 客户端 / 认证 / 格式化工具
│   └── package.json
├── miniprogram/                       # 原生微信小程序（登录参考 scaffold）
└── logo-1/                            # 品牌素材
```

---

## 快速启动（本地开发）

### 1. 环境配置

复制 `backend/.env.example` 为 `backend/.env`，编辑以下必填项：

```env
# ★ 必填：大模型配置
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-your-key-here

# ★ 必填：高德地图
AMAP_WEB_KEY=your_amap_web_key
AMAP_SECURITY_CODE=your_amap_sec_code

# ★ 必填：JWT 鉴权（生产环境务必替换为随机长字符串）
JWT_SECRET=change-this-to-a-random-secret-in-production

# ★ 必填：管理后台密码
ADMIN_PASSWORD=your_secure_password
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000
# Swagger 文档 → http://localhost:8000/docs
```

### 3. 启动 uni-app 开发

```bash
cd uniapp
npm install
npm run dev:mp-weixin
# 用微信开发者工具打开 dist/build/mp-weixin
```

如需切换到其他平台：
```bash
npm run dev:mp-toutiao    # 抖音小程序
npm run dev:app-plus      # App
npm run dev:h5            # H5 网页
```

### 4. 管理后台

独立 HTML 管理后台（`/admin`），8 个导航模块完整功能：

```bash
http://localhost:8000/admin          # 管理后台（后台独立页面，非 Swagger）
http://localhost:8000/docs           # Swagger API 文档（调试用）
```

主要管理接口：
- `POST /api/admin/login` — 管理员登录
- `GET/PUT /api/admin/config` — 核心配置管理
- `GET/POST/PUT/DELETE /api/admin/amap-keys` — 高德 Key 池管理
- `GET/PUT /api/admin/skus` — 套餐/定价管理
- `POST /api/admin/cdk/generate` — CDK 批量生成
- `GET /api/admin/users` — 用户管理
- `GET /api/admin/stats` — 仪表盘统计

---

## 计费模型

### 会员订阅

| 档位 | 时长 | 权益 |
|------|------|------|
| 月度会员 | 30 天 | 无限次分析 |
| 季度会员 | 90 天 | 无限次分析 |
| 年度会员 | 365 天 | 无限次分析 |

### 点数包

| 档位 | 点数 |
|------|------|
| 体验包 | 1 点 |
| 标准包 | 5 点 |
| 专业包 | 25 点 |
| 企业包 | 100 点 |

会员有效期内分析免费；非会员每次分析消耗 1 点。CDK 兑换码支持后台批量生成。

---

## 版本历史

- **v3.9.0** (2026-06-08) — 退款全链路闭环：用户一键申请 + 自动退款 + 5次轮询 + 自动扣点 REFUNDED；退款余额不足硬拦截（不退钱不退点）；_revoke_order 幂等扣点（负数 REFUND 流水去重 + REFUND_SHORTFALL 兜底）；XPay 退款签名算法修复（endpoint&body HMAC-SHA256）；admin 退款同步兜底；订单管理 REFUNDING 行同步退款按钮；pay-existing 继续支付（超30分自动 TIMEOUT）；prepay 统一 _get_virtual_env 环境读取；前端充值前自动 refreshWxLogin 防 session_key 过期；管理后台 F5 hash 记忆当前页；管理后台报告库（列表筛选 + 三源报告详情 + 抽屉全屏 + 锚点导航）；POI 数据表格化展示；用户端 UI 重写（自定义导航/订单卡片/详情页/登录弹窗/按钮统一）；服务器时区 Asia/Shanghai 全局统一
- **v3.8.0** (2026-06-05) — 虚拟支付全链路闭环：notify 六重校验 + 退款回退权益；iOS 正式 Key 打通；用户充值记录页；管理后台订单渠道 + 反馈删除；腾讯云 COS 集成
- **v3.7.0** (2026-06-04) — 上线前收口：支付 500 修复、AppID 一致性校验、openid 自动刷新、分享图预加载+下载、下拉刷新 5 页面、管理后台重置微信登录、公交措辞修正、data_quality_notes 修复、401 全局 token 清理
- **v1.15.1** (2026-06-01) — Codex UI 精细收口：管理后台仪表盘交互折线图、分享图拆分首页/报告独立封面、用户列表会员友好化、业态按类目分组、操作记录美化；前端 ProfilePanel 图标改用 PNG、首页和报告分享封面独立配置
- **v1.15.0** (2026-06-01) — C-4 报告幻觉专项 + 管理后台 SaaS 闭环：POI 名称校验 retry 白名单收窄、retry prompt 注入强约束、模板去诱导；后台新增订单管理+点数流水、业态 CRUD、SKU/CDK/二维码/Key池接口对齐；fact guard 175 PASS
- **v1.14.0** (2026-06-01) — 上线闭环与安全加固：支付 queryOrder 确认闭环、.gitignore 防护、管理后台 search→phone 修复、innerHTML XSS 转义、匿名设备 ID 去硬编码、退款幂等保护、location key 池完整重试、文档统一
- **v1.13.0** (2026-05-30) — 管理后台重建 + 微信支付接入：全新独立 HTML 管理后台（`/admin`），8 模块功能完整对齐旧版；系统设置含 7 子标签（核心配置/UI/分享/二维码/SKU/Key池/存储）；业态规则从 industry_config.py 直接读取；仪表盘含 15 天趋势图；微信支付 JSAPI v3 完整链路（prepay + notify）；小程序充值页接入真实支付；死代码清理 ~1,000 行；P0 计费时序修复；B26/B27 修复
- **v1.12.0** (2026-05-30) — 项目简化与安全加固：移除 Web 前端（React），uni-app 成为唯一客户端；后端 location 端点接入 Key 池实现配额自动切换；计费扣点时序优化（AMap 成功后再 commit，失败则 rollback）；uniapp 4 页面 safe-area-inset-bottom iPhone 适配
- **v1.11.0** (2026-05-29) — 小程序 UI 精细化收口：`compactAddress` 地址简写增强，四 tab 底部间距统一，guest 未登录态布局修复，Profile 页脚文案优化，首页/收藏页脚 padding 平衡，Profile 页面重构。check_industry_rigor_rules.py 2168 PASS / check_report_fact_guard.py 147 PASS
- **v1.10.0** (2026-05-26) — 上线收口：微信支付后台 PEM 证书配置闭环，头像持久化上传，登录后 onboarding 流程，快捷登录错误引导，法律页面（用户协议/隐私政策），Admin 用户管理展示头像昵称。2168/147 PASS
- **v1.9.0** (2026-05-26) — uni-app 登录/充值/CDK 独立页面化：快捷登录/密码登录/注册、兑换码独立页、充值中心独立页，微信支付后端（JSAPI v3），User.nickname 字段 DB 迁移。2168/147 PASS
- **v1.8.0** (2026-05-23) — uni-app Home 首页视觉重做：品牌 logo lockup、搜索浮卡、地图模块、业态卡片、Feature tiles 信任条，二级页面视觉对齐，真实收藏 API 集成，免费额度倒计时 + 全局公告。2168/147 PASS
- **v1.7.0** (2026-05-23) — uni-app 多端客户端接近完成：地址自动联想，地图点选/定位，分析接口 SSE 流集成，Web 母版对齐原则。2168/147 PASS
- **v1.6.0** (2026-05-21) — 多端客户端基线与资金安全加固：新增 uni-app 客户端，资金安全修复（DB保存失败→退款、PDF并发解锁回滚），微信小程序登录端点。2168/147 PASS
- **v1.5.0** (2026-05-20) — 上线前精准度全线收口：P0/P2/P3 升级为 hard-error，7 个高风险 master strict_exclude_names，禁止推荐/不推荐决策语言检测，财务单点精确数字检测。2168/101 PASS
- **v1.4.0** (2026-05-19) — Master 业态映射修复与正式保存链路扩样：14 master 业态名自映射缺失修复，33 次正式 API 保存链路回归。2158/92 PASS
- **v1.3.0** (2026-05-18) — 报告精准度防线加固：fact_errors 后免费重试 fallback，报告边界声明强制初筛参考，餐饮 Sample Bank 加厚。1902/92 PASS
- **v1.2.0** (2026-05-15) — 报告精准度体系化收口：7/7 master req_kw=True 消除高风险 code 裸奔，new category + 脱水函数，C-1/C-2 真实报告验收。1876/86 PASS
- **v1.1.2** (2026-05-14) — Guard 体系上线：P0/P2/P3 三层 warning-only，离线验收样本归零。1598/50 PASS
- **v1.1.1** (2026-05-13) — POI 分类精准度全面整改：医院归并去重、住宅/便利店/药店/酒店名称脱水、14 业态 subtype 深化、6 个新 category 打通真实采集链路。1291 PASS
- **v1.0.0** (2026-05-09) — 正式生产版

---

# 宝塔面板生产环境部署指南

> 适用版本：宝塔 Linux 面板 9.x | 更新日期：2026-05-30

## 部署架构

```
用户 → 微信小程序
        │
        ▼
Nginx (HTTPS, 宝塔面板)
        │
        ├── /api/* → proxy_pass → localhost:8000 (FastAPI + uvicorn)
        ├── /assets/ → proxy_pass → localhost:8000
        └── /docs → proxy_pass → localhost:8000
                │
                ▼
        FastAPI (uvicorn, port 8000) + SQLite (WAL mode)
```

## 第一步：上传项目

```bash
# 在宝塔"文件"页面或通过 SFTP，将整个项目上传到
/www/wwwroot/location-tool/
```

## 第二步：Python 环境

宝塔默认已安装 Python 3.x。在宝塔"网站 → Python项目"中添加：

| 配置项 | 值 |
|--------|-----|
| 项目路径 | `/www/wwwroot/location-tool/backend` |
| 启动文件 | `main.py` |
| 运行端口 | `8000` |
| 框架 | FastAPI |

或手动启动：
```bash
cd /www/wwwroot/location-tool/backend
pip install -r requirements.txt
nohup python main.py > /tmp/zdx-api.log 2>&1 &
```

## 第三步：Nginx 反向代理

在宝塔网站设置 → 配置文件 中添加：

```nginx
server {
    listen 80;
    server_name api.your-domain.com;

    client_max_body_size 10m;
    proxy_read_timeout 180s;   # SSE 流式分析可能超过 60s

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_buffering off;           # ★ SSE 必须关闭缓冲
    }

    location /assets/ {
        proxy_pass http://127.0.0.1:8000;
    }

    location /docs {
        proxy_pass http://127.0.0.1:8000;
    }

    location /admin {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

> **注意**：`proxy_buffering off` 和 `proxy_read_timeout 180s` 是 SSE 流式分析正常运行的关键配置。

## 第四步：配置环境变量

编辑 `/www/wwwroot/location-tool/backend/.env`，填入真实的 Key 和密码：

```env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-real-key-here

AMAP_WEB_KEY=real_amap_key_here
AMAP_SECURITY_CODE=real_security_code

JWT_SECRET=<生成一个64位随机字符串>
ADMIN_PASSWORD=<设置强密码>
```

## 第五步：SSL 证书

在宝塔"网站 → SSL"中申请 Let's Encrypt 免费证书，或上传已有证书。

## 第六步：uni-app 小程序发布

```bash
cd /www/wwwroot/location-tool/uniapp
npm install
npm run build:mp-weixin
```

将 `dist/build/mp-weixin/` 目录用微信开发者工具打开，上传审核。

> **注意**：编译前确认 `src/utils/config.js` 中的 `API_BASE_URL` 指向生产环境域名。

---

## 数据库管理

SQLite 数据库位于 `backend/location_tool.db`，建议定期备份：

```bash
cp /www/wwwroot/location-tool/backend/location_tool.db \
   /www/backup/zdx-$(date +%Y%m%d).db
```

WAL 模式会自动生成 `-wal` 和 `-shm` 文件，备份时一起复制。

---

## 常用运维命令

```bash
# 查看后端日志
tail -f /tmp/zdx-api.log

# 重启后端
pkill -f "python main.py" && cd /www/wwwroot/location-tool/backend && nohup python main.py > /tmp/zdx-api.log 2>&1 &

# 验证后端健康
curl http://localhost:8000/api/health

# 运行测试
cd /www/wwwroot/location-tool/backend
python -m compileall .
python tests/check_industry_rigor_rules.py
python tests/check_report_fact_guard.py
```

---

## 安全清单

- [ ] `.env` 已加入 `.gitignore`，未提交到 Git
- [ ] `JWT_SECRET` 已替换为高强度随机字符串（非默认值）
- [ ] `ADMIN_PASSWORD` 已设置强密码
- [ ] Nginx 已配置 SSL 证书
- [ ] 管理后台 `/docs` 建议加 IP 白名单（宝塔 Nginx 可配 `allow/deny`）
- [ ] 数据库文件权限设为 600（`chmod 600 location_tool.db`）
- [ ] 高德 Key 已通过管理后台 Key 池配置（支持自动故障切换）
