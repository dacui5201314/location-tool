# Current Handoff - 2026-05-28 Launch Stabilization Complete

## READ THIS FIRST — 2026-05-28 Evening Authoritative State

**Current HEAD**: `6a55fce` — `feat: single-page shell with custom tabbar replacing native switchTab`
**Pushed**: yes
**Launch target**: uniapp WeChat Mini Program

### Latest Commits

| Commit | Summary |
|--------|---------|
| `6a55fce` | Single-page shell + custom tabbar + frontend fixes |
| `668ccf7` | Retry diagnostics + P0-NAME artifact blacklist |
| `b5f9618` | Add backend/logs to gitignore |

### What Works Now

- WeChat login, avatar, nickname
- Password login + rate limiting
- Home page with custom tabbar (no native switchTab white flash)
- Map center pin + drag-to-select + tap-to-select
- /api/analyze Step 1-4 end-to-end (with P0 guard hard-blocking)
- Report detail page
- Records list page
- Favorites → analyze → report closed loop with favorite_id write-back
- Profile page with full modules (VIP, points, CDK, recharge, CS)
- Report sharing via share_token
- Admin AMap key pool with auto-failover
- Admin share config

### Known Issues (P2, non-blocking)

- P0-NAME guard may still flag new LLM-output artifact phrases — narrow blacklist fixes only
- analyze success rate ~50-67% depending on LLM output — retry mechanism helps
- welcome modal flash (map renders behind it correctly now)
- DevTools wxss selector warnings — cosmetic only

### Hard Boundaries

- Do not push secrets (AppID/AppSecret/keys/PEM/tokens)
- Do not modify frontend/ (Web reference only)
- Do not weaken P0/P2/P3 fact guard
- Do not add /unlock-pdf or /download to uniapp
- PDF replaced by report sharing
- Native miniprogram/ is frozen
