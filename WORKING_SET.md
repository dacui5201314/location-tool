# 当前工作状态（2026-05-23）

## Phase 23N — uni-app Web 母版对齐

### 当前 commit

`50508c2` — `fix: remove auto-suggest diagnostic UI, keep formal experience; verify analyze flow states`

### uni-app 整体进度：~93%

### Phase 23N-1 地址自动联想（~98%）

- 用户实测通过：输入文字自动出现候选，不需要点击搜索
- `@input` 显式绑定 + `:value="addressKeyword"`（对齐 Web 非受控输入模式）
- 400ms debounce + 竞态守卫（`keyword !== this.addressKeyword.trim()` 丢弃旧结果）
- 地图点选/定位共用 `resolveAddressByLngLat(lng, lat, source)`
- Timeout 三级降级：getLocation / locationRegeocode / locationSuggest
- 诊断 UI（inputDiag / suggestDiag）已删除

### Phase 23N-2 分析接口（~40%）

- `/api/analyze` SSE 流已集成（`api.analyzeLocation`）
- 401 → 提示登录 | 402 → 提示余额不足 | 5xx → 后端异常 | 成功 → navigateTo report-detail
- 后端 `record_id` 已添加到 SSE step 4 result
- 待 devtools 实测验证

### 全局原则（写入 CURRENT_HANDOFF.md / PROJECT_PROGRESS.yml）

**uni-app 是未来主客户端，但 Web frontend 仍是产品母版/参照。**
所有 uni-app 页面/逻辑/UI/文案/状态流必须以 Web 为目标对齐。
新增功能前先查看 Web 对应实现，再在 uni-app 中复刻。

### 对齐优先级

1. 地址自动联想 → Web 行为一致 ✅
2. 分析接口流程 → Web /api/analyze SSE ✅（待实测）
3. 首页 UI → Web 首屏对齐
4. 报告详情 UI → Web 报告页对齐
5. 记录/收藏/我的 → 逐页对齐

### 硬边界

- 不 push（除非明确指令）
- 不提交 AppID/AppSecret/API keys
- 不处理 tmp_*
- 不修改 frontend/ Web 母版
- 不继续 native miniprogram 新功能
- 不接 requestPayment / unlock-pdf / download
- 不修改报告精准度逻辑、POI、rules、prompt、report_fact_guard、classification、DB schema

### 验证基线

- backend compileall：PASS（37 files, 0 errors）
- check_industry_rigor_rules.py：2168 PASS, 0 FAIL
- check_report_fact_guard.py：147 PASS, 0 FAIL
- uniapp build:mp-weixin：PASS
- JSON parse：PASS（package/manifest/pages/dist app.json）
- secret scan：PASS
