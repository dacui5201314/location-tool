# 址得选 外部资料接入模板

> 用于用户提供书籍、行业报告、官方资料、访谈纪要时填写。
> 没有用户材料时，不新增 book/report_summary/official_public/interview source card。

## 必填字段

| 字段 | 说明 | 示例 |
|------|------|------|
| `source_type` | `book` / `report_summary` / `official_public` / `interview` | `book` |
| `source_title` | 资料名称 | 《零售选址实战》 |
| `author_or_org` | 作者或发布机构 | 张三 / 中国连锁经营协会 |
| `publication_or_url` | 出版信息或链接 | 中信出版社 2024 / https://xxx |
| `user_notes` | 为何这份资料对选址判断有价值 | "第3章餐饮选址逻辑与当前 snack_fast_food 模型高度一致" |

## 合规字段（至少填一个）

| 字段 | 说明 |
|------|------|
| `copyright_note` | 版权来源说明：书名/作者/出版社，不复制原文 |
| `derived_rule_only` | `true` = 仅保留自己提炼的抽象规则，不含原文 |

## 用途范围

| 字段 | 说明 |
|------|------|
| `allowed_excerpt_scope` | 用户授权可提取的内容范围，例如"仅第3章选址方法论" / "全文统计结论" |
| `target_business_models` | 预期反哺的生意模型，例如 `["snack_fast_food", "education_childcare"]` |
| `expected_rules_to_extract` | 预期提炼的规则类型和数量，例如"demand_sources 3 条、red_flags 2 条" |

## 模板（直接复制填写）

```yaml
# 外部资料接入申请
source_type: ""             # book / report_summary / official_public / interview
source_title: ""
author_or_org: ""
publication_or_url: ""
user_notes: ""

# 合规（至少填一个）
copyright_note: ""          # 例: "《零售选址实战》张三 中信出版社 2024"
derived_rule_only: false    # true = 不包含原文

# 用途范围
allowed_excerpt_scope: ""   # 例: "第3章餐饮选址方法论"
target_business_models: []  # 例: ["snack_fast_food"]
expected_rules_to_extract: ""  # 例: "demand_sources 3条、red_flags 2条"
```

## 流程

1. 用户填写此模板并提交资料（章节截图/报告链接/访谈摘要）。
2. 审核 `allowed_excerpt_scope` 确认不超出 copyright safe 边界。
3. 蒸馏为 source card YAML，仅保留抽象规则，不复制原文。
4. source card 通过 `check_knowledge_schema_rules.py` T12 合规检查。
5. 规则经 `check_business_model_rules.py` 验证后可反哺 YAML。

## 非目标

- 不要求用户提供整本书。
- 不接受逐字复制的原文作为 source card。
- 不因缺少外部材料而阻塞 Phase 1.5 流程。
