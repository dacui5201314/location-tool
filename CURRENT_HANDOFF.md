# Current Handoff - 2026-05-28

## Read This First

This file is intentionally short. Older phase history was removed because it is
already in git history and was becoming context noise.

- Project: `C:\Users\admin\location-tool`
- Launch target: `uniapp` WeChat Mini Program
- Web `frontend/`: product master/reference only; do not modify unless the user explicitly approves
- Current committed HEAD before this handoff-slimming edit: `082c43d`
- Latest code commit: `6a55fce` - single-page shell with custom tabbar replacing native `switchTab`
- Latest backend fix: `668ccf7` - retry diagnostics and narrow P0-NAME artifact blacklist
- This slimming edit may leave `CURRENT_HANDOFF.md` / `PROJECT_PROGRESS.yml` modified until committed

## Current Working State

- Native tabBar white transition is fixed by the single-page shell/custom bottom nav.
- Map no longer overlays other tabs and no longer disappears after fast tab switching.
- Map uses a fixed center pin. Current interaction is drag/tap map under the pin.
- Favorites -> Analyze -> Report is working with `favorite_id`, address, lat/lng, and report UUID write-back.
- User manually verified favorite id=6 can read/open report `6413ae9793384520ae0fb90dbe24930f`.
- `/api/analyze` has succeeded end-to-end with P0/P2/P3 hard guard preserved.
- Report-detail UI has been redesigned on the mini-program display layer only: score card alignment, professional card hierarchy, dimension radar section, risk/crowd/POI sections, and visual polish were improved without changing report data or accuracy logic.
- Mini-program global UI has a first launch-polish pass: clearer favorite button, traditional bottom tabbar, profile/cards/button states, and records/favorites/profile panel visual polish.
- Home address display was adjusted: top "门店位置" uses `compactAddress` as a short display-only label; "当前位置" keeps the full address and can wrap. `addressText`, `addressKeyword`, analyze payload, favorites, map selection, and regeocode must remain unchanged.
- Report sharing uses `share_token`.
- Payment code path exists, but production payment still needs real WeChat Pay credentials.

## Successful Analyze Evidence

- Latest successful `report_uuid`: `6413ae9793384520ae0fb90dbe24930f`
- `AnalysisRecord id`: `96`
- User: `46`
- Favorite: `6`
- `SavedLocation.latest_report_uuid` for favorite 6 equals the report UUID above
- Input: Shaanxi Baoji, `小吃快餐`, `陕二丫擀面皮`, `50㎡`
- User 46 is yearly member, so this successful analyze did not deduct points
- First LLM output hit P0, retry corrected it, then the report saved. This is desired behavior.

## Still Open

1. **Final mini-program visual QA**: report-detail and global UI have been improved, but still need final real-device/DevTools pass for overlap, bottom tabbar safe-area spacing, long text, empty/loading states, and visual consistency.
2. **Home address display QA**: top compact address may prefer short landmark names even if it removes province/city/district/street text. This is accepted only as display behavior; full address and analyze payload must stay original.
3. **WeChat Pay**: external credential/setup task. After cert/key upload, replace customer-service purchase path with direct order/payment.
4. **Admin UI/IA**: system settings are crowded; industry management and per-industry prompt participation need audit. Ask before touching `frontend/`.
5. **P0 artifact maintenance**: keep hard guard. If a new false positive appears, add only narrow artifact filters with regression tests.
6. **Analyze stability**: one success is confirmed; 5-run same-input acceptance is still pending and should only run after the user approves API/time cost.
7. **HarmonyOS**: P2 compatibility QA only; no dedicated business branch yet.
8. **Draggable map pointer**: user wants it, but WeChat map marker dragging is not natively supported. Research before attempting.

## Hard Boundaries

- Do not push unless explicitly asked.
- Do not leak AppID/AppSecret/tokens/API keys/AMap keys/security secrets/merchant keys/certs/PEM/private keys.
- Do not process `tmp_*`.
- Do not add `/unlock-pdf` or `/download`.
- Do not implement PDF now.
- Do not weaken P0/P2/P3 fact guard.
- Do not turn real P0 into warning-save.
- Do not modify scoring, POI classification, prompt semantics, report accuracy logic, or `report_fact_guard` unless explicitly authorized.
- Do not modify `frontend/` unless explicitly approved.
- Do not modify `PROJECT_STATE.md` / `WORKING_SET.md` unless explicitly needed.

## Next Window Instruction

```text
Project: C:\Users\admin\location-tool

You are a new Codex window. First read:
1. CURRENT_HANDOFF.md
2. PROJECT_RULES.md
3. PROJECT_PROGRESS.yml
4. C:\Users\admin\Desktop\问题审计.txt

Do not read PROJECT_STATE.md / WORKING_SET.md unless explicitly needed.

Start by running git status. Do not reset/revert/push/commit unless I explicitly ask.

Current priority:
1. Final QA mini-program UI polish already done in uniapp/: report-detail, home, favorites, records, profile, and traditional bottom tabbar.
2. Verify bottom tabbar safe-area spacing, long text, empty/loading states, and home compact address display on real device/DevTools.
3. Keep compactAddress display-only: do not change addressText/addressKeyword/analyze payload/favorites/map/regeocode.
4. WeChat Pay direct purchase only after I provide credentials.
5. Admin IA/UI and industry prompt audit later; ask before modifying frontend/.

Keep P0/P2/P3 hard guard intact. Do not change scoring, POI classification, prompt semantics, report_fact_guard, PDF/download, or secrets.
```

## Validation For Any Code Change

- Backend changed: `uv run python -m compileall backend`
- Uniapp changed: `cd uniapp && npm run build:mp-weixin`
- Frontend changed with permission: `cd frontend && npm run build`
- JSON parse: `uniapp/package.json`, `uniapp/src/manifest.json`, `uniapp/src/pages.json`, `uniapp/dist/build/mp-weixin/app.json`, `uniapp/dist/build/mp-weixin/project.config.json`
- `rg "unlock-pdf|/download" uniapp/src` must be 0
- `rg "moveToLocation|moveToMapLocation" uniapp/src uniapp/dist/build/mp-weixin` must be 0
- `rg "switchTab" uniapp/src uniapp/dist/build/mp-weixin` must be 0
- Payment chain must still use real `requestPayment/createPrepay/queryOrder`
- Share chain must keep `share_token/onShareAppMessage`
- Developer/debug copy scan
- Secret scan
- `git status --short`
