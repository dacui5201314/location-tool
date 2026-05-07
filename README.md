# AI选址 · 智赢未来

## 软件概述

面向线下实体商业的 AI 驱动选址分析工具。用户在地图上选定门店位置、填写业态与品牌信息后，系统自动采集周边 POI 数据（200m/500m/1000m 三层半径），调用大模型进行多维度商业分析，生成包含综合评分、竞争格局、盈亏测算的选址报告，并支持 PDF 导出。

### 核心能力

- **POI 数据采集**：高德地图 Web API + JS API 双通道，覆盖 14 大类别、6 层数据脱水过滤
- **AI 选址分析**：14 个业态集群 × 5 维参数 × 动态阈值判定，支持 32 个细分业态
- **财务精算**：基于门店面积自动推算租金、人工、盈亏平衡点
- **品牌匹配**：品牌客单价与周边客群消费力交叉校验，品类锁定防策略偏离
- **PDF 报告**：前端高保真渲染 + 评分环 + 雷达图 + POI 数据表格 + 引流 Footer
- **用户系统**：JWT 鉴权 + 分析记录存档 + 地址收藏 + 双轨制计费（会员订阅 / 点数余额）+ 管理后台
- **SSE 实时流**：StreamingResponse 四步进度推送 + 前端极客控制台逐帧动画，免疫代理缓冲
- **PDF 导出引擎**：html2pdf.js 分页 + 零高度物理切断 + inline-block 原子防断 + 800px A4 黄金宽度
- **业态专属规则引擎**：数据库驱动业态配置 + Admin 可视化管理 + 专属 Prompt 动态拼接注入 LLM

### 技术栈

| 层 | 技术 |
|---|------|
| 前端 | React 18 + Vite 6 + Tailwind CSS + react-router-dom v7 |
| 后端 | Python FastAPI + SQLAlchemy + SQLite (WAL 模式) |
| 地图 | 高德 JS API 2.0 + Web API v3（环境变量注入 Key） |
| AI | DeepSeek / OpenAI / Gemini / Kimi / MiniMax / 智谱（通过 .env 切换） |
| 鉴权 | PyJWT (HS256, 72h expiry) + Bearer Token |
| PDF | html2pdf.js（iframe 独立渲染上下文 + page-break CSS 智能分页 + .pdf-no-break 防断） |
| 实时流 | FastAPI StreamingResponse + SSE + 前端 ReadableStream 逐帧动画回放 |
| 安全 | JWT Bearer + Canvas 指纹 + 原子化 UPDATE 防 TOCTOU + html.escape 防 XSS |

---

## 目录结构

```
location-tool/
├── README.md                          # 本文档
├── backend/                           # Python 后端
│   ├── .env                           # 环境变量（API Key、数据库配置）
│   ├── .env.example                   # 环境变量模板（含详细注释）
│   ├── requirements.txt               # Python 依赖清单
│   ├── config.py                      # 统一配置中心：JWT、LLM 参数、API Key
│   ├── auth.py                        # ★ JWT 鉴权：签发/校验 + FastAPI 依赖注入
│   ├── database.py                    # SQLAlchemy 引擎 + Session 管理 + WAL 模式
│   ├── main.py                        # FastAPI 入口：路由注册、分析端点、JWT 鉴权
│   │
│   ├── ai_providers/                  # 大模型调用适配层
│   │   ├── __init__.py                # Provider 工厂注册
│   │   ├── base.py                    # 抽象基类 BaseProvider
│   │   ├── unified.py                 # ★ 统一入口 generate_llm_response()
│   │   ├── deepseek.py               # DeepSeek API 适配
│   │   ├── gemini.py                  # Google Gemini API 适配
│   │   ├── kimi.py                    # Moonshot Kimi API 适配
│   │   ├── minimax.py                 # MiniMax API 适配
│   │   └── zhipu.py                   # 智谱 GLM API 适配
│   │
│   ├── models/                        # 数据模型
│   │   ├── schemas.py                 # Pydantic 请求/响应模型
│   │   └── db_models.py              # SQLAlchemy ORM：User/AnalysisRecord/SavedLocation/RedeemCode/SystemConfig/OperationLog/BillingRecord
│   │
│   ├── prompts/                       # AI 提示词系统
│   │   ├── industry_config.py         # ★ 14个业态母版配置（权重/阈值/关键词/策略）
│   │   ├── location_analysis.py       # ★ 动态 System Prompt + Python层互斥预判
│   │   └── business_profiles.py       # 38个业态详细画像库
│   │
│   ├── routers/                       # RESTful API 路由
│   │   ├── __init__.py
│   │   ├── auth.py                    # ★ JWT Token 签发 + 设备指纹防刷
│   │   ├── records.py                 # 分析记录 CRUD + PDF解锁（原子化） + 报告下载
│   │   ├── favorites.py               # 收藏地址 CRUD + 跨表校验 is_analyzed
│   │   ├── user.py                    # 用户中心（profile/consume/设备防刷/免费点数限时）
│   │   ├── admin.py                   # 管理后台（JWT Admin 鉴权 / 仪表盘 / 用户 / CDK / 配置）
│   │   └── industries.py              # ★ 业态专属规则引擎（CRUD + 公开匹配 + OperationLog 审计）
│   │
│   ├── services/                      # 业务服务
│   │   ├── __init__.py
│   │   ├── amap_service.py            # ★ 高德 POI 采集：搜索/分类/脱水/竞品检测
│   │   ├── billing_service.py         # ★ 统一计费校验：会员优先 + 原子化点数扣除 + 免费过期原子判定
│   │   ├── runtime_config.py          # ★ 运行时配置引擎：DB 持久化配置 / SKU 管理 / LLM 动态切换 / 报告归一化
│   │   └── storage_service.py         # ★ 报告存储：本地/云端 OSS + Fallback + HTML 生成（XSS 安全）
│   │
│   └── storage/                       # 文件存储（运行时生成）
│       ├── reports/                   # PDF/HTML 报告文件
│       └── assets/                    # 上传资源（公众号二维码等）
│
├── frontend/                          # React 前端
│   ├── index.html                     # HTML 入口（标题 + Favicon）
│   ├── .env.local                     # Vite 环境变量（高德 Key）
│   ├── package.json                   # npm 依赖
│   ├── vite.config.js                 # Vite 配置 + API 代理
│   ├── tailwind.config.js             # Tailwind 配置
│   ├── postcss.config.js              # PostCSS 配置
│   │
│   ├── public/
│   │   ├── favicon.png                # 浏览器标签页图标
│   │   ├── brand-logo-icon.png        # 品牌 Logo
│   │   └── brand-lockup.png           # 品牌组合标识
│   │
│   └── src/
│       ├── main.jsx                   # React 入口 + BrowserRouter
│       ├── App.jsx                    # ★ 路由表：MainLayout + /admin + /record/:id
│       ├── index.css                  # 全局样式：设计系统变量、卡片、按钮
│       │
│       ├── layouts/
│       │   └── MainLayout.jsx         # ★ App Shell：TabBar + Outlet
│       │
│       ├── pages/
│       │   ├── HomePage.jsx           # ★ 主页：地图 + 搜索 + 表单 + 分析 + JWT 初始化
│       │   ├── RecordDetail.jsx       # 报告详情页：统一 AnalysisResult + PDF 下载
│       │   └── AdminPage.jsx          # 管理后台：JWT Admin 鉴权 / 仪表盘 / 配置
│       │
│       ├── components/
│       │   ├── MapView.jsx            # 高德地图：点击选点 + 拖拽 + 逆地理编码 + 错误降级
│       │   ├── AddressInput.jsx       # 地址搜索：AutoComplete + PlaceSearch + Geolocation
│       │   ├── BusinessTypeSelector.jsx # 选址业态：8大类主业态 + 细分业态面板
│       │   ├── BrandInput.jsx         # 品牌名称输入 + 实时校验
│       │   ├── StoreSizeInput.jsx     # 门店面积输入 + 数字过滤 + ㎡后缀
│       │   ├── AnalysisResult.jsx     # ★ 分析结果展示：评分环 + 雷达图 + POI 数据表格 + 维度分析
│       │   ├── RadarChart.jsx         # 纯 SVG 雷达图（含无障碍 title/desc）
│       │   ├── PdfExport.jsx          # PDF 导出：Portal 渲染 + 统一 useReportExport Hook
│       │   ├── RecordsView.jsx        # 分析记录列表 + 删除确认 + 统一导出
│       │   ├── FavoriteView.jsx       # 收藏地址列表 + 状态标签 + 发起分析
│       │   ├── ProfileView.jsx        # 个人中心 + 双轨充值（会员/点数） + 倒计时
│       │   ├── LoadingSpinner.jsx     # 加载动画
│       │   └── ErrorBoundary.jsx      # 错误边界：捕获崩溃显示重试
│       │
│       ├── hooks/
│       │   ├── useAMap.js             # 高德地图加载 + 插件初始化 + Key 校验
│       │   ├── useFetch.js            # 安全数据请求：AbortController + JWT 自动注入 + isMounted
│       │   └── useReportExport.jsx    # ★ 全局统一 PDF 导出 Hook：计费 → 解锁 → 高保真导出
│       │
│       ├── services/
│       │   ├── api.js                 # ★ API 客户端：JWT 拦截器 + authFetch + 全部业务接口
│       │   └── amapData.js            # 前端 JS API POI 采集 + 中文分类器
│       │
│       └── utils/
│           ├── constants.js           # AMap Key（Vite 环境变量注入）+ 业态映射
│           ├── deviceId.js            # ★ Canvas 指纹 + Browser 属性 + localStorage 三层设备标识
│           └── exportToPDF.js         # ★ 高保真 PDF 引擎：RAF 轮询图表就绪 + 图形冻结 + html2canvas
```

---

## 快速启动

### 环境准备

**后端 `.env`（`backend/.env`）：**
```env
# 大模型（推荐：只需配 LLM_PROVIDER + LLM_API_KEY）
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxx

# 各平台独立 Key（旧版兼容，保留可用）
DEEPSEEK_API_KEY=sk-xxx
GEMINI_API_KEY=xxx
KIMI_API_KEY=xxx
MINIMAX_API_KEY=xxx
ZHIPU_API_KEY=xxx

# 高德地图
AMAP_WEB_KEY=xxx
AMAP_SECURITY_CODE=xxx

# JWT 鉴权
JWT_SECRET=change-this-to-a-random-secret-in-production
JWT_EXPIRY_HOURS=72

# 管理后台
ADMIN_PASSWORD=your_secure_password
```

**前端 `.env.local`（`frontend/.env.local`）：**
```env
VITE_AMAP_KEY=你的高德JS_API_Key
VITE_AMAP_SECURITY_CODE=你的高德安全密钥
```

### 后端

```bash
cd backend
uv run python main.py
# 或：uv run uvicorn main:app --host 0.0.0.0 --port 8000
# 启动于 http://localhost:8000
```

### 前端

```bash
cd frontend
npm install
npx vite --host
# 启动于 http://localhost:5173
```

---

## 核心业务流程

```
用户访问 → Canvas 指纹采集 → POST /api/auth/token → JWT 签发
  → 选择位置 → 填写业态/品牌/面积
  → 前端 PlaceSearch 采集 POI（备用通道）
  → 后端 AmapService 采集 POI（主通道）
  → 6层数据脱水过滤
  → 行业配置匹配（14母版 → 32业态）
  → 构建动态 System Prompt + Python层互斥预判
  → ★ JWT 鉴权 → 计费校验：会员优先 → 原子化点数扣除（含免费过期判定）→ 拦截
  → generate_llm_response() 调用大模型
  → 解析 JSON → 存入 AnalysisRecord（含完整 real_data）
  → 保存报告物理文件到 storage/reports/（支持本地/OSS 双向 Fallback）
  → 返回前端展示：评分环 + 雷达图 + POI 数据 + 维度分析
  → 可选：收藏地址 / 导出 PDF（RAF 轮询图表就绪 + Canvas/SVG 静态化）
```

---

## API 端点总览

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| GET | `/api/health` | 无 | 健康检查 |
| GET | `/api/providers` | 无 | AI 提供商列表 |
| POST | `/api/auth/token` | 设备指纹 | ★ JWT 签发 + 多端身份绑定 + 防刷注册 |
| POST | `/api/auth/register` | 无 | ★ 手机号+密码注册（PBKDF2 哈希） |
| POST | `/api/auth/login` | 无 | ★ 手机号+密码登录 |
| POST | `/api/auth/wechat/official` | 微信 code | ★ 公众号网页授权登录（code→openid→JWT） |
| POST | `/api/analyze` | JWT | ★ 执行选址分析（含计费校验） |
| GET | `/api/records` | JWT | 分析记录列表（分页） |
| GET | `/api/records/{id}` | JWT | 分析记录详情（含完整 report_json） |
| DELETE | `/api/records/{id}` | JWT | 删除记录 |
| POST | `/api/records/{id}/unlock-pdf` | JWT | ★ PDF 导出解锁（原子化防双扣） |
| GET | `/api/records/{id}/download` | JWT | 动态获取报告 HTML 文件（含存储 Fallback） |
| GET | `/api/favorites` | JWT | 收藏列表（含 is_analyzed） |
| GET | `/api/favorites/check` | JWT | 检查坐标是否已收藏 |
| POST | `/api/favorites` | JWT | 添加收藏 |
| DELETE | `/api/favorites/{id}` | JWT | 取消收藏 |
| GET | `/api/user/profile` | JWT | ★ 用户信息 + 会员/点数状态 |
| POST | `/api/admin/login` | 密码 Body | ★ 管理员登录（JWT 签发，role=admin） |
| GET | `/api/admin/stats` | JWT Admin | 仪表盘统计 |
| GET | `/api/admin/users` | JWT Admin | 用户列表 |
| POST | `/api/admin/users/{id}/add-credits` | JWT Admin | 增加点数 |
| GET | `/api/admin/orders` | JWT Admin | 充值记录（预留） |
| GET/PUT | `/api/admin/skus` | 无 / JWT Admin | 套餐管理 |
| PUT | `/api/admin/config` | JWT Admin | 系统配置（敏感，仅管理员可写） |
| GET/PUT | `/api/admin/ui-config` | 无 / JWT Admin | 全局公告/客服名称/二维码配置 |
| GET/PUT | `/api/admin/pdf-config` | JWT Admin | PDF 品牌定制（管理员可读写） |
| GET/PUT | `/api/admin/storage-config` | JWT Admin | ★ 对象存储配置（含 OSS 密钥，管理员可读写） |
| GET | `/api/admin/qrcode` | 无 | 获取公众号二维码 |
| POST | `/api/admin/upload-qrcode` | JWT Admin | 上传公众号二维码 |
| POST | `/api/admin/cdk/generate` | JWT Admin | 生成兑换码 |
| GET | `/api/admin/cdk/list` | JWT Admin | 兑换码列表 |
| POST | `/api/admin/cdk/activate` | IP 限速 | ★ 激活兑换码（原子化防一码多充 + 5次/分钟限速） |
| GET/PUT | `/api/admin/system-settings` | JWT Admin | ★ 全局参数配置（注册奖励 / 微信各端密钥） |
| GET | `/api/admin/logs` | JWT Admin | 系统日志 |
| GET | `/api/admin/trends` | JWT Admin | 搜索趋势看板 |
| GET | `/api/admin/dashboard/stats` | JWT Admin | ★ 仪表盘聚合（15天趋势+业态/品牌TOP分布） |
| POST | `/api/admin/users/{id}/package` | JWT Admin | ★ 为用户分配预设套餐（会员/点数包） |
| POST | `/api/admin/users/{id}/points` | JWT Admin | ★ 独立调整用户点数（正负+审计备注） |
| GET | `/api/admin/config/core-prompt` | JWT Admin | ★ 获取当前 System Prompt |
| POST | `/api/admin/config/prompt` | JWT Admin | ★ 热更新 System Prompt |
| GET | `/api/admin/operation-logs` | JWT Admin | ★ 管理员操作审计日志 |
| GET | `/api/admin/industries` | JWT Admin | ★ 业态规则列表 |
| POST | `/api/admin/industries` | JWT Admin | ★ 新增业态 |
| PUT | `/api/admin/industries/{id}` | JWT Admin | ★ 更新业态（含专属 Prompt） |
| DELETE | `/api/admin/industries/{id}` | JWT Admin | ★ 删除业态 |
| GET | `/api/industries/active` | 无 | ★ 前台获取启用业态列表 |
| GET | `/api/industries/match?business_type=xxx` | 无 | ★ 精准匹配业态专属规则 |

---

## 计费系统架构

### 双轨制模型

```
用户请求（分析 / 导出PDF）
  │
  ├─ JWT 鉴权（Authorization: Bearer <token>）
  │
  ├─ 会员有效期内？
  │   └─ YES → 直接放行（不扣点）
  │
  ├─ 会员已过期 / 非会员？
  │   ├─ 有效点数 >= 1？
  │   │   └─ YES → 原子化 UPDATE 扣除，WHERE 同时校验：
  │   │           ① balance_credits >= cost
  │   │           ② free_point_expire_at IS NULL  OR  未过期  OR 已购点数够
  │   │           防 TOCTOU + 免费点数临界点并发
  │   │
  │   └─ 免费点数已过期？
  │       └─ YES → 拦截："请充值"
  │
  └─ 前端 Canvas 设备指纹防刷
      └─ 同设备/IP 24h 内 > 2 账号 → 不赠送初始点数
```

### 会员档位
| 档位 | 价格 | 时长 | 权益 |
|------|------|------|------|
| 月度会员 | ¥88 | 30 天 | 无限次分析 + PDF 导出 |
| 季度会员 | ¥218 | 90 天 | 无限次分析 + PDF 导出 |
| 年度会员 | ¥888 | 365 天 | 无限次分析 + PDF 导出 |

### 点数档位
| 档位 | 价格 | 点数 |
|------|------|------|
| 体验包 | ¥9.9 | 1 点 |
| 标准包 | ¥29.9 | 5 点 |
| 专业包 | ¥99 | 25 点 |
| 企业包 | ¥299 | 100 点 |

---

## 数据脱水引擎

| 类别 | 保留关键词 | 剔除关键词 |
|------|-----------|-----------|
| 医院 | 医院、妇幼保健院、社区卫生服务中心 | 诊所、牙科、门诊、药店、医务室 |
| 学校 | 小学、中学、大学、幼儿园 | 培训、画室、托管、驾校 |
| 写字楼 | 大厦、写字楼、国际中心、商务中心 | 公司、厂房、工业园、公寓 |
| 商场 | 购物中心、百货、商业街、茂 | 建材、批发、农贸、汽配 |
| 住宅 | — | 售楼、中介、销售中心 |
| 酒店 | — | 招待所、农家乐、洗浴、日租房 |

---

## 14 个业态母版配置

| # | 母版 | 覆盖业态 | 核心半径 | 关键权重 |
|---|------|---------|---------|---------|
| 1 | 刚需快餐小吃 | 小餐饮、快餐店、小吃店 | 200m | 竞品30% 人口30% |
| 2 | 大餐饮_火锅_中餐 | 大餐饮、中餐、火锅店 | 1000m | 停车30% 竞品25% |
| 3 | 异国_中高端正餐 | 西餐、日餐 | 1000m | 互补35% 交通20% |
| 4 | 烧烤_夜宵 | 烧烤店 | 1000m | 停车30% 竞品25% |
| 5 | 烘焙甜品 | 烘焙店、甜品店 | 500m | 人口40% |
| 6 | 精品茶饮咖啡 | 奶茶店、咖啡店、饮品店 | 200m | 竞品30% 交通30% |
| 7 | 商务酒店 | 酒店 | 1500m | 交通50% |
| 8 | 民宿青旅 | 民宿、青年旅舍 | 1500m | 交通40% 竞品25% |
| 9 | 高频刚需零售 | 便利店、超市、药店 | 300m | 人口50% 竞品30% |
| 10 | 低频目的零售 | 零售店、服装店、数码店 | 1000m | 互补50% 交通30% |
| 11 | 专业生活服务 | 美容美发、宠物店、健身房 | 800m | 人口60% |
| 12 | 社区基础服务 | 教育培训、洗衣店、诊所 | 800m | 人口55% |
| 13 | 夜经济娱乐 | 酒吧、KTV、网吧 | 1000m | 互补30% 停车30% |
| 14 | 沉浸式社交娱乐 | 剧本杀、台球厅 | 1000m | 互补30% 交通20% |

---

## 安全加固

| 措施 | 位置 | 说明 |
|------|------|------|
| 全站 JWT 鉴权 | `auth.py` + 全部 Router | Bearer Token 保护所有敏感接口，Admin 接口叠加 role 校验 |
| Canvas 设备指纹 | `deviceId.js` | Canvas 渲染 hash + Browser 属性 + localStorage 三层指纹，清除缓存无法绕过 |
| 原子化点数扣除 | `billing_service.py` | `UPDATE ... WHERE balance_credits >= cost AND (free_point_expire_at IS NULL OR ...)` 防 TOCTOU + 免费点数临界并发 |
| CDK 原子激活 | `admin.py` | `UPDATE ... WHERE is_used == 0` 防一码多充 |
| CDK 速率限制 | `admin.py` | IP 滑动窗口 5次/60秒，429 拦截暴力枚举 |
| PDF 解锁原子化 | `records.py` | `UPDATE ... WHERE is_pdf_unlocked == 0` 防双扣 |
| 设备指纹防刷 | `auth.py` | device_id + IP 24h 限制 2 个赠点账号 |
| 免费点数限时 | `db_models.py` | 注册 +24h 过期，SQL 层原子判定 |
| XSS 防御 | `storage_service.py` | `html.escape()` 包裹所有用户输入 |
| Admin 密码防泄漏 | `admin.py` | POST Body 传输密码，永不落入 URL / Nginx 日志 |
| 敏感配置读保护 | `admin.py` | pdf-config / storage-config GET 强制 Admin JWT |
| 前端扣费端点下线 | `user.py` | 移除 `POST /api/user/consume`，计费仅限后端业务流内部调用 |
| SQLite WAL 模式 | `database.py` | WAL 模式读写并发不互斥 |
| Token 抢跑防护 | `api.js` + `useFetch.js` + `App.jsx` | `_tokenPromise` 门控 + `authFetch`/`useFetch` 自动 `await ensureToken()` |
| JWT 过期延长 | `config.py` | 默认 168h（7天），缓解反复掉线触发防刷 |
| API Key 隔离 | `constants.js` | `import.meta.env.VITE_AMAP_KEY` 环境变量注入 |
| AMap 空 Key 降级 | `useAMap.js` | Key 为空时拒绝加载 + 友好错误 UI |
| Error 对象渲染防护 | `HomePage.jsx` | `String(error?.message \|\| error)` |
| 存储 Fallback | `storage_service.py` | 云端/本地双向回退，切换存储模式不丢报告 |
| PDF 图表就绪检测 | `exportToPDF.js` | RAF 轮询 SVG/Canvas 渲染完毕，替代 setTimeout(800) |
| 雷达图无障碍 | `RadarChart.jsx` | `<title>` + `<desc>` + `role="img"` 屏幕阅读器兼容 |
| JWT 弱密钥启动拦截 | `config.py` | 检测到默认 JWT_SECRET 直接 `raise ValueError`，物理杜绝弱密钥部署 |
| 运行时配置引擎 | `runtime_config.py` | DB 持久化运行时配置，SKU/LLM Provider/API Key 动态切换无需重启 |
| 报告归一化 | `runtime_config.py` | `normalize_report_result()` 统一评分计算、执行摘要生成、行动计划模板 |
| 用户专属套餐 | `runtime_config.py` + `admin.py` | Admin 可为单个用户设置独立 SKU 定价策略 |
| 用户模型多端兼容 | `db_models.py` | `wx_openid` / `phone` / `channel` 字段，多端身份统一绑定 |
| 点数流水审计 | `db_models.py` | `BillingRecord` 表，`record_type` 区分 BONUS/PURCHASE/CONSUME/REFUND |
| 新手礼包可视化配置 | `admin.py` + `AdminPage.jsx` | 后台"全局参数"Tab 动态调整赠送点数，DB 持久化即时生效 |
| 前端收藏/记录重构 | `FavoriteView.jsx` / `RecordsView.jsx` | 全新 UI：分类筛选、批量管理、评分星级、导出状态追踪 |
| 手机号注册/登录 | `auth.py` + `LoginModal.jsx` | PBKDF2-SHA256 密码哈希，强制登录门控拦截分析流程 |
| 私域充值闭环 | `ProfileView.jsx` | 模拟支付替换为客服二维码 + CDK 激活，后台动态配置客服信息 |
| 幽灵 UI 裁剪 | `ProfileView.jsx` / `AdminPage.jsx` | 移除 10+ 占位按钮/菜单项（邀请好友/反馈/关于/消息/设置等） |
| 管理后台用户充值 | `AdminPage.jsx` | 增强用户列表（手机号/会员到期/来源渠道）+ 加点数弹窗 |
| 管理员操作审计 | `admin.py` + `db_models.py` | OperationLog 表 + 套餐分配/点数调整/Prompt热更新全量留痕 |
| 管理后台用户筛选 | `admin.py` | 用户列表支持手机号/会员/渠道/注册日期多条件筛选 |
| 系统配置真实持久化 | `admin.py` | `PUT /api/admin/config` 写入 `system_config` 表，刷新不丢 |
| 客服二维码运营配置 | `admin.py` + `AdminPage.jsx` | 后台上传客服二维码 + 名称，前端充值弹窗动态渲染 |
| .gitignore 全量覆盖 | 根/后端/前端 | 3 个 .gitignore，屏蔽 .env/.db/node_modules/chrome-profile 等 |

---

## 版本历史

- **v4.5** (2026-05-07) — 全量业态实战规则库：34 个业态全部注入高质量专属 AI 选址规则（核心关注 / 红线避坑 / 权重调整），每个业态拥有独立的测算策略，LLM 分析精准度大幅提升
- **v4.4** (2026-05-07) — 业态名称精细化：删除 11 条斜杠拼凑名，插入 34 个清爽专业业态名（中餐厅/日料店/咖啡馆/火锅店等），按 6 大类分组展示，前端选择器彻底专业化
- **v4.3** (2026-05-07) — 安全防线加固：SSE 退款精确化（仅 LLM 500 错误退款，客户端断开/JSON解析失败不退款）、管理员登录速率限制（5次/分钟/IP, HTTP 429）、报告 UUID 防遍历（report_uuid 替代自增 id，存量数据已补齐）、API 端点全面 UUID 化
- **v4.2** (2026-05-07) — 安全审计清零：修复 SSE 双重退款 Bug（统一 finally 收口 + GeneratorExit 客户端断开不退款）、清理 api.js 死代码陷阱（analyzeLocation/fetchProviders）、数据驱动业态选择器（config_key + 动态 API 绑定替代 34 个硬编码业态）、消除前后端 AMAP 映射重复
- **v4.1** (2026-05-07) — 业态专属规则引擎：数据库驱动业态配置（business_industries 表）、Admin 可视化管理界面（列表/新增/编辑/规则编辑器抽屉/删除）、专属 Prompt 动态拼接注入 LLM、前台自动匹配 industry_id、OperationLog 全量审计
- **v4.0** (2026-05-07) — 全栈架构重构：SSE 实时分析流（四步进度推送+控制台UI+流中断自动退款）、PDF 引擎彻底重写（html2pdf.js+iframe独立渲染+物理分页+Table/float布局+零高度切断+inline-block防断）、安全防线全线加固（Phase 1-5 审计修复：弱密码拦截/OperationLog审计流水/CDK原子性/竞态修复/N+1性能/死代码清理）、管理员仪表盘（15天趋势+业态/品牌TOP分布+用户多条件筛选）、套餐分配+独立点数调整+Prompt热更新端点、数据精度锁定（后端强制维度平均接管LLM总分+维度固定顺序+Prompt去决策化+JSON尾逗号清洗）、前端三重算分+雷达图ORDER锁+UTC时区修正、综合评分环+高级商务排版
- **v3.8** (2026-05-06) — 运行时配置引擎与后台增强
- **v3.7** (2026-05-05) — 私域运营与账号体系：手机号+密码注册登录、强制登录门控、模拟支付替换为私域客服二维码+CDK、幽灵 UI 裁剪（移除 10+ 占位项）、管理后台用户充值面板、系统配置真实持久化、客服二维码运营配置、.gitignore 全量覆盖
- **v3.6** (2026-05-04) — 商业化增长模块：公众号网页授权登录、用户多端兼容模型（wx_openid/phone/channel）、BillingRecord 点数流水审计、新用户注册奖励可视化后台配置、收藏/记录页面全新 UI 重构、JWT 弱密钥启动拦截
- **v3.5** (2026-05-04) — 安全狙击清零：敏感配置 GET 端点 Admin 鉴权、下线前端 consume 端点、CDK IP 速率限制防暴力枚举、JWT 过期延长至 7 天、Token 抢跑门控消除 401
- **v3.4** (2026-05-04) — 性能优化与安全清零：SQLite WAL 并发、CDK 原子激活防一码多充、存储双向 Fallback、PDF RAF 图表就绪检测、Canvas 指纹强化、幽灵代码清理、雷达图无障碍
- **v3.3** (2026-05-04) — 全站 JWT 鉴权重构：Bearer Token 保护全部敏感接口、Admin JWT role 校验、前端 authFetch 拦截器、设备指纹防刷强化、.env.example 规范化
- **v3.2** (2026-05-03) — 安全审计与加固：原子化计费、XSS 防御、设备防刷、Key 环境变量化、AMap 降级、全量代码审查
- **v3.1** (2026-05-03) — 双轨制计费系统：会员订阅 + 点数余额 + 免费点数限时过期 + 公众号二维码引流 + 统一报告渲染组件 + PDF 导出统一 Hook
- **v3.0** (2026-04-30) — 用户系统、管理后台、动态豁免引擎、双轨制展示、全业态配置重构
- **v2.0** (2026-04-28) — 三层半径数据、雷达图、PDF 导出、品牌分析
- **v1.0** (2026-04-27) — 基础选址分析、单一半径 POI、DeepSeek 集成
