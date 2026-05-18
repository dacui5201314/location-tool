# Current Handoff - 2026-05-18

## Current State

- Latest code commit to audit: `7cbba83` - `test: audit remaining subtype coverage`
- Previous key commits:
  - `cea6414` - `test: strengthen restaurant sample bank`
  - `8db18da` - `prompt: avoid uncertain poi count ranges`
  - `837cbaa` - `prompt: tighten report numeric grounding`
  - `26198c0` - `docs: record C-3 real report validation`
  - `2384293` - `feat: extract report fact consistency guard`
- Not pushed.
- Worktree should only have untracked temp artifacts:
  - `tmp_latest_report_text.txt`
  - `tmp_report_images/`
  - `tmp_report_pages/`

## Validation Baseline

- `python -m compileall backend`: PASS
- `python backend/tests/check_industry_rigor_rules.py`: `1902 PASS, 0 FAIL`
- `python backend/tests/check_report_fact_guard.py`: `86 PASS, 0 FAIL`
- `KNOWN_RULE_GAPS`: `(none)`

## Completed Since Phase 4B

- Phase 4B-1: extracted `backend/report_fact_guard.py` as a lightweight fact guard module.
- Phase 4B-2: extended report fact guard coverage to `86 PASS, 0 FAIL`.
- C-3: real report validation for `精品茶饮咖啡` at `上海市徐汇区淮海中路999号`.
  - AMap and LLM succeeded.
  - Report was not saved because `fact_errors` correctly blocked: `stats_1000m.hospitals=14 but report says 57 (>3x)`.
  - Refund path triggered.
- Phase 4C-1: tightened prompt numeric grounding; POI counts must come from provided data and must not be expressed as uncertain ranges.
- Phase 5B: strengthened restaurant sample bank coverage.
- Phase 5C: Claude added an audit note for the 9 remaining non-subtyped masters; no rule change.

## Main-Line Assessment

- The core four-way classification framework is in place: `direct`, `substitute`, `anchor`, `irrelevant`.
- High-risk code naked-direct risk is guarded by `require_name_keyword_for_code`, `substitute_before_direct`, and Section AB invariants.
- Remaining main-line work is breadth:
  - sample bank still has partial groups, especially substitute coverage.
  - real report validation is sparse: C-1 and C-3 were blocked by fact guard, C-2 saved successfully.
  - PDF/HTML/page口径一致性 is intentionally deferred.

## Next Recommended Flow

1. New Codex window first audits commit `7cbba83`.
2. If accepted, send Claude Code the Phase 5D prompt in `NEXT_SESSION_PROMPT.md`.
3. Phase 5D should batch-strengthen substitute samples for partial master groups without widening direct rules.

## Hard Boundaries

- Do not push.
- Do not modify frontend / UI / PDF.
- Do not modify database schema.
- Do not process temp artifacts.
- Claude Code may implement, test, and commit within a phase; Codex audits commits afterward.
