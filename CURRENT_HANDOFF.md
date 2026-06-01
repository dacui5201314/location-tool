# Current Handoff - 2026-06-01

## Read This First

- Project: `C:\Users\admin\location-tool`
- Launch target: `uniapp` WeChat Mini Program
- Web `frontend/`: **已删除** — uni-app 唯一客户端
- GitHub: `https://github.com/dacui5201314/location-tool` (干净仓库)
- Admin Dashboard: `http://localhost:8000/admin` (独立 HTML，10 模块)
- Latest commit: see git log

## 项目结构

```
location-tool/
├── backend/
│   ├── admin/index.html      ← 管理后台（独立 HTML，/admin 路由，10 模块）
│   ├── main.py               ← FastAPI 入口 v3.7.0
│   ├── routers/              ← 10 个路由模块（含 orders/billing-records）
│   ├── services/             ← amap/billing/runtime_config/storage/poi_name_guard
│   ├── prompts/              ← location_analysis + industry_config（14 Master 模板）
│   ├── tests/                ← 2343 PASS（2168 + 175）
│   └── storage/              ← 运行时文件
├── uniapp/                   ← 主力客户端（Vue3 + Vite → 微信小程序）
└── miniprogram/              ← 原生小程序 scaffold（登录参考，不开发）
```

## 当前工作状态

- 后端测试基线：compileall PASS / industry 2168 PASS / fact guard 175 PASS
- 管理后台 `/admin` — 10 个导航模块（仪表盘/用户/订单/流水/设置/日志/CDK/全局参数/操作记录/业态规则）
- 微信支付 JSAPI v3 后端就绪，前端 queryOrder 确认闭环已接入
- 小程序充值页已接入真实支付 + queryOrder 轮询
- 退款幂等保护（per-request UUID）+ 匿名设备 ID 随机持久化
- location suggest/regeocode 完整 Key 池 failover
- C-4 POI 名称幻觉：retry 白名单收窄 + 禁用名注入 + 模板去诱导

## 2026-06-01 完成清单

### 第一轮：上线闭环 P0/P1（commit 3444360）
- 支付闭环：requestPayment → queryOrder 轮询 → PAID 确认
- .gitignore：数据库/storage/__pycache__/*.pyc
- 管理后台：search→phone 参数修复 + esc/escUrl XSS 全局转义
- 匿名设备 ID 去硬编码 + 退款幂等 + Key 池完整 failover + 文档统一

### 第二轮：C-4 报告幻觉（commit e7153c3）
- poi_name_guard.py：build_retry_name_constraints 白名单/禁用名导出
- retry_prompt：注入 allowed_names + forbidden_names + 强约束
- location_analysis.py：5 处模板去诱导（禁止编造学校/小区/商场名）
- 测试：175 PASS（+8 C-4 专项 + 收窄白名单 + 仅空名 allowlist_empty）

### 第三轮：管理后台 SaaS 闭环（commit b92e66f）
- /api/admin/orders：PaymentOrder JOIN User 查询，分页/筛选
- /api/admin/billing-records：BillingRecord JOIN User 查询，分页/筛选
- 后台新增 💳 订单管理 + 🧾 点数流水页面
- 用户列表：📋 查看订单 / 🧾 查看流水 快捷跳转
- 业态管理：完整 CRUD（新增/编辑/启停/删除）
- SKU 保存：body { items: [...] } 对齐后端
- CDK：prefix/days_valid 字段对齐 + codes 路径修复
- 客服二维码：上传后 PUT /qrcode-slot/cs 持久化
- Key 池：r.data.keys + masked_key/has_security_secret 字段对齐
- 筛选状态：openOrders/openBilling 重置逻辑 + sv 回填一致性
- 用户列表分页 + Key 池启用停用快捷切换

## 测试基线

```
python -m compileall backend              → PASS
python tests/check_industry_rigor_rules.py → 2168 PASS, 0 FAIL
python tests/check_report_fact_guard.py    → 175 PASS, 0 FAIL
uniapp build:mp-weixin                     → DONE
```

### 第四轮：Codex UI 精细收口（2026-06-01）

**管理后台：**
- 仪表盘趋势图：从简单柱状图升级为 DPI-aware 交互折线图（hover 提示每日数量）
- 品牌 logo 移至 `/assets/admin-logo.png`，带 fallback 文字
- 移除已废弃的"系统日志"导航项
- 分享配置：首页分享图 + 报告分享图独立设置（`home_share_image_url` / `report_share_image_url`）
- 用户列表：会员显示友好化（普通用户/月度/季度/年度）、头像昵称强化
- 操作记录：增加类型标签、变更内容详情、管理员信息
- 业态规则：按大类别（餐饮/茶饮咖啡/零售/生活服务等）分组展示，从 `/api/industries/active` 读取前台分类
- CDK 批量删除：增加 POST `/api/admin/cdk/batch-delete` 兼容路由

**前端 uni-app：**
- ProfilePanel：金币堆和皇冠改用 PNG 图片（`coin-stack-v2.png` / `vip-crown.png`）
- 首页分享：支持 `home_share_image_url` 独立封面，`resolveShareImage()` 处理 `/assets/` 路径
- 报告分享：支持 `report_share_image_url` 独立封面

## 待上线事项

- 微信支付真机联调（需公网 HTTPS + 商户配置）
- C-4 真实 LLM 回归验证（代码防线已就绪，待实际跑一次分析确认不再编造假 POI）
- 小程序审核提交
