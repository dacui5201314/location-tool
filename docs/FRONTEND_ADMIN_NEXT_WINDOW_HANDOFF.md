# 前端 / 管理后台 下一窗口交接 v2026-06-18

## 交接范围

下一窗口继续只做**前端体验 + 管理后台优化 + 上线验证**，不继续推进报告精准度主线。

2026-06-18 这一轮已把小程序报告页、首页流程、反馈闭环、管理后台 IA 和报告库预览补了一轮。下个窗口重点不是重写，而是部署核对、真机/真实数据验收和少量体验修补。

## 2026-06-18 已完成

### 小程序前端

- 首页流程按“选位置 -> 选业态 -> 填画像 -> 出报告”重新梳理，地址展示做了压缩，弱化第三方平台名称。
- 报告详情页以小程序端为准重排：综合评分置顶、结论卡增加间距、优势/风险上下排列、现场核验清单重新排版、竞品口径和数据边界脱敏。
- 登录页去除容易混淆腾讯官方的“微信”字样，手机号授权提示改为“手机号快捷登录”。
- 新增“我的反馈”链路：用户可在报告详情和个人中心提交反馈，并查看运营回复。
- 维持报告分享的公开查看口径；不强制被分享人先登录，避免影响分享裂变。

### 管理后台

- 菜单 IA 已按概览、客户与报告、交易与权益、配置中心分组。
- 仪表盘增加今日新增用户、今日报告、今日反馈、今日实收等运营指标；今日实收按 PAID 实收口径。
- 报告库预览改为从 `report_json` 结构化渲染，向小程序报告详情对齐；支持下载 HTML 报告。
- 反馈处理页可查看用户反馈、报告来源、处理状态，并写入运营回复同步到用户端“我的反馈”。
- 存储配置的本地/阿里云/腾讯云按钮状态已修正；云存储上传成功后以云端 URL 为准，并清理本地临时文件。
- 后台和小程序时间展示统一按北京时间显示，后端旧 naive 时间按 UTC 兼容处理。

## 下一窗口优先级

### P0：上线与真实链路验证

- 同步本轮变更到服务器，执行 `database.init_db()` 补齐 feedback 字段。
- 重启后端后验证 `/api/health`、反馈提交、我的反馈、后台回复、报告库预览、HTML 下载。
- 用真实报告样本检查后台报告预览是否与小程序展示字段一致，尤其是维度标题、评分卡、现场核验清单、竞品口径、数据边界。
- 真机或微信开发者工具重新验证“手机号快捷登录”审核文案、报告详情、反馈页、分享报告。

### P1：体验微调

- 统一按钮、卡片、表单、状态标签、空状态、错误态。
- 继续检查移动端文字溢出、层级混乱、信息密度问题。
- 管理后台报告库和反馈处理如继续变复杂，再补筛选、抽屉和批量状态。

### P2：拆分建议

- `backend/admin/index.html` 已继续变厚，短期可维护；中期建议拆出静态 JS/CSS 或引入轻量前端工程。
- `uniapp/src/pages/home/index.vue`、`uniapp/src/pages/report-detail/index.vue` 已是大页面，后续可拆报告模块组件，但不要在上线前做大重构。

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

```powershell
cd C:\Users\admin\location-tool\backend
C:\Users\admin\.local\bin\uv.exe run python tests\check_business_model_rules.py
C:\Users\admin\.local\bin\uv.exe run python tests\check_sample_regression.py
C:\Users\admin\.local\bin\uv.exe run python tests\check_report_fact_guard.py
C:\Users\admin\.local\bin\uv.exe run python tests\check_report_enrichment_service.py

cd C:\Users\admin\location-tool\uniapp
npm.cmd run build:mp-weixin
```

## 当前基线

- Sample: 71, BM: 46, LP: 12, Schema: 18, Fact Guard: 188
- `check_report_enrichment_service.py` PASS
- `npm.cmd run build:mp-weixin` PASS
- 版本 v4.1.0，基线 commit `36ce17b5`；当前工作区包含前端/后台优化改动，交付前需重新确认 git status
