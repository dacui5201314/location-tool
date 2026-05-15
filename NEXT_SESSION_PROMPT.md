# 新窗口无缝交接提示词（短版入口）

新窗口优先只读取：

1. `PROJECT_RULES.md`
2. `PROJECT_PROGRESS.yml`
3. `CURRENT_HANDOFF.md`

`PROJECT_STATE.md` / `WORKING_SET.md` 仅作参考资料。

当前状态：**Phase 4B-1 code_review_passed**，以 `CURRENT_HANDOFF.md` 为准。

---

# 历史长版交接（仅参考）

项目路径：C:/Users/admin/location-tool，产品名址得选。

## Phase 4B-1 已完成代码侧审核

- latest commit: `8e06ec5`（Phase 4B-1），未 push
- previous: `579b004`（Phase 4A）
- `backend/report_fact_guard.py` 新增纯函数（仅 json/re），`main.py` 内联逻辑已抽取
- fact guard: 76 PASS, 0 FAIL / industry: 1876 PASS, 0 FAIL
- 轻量测试边界：check_report_fact_guard.py 不 import main
- 待 Codex/用户决定是否提交

新窗口第一步：

1. 读取 `PROJECT_RULES.md` / `PROJECT_PROGRESS.yml` / `CURRENT_HANDOFF.md`
2. 运行 `git status --short`
3. 复跑：
   - `python -m compileall backend`
   - `python backend/tests/check_industry_rigor_rules.py`
   - `python backend/tests/check_report_fact_guard.py`
4. 若全部通过，进入等待态（Phase 4B-1 已完成，不要继续实现）。

## 历史记录

- 只允许围绕 `backend/main.py` 和 `backend/tests/check_report_fact_guard.py`
- 不调用 AMap/LLM
- 不启动前端
- 不真实请求
- 不 push
- 不处理临时产物
- 不继续扩 Sample Bank 或 POI 关键词

## C-2 已通过

- 业态：刚需快餐小吃 | 地址：北京市海淀区中关村大街19号
- 报告保存 id=22, score=50，fact_errors=0
- P0 假阳性已二次收窄，fact guard 76 PASS

## 最新基线

- compileall backend：PASS
- check_industry_rigor_rules.py：1876 PASS, 0 FAIL
- check_report_fact_guard.py：76 PASS, 0 FAIL
- KNOWN_RULE_GAPS：(none)

## 下一步

等待用户明确授权下一次真实报告或新任务。
不调用 AMap/LLM 除非用户再次授权。
不提交、不 push。

## 角色分工

- 用户是产品负责人和最终验收人。
- Claude Code 是代码执行者。
- Codex 是项目总负责、代码审查者、Claude Code 指挥官。
- Codex 默认不要直接改后端 POI 分类、评分逻辑、AMap 规则、数据库结构；优先给 Claude Code 明确提示词，再由 Codex 审核。
- 交接文档类修改可由 Codex 直接完成。

## 产品定位

“址得选”是全国商铺选址初筛参考工具，不是决策平台。

所有报告必须强调：

- 初筛参考
- 需线下验证
- 不提供投资建议
- 不替用户做决策

禁止表达：

- 推荐/不推荐
- 建议推进
- 高风险推进
- 决策平台
- 助力决策

## 当前最高优先级

报告精准度。

UI、PDF、页脚、端口清理暂时降级，除非阻塞报告精准度验证。

## 2026-05-15 历史交接状态（方案 C + P0 小修补强，已过期）

旧内容中出现的 `50 PASS`、id=21 离线复验、P0-FIX 等信息可能已过期。新窗口先以本节为准。

### 角色边界（非常重要）

- Claude Code 是代码执行者。
- Codex 是审核者和指挥者。
- Codex 不直接操作修改代码，不接手实现。
- Codex 只读审计、复核 Claude Code 的 diff/测试结果，并给下一步 Claude Code 指令。
- 交接文档类修改可由 Codex 直接完成。

### 方案 C 已执行

- 业态：药店 | 地址：陕西省宝鸡市渭滨区经二路138号 | lng=107.148, lat=34.362
- AMap 采集/脱水成功，LLM 8维评分生成成功
- **报告未保存**：fact_errors 拦截 `stats_200m.residential=0 but report says 7个`
- 退款链路触发正常，Guard hard-error 有效
- Guard: P0=4条(1真+3假)，P2=0，P3=0

### P0 假阳性小修已完成

- `_DESCRIPTIVE_MARKERS`：`米内无`/`商圈内`/`无任何` + `无大型` 开头
- 用 `"米内无"` 而非 `"米内"`，避免误杀 `"米内有XX店"`
- 锁回归：T-P0F-12 `"500米内聚集了益丰大药房"` 仍 warning

### 当前最新基线

- `python -m compileall backend` 通过。
- `python backend/tests/check_report_fact_guard.py`：**61 PASS, 0 FAIL**。
- `python backend/tests/check_industry_rigor_rules.py`（历史）：1598 PASS, 0 FAIL（当前 1876 PASS）。
- `KNOWN_RULE_GAPS: (none)`。
- 未调用 AMap/LLM API（C-1 以后，C-2 前）。
- 未启动前端。
- 未提交、未 push。

### 下一步

C-2 已完成并通过。下一步等待用户授权新任务。
C-2 中 fact_errors=0，residential 幻觉未复现。

## 2026-05-14 历史交接状态（已过期）
- Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5`
- Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5`
- Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5`
- Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5`
- Convenience：`d=10 nd=10 s=5 a=5 i=5`
- Fresh Produce：`d=10 nd=10 s=5 a=5 i=5`

其余 13 个保持 `partial`，均达到 `d>=10 nd>=10 s=0 a=5 i=5`：

- Pharmacy / Tobacco-Liquor / Daily Goods
- Beauty / Pet / Fitness
- Education / Laundry / Clinic
- Bar / KTV / Internet Cafe
- Immersive Social：`d=22 nd=10 s=0 a=5 i=5`

### 报告事实校验层状态

- P0 已完成：POI 名称引用校验，warning-only。
  - 函数：`check_poi_name_hallucination(full_text, real_data, strict=False)`
  - 写入：`result["_poi_name_warnings"]`
- P0-FIX 已完成：泛称/描述性前缀假阳性修补，warning-only。
  - 覆盖 `周边/附近 + 泛称 POI 后缀`。
  - 覆盖 `晚间客流依赖周边酒店` 这类长候选误提取。
  - 保留具体伪造名称检测能力，例如 `瑞幸咖啡门店` 仍 warning。
- P1 暂缓：旧口径 `competitors_*` 误用检测。当前不实现，待无-rigor 业态或旧字段再暴露时处理。
- P2 已完成：`substitute_list` / `traffic_anchor_list` 被报告误写成竞品语境，warning-only。
  - 函数：`check_poi_context_mismatch(full_text, real_data)`
  - 写入：`result["_poi_context_warnings"]`
- P3 已完成：直接竞品数量膨胀，warning-only。
  - 函数：`check_direct_competitor_count_mismatch(full_text, real_data)`
  - 只检查 `direct_competitors_200m/500m/1000m`
  - 只在“竞品语境 + 明确半径 + 精确阿拉伯数字 + reported > expected”时 warning
  - 不抓少报
  - 写入：`result["_direct_competitor_count_warnings"]`

三类校验共同要求：

- 打印 warning 日志。
- 写入 `result` JSON。
- 不加入 `fact_errors`。
- 不 `raise ValueError`。
- 不影响报告保存或退款链路。

### 当前工作区提醒

- `backend/tests/check_industry_rigor_rules.py` 有既有 diff，不要处理、不要回滚、不要格式化。
- `backend/prompts/industry_config.py` 有既有 diff，不要处理、不要回滚、不要格式化。
- `frontend/vite.config.js` 有既有 diff，不要处理。
- `PROJECT_RULES.md`、`PROJECT_STATE.md`、`WORKING_SET.md`、`NEXT_SESSION_PROMPT.md` 是交接文档。
- `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时报告产物不要处理。
- 不要保留临时 `_offline/_recheck/_trace/id21` 脚本；离线复验用 inline python。

### 下一步 Claude Code 指令建议

```text
进入“方案 C：一次最小端到端真实报告验收”。

严格限制：
- 必须先获得用户明确授权，才允许调用 AMap API 和 LLM API
- 不启动前端
- 可启动后端或使用已有后端
- 用 curl/httpx 发起 1 次真实分析请求
- 不提交，不 push
- 不处理、不回滚、不格式化既有 diff：
  - backend/tests/check_industry_rigor_rules.py
  - backend/prompts/industry_config.py
  - frontend/vite.config.js

执行前必须让用户确认：
1. 是否允许调用 AMap API
2. 是否允许调用 LLM API
3. 使用哪个业态和地址
4. 是否允许启动后端服务
5. 明确不启动前端

建议样本：
- 优先药店：社区底商、竞品边界清晰，适合观察 direct/substitute/anchor。
- 备选茶饮咖啡：商圈/写字楼，适合观察竞品密集和 P3。
- 备选快餐小吃：学校/交通枢纽，适合观察 P0/P3。

验收输出：
1. 请求参数（业态、地址、经纬度如有）
2. 是否成功完成 AMap 采集和 LLM 生成
3. result 中三类 warning 字段：
   - _poi_name_warnings
   - _poi_context_warnings
   - _direct_competitor_count_warnings
4. fact_errors 是否触发
5. 报告是否保存成功
6. 是否触发退款/失败链路
7. 若有 warning，逐条判定真阳性/假阳性/不确定
8. 是否建议继续保持 warning-only
```

## 2026-05-14 历史交接状态（P0/P2/P3 收口，已过期）

旧内容中出现的 `17 PASS, 0 FAIL`、`1511 PASS, 0 FAIL`、`1391 PASS, 0 FAIL`、`1291 PASS, 0 FAIL`、Laundry/Convenience/P2 下一步等信息已经过期。新窗口先以本节为准，再读下方历史脉络。

### 角色边界（非常重要）

- Claude Code 是代码执行者。
- Codex 是审核者和指挥者。
- Codex 不直接操作修改代码，不接手实现。
- Codex 只读审计、复核 Claude Code 的 diff/测试结果，并给下一步 Claude Code 指令。
- 交接文档类修改可由 Codex 直接完成。

### 当前最新基线

- `python -m compileall backend` 已通过。
- `python backend/tests/check_report_fact_guard.py` 已通过：`42 PASS, 0 FAIL`。
- `python backend/tests/check_industry_rigor_rules.py` 已通过。
- Sample Bank canonical（历史）：1598 PASS, 0 FAIL（当前 1876 PASS）。
- `KNOWN_RULE_GAPS: (none)`。
- 未生成真实报告。
- 未启动前端。
- 未提交、未 push。

### Sample Bank 收口状态

`complete_candidate` 仍只有 7 个：

- Snack Shop：`d=13 nd=10 s=5 a=5 i=5`
- Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5`
- Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5`
- Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5`
- Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5`
- Convenience：`d=10 nd=10 s=5 a=5 i=5`
- Fresh Produce：`d=10 nd=10 s=5 a=5 i=5`

其余 13 个保持 `partial`，均达到 `d>=10 nd>=10 s=0 a=5 i=5`：

- Pharmacy / Tobacco-Liquor / Daily Goods
- Beauty / Pet / Fitness
- Education / Laundry / Clinic
- Bar / KTV / Internet Cafe
- Immersive Social：`d=22 nd=10 s=0 a=5 i=5`

### 报告事实校验层状态

- P0 已完成：POI 名称引用校验，warning-only。
  - 函数：`check_poi_name_hallucination(full_text, real_data, strict=False)`
  - 写入：`result["_poi_name_warnings"]`
- P1 暂缓：旧口径 `competitors_*` 误用检测。当前不实现，待无-rigor 业态或旧字段再暴露时处理。
- P2 已完成：`substitute_list` / `traffic_anchor_list` 被报告误写成竞品语境，warning-only。
  - 函数：`check_poi_context_mismatch(full_text, real_data)`
  - 写入：`result["_poi_context_warnings"]`
- P3 已完成：直接竞品数量膨胀，warning-only。
  - 函数：`check_direct_competitor_count_mismatch(full_text, real_data)`
  - 只检查 `direct_competitors_200m/500m/1000m`
  - 只在“竞品语境 + 明确半径 + 精确阿拉伯数字 + reported > expected”时 warning
  - 不抓少报
  - 写入：`result["_direct_competitor_count_warnings"]`

三类校验共同要求：

- 打印 warning 日志。
- 写入 `result` JSON。
- 不加入 `fact_errors`。
- 不 `raise ValueError`。
- 不影响报告保存或退款链路。

### 当前工作区提醒

- `backend/tests/check_industry_rigor_rules.py` 有既有 diff，不要处理、不要回滚、不要格式化。
- `backend/prompts/industry_config.py` 有既有 diff，不要处理、不要回滚、不要格式化。
- `frontend/vite.config.js` 有既有 diff，不要处理。
- `PROJECT_RULES.md`、`PROJECT_STATE.md`、`WORKING_SET.md`、`NEXT_SESSION_PROMPT.md` 是交接文档。
- `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时报告产物不要处理。

### 下一步 Claude Code 指令建议

```text
进入“报告事实校验层 P0/P2/P3 收口后的真实报告前 guard 总体验收方案”。

严格限制：
- 只读设计，不改代码
- 不生成真实报告
- 不启动前端
- 不提交，不 push
- 不处理、不回滚、不格式化既有 diff：
  - backend/tests/check_industry_rigor_rules.py
  - backend/prompts/industry_config.py
  - frontend/vite.config.js

输出方案需包含：
1. 验收目标：验证 result 中三类 warning 字段在真实报告生成链路中的表现。
2. 是否需要生成真实报告：先列方案，不执行，等待用户明确授权。
3. 建议验收样本数量：1-3 个。
4. 每个样本应检查：
   - _poi_name_warnings
   - _poi_context_warnings
   - _direct_competitor_count_warnings
   - fact_errors 是否仍只处理 hard-error
   - 报告是否仍保存成功
   - 是否触发退款/失败链路
5. false positive / false negative 记录模板。
6. 是否建议升级 hard-error：当前默认不升级，先观察 warning。
7. 风险点：
   - P0/P2/P3 都是文本启发式，不应立刻硬阻断
   - P3 只抓数量膨胀，不抓少报
   - P1 暂缓，除非出现无-rigor 业态或旧 competitors_* 再暴露
8. 明确下一步需要用户授权后，才可进入真实报告验收。
```

## 2026-05-14 历史交接状态（P0/P2，已过期）

旧内容中出现的 `1511 PASS, 0 FAIL`、`1391 PASS, 0 FAIL`、`1291 PASS, 0 FAIL`、Laundry/Convenience 下一步等信息已经过期。新窗口先以本节为准，再读下方历史脉络。

### 角色边界（非常重要）

- Claude Code 是代码执行者。
- Codex 是审核者和指挥者。
- Codex 不直接操作修改代码，不接手实现。
- Codex 只读审计、复核 Claude Code 的 diff/测试结果，并给下一步 Claude Code 指令。
- 交接文档类修改可由 Codex 直接完成。

### 当前最新基线

- `python -m compileall backend` 已通过。
- `python backend/tests/check_industry_rigor_rules.py` 已通过。
- Sample Bank canonical（历史）：1598 PASS, 0 FAIL（当前 1876 PASS）。
- `KNOWN_RULE_GAPS: (none)`。
- `python backend/tests/check_report_fact_guard.py` 已通过：`17 PASS, 0 FAIL`。
- 未生成真实报告。
- 未启动前端。
- 未提交、未 push。

### Sample Bank 收口状态

`complete_candidate` 仍只有 7 个：

- Snack Shop：`d=13 nd=10 s=5 a=5 i=5`
- Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5`
- Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5`
- Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5`
- Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5`
- Convenience：`d=10 nd=10 s=5 a=5 i=5`
- Fresh Produce：`d=10 nd=10 s=5 a=5 i=5`

其余 13 个保持 `partial`，均达到 `d>=10 nd>=10 s=0 a=5 i=5`：

- Pharmacy / Tobacco-Liquor / Daily Goods
- Beauty / Pet / Fitness
- Education / Laundry / Clinic
- Bar / KTV / Internet Cafe
- Immersive Social：`d=22 nd=10 s=0 a=5 i=5`

### 报告事实校验层状态

- P0 POI 名称引用校验已 warning-only 实现。
- P0 新增：`backend/services/poi_name_guard.py`
- P0 新增：`backend/tests/check_report_fact_guard.py`
- P0 修改：`backend/main.py`
- P0 行为：
  - 调用 `check_poi_name_hallucination(full_text, real_data, strict=False)`
  - 有问题时打印 `[SSE Guard] POI名称引用告警`
  - 写入 `result["_poi_name_warnings"]`
  - 不加入 `fact_errors`
  - 不 `raise ValueError`
  - 不影响报告保存或退款
- P1 旧口径 `competitors_*` 误用检测已审计，当前暂缓。
- 下一步是 P2：`substitute_list` / `traffic_anchor_list` 被报告误写成竞品的 warning-only 语境校验。

### 当前工作区提醒

- `backend/prompts/industry_config.py` 有既有 diff，不要处理、不要回滚、不要格式化。
- `frontend/vite.config.js` 有既有 diff，不要处理。
- `PROJECT_RULES.md`、`PROJECT_STATE.md`、`WORKING_SET.md`、`NEXT_SESSION_PROMPT.md` 是交接文档。
- `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时报告产物不要处理。

### 下一步 Claude Code 指令建议

```text
进入“报告事实校验层 P2：anchor/substitute 被误写成竞品 warning-only 实现”。

严格限制：
- 只允许修改：
  1. backend/services/poi_name_guard.py
  2. backend/tests/check_report_fact_guard.py
  3. backend/main.py
- 不修改 backend/tests/check_industry_rigor_rules.py
- 不修改 backend/prompts/industry_config.py
- 不修改 frontend/vite.config.js
- 不生成真实报告
- 不启动前端
- 不提交，不 push

实现目标：
新增 check_poi_context_mismatch(report_text, real_data) -> list[str]。

要求：
1. 只做 warning-only，不 hard error。
2. 只检查“竞品语境”里的 substitute/anchor 混入。
3. direct 名称在竞品语境中合法。
4. substitute 名称在“替代压力/替代消费”语境中不告警。
5. anchor 名称在“客流锚点/客流来源”语境中不告警。
6. 名称重复时优先级：direct > substitute > anchor。
7. 不要只用精确匹配，必须复用或等价复用 P0 的去括号、前缀/包含匹配逻辑，将 candidate 解析到真实 list 名称后再判断类别。

测试：
在 backend/tests/check_report_fact_guard.py 追加至少 6 个 P2 用例：
- direct 名称出现在竞品句中 → 通过
- substitute 名称出现在替代语境中 → 通过
- substitute 名称出现在直接竞品语境中 → warning
- anchor 名称出现在客流锚点语境中 → 通过
- anchor 名称出现在竞争对手/同类竞品语境中 → warning
- 泛称“周边学校/附近小区是客流锚点，直接竞争压力可控” → 不误杀

main.py 接入：
- 在 P0 warning 之后、if fact_errors 之前
- 调用 check_poi_context_mismatch(full_text, real_data)
- 有结果时 print warning，并写入 result["_poi_context_warnings"]
- 不 fact_errors.extend，不 raise

验证：
- python -m compileall backend
- python backend/tests/check_report_fact_guard.py
- python backend/tests/check_industry_rigor_rules.py

回报：
- 修改文件
- P2 新增测试数
- check_report_fact_guard.py PASS/FAIL
- canonical PASS/FAIL
- 是否仍 warning-only
```

## 2026-05-14 最新交接状态（以本节为准）

旧内容中出现的 `1391 PASS, 0 FAIL`、`1291 PASS, 0 FAIL`、零售 Convenience 下一步等信息已经过期。新窗口先以本节为准，再读下方历史脉络。

当前最新基线：

- `python -m compileall backend` 已通过。
- `python backend/tests/check_industry_rigor_rules.py` 已通过。
- canonical 测试：`1511 PASS, 0 FAIL`。
- `KNOWN_RULE_GAPS`：`(none)`。
- 未生成真实报告。
- 未启动前端。
- 主要样本改动集中在 `backend/tests/check_industry_rigor_rules.py`。

当前 Sample Bank 状态：

- Snack Shop：`d=13 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5 [complete_candidate]`
- Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5 [complete_candidate]`
- Convenience：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Fresh Produce：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Pharmacy：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Tobacco/Liquor：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Daily Goods：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Beauty：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Pet：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Fitness：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Education：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Laundry：`d=7 nd=10 s=0 a=0 i=0 [partial]`
- Clinic：`d=8 nd=10 s=0 a=0 i=0 [partial]`
- Bar：`d=6 nd=7 s=0 a=0 i=0 [partial]`
- KTV：`d=6 nd=7 s=0 a=0 i=0 [partial]`
- Internet Cafe：`d=5 nd=7 s=0 a=0 i=0 [partial]`
- Immersive Social：`d=22 nd=10 s=0 a=0 i=0 [partial]`

当前策略：

- 对 substitute 规则不适用或为空壳的组，保持 `partial`，不硬凑 substitute。
- 不新增 `KNOWN_RULE_GAPS`，保持 `(none)`。
- 不改业务规则，仅补 canonical 样本。

建议下一步：

执行“社区基础服务 Laundry（洗衣店）保守补样本”。本轮不是审计，已审计通过，可直接执行，但仍只改测试文件。

```text
进入“社区基础服务 Laundry（洗衣店）保守补样本执行”。

项目路径：
C:\Users\admin\location-tool

严格限制：
- 只修改 backend/tests/check_industry_rigor_rules.py
- 不修改 backend/prompts/industry_config.py
- 不修改 backend/services/amap_service.py
- 不修改 frontend/src/services/amapData.js
- 不生成真实报告
- 不启动前端
- 不改 UI/PDF/端口/数据库 schema
- 不改 AMap API 调用方式
- 不提交，不 push
- 不新增 KNOWN_RULE_GAPS
- 不把 Laundry 强行标记为 complete_candidate

当前状态行：
("Laundry",7,10,0,0,0,"partial")

目标状态行：
("Laundry",10,10,0,5,5,"partial")

执行内容：
1. Laundry direct 新增 3 个：
   - 洗衣房，type_code: 生活服务;洗衣店
   - 洗衣馆，type_code: 生活服务;洗衣店
   - 干洗馆，type_code: 生活服务;洗衣店
2. Laundry anchor 新增 5 个：
   - 住宅小区，type_code: 120300
   - 公寓，type_code: 120300
   - 写字楼，type_code: 120200
   - 小学，type_code: 科教文化服务;学校
   - 中学，type_code: 科教文化服务;学校
3. Laundry irrelevant 新增 5 个：
   - 驾校，type_code: 050300
   - 职业培训，type_code: 050300
   - 职业培训学校，type_code: 050300
   - 医院，type_code: 050300
   - 药店，type_code: 050300
4. 不新增 substitute 样本。社区基础服务 substitute 目前只有 description，没有可匹配字段。
5. 更新 Sample Bank Status：
   ("Laundry",10,10,0,5,5,"partial")

执行后验证：
- python -m compileall backend
- python backend/tests/check_industry_rigor_rules.py
- 必须保持 0 FAIL
- KNOWN_RULE_GAPS 必须仍为 (none)
- 回报最终 PASS/FAIL 数、Laundry 状态行、实际改动文件列表
```

## 2026-05-13 历史交接状态

旧内容中出现的 `1291 PASS, 0 FAIL`、餐饮 known_gap、Tea/Coffee 下一步等信息已经过期。新窗口先以本节为准，再读下方历史脉络。

当前最新基线：

- `python -m compileall backend` 已通过。
- `python backend/tests/check_industry_rigor_rules.py` 已通过。
- canonical 测试：`1391 PASS, 0 FAIL`。
- `KNOWN_RULE_GAPS`：`(none)`。
- 餐饮五组 Sample Bank 已推进到 `complete_candidate`：
  - Snack Shop：`d=13 nd=10 s=5 a=5 i=5 [complete_candidate]`
  - Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
  - Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
  - Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5 [complete_candidate]`
  - Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5 [complete_candidate]`
- `frontend/src/services/amapData.js` 无 diff。
- 未生成真实报告。
- 未启动前端。

本轮已收口的关键点：

- Tea/Coffee、Chinese Restaurant、Hotpot/BBQ、Bakery/Dessert、Convenience routing 共 5 个 known_gap 已关闭。
- Hotpot/BBQ 没有扩大 direct 口径；只是加了 `require_name_keyword_for_code`、边界 exclude 和窄 irrelevant blacklist。
- Convenience routing 是测试 type_code 问题，未改业务规则。
- Sample Bank 当前仍是测试防线建设阶段，不代表可以生成真实报告。

建议下一步：

进入“零售 Sample Bank complete_candidate 第一组：Convenience（便利店）”。

新窗口第一步只做只读审计，不直接改代码：

```text
进入零售 Sample Bank complete_candidate 第一组审计：Convenience（便利店）。
只分析，不改代码，不生成真实报告，不启动前端，不改 UI/PDF/端口/数据库 schema，
不改 AMap API 调用方式，不改 frontend/src/services/amapData.js，
不处理历史前端脏文件，不提交，不 push。

当前基线：
- compileall backend 通过
- canonical 1391 PASS, 0 FAIL
- KNOWN_RULE_GAPS: (none)
- 餐饮五组 complete_candidate 已完成

请只读检查：
1. backend/prompts/industry_config.py 中 高频刚需零售 / convenience / supermarket 相关规则：
   direct_competitor_rules
   substitute_competitor_rules
   traffic_anchor_rules
   irrelevant_poi_rules
2. backend/tests/check_industry_rigor_rules.py 中 Convenience 当前 Sample Bank 状态和样本。

输出：
1. 当前 Convenience 样本 d/nd/s/a/i 数量。
2. 距 complete_candidate 还缺哪些类别。
3. 每个缺口的全国通用候选样本、真实 type_code、真实链路推演。
4. 是否仅补 canonical 测试即可，还是暴露规则缺口。
5. 若需修规则，必须说明是否会扩大 direct 口径；优先不扩大 direct。
6. 最小执行方案和风险。
```

## 当前最新基线

最近一次 Codex 审核确认：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical 测试：`1291 PASS, 0 FAIL`。
- Sample Bank v1 partial baseline 已建立。
- 14/14 master 已消除高风险 broad code 裸 direct 风险。
- `frontend/src/services/amapData.js` 无 diff。
- 未生成真实报告。
- 未启动前端。
- `backend/tools/` 无 `fix_sample_bank*.py` 临时脚本残留。

## 已完成主线

### 第一阶段：底层规则引擎和小吃店误判

已完成：

- `classify_poi_rigor()` 支持：
  - `require_name_keyword_for_code`
  - `substitute_before_direct`
  - `strict_exclude_names`
  - subtype 继承
- `刚需快餐小吃` 不再让 `050300` 裸直通 direct。
- 肯德基、麦当劳、必胜客、普通中餐厅不进小吃店 direct。
- 擀面皮、凉皮、麻辣烫等进 direct。
- 鸭脖、卤味、炸鸡、汉堡等进 substitute。

### 第二阶段：subtype 深化和真实链路

已深化：

- 高频刚需零售
- 专业生活服务
- 社区基础服务
- 夜经济娱乐

已新增真实链路 category：

- `education_training`
- `laundry`
- `clinics`
- `fitness`
- `fresh_retail`
- `tobacco_liquor`

已完成：

- `cat_override` 已从真实链路测试中移除。
- `fresh_retail` / `tobacco_liquor` 通过 shopping 业务感知改写进入真实链路。
- `FRESH_RETAIL_KEEP` 重复关键词已去重。

### 第三阶段：住宿业态

已完成：

- `商务酒店` / `民宿青旅` 均开启：
  - `require_name_keyword_for_code=True`
  - `substitute_before_direct=True`
- `100000` 裸 direct 风险已消除。
- 已补住宿 direct / substitute / excluded / 真实链路测试。

### 第四阶段：anchor 和沉浸式社交娱乐

已完成：

- Section U：anchor 规则层显式测试。
- `沉浸式社交娱乐` subtype 深化：
  - 剧本杀
  - 密室逃脱
  - 台球厅
  - 桌游/轰趴
  - 电玩/VR
- 新增 `immersive_entertainment` category。
- `体育休闲服务;娱乐场所 -> immersive_entertainment`。
- 裸 `080000` 仍不展示，不映射到 immersive。
- KTV/酒吧/网吧仍归 `bars`，夜经济娱乐 direct 不受影响。
- 混名 POI 在真实链路中返回 `dewater_drop`。

### 第五阶段：Sample Bank v1 partial baseline

已完成：

- X-AA Sample Bank 第一批稳定样本入库。
- canonical 从 `941 PASS, 0 FAIL` 扩展到 `1291 PASS, 0 FAIL`。
- 没有 complete 组。
- 所有组状态只允许 `partial` 或 `known_gap`。
- 没有 `near-complete`。
- `sim_full_chain()` 无 `cat_override/default_cat`。
- `check_sub()` 严格 `r == "substitute"`。
- 不带 FAIL 交付。

当前 known gaps：

1. 精品茶饮咖啡：甜品店/冰淇淋店/便利店/火锅店/烧烤店边界。
2. 中餐正餐：火锅店/烧烤店/茶饮店/咖啡店边界。
3. 火锅烧烤：茶饮店/咖啡店/西餐/日料/中餐馆边界。
4. 烘焙甜品：便利店/火锅店/烧烤店/茶饮店边界。
5. 便利店：快餐/咖啡/茶饮/炸鸡 substitute 路由类型不匹配。

## 当前未完成

### 1. 完整样本库未铺满

Sample Bank v1 只是 partial baseline。

完整目标仍是每个业态或 subtype：

- direct 正例 ≥ 10
- not direct 反例 ≥ 10
- substitute 正例 ≥ 5
- anchor 正例 ≥ 5
- irrelevant 正例 ≥ 5

下一步不要全量铺开。每轮只处理一个 known_gap 或一个小业态组。

### 2. 报告事实校验层未全面进入

已有 prompt 约束和基础事实校验，但还未系统强化：

- has_rigor=True 时禁止使用旧口径 `competitors_*`。
- 报告正文中竞品、医院、学校、住宅、anchor 等数量必须和 `real_data` 对齐。
- substitute 必须明确为“非直接竞品”。
- anchor 必须明确为“客流锚点，不是竞品”。
- 数字不一致时拦截、退款、不保存正式报告的完整链路还需验收。

### 3. 真实报告验收未进入

不要主动生成真实报告。

只有用户明确允许进入验收时，才选择 1-3 个真实样本生成报告，检查 direct/substitute/anchor/irrelevant 与报告措辞。

## 新窗口第一步建议

只做只读检查，不改代码：

```powershell
git status --short
git status --short frontend/src/services/amapData.js backend/services/amap_service.py backend/prompts/industry_config.py backend/tests/check_industry_rigor_rules.py
C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe backend/tests/check_industry_rigor_rules.py
```

确认：

- canonical 当前是否仍是 `1291 PASS, 0 FAIL`。
- `frontend/src/services/amapData.js` 是否无 diff。
- `backend/tools/` 是否无临时脚本。
- 工作区是否仍有历史脏文件，不要擅自处理。

## 下一步执行动作

建议下一步：**餐饮 known_gap 第一组小收口：精品茶饮咖啡**。

不要继续全量铺样本库。不要生成真实报告。

先让 Claude Code 只做分析，不直接改规则：

```text
进入餐饮 known_gap 第一组审计：精品茶饮咖啡。不要生成真实报告，不启动前端，不改 UI/PDF/端口/数据库 schema，不改 AMap API 调用方式，不改 frontend/src/services/amapData.js。

当前基线：
- compileall backend 通过
- canonical 1291 PASS, 0 FAIL
- Sample Bank v1 partial baseline 已建立

本轮先只分析，不改业务逻辑：
1. 读取 backend/prompts/industry_config.py 中“精品茶饮咖啡”的 direct/substitute/anchor/irrelevant 规则。
2. 读取 backend/tests/check_industry_rigor_rules.py 中 Tea/Coffee 相关样本和 known_gap。
3. 判断以下样本应进入哪类：
   - 甜品店
   - 冰淇淋店
   - 便利店
   - 火锅店
   - 烧烤店
4. 给出全国通用规则修复建议：
   - 哪些应 exclude/irrelevant
   - 哪些应 substitute
   - 是否需要 substitute_before_direct 或 strict_exclude
   - 是否影响其他餐饮业态
5. 不要直接改代码。

输出：
- 当前规则为什么会误判
- 每个 gap 样本建议分类
- 最小修改方案
- 需要新增/调整哪些 canonical 测试
- 风险评估
```

等 Claude Code 返回分析后，Codex 再审核并给具体代码修改指令。

## 永久提醒

- 不要为宝鸡、经二路、商场、门店、品牌写硬编码特判。
- 样本只用于暴露全国通用规则问题。
- 不要只看规则层 PASS，必须关注真实链路。
- 当前报告精准度优先于 UI/PDF/端口清理。
- 不要擅自处理历史前端脏文件或临时报告文件。
- 不要用临时脚本批量重写测试文件。
- 不要带 FAIL 交付。
