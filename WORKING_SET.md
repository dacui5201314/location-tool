# 最新工作集（2026-05-15 C-2 收口，以本节为准）

## C-2 已完成

- 业态：刚需快餐小吃 | 地址：北京市海淀区中关村大街19号
- AMap/LLM 链路跑通，报告保存 id=22, score=50
- fact_errors=0，退款未触发
- P0 初始 1 条假阳性 → 已二次收窄修复
- P2/P3=0

## 当前有效基线

- python -m compileall backend：PASS
- python backend/tests/check_industry_rigor_rules.py：1876 PASS, 0 FAIL
- python backend/tests/check_report_fact_guard.py：61 PASS, 0 FAIL
- KNOWN_RULE_GAPS：(none)

## 不要处理

- frontend/vite.config.js 既有 diff
- tmp_latest_report_text.txt / tmp_report_images / tmp_report_pages
- 不提交、不 push
- 不调用 AMap/LLM 除非用户再次授权

## 当前目标

Phase 3B 已完成并通过 Codex 复核。Sample Bank 已从打印状态表升级为结构化、可校验台账。C-2 已通过。下一步等待用户授权新任务或下一次真实报告。

## 当前有效基线

- python -m compileall backend：PASS
- check_industry_rigor_rules.py：1876 PASS, 0 FAIL
- check_report_fact_guard.py：61 PASS, 0 FAIL
- KNOWN_RULE_GAPS: (none)
- P0/P2/P3：warning-only
- P1：暂缓

## 锁住的 invariant

- Section A：43 entries / 14 masters / 14 rigor / 四类规则齐全（硬断言）
- Section AB：逐 source (master+subtype) 扫描 forbidden/risky codes
- Section AC：低频目的零售 real chain sim_full_chain invariant
- Sample Bank Ledger：8 个 complete_candidate 全量硬断言，14 个 partial 硬断言 d/nd/a/i 且必须有 partial_reason
- partial_reason：当前业态无稳定全国通用 substitute 规则时，不为凑数污染 direct/substitute 边界

## 本轮相关改动文件

后端规则/链路：
- backend/prompts/industry_config.py
- backend/services/amap_service.py
- backend/services/poi_name_guard.py

测试：
- backend/tests/check_industry_rigor_rules.py
- backend/tests/check_report_fact_guard.py

## 不要处理

- frontend/vite.config.js 既有 diff
- tmp_latest_report_text.txt / tmp_report_images / tmp_report_pages
- 不提交、不 push
- 不调用 AMap/LLM API（未授权）

## 2026-05-14 历史（已过期）

角色边界：

- Claude Code 执行代码修改。
- Codex 负责审核 Claude Code 输出并给指令。
- Codex 不直接实现后端业务逻辑。
- Codex 可直接更新交接文档。

建议下一步 Claude Code 指令主题：

`方案 C：一次最小端到端真实报告验收`（历史，C-1 + C-2 均已完成，勿执行）

执行边界：

- 需要用户明确授权后才能调用 AMap API / LLM API。
- 不启动前端。
- 可启动后端或使用已有后端。
- 用 curl/httpx 发起 1 次真实分析请求。
- 不提交、不 push。
- 不处理、不回滚、不格式化既有 diff。

验收重点：

- 三类 warning 字段是否出现在 `result` 中并保持 warning-only。
- `fact_errors` 是否仍只处理 hard-error。
- 报告是否保存成功。
- 是否触发退款/失败链路。
- 若出现 warning，记录 false positive / false negative。
- 当前不建议升级 hard-error，至少需要更多真实样本观察。

## 2026-05-14 历史工作集更新（P0/P2/P3 收口，已过期）

当前 Sample Bank 保守补样本已经收口，报告事实校验层 P0/P2/P3 已完成并收口。旧章节中的 `17 PASS`、`1511 PASS`、`1391 PASS`、`1291 PASS`、Laundry 下一步、P2 下一步等均为历史信息；继续工作以本节为准。

最新基线：

- `python -m compileall backend` 通过。
- `python backend/tests/check_report_fact_guard.py` 通过：`42 PASS, 0 FAIL`。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical（历史）：1598 PASS, 0 FAIL（当前 1876 PASS）。
- `KNOWN_RULE_GAPS: (none)`。
- 未生成真实报告。
- 未启动前端。
- 未提交、未 push。

当前报告事实校验层状态：

- P0 已完成：POI 名称引用校验，warning-only。
  - 函数：`check_poi_name_hallucination(full_text, real_data, strict=False)`
  - 写入：`result["_poi_name_warnings"]`
- P1 暂缓：旧口径 `competitors_*` 误用检测。
- P2 已完成：substitute/anchor 被误写成竞品语境，warning-only。
  - 函数：`check_poi_context_mismatch(full_text, real_data)`
  - 写入：`result["_poi_context_warnings"]`
- P3 已完成：直接竞品数量膨胀，warning-only。
  - 函数：`check_direct_competitor_count_mismatch(full_text, real_data)`
  - 写入：`result["_direct_competitor_count_warnings"]`
  - 仅在 reported > expected 时 warning，不抓少报。

当前活跃文件：

- `backend/services/poi_name_guard.py`
  - P0/P2/P3 warning-only 纯函数。
- `backend/tests/check_report_fact_guard.py`
  - P0/P2/P3 自测，当前 `42 PASS, 0 FAIL`。
- `backend/main.py`
  - 已接入 P0/P2/P3，接入点均在 `if fact_errors:` 之前。
  - 三类 warning 均只写入 `result`，不加入 `fact_errors`，不 `raise`。

工作区提醒：

- `backend/tests/check_industry_rigor_rules.py` 有既有 diff，不要处理。
- `backend/prompts/industry_config.py` 有既有 diff，不要处理。
- `frontend/vite.config.js` 有既有 diff，不要处理。
- `PROJECT_*.md`、`WORKING_SET.md`、`NEXT_SESSION_PROMPT.md` 属于交接文档，可由 Codex 更新。
- `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时产物不要处理。

角色边界：

- Claude Code 执行代码修改。
- Codex 负责审核 Claude Code 输出并给指令。
- Codex 不直接实现后端业务逻辑。
- Codex 可直接更新交接文档。

建议下一步 Claude Code 指令主题：

`报告事实校验层 P0/P2/P3 收口后的真实报告前 guard 总体验收方案`

执行边界：

- 只读设计，不改代码。
- 不生成真实报告，除非用户明确授权。
- 不启动前端。
- 不提交、不 push。
- 不处理、不回滚、不格式化既有 diff。

方案输出重点：

- 验证三类 warning 字段在真实报告生成链路中的表现。
- 建议验收样本数量：1-3 个。
- 检查 `_poi_name_warnings` / `_poi_context_warnings` / `_direct_competitor_count_warnings`。
- 检查 `fact_errors` 是否仍只处理 hard-error。
- 检查报告是否仍保存成功、是否触发退款/失败链路。
- 建立 false positive / false negative 记录模板。
- 当前默认不建议升级 hard-error，先观察 warning。

## 2026-05-14 历史工作集更新（P0/P2 交接，已过期）

当前 Sample Bank 保守补样本已经收口，报告事实校验层已开始建设。旧章节中的 `1511 PASS`、`1391 PASS`、`1291 PASS`、Laundry 下一步等均为历史信息；继续工作以本节为准。

最新基线：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical（历史）：1598 PASS, 0 FAIL（当前 1876 PASS）。
- `KNOWN_RULE_GAPS: (none)`。
- `python backend/tests/check_report_fact_guard.py` 通过：`17 PASS, 0 FAIL`。
- 未生成真实报告。
- 未启动前端。
- 未提交、未 push。

当前 Sample Bank 状态：

- `complete_candidate` 7 个：
  - Snack Shop：`d=13 nd=10 s=5 a=5 i=5`
  - Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5`
  - Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5`
  - Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5`
  - Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5`
  - Convenience：`d=10 nd=10 s=5 a=5 i=5`
  - Fresh Produce：`d=10 nd=10 s=5 a=5 i=5`
- `partial` 13 个，均达到 `d>=10 nd>=10 s=0 a=5 i=5`：
  - Pharmacy / Tobacco-Liquor / Daily Goods
  - Beauty / Pet / Fitness
  - Education / Laundry / Clinic
  - Bar / KTV / Internet Cafe
  - Immersive Social：`d=22 nd=10 s=0 a=5 i=5`

当前报告事实校验层状态：

- P0 POI 名称引用校验已实现 warning-only。
- P0 新增纯函数文件：`backend/services/poi_name_guard.py`。
- P0 新增测试文件：`backend/tests/check_report_fact_guard.py`。
- P0 已接入 `backend/main.py`，只写 `result["_poi_name_warnings"]`，不硬阻断。
- P1 旧口径 `competitors_*` 误用检测已审计，当前暂缓。
- P2 是下一步：检查 `substitute_list` / `traffic_anchor_list` 中的名称是否被报告写成竞品语境，先 warning-only。

当前活跃文件：

- `backend/services/poi_name_guard.py`
  - P0 名称引用 warning-only 校验。
  - 下一步 P2 可在此追加 `check_poi_context_mismatch(report_text, real_data) -> list[str]`。
- `backend/tests/check_report_fact_guard.py`
  - P0 自测，当前 `17 PASS, 0 FAIL`。
  - 下一步追加 P2 测试。
- `backend/main.py`
  - 已接入 P0 warning-only。
  - 下一步 P2 接入点应在 P0 warning 之后、`if fact_errors:` 之前。
- `backend/tests/check_industry_rigor_rules.py`
  - Sample Bank canonical 已收口，当前不要再改，除非用户明确要求继续扩展样本。

工作区提醒：

- `backend/prompts/industry_config.py` 有既有 diff，不要处理。
- `frontend/vite.config.js` 有既有 diff，不要处理。
- `PROJECT_*.md`、`WORKING_SET.md`、`NEXT_SESSION_PROMPT.md` 属于交接文档，可由 Codex 更新。
- `tmp_latest_report_text.txt`、`tmp_report_images/`、`tmp_report_pages/` 等临时产物不要处理。

角色边界：

- Claude Code 执行代码修改。
- Codex 负责审核 Claude Code 输出并给指令。
- Codex 不直接实现代码，不接手修改后端逻辑。
- Codex 可直接更新交接文档。

建议下一步 Claude Code 指令主题：

`报告事实校验层 P2：anchor/substitute 被误写成竞品 warning-only 实现`

执行边界：

- 只允许修改：
  - `backend/services/poi_name_guard.py`
  - `backend/tests/check_report_fact_guard.py`
  - `backend/main.py`
- 不修改：
  - `backend/tests/check_industry_rigor_rules.py`
  - `backend/prompts/industry_config.py`
  - `frontend/vite.config.js`
- 不生成真实报告。
- 不启动前端。
- 不提交、不 push。

## 2026-05-14 最新工作集更新（以本节为准）

当前 Sample Bank 工作已从餐饮组推进到社区基础服务组。最新基线：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical：`1511 PASS, 0 FAIL`。
- `KNOWN_RULE_GAPS: (none)`。
- 未生成真实报告。
- 未启动前端。
- 本轮主要修改文件：`backend/tests/check_industry_rigor_rules.py`。

当前 Sample Bank 状态重点：

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

当前建议下一步：

执行已审核通过的 `Laundry` 保守补样本，仍只改 `backend/tests/check_industry_rigor_rules.py`：

1. direct 增补 `洗衣房`、`洗衣馆`、`干洗馆`，`type_code=生活服务;洗衣店`。
2. anchor 增补 `住宅小区/公寓/写字楼/小学/中学`；小学/中学必须使用 `科教文化服务;学校`，不要用 `141200`。
3. irrelevant 增补 `驾校/职业培训/职业培训学校/医院/药店`，`type_code=050300`。
4. 不补 substitute，不新增 `KNOWN_RULE_GAPS`，不改规则。
5. 目标状态：`Laundry: d=10 nd=10 s=0 a=5 i=5 [partial]`。

继续禁止：

- 不生成真实报告。
- 不启动前端。
- 不改 UI/PDF/端口/数据库 schema。
- 不改 AMap API 调用方式。
- 不改 `frontend/src/services/amapData.js`。
- 不处理历史前端脏文件和临时报告文件。
- 不用临时脚本批量重写测试。
- 不为城市、商场、门店、品牌写硬编码特判。

注意：下方旧内容中的 `1391 PASS`、`1291 PASS`、Convenience 下一步等是历史信息；继续工作以本节为准。

## 2026-05-13 历史工作集更新

本轮已完成餐饮 known_gap 收口，并把餐饮五组推进到 `complete_candidate`。

最新基线：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical：`1391 PASS, 0 FAIL`。
- `KNOWN_RULE_GAPS: (none)`。
- `frontend/src/services/amapData.js` 无 diff。
- 未生成真实报告。
- 未启动前端。

当前 Sample Bank 状态重点：

- Snack Shop：`d=13 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Tea/Coffee：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Chinese Restaurant：`d=10 nd=10 s=5 a=5 i=5 [complete_candidate]`
- Hotpot/BBQ：`d=11 nd=13 s=5 a=5 i=5 [complete_candidate]`
- Bakery/Dessert：`d=10 nd=13 s=5 a=5 i=5 [complete_candidate]`
- Convenience：`d=5 nd=10 s=4 a=0 i=0 [partial]`
- Fresh Produce：`d=7 nd=8 s=0 a=0 i=0 [partial]`
- Pharmacy：`d=10 nd=10 s=0 a=0 i=0 [partial]`
- Tobacco/Liquor：`d=10 nd=10 s=0 a=0 i=0 [partial]`
- Daily Goods：`d=6 nd=9 s=0 a=0 i=0 [partial]`

当前建议下一步：

进入零售组 complete_candidate 阶段，但不要一次铺开。下一轮建议只做 `Convenience complete_candidate` 审计：

1. 只读检查 `高频刚需零售` master 与 `supermarket/便利店` subtype。
2. 只读检查 Y1 Convenience 样本。
3. 判断 direct / not-direct / substitute / anchor / irrelevant 分别缺哪些真实链路样本。
4. 先输出方案，不直接改代码。

继续禁止：

- 不生成真实报告。
- 不启动前端。
- 不改 UI/PDF/端口/数据库 schema。
- 不改 AMap API 调用方式。
- 不改 `frontend/src/services/amapData.js`。
- 不处理历史前端脏文件和临时报告文件。
- 不用临时脚本批量重写测试。
- 不为城市、商场、门店、品牌写硬编码特判。

注意：下方旧内容中的 `1291 PASS`、known_gap 列表和“下一步精品茶饮咖啡”是历史信息；继续工作以本节为准。

最新基线：

- `python -m compileall backend` 通过。
- `python backend/tests/check_industry_rigor_rules.py` 通过。
- canonical：`1291 PASS, 0 FAIL`。
- Sample Bank v1：partial baseline，不是完整样本库。

现在不要继续全量铺样本库，不要生成真实报告，不要启动前端。下一步建议只处理 **一个 known_gap 组**，保持小步、可回归、0 FAIL。

## 活跃文件

### `backend/tests/check_industry_rigor_rules.py`

唯一 canonical 本地规则自测脚本。

当前状态：

- A-W：规则体系、真实链路、住宿、anchor、沉浸式等核心测试。
- X-AA：Sample Bank v1 partial baseline。
- 当前总数：`1291 PASS, 0 FAIL`。

关键要求：

- 不要恢复 `cat_override`。
- `sim_full_chain()` 不得有 `default_cat` 或任何 category override。
- `check_sub()` 必须严格断言 `r == "substitute"`。
- 新增样本必须保持 canonical 0 FAIL。
- 如果样本暴露规则问题，先加入 `known_gaps`，不要让测试红。

当前 Sample Bank known gaps：

1. `精品茶饮咖啡`：甜品店/冰淇淋店/便利店/火锅店/烧烤店边界。
2. `中餐正餐`：火锅店/烧烤店/茶饮店/咖啡店边界。
3. `火锅_烧烤`：茶饮店/咖啡店/西餐/日料/中餐馆边界。
4. `烘焙甜品`：便利店/火锅店/烧烤店/茶饮店边界。
5. `便利店`：快餐/咖啡/茶饮/炸鸡 substitute 路由类型不匹配。

### `backend/services/amap_service.py`

核心职责：

- AMap POI 类型分类：`classify_poi_type`
- POI 名称脱水
- category 计数与 `poi_lists`
- 严谨规则分类：`classify_poi_rigor`
- `real_data` 输出

当前重点内容：

- `classify_poi_rigor()` 支持 `require_name_keyword_for_code`、`substitute_before_direct`、`strict_exclude_names`、subtype 继承。
- 新增 category：
  - `education_training`
  - `laundry`
  - `clinics`
  - `fitness`
  - `fresh_retail`
  - `tobacco_liquor`
  - `immersive_entertainment`
- shopping 业务感知改写：
  - 生鲜类：`shopping -> fresh_retail`
  - 烟酒类：`shopping -> tobacco_liquor`
- 沉浸式娱乐真实链路：
  - `体育休闲服务;娱乐场所 -> immersive_entertainment`
  - 混名强排除优先

注意：

- 裸 `080000` 仍不展示，不应映射到 immersive。
- `体育休闲服务;KTV`、`体育休闲服务;酒吧`、`体育休闲服务;网吧` 仍归 `bars`。

### `backend/prompts/industry_config.py`

核心职责：

- `BUSINESS_TYPE_TO_MASTER`
- `MASTER_TEMPLATES`
- `INDUSTRY_RIGOR`
- `get_rigor_for_config_key`
- 行业规则、评分规则、报告提示规则

已完成重点：

- 小吃店 `050300` direct 风险已收紧。
- 高频刚需零售、专业生活服务、社区基础服务、夜经济娱乐已做 subtype 深化。
- 商务酒店、民宿青旅已消除 `100000` 裸 direct 风险。
- 沉浸式社交娱乐已深化为剧本杀、密室逃脱、台球厅、桌游/轰趴、电玩/VR。

下一步若处理 known_gap，不要一次处理多个组。建议先处理餐饮中一个最清晰的组，比如 `精品茶饮咖啡`。

### `backend/prompts/location_analysis.py`

当前已做第一轮报告 prompt 收紧：

- 定位为“商业选址初筛 AI 分析员”。
- 明确“不提供投资建议，不替用户做决策，需结合实地考察验证”。
- 竞争环境仅基于 `direct_competitors`。
- `substitute` 和 `traffic_anchors` 不得计入竞品数量或竞争评分。

下一阶段若处理报告事实校验，需要继续检查这里和 `backend/main.py`。

### `frontend/src/services/amapData.js`

当前要求：

- 不修改。
- 该文件是 Deprecated 兼容层，正式分析链路以后端 `amap_service.py` 和 `real_data` 为准。
- 最近 Codex 审核该文件无 diff。

## 真实报告数据链路

```text
AMap POI
  -> classify_poi_type(type)
  -> category-specific dewatering
  -> business-aware rewrite (shopping -> fresh_retail/tobacco_liquor)
  -> classify_poi_rigor(name, cat, type_code, rigor, business_type)
  -> real_data.rigor_enabled / direct / substitute / anchors / irrelevant
  -> prompt
  -> LLM
  -> frontend/PDF/HTML
```

## 当前不要做

- 不生成真实报告。
- 不启动前端。
- 不改 UI/PDF/页脚。
- 不改端口。
- 不改数据库 schema。
- 不改 AMap API 调用方式。
- 不处理历史前端脏文件。
- 不处理临时报告图片/文本文件。
- 不为宝鸡、经二路、商场、门店、品牌写特判。
- 不全量铺样本库。
- 不带 FAIL 交付。

## 建议下一步

建议进入：**餐饮 known_gap 第一组小收口：精品茶饮咖啡**。

原则：

- 只处理一个组。
- 先让 Claude Code 提出规则修复方案，不要直接大改。
- Codex 审核后，再允许 Claude Code 做小补丁。
- 每次必须保持 `0 FAIL`。

候选第一组：

`精品茶饮咖啡` known_gap：

- 甜品店
- 冰淇淋店
- 便利店
- 火锅店
- 烧烤店

目标是让这些不进入茶饮咖啡 direct；具体是 exclude、substitute 还是 irrelevant，需要先看当前 `INDUSTRY_RIGOR["精品茶饮咖啡"]` 规则后决定。
