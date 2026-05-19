# New Window Prompt - 2026-05-19

Project: `C:\Users\admin\location-tool`

Read first only:
1. `PROJECT_RULES.md`
2. `PROJECT_PROGRESS.yml`
3. `CURRENT_HANDOFF.md`

Do not read `PROJECT_STATE.md` / `WORKING_SET.md` unless the user explicitly asks.

## Current Status

Report accuracy mainline is nearly done. Do not keep expanding samples.

Latest important commits:
- `3484608` - `fix: map master business types to real POI config`
- `a365727` - `docs: record Phase 9G post-fix real regression`

Current baseline:
- `compileall`: PASS
- `check_industry_rigor_rules.py`: 2158 PASS, 0 FAIL
- `check_report_fact_guard.py`: 92 PASS, 0 FAIL
- DB `analysis_records`: count/max id = 70/70 after Phase 9G

Phase 9 key result:
- Master business type self-mapping was missing and caused empty POI for direct master names.
- Fixed in `BUSINESS_TYPE_TO_MASTER` (+14 self maps) and tests.
- Phase 9F/9G verified official API save path with real POI, `rigor_enabled=True`, DB ids 60-70.
- No known blocking direct/substitute/anchor/irrelevant issue remains.
- Remaining errors are mainly LLM numeric inflation; keep fact guard hard-error and retry fallback.

Expected `git status --short`: only:
- `tmp_latest_report_text.txt`
- `tmp_report_images/`
- `tmp_report_pages/`

## Next Step: Phase 10 Quick Wrapup

Run only 4 subtype saved-chain checks, then summarize acceptance. Do not run random or large expansion.

Samples:
1. 洗衣店 | 天河路208号
2. 诊所 | 建国路88号
3. 宠物店 | 淮海中路999号
4. 健身房 | 春熙路1号

Record: new id, score, retry, fact_errors pre/post, `rigor_enabled`, POI total, direct/substitute/anchor counts, irrelevant count, disclaimer, save/refund/timeout.

Then update `CURRENT_HANDOFF.md` with Phase 10 acceptance summary. Optionally update `PROJECT_PROGRESS.yml`.

Commit:
`docs: summarize Phase 10 accuracy acceptance`

## Hard Boundaries

- No push.
- Do not process `tmp_*`.
- Do not modify frontend / UI / PDF.
- Do not modify database schema.
- Do not relax `report_fact_guard.py`.
- Do not weaken `require_name_keyword_for_code`, `substitute_before_direct`, `strict_exclude_names`, or `exclude_names`.
- Do not continue forcing Sample Bank completion.
