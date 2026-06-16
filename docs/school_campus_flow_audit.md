# Phase 4L-A：学校/校园客流源归并审计

> 审计范围：12 族 business model + location_profile + fallback scoring + enrichment + sample regression
> 审计日期：2026-06-16
> 状态：审计完成，待 Phase 4L-B 实施

## 1. 涉及学校/校园客流的代码位置清单

### 1.1 location_profile_service.py

| 行号 | 函数/逻辑 | school 使用方式 |
|------|----------|----------------|
| 30-50 | `_classify_school(name)` | 按名称关键词分类：elementary / kindergarten / university / middle_high / training / unknown |
| 53-87 | `compute_school_anchor_breakdown()` | 从 `poi_lists.schools` 提取学校列表，输出 `{total, breakdown, note}` |
| 99 | `school_500 = _int(s5.get("schools", 0))` | 定量提取 |
| 108 | `school_500 >= 8 → "学区及周边"` | 位置类型首要判定条件 |
| 118 | `school_500 >= 3 and bus_500 <= 3 ... → "学区弱交通社区型"` | 弱交通学区判定 |
| 120 | `school_500 >= 3 and res_500 >= 5 → "学区社区混合型"` | 混合学区判定 |
| 133 | `school_500 >= 3 and bus_500 <= 3 ... → "学区弱交通社区型"` label | 标签也按学区优先 |
| 134 | `school_500 >= 5 → "学区边缘位置"` label | 学校数 ≥5 即标为学区 |
| 165 | `school_500 >= 5: strengths.append("学区客群基础较好")` | 机械优势语句 |
| 183 | `office_500 < 3 and school_500 < 3` | 学校不足纳入风险判断 |
| 197 | `school_500 >= 3` | 学校数作为 area_profile 属性 |
| 208 | `office_500 < 5 and school_500 < 3` | 学区不足纳入客流风险 |
| 213 | `res_500 < 10 and school_500 < 3` | 双重不足 → 全天客流偏低 |
| 219 | `"schools_500m": school_500` | 输出到 structure |
| 227 | `"school_anchor_breakdown": compute_school_anchor_breakdown(r)` | 学校锚点分解输出 |
| 233 | summary 模板含 `{school_500}所学校` | 摘要中硬编码学校数 |

**问题**：
- `school_500 >= 5` 直接判定"学区客群基础较好" → 不区分小学/大学/培训机构
- `school_500 >= 8` 直接判定"学区及周边" → 大学聚集区不等于学区
- 教育类业态的 `school_anchor_breakdown` 有细分，但非教育业态不使用

### 1.2 business_model_service.py

| 行号 | 函数/逻辑 | school 使用方式 |
|------|----------|----------------|
| 194 | `compute_location_fundamentals()` 读取 `school_500` | 与 location_profile_service 功能重复 |
| 203-214 | 位置类型判定含 `school_500 >= 8 / >= 3` | 同上 |
| 239-240 | strengths: `school_500 >= 5 → "学区客群基础较好"` | 同上 |
| 272 | summary 模板含 school 数 | 同上 |
| 339-340 | `_snapshot_education_childcare` 读取 `school_500/school_200` | 教育托管专用 |
| 386 | `school_500 < 3 and res_500 < 10 → score_explanation` | 教育托管需求不足判定 |
| 413 | `_snapshot_education_training` 读取 `school_500` | 教育培训专用 |
| 453 | `_snapshot_snack_fast_food` 读取 `school_500` | 小吃快餐学校午市客流 |
| 488 | `score_explanation` 提及住宅/办公/学校维度 | 小吃快餐评分 |
| 810 | `_checklist_snack_fast_food` 读取 `school_500` | 只在 checklist 中引用 |
| 926 | `_checklist_education_training` 读取 `school_500` | 教育培训核验项 |
| 1021-1028 | `school_500 >= 2` 时插入"学校午休放学动线"核验项 | 小吃快餐核验清单 |

**问题**：
- `compute_location_fundamentals()` 与 `compute_location_profile()` 逻辑高度重复
- 小吃快餐 checklist 的 `school_500 >= 2` 条件未区分学校类型（大学/小学/培训机构）
- 学校午市对应的"寒暑假断崖"只在 YAML red_flags 中提及，未在 report 中显式输出

### 1.3 fallback_report_service.py

| 行号 | 函数/逻辑 | school 使用方式 |
|------|----------|----------------|
| 41 | `_site_suggestion_detail`: "确认周边小学距离和放学动线" | 教育托管选址提示 |
| 87 | `school_500 = _int(s5.get("schools", 0))` | 提取 |
| 103 | `school_500 >= 8 → _scene = "学区"` | _scene 分类 |
| 140-141 | `school_500 >= 3: advantages.append("学生客群稳定")` | 通用优势语句 |
| 183 | summary 含 school 数 | 摘要 |
| 201-214 | 教育托管/培训的 executive_summary 含放学动线/周末流量提示 | 教育专用 |
| 240 | `_traffic_flow_detail(res, office, school, ...)` | 客流特征维度 |
| 264-265 | `_consumer_profile_detail` + `consumer_profile` 评分: `20 + office + school` | school 直接加到消费人群分！ |
| 320 | `consumer_profile.score = _clamp(25, 80, 20 + office_500 + school_500)` | **所有业态通用** |
| 324 | `_competition_score(..., school_500, ...)` | school 参与竞争评分 |
| 331 | `_category_advantage_score(..., school_500, ...)` | school 参与品类优势评分 |
| 340-341 | `_traffic_flow_detail` 和 `_consumer_profile_detail` | 都传 school |
| 348-349 | details 含 school 数 | 详情输出 |
| 438-439 | `"schools": {"200m": .., "500m": .., "1000m": ..}` | 输出到 evidence_summary |
| 564 | `_build_executive_summary` 传 school_500 | 摘要构造 |
| 586 | `pop = res_500 + office_500 + school_500` | **将学校等同于人口！** |
| 615 | 托管核验提示含小学放学动线 | 教育专用 |
| 646, 650 | `pop = res_500 + school_500 + office_500` | 再次将学校等同于人口 |
| 703 | `_category_advantage_text`: `pop_support = res + office + school` | 品类优势文本用 |
| 723 | `_category_advantage_score`: school 作为参数 | 评分函数 |
| 764 | `_category_advantage_text`: `pop_support = res + office + school` | 同上 |
| 785 | summary 模板含 school | 摘要 |

**严重问题**：
- **line 586/646/650**: `pop = res_500 + office_500 + school_500` — 将学校数量与住宅小区/办公楼**线性加总为人口**，完全没有区分学校类型、学生数量、是否走读
- **line 265/320**: `consumer_profile.score = 20 + office_500 + school_500` — school 直接加到消费人群评分，对所有业态通用
- **line 140-141**: `school_500 >= 3: "学生客群稳定"` — 所有业态共享此优势语句，便利店看到 3 所学校也说"学生客群稳定"

### 1.4 report_enrichment_service.py

| 行号 | school 使用方式 |
|------|---------------|
| 86 | `"schools": {"200m": ..., "500m": ..., "1000m": ...}` 输出到 evidence_summary |

仅做数据透传，不产生新的 school 语义判断。

### 1.5 check_sample_regression.py (测试覆盖)

| 样本 case_id | school 场景 | 验证内容 |
|-------------|-----------|---------|
| snack_fast_food_04 | schools_500m=5, 1000m=8 | 学校强（寒暑假弱未显式测试） |
| snack_fast_food_05 | schools_500m=6, 1000m=10 | 学校密集+晚餐弱 |
| education_childcare_01-05 | schools_500m=3~6 | 暗竞品、放学动线、合规 |
| education_training_01-05 | schools_500m=2~4 | 生源、停车、满班率 |
| beverage_dessert_03 | schools_500m=1 | 学校少，客流弱 |
| retail_convenience_04 | schools_500m=1 | 辅助客流 |

**缺失覆盖**：
- ❌ 小吃快餐：schools_500m=8 但无住宅/办公 → 寒暑假断崖风险未测试
- ❌ 茶饮：schools_500m=6 但无步行动线核验 → 学校客流≠步行动线客流
- ❌ 教育培训：schools_500m=5 但家庭消费力弱 → 学校数高但生源质量低
- ❌ 便利店/零售：schools_500m=8 → 学校成为主导客流（不应如此）

---

## 2. 12 个 YAML 中 school 作为 demand_source / anchor / risk

| model_id | school 角色 | 具体用法 | 问题 |
|----------|-----------|---------|------|
| snack_fast_food | **demand_source** (high) | `schools >= 1 → "学校午市"` | 不区分学校类型、寒暑假断崖只在 red_flags/blind_spots 提及 |
| food_service | **无直接引用** | — | school 不在 demand_sources 中，但 fallback scoring 仍对 school 加分 |
| beverage_dessert | **demand_source 触发条件** | `schools >= 2 or office >= 5 → "年轻客群"` | 学校客群≠步行经过门店的客群；学校门口 vs 500m 外完全不同 |
| retail_convenience | **无直接引用** | — | school 不在 YAML demand_sources 中 |
| pharmacy | **无直接引用** | — | — |
| retail_shopping | **无直接引用** | — | — |
| education_childcare | **核心 demand_source** | `schools >= 3`，weak_demand_threshold 含 schools | 仅限小学，YAML forbidden_misreadings 明确禁止把大学/幼儿园/中学混入 |
| education_training | **demand_source** | `schools >= 3 → "周边生源"` | forbidden_misreadings 禁止混入大学/幼儿园/中学生源 |
| service_beauty | **无直接引用** | — | — |
| service_basic | **无直接引用** | — | — |
| hotel | **无直接引用** | — | — |
| entertainment | **无直接引用** | — | — |

**结论**：
- 只有 3 个族（snack_fast_food, beverage_dessert, education_childcare, education_training）的 YAML 明确将 school 列为 demand_source
- 但 **fallback_report_service 的 scoring 对所有 12 族都使用 `school_500`** 参与 consumer_profile、category_advantage、traffic_flow 评分
- 这导致 hotel/entertainment/retail 等非教育业态也被 school 数"污染"评分

---

## 3. 已有测试覆盖 - school 场景缺口

### 已覆盖 ✅
| 场景 | 测试 |
|------|------|
| 教育托管 0 POI + 暗竞品 | T2-T5, education_childcare_01-05 |
| 教育培训 school=3~4 生源判断 | education_training_01-05 |
| 小吃快餐 school=5~6 + 外卖 | snack_fast_food_04, snack_fast_food_05 |
| 非教育业态不出现托管核验词 | T5, T28 |
| YAML forbidden_misreadings: 大学≠小学托管客源 | YAML schema 检查（T24 PH4H beauty absorbed） |

### 未覆盖 ❌（Phase 4L-B 应补齐）

| 缺口编号 | 场景 | 风险 | 建议测试 |
|---------|------|------|---------|
| **G1** | 小吃快餐 schools_500m=8, res_500=2, office_500=0 | 学校主导但寒暑假/周末断崖，"学生客群稳定"被误写为优势 | 优势中不得出现"学生客群稳定"无寒暑假提示 |
| **G2** | 茶饮 schools_500m=6, 门店不在校门口动线上 | 学校客流≠步行动线客流，POI 学校数高但实际无人经过 | checklist 必须含"步行动线"核验 |
| **G3** | 教育培训 schools_500m=5, res_500=2（老旧小区） | 学校多但周边家庭消费力弱 | 不得写"生源充足"；必须提示"消费力核验" |
| **G4** | 便利店 schools_500m=8, res_500=2 | 学校成为主导客流源，但便利店核心是住宅 | 不应将学校写为优势 |
| **G5** | 酒店 schools_500m=5, office_500=1, res_500=3 | 学校数参与 consumer_profile 评分，不合逻辑 | 酒店客群评分不应被学校抬高 |
| **G6** | 所有业态 school_500 >= 3 → "学生客群稳定" | 通用优势语句对所有业态生效 | 非教育/餐饮业态不应出现此句 |

---

## 4. Phase 4L-B 最小实现建议

### 4.1 需要改的代码

| 优先级 | 文件 | 改动 | 理由 |
|--------|------|------|------|
| **P0** | `fallback_report_service.py` L586/646/650 | `pop = res_500 + office_500 + school_500` → 按业态区分 school 权重（教育=1.0，餐饮=0.3，其他=0） | 当前将学校等同于人口 |
| **P0** | `fallback_report_service.py` L265/320 | consumer_profile 评分 `20 + office + school` → 按业态加权 | 酒店/娱乐/零售不应被 school 影响客群评分 |
| **P1** | `fallback_report_service.py` L140-141 | `school_500 >= 3 → "学生客群稳定"` → 加业态判断 | 只对教育/餐饮输出此优势 |
| **P1** | `location_profile_service.py` L165 | `school_500 >= 5 → "学区客群基础较好"` → 使用 school_anchor_breakdown 区分小学/大学 | 大学聚集区不是"学区" |
| **P1** | `location_profile_service.py` L108 | `school_500 >= 8 → "学区及周边"` → 同样需要细分 | 同上 |
| **P2** | `business_model_service.py` L1021 | `school_500 >= 2 → 插入学校午休动线核验` → 仅在小学/中学存在时触发 | 大学周边不需要放学动线核验 |
| **P2** | `01_snack_fast_food.yaml` | demand_sources "学校午市" → 加条件 `仅中小学` | 寒暑假提示已有，但触发条件过于宽泛 |

### 4.2 需要新增的回归样本（建议 +6）

| 样本 case_id | 场景 | expected_present | expected_absent |
|-------------|------|-----------------|----------------|
| snack_fast_food_06_schoolonly | schools=8, res=2, office=0 | "寒暑假","断崖"或"晚餐弱" | "学生客群稳定" |
| beverage_dessert_06_schoolflow | schools=6, res=2 | "步行动线","学校门口" | "年轻客群充足" |
| education_training_06_weakspend | schools=5, res=2 | "消费力核验" | "生源充足" |
| retail_convenience_06_schooldominant | schools=8, res=2 | "住宅不足" | "学生客群稳定" |
| hotel_03_no_school_bias | schools=5+ | — | consumer_profile 评分不受 school 抬高 |
| generic_school_advantage | any non-edu/dining | — | 通用优势不含"学生客群" |

### 4.3 需要新增的 business_model_rules 测试项（建议 +4）

| 测试 ID | 内容 |
|---------|------|
| T31 | 小吃快餐 school=8+res=2 → 优势不得含"学生客群稳定"无寒暑假提示 |
| T32 | 便利店 school=5+ → consumer_profile 评分不受 school 主导 |
| T33 | hotel/entertainment 业态 school_500 不参与客群评分 |
| T34 | location_profile school>=8 但全是大学 → location_type 不为"学区及周边" |

### 4.4 禁止项（Phase 4L-B 也不能碰）

- ❌ report_fact_guard.py / poi_name_guard.py
- ❌ HTML / 小程序 / 支付 / 候选池 / 多点对比 / PDF / 长图
- ❌ prompt 主体
- ❌ YAML schema 结构（可以改 YAML 字段值，不改 schema 定义）

---

## 5. 审计结论摘要

1. **school_500 被过度使用**：`fallback_report_service.py` 将 `school_500` 与 `res_500`、`office_500` 线性加总为人口（L586/646/650），对所有 12 族生效，而 YAML 中仅 3 个族将 school 列为 demand_source。

2. **6 个测试缺口**：小吃快餐学校主导无寒暑假提示、茶饮学校多但步行动线未核验、教育培训学校多但消费力弱、便利店学校主导、酒店/娱乐被 school 抬高评分、通用优势误写学生客群。

3. **location_profile 学区判定粗糙**：`school_500 >= 8` 直接判为"学区及周边"，已有 `school_anchor_breakdown` 做类型细分但未被使用。

4. **最小修复路径**：P0 改 fallback scoring 的 school 权重按业态区分 + P1 改通用优势语句的业态判断 + 6 样本 + 4 规则测试。

---

*审计完成于 2026-06-16。Phase 4L-B 待执行。*
