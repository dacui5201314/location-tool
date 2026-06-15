# 址得选 选址知识蒸馏流程规范 v2026-06-15

## 一、目的

把书籍、行业报告、官方资料、一线访谈和历史样本中的选址判断经验，
转化为结构化的 source card（来源卡），供 Phase 1/2 YAML 模型和确定性服务消费。

## 二、核心原则

1. **不保存整本书原文。** 任何情况下不得将书籍章节、报告全文或长段文字复制到仓库中。
2. **不复制长段内容。** 蒸馏只提取抽象规则、判断条件、风险信号、核验项和数据盲区。
3. **只沉淀可反哺 YAML 的内容。** 如果一条信息不能映射到现有 business_model YAML 字段
   （demand_sources / red_flags / fit_signals / field_checklist / data_blind_spots / forbidden_misreadings），
   则不应出现在 source card 中。
4. **来源可追溯。** 每条规则必须记录来源类型和可信度，外部来源必须附带合规说明。
5. **可信度分级。** A=内部样本验证 / B=行业通行规则 / C=推测或单次访谈未交叉验证。

## 三、来源类型与 copyright 安全边界

| 来源类型 | 可用内容 | 禁止内容 | 合规要求 |
|---------|---------|---------|---------|
| `internal_sample` | 自有报告复盘、评分对比、核验结论 | — | 无 |
| `product_review` | 产品使用反馈、结构性问题总结 | — | 无 |
| `rule_seed` | 从内部样本和产品复盘抽象出的通用选址规则 | — | 无 |
| `report_summary` | 公开行业报告的统计结论和数据趋势（如"XX 品类闭店率 Y%"） | 报告原文段落、图表、具体案例描述 | 标注 derived_rule_only=true，仅保留自己提炼的判断规则 |
| `book` | 已出版书籍中的选址方法论抽象（如"零售选址四要素"） | 原文章节、段落、示意图、案例故事 | 标注 copyright_note 说明来源书名/作者/出版社，仅保留抽象规则，不得引用原文 |
| `official_public` | 政府部门公开的统计数据、合规要求、许可条件 | 内部文件、未公开数据 | 标注出处 URL 或文号 |
| `interview` | 一线从业者提供的选址经验判断 | 具体人名、店名、经营数据 | 标注 derived_rule_only=true，不得引用原话 |

## 四、Source Card 标准流程

### 步骤 1：确定来源类型和可信度

- 自有报告复盘 → `internal_sample`，可信度 A
- 产品评审发现 → `product_review`，可信度 A
- 行业公开数据 → `report_summary`，可信度 B
- 书籍方法论 → `book`，可信度 B（需 copyright_note）
- 政府公开资料 → `official_public`，可信度 A（需出处）
- 一线访谈 → `interview`，可信度 C（需 derived_rule_only）

### 步骤 2：提取规则

只提取以下类型的规则：

- **demand_sources**: 该业态的核心需求来源和触发条件
- **red_flags**: 风险信号和 severity（stop / downgrade / warning）
- **fit_signals**: 成立条件
- **field_checklist_additions**: 现有 YAML field_checklist 未覆盖的核验项
- **data_blind_spots**: 该来源揭示的数据盲区
- **forbidden_misreadings**: 常见的错误解读

### 步骤 3：填写 Source Card YAML

按 `source_card_schema.yaml` 格式填写，外部来源必须填写 `copyright_note` 或 `derived_rule_only`。

### 步骤 4：验证可追溯性

- 每条规则必须能对应到至少一个 `applicable_models` 中的 YAML 字段。
- 不能反哺现有 YAML 的规则标记为 `provisional`，不进入确定性判断链路。

## 五、文件组织

```
backend/knowledge/sources/
  source_manifest.yaml              # 所有来源清单
  internal_sample_001_*.yaml        # 内部样本来源卡
  product_review_001_*.yaml         # 产品复盘来源卡
  # 外部来源（需用户提供材料后才创建）
  # book_001_*.yaml                 # 书籍蒸馏来源卡
  # report_summary_001_*.yaml       # 行业报告蒸馏来源卡
  # official_public_001_*.yaml      # 官方资料来源卡
  # interview_001_*.yaml            # 访谈蒸馏来源卡
```

## 六、版本

- 创建日期：2026-06-15
- 适用范围：Phase 1.5 起所有 source card 创建和审核
