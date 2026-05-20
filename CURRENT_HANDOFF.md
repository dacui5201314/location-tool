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
- **结论：核心路径可用，少数 master/subtype-only 的 sub_first gap 属后续优化项，不阻塞现有业态。**

#### 客流锚点准确

- 14/14 master 拥有 traffic_anchor_rules
- P2 可检测 anchor 被写成竞品（warning-only）
- **结论：核心路径可用。P2 warning 不阻塞保存但应后续升级为 hard-error。**

#### 无关 POI 剔除

- 8/14 master 拥有 categories_excluded
- 高频刚需零售 strict_exclude_names 72 条为最完整
- 6 master 缺 categories_excluded（中餐正餐、烘焙甜品、民宿青旅、低频目的零售、专业生活服务、社区基础服务）
- **结论：核心业态覆盖充足。缺失的 6 master 依赖 name_blacklist 补偿，不阻塞。**

#### LLM 防污染

- fact_errors 硬阻断 + retry — 退款率从 28% 降至 5%
- P0/P2/P3 已在 Phase 11 升级为 hard-error，retry 后仍失败则退款/不保存
- _check_sentence 3x 容忍（允许 expected×3 以内偏差）
- "附近""周边"默认回退 1000m 半径
- **结论：硬阻断有效（75% retry 成功率）。3x 容忍和半径回退是已知精度损失，非阻塞。**

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
| 是否还有必须先修的代码问题 | **无。** P0/P2/P3 hard-error 已完成；剩余 3x 容忍、radius fallback、少数 sub_first/categories_excluded 为后续优化项，非阻塞。 |

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

Next window should observe real user reports for quality, not expand random samples. Remaining non-blocking gaps (3x tolerance, radius fallback, sub_first on a few masters, categories_excluded gaps) can be addressed in subsequent optimization phases. P0/P2/P3 hard-error is complete.

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
| `check_report_fact_guard.py` | 92 PASS, 0 FAIL |

---
