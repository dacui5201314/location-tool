# New Window Prompt - 2026-05-19

Project path: `C:\Users\admin\location-tool`

Read first:
1. `PROJECT_RULES.md`
2. `PROJECT_PROGRESS.yml`
3. `CURRENT_HANDOFF.md`

Do not read long historical docs unless needed.

## Current Status

Phase 8C complete. The report-accuracy mainline has:
- high-risk direct classification guarded by `require_name_keyword_for_code` and Section AB invariants
- fact guard hard-errors plus one free retry fallback
- verified report boundary disclaimer in real output
- Sample Bank improved to 12 complete_candidate / 10 partial
- subtype substitute boundaries added and regression-tested for Pet/Fitness/Laundry

Current baseline:
- `python -m compileall backend`: PASS
- `python backend/tests/check_industry_rigor_rules.py`: 1961 PASS, 0 FAIL
- `python backend/tests/check_report_fact_guard.py`: 92 PASS, 0 FAIL
- `KNOWN_RULE_GAPS`: none

Latest code commit to audit:
- `1b5d313` - `test: cover subtype substitute real-chain boundaries`

Not pushed.

Expected `git status --short`: only untracked temp artifacts:
- `tmp_latest_report_text.txt`
- `tmp_report_images/`
- `tmp_report_pages/`

## First Steps

1. Run `git status --short`.
2. Audit the latest commits, especially:
   - `1031400` subtype substitute engine support
   - `8b3ff12` Laundry repair boundary fix
   - `1b5d313` subtype substitute boundary regression tests
3. Re-run:
   - `python -m compileall backend`
   - `python backend/tests/check_industry_rigor_rules.py`
   - `python backend/tests/check_report_fact_guard.py`
4. If all pass, proceed to Phase 9.

## Phase 9 Recommendation

Targeted real report expansion to 30-40 total samples. Do not run random samples. Focus on:
- newly changed subtype substitute areas: Pet, Fitness, Laundry
- low-coverage areas: Low Frequency Retail, Community Services, Night Economy, Hotels
- retry/fact_errors monitoring

Do not continue forcing Sample Bank completion. Remaining partial groups should stay partial unless nationally stable substitute samples exist.

## Hard Boundaries

- Do not push.
- Do not modify frontend / UI / PDF.
- Do not modify database schema.
- Do not process `tmp_*` artifacts.
- Do not relax `report_fact_guard.py`.
- Do not weaken `require_name_keyword_for_code`, `substitute_before_direct`, `strict_exclude_names`, or `exclude_names`.
