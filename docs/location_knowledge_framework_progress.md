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
- **60 个 Phase 4J 基线样本 + 1 个 Phase 4K category-only 宠物店防回归样本，共 61**（4A: 12基础 → 4B: +6高风险 → 4C: +12第三样本 → 4D: 扩至36 → 4J: +24 → 60 → 4K fix-1: +1）
- 每样本 expected_present/expected_absent，JSON + HTML 双文本扫描，禁止表达扫描
- expected_model_id 60/60 全覆盖，meta 强制必填且断言 `expected_model_id == model_id`
- 元测试：EXPECTED_MODEL_IDS 常量、set 精确匹配、每族 >=5、case_id 唯一
- **Phase 4K 已收口**：宠物店物业/噪音/气味限制已通过 `_is_pet_business(business_type, brand_name, category)` 三参数检测 + snapshot.must_verify/stop_condition + field_checklist 确定性注入 report_json。
  - `service_beauty_05`：覆盖 `business_type="宠物店"`，expected_present 含 物业/噪音/气味 ✅
  - `service_beauty_06`：覆盖 `business_type="专业生活服务"`, `category="宠物店"`（category-only 路径），expected_present 含 物业/噪音/气味 ✅
  - 两条路径均要求 report_json/HTML 出现 物业/噪音/气味。非宠物业态（美容美发/健身）不受影响。source_refs 不变（沿用 product_review_004）。
- **Phase 4K fix-1**：修复 `_is_pet_business()` 支持 category 参数但 `_snapshot_service_beauty` / `_checklist_service_beauty` 未传 category 导致 category-only 宠物店漏识别问题。`compute_business_model_snapshot` 和 `build_business_field_checklist` 对 service_beauty 族类分流传 `category=`，`build_fallback_report` 加 `category` 参数防止 enrich 幂等跳过覆盖。

### Phase 4L-A：学校/校园客流源归并审计
- 新增 `docs/school_campus_flow_audit.md`：审计 12 族 × 4 service + YAML + 61 样本中 school 使用口径
- 发现 **6 个测试缺口**、**fallback scoring 对非教育业态误用 school**、**location_profile 学区判定不区分学校类型**
- **Phase 4L-B P0 已实施**（e30241f2）：`_weighted_school()` 按业态区分 school 权重、7 处评分路径走加权、通用优势三档输出、T31-T33 + 2 样本。P1/P2（location_profile 学区细分、checklist 学校类型）待后续。

## 当前测试矩阵

| 测试文件 | 项数 | 状态 |
|---------|------|------|
| check_report_fact_guard.py | 188 | PASS |
| check_industry_rigor_rules.py | 2178 | PASS |
| check_fallback_report.py | 2 | PASS |
| check_p05_report_quality.py | 13 | PASS |
| check_p1_business_model_quality.py | 22 | PASS |
| check_location_profile_rules.py | 6 | PASS |
| check_business_model_rules.py | 37 | PASS |
| check_report_enrichment_service.py | 11 | PASS |
| check_knowledge_schema_rules.py | 16 | PASS |
| check_sample_regression.py | 63 | PASS |

## 明确不做 / 不纳入本轮

- 不新增候选点池、多点对比、支付链路、PDF、长图。
- 不重构 prompt 主体来掩盖业务模型问题。
- 不放宽 report_fact_guard.py。
- 不放宽 poi_name_guard.py。

## 后续只允许围绕本方案继续

- ~~报告精准度样本扩充：36 → 60（12 族 x5）~~ ✅ 已完成（Phase 4J）。
- ~~宠物店物业/噪音/气味限制 YAML/service 吸收~~ ✅ 已完成（Phase 4K）。
- ~~学校/校园客流源归并审计~~ ✅ 已完成（Phase 4L-A）。详见 `docs/school_campus_flow_audit.md`。
- 外部资料蒸馏继续补齐，但只做 source card 候选规则，不直接改变报告行为。
- source card → YAML 吸收时必须补 source_refs 和回归测试。
- 学校/校园客流源归并 P1/P2：location_profile 学区细分 + business_model_service checklist 学校类型（P0 已关，P1/P2 待做）。
- ~~学校/校园客流源归并 P0 实施~~ ✅ 已完成（Phase 4L-B）。`_weighted_school()` 按业态区分 school 权重；consumer_profile / traffic_flow / executive_summary / category_advantage / competition 五个评分路径全部走加权；通用优势 school_500>=3 按 family 分教育/餐饮/禁止三档输出。新增 T31-T33 + 2 样本（retail_convenience_06, hotel_06）。
