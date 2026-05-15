# 项目状态（2026-05-15，以本节为准）

## Phase 4B-1 已完成代码侧审核

- latest commit: `8e06ec5`（Phase 4B-1），未 push
- previous: `579b004`（Phase 4A）
- `backend/report_fact_guard.py` 新增 `validate_report_fact_consistency` 纯函数（仅 json/re）
- `backend/main.py` 内联逻辑抽取完成
- `backend/tests/check_report_fact_guard.py` P4 段 10 用例，importlib 加载
- **fact guard: 76 PASS, 0 FAIL** / industry: 1876 PASS, 0 FAIL / KNOWN_RULE_GAPS: (none)
- 待 Codex/用户决定是否提交

## 历史记录（C-2 及更早，已过期）

- 方向正确：继续从“规则修补”升级到“real_data 与 LLM 正文对账”。
- 现有 `backend/main.py` 已有 hard-error 逻辑，覆盖：
  - `direct_competitors_200m/500m/1000m`
  - `substitute_competitors_200m/500m/1000m`
  - `traffic_anchors_200m/500m/1000m`
  - `stats_*.subway/bus/schools/hospitals/residential/office`
  - 异常大数字
- Phase 4B-1 已完成：抽成 `report_fact_guard.py` 纯函数 + subject 关键词补强 + 旧口径检测 + P4 10 用例
- fact guard: 76 PASS, 0 FAIL
- 不处理临时产物
- 不继续补 POI 关键词或 Sample Bank，除非用户另行授权

## C-2 后端真实报告复验

C-2 已完成并通过 Codex 复核。

### C-2 请求参数

| 参数 | 值 |
|---|---|
| 业态 | 刚需快餐小吃 |
| 地址 | 北京市海淀区中关村大街19号 |
| Provider | deepseek |

### C-2 结果

- AMap 采集：成功
- LLM 生成：成功（8 维评分，平均分=50）
- 报告保存：analysis_records id=22, score=50
- fact_errors：0（C-1 的 residential 幻觉问题未复现）
- 退款/失败链路：未触发
- P2：0，P3：0
- P0：初始 1 条假阳性「周边客群以高校」

### P0 假阳性二次收窄

- 移除全局「客群」marker
- 新增窄规则：周边/附近+客群、客群开头截断片段、裸泛称「写字楼/高校」
- 新增 T-P0F-13 / T-P0F-14 / T-P0F-15
- fact guard 从 57 PASS 增至 61 PASS（C-2 时）→ 76 PASS（Phase 4B-1）

### 历史基线

- python -m compileall backend：PASS
- python backend/tests/check_industry_rigor_rules.py：1876 PASS, 0 FAIL
- python backend/tests/check_report_fact_guard.py：76 PASS, 0 FAIL
- KNOWN_RULE_GAPS：(none)
- P0/P2/P3：warning-only，P1 暂缓

### 当前状态

- 未提交、不 push
- 前端未启动
- 不要再次调用 AMap/LLM，除非用户明确授权下一次真实报告
- 既有 diff (vite.config.js) 不处理
- 临时产物 (tmp_report_*) 不处理


## Phase 4B-1 代码侧审核通过

- report_fact_guard.py 新增 validate_report_fact_consistency 纯函数（仅依赖 json/re）
- main.py 内联逻辑抽取完毕，残留 import re as _re 已清除
- check_report_fact_guard.py P4 10 用例，importlib 加载，不 import main
- fact guard: 76 PASS, 0 FAIL
- industry: 1876 PASS, 0 FAIL

## Phase 2 历史（餐饮+零售裸奔收口，已过期）

已完成 7/7 master req_kw=True 收口 + 低频目的零售 low_freq_retail 通车。
Phase 2B: 中餐正餐 050100；Phase 2D: 异国_中高端正餐 050100/050200；
Phase 2F: 烘焙甜品 050600；Phase 2H/2J: 低频目的零售 060100/060400。
## Phase 2J 审核状态

当前处于“报告精准度规则体系 + 样本库 + 真实链路脱水校验”阶段。

已完成：
- 方案 C 最小端到端真实报告验收已跑过 1 次：AMap/LLM 链路可用，fact_errors 正确拦截 `stats_200m.residential=0 but report says 7个小区`，报告未保存并触发退款链路。
- P0/P2/P3 继续保持 warning-only；P1 暂缓。
- P0 泛称/描述性前缀假阳性已修补，并增加“米内无”不误杀“米内+具名品牌”的回归用例。
- 餐饮与零售高风险 code 裸奔已收口：中餐正餐、异国_中高端正餐、烘焙甜品、低频目的零售均已启用 `require_name_keyword_for_code=True`。
- 低频目的零售 Phase 2J 已打通真实链路：新增 `low_freq_retail` category、脱水函数、business_type rewrite、真实链路 X5c 样本。

最新 Claude Code 验证结果：
- `python -m compileall backend`：PASS
- `python backend/tests/check_industry_rigor_rules.py`：1876 PASS, 0 FAIL, `KNOWN_RULE_GAPS: (none)`
- `python backend/tests/check_report_fact_guard.py`：61 PASS, 0 FAIL

Codex 审核结论：
- Phase 2J 的方向正确：没有扩大 `SHOPPING_KEEP`，而是通过独立 `low_freq_retail` 避免污染 shopping 大类。
- 真实链路测试 X5c 使用 `sim_full_chain()`，覆盖从 AMap type 到 rewrite、dewater、rigor 分类的关键路径。
- 当前 Codex PowerShell 环境没有 `python`/`py` 命令，无法独立复跑测试；以 Claude Code 已跑通结果为当前基线，并建议新窗口优先复跑。

当前禁止/未做事项：
- Phase 2J 未调用 AMap API。
- Phase 2J 未调用 LLM API。
- 未启动前端。
- 未提交，不 push。
- 不处理 `frontend/vite.config.js` 既有 diff。
- 不处理 `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时产物。

下一步建议：
1. 新窗口先复核 Phase 2J diff 并复跑三项验证。
2. 若验证保持通过，进入 Phase 3A：业务入口映射完整性测试和高风险 invariant 测试。
3. 真实报告复验 C-2 只有在用户再次明确授权 AMap API 和 LLM API 后才执行。

# 址得选项目状态

## 当前阶段

项目处于”报告精准度规则体系重构 + 样本库建设”阶段。当前最高优先级仍是报告精准度。

Guard 体系（v1.1.2）已推送 GitHub。方案 C 最小端到端真实报告验收已完成。

当前不生成真实报告，不启动前端，不改 UI/PDF/端口/数据库 schema，不改 AMap API 调用方式，除非用户明确要求进入对应验收。

产品定位必须保持：**址得选是全国商铺选址初筛参考工具，不是决策平台**。

## 2026-05-15 历史：方案 C 端到端验收 + P0 小修补强（已过期）

### 方案 C 执行记录

| 项目 | 值 |
|---|---|
| 业态 | 药店 |
| 地址 | 陕西省宝鸡市渭滨区经二路138号 |
| 经纬度 | lng=107.148, lat=34.362 |
| AMap API | 已调用，采集/脱水成功 |
| LLM API | 已调用，8维评分生成成功 |
| 前端 | 未启动 |
| 提交/push | 未执行 |

### 方案 C 结果

- AMap/LLM 链路跑通。
- **报告未保存** — fact_errors hard-error 正确拦截。
- hard-error 内容：`stats_200m.residential=0 but report says 7个小区`（LLM 数字幻觉）。
- 退款/失败链路已触发，user_id=23 退款成功。
- **结论：Guard hard-error 链路有效，真实报告未通过保存验收。**

### Guard 表现

- **P0**：4 条 warning（1 真阳性 + 3 假阳性）
  - 真阳性：`公园路店`
  - 假阳性：`米内无任何同类药店` / `公里商圈内同类药店` / `无大型商圈或购物商场`
- **P2**：0 条
- **P3**：0 条
- P0/P2/P3 继续 warning-only。

### P0 假阳性小修（已完成）

- 修改：`backend/services/poi_name_guard.py` + `backend/tests/check_report_fact_guard.py`
- 新增：`_DESCRIPTIVE_MARKERS`（`米内无`/`商圈内`/`无任何`）+ `无大型` 开头检测
- 关键设计：用 `”米内无”` 而非 `”米内”`，避免误杀 `”米内有XX店”` 含具名品牌候选
- 新增测试：T-P0F-8 ~ T-P0F-12（5 个）

### 最新测试基线

- `python -m compileall backend`：通过
- `python backend/tests/check_report_fact_guard.py`：**61 PASS, 0 FAIL**
- `python backend/tests/check_industry_rigor_rules.py`（历史）：1598 PASS, 0 FAIL（当前 1876 PASS）
- `KNOWN_RULE_GAPS`：(none)

### 当前仍未处理

- 未再次生成真实报告
- 未再次调用 AMap/LLM API
- 未启动前端
- 未提交，不 push
- 不处理既有 diff：`industry_config.py` / `check_industry_rigor_rules.py` / `vite.config.js`
- 不处理临时产物：`tmp_latest_report_text.txt` / `tmp_report_images/` / `tmp_report_pages/`

### 下一步建议

- 等待用户明确授权后，进入”方案 C-2：第二次最小端到端真实报告复验”
- C-2 已完成：P0 初始 1 条假阳性已二次收窄修复
- C-2 已执行 1 次真实请求，报告保存 id=22
- 如再次出现 residential 或 stats hard-error，优先记录为 LLM 数字幻觉

## 2026-05-14 历史：用户十节精准度框架 + 差距分析（已过期）

用户已给出完整的精准度目标拆解（十节框架）。Claude Code 逐项对照当前进展，核心发现：

**四层目标已有规则，但精准度参差不齐。** `classify_poi_rigor()` 四分类已实现，14 master 各有四套规则。

**最大结构性风险**：餐饮 5 组 master（中餐正餐/火锅_烧烤/异国风味/茶饮咖啡/烘焙甜品）的 amap_codes 仍用宽 code（050100/050200/050500/050600），未启用 `require_name_keyword_for_code=True`。

**Sample Bank 现状**：20 业态中 6 个 complete_candidate，14 个 partial（缺 substitute 样本）。canonical 1598 PASS 0 FAIL。

**下一步最有效动作**：先给餐饮剩余 5 组 master 加上 `require_name_keyword_for_code=True` 或收窄 code，再补 14 组样本库的 substitute 列。

## 2026-05-14 历史阶段更新（P0/P2/P3 收口，已过期）

本轮报告事实校验层 P0/P2/P3 已完成并收口。当前仍不生成真实报告、不启动前端、不提交、不 push。下一阶段建议先做“真实报告前 guard 总体验收方案”，不要继续扩大规则面。

最新 Codex / Claude Code 复核确认：

- `python -m compileall backend` 通过。
- `python backend/tests/check_report_fact_guard.py` 通过：`42 PASS, 0 FAIL`。
- `python backend/tests/check_industry_rigor_rules.py`（历史）：1598 PASS, 0 FAIL。当前：1876 PASS。
- `KNOWN_RULE_GAPS: (none)`。
- 未生成真实报告。
- 未启动前端。
- 未提交、未 push。

报告事实校验层当前状态：

- P0 已完成：POI 名称引用校验，warning-only。
  - 函数：`check_poi_name_hallucination(full_text, real_data, strict=False)`
  - 写入：`result["_poi_name_warnings"]`
- P1 暂缓：旧口径 `competitors_*` 误用检测。当前所有业态严谨框架状态下暂不实现，待无-rigor 业态或旧字段再次暴露时再处理。
- P2 已完成：`substitute_list` / `traffic_anchor_list` 被报告误写成竞品语境的校验，warning-only。
  - 函数：`check_poi_context_mismatch(full_text, real_data)`
  - 写入：`result["_poi_context_warnings"]`
- P3 已完成：直接竞品数量膨胀校验，warning-only。
  - 函数：`check_direct_competitor_count_mismatch(full_text, real_data)`
  - 只检查 `direct_competitors_200m/500m/1000m`
  - 只在“竞品语境 + 明确半径 + 精确阿拉伯数字 + reported > expected”时 warning
  - 写入：`result["_direct_competitor_count_warnings"]`

三类 guard 均保持 warning-only：

- 打印 warning 日志。
- 写入 `result` JSON。
- 不加入 `fact_errors`。
- 不 `raise ValueError`。
- 不影响报告保存/退款链路。

当前 P0/P2/P3 文件状态：

- 新增：`backend/services/poi_name_guard.py`
- 新增：`backend/tests/check_report_fact_guard.py`
- 修改：`backend/main.py`

当前工作区提醒：

- `backend/tests/check_industry_rigor_rules.py` 有既有 diff，不要处理、不要回滚、不要格式化。
- `backend/prompts/industry_config.py` 有既有 diff，不要处理、不要回滚、不要格式化。
- `frontend/vite.config.js` 有既有 diff，不要处理。
- `PROJECT_RULES.md`、`PROJECT_STATE.md`、`WORKING_SET.md`、`NEXT_SESSION_PROMPT.md` 是交接文档，可由 Codex 更新。
- `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时报告产物不要处理。

下一阶段建议：

先进入“真实报告前 guard 总体验收方案”只读设计，不直接生成真实报告。需要用户明确授权后，才选择 1-3 个真实样本进入报告验收。验收重点包括：

- `_poi_name_warnings`
- `_poi_context_warnings`
- `_direct_competitor_count_warnings`
- `fact_errors` 是否仍只处理 hard-error
- 报告是否保存成功
- 是否触发退款/失败链路
- false positive / false negative 记录

注意：下方旧章节中的 P2 下一步、`17 PASS`、`1511 PASS`、`1391 PASS`、`1291 PASS`、Laundry 下一步等均为历史状态；继续工作时以本节最新状态为准。

## 2026-05-14 历史阶段更新（P0/P2 交接，已过期）

本轮 Sample Bank 保守补样本阶段已经收口，并开始进入“报告事实校验层”建设。当前仍不生成真实报告、不启动前端、不提交、不 push。

最新 Codex 审核确认：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- Sample Bank canonical（历史）：1598 PASS, 0 FAIL。
- `KNOWN_RULE_GAPS: (none)`。
- `python backend/tests/check_report_fact_guard.py` 通过：`17 PASS, 0 FAIL`。
- P0 POI 名称引用校验已接入 `backend/main.py`，当前为 warning-only：
  - 写入 `result["_poi_name_warnings"]`
  - 打印 `[SSE Guard] POI名称引用告警`
  - 不加入 `fact_errors`
  - 不 `raise ValueError`
  - 不影响报告保存/退款流程
- P1 旧口径 `competitors_*` 误用检测已审计，当前暂缓实现。
- 下一步是 P2：`substitute_list` / `traffic_anchor_list` 被报告误写成竞品的 warning-only 语境校验。

当前 Sample Bank 状态：

- `complete_candidate` 仍只有 7 个：
  - Snack Shop：`d=13 nd=10 s=5 a=5 i=5`
  - Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5`
  - Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5`
  - Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5`
  - Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5`
  - Convenience：`d=10 nd=10 s=5 a=5 i=5`
  - Fresh Produce：`d=10 nd=10 s=5 a=5 i=5`
- 其余 13 个保持 `partial`，均达到 `d>=10 nd>=10 s=0 a=5 i=5`：
  - Pharmacy / Tobacco-Liquor / Daily Goods
  - Beauty / Pet / Fitness
  - Education / Laundry / Clinic
  - Bar / KTV / Internet Cafe
  - Immersive Social：`d=22 nd=10 s=0 a=5 i=5`

P0 已完成文件：

- 新增：`backend/services/poi_name_guard.py`
- 新增：`backend/tests/check_report_fact_guard.py`
- 修改：`backend/main.py`

当前工作区提醒：

- `backend/prompts/industry_config.py` 仍有既有 diff，不要处理、不要回滚、不要格式化。
- `frontend/vite.config.js` 仍有既有 diff，不要处理。
- `PROJECT_RULES.md`、`PROJECT_STATE.md`、`WORKING_SET.md`、`NEXT_SESSION_PROMPT.md` 可能是未跟踪交接文档，按交接用途保留。
- `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时报告产物不要纳入本轮处理，除非用户明确要求清理。

角色边界再次确认：

- Claude Code 是代码执行者。
- Codex 是审核者和指挥者。
- Codex 不直接接手实现代码；只读审计、复核 diff/测试结果、给 Claude Code 下一步指令。
- 交接文档可由 Codex 直接更新。

下一步建议：

进入 P2：报告事实校验层 `anchor/substitute 被误写成竞品` warning-only 实现。执行前需继续坚持：

- 只允许 Claude Code 修改 `backend/services/poi_name_guard.py`、`backend/tests/check_report_fact_guard.py`、`backend/main.py`。
- 不改 `backend/tests/check_industry_rigor_rules.py`。
- 不改 `backend/prompts/industry_config.py`。
- 不改 `frontend/vite.config.js`。
- 不生成真实报告。
- 不启动前端。
- 不提交、不 push。

注意：下方旧章节中的 `1511 PASS`、`1391 PASS`、`1291 PASS`、Laundry 下一步等均为历史状态；继续工作时以本节最新状态为准。

## 2026-05-14 最新阶段更新（以本节为准）

本轮已完成零售组与专业生活服务组的多轮 Sample Bank 保守补样本审核，并进入社区基础服务组。当前仍处于本地 canonical 样本防线建设阶段，不生成真实报告、不启动前端、不改 UI/PDF/端口/数据库 schema、不改 AMap API 调用方式。

最新 Codex 审核确认：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical 自测：`1511 PASS, 0 FAIL`。
- `KNOWN_RULE_GAPS: (none)`。
- 未生成真实报告。
- 未启动前端。
- 本轮代码执行仅围绕 `backend/tests/check_industry_rigor_rules.py` 的 canonical 样本补强；未要求修改业务规则。

已完成的 `complete_candidate`：

- Snack Shop：`d=13 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5 [complete_candidate]`
- Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5 [complete_candidate]`
- Convenience：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Fresh Produce：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`

已保守补强但仍保持 `partial` 的组：

- Pharmacy：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Tobacco/Liquor：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Daily Goods：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Beauty：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Pet：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Fitness：`d=10 nd=10 s=0 a=5 i=5 [partial]`
- Education：`d=10 nd=10 s=0 a=5 i=5 [partial]`

这些组保持 `partial` 的原因主要是当前 substitute 规则不适用于对应业态或为空壳规则。当前策略是不硬凑 substitute、不新增 `KNOWN_RULE_GAPS`、不改业务规则。

当前已审核但尚未执行的下一步：

- Laundry 审计已通过，建议执行保守补样本：
  - direct 新增：洗衣房、洗衣馆、干洗馆，`type_code=生活服务;洗衣店`
  - anchor 新增：住宅小区/公寓/写字楼/小学/中学，其中小学/中学必须使用 `科教文化服务;学校`
  - irrelevant 新增：驾校/职业培训/职业培训学校/医院/药店，使用 `050300` 绕开脱水，验证 irrelevant blacklist
  - 不补 substitute，不改规则，状态目标：`Laundry: d=10 nd=10 s=0 a=5 i=5 [partial]`

注意：下方旧章节中的 `1391 PASS`、`1291 PASS`、零售组下一步等属于历史基线描述；继续工作时以本节最新状态为准。

## 2026-05-13 历史阶段更新

本轮已完成餐饮 known_gap 收口，并进入 Sample Bank complete_candidate 铺样本阶段。

最新 Codex 审核确认：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical 自测：`1391 PASS, 0 FAIL`。
- `KNOWN_RULE_GAPS: (none)`。
- `frontend/src/services/amapData.js` 无 diff。
- 未生成真实报告。
- 未启动前端。

已完成的餐饮 complete_candidate：

- Snack Shop：`d=13 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5 [complete_candidate]`
- Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5 [complete_candidate]`

本轮规则侧新增/收紧点：

- `精品茶饮咖啡`：收紧 `050500` 裸 direct，甜品/冰淇淋/便利店/火锅/烧烤边界已收口。
- `中餐正餐`：火锅/烧烤/茶饮/咖啡边界已收口。
- `火锅_烧烤`：开启 `require_name_keyword_for_code`，并补充明显无关项 irrelevant 黑名单；没有扩大 direct。
- `烘焙甜品`：茶饮/咖啡/奶茶 substitute 与便利店/火锅/烧烤 not-direct/irrelevant 边界已收口。
- `便利店`：最后一个 sub-type routing known_gap 已确认是测试 type_code 不真实导致，仅修测试，不改规则。

下一阶段建议进入零售组 complete_candidate 规划，但仍然每轮只处理一个 subtype，先审计、再执行：

1. Convenience
2. Fresh Produce
3. Pharmacy
4. Tobacco/Liquor
5. Daily Goods

注意：下方旧章节中的 `1291 PASS`、known_gap 列表等属于历史基线描述；继续工作时以本节最新状态为准。

## 最新审核基线

最近一次 Codex 独立审核确认：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical 自测：`1291 PASS, 0 FAIL`。
- Sample Bank v1 已成为 partial baseline。
- 14/14 master 已消除高风险 broad code 裸 direct 风险。
- 未生成真实报告。
- 未启动前端。
- `frontend/src/services/amapData.js` 无 diff。
- `backend/tools/` 无 `fix_sample_bank*.py` 临时脚本残留。

注意：工作区里存在历史脏文件，不要擅自 revert。`backend/services/amap_service.py`、`backend/prompts/industry_config.py`、`backend/prompts/location_analysis.py` 有前序阶段业务改动；前端部分文件也可能有历史脏状态。除非用户明确要求，不要处理这些历史脏文件。

## 已完成主线

### 1. 底层规则引擎

`classify_poi_rigor()` 已支持：

- `require_name_keyword_for_code`
- `substitute_before_direct`
- `strict_exclude_names`
- subtype 选择与继承
- master bool 字段继承：
  - `require_name_keyword_for_code`
  - `substitute_before_direct`
- master 排除词继承：
  - `strict_exclude_names`
  - `exclude_names`
- subtype 的 `name_keywords` / `amap_codes` 优先使用 subtype 自身配置，避免盲目合并导致口径变宽。

高风险 AMap 大类或宽类 code 不允许裸直通 direct。若必须使用，必须配合名称关键词锁定。

### 2. 小吃店 direct 误判修复

`刚需快餐小吃` 已收紧：

- direct code 从 `050000/050300` 收紧到 `050300`。
- 开启 `require_name_keyword_for_code=True`。
- 开启 `substitute_before_direct=True`。
- direct 关键词去掉单字“面/皮/粉/饭/包/粥”。
- 鸭脖、卤味、炸鸡、汉堡等进入 substitute，不进 direct。

已确认：肯德基、麦当劳、必胜客、普通中餐厅不进 direct；擀面皮、凉皮、麻辣烫等进 direct；绝味鸭脖、正新鸡排、汉堡等进 substitute。

### 3. 脱水增强

已增强医院、药店、住宅、便利店等脱水：

- 医院强排除：体检、整形美容、眼科、视光、助听器、医美、理疗等。
- 医院主体归并：门诊部、发热门诊、住院部、急诊中心、创伤中心等归并到医院主体，不重复计数。
- 住宅排除产业园、科技园、写字楼、办公楼、商务大厦等。
- 便利店排除美甲、手机维修、彩票、黄金回收、OPPO/华为体验店、快递驿站等。

### 4. subtype 深化

已深化的复合 master：

- `高频刚需零售`
  - `supermarket`
  - `fresh`
  - `pharmacy2`
  - `tobacco_liquor`
  - `daily_goods`
- `专业生活服务`
  - `beauty`
  - `pets`
  - `fitness`
- `社区基础服务`
  - `education`
  - `laundry`
  - `clinic`
- `夜经济娱乐`
  - `bar`
  - `ktv`
  - `internet_cafe`
- `沉浸式社交娱乐`
  - `jubensha`
  - `escape_room`
  - `billiards`
  - `board_game`
  - `arcade_vr`

### 5. 真实 POI 分类/脱水链路

已新增 backend category：

- `education_training`
- `laundry`
- `clinics`
- `fitness`
- `fresh_retail`
- `tobacco_liquor`
- `immersive_entertainment`

已新增脱水函数：

- `is_real_training`
- `is_real_laundry`
- `is_real_clinic`
- `is_real_fitness`
- `is_real_fresh_retail`
- `is_real_tobacco_liquor_retail`
- `is_real_immersive_entertainment`

已更新 `TYPE_CLASSIFIERS`、`ALL_CATEGORY_KEYS`、`CATEGORY_LABELS` 和采集循环脱水逻辑。

已打通 shopping 业务感知改写：

- 生鲜/水果/蔬菜/菜店/鲜果类业务，名称命中生鲜规则时：`shopping -> fresh_retail`
- 烟酒/名烟/名酒/酒行/酒类业务，名称命中烟酒规则时：`shopping -> tobacco_liquor`

已打通沉浸式真实链路：

- `体育休闲服务;娱乐场所 -> immersive_entertainment`
- 裸 `080000` 仍不展示，不映射到 immersive。
- `体育休闲服务;KTV/酒吧/网吧 -> bars`，夜经济娱乐 direct 不受影响。
- KTV剧本杀、酒吧密室、网吧VR、电竞酒店剧本杀、麻将馆桌游等混名样本在真实链路中 `dewater_drop`。
- 棋牌室、桌游棋牌室仍可在桌游/轰趴业务下 direct。

### 6. 住宿业态规则重构

`商务酒店` 和 `民宿青旅` 已消除 `100000` 裸 direct 风险：

- 均开启 `require_name_keyword_for_code=True`。
- 均开启 `substitute_before_direct=True`。
- 已补 direct / not direct / substitute / excluded 边界测试。
- 已补真实链路测试，使用真实 type_code：`住宿服务` / `100000`。

### 7. anchor 显式测试

`backend/tests/check_industry_rigor_rules.py` 已新增 Section U：

- 这是 `traffic_anchor_rules` 规则层测试。
- 手工传入 cat/type_code，验证 anchor 优先级且不被 direct/substitute 污染。
- 不代表真实采集链路；真实链路测试在 M/P/S/W 等章节。

### 8. 报告 prompt 初筛定位

`backend/prompts/location_analysis.py` 已做第一轮补强：

- 系统角色改为“商业选址初筛 AI 分析员”。
- 明确“不提供投资建议，不替用户做决策，需结合实地考察验证”。
- 竞争环境段要求仅基于 `direct_competitors` 做竞争判断。
- `substitute` 和 `traffic_anchors` 只能定性提及，不能计入竞品数量或竞争评分。

### 9. Sample Bank v1 partial baseline

`backend/tests/check_industry_rigor_rules.py` 已新增 X-AA Sample Bank 第一批稳定样本。

当前状态：

- canonical：`1291 PASS, 0 FAIL`
- 没有 complete 组。
- 状态只使用：
  - `partial`
  - `known_gap`
- `check_sub()` 严格断言 `r == "substitute"`。
- `sim_full_chain()` 无 `cat_override/default_cat`，走真实链路。
- `backend/tools/` 无临时批量修复脚本。

当前 Sample Bank 状态：

- Snack Shop：partial
- Tea/Coffee：known_gap
- Chinese Restaurant：known_gap
- Hotpot/BBQ：known_gap
- Bakery/Dessert：known_gap
- Convenience：known_gap
- Fresh Produce：partial
- Pharmacy：partial
- Tobacco/Liquor：partial
- Daily Goods：known_gap
- Beauty：partial
- Pet：partial
- Fitness：partial
- Education：partial
- Laundry：partial
- Clinic：partial
- Bar：partial
- KTV：partial
- Internet Cafe：partial
- Immersive Social：partial

当前 known gaps：

1. 精品茶饮咖啡：甜品店/冰淇淋店/便利店/火锅店/烧烤店边界需要收紧。
2. 中餐正餐：火锅店/烧烤店/茶饮店/咖啡店边界需要收紧。
3. 火锅烧烤：茶饮店/咖啡店/西餐/日料/中餐馆边界需要收紧。
4. 烘焙甜品：便利店/火锅店/烧烤店/茶饮店边界需要收紧。
5. 便利店：快餐/咖啡/茶饮/炸鸡 substitute 路由存在类型不匹配，需要单独审查，不要直接放宽规则。

## 当前未完成事项

### A. 完整样本库未铺满

Sample Bank v1 只是 partial baseline，不是完整样本库。

完整目标仍是每个业态或 subtype：

- direct 正例至少 10 个
- not direct 反例至少 10 个
- substitute 正例至少 5 个
- anchor 正例至少 5 个
- irrelevant 正例至少 5 个

下一步不要全量铺开。建议每轮只处理 1 个 known_gap 组，保持 `0 FAIL`。

### B. 报告事实校验层未全面进入

已有基础事实校验和 prompt 约束，但还未系统完成：

- has_rigor=True 时禁止 LLM 使用旧口径 `competitors_*`。
- 报告正文中 direct/substitute/anchor/医院/学校/住宅等数量必须和 `real_data` 对齐。
- substitute 必须明确为“非直接竞品”。
- anchor 必须明确为“客流锚点，不是竞品”。
- 数字不一致时拦截、退款、不保存正式报告的完整链路还需验收。

### C. 真实报告验收未进入

尚未生成真实报告，符合当前阶段要求。

真实报告验收应放在本地样本库和事实校验层之后，选择 1-3 个真实样本检查：

- direct 列表是否无明显错类
- substitute 是否未混进 direct
- anchor 是否未混进 direct
- irrelevant 是否被剔除
- 三层 200m/500m/1000m 数字和明细是否一致
- LLM 文案是否没有引用旧口径
- 是否始终强调初筛参考、需线下验证

### D. PDF/HTML/页面口径一致性未进入

当前阶段 UI/PDF/HTML 展示降级，不主动处理。

## 当前工作树提醒

- 本轮未创建 git commit。
- 当前工作树存在历史脏文件，不要随意 revert。
- `frontend/src/services/amapData.js` 当前无 diff。
- 不要处理历史前端脏文件或临时报告文件，除非用户明确要求。
