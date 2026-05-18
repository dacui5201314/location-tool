# New Window Prompt - 2026-05-18

Project path: `C:\Users\admin\location-tool`

Read first:
1. `PROJECT_RULES.md`
2. `PROJECT_PROGRESS.yml`
3. `CURRENT_HANDOFF.md`

## Current Status

Phase 7D: mainline ready for product acceptance. 19 real reports, retry fallback validated, boundary disclaimer verified. Not pushed.

## Baseline

| Test | Result |
|---|---|
| `compileall backend` | PASS |
| `check_industry_rigor_rules.py` | 1902 PASS, 0 FAIL |
| `check_report_fact_guard.py` | 92 PASS, 0 FAIL |
| `KNOWN_RULE_GAPS` | (none) |

Key commits: `660e5b2` (code), `548c4a1` (docs). Not pushed.

## First Steps

1. `git status --short`
2. `python -m compileall backend && python backend/tests/check_industry_rigor_rules.py && python backend/tests/check_report_fact_guard.py`
3. Audit latest doc commits
4. If all pass: wait for product owner decision on push / deploy / next direction. Do NOT run more real reports without user authorization. Do NOT push. Do NOT process tmp_* artifacts.
