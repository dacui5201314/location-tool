# 前端 / 管理后台 下一窗口交接 v2026-06-17

## 交接范围

下一窗口只做**前端体验 + 管理后台优化**，不涉报告业务逻辑。

## 约束清单（红线）

以下模块在新窗口中**禁止修改语义**：

| 禁止触碰 | 说明 |
|----------|------|
| `backend/prompts/system_prompt.py` | Prompt 主体语义不变 |
| `backend/prompts/industry_prompt.py` | 业态 Prompt 语义不变 |
| `backend/knowledge/business_models/*.yaml` | 12 族 YAML 业务规则不变 |
| `backend/knowledge/sources/*.yaml` | Source card 不变 |
| `backend/services/report_fact_guard.py` | 事实校验不变 |
| `backend/services/poi_name_guard.py` | POI 名称守卫不变 |
| `backend/services/business_model_service.py` | Snapshot/checklist 逻辑不变 |
| `backend/services/fallback_report_service.py` | Fallback 评分逻辑不变 |
| `backend/services/location_profile_service.py` | 位置基本面不变 |
| `backend/main.py` `/api/analyze` | 主分析链路不变 |
| `uniapp/src/pages/report-detail/index.vue` | 报告展示页不做业务逻辑改动 |

## 可以做

| 范围 | 允许 |
|------|------|
| 管理后台 UI | 仪表盘布局、表单交互、菜单结构优化 |
| 管理后台 IA | 标签页拆分、导航重组 |
| 小程序前端 | Home 页视觉、搜索体验、登录流程、充值/收藏页 UI |
| uniapp 组件 | 抽取公共组件、样式统一 |
| 后端 API | 仅允许为 UI 需求新增查询端点，不改已有端点语义 |

## 测试回归

任何改动后必须跑：

```
python tests/check_business_model_rules.py
python tests/check_sample_regression.py
python tests/check_report_fact_guard.py
python tests/check_report_enrichment_service.py
npm run build:mp-weixin
```

## 当前基线

- Sample: 71, BM: 46, LP: 12, Schema: 18, Fact Guard: 188
- 全部 7 套测试 PASS
- 版本 v4.1.0，已推送 GitHub
