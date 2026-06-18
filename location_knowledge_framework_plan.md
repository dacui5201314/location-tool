# 址得选选址知识蒸馏与业态框架固化方案

版本：2026-06-15.v1

> 当前状态（2026-06-18）：本方案的主体工程已经完成并进入回归保护阶段。它保留为历史设计方案和架构依据，不再作为新的执行清单逐项推进。当前进度与最终基线以 `docs/location_knowledge_framework_progress.md` 为准；后续如有新书源或高质量资料，按 `docs/source_material_absorption_checklist.md` 执行。2026-06-18 的小程序/管理后台展示优化只消费 `report_json`，不改变本知识框架、YAML、prompt、guard 或评分语义。

## 一、项目目标

本方案用于把选址书籍、行业报告、官方资料、一线访谈和真实报告复盘，沉淀为可执行、可测试、可迭代的选址判断框架。

核心目标不是建设一个“大而全知识库”，而是解决当前报告付费价值里的三个关键问题：

1. 竞争评分不会区分“没有竞品是机会”还是“没有竞品是低需求信号”。
2. 不同业态共用通用模板，导致教育托管出现餐饮核验项。
3. 同一地址切换不同业态后，报告对地点本身的叙事不一致。

最终产物应进入代码、报告 JSON、HTML 导出和小程序展示，而不是只停留在文档或 prompt 中。

## 二、总体架构

采用两层判断架构：

```text
第一层：位置基本面 location_profile
只看 real_data，不看业态。
回答：这个地方本身是什么类型？

第二层：业态生意模型 business_model
看 location_profile + business_type / category / brand_name。
回答：这个业态在这个地方是否匹配？
```

报告生成顺序：

```text
real_data
  -> compute_location_profile(real_data)
  -> classify_business_model_family(business_type, category, brand_name)
  -> load business_model YAML
  -> compute_business_model_snapshot(...)
  -> enrich_report_business_context(...)
  -> normal / retry / fallback report_json
  -> HTML / 小程序统一渲染 report_json
```

关键原则：

1. 同一份 real_data 生成的位置基本面必须一致。
2. 不同业态的业务判断可以不同，但不能对同一地点事实说反话。
3. HTML 和小程序只负责渲染 report_json，不各自生成业务逻辑。
4. 业态知识应固化在 YAML + deterministic service + tests 中，不依赖 LLM 自行发挥。

## 三、位置基本面标签

位置基本面不做单一死标签，而采用“主类型 + 副标签 + 证据”的结构。

建议结构：

```yaml
model_version: 2026-06-15.v1

location_profile:
  primary_type: 学区弱交通社区型
  secondary_tags:
    - 学区锚点
    - 社区客群一般
    - 弱交通
    - 弱办公
  summary: 该位置以学校锚点为主要可用客流，住宅和办公支撑一般，公共交通导入偏弱。
  core_anchors:
    - 学校
    - 住宅
  strengths:
    - 500米内学校数量较多，可形成特定时段客流。
    - 周边具备基础社区消费场景。
  weaknesses:
    - 办公客群弱，工作日全天稳定客流不足。
    - 公共交通弱，外部导入客流有限。
    - 晚间和周末消费需要现场核验。
  suitable_business_families:
    - snack_fast_food
    - education_childcare
    - student_retail
  cautious_business_families:
    - group_dining
    - large_education_training
    - entertainment
  evidence:
    schools_500m: 4
    residential_500m: 4
    office_500m: 0
    bus_500m: 0
    subway_500m: 0
```

初始位置类型建议：

1. 学区社区型
2. 学区弱交通型
3. 居住密集型
4. 商业办公型
5. 交通枢纽型
6. 商业综合型
7. 酒店商务型
8. 夜间消费型
9. 低密度弱支撑型
10. 混合型

位置打标必须基于确定性规则，不依赖 LLM。

## 四、业态族群规划

采用“后台规则组为基础 + 必要拆分”的方式，避免重新发明一套和现有系统冲突的业态体系。

建议从 34 个前台业态归并为 12 个业务模型族群：

| 序号 | YAML 文件 | 族群 | 覆盖示例 | 竞争类型 |
|---|---|---|---|---|
| 01 | 01_snack_fast_food.yaml | 小吃快餐 | 小吃快餐、小吃店、快餐店、小餐饮、麻辣烫、砂锅 | 排斥型 |
| 02 | 02_group_dining.yaml | 正餐聚餐 | 中餐厅、大餐饮、火锅、烧烤、西餐、日料 | 半聚集型 |
| 03 | 03_beverage_dessert.yaml | 茶饮烘焙 | 奶茶、咖啡、饮品、烘焙、甜品 | 半聚集型 |
| 04 | 04_convenience_supermarket.yaml | 便利超市 | 便利店、小超市、超市、生鲜 | 排斥型 |
| 05 | 05_pharmacy.yaml | 药店药房 | 药店、药房、医药零售 | 中性型 |
| 06 | 06_specialty_retail.yaml | 目的零售 | 服装、数码、眼镜、专卖零售 | 中性型 / 聚集型 |
| 07 | 07_education_childcare.yaml | 教育托管 | 托管、小饭桌、午托、晚托、作业辅导、课后服务 | 暗竞品型 |
| 08 | 08_education_training.yaml | 教育培训 | 英语培训、美术培训、琴行、画室、早教、学科辅导 | 聚集型 / 信任型 |
| 09 | 09_laundry_clinic.yaml | 社区基础服务 | 洗衣、诊所、维修、家政 | 暗竞品型 / 排斥型 |
| 10 | 10_beauty_fitness_pet.yaml | 美业健身宠物 | 美容美发、美甲、宠物、健身、瑜伽 | 暗竞品型 / 半聚集型 |
| 11 | 11_hotel_hostel.yaml | 酒店住宿 | 酒店、民宿、青年旅舍、宾馆 | 聚集型 |
| 12 | 12_entertainment.yaml | 休闲娱乐 | 酒吧、KTV、网吧、剧本杀、台球 | 聚集型 |

教育托管和教育培训必须拆开，不允许为了减少 YAML 数量合并。两者核心逻辑不同：

```text
教育托管：
小学距离、放学动线、家长接送、食品/消防/托管合规、空间分区、暗竞品。

教育培训：
课程需求、家庭消费力、周末和放学后流量、满班率、教师资源、续费率、品牌信任。
```

Phase 2 可重新评估 `05_pharmacy.yaml` 是否需要独立存在。药店当前只覆盖 1 个前台业态，且竞争类型偏中性，复杂判断较少；如果后续样本验证其与洗衣、诊所、维修等社区独立日需服务的判断结构高度一致，可合并为 `05_daily_independent.yaml`。该合并不是 Phase 1 阻塞项，不能影响教育托管和小吃快餐打样。

## 五、竞争类型

竞争类型是 business_model 的关键字段，直接影响 0 竞品解释、竞争评分封顶和现场核验方向。

建议五类：

1. 排斥型  
   同类竞品少通常是优势。例：小吃快餐、便利店、洗衣店。

2. 半聚集型  
   同类竞品少不一定好，同类聚集可证明需求。例：茶饮、正餐、美业。

3. 聚集型  
   需要商圈或品类聚集验证需求。0 竞品反而可能是需求不足。例：酒店、娱乐、部分教育培训。

4. 中性型  
   竞品数量只作参考，不直接决定优势。例：药店、目的零售。

5. 暗竞品型  
   POI 收录率低，0 竞品不能作为强优势。例：托管、小饭桌、美业工作室、家政、维修。

竞争评分规则原则：

```text
排斥型：
  近场竞品少可以加分，但仍要看需求侧支撑。

半聚集型：
  近场竞品少只能中性表达，不能直接写市场空白。

聚集型：
  0 竞品必须保守，需求侧不足时竞争/品类评分封顶。

暗竞品型：
  0 POI 竞品必须提示可能存在未收录暗竞品。

中性型：
  竞品数量不直接推导强结论。
```

## 六、business_model YAML 标准字段

每个 YAML 必须包含以下字段：

```yaml
model_id: snack_fast_food
model_version: 2026-06-15.v1
display_name: 小吃快餐

coverage:
  backend_rule_groups:
    - 刚需快餐小吃
  frontend_business_types:
    - 小吃快餐
    - 小吃店
    - 快餐店
    - 小餐饮
  keywords:
    - 麻辣烫
    - 砂锅
    - 米线
    - 面馆

competition:
  type: 排斥型
  zero_competitor_policy: 近场无同类直接竞品可以作为机会线索，但必须结合需求侧和远场供给判断。
  hidden_competitor_risk: 企业/学校食堂、小摊贩、档口可能未被 POI 收录。
  score_caps:
    weak_demand_zero_competitor: 60
    far_field_many_competitors: 70

demand_sources:
  - name: 学校午市
    weight: high
    trigger: stats_500m.schools >= 1
  - name: 办公午市
    weight: medium
    trigger: stats_500m.office >= 1
  - name: 社区晚餐
    weight: medium
    trigger: stats_500m.residential >= 5
  - name: 外卖补充
    weight: low
    trigger: delivery_condition_verified

key_time_windows:
  - label: 午高峰
    value: 工作日 11:30-13:00
  - label: 晚高峰
    value: 工作日 17:30-20:00

hard_gates:
  - 食品经营许可和排烟条件可办理

fit_signals:
  - 午高峰实测目标客群达标
  - 租金低
  - 小档口 1-2 人可运营
  - 外卖可补晚餐缺口

red_flags:
  - 两个高峰实测客流均明显不足
  - 月租金超过预估月营收 25%
  - 1000米同类供给较多且自身无差异化
  - 寒暑假客流断崖且无外卖补充

field_checklist:
  - title: 午高峰门前客流量
    time_window: 工作日 11:30-13:00
    action: 门口定点计数 15 分钟，记录目标客群经过人数。
    risk_type: 客流不足
    pass_hint: 有效目标客群稳定经过。
    eliminate_hint: 两个高峰目标客群都明显不足，不建议继续。

revenue_model:
  unit_logic: 日均单量 x 客单价 x 毛利率
  area_range_sqm: [15, 60]
  rent_ratio_limit: 0.20
  disclaimer: 以上为模型估算，不代表实际经营结果；需结合现场客流、租金、转让费、出餐能力和外卖能力复核。

data_blind_spots:
  - 高德 POI 对小摊贩、档口、内部食堂收录不全。
  - 外卖单量无法从 POI 数据直接推导。
  - 寒暑假对学区型点位影响需线下确认。

forbidden_misreadings:
  - 不能把 200m 无竞品直接写成市场空白红利。
  - 不能把多所大学下属学院当成多所独立学校推高客流判断。
  - 不能输出推荐开店、值得投资、可以放心等决策语言。

sources:
  - id: internal_sample_001
    type: internal_sample
    confidence: A
  - id: industry_report_001
    type: report_summary
    confidence: B

last_reviewed: 2026-06-15
owner: product
```

成立条件不使用全部 AND。统一分为：

1. hard_gates：硬门槛，不满足则降级或淘汰。
2. fit_signals：成立信号，满足越多越适配。
3. red_flags：风险信号，触发后降级或淘汰。

## 七、资料来源与蒸馏流程

资料来源分五类：

1. 内部真实样本  
   从址得选历史报告和真实体验样本中，每个族群选 3-5 份 JSON + HTML + 人工评价。

2. 行业报告与加盟手册  
   包括美团、饿了么、高德、红餐、NCBD、连锁经营协会、品牌公开招商资料等。

3. 正版书籍和教材  
   方向包括零售选址、商圈分析、餐饮开店、酒店管理、教育培训、美业经营。

4. 一线访谈  
   老板、加盟商、铺位中介、商场招商、托管老师、美业店长、酒店运营人员。

5. 官方公开资料  
   国家统计局、市场监管、消防、住建、教育主管部门等，用于合规和宏观口径，不直接作为单点选址判断。

蒸馏原则：

1. 不保存整本书原文。
2. 不逐字复制书中长段内容到产品报告。
3. 只保留抽象规则、判断条件、核验清单、数据盲区和风险边界。
4. 每条关键规则必须记录来源类型和可信度。
5. 来源不足时，规则必须标记为 provisional，不得当成强判断。

资料卡格式：

```yaml
source_id: snack_fast_food_sample_001
source_type: internal_sample
title: 宝鸡文理学院高新校区麻辣烫报告复盘
confidence: A
applicable_models:
  - snack_fast_food
extracted_rules:
  demand_sources:
    - 学校午市可作为核心需求，但必须检查寒暑假断崖风险。
  red_flags:
    - 高租金、弱晚餐、弱外卖同时出现时，不应作为优先候选点。
  forbidden_misreadings:
    - 200m 无竞品不能直接等于市场空白。
```

## 八、代码落地

建议新增目录：

```text
backend/knowledge/
  location_profiles.yaml
  business_models/
    01_snack_fast_food.yaml
    02_group_dining.yaml
    03_beverage_dessert.yaml
    04_convenience_supermarket.yaml
    05_pharmacy.yaml
    06_specialty_retail.yaml
    07_education_childcare.yaml
    08_education_training.yaml
    09_laundry_clinic.yaml
    10_beauty_fitness_pet.yaml
    11_hotel_hostel.yaml
    12_entertainment.yaml
  sources/
    source_manifest.yaml
```

建议新增或改造服务：

```text
backend/services/location_profile_service.py
  compute_location_profile(real_data) -> dict

backend/services/business_model_service.py
  load_business_model(model_id) -> dict
  classify_business_model_family(business_type, category="", brand_name="") -> str
  compute_business_model_snapshot(real_data, location_profile, business_type, category="", brand_name="", store_size=0) -> dict
  build_business_field_checklist(...) -> list
  build_business_caliber_explanation(...) -> str
  build_revenue_disclaimer(...) -> str

backend/services/report_enrichment_service.py
  enrich_report_business_context(report, real_data, business_type="", category="", brand_name="", store_size=0, is_fallback=False) -> dict
```

统一补齐字段：

```json
{
  "location_profile": {},
  "business_model_snapshot": {},
  "business_model_version": "snack_fast_food@2026-06-15.v1",
  "caliber_explanation": "",
  "evidence_summary": {},
  "data_boundary": "",
  "revenue_disclaimer": "",
  "field_checklist": []
}
```

接入点：

1. main.py  
   normal / retry / fallback 保存前统一调用 enrich_report_business_context。

2. fallback_report_service.py  
   不再维护另一套完整 field_checklist 逻辑，改为调用 business_model_service。

3. report_decision_service.py  
   使用 business_model_snapshot 的 fit_signals / red_flags 生成成立条件和降级条件，但 verdict 三档仍只由 score 决定。

4. storage_service.py  
   HTML 只渲染 report_json 中的字段，不自行生成核验清单。

5. uniapp/src/pages/report-detail/index.vue  
   小程序只渲染 report_json 中的字段，展示逻辑与 HTML 保持一致。

## 九、验收测试

新增测试建议：

```text
backend/tests/check_business_model_rules.py
backend/tests/check_location_profile_rules.py
backend/tests/check_report_enrichment_service.py
```

必须覆盖：

1. 34 个前台业态全部能归入 12 个族群。
2. category-only 情况也能识别托管/小饭桌/作业辅导，不只依赖 brand_name。
3. 同一 real_data 切换多个业态，location_profile 完全一致。
4. 同一 real_data 切换多个业态，business_model_snapshot 合理不同。
5. 教育托管报告不得出现外卖骑手、取餐、出餐速度、上座率、排队、午晚高峰堂食。
6. 教育培训和教育托管必须生成不同 field_checklist。
7. 暗竞品型业态 0 POI 竞品不得输出市场空白明显、先发优势、品类切入空间较好。
8. 小吃快餐 200m 无竞品但 1000m 同类多时，必须提示远场供给和低客流空白风险。
9. HTML 和小程序展示字段来自同一 report_json。
10. normal / retry / fallback 都包含 location_profile、business_model_snapshot、revenue_disclaimer。
11. 所有用户可见字段不得触发 report_fact_guard 和 poi_name_guard。
12. 每个 YAML 必须通过 schema 校验，字段缺失时测试失败。

必须跑的回归：

```text
python tests/check_report_fact_guard.py
python tests/check_industry_rigor_rules.py
python tests/check_fallback_report.py
python tests/check_p05_report_quality.py
python tests/check_business_model_rules.py
python tests/check_location_profile_rules.py
python tests/check_report_enrichment_service.py
npm run build:mp-weixin
```

## 十、实施节奏

Phase 0：方案冻结与 schema 定义，1-2 天

交付：

```text
backend/knowledge/business_model_schema.yaml
backend/knowledge/location_profile_schema.yaml
backend/knowledge/source_card_schema.yaml
```

Phase 1：打样 5 个高优先级族群，1-2 周

优先族群：

1. 小吃快餐
2. 茶饮烘焙
3. 教育托管
4. 便利超市
5. 美业健身宠物

交付：

```text
location_profiles.yaml
01_snack_fast_food.yaml
03_beverage_dessert.yaml
04_convenience_supermarket.yaml
07_education_childcare.yaml
10_beauty_fitness_pet.yaml
```

验收样本：

1. 宝鸡文理学院高新校区，麻辣烫，小餐饮，50 平方米。
2. 九悦香都，教育托管，100 平方米。
3. 九悦香都，教育培训，100 平方米。
4. 高竞品餐饮点。
5. 同品牌分店风险点。
6. 非餐饮业态点。

Phase 1 即使暂不交付 `08_education_training.yaml`，也必须把教育培训样本测试写出来：

```text
九悦香都 + 教育托管：
0 POI 竞品 = 暗雷，重点提示托管/小饭桌/家庭式托管可能漏收录。

九悦香都 + 教育培训：
0 POI 竞品同样不能写成强优势，但原因不同；应按聚集型/信任型逻辑保守表达，提示需求密度、课程品类匹配、满班率和品牌信任需要现场验证。
```

如果 `08_education_training.yaml` 尚未完成，教育培训样本先走保守 fallback 或 generic education_training 模板，但测试用例必须保留，防止后续补 08 时忘记这类判断差异。

Phase 2：补齐全部 12 个族群，2 周

交付：

```text
02_group_dining.yaml
05_pharmacy.yaml
06_specialty_retail.yaml
08_education_training.yaml
09_laundry_clinic.yaml
11_hotel_hostel.yaml
12_entertainment.yaml
```

验收：

1. 全 34 个前台业态归类完成。
2. 每个族群至少 3 个样本。
3. 同地址换业态测试通过。

Phase 3：接入 normal / retry / fallback / HTML / 小程序，1 周

要求：

1. 报告保存前统一 enrichment。
2. HTML 和小程序只渲染 report_json。
3. fallback 不再维护独立模板。
4. 所有回归通过。

Phase 4：持续样本回归

每个族群维护：

1. 3-5 个固定验收样本。
2. 典型误判案例。
3. 禁止表达清单。
4. 评分封顶案例。
5. 每次业务模型改动必须跑样本回归。

## 十一、不做的事

1. 不把整本书直接喂给模型。
2. 不在产品报告里复制书籍或报告长段原文。
3. 不把非知识框架功能塞进本方案。
4. 不放宽 report_fact_guard.py。
5. 不放宽 poi_name_guard.py。
6. 不重构 prompt 主体来掩盖业务模型问题。
7. 不让 HTML 或小程序各自生成业务判断。
8. 后续如需新增资料或规则，必须走 source card → YAML source_refs → service/report_json → regression 流程。

## 十二、第一批执行清单

建议先执行以下文件：

```text
docs/location_knowledge_distillation_plan.md
backend/knowledge/location_profiles.yaml
backend/knowledge/business_model_schema.yaml
backend/knowledge/location_profile_schema.yaml
backend/knowledge/business_models/01_snack_fast_food.yaml
backend/knowledge/business_models/07_education_childcare.yaml
backend/services/location_profile_service.py
backend/services/report_enrichment_service.py
backend/tests/check_location_profile_rules.py
backend/tests/check_business_model_rules.py
backend/tests/check_report_enrichment_service.py
```

第一批不要急着做 12 个 YAML。先用小吃快餐和教育托管打穿闭环：

```text
真实样本 -> location_profile -> business_model -> report_json enrichment -> HTML/小程序展示 -> 自动化测试
```

这条链路跑通后，再扩展茶饮、便利店、美业。
