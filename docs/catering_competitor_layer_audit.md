# Phase 4M-A：小餐饮竞品分层审计

> 审计范围：snack_fast_food / food_service / beverage_dessert 三族的竞品口径
> 审计日期：2026-06-16
> 状态：P0 已实施（4M-B），G1/G2 已关；G3/G4/G5/G6 待 4M-C

## 1. 现有代码位置清单

### 1.1 business_model_service.py — 三族 snapshot 竞品逻辑

| 行号 | 函数 | 竞品逻辑 |
|------|------|---------|
| L461-514 | `_snapshot_snack_fast_food` | 四档 competitor_note：近场0+远场多 / 近场0+远场少 / 远场>=10 / 默认。引用 `dc_200/dc_500/dc_1000/restaurants_1k` |
| L531-566 | `_snapshot_food_service` | ✅ 已关闭（b95819eb）。四档 competitor_note，0竞品走半聚集型语义（停车/餐饮生态/品质支撑） |
| L569-618 | `_snapshot_beverage_dessert` | ✅ 已关闭（b95819eb）。四档 competitor_note，0竞品走半聚集型语义（步行动线/外卖平台/强品牌）+ hot_brands 感知 |

**G1/G2 已关**：food_service 和 beverage_dessert snapshot 均补 competitor_note，YAML 半聚集型 zero_competitor_policy 已落地到 snapshot 层。

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

### 2.2 food_service（6 样本）

| 样本 | dc_200 | dc_500 | dc_1000 | 覆盖场景 | 缺口 |
|------|--------|--------|---------|---------|------|
| 01 | 3 | 5 | 8 | 有竞品 | — |
| 02 | 2 | 6 | 10 | 竞品密集+停车排烟 | — |
| 03_semiagg | 0 | 3 | 7 | 近场0+远场存在 | — |
| 04 | 1 | 4 | 8 | 停车排烟消防不足 | — |
| 05 | 2 | 5 | 10 | 办公热闹+晚市弱 | — |
| 06_zero_comp | 0 | 0 | 0 | 0竞品+半聚集型语义 ✅ (4M-B) | — |

### 2.3 beverage_dessert（7 样本）

| 样本 | dc_200 | dc_500 | dc_1000 | 覆盖场景 | 缺口 |
|------|--------|--------|---------|---------|------|
| 01 | 1 | 3 | 6 | 有竞品 | — |
| 02 | 1 | 4 | 8 | 办公强+外卖 | — |
| 03_semiagg | 0 | 0 | 1 | 近场0+远场少 | 缺 0竞品+强品牌平台覆盖 |
| 04 | 0 | 0 | 1 | 缺年轻客群 | — |
| 05 | 0 | 1 | 3 | 品牌提示 | — |
| 06_schoolflow | 0 | 0 | 1 | school 高+步行动线 | — |
| 07_zero_comp | 0 | 0 | 0 | 0竞品+半聚集型语义 ✅ (4M-B) | —（hot_brands 为空，G5 强品牌场景仍待） |

---

## 3. 缺口分析

### G1：food_service snapshot competitor_note 为空 ✅ 已关（b95819eb）
- 四档 competitor_note 已落地：0竞品→半聚集型+停车+餐饮生态+品质支撑

### G2：beverage_dessert snapshot competitor_note 为空 ✅ 已关（b95819eb）
- 四档 competitor_note 已落地：0竞品→步行动线+外卖平台+半聚集型+hot_brands 感知

### G3：food_service/beverage 0竞品时 advantages 走默认"竞争压力较小" ⬜ 待 4M-C
- **位置**：`fallback_report_service.py` L150-152
- **风险**：半聚集型 0竞品不应该直接写"竞争压力较小"
- **已有样本**：beverage_dessert_03/04/05/06 的 expected_absent 均已排除"市场空白明显"，但默认 advantages 仍可能输出"竞争压力较小"
- **注意**：4M-B 新增的 food_service_06 / beverage_dessert_07 样本 expected_absent 含"竞争压力较小"，但这仅验证 snapshot competitor_note 不含该词，不代表 fallback advantages 路径的 G3 已关。G3 仍需在 4M-C 通过修改 `fallback_report_service.py` advantages 分支关闭。

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

## 4. 4M-B P0 已实施 / 4M-C 待实施

### P0：food_service / beverage_dessert snapshot 竞品化 ✅ 已实施（b95819eb）

| 文件 | 状态 | 改动 |
|------|------|------|
| `_snapshot_food_service` | ✅ 已实施 | 四档 competitor_note，0竞品→半聚集型+停车+餐饮生态+品质支撑 |
| `_snapshot_beverage_dessert` | ✅ 已实施 | 四档 competitor_note，0竞品→步行动线+外卖平台+半聚集型+hot_brands 感知 |

### P1：正餐/茶饮 0竞品时 advantages 不走默认"竞争压力较小" ⬜ 待 4M-C

| 文件 | 改动 | 理由 |
|------|------|------|
| `fallback_report_service.py` advantages L150-152 | food_service/beverage_dessert 在 dc_200==0+dc_500==0 时输出半聚集型语义 | G3 |
| `fallback_report_service.py` `_competition_score` | food_service/beverage 0竞品时封顶（如 0竞品+restaurants_1k<20 → cap=65） | G4 |

### P2：补齐样本覆盖 ⬜ 待 4M-C（部分已加）

| 样本 | 状态 | 场景 |
|------|------|------|
| food_service_06_zero_comp | ✅ 已加（4M-B） | 正餐 0竞品+半聚集型语义 |
| beverage_dessert_07_zero_comp | ✅ 已加（4M-B） | 茶饮 0竞品+半聚集型语义（hot_brands 为空，G5 强品牌场景仍待） |
| beverage_dessert_08_strongbrand | ⬜ 待 4M-C | 茶饮 0竞品+hot_brands 含强品牌（G5） |
| snack_fast_food_07_substitute | ⬜ 待 4M-C | 小吃 0竞品+替代消费多（G6） |

### 对应 business_model_rules 测试

| 测试 ID | 状态 | 内容 |
|---------|------|------|
| T38 | ✅ 已加（4M-B） | food_service 0竞品 → competitor_note 非空+半聚集/停车/餐饮生态 |
| T39 | ✅ 已加（4M-B） | beverage_dessert 0竞品 → competitor_note 非空+步行动线/外卖平台/半聚集 |
| T40 | ⬜ 待 4M-C | food_service 0竞品 → advantages 不含"竞争压力较小" |
| T41 | ⬜ 待 4M-C | 小吃快餐 sub_500>0 → advantages 含"替代消费较多" |

### 始终禁止项

- ❌ report_fact_guard.py / poi_name_guard.py
- ❌ HTML / 小程序 / 支付 / 候选池 / 多点对比 / PDF / 长图
- ❌ prompt 主体
- ❌ YAML schema 结构 / source card / manifest
- ❌ location_profile_service.py

---

## 5. 审计结论摘要

1. **snack_fast_food 竞品逻辑最完善**：四档 competitor_note + 排斥型 score caps + YAML far_field 封顶 + 6 样本。
2. **G1/G2 已关（4M-B）**：food_service / beverage_dessert snapshot competitor_note 已补，0竞品走半聚集型语义。
3. **G3/G4/G5/G6 待 4M-C**：fallback advantages 差异化（G3）、competition_score 封顶（G4）、强品牌样本（G5）、替代消费分支样本（G6）仍待。
4. **剩余路径**：P1 advantages/competition_score 差异化（2 处 fallback）→ P2 补齐 2 样本 + 2 测试（T40/T41）。

---

*审计 2026-06-16。4M-B P0 实施（b95819eb），4M-C 待实施。*
