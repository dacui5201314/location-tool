# Phase 4L-A：学校/校园客流源归并审计

> 审计范围：12 族 business model + location_profile + fallback scoring + enrichment + sample regression
> 审计日期：2026-06-16
> 状态：P0 已实施（e30241f2），P1-A 已实施（Phase 4L-C），P2 + G2/G3 待实施

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

**P0 已关 / P1 残余**（T31-T33 + 2 样本已覆盖 P0，以下标注 P0 已关或 P1 残余）：
- ✅ G1 小吃快餐 school 高+无住宅/办公 → T33 P0 已关（advantages 已带"寒暑假/午间动线/晚餐"核验词）。独立回归样本为可选增强，非 P1 必做。
- ✅ G4 便利店 school=8+res=2 → T31 + retail_convenience_06 P0 已关
- ✅ G5 酒店 school=8+res=3 → T32 + hotel_06 P0 已关
- P1 G2 茶饮 school 高但无步行动线核验 → 需改 business_model_service checklist
- P1 G3 教育培训 school 高但家庭消费力弱 → 需加消费力核验样本

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
- 只有 4 个 model（snack_fast_food, beverage_dessert, education_childcare, education_training）的 YAML 明确将 school 列为 demand_source
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

### P1/P2 未覆盖（Phase 4L-B P0 已关，以下待后续）

| 缺口编号 | 状态 | 场景 | 风险 | 建议测试 |
|---------|------|------|------|---------|
| **G1** | P0 已关 (T33) | 小吃快餐 schools=8, res=2, office=0 | 学校优势必须带核验词 | ✅ advantages 已带"寒暑假/午间动线/晚餐" |
| **G2** | P1 | 茶饮 schools=6 不在校门口动线 | 学校客流≠步行动线客流 | 需改 business_model_service checklist（P1） |
| **G3** | P1 | 教育培训 schools=5, res=2 | 学校多但消费力弱 | 需加消费力核验独立样本（P1） |
| **G4** | P0 已关 (T31) | 便利店 schools=8, res=2 | 学校不写优势 | ✅ T31 + retail_convenience_06 |
| **G5** | P0 已关 (T32) | 酒店 schools=5, office=1, res=3 | school 不参与客群评分 | ✅ T32 + hotel_06 |
| **G6** | P0 已关 | 非教育/餐饮业态不输出"学生客群稳定" | 通用优势三档输出 | ✅ 已实施三档分流 |

---

## 4. Phase 4L-B 实施状态

### 4.1 P0 已实施（e30241f2）

| 改动 | 文件 | 说明 |
|------|------|------|
| `_weighted_school()` | `fallback_report_service.py` | 教育=1.0, 小吃/茶饮=0.3, 其他=0 |
| consumer_profile 评分 | 同上 | `20 + office + weighted_school(school, family)` |
| traffic_flow_detail.pop | 同上 | `r500 + o500 + weighted_school(s500, family)` |
| executive_summary.pop | 同上 | 同上 |
| category_advantage_score.pop | 同上 | 同上 |
| category_advantage_text.pop | 同上 | 同上 |
| competition_score.pop | 同上 | 同上 |
| advantages school_500>=3 | 同上 | 教育→"核验生源与消费力"，小吃/茶饮→"核验午间动线/寒暑假/晚餐"，其他→不输出 |
| T31-T33 | `check_business_model_rules.py` | 便利店/酒店/小吃快餐 school 高 res 低 |
| retail_convenience_06, hotel_06 | `check_sample_regression.py` | 2 个回归样本 |

### 4.2 P1-A 已实施（Phase 4L-C）/ P2 + G2/G3 待实施

| 优先级 | 状态 | 文件 | 改动 | 理由 |
|--------|------|------|------|------|
| **P1-A** | ✅ 已实施 | `location_profile_service.py` | `_k12_school_count()` + 学区判定全部走 K12 有效学校数；T7（全大学不判学区）+ T8（K12 仍判学区） | 大学聚集区不是"学区" |
| **G2** | 待实施 | `business_model_service.py` checklist | 茶饮 school 高但步行动线未核验 | 学校客流≠步行动线客流 |
| **G3** | 待实施 | 测试缺样本 | 教育培训 school 高但消费力弱 | 需加消费力核验独立样本 |
| **P2** | 待实施 | `business_model_service.py` L1021 | `school_500 >= 2 → 插入学校午休动线核验` → 仅在小学/中学时触发 | 大学周边不需要放学动线核验 |
| **P2** | 待实施 | `01_snack_fast_food.yaml` | demand_sources "学校午市" → 加 `仅中小学` | 触发条件过于宽泛 |

待加 P1 样本/测试（可选）：
- snack_fast_food 寒暑假断崖独立回归样本
- beverage_dessert 学校多但步行动线未核验样本
- education_training 学校多但消费力弱样本
- location_profile 大学聚集≠学区测试

### 4.3 始终禁止项

- ❌ report_fact_guard.py / poi_name_guard.py
- ❌ HTML / 小程序 / 支付 / 候选池 / 多点对比 / PDF / 长图
- ❌ prompt 主体
- ❌ YAML schema 结构（可以改 YAML 字段值，不改 schema 定义）

---

## 5. 审计结论摘要

1. **school_500 被过度使用** — ✅ P0 已修正：`_weighted_school()` 按业态区分，7 处评分/文本路径全部走加权。

2. **6 个测试缺口** — ✅ P0 已关 4 个（G1/G4/G5/G6），P1 残余 2 个（G2/G3）。

3. **location_profile 学区判定粗糙** — ✅ P1-A 已修正。`_k12_school_count()` 排除大学/培训，学区判定全部走 K12 有效学校数。全大学不再判学区，K12 足够多仍判学区。G2/G3 仍为后续残余。

---

*审计 2026-06-16，P0 实施 2026-06-16（e30241f2），P1-A 实施 2026-06-16（Phase 4L-C），P2 + G2/G3 待实施。*
