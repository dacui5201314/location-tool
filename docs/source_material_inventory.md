# 址得选 外部资料盘点 v2026-06-16

## 蒸馏准入标准

本项目的最终目标是让报告更专业，而不是把所有资料都塞进知识库。
外部资料只有同时满足以下条件，才允许创建 source card：

1. **内容可读**：本地文件能抽取到足够文本，或已有人工摘录/历史蒸馏证据。
2. **与选址判断直接相关**：能反哺需求来源、风险信号、现场核验、数据盲区或禁误读。
3. **适用模型明确**：能落到 12 个 business model 中的一个或多个，不做泛泛而谈。
4. **专业可信**：优先书籍、论文、报告、官方资料；论坛帖/营销文只入库存，不进 source card。
5. **已吸收闭环**：所有蒸馏来源均已通过对应 Phase 吸收进 YAML，补全 `source_refs` 和业务回归测试。新增来源卡必须走相同闭环。

## 已蒸馏来源

| source_id | 资料名 | 类型 | 状态 | 适用模型 |
|-----------|--------|------|------|----------|
| book_001 | 千分选址 最实效的餐饮连锁门店选址策略 | book | Phase 1.5 已吸收 | snack_fast_food, food_service |
| book_002 | 连锁门店开发与选址 | book | Phase 1.5 已吸收 | snack_fast_food, retail_convenience, retail_shopping |
| report_summary_001 | 社区化新零售的布局选址与优化发展研究-以南京市盒马鲜生为例 | report_summary | Phase 1.5 已吸收 | retail_convenience |
| book_003 | 从零开始做餐饮 | book | Phase 4G 已吸收 | snack_fast_food, food_service |
| book_005 | 零售的哲学：7-Eleven便利店创始人自述 | book | Phase 4G 已吸收 | retail_convenience |
| book_011 | 现代酒店管理 | book | Phase 4G 已吸收 | hotel |
| book_012 | 酒店管理概论 | book | Phase 4G 已吸收 | hotel |
| book_013 | 一本书读懂校外托管机构运营与管理 | book | Phase 4I 已吸收 | education_childcare |
| product_review_002 | 址得选 教育托管业态知识梳理 | product_review | Phase 4H 已吸收 | education_childcare |
| product_review_003 | 址得选 教育培训业态知识梳理 | product_review | Phase 4H 已吸收 | education_training |
| product_review_004 | 址得选 美业健身宠物业态知识梳理 | product_review | Phase 4H 已吸收 | service_beauty |
| product_review_005 | 址得选 药店业态知识梳理 | product_review | Phase 4H 已吸收 | pharmacy |
| product_review_006 | 址得选 休闲娱乐业态知识梳理 | product_review | Phase 4H 已吸收 | entertainment |

## 本地有文件但本轮不蒸馏

| 资料名 | 原因 | 后续处理 |
|--------|------|----------|
| 白手起家 餐饮开店全程实战手册 | PDF 文本抽取质量不足，无法稳定定位选址规则 | 需要 OCR 或人工摘录选址章节 |
| 零售学 第2版 | PDF 文本抽取质量不足，且内容偏教材泛论 | 需要 OCR 后只提取零售选址/商圈章节 |
| 开店选址实用手册 | PDF 文本抽取质量不足，虽然题名高度相关但不能凭题名蒸馏 | 需要 OCR 或人工摘录 |
| 商店选择、店面选址与市场分析 | PDF 文本抽取质量不足，不能安全提炼 | 需要 OCR 或人工摘录 |
| 选址！选址！选址！ | PDF 文本抽取质量不足，不能安全提炼 | 需要 OCR 或人工摘录 |
| 选址创新 创新者行为与商业中心地的兴亡 | PDF 文本抽取质量不足，且偏理论研究 | OCR 后仅作为商圈迁移/新兴节点候选规则 |
| 关于商铺选址(想开店的进) | 论坛/文章属性强，本轮关键词命中不足，不适合支撑专业报告 | 不进入 source card，可作为人工启发材料 |

## 用户清单中本地未找到的资料

这些条目出现在用户清单中，但本轮未在 `Desktop/书籍` 找到对应文件，因此没有创建 source card。

| 方向 | 缺失资料 |
|------|----------|
| 小吃快餐/聚餐餐饮 | 餐饮开店120讲；餐饮管理；饭店管理：理论、方法与技巧；火锅店选址的几大要点；小火锅加盟选址技巧 |
| 茶饮轻餐 | 2023新茶饮选址洞察报告；中国新茶饮品牌门店分布及好店洞察；茶饮店选址应该考虑哪些问题；奶茶店选址的商圈分析方法与技巧；饮料店创业经营策略 |
| 药店 | 药店选址指南；药品零售网点空间布局指引 |
| 低频零售 | 零售店位置分析：选址适宜性；影响零售商业选址决策的相关资料；商业地产与门店拓展 |
| 教育托管/培训 | 衡阳市校外托管机构合规经营指南；新型托管机构创业挣钱指南；教育培训大运营：K12业务精细化操作指南；托育综合服务中心建设指南 |
| 洗衣/诊所 | 自助洗衣烘衣店行业分析；连锁洗衣店选址布局相关报告；社区诊所选址报告 |
| 美业/健身/宠物 | 田杨美业经营管理实务；美业超级店长；美业超级顾问；商业健身房经营书；宠物店经营书或宠物行业深度报告 |
| 休闲娱乐 | 城市（营业性）娱乐场所空间结构研究；竞争性设施选址问题相关研究 |

## 本轮处理说明

- 撤回 7 张不够稳的候选卡：`book_004`、`book_006`、`book_007`、`book_008`、`book_009`、`book_010`、`report_summary_002`。
- 所有来源卡均标记 `derived_rule_only: true`，不包含原文摘录。
- Phase 4G 已吸收 `book_003`/`book_005`/`book_011`/`book_012` 到对应 business model YAML 并补 source_refs 和回归测试。
- Phase 4H 已吸收 `product_review_002`-`006`（五业态知识梳理）到对应 YAML。
- Phase 4I 已吸收 `book_013`（托管书籍）到 education_childcare YAML。

## 蒸馏原则

- 不保存 OCR 全文、不保存章节原文、不复制长段内容。
- 只沉淀可反哺 YAML 的抽象规则、风险信号、现场核验项、数据盲区。
- 所有外部卡必须有 `derived_rule_only: true` 或 `copyright_note`。
- 版权信息只记录书名/作者/资料名，不记录下载来源。
