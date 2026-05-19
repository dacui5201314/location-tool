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

## Current Baseline

| Check | Result |
|---|---|
| `python -m compileall backend` | PASS |
| `python backend/tests/check_industry_rigor_rules.py` | 1961 PASS, 0 FAIL |
| `python backend/tests/check_report_fact_guard.py` | 92 PASS, 0 FAIL |
| `KNOWN_RULE_GAPS` | none |

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
