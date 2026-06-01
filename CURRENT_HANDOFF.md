# Current Handoff - 2026-06-01

## Read This First

- Project: `C:\Users\admin\location-tool`
- Launch target: `uniapp` WeChat Mini Program
- Web `frontend/`: **已删除** — uni-app 唯一客户端
- GitHub: `https://github.com/dacui5201314/location-tool` (干净仓库)
- Admin Dashboard: `http://localhost:8000/admin` (独立 HTML，替代旧 React 后台)
- Latest commit: pending — P0/P1 上线闭环修复 (2026-06-01)

## 项目结构

```
location-tool/
├── backend/
│   ├── admin/index.html      ← 管理后台（独立 HTML，/admin 路由）
│   ├── main.py               ← FastAPI 入口
│   ├── routers/              ← 9 个路由模块
│   ├── services/             ← amap/billing/runtime_config/storage/poi_name_guard
│   ├── prompts/              ← location_analysis + industry_config（14 Master 模板）
│   ├── tests/                ← 2168 PASS / 147 PASS
│   └── storage/              ← 运行时文件
├── uniapp/                   ← 主力客户端（Vue3 + Vite → 微信小程序）
└── miniprogram/              ← 原生小程序 scaffold（登录参考，不开发）
```

## 当前工作状态

- 后端测试基线：compileall PASS / industry 2168 PASS / fact guard 147 PASS
- 管理后台 `/admin` — 8 个导航模块，独立 HTML（非 Swagger UI）
- 微信支付后端（JSAPI v3）代码就绪，前端 queryOrder 确认闭环已接入
- 小程序充值页已接入真实支付 + queryOrder 轮询
- 匿名设备 ID 已去硬编码，使用随机持久 ID
- 退款幂等保护已添加（AUTO_REFUND:<key> 前缀写入 BillingRecord）
- location suggest/regeocode 已接入完整 Key 池重试
- 管理后台 innerHTML XSS 转义全部完成

## 2026-06-01 完成清单

### P0 修复
- 支付闭环：requestPayment → queryOrder 轮询 → PAID 确认 → 余额刷新
- .gitignore：数据库、storage、__pycache__、*.pyc 已屏蔽
- 管理后台用户搜索：search→phone 参数匹配修复
- 管理后台 XSS：esc()/escUrl() 全局转义所有 innerHTML 注入点

### P1 修复
- 匿名设备 ID：uni-default 硬编码 → uni_<timestamp>_<random> 持久化
- 退款幂等：idempotency_key 参数 + AUTO_REFUND 前缀去重
- Location Key 池：suggest/regeocode 完整多 Key failover
- 文档统一：README/PROJECT_RULES/PROJECT_PROGRESS/CURRENT_HANDOFF/uniapp README

## C-4 真实报告验证 — 当前阻塞（本轮未修）

- 业态：小餐饮 | 地址：陕二丫擀面皮(兰宝小区店) | 宝鸡
- 结果：AMap 成功、计费扣点/退款链路正确、报告未保存
- 失败原因：LLM 编造假 POI 名称（好又多、学校、住宅小区），P0 guard 拦截但 retry 后仍未通过
- **本轮未修 C-4**：后续单独任务处理。不要顺手改评分、POI 分类、prompt 语义、report_fact_guard。

## 测试基线

```
python -m compileall backend              → PASS
python tests/check_industry_rigor_rules.py → 2168 PASS, 0 FAIL
python tests/check_report_fact_guard.py    → 147 PASS, 0 FAIL
uniapp build:mp-weixin                     → DONE
```
