# Phase 4R 代码体检审计 v2026-06-17

> 本轮只审计，不重构。标记将来可拆大文件、臃肿模块、可优化路径。

## 大文件清单（>500 行）

| 文件 | 行数 | 职责 | 可拆方向 |
|------|------|------|---------|
| `backend/routers/admin.py` | 1971 | 管理后台全部 API | 按模块拆：dashboard / users / orders / config / keys / sku / cdk |
| `backend/services/amap_service.py` | 1501 | 高德 POI 采集 + 脱水 + 分类 + 公交专项 | 拆为 amap_fetch / amap_dehydrate / amap_classify / amap_bus |
| `backend/services/business_model_service.py` | 1272 | 12 族 snapshot/checklist/分类器 | 按族群拆 or 拆分 snapshot 与 checklist 为独立文件 |
| `backend/main.py` | 1219 | FastAPI 入口 + SSE 端点 + 全局中间件 | 路由模块化：analyse_router / health_router |
| `backend/routers/virtual_pay.py` | 1178 | 微信虚拟支付全链路 | 拆为 virtual_pay_prepay / virtual_pay_notify / virtual_pay_refund |
| `backend/admin/index.html` | 517 | 管理后台 HTML | 不做拆分（独立页面，非模块化需求） |

## 主链路过长（本轮禁止重构）

**`backend/main.py` `/api/analyze`** — SSE 六步编排 + LLM 调用 + 事实校验 + retry 兜底 + refund 收口。当前 1219 行中有 ~500 行属于该端点。

- 风险：改动一处可能影响整个分析链路
- 约束：本轮禁止拆解该端点
- 后续方向：将六步提取为独立 service（`analyse_orchestrator.py`），main.py 只保留路由声明

## 管理后台 IA 臃肿

**`backend/admin/index.html`** — 单文件 ~517 行，包含仪表盘/用户/订单/业态/SKU/CDK/Key池/配置/审计 9 个标签页。

- 风险：新功能添加时 HTML 持续膨胀
- 约束：本轮不改
- 后续方向：考虑拆为多页面或引入轻量前端框架

**`backend/routers/admin.py`** — 1971 行单文件，覆盖全部管理 API。建议按业务模块拆分为 admin_users / admin_orders / admin_config 等独立路由文件。

## System Prompt / Prompt 路径保护

**`backend/prompts/system_prompt.py`** + **`backend/prompts/industry_prompt.py`** 仍是有效报告生成路径。

- 原则：后台优化只改 UI/交互/管理功能，不得修改 prompt 语义、配置阈值或 YAML 规则
- 任何 prompt 改动必须通过 check_report_fact_guard.py + check_business_model_rules.py 回归

## 前端工程

- **`uniapp/`** — 小程序主工程（Vue 3 + Vite → 微信小程序）。包含首页/报告详情/个人中心/充值/收藏/登录等全部页面
- **`miniprogram/`** — 旧版登录参考工程。不再主动维护，仅保留作为历史参考

## 本轮清理

- `uniapp/src/utils/api.js` L237：422 错误详情 console.log → dev-gate（`process.env.NODE_ENV !== 'production'`）
