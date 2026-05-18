# Current Handoff - 2026-05-18

## Phase 7D：主线阶段完成，等待产品验收

19 次真实报告。5 次 fact_errors，3 次 retry 挽救，实际退款率 11%。retry fallback 有效，fact guard 不放宽。报告边界声明已真实验证。无 Major 质量问题。**未 push。**

代码: `660e5b2` | 文档: `548c4a1` | 基线: compileall PASS / industry 1902 / fact guard 92

## Phase 6E 扩大回归（2026-05-18）

5/5 保存成功。2 次 retry 触发并全部挽救成功。0 退款。

| # | 业态 | 地址 | id | score | retry | 结果 |
|---|---|---|---|---|---|---|
| P6E-1 | 民宿青旅 | 春熙路1号 | 33 | 52 | **触发→通过** | 保存 |
| P6E-2 | 商务酒店 | 建国路88号 | 34 | 40 | **触发→通过** | 保存 |
| P6E-3 | 烘焙甜品 | 淮海中路999号 | 37 | 65 | 无 | 保存 |
| P6E-4 | 社区基础服务 | 天河路208号 | 35 | 61 | 无 | 保存 |
| P6E-5 | 夜经济娱乐 | 春熙路1号 | 36 | 54 | 无 | 保存 |

### retry 详情

- id=33 (民宿青旅): stats_500m.schools=6 but report says 22 (>3x) → retry passed
- id=34 (商务酒店): stats_200m.subway=1 but report says 4 (>3x) → retry passed

### 累计统计 (18 次真实报告)

- fact_errors 触发: 5 次 (28%)
- retry 挽救: 3 次 (60% of errors)
- 实际退款: 2 次 (11%)
- 正常保存 (含 retry 挽救): 16 次 (89%)

retry fallback 将实际退款率从 28% 降至 11%。

## Phase 6D 真实 fallback 验证（2026-05-18）

3/3 保存成功。低频目的零售触发 1 次 retry 并挽救成功。

| # | 业态 | 地址 | id | score | retry | 结果 |
|---|---|---|---|---|---|---|
| P6D-1 | 精品茶饮咖啡 | 淮海中路999号 | 31 | 54 | 无 | 保存 |
| P6D-2 | 药店 | 淮海中路999号 | 30 | 61 | 无 | 保存 |
| P6D-3 | 低频目的零售 | 建国路88号 | 32 | 44 | **触发→通过** | 保存 |

### id=32 retry 详情

- 第一次 fact_errors: `stats_500m.schools=1 but report says 13 (>3x)`
- retry 后 fact_errors 修正 → 正常保存
- 元数据完整: `_fact_retry=True`, `_fact_retry_passed=True`, `_fact_errors_before_retry` 已记录

### fallback 真实验证结论

retry fallback 在真实链路中成功挽救一次 LLM 数字幻觉 (schools 1→13)。
正常报告 (茶饮/药店) 未受影响，无 retry 触发。
累计真实报告 13 次，3 次 fact_errors (23%)，其中 1 次被 retry 挽救。

## Phase 6B 定向回归（2026-05-18）

4/4 全部保存成功。C-1/C-3 幻觉业态（药店/茶饮）在不同地址下均未复现。

| # | 业态 | 地址 | id | score | fact_errors |
|---|---|---|---|---|---|
| P6B-1 | 药店 | 上海市徐汇区淮海中路999号 | 26 | 57 | 0 |
| P6B-2 | 药店 | 北京市朝阳区建国路88号 | 27 | 54 | 0 |
| P6B-3 | 精品茶饮咖啡 | 广州市天河区天河路208号 | 28 | 53 | 0 |
| P6B-4 | 精品茶饮咖啡 | 成都市锦江区春熙路1号 | 29 | 56 | 0 |

### 累计统计

10 次真实报告：2 次 fact_errors (20%)，8 次保存成功 (80%)。
C-1/C-3 幻觉未在相同业态不同地址复现 → LLM 数字幻觉与具体地址/周边 POI 数据相关，非业态固有特性。

### 建议

fact_errors 触发率 20%，不建议放宽 guard。可考虑下一 Phase 加免费重试 1 次 fallback（不同 temperature），预期挽救约一半退款。

## Phase 6 真实报告多业态回归（2026-05-18）

3/3 全部保存成功，0 fact_errors，0 退款。

| # | 业态 | 地址 | id | score | fact_errors |
|---|---|---|---|---|---|
| P6-1 | 刚需快餐小吃 | 上海市徐汇区淮海中路999号 | 23 | 58 | 0 |
| P6-2 | 中餐正餐 | 北京市朝阳区建国路88号 | 24 | 51 | 0 |
| P6-3 | 商务酒店 | 广州市天河区天河路208号 | 25 | 53 | 0 |

### 对比全量真实报告

| 轮次 | 业态 | fact_errors | 结果 |
|---|---|---|---|
| C-1 | 药店 | 1 (residential 幻觉) | 退款 |
| C-2 | 刚需快餐小吃 | 0 | 保存 |
| C-3 | 精品茶饮咖啡 | 1 (hospitals 幻觉) | 退款 |
| P6-1 | 刚需快餐小吃 | 0 | 保存 |
| P6-2 | 中餐正餐 | 0 | 保存 |
| P6-3 | 商务酒店 | 0 | 保存 |

**6 次真实报告，2 次 fact_errors 退款 (33%)，4 次成功保存 (67%)。**
幻觉集中出现在药店和茶饮咖啡业态——需要后续 Phase 对比这两个业态的不同地址。

## Phase 7 报告内容质量抽检（2026-05-18）

8 份已保存报告抽检结果：

| id | 业态 | score | retry | 边界 | 决策语言 | 四分类 | 评分一致 | 判定 |
|---|---|---|---|---|---|---|---|---|
| 32 | 低频零售 | 44 | 是 | ✗ | 无 | ✓ | ✓ | Minor |
| 33 | 民宿青旅 | 52 | 是 | ✗ | 无 | ✓ | ✓ | Minor |
| 34 | 商务酒店 | 40 | 是 | ✗ | 无 | ✓ | ✓ | Minor |
| 30 | 药店 | 61 | 是 | ✗ | 无 | ✓ | ✓ | Minor |
| 31 | 茶饮咖啡 | 54 | 否 | ✗ | 无 | ✓ | ✓ | Minor |
| 24 | 中餐正餐 | 51 | 否 | ✗ | 无 | ✓ | ✓ | Minor |
| 23 | 快餐小吃 | 58 | 否 | ✓ | 无 | ✓ | ✓ | Pass |
| 37 | 烘焙甜品 | 65 | 否 | ✗ | 无 | ✓ | ✓ | Minor |

### 统计

- Pass: 1, Minor: 7, Major: 0
- 无禁用决策化表达
- 无 anchor 被写成竞品
- 评分与文案方向一致
- retry 元数据全部完整

### 主要问题

**7/8 报告未显式标注"初筛参考/需线下核验"产品边界。** 这是 prompt 层面的遗漏——当前 prompt 有禁止决策化表达的规则，但没有正向要求每份报告必须显式声明产品边界。

### 建议

进入 **Phase 7B**：在 `location_analysis.py` 的 output 模板中增加一行"本报告为选址初筛参考，需线下实地核验"的强制尾部声明。极小改动，不影响 guard/engine。

## Phase 7C 边界声明真实验证（2026-05-18）

1 个真实样本验证通过。

| # | 业态 | 地址 | id | score | retry | 声明 | 结果 |
|---|---|---|---|---|---|---|---|
| P7C-1 | 刚需快餐小吃 | 淮海中路999号 | 38 | 54 | 无 | **已出现在 summary 中** | 通过 |

summary 末尾: "本报告为选址初筛参考，需线下实地核验。" ✓ 无禁用决策化表达 ✓

Phase 7B prompt 改动已生效，边界声明成功进入报告输出。

## Baseline

| Test | Result |
|---|---|
| `compileall backend` | PASS |
| `check_industry_rigor_rules.py` | 1902 PASS, 0 FAIL |
| `check_report_fact_guard.py` | 92 PASS, 0 FAIL |
| `KNOWN_RULE_GAPS` | (none) |

## Commits

| Type | SHA | Message |
|---|---|---|
| Code | `01ef4de` | fix: keep fact retry audit metadata |
| Docs | `ffadda1` | docs: fix next session handoff |

Not pushed.

## Next Step

**Phase 7**: spot-check content quality of 16 saved reports. Do NOT run more real reports without user authorization. Do NOT push.
