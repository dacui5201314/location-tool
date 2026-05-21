# New Window Prompt - Phase 13

Project: `C:\Users\admin\location-tool`

Read first only:
1. `PROJECT_RULES.md`
2. `PROJECT_PROGRESS.yml`
3. `CURRENT_HANDOFF.md`

Do not read `PROJECT_STATE.md` / `WORKING_SET.md` unless explicitly needed.

## Current State

Report accuracy mainline is complete. Do not reopen POI/rules/sample expansion.

Latest relevant commits:
- `52cc749` - `feat: complete pre-launch accuracy hardening`
- `0871bac` - `docs: finalize Phase 12 launch readiness wording`
- `53813cd` - `docs: update README to v1.5.0 with Phase 10-12 changes`

Baseline:
- `python -m compileall backend`: PASS
- `python backend/tests/check_industry_rigor_rules.py`: 2168 PASS, 0 FAIL
- `python backend/tests/check_report_fact_guard.py`: 101 PASS, 0 FAIL
- DB `analysis_records`: count/max id = 74/74
- Expected `git status --short`: `M backend/main.py`, `M backend/routers/records.py`, and `M backend/tests/check_report_fact_guard.py` may be present from uncommitted partial Phase 13 attempts, plus `tmp_latest_report_text.txt`, `tmp_report_images/`, `tmp_report_pages/`

## Phase 13 Goal

Fix launch-blocking billing/save-chain risks:

1. `backend/main.py`: `AnalysisRecord` DB save failure is currently logged but can still return SSE success.
   - Must hard-fail, not yield success.
   - Must refund point users.
   - HTML file save failure can remain best-effort if the DB record is saved.
   - Note: if `backend/main.py` is dirty, it likely already contains a partial `_db_save_error` / `_db_save_ok` attempt; finish it rather than duplicating it.

2. `backend/routers/records.py`: PDF unlock can double-charge on concurrent requests.
   - If points were charged and conditional unlock `rowcount == 0`, refund before returning `already_unlocked`.
   - Member unlocks should not refund.
   - Note: if `records.py` is dirty, it likely attempts to rely on `db.rollback()` to undo `check_billing_access()` in the same transaction; verify with a focused test before committing.

Add minimal focused tests if feasible without broad refactor.
If `check_report_fact_guard.py` is dirty, it likely has source-level/import Phase 13 checks; decide whether to keep, strengthen, or replace them with focused behavioral tests.

## Boundaries

- No push.
- Do not process `tmp_*`.
- Do not modify POI/rules/prompt accuracy logic.
- Do not random sample or generate more real reports.
- Do not change DB schema unless impossible to avoid.
- Do not relax fact guard or classification boundaries.

Commit suggestion:
`fix: harden billing refund and report save failure paths`
