# 高质量书源蒸馏吸收 Checklist v2026-06-17

新书源从接入到吸收的固定步骤。每一步必须验证通过才能进入下一步。

## 步骤总览

```
intake → 版权边界 → source card → manifest → status 判定 → YAML 吸收 → service/report → regression
  1          2           3           4           5             6             7              8
```

---

## 1. Intake（资料接入）

- [ ] 资料文件已在本地可读（PDF/EPUB/文本均可）
- [ ] 如为 PDF：文本抽取质量足够定位选址规则（非 OCR 失败/乱码）
- [ ] 如为网络来源：已保存离线副本，来源 URL 已记录
- [ ] 已填写 `docs/source_material_intake_template.md`
- [ ] 已更新 `docs/source_material_inventory.md` 用户清单

**阻塞条件：下载不到、OCR 不稳、文本抽取质量不足 → 到此为止，不进入 source card。**

## 2. 版权/原文边界

- [ ] 已确认资料版权状态（书籍/报告/论文/公开资料）
- [ ] `copyright_note` 已填写：仅保留抽象选址判断规则，不包含原文摘录
- [ ] 规则来自对原文的抽象提炼，非逐字复制
- [ ] 不记录下载来源

## 3. Source Card（来源卡）

- [ ] 创建 `backend/knowledge/sources/{source_id}_{slug}.yaml`
- [ ] 必填字段完整：
  - [ ] `source_id`
  - [ ] `source_type`（book / report_summary / product_review / rule_seed / internal_sample）
  - [ ] `title`
  - [ ] `confidence`（A=内部样本复盘 / B=已蒸馏专业资料 / C=候选未验证）
  - [ ] `derived_rule_only: true`
  - [ ] `distillation_status`
  - [ ] `applicable_models`
  - [ ] `extracted_rules`（demand_sources / red_flags / fit_signals / data_blind_spots / forbidden_misreadings）
  - [ ] `professional_use_policy`

## 4. Manifest（来源清单）

- [ ] `backend/knowledge/sources/source_manifest.yaml` 已追加新条目
- [ ] `source_id` 唯一，不与已有来源冲突
- [ ] `source_type`、`confidence`、`applicable_models` 与 source card 一致

## 5. Status 判定

- [ ] 判定为 `candidate_only` 或 `absorbed`：

| 状态 | 条件 |
|------|------|
| `candidate_only` | 资料存在但未验证/未蒸馏；不改变报告行为；usage_limits 必须明确吸收障碍 |
| `absorbed` | 规则已通过 YAML source_refs 吸收进 business_model；已补回归测试 |

- [ ] candidate_only 来源：
  - [ ] `confidence` 强制 = C
  - [ ] `extracted_rules` 强制为空（规则在 `candidate_rules` 中）
  - [ ] `usage_limits` 必须含吸收障碍声明（"不得吸收/不改报告/OCR/可读性"等）
- [ ] absorbed 来源：
  - [ ] `confidence` 至少 = B
  - [ ] `extracted_rules` 非空
  - [ ] `distillation_status` = "absorbed"

## 6. YAML 吸收（仅 absorbed 来源）

- [ ] 目标 `business_model` YAML 已追加 `source_refs`
- [ ] `source_refs` 格式：`{source_id, applies_to: [...], rule_key: "..."}`
- [ ] `applies_to` 涵盖规则影响的 YAML 字段（demand_sources / red_flags / fit_signals / data_blind_spots / forbidden_misreadings / hard_gates）
- [ ] `sources` 字段（如有）与 `source_refs` 一致
- [ ] `last_reviewed` 已更新

**重要：candidate_only 来源绝对不得出现在任何 YAML source_refs 中。**

## 7. Service/Report JSON 消费

- [ ] 如需改动 `backend/services/*.py`：
  - [ ] 改动必须可测试
  - [ ] 改动不影响现有报告语义（除非规则明确要求）
- [ ] HTML/小程序只消费 report_json，不得自行生成业务逻辑
- [ ] 不改 prompt 主体来掩盖业务模型问题

## 8. Regression（回归测试）

必跑清单：

```
python backend/tests/check_knowledge_schema_rules.py   # schema + source_refs 校验
python backend/tests/check_business_model_rules.py     # BM 规则测试
python backend/tests/check_sample_regression.py        # 样本回归
python backend/tests/check_report_enrichment_service.py # enrichment 三路径
python backend/tests/check_report_fact_guard.py        # 事实校验 (188)
```

如改动 fallback_report_service.py，加跑：
```
python backend/tests/check_fallback_report.py
python backend/tests/check_p1_business_model_quality.py
```

---

## 已有书源吸收状态

| 业态 | book 吸收 |
|------|----------|
| snack_fast_food | book_001 + book_003 |
| food_service | book_001 + book_003 |
| retail_convenience | book_002 + book_005 |
| retail_shopping | book_002 |
| education_childcare | book_013 |
| hotel | book_011 + book_012 |
| beverage_dessert | —（rule_seed_001） |
| pharmacy | —（product_review_005 + rule_seed_007） |
| education_training | —（product_review_003 + rule_seed_005） |
| service_beauty | —（product_review_004） |
| entertainment | —（product_review_006 + rule_seed_006） |
| service_basic | —（rule_seed_006） |

## candidate_only 清单

| source_id | 阻塞原因 |
|-----------|----------|
| candidate_001 | PDF OCR 未完成 |
| candidate_002 | 原始文件未获取 |
| candidate_003 | 原始文件未获取 |
