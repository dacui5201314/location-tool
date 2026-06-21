# 址得选 · 当前交接文档

**状态**：第一阶段收口（2026-06-21）

## 当前阶段

报告精准度 / 选址知识蒸馏框架第一阶段已关闭，内容如下：

1. 前端体验优化。
2. 管理后台信息架构与 UI 优化。
3. 反馈闭环、部署同步和真实链路验收。
4. 保持报告生成逻辑、YAML、guard、prompt 语义不回退。

## 2026-06-18 已完成

- 小程序首页流程、报告详情页、登录审核文案、我的反馈页完成一轮体验优化。
- 管理后台菜单 IA、仪表盘指标、报告库结构化预览、HTML 下载、反馈处理、存储配置状态完成一轮优化。
- 用户反馈闭环已打通：报告详情/个人中心提交，后台回复，用户端“我的反馈”查看。
- 报告分享保持公开 token 查看，不强制被分享人登录。
- 后台和小程序时间展示按北京时间统一。

## 当前必读入口

- `docs/FRONTEND_ADMIN_NEXT_WINDOW_HANDOFF.md`：前端/管理后台下一窗口执行边界与 2026-06-18 已完成清单。
- `report_product_rectification_plan.md`：报告产品整改总账。
- `docs/location_knowledge_framework_progress.md`：报告精准度与知识框架最终进度。
- `docs/codebase_optimization_audit.md`：代码体检和后续拆分建议。
- `docs/production_deployment_boundary.md`：生产部署文件边界。
- `uniapp/README.md`：小程序主工程和当前前端能力。
- `miniprogram/README.md`：旧原生小程序参考口径。

## 当前基线

- Sample Regression：71 PASS
- Business Model Rules：46 PASS
- Location Profile Rules：12 PASS
- Knowledge Schema：18 PASS
- Fact Guard：188 PASS
- Industry Rigor：2178 PASS
- Source Cards：18 张（15 absorbed + 3 candidate）

## 当前红线

- 不改 `/api/analyze` 主分析链路。
- 不改 `backend/knowledge/business_models/*.yaml`。
- 不改 `backend/knowledge/sources/*.yaml`。
- 不改 `backend/services/report_fact_guard.py`。
- 不改 `backend/services/poi_name_guard.py`。
- 不改 `backend/services/business_model_service.py`、`fallback_report_service.py`、`location_profile_service.py` 的业务语义。
- 不改 prompt 语义。
- HTML/小程序只展示 `report_json`，不得各自生成业务判断。

## 常用回归

```powershell
cd C:\Users\admin\location-tool\backend
C:\Users\admin\.local\bin\uv.exe run python tests\check_business_model_rules.py
C:\Users\admin\.local\bin\uv.exe run python tests\check_sample_regression.py
C:\Users\admin\.local\bin\uv.exe run python tests\check_report_fact_guard.py
C:\Users\admin\.local\bin\uv.exe run python tests\check_report_enrichment_service.py

cd C:\Users\admin\location-tool\uniapp
npm.cmd run build:mp-weixin
```

## 说明

服务器路径、域名、小程序 AppID、支付配置等运行信息以当前服务器和后台配置为准。旧交接文档中的历史值仅供追溯，不作为当前上线验收依据。

## 下一个窗口接手指令

先读：

1. `CURRENT_HANDOFF.md`
2. `docs/FRONTEND_ADMIN_NEXT_WINDOW_HANDOFF.md`
3. `docs/production_deployment_boundary.md`
4. `docs/codebase_optimization_audit.md`
5. `docs/location_knowledge_framework_progress.md`
6. `uniapp/README.md`
7. `miniprogram/README.md`

然后执行：

```powershell
git status
git log --oneline -5
```

接手后优先做服务器同步和真实链路验收；除非用户明确要求，不继续改报告精准度、YAML、guard、prompt 或 `/api/analyze` 主链路。
