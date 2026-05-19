# Current Handoff - 2026-05-19

## Phase 8C Status

Latest code commit: `1b5d313` - `test: cover subtype substitute real-chain boundaries`.

The report-accuracy mainline is still active. Current goal is to optimize toward direct launch quality, not internal-only acceptance.

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
