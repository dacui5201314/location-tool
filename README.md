# 址得选 — AI 驱动的连锁餐饮与零售选址专家系统

## 产品简介

址得选是面向线下实体商业的 AI 选址分析平台。用户在地图上选定门店位置、填写业态与品牌信息后，系统自动采集周边 POI 数据（200m/500m/1000m 三层半径），调用大模型进行 10 维度商业分析，生成包含综合评分、竞争格局、盈亏测算的专业选址报告，支持高保真 PDF 导出。

### 核心能力

- **34 种业态深度适配**：覆盖餐饮、酒店、零售、生活服务、休闲娱乐五大行业，43 个前台入口 → 14 个 Master 业态集群 → 每集群独立 Rigor 规则引擎（direct/substitute/anchor/irrelevant 四层分类），支持子业态精准分流。新增 uni-app 多端客户端（微信小程序优先，后续抖音/App）
- **双层 POI 数据采集**：高德 Web API + JS API 双通道，28 大类别 6 层数据脱水过滤，最大 550 条周边数据
- **AI 选址分析引擎**：动态 System Prompt 拼接 + 14 套 Master 专属规则 + subtype 子业态分流 + Python 层互斥预判 + 维度平均锁定总分
- **财务精算模型**：基于门店面积自动推算租金、人工、盈亏平衡点
- **报告事实校验 Guard**：P0 POI 名称引用校验 + P2 竞品语境误用检测 + P3 竞品数量膨胀检测 → 全部 hard-error → retry fallback → 仍失败退款/不保存（退款率从 28% 降至 5%）；新增禁止推荐/不推荐决策语言检测 + 财务单点精确数字检测
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

## 快速启动（本地开发）

### 1. 环境配置

**后端 `backend/.env`：**

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

- **v1.7.0** (2026-05-23) — uni-app 多端客户端接近完成：地址自动联想对标 Web（@input 显式绑定 + 400ms debounce + 竞态守卫）、地图点选/定位反向地理编码共用、Timeout 三级降级覆盖（getLocation/locationRegeocode/locationSuggest）、分析接口 /api/analyze SSE 流已集成（401/402/5xx/成功→report-detail）。Phase 23N-1 自动联想 98%，Phase 23N-2 分析接口 40%。Web 母版对齐原则正式写入项目文档。check_industry_rigor_rules.py 2168 PASS / check_report_fact_guard.py 147 PASS
- **v1.6.0** (2026-05-21) — 多端客户端基线与资金安全加固：新增uniapp多端客户端（Vue3+Vite+uni-app），6页面+4TabBar+API基座+微信登录联调+地图选点壳，覆盖微信/抖音/App三端路线；资金安全修复（DB保存失败→退款、PDF并发解锁回滚）；微信小程序登录端点（/api/auth/wechat/mini + jscode2session + JWT）；小流量上线执行清单。check_industry_rigor_rules.py 2168 PASS / check_report_fact_guard.py 147 PASS
- **v1.5.0** (2026-05-20) — 上线前精准度全线收口：P0/P2/P3 从 warning-only 升级为 hard-error（编造 POI 名称/substitute 写成 direct/竞品数量膨胀 → retry → 仍失败则退款/不保存）；7 个高风险 master 新增 strict_exclude_names（18 项跨行业强排除词）；火锅_烧烤 sub_first 修复；_check_sentence 容忍从 3x 收窄为 max(expected+3, expected*2)；新增禁止推荐/不推荐决策语言检测 + 财务单点精确数字检测 → fact_errors 硬阻断；AB invariant 锁定未来高风险 code 裸奔风险；5 个 master 补齐 categories_excluded；累计 37 次正式 API 保存报告（DB 74 条），retry 挽救 9/12（75%），退款 2 次（5%）；check_industry_rigor_rules.py 2168 PASS 0 FAIL / check_report_fact_guard.py 101 PASS 0 FAIL
- **v1.4.0** (2026-05-19) — Master 业态映射修复与正式保存链路扩样：修复 BUSINESS_TYPE_TO_MASTER 14 个 master 业态名自映射缺失，消除低频目的零售/民宿青旅/夜经济娱乐 POI 数据为空的链路缺陷；Phase 9D-9G 累计 33 次正式 API 保存链路真实报告（DB max_id 70），retry 挽救 9 次（75%），退款 2 次（6%）；industry 2158 PASS / fact guard 92 PASS
- **v1.3.0** (2026-05-18) — 报告精准度防线加固与真实回归：fact_errors 后免费重试 fallback（退款率 28%→11%，真实验证挽救 3 次）；报告边界声明强制要求"本报告为选址初筛参考，需线下实地核验"；餐饮 Sample Bank 加厚至 1902 PASS；Phase 6 累计 19 次真实报告回归；check_industry_rigor_rules.py 1902 PASS 0 FAIL / check_report_fact_guard.py 92 PASS 0 FAIL
- **v1.2.0** (2026-05-15) — 报告精准度体系化收口：7/7 master req_kw=True 消除高风险 code 裸奔 direct；新增 `low_freq_retail` category + 脱水函数；P0 假阳性窄规则修补；fact_errors 抽取为纯函数 + 旧口径检测；C-1/C-2 真实报告验收；industry 1876 PASS / fact guard 86 PASS
- **v1.1.2** (2026-05-14) — 报告事实校验 Guard 体系上线：P0 POI 名称引用校验、P2 竞品语境误用检测、P3 竞品数量膨胀检测，三层 warning-only；离线验收样本 id=21 P0/P2/P3 归零；check_report_fact_guard.py 50 PASS；check_industry_rigor_rules.py 1598 PASS
- **v1.1.1** (2026-05-13) — POI 分类精准度全面整改：医院归并去重、住宅/便利店/药店/酒店名称脱水全量覆盖、14业态 subtype 深化(高频刚需零售/专业生活服务/社区基础服务/夜经济娱乐/沉浸式社交娱乐)、6 个新 category 打通真实采集链路(education_training/laundry/clinics/fitness/fresh_retail/tobacco_liquor/immersive_entertainment)、商务酒店/民宿青旅 100000 裸 direct 风险消除、anchor 显式测试补强、报告 prompt 产品定位强化(初筛参考/不构成投资建议)、canonical 测试 1291 PASS 0 FAIL
- **v1.0.0** (2026-05-09) — 正式生产版：34 种业态深度适配、SSE 流式分析、高保真 PDF 导出、双重计费系统、管理后台、UUID 混淆路由、全量安全加固、Canvas 硬件指纹防刷、全栈死代码清零
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
│   ├── prompts/                       # AI 提示词系统（14 套 Master 业态规则 + 34 套前台专属 Prompt）
│   ├── routers/                       # RESTful API 路由（auth/records/favorites/user/admin/industries）
│   ├── services/                      # 业务服务（amap/billing/runtime_config/storage/poi_name_guard）
│   ├── tests/                         # 自测套件（check_report_fact_guard/check_industry_rigor_rules）
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

---

# 宝塔面板生产环境部署指南

> 适用版本：宝塔 Linux 面板 9.x | 项目版本：v1.6.0 | 更新日期：2026-05-21
>
> 本指南假设你已经在服务器上安装好宝塔面板，并且已经打开了宝塔面板的网页后台。

## 部署架构

```
用户浏览器
    │
    ▼
┌──────────────────────────────────────┐
│  Nginx (宝塔站点)                      │
│  • 静态文件: frontend/dist/           │
│  • API 反向代理 → localhost:8000      │
│  • 域名 + SSL (Let's Encrypt)         │
└──────────┬───────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│  Uvicorn (Python 项目管理器)           │
│  • FastAPI 后端 :8000                 │
│  • SQLite (WAL 模式)                  │
│  • LLM 多供应商适配                   │
└──────────────────────────────────────┘
```

---

### 零、开始之前：你需要准备的东西

在开始部署之前，请确认你手上有以下资料：

| 序号 | 资料名称 | 说明 | 从哪里获取 |
|------|----------|------|-----------|
| 1 | 服务器 IP | 你的云服务器公网 IP | 阿里云/腾讯云控制台 |
| 2 | 域名 | 已经解析到服务器 IP 的域名 | 域名服务商（如阿里云 DNS） |
| 3 | DeepSeek API Key | LLM 大模型调用密钥 | platform.deepseek.com → API Keys |
| 4 | 高德 Web 服务 Key | 后端 POI 数据采集 | 高德开放平台 → 应用管理 |
| 5 | 高德安全密钥 | 配合 Web 服务 Key 使用 | 同上页面 |
| 6 | 高德 JS API Key | 前端地图显示 | 高德开放平台 → 应用管理（JS API 类型） |
| 7 | 高德 JS 安全密钥 | 配合 JS API Key 使用 | 同上页面 |

> **重要**：高德 Web 服务 Key 和 JS API Key 是**两个不同的 Key**，申请时选择的应用类型不同。前者选"Web 服务"，后者选"JS API"。

---

### 一、宝塔软件商店：安装必要软件

#### 1.1 打开软件商店

登录宝塔面板后，在左侧菜单栏找到 **「软件商店」**（图标是一个购物袋），点击进入。

#### 1.2 安装 Nginx

1. 在软件商店页面的搜索框中输入 **「Nginx」**
2. 在搜索结果中找到 **「Nginx」**（注意不是 Nginx 防火墙，是 Web 服务器那个）
3. 点击它，在弹出的窗口中点击 **「安装」** 按钮
4. 版本选择默认的 **1.24** 或 **1.26** 均可，安装方式选择 **「极速安装」**（不要选编译安装）
5. 点击 **「提交」**，等待安装完成（大约 1-2 分钟）
6. 安装完成后，Nginx 旁边会显示 **「已安装」** 字样

#### 1.3 安装 Python 项目管理器

1. 在软件商店搜索框中输入 **「Python」**
2. 找到 **「Python 项目管理器」**（图标是 Python 的 logo）
3. 点击安装，同样选择 **「极速安装」**
4. 等待安装完成

#### 1.4 安装 Node.js 版本管理器（必装，前端编译需要）

1. 在软件商店搜索 **「Node」**
2. 找到 **「Node.js 版本管理器」**
3. 点击安装
4. 安装完成后，点击进入 Node.js 版本管理器，在版本列表中选择 **v18.20.x** 或 **v20.x**，点击安装
5. 安装完成后，点击 **「命令行版本」** 旁边的 **「设为默认」** 按钮

---

### 二、上传项目文件到服务器

#### 2.1 使用宝塔文件管理器

1. 点击宝塔左侧菜单的 **「文件」**（图标是一个文件夹）
2. 你会看到服务器上的目录列表。双击进入 **「www」** 目录，再双击进入 **「wwwroot」** 目录
   - 完整路径是 `/www/wwwroot/`，这是宝塔网站默认存放目录
3. 在 `/www/wwwroot/` 目录下，点击顶部的 **「新建目录」** 按钮
4. 目录名输入 **`location-tool`**，点击确定
5. 双击进入 `location-tool` 目录

#### 2.2 上传项目文件（方式一：本地上传）

1. 在你的 Windows 电脑上，把项目文件夹打包成 `.zip` 文件
   - 只打包项目核心文件，**不要打包** `node_modules/`、`.git/`、`__pycache__/`、`.uv-cache/`、`frontend/dist/` 这些目录（它们要么体积巨大，要么需要在服务器上重新生成）
   - 项目当前**没有** `dist/` 目录，这是正常的——我们将在服务器上编译生成
2. 在宝塔文件管理器（当前位置 `/www/wwwroot/location-tool/`）点击顶部的 **「上传」** 按钮
3. 点击 **「选择文件」**，选择你打包好的 zip 文件
4. 点击 **「开始上传」**，等待上传完成
5. 上传完成后，选中这个 zip 文件，点击顶部的 **「解压」** 按钮
6. 解压到当前目录，点击确定
7. 解压后的目录结构应该是这样的（**注意：此时还没有 `dist/` 目录，后面会编译生成**）：

```
/www/wwwroot/location-tool/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── config.py
│   ├── database.py
│   ├── ai_providers/
│   ├── models/
│   ├── prompts/
│   ├── routers/
│   ├── services/
│   └── storage/
├── frontend/
│   ├── package.json        ← 前端依赖清单
│   ├── vite.config.js      ← Vite 构建配置
│   ├── tailwind.config.js
│   ├── index.html          ← Vite 入口 HTML
│   ├── src/                ← React 源代码
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── pages/
│   │   ├── components/
│   │   └── ...
│   └── public/             ← 静态资源
└── README.md
```

#### 2.3 上传项目文件（方式二：Git 克隆）

如果你已经把代码推送到了 GitHub/Gitee，可以在服务器上用 Git 拉取。在宝塔面板左侧菜单找到 **「终端」**，执行：

```bash
cd /www/wwwroot
git clone <你的仓库地址> location-tool
```

---

### 三、配置后端环境变量（.env 文件）

#### 3.1 创建 .env 文件

1. 在宝塔 **「文件」** 页面，导航到 `/www/wwwroot/location-tool/backend/`
2. 点击顶部的 **「新建文件」** 按钮
3. 文件名输入 **`.env`**（注意有一个点，没有扩展名）
4. 点击 **「确定」**

#### 3.2 生成必要的密钥

在写入 .env 之前，先生成一个安全的 JWT 密钥。打开宝塔左侧菜单的 **「终端」**，执行：

```bash
openssl rand -hex 32
```

终端会输出一串类似 `a1b2c3d4e5f6789012345678abcdef01ab12cd34ef56ab78cd90ef12ab34cd` 的字符串，复制这串字符备用。

#### 3.3 填写 .env 文件内容

在宝塔文件管理器中，找到刚创建的 `.env` 文件，点击它或右键选择 **「编辑」**（宝塔内置了文本编辑器）。

将以下内容**完整粘贴**进去：

```ini
# ===== LLM 大模型配置 =====
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=sk-你的DeepSeek_API_Key

# ===== 备用供应商 API Key（可只填你用的那个）=====
DEEPSEEK_API_KEY=sk-你的DeepSeek_API_Key
GEMINI_API_KEY=
KIMI_API_KEY=
MINIMAX_API_KEY=
ZHIPU_API_KEY=

# ===== 高德地图 API（后端采集 POI 数据用）=====
AMAP_WEB_KEY=你的高德Web服务Key
AMAP_SECURITY_CODE=你的高德Web服务安全密钥

# ===== JWT 认证配置 =====
JWT_SECRET=这里粘贴刚才openssl生成的随机字符串
JWT_EXPIRY_HOURS=168

# ===== 新用户注册赠送额度 =====
SIGNUP_BONUS_CREDITS=3
SIGNUP_FREE_CREDITS=1

# ===== 管理员后台密码 =====
ADMIN_PASSWORD=你自己设置一个强密码至少8位

# ===== 跨域配置（填你的域名，多个用英文逗号分隔）=====
CORS_ORIGINS=https://你的域名.com

# ===== 微信公众号登录（可选，不填不影响使用）=====
WECHAT_MP_APPID=
WECHAT_MP_SECRET=
```

#### 3.4 逐行替换说明

请按照下表，把上面模板中的占位符替换为你自己的真实值：

| 占位符 | 替换为 | 注意 |
|--------|--------|------|
| `sk-你的DeepSeek_API_Key` | 你的 DeepSeek API Key | 去 platform.deepseek.com 的 API Keys 页面复制 |
| `你的高德Web服务Key` | 高德开放平台的 Web服务 Key | **不是** JS API Key |
| `你的高德Web服务安全密钥` | 对应上面 Key 的安全密钥 | 在高德控制台同一页面的右侧 |
| `openssl生成的随机字符串` | 刚才终端输出的那串字符 | 不要用默认值，后端会拒绝启动 |
| `你自己设置一个强密码` | 你自定义的管理员密码 | 至少8位，登录 /admin 后台用 |
| `你的域名.com` | 你解析到服务器的域名 | 如果有多个域名，用英文逗号分隔 |

> **关键提醒**：后端 `AMAP_WEB_KEY` 是**高德「Web服务」类型**的 Key；前端 `.env.local` 中的 `VITE_AMAP_KEY` 是**高德「JS API」类型**的 Key。它们必须是**两个不同的应用**，各自有独立的 Key 和安全密钥，不能混用。详见第十章问题 7。

#### 3.5 保存并设置权限

1. 编辑完成后，点击编辑器右上角的 **「保存」** 按钮
2. 关闭编辑器
3. 在文件管理器中，右键点击 `.env` 文件，选择 **「权限」**
4. 将权限设置为 **600**（即只有文件所有者可读写），点击确定
   - 如果权限界面是数字输入框，填 `600`
   - 如果权限界面是勾选框，勾选 **所有者：读+写**，其余全部取消勾选

---

### 四、部署后端（Python 项目管理器）

这是最关键的步骤。我们在宝塔的 Python 项目管理器中创建一个项目来运行 FastAPI 后端。

#### 4.1 打开 Python 项目管理器

点击宝塔左侧菜单的 **「软件商店」**，找到已安装的 **「Python 项目管理器」**，点击 **「打开」** 或 **「设置」**。

#### 4.2 进入项目管理页面

Python 项目管理器打开后，你会看到顶部有几个标签页。点击 **「Python 项目」** 标签。

#### 4.3 添加 Python 项目

点击页面中央或右上角的 **「添加项目」** 按钮，会弹出一个表单。按以下内容填写（没提到的字段留空）：

**基本信息：**

| 表单字段 | 你填写的内容 | 说明 |
|----------|-------------|------|
| **项目名称** | `zhidexuan-backend` | 自定义，建议用英文 |
| **项目路径** | `/www/wwwroot/location-tool/backend` | 点击右侧 **「选择」** 按钮，在文件树中依次双击 www → wwwroot → location-tool → backend，然后点确定 |
| **运行文件** | `main.py` | 入口文件名 |
| **运行方式** | 下拉选择 **`uvicorn`** | FastAPI 的标准运行方式 |
| **框架** | 下拉选择 **`FastAPI`** | |

**启动命令与端口：**

| 表单字段 | 你填写的内容 |
|----------|-------------|
| **启动命令** | `uvicorn main:app --host 0.0.0.0 --port 8000` |
| **端口** | `8000` |

> `main:app` 的意思是运行 `main.py` 文件中的 `app` 对象（FastAPI 实例）。`--host 0.0.0.0` 表示监听所有网络接口。

**Python 版本和依赖：**

| 表单字段 | 你填写的内容 |
|----------|-------------|
| **Python 版本** | 下拉选择 `3.12`（如果列表中没有 3.12，先点击「版本管理」标签页安装一个） |
| **是否安装依赖** | 勾选 ✅ |
| **依赖文件** | `requirements.txt`（会自动识别项目路径下的这个文件） |
| **开机自启** | 勾选 ✅ |

#### 4.4 提交并等待安装

1. 检查所有字段填写无误后，点击 **「确定」** 按钮
2. 页面会开始创建虚拟环境并安装依赖包。这个过程大约需要 1-3 分钟
3. 你可以在 Python 项目管理器的 **「日志」** 标签页中看到实时安装进度
4. 安装完成后，项目状态显示为 **「运行中」**（绿色图标），表示后端已成功启动

#### 4.5 如果出现 "JWT_SECRET cannot be the default value" 错误

这说明你的 `.env` 文件中的 `JWT_SECRET` 还是占位符。请回到第三章，重新编辑 `.env` 文件，把 `JWT_SECRET` 替换成 `openssl rand -hex 32` 生成的随机字符串。然后回到 Python 项目管理器，点击 **「重启」** 按钮。

#### 4.6 验证后端是否正常运行

在宝塔左侧菜单打开 **「终端」**，执行：

```bash
curl http://localhost:8000/api/health
```

如果返回类似 `{"status":"ok","version":"3.7.0"}` 的 JSON 字符串，说明后端运行成功。

如果返回 `Connection refused` 或其他错误：
- 项目状态是否为「运行中」？
- 点击「日志」标签查看是否有错误信息
- 确认 `.env` 文件中的 `JWT_SECRET` 不是占位符

---

### 五、编译前端（必做步骤）

> **项目目前没有 `dist/` 目录，必须通过编译生成。** 这一步将 React 源代码打包成浏览器可运行的 HTML/JS/CSS 静态文件。

#### 5.1 确认 Node.js 已安装

1. 宝塔左侧菜单 **「软件商店」** → 找到 **「Node.js 版本管理器」** → 点击打开
2. 查看是否已经安装了 Node 版本（v18.x 或 v20.x）
3. 如果显示"未安装"，在版本列表中选择 **v18.20.x** 或 **v20.x**，点击 **「安装」**
4. 安装完成后，点击 **「命令行版本」** 旁边的 **「设为默认」**

验证 Node.js 是否可用。打开宝塔 **「终端」**，执行：

```bash
node -v
# 应该输出 v18.20.x 或 v20.x.x

npm -v
# 应该输出 npm 的版本号，如 10.x.x
```

#### 5.2 创建前端环境变量文件（.env.local）

**这个文件必须在编译之前创建**，因为 Vite 会在编译时把环境变量嵌入到 JS 代码中。

1. 宝塔左侧 **「文件」** → 导航到 `/www/wwwroot/location-tool/frontend/`
2. 点击顶部 **「新建文件」**
3. 文件名输入 **`.env.local`**（注意有一个点，不要有扩展名）
4. 点击确定，再点击文件打开编辑器
5. 粘贴以下内容：

```ini
VITE_AMAP_KEY=你的高德JS_API_Key
VITE_AMAP_SECURITY_CODE=你的高德JS_API安全密钥
```

6. 替换占位符为真实值，然后点击 **「保存」**

> **关键提醒**：这里是**高德 JS API Key**，和第三章后端 `.env` 中填的**高德 Web 服务 Key**是**两个不同的 Key**！前者选"JS API"类型创建，后者选"Web服务"类型创建。两者不能混用，否则地图不会显示。

#### 5.3 安装前端 npm 依赖

打开宝塔 **「终端」**，执行：

```bash
cd /www/wwwroot/location-tool/frontend
npm install
```

这个过程需要 30 秒到 2 分钟。

**如果 `npm install` 很慢或卡住**，换成国内镜像源：

```bash
npm config set registry https://registry.npmmirror.com
npm install
```

**常见报错及解决方法**：

| 报错信息 | 原因 | 解决方法 |
|----------|------|----------|
| `npm: command not found` | Node.js 未安装 | 回到 5.1 安装 Node.js |
| `Cannot find module ...` | node_modules 损坏 | `rm -rf node_modules && npm install` |
| `EACCES: permission denied` | 目录权限不足 | `chmod -R 755 /www/wwwroot/location-tool/frontend` |
| `code ENOTFOUND` | DNS 解析失败 | 换国内源 |
| `npm ERR! cb() never called` | npm 缓存损坏 | `npm cache clean --force && npm install` |
| `npm ERR! code ENOENT` | 当前目录不对 | `cd /www/wwwroot/location-tool/frontend` 后再执行 |

#### 5.4 执行编译（npm run build）

依赖安装完成后，在同一个终端中执行：

```bash
npm run build
```

编译过程大约需要 30 秒到 1 分钟。看到 **`✓ built in xx.xxs`** 就表示编译成功。

#### 5.5 验证编译产物

编译完成后，在宝塔 **「文件」** 页面导航到 `/www/wwwroot/location-tool/frontend/dist/`。应该看到：

```
frontend/dist/
├── index.html          ← Nginx 的入口页面
├── assets/             ← 打包后的 JS、CSS、图片
│   ├── index-xxxxx.js
│   ├── react-xxxxx.js
│   └── index-xxxxx.css
└── brand-logo-xxx.png
```

如果 `dist/` 为空或不存在，或编译报错：
1. 确认 `npm run build` 没有报错
2. 检查 `src/` 目录是否完整（`main.jsx`、`App.jsx` 是否存在）
3. 检查 `.env.local` 格式是否正确
4. 如报模块找不到：`rm -rf node_modules && npm install && npm run build` 三连重试

**编译报错：`ENOTDIR: not a directory, scandir '.../dist/.user.ini'`**

这是宝塔建站时在 `dist/` 目录自动生成的保护文件，带不可变属性导致 Vite 无法清空目录。执行：

```bash
chattr -i /www/wwwroot/location-tool/frontend/dist/.user.ini
rm -rf /www/wwwroot/location-tool/frontend/dist
cd /www/wwwroot/location-tool/frontend && npm run build
```

> 如果 `chattr` 命令无效，在宝塔「文件」页面找到 `dist/.user.ini`，右键删除后再编译。

---

### 六、创建 Nginx 网站站点

#### 6.1 进入网站管理

点击宝塔左侧菜单的 **「网站」**（图标是一个地球）。

#### 6.2 添加 HTML 站点

1. 点击 **「HTML项目」** 标签（宝塔 9.x）或 **「PHP项目」** → **「添加站点」**
2. 弹出创建站点的表单，按以下内容填写：

| 表单字段 | 你填写的内容 | 说明 |
|----------|-------------|------|
| **域名** | `你的域名.com` | 填写你已解析到服务器的域名 |
| **根目录** | `/www/wwwroot/location-tool/frontend/dist` | 点击选择按钮导航到 dist 目录 |
| **FTP** | **不勾选** | 不需要 FTP |
| **数据库** | **不勾选** | 项目用 SQLite |
| **PHP版本** | 选 **「纯静态」** | 前端只是静态 HTML |

3. 点击 **「提交」**

#### 6.3 配置 Nginx 反向代理

1. 在 **「网站」** 页面，找到你刚创建的站点
2. 点击站点右侧的 **「设置」** → **「配置文件」** 标签
3. **全选（Ctrl+A）→ 删除**，然后把下面的配置**完整粘贴**进去：

```nginx
server {
    listen 80;
    server_name 你的域名.com;

    access_log /www/wwwlogs/zhidexuan.access.log;
    error_log  /www/wwwlogs/zhidexuan.error.log;

    root /www/wwwroot/location-tool/frontend/dist;
    index index.html;

    #error_page 404/404.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;
    gzip_min_length 1000;

    # SPA 路由回退
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # 静态资源转发
    location /assets/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # 浏览器缓存策略
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

4. 把配置中的 **`你的域名.com`** 替换成你自己的真实域名
5. 点击 **「保存」**

#### 6.4 启用 HTTPS（SSL 证书）

1. 在站点设置弹窗中，点击 **「SSL」** 标签
2. 选择 **「Let's Encrypt」** 子标签
3. 勾选你的域名，填写邮箱地址，点击 **「申请」**

> **如果报错"未找到标识信息 #error_page 404/404.html"**：说明配置文件缺少宝塔 SSL 注入标记。在站点「配置文件」的 `server` 块中（`index index.html;` 后面）添加一行 `#error_page 404/404.html;`，保存后重新申请。

4. 申请成功后，打开 **「强制HTTPS」** 开关

> 如果服务器在国内且域名没有备案，Let's Encrypt 可能无法使用。需要先完成 ICP 备案。

#### 6.5 测试 Nginx 配置

打开宝塔 **「终端」**，执行：

```bash
nginx -t
# 应输出: nginx: configuration file ... test is successful

nginx -s reload
```

---

### 七、防火墙和安全组设置

#### 7.1 宝塔面板安全设置

1. 点击宝塔左侧菜单的 **「安全」**（图标是一个盾牌）
2. 在 **「系统防火墙」** 标签页中，检查以下端口状态：

| 端口 | 协议 | 状态 | 说明 |
|------|------|------|------|
| 80 | TCP | 放行 | HTTP 网页访问 |
| 443 | TCP | 放行 | HTTPS 加密访问 |
| 8000 | TCP | **删除** | 后端端口，绝对不能对外暴露 |
| 8888 | TCP | 建议修改 | 宝塔默认端口 |

3. 如果 8000 端口在列表中，点击右侧 **「删除」**。后端通过 Nginx 代理访问，不需要直接暴露。
4. 如果 80 和 443 不在列表中，手动添加。

#### 7.2 云服务商安全组

如果你用的是阿里云、腾讯云等，还需要在云服务商控制台的安全组中放行 80 和 443 端口。

---

### 八、验证整体部署

#### 8.1 在宝塔终端中验证

```bash
# 测试 1：后端进程是否在运行
ps aux | grep uvicorn

# 测试 2：后端端口是否在监听
netstat -tlnp | grep 8000

# 测试 3：本地请求后端是否正常
curl http://localhost:8000/api/health
# 应返回 {"status":"ok","version":"3.7.0"}

# 测试 4：Nginx 配置是否生效
curl -I http://localhost/
# 应返回 HTTP/1.1 200 OK

# 测试 5：通过 Nginx 代理访问 API
curl http://localhost/api/health
# 应返回 {"status":"ok","version":"3.7.0"}
```

#### 8.2 在浏览器中验证

1. 访问 `https://你的域名.com/` → 应看到选址分析主页（深色主题界面），地址栏有🔒图标
2. 访问 `https://你的域名.com/api/health` → 应返回 JSON `{"status":"ok","version":"3.7.0"}`
3. 访问 `https://你的域名.com/api/docs` → 应看到 Swagger API 文档页面
4. 在前端页面测试完整分析流程：输入地址 → 选择业态 → 点击分析 → 确认正常返回结果

#### 8.3 常见验证失败的情况

| 现象 | 原因 | 解决步骤 |
|------|------|----------|
| 域名显示"无法连接" | 域名 DNS 未解析或 Nginx 未启动 | 1. `curl -s ip.sb` 查公网 IP 2. `curl -I http://服务器IP/` 测试 3. IP 能通域名不通 → 去 DNS 管理添加 A 记录 |
| 域名能通但 `www` 不能通（或反过来） | DNS 只解析了一个 | 在 DNS 管理中添加 `@` 和 `www` 两条 A 记录，同时更新 Nginx `server_name` |
| 页面能打开但全是乱的 | 静态文件路径不对 | 检查根目录是否指向 `frontend/dist/` |
| 页面刷新后 404 | Nginx try_files 没配置 | 检查配置文件 `try_files` 那行 |
| API 返回 502 | 后端没运行 | Python 项目管理器确认状态为「运行中」 |
| API 返回 500 | 后端代码报错 | 查看 Python 项目管理器「日志」标签 |
| 地图不显示 | 高德 JS API Key 未设置或类型不对 | 确认 `.env.local` 为 JS API 类型，且构建前已配置 |
| 点击搜索/定位后输入框显示坐标（如`107.2340, 34.3427`） | 1. 安全密钥与 Key 不匹配 2. 用了 Web服务Key 而非 JS API Key 3. 未启用逆地理编码服务 | 在高德控制台确认：Key 类型为 JS API、安全密钥正确、已启用「地理编码」和「逆地理编码」服务，然后重新编译前端 |

---

### 九、日常运维操作

#### 9.1 如何重启后端

宝塔 **「软件商店」** → **「Python 项目管理器」** → 找到 `zhidexuan-backend` → 点击右侧 **「重启」**。

#### 9.2 如何重启 Nginx

宝塔 **「网站」** 页面 → 找到站点 → 点击 **「状态」** 切换按钮，或终端执行 `nginx -s reload`。

#### 9.3 如何查看日志

- **后端日志**：Python 项目管理器 → 项目右侧 **「日志」** 按钮
- **Nginx 日志**：宝塔「文件」→ `/www/wwwlogs/zhidexuan.access.log` 和 `zhidexuan.error.log`

#### 9.4 如何备份数据库

项目使用 SQLite，数据库文件位于 `/www/wwwroot/location-tool/backend/location_tool.db`。

**方法一：宝塔计划任务自动备份（推荐）**

1. 宝塔左侧 **「计划任务」** → **「添加任务」**
2. 任务类型选 **Shell 脚本**，执行周期 **每天 03:00**
3. 脚本内容：

```bash
#!/bin/bash
BACKUP_DIR=/www/backup/zhidexuan
mkdir -p $BACKUP_DIR
cp /www/wwwroot/location-tool/backend/location_tool.db $BACKUP_DIR/location_tool_$(date +%Y%m%d).db
find $BACKUP_DIR -mtime +7 -delete
echo "Backup completed at $(date)"
```

**方法二：手动备份** — 宝塔「文件」页面找到 `location_tool.db`，右键 → **「下载」** 到本地。

#### 9.5 如何更新项目代码

**如果项目通过 `git clone` 部署：**

```bash
# 第一步：拉取最新代码
cd /www/wwwroot/location-tool
git pull

# 第二步：更新后端依赖（如有变动）
cd backend
pip install -r requirements.txt

# 第三步：重新构建前端（如有变动）
cd ../frontend
npm install
npm run build

# 第四步：重启后端
kill -HUP $(cat /www/wwwroot/location-tool/backend/gunicorn.pid)
```

**如果项目通过 zip 上传部署（目录中无 `.git`）：**

1. 宝塔「文件」→ 导航到 `/www/wwwroot/location-tool/`
2. 点击「上传」→ 选择更新后的文件 → 覆盖上传
3. 或使用宝塔「终端」用 `curl` 下载单个文件（需服务器能访问 GitHub）
4. 更新后执行上述第三、四步

> 推荐首次部署后执行一次 `git init && git remote add origin ...`（见问题 18），后续即可用 `git pull` 更新。

#### 9.6 首次部署：初始化业态数据

> 新部署的服务器数据库为空，业态下拉框无选项，**必须执行本步骤**。

```bash
# 1. 找到正在使用的 Python 路径
PYTHON=$(readlink -f /proc/$(pgrep -f "gunicorn|uvicorn" | head -1)/exe)
echo $PYTHON

# 2. 创建 34 条细分业态记录
$PYTHON /www/wwwroot/location-tool/backend/fix_industry_names.py

# 3. 注入 34 条 AI 专属规则
$PYTHON /www/wwwroot/location-tool/backend/import_all_prompts.py
```

预期：`[DONE] 成功注入 34/34 个业态的 AI 专属规则！`

---

### 十、常见问题排查

#### 问题 1：Python 项目管理器中没有 3.12 版本

在 Python 项目管理器中点击 **「版本管理」** → **「安装新版本」** → 选择 `3.12.x` → 安装。

#### 问题 2：安装依赖时报错 "Could not find a version that satisfies the requirement"

使用国内镜像源手动安装：

```bash
cd /www/wwwroot/location-tool/backend
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

#### 问题 3：前端页面能打开但地图是空白的

1. 确认 `.env.local` 中填的是 **JS API 类型**的 Key（不是 Web 服务类型）
2. 确认 `.env.local` 在 `npm run build` **之前**就已填写好
3. 如果 Key 是构建后才填的，需要重新 `npm run build`

#### 问题 4：分析一直转圈不返回结果

1. Python 项目管理器 → 查看「日志」
2. 检查 DeepSeek API Key 是否有效、余额是否充足
3. 在终端测试 API 连通性：

```bash
curl -X POST https://api.deepseek.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-你的APIKey" \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"test"}]}'
```

#### 问题 5：服务器重启后网站打不开

Python 项目管理器 → 项目设置 → 勾选 **「开机自启」**。

#### 问题 6：.env 文件改了不生效

修改 `.env` 后必须重启后端。在 Python 项目管理器中点击 **「重启」**。

#### 问题 7：高德地图 Key 配置混淆

项目需要**两个不同的高德应用**，Key 不能混用：

| 用途 | 应用类型 | 配置文件 |
|------|----------|----------|
| 后端 POI 数据采集 | **Web服务** | `backend/.env` 中的 `AMAP_WEB_KEY` |
| 前端地图显示 + 搜索 | **JS API** | `frontend/.env.local` 中的 `VITE_AMAP_KEY` |

两个应用各自有独立的 Key 和安全密钥。用同一个 Key 会导致地图不显示或坐标无法解析。
另外，高德控制台 → 应用管理 → 点击应用，确认已启用 **「地理编码」** 和 **「逆地理编码」** 服务。

#### 问题 8：关闭 8000 端口后管理后台不能用？

关闭 8000 公网端口不影响使用。所有请求通过 Nginx 代理走：

```
浏览器 → 443(Nginx) → 127.0.0.1:8000(后端)
```

Nginx 和 uvicorn 在同台机器上通过 localhost 通信，不经过外部防火墙。关闭 8000 端口只是阻止外部直连，正常用户不受影响。

#### 问题 9：管理后台入口在哪？

浏览器访问 `https://你的域名.com/admin`，登录密码是 `.env` 中设置的 `ADMIN_PASSWORD`。

#### 问题 10：编译报错 `ENOTDIR: not a directory, scandir '.../dist/.user.ini'`

宝塔建站时在 `dist/` 目录自动生成的保护文件导致 Vite 无法清空目录。解决：

```bash
chattr -i /www/wwwroot/location-tool/frontend/dist/.user.ini
rm -rf /www/wwwroot/location-tool/frontend/dist
cd /www/wwwroot/location-tool/frontend && npm run build
```

#### 问题 11：SSL 证书申请报错"未找到标识信息"

Nginx 配置文件缺少宝塔 SSL 注入标记。在「配置文件」的 `server` 块中添加一行 `#error_page 404/404.html;`（`index index.html;` 后面），保存后重新申请证书。

#### 问题 12：`curl http://域名` 返回 `Could not resolve host`

域名 DNS 解析未配置或未生效：
1. 执行 `curl -s ip.sb` 获取服务器公网 IP
2. 用 `curl -I http://服务器IP/` 测试 → IP 通说明服务正常
3. 登录域名 DNS 管理平台，添加 A 记录：`@` → 服务器IP、`www` → 服务器IP
4. 保存后等 1-10 分钟生效

#### 问题 13：分析报错"分析服务异常"或日志显示 401 Authorization Required

**原因**：`.env` 中 `LLM_API_KEY` 未从占位符改成真实 Key。

**检查方法**：

```bash
cat /www/wwwroot/location-tool/backend/.env | grep LLM_API_KEY
```

如果显示 `LLM_API_KEY=sk-your-key-here`（占位符），说明真实 Key 只填在了 `DEEPSEEK_API_KEY` 里但未被使用。代码优先读取 `LLM_API_KEY`。

**修复**：

```bash
sed -i 's/LLM_API_KEY=sk-your-key-here/LLM_API_KEY=你的真实Key/' /www/wwwroot/location-tool/backend/.env
```

然后重启后端：`kill -HUP $(cat /www/wwwroot/location-tool/backend/gunicorn.pid)`

> **提醒**：所有 `.env` 中标注 `★` 或 `必填` 的变量**每一行都要检查**，特别是那些值为 `sk-your-key-here` 或 `change-this` 的占位符。

#### 问题 14：分析报错"高德API错误: CUQPS_HAS_EXCEEDED_THE_LIMIT"

高德 Web 服务 API 日调用量超限。免费版每个 Key 每日 5000 次 POI 搜索配额。

**解决**：
1. 等次日 00:00 自动重置，或
2. 登录 [高德开放平台](https://console.amap.com) 购买更高配额套餐

#### 问题 15：服务器部署后业态下拉框为空 / 没有选择项

数据库表是新建的，业态数据未初始化。需要在服务器上运行同步脚本：

**第一步：查找正在使用的 Python 路径**

```bash
readlink -f /proc/$(pgrep -f uvicorn | head -1)/exe 2>/dev/null || readlink -f /proc/$(pgrep -f gunicorn | head -1)/exe
```

**第二步：创建 34 条细分业态**

```bash
PYTHON_PATH:/www/server/pyporject_evn/versions/3.12.13/bin/python3.12
$PYTHON_PATH /www/wwwroot/location-tool/backend/fix_industry_names.py
```

**第三步：注入 34 条 AI 专属规则**

```bash
$PYTHON_PATH /www/wwwroot/location-tool/backend/import_all_prompts.py
```

预期输出：`[DONE] 成功注入 34/34 个业态的 AI 专属规则！`

#### 问题 16：查看后端错误日志

后端通过 Gunicorn 启动的，错误日志位置：

```bash
tail -100 /www/wwwlogs/python/backend/gunicorn_error.log
```

如果目录不存在，查看 Gunicorn 配置：

```bash
cat /www/wwwroot/location-tool/backend/gunicorn_conf.py | grep errorlog
```

#### 问题 17：宝塔网页终端粘贴命令后出现混乱文本

宝塔的网页终端在粘贴多行时会混入历史输出，导致命令无法正常执行。

**解决方法**：使用 SSH 客户端连接服务器（推荐 Windows 自带 PowerShell）：

```bash
ssh root@你的服务器IP
```

进入后终端干净，不会出现粘贴混乱。

#### 问题 18：项目通过 zip 上传无法 `git pull` 更新

如果项目不是 `git clone` 而是压缩包上传的，目录中没有 `.git` 无法拉取更新。

**方法 A（推荐）**：将已有目录转为 Git 仓库

```bash
cd /www/wwwroot/location-tool
git init
git remote add origin https://github.com/dacui5201314/location-tool.git
git fetch origin main
git reset --hard origin/main
```

> 首次执行会覆盖本地文件。如果 `.env` 有修改会被覆盖，操作前先备份：`cp backend/.env ~/env.backup`，操作后恢复。

**方法 B**：通过宝塔「文件」页面，手动上传更新的文件覆盖旧文件。

---

### 十一、项目安全防护教程（强烈建议执行）

> 服务器暴露在公网上，每天都会有自动化扫描攻击。以下安全配置能挡住 90% 以上的常见攻击。**建议全部执行，至少做完前三节。**

#### 11.1 宝塔面板安全加固

宝塔面板是服务器的管理入口，这是**优先级最高**的防护。

**11.1.1 修改面板默认端口**

1. 宝塔左侧 **「面板设置」** → 找到 **「面板端口」**
2. 把 `8888` 改成 `10000~65535` 之间的不常用端口，如 `25876`
3. 点击保存，面板会自动跳转到新地址
4. 去 **「安全」** 页面添加新端口放行，删除 `8888` 端口规则

> 忘记端口号时，SSH 执行 `bt 14` 可查看面板地址。

**11.1.2 修改面板默认用户名和密码**

1. 宝塔左侧 **「面板设置」** → 找到 **「面板用户」** 和 **「面板密码」**
2. 把默认 `admin` 改成自定义用户名
3. 密码改成至少 12 位，包含大小写字母 + 数字 + 特殊符号

**11.1.3 开启面板 SSL**

1. 宝塔 **「面板设置」** → 找到 **「面板SSL」** 开关
2. 如果没有 SSL 证书，勾选 **「使用自签名证书」**
3. 保存后面板访问变为 `https://`

**11.1.4 开启 BasicAuth 双因素认证**

1. 宝塔 **「面板设置」** → 找到 **「BasicAuth 认证」** → 开启
2. 设置与面板用户名/密码不同的额外用户名和密码
3. 保存后浏览器会弹出认证窗口，输入正确才能进入面板登录页

**11.1.5 设置面板安全入口**

1. 宝塔 **「面板设置」** → 找到 **「安全入口」**
2. 系统已自动生成随机路径如 `/08a45b6c`，复制保存好
3. 不要用 `/admin`、`/panel` 等容易被猜到的路径

> 配置后面板 URL 为：`https://你的IP:端口/安全入口`。不知道路径的人访问返回 404。

**11.1.6 限制面板登录 IP（固定 IP 才开启）**

如果你的电脑使用固定 IP，宝塔 **「面板设置」** → **「授权IP」** → 输入你的公网 IP。动态 IP 用户不要开启，否则可能把自己锁在外面。

#### 11.2 系统防火墙配置

**11.2.1 最小端口原则**

宝塔 **「安全」** 页面，只放开必需端口：

| 端口 | 用途 |
|------|------|
| 你的面板新端口 | 宝塔面板 |
| 80 | HTTP |
| 443 | HTTPS |
| 你的 SSH 新端口 | SSH 远程连接 |

必须删除：`8888`、`8000`、`3306`、`6379`、`20/21`、`22`（已改端口的话）。

**11.2.2 云服务商安全组**

登录云服务商控制台，确保安全组规则与宝塔防火墙一致。

#### 11.3 SSH 安全加固

**11.3.1 修改 SSH 默认端口**

```bash
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak
```

编辑 `/etc/ssh/sshd_config`，找到 `#Port 22` 改为 `Port 22022`（选 10000~65535 之间）。保存后在宝塔「安全」页面放行新端口，重启 `systemctl restart sshd`，测试成功后删除 22 端口规则。

> **务必在宝塔终端中操作而非 SSH 客户端**，避免配置出错后失去连接。

**11.3.2 改用密钥登录，禁用密码**

在 Windows 本地生成密钥对：

```bash
ssh-keygen -t ed25519 -C "你的邮箱@example.com"
```

上传公钥到服务器：

```bash
ssh-copy-id -p 22022 root@你的服务器IP
```

测试密钥登录成功后，编辑 `/etc/ssh/sshd_config`：

```
PermitRootLogin prohibit-password
PasswordAuthentication no
PermitEmptyPasswords no
MaxAuthTries 3
```

重启 SSH：`systemctl restart sshd`。

> 从此只能用密钥登录。务必保管好私钥文件 `C:\Users\admin\.ssh\id_ed25519`，丢失后将无法登录。

**11.3.3 安装 fail2ban 防暴力破解**

```bash
# CentOS
yum install -y fail2ban

# Ubuntu/Debian
apt update && apt install -y fail2ban

systemctl enable fail2ban
systemctl start fail2ban
```

创建 `/etc/fail2ban/jail.local`：

```ini
[sshd]
enabled = true
port = 22022
filter = sshd
logpath = /var/log/secure
maxretry = 3
bantime = 86400
findtime = 600
```

重启：`systemctl restart fail2ban`。验证：`fail2ban-client status sshd`。

#### 11.4 项目文件安全防护

##### 11.4.1 保护 .env 敏感文件

```bash
# 设置严格权限
chmod 600 /www/wwwroot/location-tool/backend/.env

# 确认
ls -la /www/wwwroot/location-tool/backend/.env
# 应显示 -rw-------
```

##### 11.4.2 Nginx 安全配置升级（完整替换版）

> **操作时机**：确认第六章基本配置已生效、网站能正常访问后，再做以下升级。

以下操作分两步。**务必按顺序执行，否则 Nginx 会报错。**

**第一步：在主配置中添加限速区（http 块）**

`limit_req_zone` 指令**只能**放在 Nginx 的 `http` 块中，不能放在 `server` 块里。在宝塔中操作：

1. 宝塔左侧 **「软件商店」** → 找到 **「Nginx」** → 点击 **「设置」** → 点击 **「配置修改」**
2. 你会看到 Nginx 的主配置文件（包含 `http { ... }` 块）
3. 在 `http {` 这一行的**下面**，找一处空行，添加以下两行：

```nginx
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=page_limit:10m rate=30r/s;
```

4. 点击 **「保存」**

> 这两行定义了限速规则：API 每秒最多 10 个请求，普通页面每秒 30 个请求。注意缩进跟在 `http {` 内部。

**第二步：用增强版配置替换站点配置**

回到宝塔 **「网站」** → 你的站点 → **「设置」** → **「配置文件」**。把当前内容**全选 → 删除**，粘贴下面的增强版配置：

```nginx
server {
    listen 80;
    server_name 你的域名.com;

    # 隐藏 Nginx 版本号
    server_tokens off;

    access_log /www/wwwlogs/zhidexuan.access.log;
    error_log  /www/wwwlogs/zhidexuan.error.log;

    root /www/wwwroot/location-tool/frontend/dist;
    index index.html;

    #error_page 404/404.html;

    # 限制请求体大小
    client_max_body_size 10m;
    client_body_timeout 30s;
    client_header_timeout 30s;

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;
    gzip_min_length 1000;

    # 安全响应头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # ===== 禁止访问敏感文件 =====
    location ~ /\. {
        deny all;
        return 404;
    }

    location ~* \.(db|sqlite|sqlite3|py)$ {
        deny all;
        return 404;
    }

    # ===== 保护 API 文档（替换为你的公网 IP）=====
    location ~ ^/api/(docs|redoc|openapi\.json) {
        allow 127.0.0.1;
        deny all;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # ===== SPA 路由回退 + 页面限速 =====
    location / {
        limit_req zone=page_limit burst=50 nodelay;
        try_files $uri $uri/ /index.html;
    }

    # ===== API 反向代理 + 接口限速 =====
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    # ===== 静态资源转发 =====
    location /assets/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    # ===== 浏览器缓存策略（放在最后，优先匹配上面的规则）=====
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

3. 把 **`你的域名.com`** 替换为你的真实域名
4. 点击 **「保存」**
5. 打开宝塔 **「终端」**，执行：

```bash
nginx -t
# 确认输出 test is successful
nginx -s reload
```

> **验证**：在浏览器访问 `https://你的域名.com/.env` → 应返回 404。访问 `https://你的域名.com/api/health` → 应正常返回 JSON。

#### 11.5 定期安全维护

在宝塔 **「计划任务」** 中添加周期任务：

**任务一：每周系统安全更新（周日 04:00）**

```bash
#!/bin/bash
# CentOS
yum update -y --security 2>&1 | tail -5
# Ubuntu/Debian: apt update && apt upgrade -y 2>&1 | tail -5
```

**任务二：每天 fail2ban 状态检查（每天 06:00）**

```bash
#!/bin/bash
echo "=== fail2ban 状态 ==="
fail2ban-client status sshd 2>&1
echo "=== 被封禁的 IP ==="
fail2ban-client get sshd banned 2>&1
```

**每月安全检查清单：**

- [ ] 宝塔面板是否有更新版本？
- [ ] `.env` 文件权限是否仍为 600？
- [ ] API Key 是否需要轮换？
- [ ] 数据库备份是否正常执行？
- [ ] fail2ban 是否运行正常？
- [ ] 磁盘空间是否充足？（`df -h`）
- [ ] 是否有异常登录？（`last | head -20`）
- [ ] Nginx 错误日志是否有异常？

#### 11.6 安全防护总结

| 优先级 | 防护项 | 防什么 | 操作耗时 |
|--------|--------|--------|----------|
| 最高 | 修改面板端口 | 自动化扫描 | 2 分钟 |
| 最高 | 修改面板密码 | 暴力破解 | 1 分钟 |
| 最高 | 开启安全入口 | 未授权访问 | 1 分钟 |
| 最高 | .env 文件权限 600 | 信息泄露 | 1 分钟 |
| 高 | SSH 改端口 | SSH 暴力破解 | 5 分钟 |
| 高 | Nginx 禁止访问隐藏文件 | 源码泄露 | 5 分钟 |
| 高 | 关闭 8000 端口对外 | API 直接攻击 | 2 分钟 |
| 中 | SSH 密钥登录 | 密码爆破 | 15 分钟 |
| 中 | BasicAuth 双因素 | 面板未授权 | 3 分钟 |
| 中 | fail2ban | 持续暴力破解 | 10 分钟 |
| 中 | Nginx 速率限制 | CC/DDoS | 5 分钟 |
| 中 | 限制 /docs 访问 | API 信息泄露 | 3 分钟 |
| 例行 | 每周安全更新 | 已知漏洞 | 自动 |
| 例行 | 每日 fail2ban 检查 | 攻击态势感知 | 自动 |

---

## 附录：服务关系速查

```
用户浏览器访问 https://你的域名.com
        │
        ▼
   Nginx（端口 80/443）
        │
        ├── 请求路径是 / 或 /records/xxx 等
        │   → 直接返回 frontend/dist/ 下的静态文件
        │
        ├── 请求路径是 /api/xxx
        │   → 代理转发到 http://127.0.0.1:8000/api/xxx
        │   → FastAPI (uvicorn) 处理
        │
        └── 请求路径是 /assets/xxx
            → 代理转发到 http://127.0.0.1:8000/assets/xxx
            → FastAPI 从 storage/assets/ 读取文件
```

> 部署完成后，建议把 `.env` 文件中的密钥妥善保存。如有问题，优先查看日志定位原因。
