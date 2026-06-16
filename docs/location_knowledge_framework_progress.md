# 址得选 选址知识框架建设进度 v2026-06-16

## 已完成

### Phase 0：位置基本面 + YAML schema
- `services/location_profile_service.py`：确定性位置打标，school_anchor_breakdown
- `knowledge/location_profiles.yaml`：位置类型/标签规则
- `knowledge/location_profile_schema.yaml`：schema
- `knowledge/business_model_schema.yaml`：生意模型 schema
- `knowledge/source_card_schema.yaml`：来源卡 schema

### Phase 1：12 族群 YAML 全部补齐
| # | model_id | competition.type |
|---|----------|-----------------|
| 01 | snack_fast_food | 排斥型 |
| 02 | food_service | 半聚集型 |
| 03 | beverage_dessert | 半聚集型 |
| 04 | retail_convenience | 排斥型 |
| 05 | pharmacy | 中性型 |
| 06 | retail_shopping | 中性型 |
| 07 | education_childcare | 暗竞品型 |
| 08 | education_training | 聚集型 |
| 09 | service_basic | 暗竞品型 |
| 10 | service_beauty | 暗竞品型 |
| 11 | hotel | 聚集型 |
| 12 | entertainment | 聚集型 |

- `services/business_model_service.py`：`load_business_model()`、`classify_business_model_family()`、`compute_business_model_snapshot()`、`build_business_field_checklist()`
- `services/report_enrichment_service.py`：normal/retry/fallback 三条链路统一 P1 模块补齐

### Phase 1.5：知识蒸馏框架
- `docs/location_knowledge_distillation_plan.md`：蒸馏 SOP（6 类来源版权边界）
- `docs/source_material_intake_template.md`：外部资料接入模板
- `docs/source_material_inventory.md`：用户清单与本地资料对照盘点
- 15 张独立 source card：internal_sample_001、product_review_001-006、book_001/002/003/005/011/012/013、report_summary_001
- `knowledge/sources/source_manifest.yaml`：24 条来源清单
- source_refs 结构化追溯（YAML → source card 可追溯）

### Phase 2：补齐剩余族群 + 覆盖矩阵
- Phase 2A：02/08/09 三个族群 YAML
- Phase 2B：05/06/11/12 四个族群 + pharmacy 最小服务接入
- Phase 2C：覆盖矩阵（45 叶子类型、14 master key、YAML keyword 一致性）
- 分类器改进：pharmacy 独立、日餐/串串/涮锅 → food_service、干洗 → service_basic、夜经济 → entertainment

### Phase 3：展示链路审计
- normal/retry/fallback 三路径 report JSON 字段完整性
- HTML/小程序只渲染 report_json，不生成业务判断（静态源码扫描）
- storage_service 业务逻辑守门
- HTML 10 字段 + 小程序 7 字段验收

### Phase 4：样本回归库
- **36 个样本，12 族 x3**（1 基础 + 1 高风险 + 1 误判场景）
- 每样本 expected_present/expected_absent，JSON+HTML 双文本扫描
- 元测试：EXPECTED_MODEL_IDS 常量、set 精确匹配、每族 >=3、case_id 唯一

## 当前测试矩阵

| 测试文件 | 项数 | 状态 |
|---------|------|------|
| check_report_fact_guard.py | 188 | PASS |
| check_industry_rigor_rules.py | 2178 | PASS |
| check_fallback_report.py | 2 | PASS |
| check_p05_report_quality.py | 13 | PASS |
| check_p1_business_model_quality.py | 22 | PASS |
| check_location_profile_rules.py | 6 | PASS |
| check_business_model_rules.py | 21 | PASS |
| check_report_enrichment_service.py | 11 | PASS |
| check_knowledge_schema_rules.py | 16 | PASS |
| check_sample_regression.py | 36 | PASS |

## 明确不做 / 不纳入本轮

- 不新增候选点池、多点对比、支付链路、PDF、长图。
- 不重构 prompt 主体来掩盖业务模型问题。
- 不放宽 report_fact_guard.py。
- 不放宽 poi_name_guard.py。

## 后续只允许围绕本方案继续

- 报告精准度样本扩充：36 → 60（12 族 x5）。
- 外部资料蒸馏继续补齐，但只做 source card 候选规则，不直接改变报告行为。
- source card → YAML 吸收时必须补 source_refs 和回归测试。
- 学校/校园客流源归并。
- 小餐饮竞品分层。
- 公交站去重。
