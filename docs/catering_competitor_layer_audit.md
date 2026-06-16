# Phase 4M-A：小餐饮竞品分层审计

> 审计范围：snack_fast_food / food_service / beverage_dessert 三族的竞品口径
> 审计日期：2026-06-16
> 状态：P0 已实施（4M-B），G1/G2 已关；G3/G4/G5/G6 待 4M-C

## 1. 现有代码位置清单

### 1.1 business_model_service.py — 三族 snapshot 竞品逻辑

| 行号 | 函数 | 竞品逻辑 |
|------|------|---------|
| L461-514 | `_snapshot_snack_fast_food` | 四档 competitor_note：近场0+远场多 / 近场0+远场少 / 远场>=10 / 默认。引用 `dc_200/dc_500/dc_1000/restaurants_1k` |
| L519-534 | `_snapshot_food_service` | 静态 snapshot，competitor_note 为空，未使用 dc/restaurants 数据 |
| L538-560 | `_snapshot_beverage_dessert` | 静态 snapshot，competitor_note 为空（4L-D 追加了 school 感知，但竞品侧仍空） |

**问题**：
- `food_service` 和 `beverage_dessert` 的 snapshot 完全不使用实时 competitor 数据，competitor_note 为空字符串
- 只有 `snack_fast_food` 有差异化 competitor_note
- food_service YAML 定义了 `zero_competitor_policy: "0 竞品不是蓝海……"` 但 snapshot 未落地

### 1.2 fallback_report_service.py — 竞品评分/优势/摘要

| 行号 | 函数 | 竞品逻辑 | 问题 |
|------|------|---------|------|
| L136-152 | advantages | 小吃快餐 200m=0+远场多 → 特殊措辞；教育托管 → 暗竞品提示；其他 → `sub_200>0 or sub_500>0` → "替代消费较多需核验" | food_service/beverage 0竞品时走默认"竞争压力较小" |
| L176-177 | disadvantages | 仅 `dc_200 > 15` 触发 | 不区分品类类型 |
| L342-346 | `_competition_score` | 所有族通用公式 `85 - dc_200*2 - dc_500 - dc_1000//2`，仅在 `dc_1000>=4` 时封顶60。小吃快餐额外 `dc_200==0 and dc_1000>=8 → min(base, 70)` | 正餐/茶饮无品类差异化封顶 |
| L349-353 | `_category_advantage_score` | 通用 `85 - dc_200*3 - dc_500 - (dc_1000-8)*2`，小吃快餐 `dc_200==0 and dc_1000>=8` 无额外处理 | food_service/beverage 半聚集型 0竞品不应机械加分 |
| L362-366 | `_category_advantage_text` | 小吃快餐有专属远场逻辑；food_service/beverage 走通用"直接竞品较少"文本 | 正餐 0竞品不会提示"半聚集型需看餐饮生态" |
| L393-423 | `_build_executive_summary` | 小吃快餐有 `restaurants_1k` 远场判断；food_service/beverage 走通用分支 | 正餐/茶饮不引用 `restaurants_1k` |
| L520-578 | `_detect_same_brand_risk` | 所有族通用，从 `direct_competitor_list` 检测同品牌分店 | 对餐饮有效，但对茶饮强品牌（星巴克/瑞幸）可能更敏感 |

### 1.3 YAML 竞品类型

| model_id | competition.type | zero_competitor_policy 核心 | score_caps |
|----------|-----------------|---------------------------|------------|
| snack_fast_food | 排斥型 | 近场 200m 无同类可作线索，必须结合需求侧+远场判断 | far_field_many=70, weak_demand=60 |
| food_service | 半聚集型 | 0竞品≠蓝海，需看停车/餐饮生态/品质支撑 | 无 |
| beverage_dessert | 半聚集型 | 0竞品≠蓝海，需看步行流/外卖平台/强品牌 | 无 |

**问题**：food_service 和 beverage_dessert 的 YAML score_caps 为空，与 snack_fast_food 差异显著。正餐/茶饮的半聚集型语义（同类聚集是正面信号）在代码中未落地。

### 1.4 同品牌/强品牌覆盖

- `_detect_same_brand_risk` 仅在品牌名 >=4 字时触发，宽松匹配
- 茶饮强品牌场景（瑞幸/星巴克/喜茶等）近场无同类但平台强品牌全覆盖时，现有逻辑不区分
- 小吃快餐同品牌风险在当前样本中未覆盖

---

## 2. 现有样本覆盖矩阵

### 2.1 snack_fast_food（6 样本）

| 样本 | dc_200 | dc_500 | dc_1000 | rest_1k | 覆盖场景 | 缺口 |
|------|--------|--------|---------|---------|---------|------|
| 01 | 0 | 3 | 12 | 56 | 近场0+远场多 ✅ | — |
| 02_highrisk | 0 | 2 | 15 | 50 | 远场极多+弱需求 ✅ | — |
| 03_weakdemand | 0 | 0 | 2 | 8 | 近场0+远场少+弱需求 ✅ | — |
| 04 | 0 | 4 | 14 | 55 | 学校强+远场多 ✅ | — |
| 05 | 1 | 3 | 6 | 12 | 有竞品+学校强 ✅ | — |
| 06_university | 0 | 2 | 4 | 8 | 全大学不触发 ✅ | — |

### 2.2 food_service（5 样本）

| 样本 | dc_200 | dc_500 | dc_1000 | 覆盖场景 | 缺口 |
|------|--------|--------|---------|---------|------|
| 01 | 3 | 5 | 8 | 有竞品 | — |
| 02 | 2 | 6 | 10 | 竞品密集+停车排烟 | — |
| 03_semiagg | 0 | 3 | 7 | 近场0+远场存在 | 缺 0竞品+停车弱 |
| 04 | 1 | 4 | 8 | 停车排烟消防不足 | — |
| 05 | 2 | 5 | 10 | 办公热闹+晚市弱 | — |

### 2.3 beverage_dessert（6 样本）

| 样本 | dc_200 | dc_500 | dc_1000 | 覆盖场景 | 缺口 |
|------|--------|--------|---------|---------|------|
| 01 | 1 | 3 | 6 | 有竞品 | — |
| 02 | 1 | 4 | 8 | 办公强+外卖 | — |
| 03_semiagg | 0 | 0 | 1 | 近场0+远场少 | 缺 0竞品+强品牌平台覆盖 |
| 04 | 0 | 0 | 1 | 缺年轻客群 | — |
| 05 | 0 | 1 | 3 | 品牌提示 | — |
| 06_schoolflow | 0 | 0 | 1 | school 高+步行动线 | — |

---

## 3. 缺口分析

### G1：food_service snapshot competitor_note 为空
- **位置**：`_snapshot_food_service` L519-534
- **风险**：正餐 0竞品时，LLM 可能从"competitor_note 为空"推断"竞争不激烈"
- **影响**：YAML 定义了半聚集型 zero_competitor_policy 但未落地到 snapshot

### G2：beverage_dessert snapshot competitor_note 为空
- **位置**：`_snapshot_beverage_dessert` L538-560
- **风险**：茶饮 0竞品时，没有"外卖平台强品牌覆盖"提示
- **影响**：与 G1 同类，YAML 语义未落地

### G3：food_service/beverage 0竞品时 advantages 走默认"竞争压力较小"
- **位置**：`fallback_report_service.py` L150-152
- **风险**：半聚集型 0竞品不应该直接写"竞争压力较小"
- **已有样本**：beverage_dessert_03/04/05/06 的 expected_absent 均已排除"市场空白明显"，但默认 advantages 仍可能输出"竞争压力较小"

### G4：正餐/茶饮 competition_score 无品类差异化封顶
- **位置**：`_competition_score` L342-346
- **风险**：正餐 0竞品时分数偏高，与半聚集型语义矛盾
- **对比**：小吃快餐有 `dc_200==0 and dc_1000>=8 → min(base, 70)`

### G5：同品牌/强品牌覆盖缺样本
- **位置**：`_detect_same_brand_risk` L520-578
- **风险**：茶饮品牌（瑞幸/星巴克）近场无同类但平台强品牌全覆盖，现有样本全部 `hot_brands=[]`，未测试同品牌风险路径

### G6：替代消费（substitute）高但直接竞品少的场景未覆盖
- **位置**：`fallback_report_service.py` L130-131
- **风险**：小吃快餐 `sub_200>0 or sub_500>0` 走"替代消费较多需核验"分支，但现有样本 substitute 全部为 0，该分支未被测试

---

## 4. Phase 4M-B 最小实现建议

### P0：food_service / beverage_dessert snapshot 竞品化

| 文件 | 改动 | 理由 |
|------|------|------|
| `business_model_service.py` `_snapshot_food_service` | 读取 dc_200/dc_500/dc_1000/restaurants_1k，生成 competitor_note（参考 snack_fast_food 模板，但用半聚集型语义：0竞品不写空白，写"正餐半聚集型需看停车/餐饮生态/品质支撑"） | G1 |
| `business_model_service.py` `_snapshot_beverage_dessert` | 同理，生成 competitor_note（0竞品写"茶饮半聚集型需核验步行动线/外卖平台强品牌覆盖"） | G2 |

### P1：正餐/茶饮 0竞品时 advantages 不走默认"竞争压力较小"

| 文件 | 改动 | 理由 |
|------|------|------|
| `fallback_report_service.py` advantages L150-152 | food_service/beverage_dessert 在 dc_200==0+dc_500==0 时输出"近场无直接竞品记录，但正餐/茶饮为半聚集型，0竞品不简单等于竞争压力低" | G3 |
| `fallback_report_service.py` `_competition_score` | food_service/beverage 0竞品时封顶（如 0竞品+restaurants_1k<20 → cap=65） | G4 |

### P2：补齐样本覆盖

| 样本 | 场景 | expected_absent |
|------|------|----------------|
| food_service_06_zero_comp | 正餐 0竞品+停车弱 | "竞争压力较小""市场空白明显" |
| beverage_dessert_07_strongbrand | 茶饮 0竞品+hot_brands 含强品牌 | "竞争压力较小" |
| snack_fast_food_07_substitute | 小吃 0竞品+替代消费多 | —（验证替代消费分支触发） |

### 对应 business_model_rules 测试（建议 +4）

| 测试 ID | 内容 |
|---------|------|
| T38 | food_service 0竞品 → snapshot competitor_note 非空，含"半聚集型"或"停车"或"餐饮生态" |
| T39 | beverage_dessert 0竞品 → snapshot competitor_note 非空，含"步行动线"或"外卖平台"或"强品牌" |
| T40 | food_service 0竞品 → advantages 不含"竞争压力较小" |
| T41 | 小吃快餐 sub_500>0 → advantages 含"替代消费较多" |

### 始终禁止项

- ❌ report_fact_guard.py / poi_name_guard.py
- ❌ HTML / 小程序 / 支付 / 候选池 / 多点对比 / PDF / 长图
- ❌ prompt 主体
- ❌ YAML schema 结构 / source card / manifest
- ❌ location_profile_service.py

---

## 5. 审计结论摘要

1. **snack_fast_food 竞品逻辑最完善**：四档 competitor_note + 排斥型 score caps + YAML far_field 封顶 + 6 样本覆盖多场景。
2. **food_service / beverage_dessert 竞品逻辑缺失**：snapshot competitor_note 为空；YAML 半聚集型语义未落地到代码；0竞品时 advantages 走默认"竞争压力较小"。
3. **6 个缺口**：G1/G2（snapshot 竞品化）、G3/G4（正餐/茶饮 0竞品语义）、G5（同品牌/强品牌样本）、G6（替代消费分支样本）。
4. **最小修复路径**：P0 snapshot 竞品化（2 函数）→ P1 advantages/competition_score 差异化（2 处）→ P2 补齐 3 样本 + 4 测试。

---

*审计完成于 2026-06-16。Phase 4M-B 待实施。*
