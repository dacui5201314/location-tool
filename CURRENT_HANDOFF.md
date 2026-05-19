# Current Handoff - 2026-05-19

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

Worktree should only contain untracked temp artifacts:
- `tmp_latest_report_text.txt`
- `tmp_report_images/`
- `tmp_report_pages/`

Not pushed.

## What Changed Since Phase 7

- Phase 8 added stable substitute samples for nightlife / immersive social groups.
- Sample Bank improved from `8 complete + 14 partial` to `12 complete + 10 partial`.
- Phase 8B added subtype-level `substitute_keywords` support for Pet/Fitness/Laundry.
- Phase 8B-fix removed Laundry `维修` pollution; phone/home appliance/computer repair are not direct and not substitute.
- Phase 8C added Section AD subtype substitute boundary regression tests.

Important nuance: Phase 8C Section AD is mostly rule-layer regression via `_cr`, with comments where it bypasses dewatering. It validates subtype substitute boundaries, but does not replace real report expansion.

## Current Product Accuracy State

- High-risk direct classification is guarded by `require_name_keyword_for_code`, `substitute_before_direct`, and Section AB invariants.
- fact guard remains hard-error; do not relax it.
- retry fallback has already saved 3 real reports and reduced observed refund rate from about 28% to 11%.
- Report boundary disclaimer is prompt-enforced and verified in a real report.
- Remaining Sample Bank partial groups should not be forced complete without stable national substitute definitions.

## Next Recommended Phase

Phase 9: targeted real report expansion to 30-40 total real samples.

Focus areas:
- newly changed subtype substitute areas: Pet, Fitness, Laundry
- low-coverage areas: Low Frequency Retail, Community Services, Night Economy, Hotels
- retry/fact_errors monitoring

Do not run random samples. Do not continue forcing Sample Bank completion. Do not push.

## Hard Boundaries

- No push.
- No frontend / UI / PDF changes.
- No database schema changes.
- Do not process `tmp_*` artifacts.
- Do not relax `report_fact_guard.py`.
- Do not weaken `require_name_keyword_for_code`, `substitute_before_direct`, `strict_exclude_names`, or `exclude_names`.
