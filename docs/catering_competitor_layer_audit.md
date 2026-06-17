# Phase 4M-A：小餐饮竞品分层审计

> 审计范围：snack_fast_food / food_service / beverage_dessert 三族的竞品口径
> 审计日期：2026-06-16
> 状态：全线关闭。4M-B（G1/G2）→ 4M-C（G3/G4/G5/G6）全部实施。6 缺口已关。

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

### G3：food_service/beverage 0竞品 advantages 走默认"竞争压力较小" ✅ 已关（4M-C）
- fallback advantages 新增 food_service/beverage 半聚集型分支，0竞品输出"需核验停车/餐饮生态"或"步行动线/外卖平台"

### G4：正餐/茶饮 competition_score 无品类差异化封顶 ✅ 已关（4M-C）
- `_competition_score` 新增 food_service/beverage 0竞品封顶：弱需求(pop<10)→cap 55，一般→cap 65

### G5：同品牌/强品牌覆盖缺样本 ✅ 已关（4M-C）
- beverage_dessert_08_strongbrand：hot_brands 含瑞幸/星巴克/霸王茶姬，0竞品+半聚集型语义

### G6：替代消费高但直接竞品少 ✅ 已关（4M-C）
- snack_fast_food_07_substitute：sub_200=2, sub_500=5，advantages 含"替代消费较多需核验分流"

---

## 4. 4M-B / 4M-C 全部实施

### P0：snapshot 竞品化 ✅ 4M-B

| 文件 | 改动 |
|------|------|
| `_snapshot_food_service` | 四档 competitor_note，0竞品→半聚集型+停车+餐饮生态+品质支撑 |
| `_snapshot_beverage_dessert` | 四档 competitor_note，0竞品→步行动线+外卖平台+半聚集型+hot_brands 感知 |

### P1：fallback advantages + score_caps ✅ 4M-C

| 文件 | 改动 |
|------|------|
| `fallback_report_service.py` advantages | food_service/beverage 0竞品→半聚集型提示，取代"直接竞争压力较小" |
| `fallback_report_service.py` `_competition_score` | food_service/beverage 0竞品封顶：弱需求 cap 55，一般 cap 65 |

### P2：样本补齐 ✅ 4M-B + 4M-C

| 样本 | 场景 |
|------|------|
| food_service_06_zero_comp | 正餐 0竞品+半聚集型语义 |
| beverage_dessert_07_zero_comp | 茶饮 0竞品+半聚集型语义 |
| beverage_dessert_08_strongbrand | 茶饮 0竞品+hot_brands 强品牌（G5） |
| snack_fast_food_07_substitute | 小吃 direct 少+substitute 高（G6） |

### 测试

| 测试 ID | 内容 |
|---------|------|
| T38 | food_service 0竞品 → competitor_note 非空+半聚集/停车/餐饮生态 |
| T39 | beverage_dessert 0竞品 → competitor_note 非空+步行动线/外卖平台/半聚集 |
| T40 | food/beverage 0竞品 → advantages 不含"直接竞争压力较小" |
| T41 | food/beverage 0竞品+弱需求 → competition_score 封顶 |
| T42 | 小吃快餐 sub_500>0 → advantages 含"替代消费" |

### 始终禁止项

- ❌ report_fact_guard.py / poi_name_guard.py
- ❌ HTML / 小程序 / 支付 / 候选池 / 多点对比 / PDF / 长图
- ❌ prompt 主体
- ❌ YAML schema 结构 / source card / manifest
- ❌ location_profile_service.py

---

## 5. 审计结论摘要

1. **6 缺口全部关闭**：G1/G2（4M-B snapshot 竞品化）、G3/G4（4M-C fallback 差异化）、G5/G6（4M-C 样本补齐）。
2. **三族竞品分层落地**：snack_fast_food 排斥型 + food_service 半聚集型 + beverage_dessert 半聚集型，各有四档 competitor_note + score caps + 样本覆盖。
3. **测试基线**：BM 46 + Sample 70 + fact_guard 188，全部 PASS。

---

*审计 2026-06-16。4M-B（b95819eb）→ 4M-C（本轮）全部实施。*
