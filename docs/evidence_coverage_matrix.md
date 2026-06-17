# 12 业态 Evidence Coverage 矩阵 v2026-06-17

## 覆盖状态说明

| 标识 | 含义 |
|------|------|
| ✅ book | 已有书籍来源吸收进 YAML source_refs |
| ✅ review | 已有 product_review 吸收 |
| ✅ seed | 已有 rule_seed 吸收 |
| 📋 cand | candidate_only 候选方向，未吸收 |
| 📋 none | 无对应类型来源 |

## 矩阵

| # | model_id | book | product_review | rule_seed | sample_regr | source_refs | 样本数 |
|---|----------|------|---------------|-----------|-------------|-------------|--------|
| 01 | snack_fast_food | ✅ book_001,book_003 | — | — | ✅ 7 | ✅ | 7 |
| 02 | food_service | ✅ book_001,book_003 | — | — | ✅ 6 | ✅ | 6 |
| 03 | beverage_dessert | — | — | ✅ rule_seed_001 | ✅ 7 | ✅ (4P-B) | 7 |
| 04 | retail_convenience | ✅ book_002,book_005 | ✅ report_summary_001 | — | ✅ 6 | ✅ | 6 |
| 05 | pharmacy | — | ✅ product_review_005 | ✅ rule_seed_007 | ✅ 5 | ✅ | 5 |
| 06 | retail_shopping | ✅ book_002 | — | ✅ rule_seed_008 | ✅ 5 | ✅ | 5 |
| 07 | education_childcare | ✅ book_013 | ✅ product_review_002 | — | ✅ 5 | ✅ | 5 |
| 08 | education_training | — | ✅ product_review_003 | ✅ rule_seed_005 | ✅ 6 | ✅ | 6 |
| 09 | service_basic | — | — | ✅ rule_seed_006 | ✅ 5 | ✅ | 5 |
| 10 | service_beauty | — | ✅ product_review_004 | — | ✅ 5 | ✅ | 5 |
| 11 | hotel | ✅ book_011,book_012 | — | ✅ rule_seed_006 | ✅ 6 | ✅ | 6 |
| 12 | entertainment | — | ✅ product_review_006 | ✅ rule_seed_006 | ✅ 5 | ✅ | 5 |

## 证据链分级

### Tier 1：book 吸收 + 样本回归（最强证据链）
- snack_fast_food：book_001 + book_003 + 7 样本
- food_service：book_001 + book_003 + 6 样本
- retail_convenience：book_002 + book_005 + report_summary_001 + 6 样本
- education_childcare：book_013 + product_review_002 + 5 样本
- hotel：book_011 + book_012 + rule_seed_006 + 6 样本

### Tier 2：product_review/rule_seed + 样本回归（可接受证据链）
- beverage_dessert：rule_seed_001 + 7 样本 ✅
- pharmacy：product_review_005 + rule_seed_007 + 5 样本
- retail_shopping：book_002 + rule_seed_008 + 5 样本
- education_training：product_review_003 + rule_seed_005 + 6 样本
- service_beauty：product_review_004 + 5 样本
- entertainment：product_review_006 + rule_seed_006 + 5 样本

### Tier 2-：rule_seed only + 样本回归（需后续补充）
- service_basic：rule_seed_006 + 5 样本（无 book/review）

## candidate_only 来源（不计算为已吸收证据）

| source_id | 适用模型 | 阻塞原因 |
|-----------|----------|----------|
| candidate_001 | snack_fast_food, food_service, retail_convenience, retail_shopping | PDF 需 OCR |
| candidate_002 | beverage_dessert, snack_fast_food | 未找到原始文件 |
| candidate_003 | pharmacy | 未找到原始文件 |

## 验收标准

每个业态至少满足：
- ✅ source_refs 或等价来源追溯（全部 12 族满足）
- ✅ 样本数 >= 5（全部 12 族满足）
- ✅ expected_present / expected_absent 禁止表达扫描（双文本 JSON+HTML）
- 4P-B 追溯修正：beverage_dessert 补 source_refs→rule_seed_001
