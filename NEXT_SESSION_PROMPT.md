# New Window Prompt - 2026-05-18

Project path: `C:\Users\admin\location-tool`

Read first:

1. `PROJECT_RULES.md`
2. `PROJECT_PROGRESS.yml`
3. `CURRENT_HANDOFF.md`

Do not read long historical docs unless needed.

## Current State

- Latest code commit to audit: `7cbba83` - `test: audit remaining subtype coverage`
- Not pushed.
- Expected `git status --short`: only untracked temp artifacts:
  - `tmp_latest_report_text.txt`
  - `tmp_report_images/`
  - `tmp_report_pages/`
- Latest validation:
  - `python -m compileall backend`: PASS
  - `python backend/tests/check_industry_rigor_rules.py`: `1902 PASS, 0 FAIL`
  - `python backend/tests/check_report_fact_guard.py`: `86 PASS, 0 FAIL`
  - `KNOWN_RULE_GAPS`: `(none)`

## Operating Mode

- Claude Code may implement, self-test, `git add`, and `git commit` at the end of each phase.
- Codex audits the resulting commit afterward.
- Do not ask the user for per-file document updates or per-commit approval.
- Still forbidden:
  - `git push`
  - frontend / UI / PDF changes
  - database schema changes
  - processing `tmp_*` artifacts

## New Window First Step

1. Run `git status --short`.
2. Audit commit `7cbba83`:
   - `git show --stat --patch 7cbba83 -- backend/tests/check_industry_rigor_rules.py`
   - Confirm it is audit/test-only and does not weaken rules.
   - Confirm it does not introduce a fake PASS count or stale baseline.
3. Re-run:
   - `python -m compileall backend`
   - `python backend/tests/check_industry_rigor_rules.py`
   - `python backend/tests/check_report_fact_guard.py`
4. If audit passes, tell the user briefly and send Claude Code the Phase 5D prompt below.

## Phase 5D Claude Code Prompt

Send Claude Code this prompt after `7cbba83` audit passes:

```text
Enter Phase 5D: batch-strengthen substitute sample coverage for partial master groups. Complete implementation, run tests, and commit. Do not push.

Context:
- Latest code commit before this phase: 7cbba83 test: audit remaining subtype coverage.
- Current baseline: industry 1902 PASS, 0 FAIL; fact guard 86 PASS, 0 FAIL; KNOWN_RULE_GAPS none.
- Sample Bank still has partial groups, mostly because stable substitute samples are missing.
- Do not chase perfect completion by polluting direct/substitute boundaries.

Goal:
Improve Sample Bank breadth by adding stable substitute examples for a small batch of partial master groups where substitutes are nationally generalizable.

Preferred batch:
1. 高频刚需零售
2. 专业生活服务
3. 社区基础服务
4. 夜经济娱乐

Allowed files:
- backend/tests/check_industry_rigor_rules.py
- PROJECT_PROGRESS.yml
- CURRENT_HANDOFF.md only if a very short status note is useful

Forbidden files/areas:
- frontend / UI / PDF
- database schema
- backend/prompts/industry_config.py unless a new sample reveals a genuine rule bug
- backend/services/amap_service.py
- backend/services/poi_name_guard.py
- backend/report_fact_guard.py
- backend/prompts/location_analysis.py
- tmp_* artifacts
- git push

Requirements:
1. First inspect the existing Sample Bank Ledger and the four preferred master sections.
2. Add substitute samples only where they are stable and defensible nationally.
3. Keep direct boundaries strict:
   - substitute must not pass as direct.
   - anchor must not pass as direct.
   - irrelevant must stay irrelevant.
4. Do not add weak substitute examples just to make the ledger look complete.
5. If a preferred group has no stable substitute examples, document it as still partial rather than forcing samples.
6. If any sample fails because of a real classifier bug, make the smallest rule fix needed in industry_config.py, with focused tests. Otherwise do not change rules.
7. Keep this as one batch, not four tiny phases.

Validation:
- python -m compileall backend
- python backend/tests/check_industry_rigor_rules.py
- python backend/tests/check_report_fact_guard.py

Commit:
- git add exact files only
- git commit -m "test: strengthen partial sample bank substitutes"
- Do not push.

Report:
- commit sha
- files changed
- which groups received substitute samples
- which groups remain partial and why
- latest Sample Bank Ledger complete/partial counts
- validation results
- git status --short
- confirm no push
```
