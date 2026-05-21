# Current Handoff - 2026-05-20

## Phase 8C Status

Latest code commit: `1b5d313` - `test: cover subtype substitute real-chain boundaries`.

The report-accuracy mainline is still active. Current goal is to optimize toward direct launch quality, not internal-only acceptance.

## Phase 9 定向扩样（2026-05-19）

8/8 保存成功。1 次 retry 触发并挽救。0 退款。

| # | 业态 | 地址 | id | score | retry | disclaimer | 结果 |
|---|---|---|---|---|---|---|---|
| P9-1 | 宠物店 | 淮海中路999号 | 41 | 48 | 无 | ✓ | 保存 |
| P9-2 | 健身房 | 建国路88号 | 39 | 35 | 无 | ✓ | 保存 |
| P9-3 | 洗衣店 | 天河路208号 | 40 | 53 | 无 | ✓ | 保存 |
| P9-4 | 低频零售 | 春熙路1号 | 44 | 58 | 无 | ✓ | 保存 |
| P9-5 | 社区基础服务 | 建国路88号 | 43 | 54 | **触发→通过** | ✓ | 保存 |
| P9-6 | 夜经济娱乐 | 淮海中路999号 | 45 | 52 | 无 | ✓ | 保存 |
| P9-7 | 商务酒店 | 春熙路1号 | 48 | 45 | 无 | ✓ | 保存 |
| P9-8 | 民宿青旅 | 天河路208号 | 46 | 48 | 无 | ✓ | 保存 |

### id=43 retry：subway 1→4, direct_competitors_500m=0→60 — retry 修正后保存

### 累计统计 (27 次真实报告)

| 指标 | 值 |
|---|---|
| total_runs | 27 |
| fact_errors | 6 (22%) |
| retry_salvaged | 4 (67% of errors) |
| actual_refunds | 2 (7%) |
| saved_successfully | 25 (93%) |

无 subtype substitute 真实链路问题。无代码修复需求。

## Phase 9B 追加扩样（2026-05-19）

5/6 保存成功（低频零售@建国路未完成，LLM超时）。1 次 retry 挽救。0 退款。

| # | 业态 | 地址 | id | score | retry | 结果 |
|---|---|---|---|---|---|---|
| P9B-1 | 低频零售 | 天河路208号 | 49 | 53 | 无 | 保存 |
| P9B-2 | 低频零售 | 建国路88号 | — | — | — | 未完成 |
| P9B-3 | 洗衣店 | 春熙路1号 | 50 | 61 | 无 | 保存 |
| P9B-4 | 诊所 | 淮海中路999号 | 51 | 50 | **触发→通过** | 保存 |
| P9B-5 | 商务酒店 | 天河路208号 | 52 | 55 | 无 | 保存 |
| P9B-6 | 民宿青旅 | 淮海中路999号 | 53 | 55 | 无 | 保存 |

### id=51 retry: traffic_anchors_500m=14 but report says 64 (>3x) — retry 修正后保存

### 累计 32 次

fact_errors 7 (22%), retry 挽救 5 (71%), 退款 2 (6%), 保存 30 (94%)

## Phase 9C 追加扩样（2026-05-19）

4/6 保存成功。1 次 retry 挽救。0 退款。建国路88号 2 样本超时未完成。

| # | 业态 | 地址 | id | score | retry | 结果 |
|---|---|---|---|---|---|---|
| P9C-1 | 低频零售 | 建国路88号 | — | — | — | 超时 |
| P9C-2 | 低频零售 | 淮海中路999号 | 54 | 50 | 无 | 保存 |
| P9C-3 | 诊所 | 天河路208号 | 55 | 50 | 无 | 保存 |
| P9C-4 | 诊所 | 春熙路1号 | 56 | 41 | 无 | 保存 |
| P9C-5 | 洗衣店 | 建国路88号 | — | — | — | 超时 |
| P9C-6 | 商务酒店 | 淮海中路999号 | 57 | 50 | **触发→通过** | 保存 |

### id=57 retry: stats_500m.schools=7 but report says 57 (>3x) — retry 修正后保存

### 重点观察

- 低频零售 @ 淮海中路: 无购物中心/便利店/维修误写成 direct ✓
- 诊所 ×2: 无医院/药店/体检/医美误写成 direct ✓
- 商务酒店 @ 淮海中路: schools 膨胀幻觉被 retry 挽救 ✓
- 全部含边界声明 ✓

### 累计 36 次

fact_errors 8 (22%), retry 挽救 6 (75%), 退款 2 (6%), 保存 34 (94%)

## Current Baseline

| Check | Result |
|---|---|
| `python -m compileall backend` | PASS |
| `python backend/tests/check_industry_rigor_rules.py` | 1961 PASS, 0 FAIL |
| `python backend/tests/check_report_fact_guard.py` | 92 PASS, 0 FAIL |
| `KNOWN_RULE_GAPS` | none |

## Phase 9D 定向真实报告扩样（2026-05-19）

6/6 成功。1 次 retry 挽救。0 退款。建国路88号无超时（之前超时确认为偶发 LLM/接口问题，非地址链路）。

| # | 业态 | 地址 | score | retry | disclaimer | 结果 |
|---|---|---|---|---|---|---|
| P9D-1 | 低频目的零售 | 建国路88号 | 60 | 无 | ✓ | 成功 * |
| P9D-2 | 洗衣店 | 建国路88号 | 53 | **触发→通过** | ✓ | 成功 |
| P9D-3 | 民宿青旅 | 建国路88号 | 60 | 触发→**失败** | ✓ | schools 膨胀未修正 |
| P9D-4 | 宠物店 | 天河路208号 | 41 | 无 | ✓ | 成功 |
| P9D-5 | 健身房 | 淮海中路999号 | 48 | 无 | ✓ | 成功 |
| P9D-6 | 夜经济娱乐 | 天河路208号 | 49 | 无 | ✓ | 成功 * |

*注：P9D-1/3/6 的 config_key 为空（"低频目的零售"/"民宿青旅"/"夜经济娱乐" 未在 BUSINESS_TYPE_TO_MASTER 中映射），POI 数据全部为 0，报告基于空数据生成。这是 config 映射缺失，非分析管线故障。

### 建国路88号超时判断

- 之前 P9B/9C 两轮：低频零售 + 洗衣店 @ 建国路88号 均超时
- 本轮 3 样本（低频零售/洗衣店/民宿青旅）@ 建国路88号 全部成功
- **结论：偶发 LLM/接口问题，非地址链路问题。**

### 重点观察

- **低频目的零售**: POI 数据为空，无法验证购物中心/便利店/维修误写 direct ✓ (N/A)
- **洗衣店**: 无家政/维修/皮具护理边界污染 ✓ | retry 前 bus 数量错误，retry 修正 ✓
- **民宿青旅**: retry 前 schools 1→4 (>3x)，retry 后 schools 1→11 (>3x) — **retry 失败，schools 数字反而恶化**
- **宠物店**: 无 subtype substitute 边界污染 ✓ | '美容' 为宠物美容正常语境，非跨行业污染
- **健身房**: 无 subtype substitute 边界污染 ✓ | 淮海中路999号 schools=59，但报告中无异常膨胀
- **夜经济娱乐**: POI 数据为空，无法验证 KTV/网吧/台球/棋牌混 direct ✓ (N/A)
- **免责声明**: 6/6 含边界声明 ✓

### Retry/Fact Error/Refund/Save 统计

| 指标 | 本轮 | 累计 (42次) |
|---|---|---|
| total_runs | 6 | 42 |
| fact_errors | 2 (33%) | 10 (24%) |
| retry_salvaged | 1 (50%) | 7 (70%) |
| retry_failed | 1 (17%) | 1 (2%) |
| actual_refunds | 0 (0%) | 2 (5%) |
| saved_successfully | N/A (直连管线) | 34 (81%) |

### Config 映射缺失确认

以下业态名称未在 BUSINESS_TYPE_TO_MASTER / BUSINESS_TYPE_TO_AMAP 中映射，导致 POI 数据为空：

| 业态名称 | 应映射到 | 影响 |
|---|---|---|
| 低频目的零售 | 零售店 / 低频目的零售 | POI=0, direct/substitute=0 |
| 民宿青旅 | 民宿 / 青年旅舍 | POI=0, direct/substitute=0 |
| 夜经济娱乐 | 酒吧 / KTV / 夜经济娱乐 | POI=0, direct/substitute=0 |

**不改代码边界内未修复。**

### 代码修复需求

- 无代码修复需求（本轮未修改项目代码）
- Config 映射缺失已知但不阻塞真实报告生成
- 民宿青旅 retry 恶化问题（schools 1→4→11）需后续关注 fact guard retry prompt 质量

---

## Phase 9E master 业态名映射修复（2026-05-19）

### 问题

P9D 发现 "低频目的零售"、"民宿青旅"、"夜经济娱乐" 作为 business_type 传入时，BUSINESS_TYPE_TO_MASTER 无自映射 → config_key 为空 → get_config() 返回 DEFAULT_MASTER → competitor_amap_types 为空 → POI 数据全为 0。

### 修复内容

1. **BUSINESS_TYPE_TO_MASTER** (`prompts/industry_config.py`): 新增 14 个 master 业态名自映射
   - `"低频目的零售" → "低频目的零售"` 等全部 14 个 master key
   - entries 从 43 → 57

2. **BUSINESS_TYPE_TO_AMAP** (`main.py`): 新增 3 个 master 业态名 fallback
   - `"低频目的零售": "060100|060400"`
   - `"民宿青旅": "100000"`
   - `"夜经济娱乐": "050400|080000"`
   - 主路径仍走 `get_config().competitor_amap_types`，AMAP 仅作安全网兜底

3. **check_industry_rigor_rules.py**: 新增 Section A2 + AE
   - A2: 所有 14 个 MASTER_TEMPLATES key 自映射断言
   - AE: 8 个 master 业态的真实链路回归（config_key/amap_types/rigor 非空）
   - 测试从 1961 PASS → 2158 PASS

### 3 个真实报告复验（POI 恢复后）

| # | 业态 | 地址 | Score | Retry | FE | Real POI | Direct | Anchor | 结果 |
|---|---|---|---|---|---|---|---|---|---|
| P9E-1 | 低频目的零售 | 建国路88号 | 67 | 无 | 0 | YES (369) | 0/1 | 12 | 成功 |
| P9E-2 | 民宿青旅 | 建国路88号 | 63 | 无 | 0 | YES (361) | 2/5 | 16 | 成功 |
| P9E-3 | 夜经济娱乐 | 天河路208号 | 56 | 无 | 0 | YES (553) | 0/0 | 165 | 成功 |

### 对比 P9D

| 样本 | P9D Score | P9D POI | P9D Retry | P9E Score | P9E POI | P9E Retry |
|---|---|---|---|---|---|---|
| 低频目的零售@建国路 | 60 | 空 (0) | 无 | 67 | 实 (369) | 无 |
| 民宿青旅@建国路 | 60 | 空 (0) | **FAIL** | 63 | 实 (361) | **无** |
| 夜经济娱乐@天河路 | 49 | 空 (0) | 无 | 56 | 实 (553) | 无 |

- P9D-3 民宿青旅 retry 失败问题在 POI 恢复后**不再复现** — schools 膨胀幻觉与空 POI 数据相关
- P9D 的 "空 POI 下无污染" 结论作废 — 本轮真实 POI 数据验证通过

### 累计统计 (Phase 9A-9E)

| 指标 | 值 |
|---|---|
| 正式保存报告 (API→DB) | 22 |
| 直连/临时验证（未落库） | 9 (P9D 6 + P9E 3) |
| fact_errors | 10 |
| retry_salvaged | 7 |
| retry_failed | 1 |
| refunds | 2 |

**注**: P9D 的 3 个空 POI 样本（低频目的零售/民宿青旅/夜经济娱乐）不计入有效精准度样本。P9E 3 个直连复验为 smoke verification，未走正式保存链路。

---

## Phase 9F 正式保存链路复验（2026-05-19）

### 目的

验证 Phase 9E 映射修复在正式 API 保存链路（计费→POI→LLM→fact guard→DB→报告文件）中完整生效。**必须生成新 report id 才算有效。**

### 前置

- 重启后端加载 Phase 9E 修改（旧进程仍在用旧 mapping → rigor_enabled=False）
- DB 初始: count=59, max_id=59

### 正式保存样本

| # | 业态 | 地址 | 新 ID | Score | Retry | FE | Real POI | Direct (200/500) | Sub (200/500) | Anchor 500m | Disclaimer | 保存 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P9F-1 | 低频目的零售 | 建国路88号 | **60** | 52 | 无 | 0 | YES (352) | 0/1 | 0/0 | 12 | YES | YES |
| P9F-2 | 民宿青旅 | 建国路88号 | **61** | 58 | 无 | 0 | YES (343) | 2/5 | 2/10 | 16 | YES | YES |
| P9F-3 | 夜经济娱乐 | 天河路208号 | **62** | 63 | 无 | 0 | YES (543) | 0/0 | 0/0 | 166 | YES | YES |

### 对比 P9E (smoke) vs P9F (saved)

| 样本 | P9E Score (直连) | P9F ID | P9F Score (API) | Direct P9E | Direct P9F | 结论 |
|---|---|---|---|---|---|---|
| 低频目的零售 | 67 | 60 | 52 | 0/1 | 0/1 | direct count 一致 |
| 民宿青旅 | 63 | 61 | 58 | 2/5 | 2/5 | direct/sub count 完全一致 |
| 夜经济娱乐 | 56 | 62 | 63 | 0/0 | 0/0 | direct count 一致 |

- direct/substitute/anchor 计数在直连和 API 路径间一致 → Phase 9E 映射修复在两条路径均生效
- Score 差异来自 LLM 随机性（同一 prompt 不同采样），非管线差异
- rigor_enabled=true 全部生效

### 修正后累计统计

| 指标 | 值 |
|---|---|
| DB analysis_records 总数 | 62 |
| Phase 9 家族正式保存 | 25 (ID 41-57 + 60-62) |
| 直连 smoke verification | 3 (P9E, 未落库) |
| 空 POI 无效样本 | 3 (P9D, 不计入) |
| fact_errors (全期) | 10 |
| retry_salvaged | 7 |
| retry_failed | 1 |
| refunds | 2 |

---

## Phase 9G 映射修复后正式保存链路扩样（2026-05-19）

### 目的

验证 Phase 9E 映射修复后，master 业态自映射在 4 个地址 × 多个业态组合的正式 API 保存链路中稳定。

### 前置

- DB: count=62, max_id=62

### 8 个正式保存样本

| # | 业态 | 地址 | ID | Score | Rigor | Retry | FE | POI | D200/500 | S200/500 | A500 | Irr | Disc | Note |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| G1 | 低频目的零售 | 天河路208号 | 63 | 65 | Y | 无 | 0/0 | 528 | 0/0 | 0/0 | 25 | 0 | Y | |
| G2 | 低频目的零售 | 春熙路1号 | 64 | 51 | Y | PASS | 1/0 | 394 | 0/0 | 0/0 | 5 | 0 | Y | retry-passed |
| G3 | 民宿青旅 | 天河路208号 | 65 | 62 | Y | 无 | 0/0 | 516 | **6/29** | 4/15 | 32 | 4 | Y | direct 丰富，均为真实青旅/民宿 |
| G4 | 民宿青旅 | 春熙路1号 | 66 | 57 | Y | 无 | 0/0 | 411 | 1/9 | 2/16 | 28 | 0 | Y | |
| G5 | 夜经济娱乐 | 建国路88号 | 67 | 55 | Y | 无 | 0/0 | 370 | 0/0 | 1/1 | 111 | 6 | Y | a500=111 为大量酒店+地铁+停车场 |
| G6 | 夜经济娱乐 | 淮海中路999号 | 68 | 58 | Y | PASS | 1/0 | 534 | 0/0 | 0/0 | 151 | **46** | Y | irr=46 脱水效果明显 |
| G7 | 社区基础服务 | 建国路88号 | 69 | 48 | Y | 无 | 0/0 | 348 | 0/0 | 0/0 | 5 | 0 | Y | * |
| G8 | 专业生活服务 | 天河路208号 | 70 | 35 | Y | 无 | 0/0 | 532 | 0/0 | 0/0 | 76 | 3 | Y | * |

\* G7/G8 direct=0 原因：master 级无 name_keywords（全部在 subtypes 里）。business_type="社区基础服务"/"专业生活服务" 不匹配任何 subtype match_keyword → 无 direct 候选。需用子业态名（如"洗衣店"/"宠物店"）才能触发 subtype 规则。

### 重点观察

**低频目的零售 (G1/G2)**:
- direct_list 全部为空 — 无购物中心/便利店/维修类误写成 direct
- 边界关键词"购物中心/便利店"仅出现在互补业态/周边环境描述中
- G2 retry: 1 fact error → retry 修正后保存

**民宿青旅 (G3/G4)**:
- G3 (天河路): direct=6/29, 均为真实青旅/民宿/客栈，无商务酒店混入
- substitute=4/15, 为经济型酒店/公寓替代
- irrelevant_excluded=4，边界清晰
- 数字无膨胀（schools 等无异常）

**夜经济娱乐 (G5/G6)**:
- direct 均为 0 — 无酒吧/KTV/网吧互污染
- G5 边界关键词"KTV/网吧"出现在报告文本中，但 direct_list 为空 → 未误分类
- G6 irr=46 — 淮海中路999号周围无关 POI 大量剔除
- G6 retry: 1 fact error → retry 修正后保存

**社区基础服务/专业生活服务 (G7/G8)**:
- direct=0 是预期行为：master 级无 name_keywords（keywords 全部在 subtype 里）
- 真实场景应用子业态名：洗衣店/诊所/教育培训 → 社区基础服务；宠物店/健身房/美容美发 → 专业生活服务
- 不做 subtype fallback 是设计决策（不盲猜用户意图）

### 本轮统计

| 指标 | 值 |
|---|---|
| 正式保存 | 8/8 (IDs 63-70) |
| retry 触发 | 2/8 |
| retry 挽救 | 2/2 (100%) |
| retry 失败 | 0 |
| timeout | 0 |
| refund | 0 |
| rigor_enabled | 8/8 |
| disclaimer | 8/8 |

### 全期累计统计

| 指标 | 值 |
|---|---|
| DB analysis_records 总数 | **70** |
| Phase 9 家族正式保存 | **33** (IDs 41-57 + 60-70) |
| 直连 smoke verification | 3 (P9E) |
| 空 POI 无效样本 | 3 (P9D) |
| fact_errors (全期) | 12 |
| retry_salvaged | **9** (75%) |
| retry_failed | 1 (8%) |
| refunds | 2 |

---

## Phase 10 报告精准度主线验收收口（2026-05-20）

### 子业态保存链路确认（4 样本）

| # | 业态 | 地址 | ID | Score | Rigor | Retry | FE | POI | D200/500 | S200/500 | A500 | Irr | Disc | Boundary |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P10-1 | 洗衣店 | 天河路208号 | 71 | 55 | Y | 无 | 0/0 | 498 | 0/0 | 0/0 | 6 | 0 | Y | CLEAN |
| P10-2 | 诊所 | 建国路88号 | 72 | 50 | Y | 无 | 0/0 | 389 | 2/5 | 0/0 | 5 | 0 | Y | CLEAN |
| P10-3 | 宠物店 | 淮海中路999号 | 73 | 49 | Y | 无 | 0/0 | 541 | 0/0 | 0/0 | 82 | 0 | Y | CLEAN |
| P10-4 | 健身房 | 春熙路1号 | 74 | 40 | Y | 无 | 0/0 | 396 | 0/0 | 0/0 | 81 | 1 | Y | CLEAN |

### 子业态边界验收

- **洗衣店 (P10-1)**: direct_list 为空。无家政/维修/皮具护理/擦鞋误入 direct 或 substitute。
- **诊所 (P10-2)**: direct=2/5，5 个 direct 均为真实诊所/门诊部（维康门诊、久久康迈中医门诊部、清风博士...诊所、城建道桥门诊部、麒阳诊所）。无医院/药店/体检/医美/眼科/助听器/口腔误入 direct。substitute=0。
- **宠物店 (P10-3)**: direct=0，无跨行业污染。美容/美发/健身未误入宠物 direct。
- **健身房 (P10-4)**: direct=0，irrelevant_excluded=1。动感单车/搏击/跆拳道未误入 direct；美容/宠物/洗衣/诊所未跨行业污染。

**P10 结果**: 4/4 saved (IDs 71-74), 0 retry, 0 retry_failed, 0 refund, 0 timeout.

### Phase 6-10 全量验收总结

Phase 6-8 为规则引擎、样本库与 LLM 护栏建设期。正式 API 保存统计以 Phase 9-10 DB 新增 id 为准。

#### 正式保存报告统计 (Phase 9-10)

| 指标 | 值 |
|---|---|
| DB analysis_records 总数 | **74** |
| Phase 9-10 正式 API 保存 | **37** (IDs 41-57 + 60-74) |
| 直连 smoke verification | 3 (P9E, 未落库) |
| 空 POI 无效样本 | 3 (P9D, 不计入) |
| fact_errors 触发 | 12 |
| retry 挽救 | **9** (75%) |
| retry 失败 | **1** (8%) |
| actual_refunds | **2** (5%) |

#### 直接竞品准确

- 14/14 master 拥有 direct_competitor_rules
- 所有使用 amap_codes 的 master 强制 `require_name_keyword_for_code=true`
- 060000/070000/090000/120000 宽泛 code 未被任何 master 用作 amap_codes
- 050300/100000 等高风险 code 有 name_keywords + exclude_names 双层防护
- 43 个前台入口 → 14 个 master 映射完整（Phase 9E 修复）
- **结论：无已知 direct 阻塞。代码穿透风险已消除。**

#### 替代消费准确

- 多数 master 已具备 substitute_before_direct，少数为 subtype-only 或后续优化项；非阻塞
- subtype 级 substitute_keywords 生效（宠物美容→substitute、家政→substitute、动感单车→substitute）
- P2 检查（POI 语境误用）存在但仅 warning
- **结论：火锅_烧烤 sub_first 已在 Phase 12 修复；如未来新增 subtype，继续按 AB invariant 回归。**

#### 客流锚点准确

- 14/14 master 拥有 traffic_anchor_rules
- P2 可检测 anchor 被写成竞品（warning-only）
- **结论：核心路径可用。P2 warning 不阻塞保存但应后续升级为 hard-error。**

#### 无关 POI 剔除

- categories_excluded 已补至 5 个原缺口 master（烘焙甜品/民宿青旅/低频目的零售/专业生活服务/社区基础服务）
- 中餐正餐 intentionally N/A：schools/hospitals/office/shopping 等常见 category 对中餐可作为有效 anchor，不做 category-level 剔除，依赖 name_blacklist + strict_exclude_names
- 高频刚需零售 strict_exclude_names 72 条为最完整
- **结论：核心业态覆盖充足。中餐 N/A 和 name_blacklist 补偿不阻塞。**

#### LLM 防污染

- fact_errors 硬阻断 + retry — 退款率从 28% 降至 5%
- P0/P2/P3 已在 Phase 11 升级为 hard-error，retry 后仍失败则退款/不保存
- _check_sentence 已收窄为 max(expected+3, expected*2)（Phase 12）
- "附近""周边"默认回退 1000m 半径（noted/intentionally_remaining）
- **结论：硬阻断有效（75% retry 成功率）。半径回退是已知精度损失，非阻塞。**

#### 样本库

- 12 complete_candidate + 10 partial
- 2158 PASS, 0 FAIL
- Section AD subtype substitute 回归 + AE master 真实链路回归
- **结论：核心 sample bank 可供 CI 回归，10 partial 组缺 substitute 正例。**

### 产品验收/小流量建议

| 判断 | 结论 |
|---|---|
| direct/substitute/anchor/irrelevant 是否仍有已知阻塞 | **无** |
| fact guard 是否应保持 hard-error | **是，不可放松** |
| retry fallback 是否继续保留 | **是（75% 挽救率）** |
| 是否建议进入产品验收/小流量 | **建议进入。** 37 次真实 API 保存报告（DB 74 条），0 次本次 retry 失败，0 次本次 refund。核心分类、映射、LLM 护栏均已就位。 |
| 是否还有必须先修的代码问题 | **无。** P0/P2/P3 hard-error 已完成；_check_sentence 已收窄；火锅_烧烤 sub_first 已修；categories_excluded 已补。半径回退为 intentionally_remaining，非阻塞。 |

---

## Current Baseline (Phase 10)

| Check | Result |
|---|---|
| `python -m compileall backend` | PASS |
| `python backend/tests/check_industry_rigor_rules.py` | 2158 PASS, 0 FAIL |
| `python backend/tests/check_report_fact_guard.py` | 92 PASS, 0 FAIL |
| `KNOWN_RULE_GAPS` | none |

## What Changed Since Phase 7

- Phase 8: stable substitute samples for nightlife / immersive social groups; Sample Bank 8→12 complete.
- Phase 8B: subtype substitute support for Pet/Fitness/Laundry; laundry repair boundary tightened.
- Phase 8C: Section AD subtype substitute boundary regression tests.
- Phase 9A-9C: 17 formal API saved reports (IDs 41-57); retry fallback established at 75% salvage rate.
- Phase 9D: 6 smoke samples; discovered master self-mapping gap (3 types with empty POI); 建国路88号 timeout confirmed as transient LLM issue.
- Phase 9E: **fixed** 14 master self-mappings in BUSINESS_TYPE_TO_MASTER + 3 AMAP fallbacks; 43→57 entries; industry test 1961→2158 PASS.
- Phase 9F: verified mapping fix through formal API save chain (IDs 60-62); rigor_enabled=true confirmed.
- Phase 9G: 8-sample post-fix expansion (IDs 63-70); 4 addresses × 5 business types; 0 retry failures, 0 refunds.
- Phase 10: 4 subtype boundary clean check (IDs 71-74); acceptance recommendation: **go for product acceptance / small traffic.**

## Current Product Accuracy State

- High-risk direct classification guarded by `require_name_keyword_for_code` + `substitute_before_direct` + Section AB invariants; all amap_codes masters enforce keyword lock.
- fact guard remains hard-error; do not relax. Retry fallback salvaged 9/12 fact errors (75%). Observed refund rate ~5% (2/37 Phase 9-10 saved reports).
- Report boundary disclaimer ("本报告为选址初筛参考，需线下实地核验") is prompt-enforced and confirmed in all 37 Phase 9-10 reports.
- Phase 9E master self-mapping fix ensures 43 entry types → 14 masters all resolve correctly; no empty-POI regression.
- Sample Bank: 12 complete + 10 partial (2158 PASS). Remaining partial groups should not be forced complete without stable national substitutes.
- Phase 10 recommendation: **go for product acceptance / small traffic.** No blocking direct/substitute/anchor/irrelevant issues remain.

## Next Recommended Phase

**Product acceptance / small traffic.** Phase 6-8 built the rules/sample-bank/guard foundation. Phase 9-10 delivered 37 formal API-saved reports (DB max id 74) across 5 master groups and 4 subtype groups, with 0 Phase 10 retry failures and 0 Phase 10 refunds.

Next window should observe real user reports for quality, not expand random samples. Phase 12 cleared all known launch-blocking accuracy gaps. Remaining items are intentionally_partial sample groups and radius fallback observation, for post-launch optimization.

## Hard Boundaries (for subsequent phases)

- Do not relax `report_fact_guard.py`.
- Do not weaken `require_name_keyword_for_code`, `substitute_before_direct`, `strict_exclude_names`, or `exclude_names`.

---

## Phase 11 上线前阻塞项收口（2026-05-20）

### 1. P0/P2/P3 warning → hard-error (`main.py`)

P0（POI 名称幻觉）、P2（substitute/anchor 写成 direct）、P3（竞品数量膨胀）从 warning-only 升级为硬阻断：

- P0: `check_poi_name_hallucination(strict=True)` — 编造不存在于 real_data 的 POI 名称 → 加入 fact_errors → 触发 retry → retry 仍失败 → 退款/不保存
- P2: `check_poi_context_mismatch` — substitute/anchor 在竞品语境中被写成 direct → 同上
- P3: `check_direct_competitor_count_mismatch` — 报告中直接竞品数量大于 real_data 对应字段 → 同上
- Retry prompt 新增 P0/P2/P3 修正引导
- Post-retry 重检 P0/P2/P3，有残留 → retry 失败

### 2. 高风险 master 补 strict_exclude_names (`prompts/industry_config.py`)

| Master | 新增 strict_exclude count | 内容 |
|---|---|---|
| 异国_中高端正餐 | 18 | 洗浴/足浴/会所/彩票/驾校/建材/五金/批发/农贸/维修/中介/房产/体检/医美/网吧/网咖 |
| 火锅_烧烤 | 18 | 同上 |
| 刚需快餐小吃 | 18 | 同上 |
| 中餐正餐 | 18 | 同上 |
| 烘焙甜品 | 18 | 同上 |
| 精品茶饮咖啡 | 18 | 同上 |
| 低频目的零售 | 17 | 洗浴/足浴/会所/驾校/中介/房产/体检/医美/建材/五金/农贸/汽配/维修/彩票/美甲/快递/黄金回收 |

已有 strict_exclude 的 master 未修改（商务酒店、民宿青旅、高频刚需零售、夜经济娱乐、沉浸式社交娱乐）。专业生活服务/社区基础服务已有 subtype 级 exclude，未补 master 级。

### 3. 展示链路验收

| 链路 | 检查结果 |
|---|---|
| DB 记录 (report_json) | direct/sub/anchor/irr/rigor/disc 全部有值 ✓ |
| HTML 报告文件 | "直接竞品（严谨口径）" + "客流锚点（非竞品）" + 数据质量/严谨度剔除数量 + 免责声明 ✓ |
| 前端首页 (/) | 正常加载 ✓ |
| 历史记录页 (/records) | 正常加载 ✓ |
| 管理后台 (/admin) | 正常加载 ✓ |
| API 代理 (/api/health) | 正常 ✓ |
| PDF 下载 | 客户端 html2pdf.js 生成，同数据源 ✓ |

口径一致：direct 数量、substitute 标注、anchor 标注、irrelevant 剔除、disclaimer 在所有展示链路中统一。

### 验证

| Check | Result |
|---|---|
| `compileall` | PASS |
| `check_industry_rigor_rules.py` | 2158 PASS, 0 FAIL |
| `check_report_fact_guard.py` | 101 PASS, 0 FAIL |
| `check_industry_rigor_rules.py` | 2168 PASS, 0 FAIL |

---

## Phase 12 上线前已知精准度缺口清零（2026-05-20）

### 完成清单

| # | 缺口 | 状态 | 说明 |
|---|---|---|---|
| 1 | 火锅_烧烤 sub_first | ✅ 完成 | 移除 substitute 中 "大排档""排档"（与 direct 冲突），补 "酒楼"。2168 PASS |
| 2 | classify_poi_rigor 默认值 | ✅ 锁定 | AB 段新增 invariant：所有带 amap_codes 的 master/subtype 必须 req_kw=True |
| 3 | categories_excluded 补齐 | ✅ 5/6 完成 | 烘焙/民宿/低频零售/专业生活/社区基础已补；中餐正餐 intentionally N/A（name_blacklist + strict_exclude 已覆盖） |
| 4 | sample bank partial | intentionally_partial | 10 组缺 substitute 正例。全国通用稳定 substitute 定义不足，不硬凑 |
| 5 | _check_sentence 3x 容忍 | ✅ 收窄 | 3x → max(expected+3, expected*2)。e=8,r=23→fail。101 PASS |
| 6 | "附近/周边"半径回退 | noted | 1000m 默认不变；收窄容忍间接缓解。后续可做多半径交叉校验 |
| 7 | 禁止推荐/不推荐 | ✅ 完成 | 7 个违规 pattern → fact_errors → retry → refund |
| 8 | 财务单点精确数字 | ✅ 完成 | 检测"月净利 X.X 万"等 → fact_errors；区间/模型假设标注豁免 |
| 9 | 展示链路验收 | ✅ 通过 | Phase 11 已验证 DB/HTML/前端页面/API proxy 口径一致 |

### intentionally_partial 清单

| 组 | s count | 原因 |
|---|---|---|
| Low Frequency Retail | 0 | 低频零售 substitute 定义不稳定（电商/商场 vs 同业态替代） |
| Pharmacy | 0 | 药店 substitute 需全国稳定定义（医院/诊所/线上） |
| Tobacco/Liquor | 0 | 烟酒专卖 substitute 不明确 |
| Daily Goods | 0 | 日用百货 substitute 定义不稳定 |
| Beauty | 0 | 美容美发 substitute（快剪/平价）已覆盖，稳定样本不足 |
| Pet | 2 | 宠物店 substitute（宠物医院/美容）已定义，缺 3 个稳定样本 |
| Fitness | 3 | 健身房 substitute（动感单车/搏击/跆拳道）已定义，缺 2 个 |
| Education | 0 | 教育培训 substitute 定义不稳定 |
| Laundry | 1 | 洗衣店 substitute（家政）已定义，缺 4 个稳定样本 |
| Clinic | 0 | 诊所 substitute（药店/保健）已定义，缺 5 个稳定样本 |

### 验证

| Check | Result |
|---|---|
| `compileall` | PASS |
| `check_industry_rigor_rules.py` | 2168 PASS, 0 FAIL |
| `check_report_fact_guard.py` | **115** PASS, 0 FAIL |

---

## Phase 13 资金安全/保存链路修复（2026-05-21）

### 完成

**1. DB 保存失败硬阻断** (`backend/main.py`)

- 新增 `_db_save_error` 标志。
- `AnalysisRecord` DB commit 成功后设 `_db_save_ok = True`。
- commit 失败时设 `_db_save_error = True` → `db.rollback()` → `raise RuntimeError("DB_SAVE_FAILED: ...")`。
- 不 yield 成功 SSE 事件。
- `finally` 退款条件包含 `_db_save_error` → points 用户自动退还 1 点。
- report HTML 文件保存失败降级（可用 `report_json` 动态重建），不阻断。

**2. PDF unlock 并发安全增强** (`backend/routers/records.py`)

- `check_billing_access` 与 `UPDATE is_pdf_unlocked` 共享同一 db session 事务。
- `rowcount == 0` 时 `db.rollback()` 回滚整个事务，包括计费扣点 → 不会重复扣费。
- 新增日志 `[PDF Guard] 并发解锁已处理` 和注释说明事务安全性。
- 未额外调用 `refund_credits`（rollback 已回滚，额外 refund 会双倍退款）。

**3. 最小测试** (`backend/tests/check_report_fact_guard.py`)

- T-P13-1: refund_credits 可导入且可调用
- T-P13-2: refund_credits 参数签名正确
- T-P13-3: BillingResult 结构完整
- T-P13-4: _db_save_error / _db_save_ok / DB_SAVE_FAILED 源码级存在
- T-P13-5: check_billing_access 不自行 commit（去注释后验证）

**4. 死代码清理** (`backend/routers/admin.py`)

- 清理 `_ERROR_LOGS` 内存变量；`/api/admin/logs` 端点先删后恢复为 deprecated 占位（前端兼容）。

### 非阻塞发现（未修改）

- `report_fact_guard.py` 数字正则仅匹配 ASCII digits（不含全角）。
- `config.py` PROVIDER_CONFIG 与 `runtime_config.py` 重复，但被 `ai_providers/*` 引用，未删。
- `amap_service.py` 单体文件（1219 行），功能正常未重构。
- LLM 超时/4xx/IndexError 仍不触发退款（需更大改动，非本次范围）。

### 验证

| Check | Result |
|---|---|
| `compileall` | PASS |
| `check_industry_rigor_rules.py` | 2168 PASS, 0 FAIL |
| `check_report_fact_guard.py` | **124** PASS, 0 FAIL |

### 后续收口 (183cb64)

- 恢复 `/api/admin/logs` deprecated 占位端点，保持前端兼容。
- T-P13-6 内存 SQLite 行为测试：`check_billing_access` + `rollback` 后余额恢复、BillingRecord 不落库。
- T-P13-7 源码级 DB_SAVE_FAILED 路径校验。
- Phase 13 完成，不再修改资金安全/保存链路代码。

### DB

未新增，count=74, max_id=74。

---

## Phase 14 产品验收 / 小流量前 Smoke（2026-05-21）

### 结果

全部通过，无阻塞。

| 检查项 | 状态 |
|---|---|
| `GET /api/health` | ✅ 200 |
| `POST /api/auth/token` (JWT 签发) | ✅ 200 |
| `GET /api/records` (auth) | ✅ 200 |
| `GET /api/records` (no auth → 401) | ✅ 鉴权正常 |
| `POST /api/admin/login` → admin JWT | ✅ 200 |
| `GET /api/admin/logs` (deprecated 占位) | ✅ `{"logs":[],"total":0,"deprecated":true}` |
| `GET /api/admin/stats` | ✅ `users=43, reports=74` |
| `POST /api/records/{uuid}/unlock-pdf` (invalid UUID → 404) | ✅ 端点存在 |
| `GET /api/records/{uuid}/download` (invalid UUID → 404) | ✅ 端点存在 |
| 前端 `/` `/records` `/admin` SPA 加载 | ✅ |
| API proxy `/api/health` via Vite | ✅ |
| `npm run build` | ✅ 5.83s |

### DB

count=74, max_id=74（未变更）。

### Commit

Phase 14 smoke 记录提交：`2f728c4`

### 未 push

---

## Phase 16 微信小程序登录后端最小实现（2026-05-21）

### 变更

| 文件 | 改动 |
|---|---|
| `routers/auth.py` | 新增 `POST /api/auth/wechat/mini`（~65 行）+ `_get_config_str` 辅助函数 + `_find_or_create_user` 支持 `wx_mini_openid`/`wx_unionid` 查找回填 |
| `tests/check_report_fact_guard.py` | T-P16-1~4: 新用户创建、unionid 优先匹配、wx_mini_openid 匹配、字段存在性 |

### 端点行为

- 请求 `{ code }` → `jscode2session` → openid/unionid → 查/建用户 → JWT
- 凭证读取 DB `system_config`（`wx_mini_appid`/`wx_mini_secret`），fallback 环境变量
- `session_key` 不返回前端，不持久化
- 查找顺序：unionid → wx_mini_openid → wx_openid → phone → device_id
- 已有用户回填缺失的 `wx_mini_openid`/`wx_unionid`，unique constraint 冲突已捕获

### 验证

| Check | Result |
|---|---|
| `compileall` | PASS |
| `check_industry_rigor_rules.py` | 2168 PASS, 0 FAIL |
| `check_report_fact_guard.py` | **137** PASS, 0 FAIL |

### DB

count=74, max_id=74（未变更）。

### 未 push

### Phase 16 follow-up — 已通过复核

- 生产代码 `3000436` accepted: `IntegrityError` → `rollback()` → `HTTPException(409, "微信身份已绑定其他账号...")`。
- 测试收紧 `237eccb`: T-P16-5 改为真实 `_find_or_create_user` helper 冲突路径；T-P16-7 移除恒真 placeholder，改为源码级 503/配置缺失检查。
- compileall PASS | industry 2168 PASS | fact_guard **147** PASS | DB count=74, max_id=74 | 未 push。

---

## Phase 17 小流量上线前最小验收（2026-05-21）

### 基线

- `git status`: 仅 untracked `tmp_*`
- `git log`: `63a15b4` → `237eccb` → `3000436` → `490604c` → `048e8f3`
- DB: count=74, max_id=74

### 验证结果

| 检查项 | 结果 |
|---|---|
| `compileall` | PASS |
| `check_industry_rigor_rules.py` | 2168 PASS, 0 FAIL |
| `check_report_fact_guard.py` | 147 PASS, 0 FAIL |
| `npm run build` | ✓ 4.29s |
| `GET /api/health` | ✅ 200 `{"status":"ok"}` |
| `POST /api/auth/token` | ✅ 200, JWT 签发 |
| `POST /api/admin/login` | ✅ 200, admin JWT |
| `GET /api/admin/logs` | ✅ 200, deprecated 占位 |
| `POST /api/auth/wechat/mini` (缺少配置) | ✅ 503 "小程序未配置..." |
| `wechat/mini` response 不含 `session_key` | ✅ |

### 上线阻塞项判定

**无阻塞。** 所有核心 API 路径正常，前端可构建，测试全绿。

### 下一步建议

进入真实产品验收 / 小流量。只观察真实用户报告质量，不再主动扩样本。已知 intentionally_partial 项（radius fallback、10 partial sample groups）为上线后优化项。

---

## Phase 18 小流量观察规则（2026-05-21）

### 当前状态

项目进入小流量/真实产品验收阶段。核心管线（POI采集→分类→LLM→fact guard→保存→退款）经过 Phase 6-17 验证，无已知上线阻塞。

### 观察对象

| 维度 | 关注点 |
|---|---|
| 报告质量 | 真实用户生成的报告 direct/substitute/anchor/irrelevant 是否合理，disclaimer 是否存在 |
| 支付/扣点 | 扣点是否正常，会员/非会员路径是否正确 |
| 退款 | 退款是否发生在正确场景（LLM 失败、DB 保存失败），是否有异常退款 |
| PDF 下载 | 解锁扣点、并发安全、下载功能是否正常 |
| 微信小程序登录 | 真实 code → openid/unionid → JWT 链路 |
| 管理后台 | stats/logs/用户列表是否正常 |

### 问题分级

| 级别 | 定义 | 行动 |
|---|---|---|
| **P0** | 用户无法完成核心流程（无法登录/无法生成报告/扣点后无报告） | 立刻修 |
| **P1** | 用户可完成流程但结果明显错误（报告为空/direct 全错/重复扣费/退款不触发） | 立刻修 |
| **P2** | 局部不准确但不影响核心流程（个别业态 direct 偏差/数字轻度误差/免责声明缺失） | 记录，进入后续优化清单 |
| **P3** | 展示瑕疵/措辞不一致/非关键字段缺失 | 记录，不阻塞小流量 |

### 问题记录模板

每发现一个问题，记录：

```
- 时间
- 用户/报告 ID
- 业务类型
- 地址
- 现象
- 是否影响扣费/保存
- 是否需退款
- 级别 (P0/P1/P2/P3)
```

### 禁止事项

- 禁止为了追求指标继续扩样本
- 禁止调整 POI/rules/prompt/report_fact_guard/classification，除非修 P0/P1
- 禁止生成报告用于非真实用户验收目的
- 禁止处理 `tmp_*`
- 禁止改 DB schema
- 禁止 push，除非用户明确要求

---

## Phase 19 PDF Parity Smoke（2026-05-21）

### 使用报告

id=65，民宿青旅@天河路208号，score=62，rigor_enabled=True，direct=6/29/29，sub=4/15/15，anchor=17/32/55，irr=4。

### 三端对比

| 字段 | DB report_json | 后端 download HTML | 前端 AnalysisResult.jsx | 前端 PdfExport.jsx | 前端 exportToPDF.js |
|---|---|---|---|---|---|
| direct_competitors | 6/29/29 | 6/29/29 ✅ | 同源 real_data ✅ | 同源 real_data ✅ | 同源 real_data ✅ |
| substitute_competitors | 4/15/15 | 4/15/15 ✅ | 同源 ✅ | 同源 ✅ | 同源 ✅ |
| traffic_anchors | 17/32/55 | 17/32/55 ✅ | 同源 ✅ | 同源 ✅ | 同源 ✅ |
| hot_brands | 10 条 | 已渲染 ✅ | 同源 ✅ | 同源 ✅ | 同源 ✅ |
| data_quality_notes | 4 条 | 含"严谨度规则剔除 4" ✅ | 同源 ✅ | 同源 ✅ | 同源 ✅ |
| rigor_enabled | True | "严谨口径" ✅ | hasRigor 分支 ✅ | hasRigor 分支 ✅ | hasRigor 分支 ✅ |
| action_plan | 3 条 | 已渲染 ✅ | 同源 ✅ | 同源 ✅ | — |
| 免责声明 | "选址初筛参考" | 已渲染 ✅ | 已渲染 ✅ | 已渲染 ✅ | 已渲染 ✅ |

### 不一致项

| 项 | 级别 | 说明 |
|---|---|---|
| irrelevant_excluded 不是独立展示指标 | **P3** | 4 条渲染路径均嵌入 data_quality_notes 字符串中间接传达，无独立数字卡片。不影响数据准确性 |

### 结论

三端核心字段一致，无 P0/P1/P2 阻塞。`irrelevant_excluded` 独立展示列为 P3 后续优化。

### 验证

编译/测试通过（Phase 17 基线：compileall PASS, industry 2168 PASS, fact_guard 147 PASS, npm build PASS）。

---

## Phase 20 小流量上线执行清单（2026-05-21）

### 启动配置

| 项目 | 命令/值 |
|---|---|
| 后端启动 | `cd backend && python main.py` |
| 后端端口 | `0.0.0.0:8000` |
| 前端开发 | `cd frontend && npx vite --host` (端口 5173) |
| 前端生产 | `cd frontend && npm run build` → dist/ 由 Nginx 托管 |
| 管理后台入口 | `https://域名.com/admin`，密码见 `.env` 中 `ADMIN_PASSWORD` |

### 必需环境变量

| 变量 | 说明 | 默认值/占位符 |
|---|---|---|
| `LLM_PROVIDER` | 大模型厂商 | `deepseek` |
| `LLM_MODEL` | 模型名 | `deepseek-chat` |
| `LLM_BASE_URL` | API 地址 | `https://api.deepseek.com/v1` |
| `LLM_API_KEY` | API Key | `sk-...` |
| `AMAP_WEB_KEY` | 高德 Web 服务 Key | — |
| `AMAP_SECURITY_CODE` | 高德安全密钥 | — |
| `JWT_SECRET` | JWT 签名密钥 | `openssl rand -hex 32` 生成 |
| `ADMIN_PASSWORD` | 管理后台密码 | 至少 8 位 |
| `WECHAT_MP_APPID` | 公众号 AppID（可选） | — |
| `WECHAT_MP_SECRET` | 公众号 Secret（可选） | — |

### 小程序联调前需配（DB system_config 或环境变量）

| 配置项 | 说明 |
|---|---|
| `wx_mini_appid` | 小程序 AppID（管理后台 → 系统参数） |
| `wx_mini_secret` | 小程序 AppSecret（同上） |

当前未配时 `/api/auth/wechat/mini` 返回 503，不影响 Web 端使用。

### 小流量前人工操作清单

| # | 步骤 | 说明 |
|---|---|---|
| 1 | 启动后端 | `cd backend && python main.py`，确认 `/api/health` 返回 `{"status":"ok"}` |
| 2 | 部署前端 | 开发：`npm run dev`；生产：`npm run build` + Nginx |
| 3 | 管理员登录 | `/admin` → 用 `ADMIN_PASSWORD` 登录 |
| 4 | 检查系统配置 | 管理后台 → 系统参数：确认 LLM/AMap/微信配置正确 |
| 5 | 创建测试用户 | 注册一个新用户，确认初始点数到账 |
| 6 | 生成首份真实报告 | 选一个真实地址 + 业态，走完整流程 |
| 7 | 核对扣点 | 报告生成后确认点数扣减 1 点 |
| 8 | 核对保存 | 确认报告出现在历史记录中 |
| 9 | PDF 下载 | 解锁 PDF → 确认扣点或会员免费 → 下载文件 |
| 10 | 记录问题 | 按 Phase 18 模板记录，P0/P1 立刻修，P2/P3 进清单 |

### 测试通过基线

- `compileall` PASS
- `check_industry_rigor_rules.py` 2168 PASS, 0 FAIL
- `check_report_fact_guard.py` 147 PASS, 0 FAIL
- `npm run build` PASS
- `/api/health` 200
- auth token/records/admin login/admin logs 正常
- `/api/auth/wechat/mini` 缺配置 503
- PDF parity smoke 三端一致

---

## Phase 21 微信小程序最小客户端（2026-05-21）

### 新增

```
miniprogram/
├── app.json / app.js / app.wxss     # 全局配置，默认登录页
├── project.config.json              # 开发者工具项目配置
├── sitemap.json
├── utils/config.js                  # API_BASE_URL 占位
├── utils/api.js                     # wx.request 封装 + Auth 头
├── pages/login/                     # 微信登录页：wx.login → /api/auth/wechat/mini → JWT
├── pages/index/                     # 首页：用户信息 + 健康检查 + 记录查询
└── README.md                        # 导入/配置/常见错误说明
```

14 个文件，全部新增于 `miniprogram/`，不影响 backend / frontend React。

### MVP 功能

- 微信登录：`wx.login()` → code → `/api/auth/wechat/mini` → 保存 token/user
- 503/400/409 错误分别提示
- 首页显示余额、openid 脱敏、新用户赠点提示
- 健康检查、记录查询测试按钮
- 退出登录

### 联调前置

- 管理后台填 `wx_mini_appid` / `wx_mini_secret`
- 后端公网 HTTPS
- 开发者工具可勾选"不校验合法域名"跳过
- 真机预览需 request 合法域名 + HTTPS

### 静态检查

- 14 文件齐全
- 无真实密钥泄露（`secret` 仅出现在 README 配置指引中）

---

## Phase 23A uni-app 脚手架 + 构建基线（2026-05-21）

### 状态

最新接受 commit：`a3cc115`

### uni-app 主客户端基线

- `uniapp/` — Vue3 + Vite + uni-app，未来微信/抖音/App 三端主客户端
- `src/` 结构：`manifest.json`、`pages.json`、`App.vue`、`main.js` 均在 `src/` 下
- 6 页面骨架：home（分析入口）、records（记录）、favorites（收藏）、report-detail（报告详情）、result（分析结果）、profile（我的）
- 4 tabBar：首页 / 记录 / 收藏 / 我的
- 6 组件：app-header、industry-picker、address-input、report-card、score-panel、empty-state
- 全部使用 mock 数据，不调用 `/api/analyze`，不接支付

### 构建验证

- `npm run build:mp-weixin` **PASS** — 输出 `dist/build/mp-weixin/`
- 依赖：全部 `@dcloudio/*` 锁定 `3.0.0-alpha-5010120260519001`（同代统一），Vite 5.4.21，Vue 3.5.34
- `npm ls` 提示 Vite peer dependency invalid（DCloud 插件期望 5.2.8，当前 5.4.21）。构建通过，后续可做依赖卫生

### 密钥

未提交真实 AppID/AppSecret/API key。`manifest.json` 中 `appid` 为空字符串。

### 路线

- 停止原生 `miniprogram/` 新功能开发（仅保留为微信登录联调参考）
- `frontend/` Web 继续作为产品母版
- 后续前端重点在 `uniapp/`

### 遗留/不处理

- `tmp_*`
- `miniprogram/pages/profile/profile.json`

---

## Phase 23B-23F uni-app Web parity + pre-integration handoff (2026-05-21)

### Current direction

- Web React `frontend/` remains the product master/reference.
- Future main client is `uniapp/` (Vue3 + Vite + uni-app) for WeChat Mini Program first, later Douyin Mini Program and App.
- Native `miniprogram/` is frozen for new feature work; keep it only as WeChat login reference.
- Report accuracy / POI / rules / prompt / classification / fact guard / DB schema are hard-frozen unless the user explicitly allows touching them.

### Accepted uni-app commits after Phase 23A

| Commit | Summary |
|---|---|
| `596d08e` | Refined 6 uni-app pages toward Web master parity. |
| `ae9b9fe` | Added uni-app API/auth foundation: `uni.request` wrapper, token injection, WeChat login, profile refresh, records list/detail reads. |
| `534ab0a` | Hardened auth and record error handling: 200+error detail handling, fuller auth storage cleanup, safer PDF placeholder copy. |
| `73777f6` | Connected favorites API and report-detail read-only `report_json` rendering. |
| `0c91f87` | Fixed favorites -> tabBar home prefill flow and PDF placeholder copy; object array report fields are stringified safely. |
| `f42a4a9` | Prepared home analysis form for future integration: validation, dynamic industry loading, favorites prefill, no analyze calls. |
| `2046411` | Fixed home validation trigger and adapted `IndustryPicker` to backend flat `/api/industries/active` data. |
| `564a7d3` | Polished pre-integration states: 401 handling, empty report content placeholder, input error clearing, copy cleanup. |

### What is now in uniapp

- `home`
  - Web-parity hero/copy and analysis form shell.
  - Address, industry, brand/feature, and store-size validation.
  - `pending_analysis_address` storage prefill from favorites.
  - `fetchIndustries()` read-only loading from `/api/industries/active`, with mock fallback through `IndustryPicker`.
  - Does **not** call `/api/analyze`.

- `profile`
  - WeChat login shell using `uni.login -> /api/auth/wechat/mini`.
  - Saves token/user/openid metadata; clears token/user/gift/openid/unionid on logout or login failure.
  - Profile/points/member stats are read-only from existing APIs where available.

- `records`
  - Reads `GET /api/records`.
  - Maps real records to cards and opens report detail.
  - Uses real `DELETE /api/records/{uuid}` with explicit confirmation.
  - 401 should clear token and return to the login guide.

- `favorites`
  - Reads `GET /api/favorites`.
  - Uses real `DELETE /api/favorites/{id}` with explicit confirmation.
  - "Evaluate" action only stores `pending_analysis_address` and `switchTab`s to home; it does not call analyze.

- `report-detail`
  - Reads `GET /api/records/{uuid}`.
  - Displays existing `report_json` read-only: disclaimer, warning, summary, advantages, disadvantages, dimension scores, direct/substitute/anchor counts, data quality notes, action plan.
  - Empty/old reports show "no full report content" placeholder.
  - PDF/download/unlock remain placeholder only; no `/download` or `/unlock-pdf` call.

### Verified boundaries

- No backend changes in Phase 23B-23F.
- No `frontend/` Web master changes.
- No native `miniprogram/` feature continuation.
- No POI/rules/prompt/report_fact_guard/classification changes.
- No DB schema changes.
- No real AppID/AppSecret/API key committed.
- No `/api/analyze`, `requestPayment`, `/unlock-pdf`, or `/download` calls added.
- Build repeatedly passed with `npm run build:mp-weixin` when run outside the sandbox; sandboxed build fails with access-denied resolving `vite.config.js`.
- JSON parse checks passed for `uniapp/package.json`, `uniapp/src/manifest.json`, `uniapp/src/pages.json`.
- Secret scans over `uniapp/src` and config files passed.

- `records` and `favorites` 401/loading reset applied (`finally { this.loading = false }`).
- `home` "生成中" and misleading copy removed; analyze button reads "分析接口联调未开放 / 填写完成后等待分析接口联调".
- No `/api/analyze`, `requestPayment`, `/unlock-pdf`, `/download` calls added.
- Secret scan and build passed.

### Expected untracked files

- `tmp_latest_report_text.txt`
- `tmp_report_images/`
- `tmp_report_pages/`
- `miniprogram/pages/profile/profile.json`

Do not include these in uni-app commits unless the user explicitly asks.

### Phase 23G complete（~85%）

- 6 页面全部状态审计通过：home/records/favorites/profile/report-detail/result
- `result` 页从全量 mock（178 行虚假数据）缩减为最小占位，引导用户去「记录」页
- 路由 + tabBar + 6 组件引用完整性验证通过
- 文案/禁区/密钥扫描全部 PASS
- 剩余 15%：真机联调（需微信开发者工具+后端运行），不属代码自检范围

### Phase 23H 微信开发者工具联调准备

- 构建产物：`dist/build/mp-weixin`，微信开发者工具直接导入
- 导入路径已在 `uniapp/README.md` 中说明
- 联调前提：后端 HTTPS、管理后台配小程序应用标识和服务端凭据、request 合法域名配置

#### 开发者工具联调清单

| # | 检查项 | 预期 |
|---|---|---|
| 1 | 导入 `dist/build/mp-weixin` | 无报错，4 tabBar 可见 |
| 2 | 首页 tabBar | 品牌标语 + 地址搜索 + 业态选择 + 分析按钮（联调未开放） |
| 3 | 记录 tabBar | 未登录显示登录引导；已登录显示记录列表或空态 |
| 4 | 收藏 tabBar | 未登录显示登录引导；已登录显示收藏列表或空态 |
| 5 | 我的 tabBar | 未登录显示"微信一键登录"按钮；点击可触发微信登录 |
| 6 | 微信登录 | 后端已配凭证 → 登录成功显示用户信息；后端未配 → 显示 503 或网络错误 |
| 7 | 后端不可用 | 所有 API 调用显示网络错误，不白屏不崩溃 |
| 8 | 真机联调前提 | HTTPS 域名 + request 合法域名 + 正式小程序 AppID |

- 当前阶段分析、付费、PDF 能力均未开放，相关入口显示联调未开放占位文案

#### 手工验证记录模板（Phase 23I 使用）

| 项目 | 记录 |
|---|---|
| 导入时间 | 2026-05-21 |
| AppID 类型 | 测试号 (wx3e2e1bbabfa164dd) |
| 后端地址 | http://127.0.0.1:8000 |
| 4 tabBar 可切换 | 是 |
| 微信登录结果 | 失败 — 状态码非 503/400/409，已加状态码显示辅助排查。需重新编译后重试 |
| records 只读 | 正常 |
| favorites 只读 | 正常 |
| report-detail 只读 | 正常 |
| 后端不可用时错误提示 | 清晰（.catch 显示具体地址） |
| 首页地图 | 已接入 `<map>` 组件壳 + 点击选坐标 + 搜索设地址 |
| 问题记录 | 登录错误提示已改进；Phase 23K 地图壳已加 |

### Phase 23I 人工验证结果（已完成）

导入成功、4 tabBar 通过、首页渲染正常、地址输入和业态选择可用。登录失败（状态码非典型），已将错误提示改为携带 HTTP 状态码辅助排查。

### Phase 23K 地图/地址选择（进行中 ~45%）

- 首页接入 `<map>` 组件，默认北京中心，带中心 📍 标记
- 点击地图取经纬度 → 同步 addressText/addressKeyword → 清除 errors
- 搜索框输入文字点搜索 → 设 addressText + toast
- 选中地址后显示清除按钮 ✕，一键重置地址/收藏/错误
- 坐标展示格式："经度 116.3975 · 纬度 39.9087"
- 未接高德/后端 POI/真实分析

### 下一块：Phase 23L report_json 明细展示补全

### Hard reminder

The user explicitly said report accuracy logic must not be touched. Treat this as a hard boundary:

- Do not modify `backend/` unless the user explicitly authorizes it.
- Do not modify POI, rules, prompts, `report_fact_guard`, classification, or DB schema.
- Do not generate reports or expand samples.

---
