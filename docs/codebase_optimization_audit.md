# Phase 4R/4S 代码体检审计 v2026-06-18

> 本文继续作为代码体检和后续拆分建议，不作为当前窗口的大重构任务单。2026-06-18 的前端/管理后台优化已落地一轮，本文件同步最新大文件和风险边界。

## 大文件清单（>500 行）

| 文件 | 行数 | 职责 | 可拆方向 |
|------|------|------|---------|
| `backend/routers/admin.py` | 1977 | 管理后台全部 API | 按模块拆：dashboard / users / reports / feedback / config / storage / sku / cdk |
| `backend/services/amap_service.py` | 1501 | 高德 POI 采集 + 脱水 + 分类 + 公交专项 | 拆为 amap_fetch / amap_dehydrate / amap_classify / amap_bus |
| `backend/services/business_model_service.py` | 1272 | 12 族 snapshot/checklist/分类器 | 按族群拆 or 拆分 snapshot 与 checklist 为独立文件 |
| `uniapp/src/pages/home/index.vue` | 1465 | 首页选址流程、地图、业态、生成入口 | 拆 location/business/profile/submit 子组件 |
| `backend/main.py` | 1219 | FastAPI 入口 + SSE 端点 + 全局中间件 | 路由模块化：analyse_router / health_router |
| `uniapp/src/pages/report-detail/index.vue` | 1254 | 小程序报告详情完整展示 | 拆 score/decision/evidence/checklist/feedback 模块 |
| `backend/routers/virtual_pay.py` | 1178 | 微信虚拟支付全链路 | 拆为 virtual_pay_prepay / virtual_pay_notify / virtual_pay_refund |
| `backend/admin/index.html` | 632 | 管理后台 HTML + 内联脚本 | 短期可维护；中期拆 admin.js/admin.css 或引入轻量工程 |

## 主链路过长（本轮禁止重构）

**`backend/main.py` `/api/analyze`** — SSE 六步编排 + LLM 调用 + 事实校验 + retry 兜底 + refund 收口。当前 1219 行中有 ~500 行属于该端点。

- 风险：改动一处可能影响整个分析链路
- 约束：本轮禁止拆解该端点
- 后续方向：将六步提取为独立 service（`analyse_orchestrator.py`），main.py 只保留路由声明

## 管理后台 IA 臃肿

**`backend/admin/index.html`** — 单文件 ~632 行，包含仪表盘、用户、报告库、反馈处理、订单、账户流水、SKU/CDK、Key 池、存储配置、分享配置、系统配置等后台页。

- 风险：新功能添加时 HTML 持续膨胀
- 当前状态：2026-06-18 已完成 IA 分组、报告库预览、反馈处理、存储配置状态等体验修补
- 后续方向：不要在上线前做大迁移；稳定后再考虑拆为 `admin.js` / `admin.css` / 模块化页面

**`backend/routers/admin.py`** — 1977 行单文件，覆盖全部管理 API。建议按业务模块拆分为 admin_dashboard / admin_users / admin_reports / admin_feedback / admin_orders / admin_config 等独立路由文件。

**`uniapp/src/pages/home/index.vue`** 与 **`uniapp/src/pages/report-detail/index.vue`** 已成为小程序最大页面。当前优先保证上线体验和回归稳定，后续可按组件边界拆分，不在临近上线时做结构性重构。

## System Prompt / Prompt 路径保护

**`backend/prompts/system_prompt.py`** + **`backend/prompts/industry_prompt.py`** 仍是有效报告生成路径。

- 原则：后台优化只改 UI/交互/管理功能，不得修改 prompt 语义、配置阈值或 YAML 规则
- 任何 prompt 改动必须通过 check_report_fact_guard.py + check_business_model_rules.py 回归

## 前端工程

- **`uniapp/`** — 小程序主工程（Vue 3 + Vite → 微信小程序）。包含首页/报告详情/个人中心/充值/收藏/登录等全部页面
- **`miniprogram/`** — 旧版登录参考工程。不再主动维护，仅保留作为历史参考

## 2026-06-18 新增技术债

- 管理后台报告库预览目前仍在 `backend/admin/index.html` 内联渲染；虽然已经与小程序字段对齐，但继续扩展会让单文件维护成本升高。
- 反馈闭环新增了用户端和后台端状态，后续若增加筛选/附件预览/批量处理，建议先拆后台前端脚本。
- 小程序报告详情页只消费 `report_json`，但展示模块已较多；后续组件抽取必须保持字段来源不变。

## 本轮清理

- `uniapp/src/utils/api.js` L237：422 错误详情 console.log → dev-gate（`process.env.NODE_ENV !== 'production'`）。
- 登录页审核文案去除容易混淆官方的“微信”字样。
- 后台和小程序时间展示统一按北京时间呈现。
