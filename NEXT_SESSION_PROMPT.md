# New Window Prompt - 2026-05-18

Project path: `C:\Users\admin\location-tool`

Read first:
1. `PROJECT_RULES.md`
2. `PROJECT_PROGRESS.yml`
3. `CURRENT_HANDOFF.md`

## Current Status

Phase 6 retry fallback validated. 18 real reports, fact_errors rate 28% reduced to 11% refund rate by retry. Baseline: compileall PASS / industry 1902 PASS / fact guard 92 PASS.

## First Steps

1. `git status --short`
2. `python -m compileall backend && python backend/tests/check_industry_rigor_rules.py && python backend/tests/check_report_fact_guard.py`
3. Audit latest commit: `01ef4de`
4. If all pass: proceed to Phase 7 (spot-check saved report content quality). Do NOT run more real reports without user authorization.
5. Do NOT push. Do NOT process tmp_* artifacts.

## Baseline

| Test | Result |
|---|---|
| `compileall backend` | PASS |
| `check_industry_rigor_rules.py` | 1902 PASS, 0 FAIL |
| `check_report_fact_guard.py` | 92 PASS, 0 FAIL |
| `KNOWN_RULE_GAPS` | (none) |

Key commits: `01ef4de` (code), `422e824` (docs). Not pushed.

## Next Step

Proceed to Phase 7: spot-check saved report content quality. Do NOT run more real reports without user authorization. Do NOT push.
