# 址得选 — AI 驱动的连锁餐饮与零售选址专家系统

## 产品简介

址得选是面向线下实体商业的 AI 选址分析平台。用户在地图上选定门店位置、填写业态与品牌信息后，系统自动采集周边 POI 数据（200m/500m/1000m 三层半径），调用大模型进行 10 维度商业分析，生成包含综合评分、竞争格局、盈亏测算的专业选址报告，支持高保真 PDF 导出。

### 核心能力

- **34 种业态深度适配**：覆盖餐饮（快餐/火锅/正餐/茶饮/烘焙）、酒店住宿、零售商业、生活服务、休闲娱乐五大行业，每种业态拥有独立的专属 AI 测算规则与权重配置
- **双层 POI 数据采集**：高德 Web API + JS API 双通道，14 大类别 6 层数据脱水过滤，最大 450 条周边数据
- **AI 选址分析引擎**：动态 System Prompt 拼接 + 34 套业态专属规则注入 + Python 层互斥预判 + 维度平均锁定总分
- **财务精算模型**：基于门店面积自动推算租金、人工、盈亏平衡点
- **SSE 实时流式分析**：四步进度推送 + 前端逐帧动画回放，免疫代理缓冲
- **高保真 PDF 报告**：html2pdf.js 分页引擎 + 评分环 + 纯 SVG 雷达图 + POI 数据表格 + 品牌引流 Footer
- **双重计费系统**：会员订阅制（月度/季度/年度）+ 点数余额制 + CDK 兑换码激活
- **Canvas 硬件级指纹防刷**：三层设备标识（Canvas 渲染 hash + Browser 属性 + localStorage），24h 同设备/IP 限注册
- **管理后台**：仪表盘统计、用户管理、业态规则编辑器、系统配置热更新、操作审计日志

---

## 技术架构

| 层 | 技术选型 |
|---|---------|
| 前端 | React 18 + Vite 6 + Tailwind CSS + react-router-dom v7 |
| 后端 | Python FastAPI + SQLAlchemy ORM + SQLite (WAL 高并发模式) |
| 地图 | 高德 JS API 2.0 + Web API v3 |
| AI | DeepSeek / OpenAI / Gemini / Kimi / MiniMax / 智谱 GLM（`.env` 一键切换） |
| 鉴权 | PyJWT HS256 (168h expiry) + Bearer Token + Admin Role 校验 |
| 实时流 | FastAPI StreamingResponse + SSE (Server-Sent Events) |
| PDF | html2pdf.js + iframe 独立渲染上下文 + page-break 物理分页 |
| 安全 | JWT + UUID 混淆路由 + Canvas 指纹 + 原子化 UPDATE + html.escape XSS 防御 + 全局异常兜底 |

---

## 安全体系

| 机制 | 说明 |
|------|------|
| **UUID 混淆路由** | 所有记录/收藏 API 使用 32 位 hex UUID 替代自增 ID，防遍历攻击 |
| **API 数据脱敏** | 公开接口（`/api/industries/active`）强制剥离 `exclusive_prompt` 等敏感字段 |
| **管理后台双锁** | Admin 接口叠加 role=admin JWT 校验；定价策略（skus）、二维码配置读写均需鉴权 |
| **原子化计费** | `UPDATE ... WHERE balance_credits >= cost AND (free_point_expire_at IS NULL OR ...)` 单条 SQL 防 TOCTOU 并发 |
| **CDK 原子激活** | `UPDATE ... WHERE is_used == 0` + 显式 `db.rollback()` 防一码多充 + 事务锁表 |
| **PDF 解锁原子化** | `UPDATE ... WHERE is_pdf_unlocked == 0` + rollback 防双扣 |
| **SSE 退款精确化** | 仅 LLM 5xx 服务端错误触发退款，客户端断开/JSON 解析失败不退款 |
| **管理员密码防泄漏** | POST Body 传输密码，永不落入 URL/Nginx 日志；前端彻底删除 localStorage 明文存储，仅依赖 JWT |
| **管理员登录限速** | IP 滑动窗口 5 次/60 秒，HTTP 429 防暴力破解 |
| **CDK 激活限速** | IP 滑动窗口 5 次/60 秒，防暴力枚举 |
| **全局异常兜底** | `@app.exception_handler(Exception)` 捕获所有未处理异常，返回 500 JSON 防进程崩溃 |
| **数据库连接池保护** | 所有手动 `SessionLocal()` 包裹 `try...finally: db.close()`，高并发下杜绝连接泄漏 |
| **SQLite WAL 模式** | Write-Ahead Logging 读写并发不互斥 |
| **XSS 防御** | `html.escape()` 包裹所有用户输入；前端 React 默认转义 |
| **AI 供应商隐蔽** | `GET /api/providers` 需 JWT 登录，防匿名者探测底层 LLM 架构 |
| **Canvas 设备指纹** | Canvas 渲染 hash + Browser 属性 + localStorage 三层标识，清除缓存无法绕过 |
| **JWT 弱密钥拦截** | 检测默认 `JWT_SECRET` 直接 `raise ValueError` 启动失败，物理杜绝弱密钥部署 |

---

## 快速启动

### 1. 环境配置

**后端 `backend/.env`（详见 `backend/.env.example`）：**

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

**前端 `frontend/.env.local`：**

```env
VITE_AMAP_KEY=你的高德JS_API_Key
VITE_AMAP_SECURITY_CODE=你的高德安全密钥
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000
```

### 3. 启动前端

```bash
cd frontend
npm install
npx vite --host
# → http://localhost:5173
```

---

## 计费模型

### 会员订阅

| 档位 | 时长 | 权益 |
|------|------|------|
| 月度会员 | 30 天 | 无限次分析 + PDF 导出 |
| 季度会员 | 90 天 | 无限次分析 + PDF 导出 |
| 年度会员 | 365 天 | 无限次分析 + PDF 导出 |

### 点数包

| 档位 | 点数 |
|------|------|
| 体验包 | 1 点 |
| 标准包 | 5 点 |
| 专业包 | 25 点 |
| 企业包 | 100 点 |

会员有效期内分析/导出免费；非会员每次分析消耗 1 点，PDF 导出消耗 1 点。CDK 兑换码支持后台批量生成。

---

## 版本历史

- **v1.0.0** (2026-05-09) — 正式生产版：34 种业态深度适配、SSE 流式分析、高保真 PDF 导出、双重计费系统、管理后台、UUID 混淆路由、全量安全加固（数据脱敏/接口鉴权/原子化计费/连接池保护/事务回滚/全局异常兜底）、Canvas 硬件指纹防刷、全栈死代码清零
- **v0.9** (2026-05-07) — 业态专属规则引擎：数据库驱动业态配置 + Admin 可视化管理 + 34 套专属 Prompt
- **v0.8** (2026-05-07) — 安全防线加固：SSE 退款精确化、UUID 防遍历、管理员限速
- **v0.7** (2026-05-07) — 全栈架构重构：SSE 实时流、PDF 引擎重写、仪表盘
- **v0.6** (2026-05-05) — 私域运营与账号体系
- **v0.5** (2026-05-04) — 商业化增长模块 + 收藏/记录 UI 重构
- **v0.4** (2026-05-04) — 全站 JWT 鉴权重构 + 原子化计费
- **v0.3** (2026-05-03) — 双轨制计费系统
- **v0.2** (2026-04-28) — 三层半径、雷达图、PDF 导出
- **v0.1** (2026-04-27) — 基础选址分析、DeepSeek 集成

---

## 目录结构

```
location-tool/
├── README.md
├── backend/
│   ├── .env.example                   # 环境变量模板
│   ├── requirements.txt               # Python 依赖
│   ├── main.py                        # FastAPI 入口 + SSE 端点 + 全局异常处理
│   ├── auth.py                        # JWT 鉴权：签发/校验/依赖注入
│   ├── config.py                      # 统一配置中心
│   ├── database.py                    # SQLAlchemy 引擎 + WAL 模式
│   ├── ai_providers/                  # 大模型适配层（6 家厂商）
│   ├── models/                        # Pydantic 请求模型 + SQLAlchemy ORM
│   ├── prompts/                       # AI 提示词系统（34 套业态规则）
│   ├── routers/                       # RESTful API 路由（auth/records/favorites/user/admin/industries）
│   ├── services/                      # 业务服务（amap/billing/runtime_config/storage）
│   └── storage/                       # 运行时文件存储
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx                   # React 入口
│       ├── App.jsx                    # 路由表
│       ├── pages/                     # 页面组件（Home/RecordDetail/Admin）
│       ├── components/                # UI 组件（Map/Address/Selectors/Analysis/PDF/Records/Favorites/Profile）
│       ├── hooks/                     # 自定义 Hook（useAMap/useFetch/useReportExport）
│       ├── services/                  # API 客户端 + POI 采集
│       └── utils/                     # 常量/设备指纹/PDF 引擎
└── logo-1/                            # 品牌素材
```
