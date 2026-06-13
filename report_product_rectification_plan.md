# 址得选报告产品整改方案

## 一、整改背景

址得选当前已经进入真实用户深度使用阶段，问题不再只是“某个类目报错”或“某个页面适配不好”，而是报告产品本身的可信度、解释力、稳定性和用户心理预期开始接受真实市场检验。

用户购买或消耗点数生成报告时，内心并不是想看一篇很长的分析文章，也不是想看一堆技术指标。用户真正想要的是：

1. 这个位置值不值得继续看。
2. 最大机会是什么。
3. 最大风险是什么。
4. 周边竞品到底多不多。
5. 我接下来去现场应该重点看什么。
6. 这份报告是不是靠谱，数据是不是有依据。
7. 如果系统失败，是否扣点，是否退款，是否值得再试一次。

所以整改不能只围绕后端 bug，也不能只追求“能生成”。报告必须从“系统输出”升级为“用户决策辅助产品”。

## 二、可行性验证结论（基于当前代码）

本方案总体可行，但不能按“从零建设”执行。当前系统已经具备报告产品化改造的关键底座，真正缺口集中在用户可见报告结构、失败体验闭环、现场核验清单和后台健康度运营。

### 1. 当前已经具备的技术基础

后端已经具备以下能力：

- `/api/analyze` 已生成本次请求追踪 `request_id`，并在关键日志中记录用户、业态、坐标、`config_key`、`rigor_enabled` 等信息。
- 计费逻辑已经改为 AMap 采集成功后再提交扣点，失败路径具备自动退款收口。
- `real_data` 已同时包含 `direct_competitors_*`、`substitute_competitors_*`、`traffic_anchors_*`，具备统一事实口径的基础。
- `fact_guard` 已能校验直接竞品、替代消费、客流锚点、旧口径字段、禁止决策语言、财务单点数字和 POI 名称幻觉。
- LLM 首次失败后已有 retry 链路，retry 仍失败时已有 fallback 保守报告。
- `fallback_report_service.py` 已经是纯函数，不依赖 LLM，能够基于真实数据生成保守摘要。
- 后台报告库已经能识别 `ai / retry_ai / fallback` 类型，并支持报告类型筛选。

前端已经具备以下能力：

- 首页分析流程已经能解析 SSE step 和 error。
- 报告详情页已经能展示综合评分、维度分、摘要、优势、风险、竞争环境、周边数据、位置范围、周边业态、数据质量和行动建议。
- 用户侧主体文案基本已经使用“选址分析 / 商业分析 / 数据报告”，没有大面积暴露技术词。

### 2. 当前尚不能满足“用户想看的报告”的关键缺口

虽然系统已经能生成报告，但还没有稳定生成一份真正符合用户心理预期的“选址体检报告”。主要缺口如下：

- 报告首屏仍以评分卡和维度雷达为主，缺少“一句话结论、最大优势、最大风险、下一步动作”。
- 后端输出缺少稳定的用户首屏字段，例如 `verdict`、`top_strength`、`top_risk`、`next_action`、`field_checklist`。
- `action_plan` 当前偏经营建议，数量通常只有 3 条，不足以替代 5-8 条现场核验任务。
- fallback 能生成保守摘要，但用户侧没有明显展示“保守版数据摘要”标识。
- 失败时后端有 `request_id` 日志，但前端没有展示失败编号，也没有明确展示“本次是否扣点 / 是否自动退还”。
- 后台有报告库，但还没有报告生成健康度模块，缺少按业态、失败阶段、fallback 比例、fact_guard 原因的聚合视图。
- 后台配置和报告库仍保留部分 `AI` 字样；如果这些文案进入审核材料、默认分享配置或用户可见页面，需要统一改为“选址分析 / 数据分析”。

### 3. 已验证结果

本轮静态核对和测试结果如下：

- `tests/check_report_fact_guard.py`：188 PASS，0 FAIL。
- `tests/check_industry_rigor_rules.py`：2178 PASS，0 FAIL。
- 使用现有 fallback 模拟“小吃快餐”报告时，可以生成分数、摘要、直接竞品、替代消费、优势和行动建议，但行动清单只有 3 条，风险表达偏泛，不足以满足“现场核验清单”的产品目标。

因此，本方案的执行重点不是重新推翻报告链路，而是在现有链路上补齐用户可见结构：让报告从“长文分析结果”变成“首屏可判断、数据可解释、现场可执行、失败可安心”的决策辅助产品。

### 4. 执行原则

本次整改不要优先改评分公式、POI 分类规则、行业权重或 `fact_guard` 语义。现有规则测试已经通过，应先在不破坏事实校验和行业配置语义的前提下补齐报告结构和展示层。

如果后续必须调整 prompt、评分、POI 分类或事实校验逻辑，必须先确认当前行业配置字段是否仍被报告生成链路使用，并补充回归样本后再改。

## 三、用户心理洞察

### 1. 用户不是来验证技术能力的

用户不会关心 direct_competitors、substitute、fact_guard、fallback 这些技术概念。用户只关心：

- 这个店能不能继续谈。
- 租下来会不会亏。
- 周边有没有人。
- 竞品是不是太多。
- 报告有没有帮他少走弯路。

因此，用户侧报告不能暴露技术过程，应该把复杂规则翻译成简单商业语言。

### 2. 用户最怕“看起来专业但不可信”

报告如果出现很精确的分数、复杂维度和长篇判断，但用户发现附近明明有很多餐饮，报告却说竞品少，他会立即失去信任。

用户对报告的信任不是来自字数，而是来自三个东西：

- 数据能对上现实。
- 口径讲得清楚。
- 结论不过度承诺。

### 3. 用户需要的是“可行动建议”，不是泛泛分析

深度使用用户会连续看多个点。他们需要报告告诉他下一步怎么做：

- 今天中午去门口数人流。
- 去问隔壁商户租金。
- 看外卖骑手是否容易停车。
- 看学校放学动线是否经过门口。
- 观察同类店午高峰是否排队。

如果报告只是写“客流较好、竞争可控、需现场核验”，用户会觉得空。

### 4. 用户对失败极其敏感

用户点击生成报告时，已经投入了时间、注意力和点数。此时失败会带来强烈不安：

- 是不是我填错了。
- 点数会不会没了。
- 还要不要再点一次。
- 是不是系统不稳定。
- 客服能不能帮我查。

所以失败提示必须给安全感，而不是技术词。

### 5. 用户天然会把报告当成“半决策”

即使系统声明“不构成投资建议”，用户仍然会把分数和结论作为重要依据。因此报告必须克制表达，不能说“推荐开店”“值得投资”“强烈建议入驻”。更合适的表达是：

- 适合作为候选点继续核验。
- 需要重点核验租金和客流。
- 数据表现偏弱，建议谨慎核验或降低候选优先级。
- 当前仅支持初筛判断。

## 四、理想报告应该是什么样

用户真正想要的不是长报告，而是一份“选址体检报告”。

建议报告结构改为五层。

### 最小可用报告 schema

为避免整改停留在文案层，建议后端完整报告、retry 报告和 fallback 报告都逐步统一支持以下用户首屏字段：

```json
{
  "decision_snapshot": {
    "verdict": "可优先现场核验 / 谨慎考察 / 应列为低优先级候选点",
    "one_sentence": "一句话说明当前点位为什么值得或不值得继续看",
    "score": 0,
    "top_strength": "最大优势，必须引用真实半径数据",
    "top_risk": "最大风险，必须引用真实半径数据",
    "next_action": "下一步最应该做的一件现场核验动作"
  },
  "evidence_summary": {
    "direct_competitors": {"200m": 0, "500m": 0, "1000m": 0},
    "substitute_consumption": {"200m": 0, "500m": 0, "1000m": 0},
    "traffic_anchors": {"200m": 0, "500m": 0, "1000m": 0},
    "key_pois": {
      "residential": {"200m": 0, "500m": 0, "1000m": 0},
      "schools": {"200m": 0, "500m": 0, "1000m": 0},
      "office": {"200m": 0, "500m": 0, "1000m": 0},
      "transport": {"200m": 0, "500m": 0, "1000m": 0}
    }
  },
  "caliber_explanation": "竞品、替代消费、客流锚点的用户可理解说明",
  "field_checklist": [
    "现场核验任务1",
    "现场核验任务2",
    "现场核验任务3",
    "现场核验任务4",
    "现场核验任务5"
  ],
  "report_type": "normal / retry / fallback",
  "data_boundary": "数据来源和风险边界说明"
}
```

短期可以不立即删除旧字段，继续保留 `summary`、`advantages`、`disadvantages`、`dimension_scores`、`details`、`action_plan` 兼容旧页面；但新报告详情页首屏必须优先消费 `decision_snapshot` 和 `field_checklist`。如果新字段缺失，再回退到旧字段拼装。

### 第一层：一句话结论

用户打开报告第一屏必须马上知道：

- 总体判断：可优先现场核验 / 谨慎考察 / 应列为低优先级候选点
- 总分
- 最大优势
- 最大风险
- 下一步动作

示例：

> 当前点位适合作为候选点继续核验。优势是 500 米内居住和学校客群较集中；主要风险是 200 米内替代餐饮较多，需现场确认午晚高峰客流是否被分流。

### 第二层：关键数据摘要

用户要快速看到真实数据：

- 直接竞品：200m / 500m / 1000m
- 替代消费：200m / 500m / 1000m
- 客流锚点：200m / 500m / 1000m
- 住宅、小区、学校、写字楼、交通、停车、医院、商场

所有数据都要明确半径，禁止“周边很多”“附近较少”这种模糊表达。

### 第三层：为什么这么判断

这一层解决用户信任问题。要解释：

- 为什么这些算直接竞品。
- 为什么这些只是替代消费。
- 为什么学校、小区、写字楼是客流来源。
- 为什么这个分数高或低。

示例：

> 本报告将同品类门店计为直接竞品，将其他可能分流消费预算的餐饮计为替代消费。替代消费不参与竞品数量评分，但会作为分流风险提示。

### 第四层：现场核验清单

这是用户最需要的行动层。

每份报告必须输出 5-8 条现场核验任务，例如：

- 工作日 11:30-13:00 观察门前实际人流。
- 晚高峰 18:00-20:00 观察同类门店上座率。
- 问询相邻商户真实租金和转让费。
- 检查外卖骑手停车和取餐是否方便。
- 确认门头可见度、遮挡物和道路对侧导流情况。
- 教育培训类需观察放学动线和家长等待空间。
- 小吃快餐类需观察午高峰出餐速度和外卖单量。

### 第五层：数据说明和风险边界

报告必须明确：

- 数据来源于地图 POI 和系统规则分析。
- POI 可能存在更新延迟。
- 报告仅用于选址初筛。
- 不替代现场调研和投资决策。
- 需要结合租金、合同、装修、人员、证照等因素判断。

## 五、当前报告与软件问题清单

### P0 问题 1：报告事实口径不统一

当前系统同时存在：

- 原始 POI 数据
- 脱水后 POI 数据
- 旧竞品字段 competitors_*
- 新竞品字段 direct_competitors_*
- 替代消费 substitute_*
- 客流锚点 traffic_anchors_*
- prompt 中被清零的数据
- guard 校验使用的 real_data
- fallback 自己生成的数据摘要

这些口径没有完全统一，导致报告容易出现前后解释不一致。

整改方向：

- 新报告只以脱水后的 real_data 为事实来源。
- 直接竞品只认 direct_competitors_*。
- 替代消费只认 substitute_competitors_*。
- 客流锚点只认 traffic_anchors_*。
- 旧 competitors_* 只做兼容，不进入新报告主展示和评分解释。

### P0 问题 2：竞品定义用户看不懂

用户看到“竞品少”时，会自然理解为“附近类似生意少”。但系统内部可能把部分门店算成替代消费或客流锚点。

如果不解释，用户会认为报告不准。

整改方向：

- 报告中增加“竞品口径说明”。
- 明确区分直接竞品、替代消费、客流锚点。
- 对小吃快餐、教育培训、酒店、茶饮等高频业态提供用户可理解的口径解释。

### P0 问题 3：业态规则覆盖不完整

部分业态有较完整的 direct/substitute/anchor 规则，部分业态仍可能走旧口径。深度用户切换业态后，会感觉报告质量不稳定。

整改方向：

- 梳理所有前台业态。
- 每个业态必须绑定一个规则组。
- 规则组至少定义：直接竞品、替代消费、客流锚点、无关 POI、核心半径。
- 对没有成熟规则的业态，只允许输出保守分析，不输出强结论。

### P0 问题 4：fallback 没有成为真正安全网

fallback 应该是全业态稳定可用的保守摘要，但现在仍可能因 guard 或文案触发失败。

整改方向：

- fallback 不写具体 POI 名称。
- fallback 只写真实数量和类别。
- fallback 不输出推荐、不输出强判断。
- fallback 必须 100% 通过 guard。
- fallback 页面或报告内明确标记为“保守版数据摘要”。

### P0 问题 5：失败体验不闭环

当前用户看到“分析服务暂不可用”或“报告未通过事实校验”，不知道是否扣点、是否退款、是否应该重试。

整改方向：

- 用户侧错误提示只保留业务语言。
- 每次失败生成 request_id。
- 明确提示是否扣点、是否自动退款。
- 提供“联系客服并复制失败编号”入口。
- 后台可按 request_id 查完整失败原因。

### P0 问题 6：报告分数解释不足

用户看到总分后，会关心为什么是这个分。当前分数来自模型维度分和 normalize 加权，但用户侧缺乏解释。

整改方向：

- 每个维度分后增加“分数原因”。
- 总分旁边增加“主要拉高项 / 主要拉低项”。
- 不展示复杂公式，但要展示商业解释。

### P1 问题 7：报告过长但行动价值不够突出

长报告不等于高价值。用户更需要决策摘要和现场核验清单。

整改方向：

- 第一屏给结论和最大风险。
- 中部给数据和解释。
- 底部给现场核验清单。
- 折叠低频细节，减少手机端阅读压力。

### P1 问题 8：业态选择对用户不友好

用户不一定知道该选“小吃快餐”“快餐店”“小吃店”还是“餐饮”。选错会影响报告。

整改方向：

- 业态选择增加搜索和示例。
- 增加“适合做什么”的说明。
- 用户输入品牌后，系统可提示更匹配的业态。

### P1 问题 9：品牌/特色字段的重要性没有说明

系统会根据品牌词影响竞品分类，但用户不知道这个字段很关键。

整改方向：

- 字段提示改为“例如：麻辣烫、小学生托管、社区洗衣、精品咖啡”。
- 提示用户写得越具体，报告越准确。

### P1 问题 10：平台审核风险未完全产品化处理

前端去 AI 只是表面。报告详情页、分享页、后台配置、默认标题都要统一口径。PDF 和长图导出不进入近期整改范围。

整改方向：

- 用户侧统一使用“选址分析”“商业分析”“数据报告”。
- 不出现 AI、人工智能、大模型、深度合成等词。
- 如果未来恢复 AI 表达，则必须按平台要求增加类目和显著说明。

## 六、完整整改方案

本节补充本轮用户视角评审后需要纳入方案的增量点。原则是：只增加能落地、能验收、能复用现有代码底座的能力；不把 PDF、长图导出、复杂自动排序等非必要形态塞进近期版本。

### 1. 生成前预期管理

目标：用户点击“生成报告”前，必须知道本次会消耗什么、失败怎么处理、报告能解决什么问题。

产品要求：

- 生成按钮附近展示“本次预计消耗 1 点；会员权益内不额外扣点；生成失败将按规则自动退回”。
- 展示“本报告适合用于商铺选址初筛，不替代现场调研、租金测算和实际商业判断”。
- 展示“填写地址、业态、品牌/特色越准确，竞品识别和现场核验建议越准确”。
- 增加“你将获得”的轻量预览：一句话结论、关键数据摘要、竞品口径解释、现场核验清单。

技术落点：

- `uniapp/src/pages/home/index.vue`
  - 在生成按钮上方增加预期说明卡片。
  - 点数余额优先读取本地 `getUser()` 的 `balance_credits`，必要时复用当前用户信息刷新逻辑。
  - `onAnalyze()` 前如点数不足，引导到充值页，不进入 SSE 请求。
- `uniapp/src/utils/auth.js`
  - 继续使用 `balance_credits`、`membership_days_left`、`is_member` 等现有字段，不新增临时本地字段。
- `backend/services/billing_service.py`
  - 保持实际扣点仍以后端为准，前端只做预期展示，不做计费判断来源。
- 后续如果不同业态有不同消耗点数，再新增 `/api/analyze/quote`；当前固定 1 点阶段不需要新增接口。

验收标准：

- 新用户在点击生成前能看到本次预计消耗点数。
- 用户能理解失败是否会退点。
- 用户能理解报告适合“初筛”，不适合替代现场和投资决策。

### 2. 现场核验清单任务化

目标：把 `field_checklist` 从阅读型建议升级为可执行任务，但短期不做复杂任务系统。

建议将 `field_checklist` 从字符串数组逐步升级为对象数组：

```json
{
  "field_checklist": [
    {
      "title": "核验午高峰门前人流",
      "time_window": "工作日 11:30-13:00",
      "action": "在门前固定位置观察 15 分钟，记录经过门店正面动线的人流情况",
      "pass_hint": "以记录和对比为主，暂不输出绝对开店阈值",
      "record_method": ["拍照", "备注", "通过/存疑/不通过"],
      "risk_type": "客流不足",
      "evidence_refs": ["traffic_anchors_500m", "key_pois.schools_500m"]
    }
  ]
}
```

技术落点：

- `backend/services/fallback_report_service.py`
  - fallback 必须输出 5-8 条结构化核验任务。
  - 任务来自真实数据和业态模板，不输出没有依据的强阈值。
- `backend/prompts/location_analysis.py`
  - prompt 要求完整报告也输出同样结构。
  - 明确禁止模型编造“必须达到多少人流才通过”的硬阈值；如无行业样本，只输出 `pass_hint`。
- `uniapp/src/pages/report-detail/index.vue`
  - 优先渲染对象数组；旧字符串数组继续兼容。
  - 每条任务展示时间、动作、记录方式、对应风险。
  - 第一版只做展示，不要求把勾选状态同步到后端。

验收标准：

- 每份新报告至少有 5 条核验任务。
- 每条任务包含核验时间、核验动作、记录方式、对应风险。
- 没有样本支撑时，不生成看似精确但不可验证的人流阈值。

### 3. 数据充分度和报告可信度

目标：让用户知道这份报告的数据是否足以支撑判断，避免把“数据不足下的保守结论”误读成强判断。

建议新增报告字段：

```json
{
  "data_sufficiency": {
    "level": "sufficient / moderate / insufficient",
    "label": "数据较充分 / 数据一般 / 数据不足",
    "summary": "可用于初筛，但需重点现场核验午晚高峰客流",
    "reasons": [
      "500 米内有直接竞品和替代消费数据",
      "当前业态已启用严谨规则",
      "本报告不是 fallback"
    ],
    "flags": {
      "has_direct_competitors_data": true,
      "has_substitute_data": true,
      "has_traffic_anchor_data": true,
      "rigor_enabled": true,
      "is_fallback": false,
      "poi_sparse": false
    }
  }
}
```

技术落点：

- `backend/main.py`
  - 在 `real_data` 生成后、保存报告前，调用确定性函数补充 `data_sufficiency`。
  - 不让模型自行判断充分度，避免幻觉。
- 可新增 `backend/services/report_quality_service.py`
  - 输入：`real_data`、`business_type`、`config_key`、`rigor_enabled`、`report_type`。
  - 输出：`data_sufficiency` 对象。
  - 初版规则：
    - `report_type=fallback` 最高只能是 `moderate`，多数情况下为 `insufficient` 或 `moderate`。
    - 未启用 rigor 或核心竞品/替代/锚点数据缺失，降级。
    - 1000 米 POI 总量过少或关键半径为空，标记 `poi_sparse=true`。
- `backend/services/fallback_report_service.py`
  - fallback 同样写入 `data_sufficiency`，并使用保守文案。
- `uniapp/src/pages/report-detail/index.vue`
  - 首屏或关键数据摘要旁展示“数据较充分 / 数据一般 / 数据不足”标签。
  - 点击或展开后显示原因列表。

验收标准：

- normal、retry、fallback 报告都能返回 `data_sufficiency`。
- fallback 不会显示“数据较充分”。
- POI 稀疏或规则不完整时，前端能明确提示“仅作保守参考”。

### 4. 用户纠错和反馈闭环

目标：用户发现报告和现场不一致时，有轻量反馈入口，后台能沉淀真实误差样本。

第一版反馈分类：

- 这里有竞品没识别。
- 地址位置不准确。
- 业态选错了，想重新生成。
- 这份报告不符合现场情况。
- 其他问题。

技术落点：

- 复用现有 `uniapp/src/pages/profile/feedback.vue` 和 `/api/feedback` 底座。
- `uniapp/src/pages/report-detail/index.vue`
  - 增加“反馈这份报告”入口。
  - 提交时带上 `report_uuid`、`request_id`、`business_type`、`category`、用户备注。
- `backend/routers/feedback.py`
  - 扩展反馈入参，允许可选 `report_uuid`、`request_id`、`category`、`metadata`。
- `backend/database.py` / 反馈表迁移逻辑
  - 如现有 `feedbacks` 表没有这些字段，追加 `report_uuid`、`request_id`、`category`、`status`、`metadata_json`。
- `backend/admin/index.html`
  - 意见反馈列表增加分类、关联报告、处理状态。
  - 支持按“报告质量问题”筛选。

验收标准：

- 用户能在报告详情页提交报告相关反馈。
- 后台能看到反馈属于哪份报告、哪类问题。
- 反馈不会自动修改 POI 分类、评分或报告规则，必须经过人工审核后再沉淀为规则样本。

### 5. 报告生成成功但用户不满意的售后规则

目标：把“技术成功但用户认为不准”的问题纳入客服闭环，而不是简单归为系统成功。

产品规则：

- 技术失败、保存失败、fallback 失败：按现有自动退款/退点规则处理。
- 报告质量投诉：用户提交问题，后台人工判断。
- 可选处理：客服解释、补偿点数、协助重新生成、标记质量样本。
- 不承诺“用户不满意自动退款”，避免滥用和计费混乱。

技术落点：

- `backend/admin/index.html`
  - 反馈列表展示“补偿点数”入口时，复用现有用户点数调整能力。
  - 增加反馈状态：待处理 / 已解释 / 已补偿 / 已纳入样本 / 不成立。
- `backend/routers/admin.py`
  - 如果当前点数调整接口已经覆盖客服补偿，则只需在反馈处理动作中记录 `credits_granted` 和处理备注。
- `backend/models/db_models.py`
  - 反馈记录保留 `credits_granted`，新增状态字段时要兼容旧数据。

验收标准：

- 客服能定位质量投诉对应报告。
- 客服能记录处理结论和是否补偿。
- 质量投诉能沉淀为后续回归样本，而不是散落在聊天记录里。

### 6. 多点对比提前，但只做轻量候选点池

目标：支持真实用户连续看点，但不在当前阶段做复杂自动排序。

P1 后段先做：

- 候选点池：复用现有收藏和报告记录。
- 标签状态：待看 / 已现场看 / 淘汰 / 重点跟进。
- 用户备注：租金、转让费、面积、门头、现场观察。
- 基础对比：地址、业态、总分、最大风险、数据充分度、报告类型。

暂不做：

- 自动判断哪个点最值得租。
- 自动综合租金风险排序。
- PDF/长图导出。

技术落点：

- `uniapp/src/pages/favorites/index.vue`、`uniapp/src/components/tab/FavoritesPanel.vue`
  - 在收藏点上增加状态和备注展示。
- `backend/models/db_models.py`
  - 如 `SavedLocation` 现有字段不足，增加 `status`、`note`、`rent`、`transfer_fee`、`area`、`frontage_note`。
- `backend/routers/favorites.py`
  - 增加更新收藏备注和状态的接口。
- `uniapp/src/pages/records/index.vue` 或收藏页
  - 增加基础对比视图，先展示字段，不做复杂评分。

验收标准：

- 用户能把多个点标为待看、重点跟进或淘汰。
- 用户能记录租金、转让费、面积等现场信息。
- 用户能在列表中看到每个候选点的最大风险和数据充分度。

### 7. 小程序分享优化，不做 PDF/长图

目标：利用小程序原生分享能力，不增加导出形态。

保留：

- 分享报告页。
- 分享标题模板。
- 分享封面配置。
- 分享页引导生成自己的报告。

删除或后置：

- PDF 导出。
- 长图导出。
- 独立分享摘要文件。

技术落点：

- `uniapp/src/pages/report-detail/index.vue`
  - 继续使用 `createShareToken()` 和 `fetchSharedReport()`。
  - 分享标题优先使用 `decision_snapshot.verdict`、地址、业态，例如“XX 地址选址初筛：谨慎考察”。
  - 分享进入页默认展示决策卡、数据充分度、最大风险和现场核验入口。
  - 分享页隐藏内部字段：`ai`、`retry_ai`、`fallback`、`request_id`、技术错误信息。
- `backend/routers/records.py`
  - 分享接口返回用户可见字段，不返回后台诊断字段。
- `backend/admin/index.html`
  - 分享配置继续保留首页分享图和报告分享图，不新增 PDF/长图配置。

验收标准：

- 用户能通过小程序原生分享打开报告详情。
- 被分享者第一屏能看到结论、风险和数据充分度。
- 分享页不暴露技术字段和审核敏感词。

### 8. 支付链路作为并行专项，不塞进报告 P0

目标：报告整改提升用户继续使用意愿，点数直购必须并行规划，但不要和报告 P0 互相阻塞。

技术落点：

- `uniapp/src/pages/profile/recharge.vue`
  - 继续承接 SKU 选择和支付入口。
- `uniapp/src/utils/api.js`
  - 继续使用 `fetchSkus`、`createVirtualPrepay`、`payExistingOrder`、`queryVirtualOrder`、`reconcileVirtualOrder`。
- `backend/routers/virtual_pay.py`
  - 按现有虚拟支付链路验收：SKU selection -> createPrepay -> requestPayment -> queryOrder -> balance/member refresh -> failure/cancel states -> admin visibility。
- `backend/admin/index.html`
  - 订单列表和退款能力继续作为支付验收的一部分。

验收标准：

- 报告 P0 不依赖支付改造上线。
- 支付专项必须单独完成端到端验收，不能只验前端按钮。
- 用户支付成功后点数或会员权益能刷新，后台订单可查。

### 9. P0 拆分为 P0-A 和 P0-B

P0-A：止血稳定，优先上线。

1. 失败提示、扣点/退款状态、失败编号。
2. `request_id` 全链路日志和用户侧展示。
3. fallback 稳定通过并明确标记“保守版数据摘要”。
4. 用户侧审核敏感词清理。
5. 不改评分、POI 分类、行业权重和 `fact_guard` 语义。

P0-B：首屏可判断。

1. 生成前预期管理。
2. `decision_snapshot` 首屏决策卡。
3. `field_checklist` 结构化展示。
4. `data_sufficiency` 简版标签。
5. 分享页展示用户可见摘要，不暴露技术字段。

### 10. 用户测试验收

工程验收之外，必须增加真实用户视角验收：

- 新用户 10 秒内能说出“可优先核验 / 谨慎 / 低优先级”。
- 用户能复述最大风险。
- 用户能根据报告列出下一步现场动作。
- 用户能理解直接竞品、替代消费、客流锚点的区别。
- 用户遇到失败时知道点数有没有退、失败编号在哪里。
- 连续生成多份报告后，用户能在收藏/记录里形成候选点排序或淘汰判断。

### 11. 当前执行状态总览（2026-06-13）

本方案不删除已完成内容。已完成部分作为当前报告产品的基线能力保留，后续修改必须保证不回退；待执行部分作为下一轮派工清单；后续部分进入 P1/P2 专项。

状态说明：

- `[已完成]`：已经开发、回归测试或真实样本验收通过，后续只做回归保护。
- `[部分完成]`：核心能力已落地，但真实体验暴露出收尾项。
- `[待执行]`：下一轮必须执行，执行完成后才能关闭 P0.5。
- `[后续]`：进入 P1/P2 专项，不阻塞 P0.5-final。

当前状态：

| 状态 | 阶段 | 当前结论 |
| --- | --- | --- |
| `[已完成]` | P0-A 止血稳定 | 失败卡片、`request_id`、结构化 `billing_status`、退款提示、fallback 稳定性和禁词稳态已完成。 |
| `[已完成]` | P0-B 首屏可判断 | 生成前预期、首屏决策卡展示框架、数据充分度、分享脱敏、分享标题模板已完成；normal 报告稳定补齐 `decision_snapshot` 纳入 P0.5-final。 |
| `[部分完成]` | P0.5 主体验收 | HTML 标题/业态/时间/POI 合计、公交数据、竞争评分、低分解释、fallback 禁词矩阵已完成；仍需 P0.5-final 收尾。 |
| `[待执行]` | P0.5-final | footer 去 AI 兜底、normal/retry/fallback 统一 `decision_snapshot`、营收免责、`action_plan` 与 `field_checklist` 分离、小餐饮替代消费过滤药店/医疗 POI。 |
| `[后续]` | P1 体验提升 | 学校/校园客流源展示归并、小餐饮竞品分层、数据充分度文案精确化、强相关 POI 优先展示、公交去重。 |
| `[后续]` | P1 后段 / P2 | 候选点池、多点对比、后台健康度、质量投诉样本、支付链路端到端验收。 |

## 七、代码执行路径与整改落点

本节从代码角度说明报告是如何生成的，以及每个整改点应该落在哪些文件，避免整改停留在产品描述层。

### 1. 前端提交路径

入口文件：

- `uniapp/src/pages/home/index.vue`
- `uniapp/src/utils/api.js`

执行路径：

1. 用户填写地址、业态、品牌/特色、面积。
2. `home/index.vue` 中 `validate()` 校验必填项。
3. `onAnalyze()` 组装 payload：
   - `address`
   - `location.lng`
   - `location.lat`
   - `business_type`
   - `brand_name`
   - `store_size`
   - `industry_id`
4. 调用 `api.analyzeLocation(payload)`。
5. `api.js` 请求后端 `/api/analyze`。
6. 前端解析 SSE 返回：
   - step 1：数据采集
   - step 2：数据脱水和比对
   - step 3：商业分析
   - step 4：报告完成
7. 成功后跳转报告详情页。
8. 失败时显示 `analyzeErr`。

当前问题：

- 前端错误提示不能区分失败阶段。
- 用户不知道是否扣点、是否退款。
- 错误文案有时过于技术化。

整改落点：

- `uniapp/src/utils/api.js`
  - 保留后端 SSE error，不要全部覆盖成“分析服务暂不可用”。
  - 区分 HTTP 500、SSE error、timeout、401、402。
- `uniapp/src/pages/home/index.vue`
  - `friendlyAnalyzeError()` 改成用户可理解文案。
  - 失败时展示“本次是否扣点/是否自动退还/失败编号”。

### 2. 后端入口路径

入口文件：

- `backend/main.py`

核心函数：

- `analyze_location()`
- `event_stream()`

执行路径：

1. `/api/analyze` 接收前端请求。
2. 读取当前登录用户。
3. 检查会员/点数权限。
4. 创建本次请求的 `refund_idem_key`。
5. 进入 SSE 流 `event_stream()`。
6. 逐步执行：
   - AMap 数据采集
   - prompt 构建
   - 模型生成
   - JSON 解析
   - normalize
   - fact_guard
   - retry
   - fallback
   - DB 保存
   - 返回报告

当前问题：

- 失败日志缺少统一 request_id。
- 用户侧错误和后端真实错误没有清晰映射。
- fallback 失败时定位成本高。

整改落点：

- `backend/main.py`
  - 每次请求生成 `request_id`。
  - 所有关键日志带上 `request_id`。
  - 记录 `business_type / industry_id / brand_name / store_size / config_key / rigor_enabled`。
  - 记录失败阶段：
    - `AMAP_FAILED`
    - `LLM_TIMEOUT`
    - `LLM_HTTP_ERROR`
    - `JSON_PARSE_FAILED`
    - `PAYLOAD_INVALID`
    - `FACT_GUARD_FAILED`
    - `RETRY_FAILED`
    - `FALLBACK_FAILED`
    - `DB_SAVE_FAILED`

### 3. AMap 数据采集路径

入口文件：

- `backend/services/amap_service.py`

核心函数：

- `collect_location_data()`
- `AmapService.collect_all()`
- `classify_poi_type()`
- `classify_poi_rigor()`

执行路径：

1. `main.py` 根据业态获取 `config_key`。
2. 根据 `config_key` 获取行业配置。
3. 调用 `collect_location_data(lng, lat, amap_type, config_key, business_type, brand_name)`。
4. 高德接口采集 1000 米内 POI。
5. 对 POI 做基础分类：
   - 住宅
   - 写字楼
   - 学校
   - 餐饮
   - 快餐
   - 茶饮
   - 酒店
   - 医院
   - 停车
   - 商场
6. 做名称脱水：
   - 非真实学校剔除
   - 医院科室归并
   - 地铁出口归并
   - 餐饮父类重算
7. 做严谨业态分类：
   - `direct`
   - `substitute`
   - `anchor`
   - `irrelevant`
   - `pass`
8. 输出 `LocationData`。

关键产物：

- `stats_200m / stats_500m / stats_1000m`
- `poi_lists`
- `direct_competitors_200m / 500m / 1000m`
- `substitute_competitors_200m / 500m / 1000m`
- `traffic_anchors_200m / 500m / 1000m`
- `competitors_200m / 500m / 1000m` 旧口径

当前问题：

- 新旧竞品口径并行。
- 部分业态没有完整 rigor 规则。
- `competitors_*` 仍可能影响 prompt 和报告理解。

整改落点：

- `backend/services/amap_service.py`
  - 明确 `direct/substitute/anchor` 为新报告主口径。
  - 保留旧字段兼容，但不进入新报告主展示。
  - 给无 rigor 业态打数据质量标记。
- `backend/prompts/industry_config.py`
  - 梳理所有前台业态对应规则组。
  - 每个规则组必须有直接竞品、替代消费、客流锚点、无关 POI 规则。

### 4. Prompt 构建路径

入口文件：

- `backend/prompts/location_analysis.py`

核心函数：

- `build_system_prompt()`
- `build_analysis_prompt()`

执行路径：

1. `main.py` 获取行业配置。
2. `build_system_prompt()` 生成系统规则：
   - 输出 JSON 格式
   - 评分维度
   - 禁止投资建议
   - 禁止编造 POI
   - 替代消费不计入直接竞品
3. `build_analysis_prompt()` 注入真实数据：
   - 三层半径数据表
   - direct 竞品列表
   - substitute 替代消费列表
   - anchor 客流锚点列表
   - 业态策略
   - 预判优势/劣势

当前问题：

- prompt 里包含大量规则，模型仍可能混淆。
- 环境降噪在 prompt 拷贝上做，和 real_data 校验口径可能不完全一致。
- 个别业态特判容易继续膨胀。

整改落点：

- `backend/prompts/location_analysis.py`
  - 增加“事实/推断/核验”输出结构。
  - 强化直接竞品、替代消费、客流锚点解释。
  - 避免继续增加单业态硬编码特判。
  - 用户侧文案去 AI 化。

### 5. 模型调用与 JSON 解析路径

入口文件：

- `backend/main.py`
- `backend/ai_providers/unified.py`

执行路径：

1. `generate_llm_response(prompt)` 调用模型。
2. `_extract_json()` 从模型返回中提取 JSON。
3. `json.loads()` 转成 dict。
4. `_validate_report_payload()` 检查结构：
   - `details`
   - `advantages`
   - `disadvantages`
   - `summary`
   - `dimension_scores`
5. 结构失败则进入错误处理和退款。

当前问题：

- 模型失败、JSON 失败、结构失败在用户侧体验接近。
- 后台需要更清楚区分。

整改落点：

- `backend/main.py`
  - 对模型调用失败、JSON 失败、结构失败分别记录。
  - 用户侧统一成业务友好文案，后台保留真实技术原因。

### 6. normalize 与评分路径

入口文件：

- `backend/services/runtime_config.py`

核心函数：

- `normalize_report_result()`

执行路径：

1. 固定 8 个维度顺序。
2. 如果模型少返回某个维度，尝试从 detail 文本补分。
3. 根据行业权重计算总分。
4. 覆盖模型原始总分。

当前问题：

- 用户不知道总分怎么来的。
- 缺失维度补分可能不稳定。

整改落点：

- 不建议立即改评分公式。
- 产品层先增加“主要拉高项/主要拉低项”解释。
- 后续再评估维度补分逻辑。

### 7. 事实校验路径

入口文件：

- `backend/report_fact_guard.py`
- `backend/services/poi_name_guard.py`

核心函数：

- `validate_report_fact_consistency()`
- `check_poi_name_hallucination()`
- `check_poi_context_mismatch()`
- `check_direct_competitor_count_mismatch()`

执行路径：

1. 检查报告维度是否完整。
2. 检查数字是否和 real_data 一致。
3. 检查是否有异常大数字。
4. 检查是否使用旧口径字段。
5. 检查是否出现投资建议。
6. 检查是否出现精确财务单点数字。
7. 检查 POI 名称是否在白名单。
8. 检查 substitute/anchor 是否误写成竞品。
9. 检查直接竞品数量是否膨胀。

当前问题：

- 分句级数字检查可能跨子句误杀。
- POI 泛称黑名单靠不断补词，不够可持续。
- 误杀会直接影响用户生成体验。

整改落点：

- `backend/report_fact_guard.py`
  - 优化数字与关键词就近匹配。
  - 避免一句话中 direct 和 substitute 互相误判。
- `backend/services/poi_name_guard.py`
  - 从黑名单补丁升级到泛称语法模式。
  - 保留真实名称白名单机制。

### 8. Retry 路径

入口文件：

- `backend/main.py`
- `backend/services/poi_name_guard.py`

执行路径：

1. 首次 fact_guard 失败。
2. 构造错误摘要。
3. `build_retry_name_constraints()` 生成：
   - forbidden_names
   - allowed_names
   - allowlist_empty
4. 带着约束重新调用模型。
5. retry 结果重新跑全部 guard。
6. retry 通过则使用 retry 报告。
7. retry 失败则进入 fallback。

当前问题：

- retry 对用户不可见。
- retry 失败原因需要后台留痕。

整改落点：

- `backend/main.py`
  - retry 失败必须记录 retry_fe。
  - 返回报告时可在后台记录 report_type：`normal / retry / fallback`。

### 9. Fallback 路径

入口文件：

- `backend/services/fallback_report_service.py`
- `backend/main.py`

执行路径：

1. retry 失败后调用 `build_fallback_report(real_data, address, business_type, brand_name, store_size)`。
2. fallback 不调用模型。
3. 只根据 real_data 生成保守报告。
4. fallback 也必须跑：
   - `validate_report_fact_consistency`
   - `check_poi_name_hallucination`
   - `check_poi_context_mismatch`
   - `check_direct_competitor_count_mismatch`
5. 通过则保存 fallback 报告，并退还点数。
6. 不通过则失败并退款。

当前问题：

- fallback 对所有业态使用固定逻辑。
- fallback 通过率必须提升到 100%。
- 用户不知道自己拿到的是 fallback。

整改落点：

- `backend/services/fallback_report_service.py`
  - fallback 文案改成“保守版数据摘要”。
  - 不写具体 POI 名称。
  - 不写强结论。
  - 只写事实数量、风险提示、核验建议。
- `backend/main.py`
  - 保存 `report_type=fallback` 或在 report_json 中明确 `_fallback_report=true`。
- 前端报告详情页
  - fallback 报告展示“保守版数据摘要”标识。

### 10. 保存与退款路径

入口文件：

- `backend/main.py`
- `backend/services/billing_service.py`
- `backend/services/storage_service.py`

执行路径：

1. 报告通过后创建 `AnalysisRecord`。
2. 写入：
   - user_id
   - brand_desc
   - address
   - latitude
   - longitude
   - business_type
   - store_size
   - overall_score
   - report_json
   - report_uuid
3. 调用 `save_report()` 保存报告文件。
4. 成功后返回 `record_id`。
5. 如果失败，根据错误类型退款：
   - 模型服务失败
   - JSON 解析失败
   - DB 保存失败
   - fact_guard 失败
6. `refund_credits()` 做幂等退款。

当前问题：

- 用户侧对退款状态不敏感。
- 后台缺少失败与退款联动视图。

整改落点：

- `backend/main.py`
  - 错误返回带 request_id。
  - 失败日志记录 refund 是否执行。
- 后台
  - 增加失败记录和退款状态查询。

### 11. 报告详情展示路径

入口文件：

- `uniapp/src/pages/report-detail/index.vue`

执行路径：

1. 根据 `record_id` 拉取报告。
2. 渲染总分、维度分、优势、劣势、周边数据、位置范围、明细。
3. 用户阅读、分享或收藏。

当前问题：

- 报告展示偏“长文结果”，不够像决策工具。
- report_type 没有明显呈现。
- 竞品口径解释不足。
- 缺少现场核验清单。

整改落点：

- `uniapp/src/pages/report-detail/index.vue`
  - 首屏增加一句话结论。
  - 增加最大优势、最大风险、下一步动作。
  - 增加竞品口径说明。
  - 增加现场核验清单。
  - fallback 报告加明显标识。

### 12. 后台运营路径

入口文件：

- `backend/admin/index.html`
- `backend/routers/admin.py`
- 数据表：可新增或复用分析记录、操作日志、账单记录

当前缺口：

- 没有报告生成失败列表。
- 没有按业态统计成功率。
- 没有 fallback 比例。
- 没有 fact_guard 失败原因聚合。
- 客服无法通过失败编号快速定位。

整改落点：

- 后台新增“报告生成健康度”模块：
  - 生成成功率
  - 失败率
  - fallback 率
  - 按业态统计
  - 按失败阶段统计
  - request_id 查询
  - 扣点/退款状态

### 13. 建议新增数据字段

为支持运营闭环，建议新增报告生成日志表或轻量日志字段。

建议字段：

- `request_id`
- `user_id`
- `business_type`
- `industry_id`
- `brand_name`
- `store_size`
- `lng`
- `lat`
- `config_key`
- `rigor_enabled`
- `stage`
- `status`
- `error_type`
- `error_summary`
- `fact_errors`
- `retry_errors`
- `fallback_errors`
- `report_type`
- `billing_source`
- `billing_status`
- `created_at`

短期如果不建表，至少 print 日志必须包含这些字段，方便线上查问题。

### 14. 代码整改优先级（按当前代码现状修订）

P0 立即执行：

1. `backend/main.py`
   - 已具备：`request_id`、扣点延后、失败退款收口、retry、fallback。
   - 需补齐：SSE error 事件带 `request_id`、`billing_status`、`billing_source`、`error_stage` 等用户可展示字段。
   - 需补齐：统一失败阶段枚举，至少覆盖 `AMAP_FAILED / LLM_TIMEOUT / LLM_HTTP_ERROR / JSON_PARSE_FAILED / PAYLOAD_INVALID / FACT_GUARD_FAILED / RETRY_FAILED / FALLBACK_FAILED / DB_SAVE_FAILED`。

2. `backend/services/fallback_report_service.py`
   - 已具备：基于 `real_data` 的保守版报告、无 LLM 依赖、不写具体 POI 名称。
   - 需补齐：输出 `decision_snapshot`、`field_checklist`、`caliber_explanation`、`report_type=fallback`。
   - 需补齐：现场核验清单扩展到 5-8 条，并按业态给出更具体的核验动作。

3. `uniapp/src/utils/api.js`
   - 已具备：解析 SSE step、保留 SSE error。
   - 需补齐：透传结构化 error 字段，不只返回字符串。
   - 需补齐：区分 `request_id`、退款状态、失败阶段，供首页错误卡片展示。

4. `uniapp/src/pages/home/index.vue`
   - 已具备：用户友好错误映射。
   - 需补齐：失败时展示“本次是否扣点 / 是否自动退还 / 失败编号”。
   - 需补齐：“复制失败编号并联系客服”入口。

5. `uniapp/src/pages/report-detail/index.vue`
   - 已具备：评分、维度、摘要、优势风险、竞争环境、周边数据、行动建议。
   - 需补齐：首屏决策卡片，优先展示 `decision_snapshot`。
   - 需补齐：明显展示 `report_type=fallback` 时的“保守版数据摘要”标识。

P1 紧接执行：

1. `backend/prompts/location_analysis.py`
   - 新增 `decision_snapshot`、`field_checklist` 输出要求。
   - 将现场核验任务从泛泛建议改为 5-8 条可执行动作。
   - 保留现有事实校验红线，不扩大单业态硬编码特判。

2. `backend/services/amap_service.py`
   - 已具备 direct/substitute/anchor 数据。
   - 需补齐：在输出数据质量说明中标注是否启用 rigor 规则、哪些业态仍为保守分析。

3. `backend/prompts/industry_config.py`
   - 已有 14 个 master rigor 规则和多类样本测试。
   - 需继续补齐 partial 业态样本库，优先覆盖用户高频业态。

4. `backend/report_fact_guard.py` 和 `backend/services/poi_name_guard.py`
   - 当前测试通过，不建议作为第一优先级继续大改。
   - 后续只针对真实误杀样本做小步修正，并同步补测试。

P2 产品体验与运营闭环：

1. `uniapp/src/pages/report-detail/index.vue`
   - 折叠长文细节，把“可读、可信、可行动”放到首屏和第二屏。
   - 增加竞品口径说明卡片。

2. `backend/admin/index.html` / `backend/routers/admin.py`
   - 新增报告生成健康度后台。
   - 新增失败阶段、fallback 比例、fact_guard 原因、业态成功率、request_id 查询。

3. 用户侧和分享侧文案
   - 继续使用“选址分析 / 商业分析 / 数据报告”。
   - 不在用户侧出现 `AI`、`大模型`、`深度合成` 等审核敏感词。

### [已完成] 阶段一：P0-A 止血稳定

周期：1-2 天。

目标：不再让用户频繁看到失败，不再输出明显混乱报告。

工作项：

1. SSE error 事件补充结构化字段：`request_id`、`error_stage`、`billing_source`、`billing_status`。
2. 首页失败卡片展示：失败编号、是否扣点、是否自动退还、联系客服入口。
3. fallback 报告补齐 `report_type=fallback`、`decision_snapshot`、`field_checklist`。
4. fallback 现场核验清单扩展到 5-8 条。
5. 清理用户侧和分享侧审核敏感词。
6. 禁止继续按单个业态打补丁；真实误杀必须补测试。

验收标准：

- 失败时用户知道是否扣点和退款。
- 失败时用户能复制失败编号。
- 后台日志能通过 `request_id` 查到失败原因。
- fallback 不再因泛称误杀失败。
- fallback 报告能明确标记为“保守版数据摘要”。
- 小程序审核敏感词不再出现在用户侧。
- `check_report_fact_guard.py` 全部通过。

### [已完成] 阶段二：P0-B 首屏可判断

周期：3-5 天。

目标：让用户生成前放心，打开报告后能立即判断，并看到数据充分度。

工作项：

1. 首页生成前展示预计消耗点数、失败退点说明、报告适用边界。
2. 报告首屏改为 `decision_snapshot` 决策卡片。
3. 增加简版 `data_sufficiency`：数据较充分 / 数据一般 / 数据不足。
4. 报告详情和分享页展示最大优势、最大风险、下一步动作。
5. 分享页隐藏 `ai / retry_ai / fallback / request_id` 等内部字段。
6. fallback 和 normal 报告均兼容旧字段，缺新字段时前端可降级拼装。

验收标准：

- 用户生成前知道本次预计消耗和失败退点规则。
- 用户 10 秒内知道这个点是否值得继续看。
- 用户能说出报告最大风险。
- fallback 报告不会被误认为完整深度报告。
- 分享页不暴露技术字段和审核敏感词。

### [后续] 阶段三：P1 统一口径和任务化核验

周期：1-2 周。

目标：建立用户能看懂的唯一事实来源，并让报告变成可现场执行的核验工具。

工作项：

1. 新报告首屏和竞争环境卡片只使用 `direct/substitute/anchor`。
2. 旧 `competitors_*` 从主报告展示和评分解释中移除，仅保留兼容。
3. 报告增加竞品口径说明：直接竞品、替代消费、客流锚点。
4. prompt 和 fallback 都输出 `evidence_summary`。
5. 每个维度分输出一句用户能理解的分数原因。
6. `field_checklist` 升级为结构化对象，包含时间、动作、记录方式和对应风险。
7. 增加报告质量反馈入口，复用现有意见反馈后台。
8. 建立或补齐核心业态回归样本，优先覆盖小吃快餐、茶饮咖啡、中餐正餐、火锅烧烤、便利店、生鲜、教育、酒店、生活服务、夜经济。

验收标准：

- 报告中“竞品”含义稳定。
- 替代消费不再被写成直接竞品。
- 客流锚点不再被写成竞品。
- 用户能理解为什么竞品少但替代消费多。
- 用户能带着核验清单去现场。
- 用户能在报告详情页提交质量反馈。
- `check_industry_rigor_rules.py` 全部通过。
- 10 个核心业态样本均能生成 `decision_snapshot`、`data_sufficiency` 和结构化 `field_checklist`。

### [后续] 阶段四：P1 后段 / P2 工作台和后台运营闭环

周期：1-2 周，可与阶段三并行。

目标：从被动修 bug 变成主动监控报告健康度，并支持用户连续看点。

工作项：

1. 新增报告生成失败列表。
2. 新增业态成功率统计。
3. 新增 fallback 比例统计。
4. 新增 fact_guard 失败原因统计。
5. 新增用户扣点/退款状态追踪。
6. 新增按 request_id 查询报告生成链路。
7. 后台报告库中的 `AI / retry_ai / fallback` 内部类型可保留，但后台展示文案建议改为“完整报告 / 修正报告 / 保守摘要”。
8. 收藏/记录增加候选点状态、备注、租金、转让费、面积、门头情况。
9. 多点对比先做基础字段对比，不做自动选址排序。
10. 支付链路作为并行专项验收，不阻塞报告 P0 上线。

验收标准：

- 客服能通过失败编号定位问题。
- 研发能看出哪个业态最容易失败。
- 产品能判断哪些业态适合开放，哪些要暂缓。
- 客服能确认用户本次失败是否已扣点、是否已退还。
- 用户能把多个候选点标记为待看、已现场看、淘汰或重点跟进。

## 八、报告产品规范

### 1. 结论表达规范

推荐使用：

- 适合作为候选点继续核验。
- 数据表现较好，但仍需确认租金和实际客流。
- 当前风险较集中，建议谨慎核验或降低候选优先级。
- 本位置更适合先做线下观察。

禁止使用：

- 推荐开店。
- 强烈建议入驻。
- 值得投资。
- 可以放心开。
- 品类空白红利。
- 稳赚。

### 2. 竞品表达规范

必须写清楚半径：

- 200 米内 0 家同品类直接竞品。
- 500 米内 3 家替代消费门店。
- 1000 米内 8 个客流锚点。

禁止：

- 周边竞品很少。
- 竞争压力很低。
- 附近没有威胁。

### 3. 数据表达规范

事实和推断必须分开。

示例：

- 事实：500 米内有 3 所学校、1 个住宅小区。
- 推断：对学生和家庭客群有一定支撑。
- 核验：需观察放学时段人流是否经过门店。

### 4. fallback 表达规范

fallback 不能假装是完整报告。

建议文案：

> 本报告为保守版数据摘要。系统已基于采集到的周边数据生成初筛参考，部分深度分析未展开，建议结合现场核验。

## 九、核心指标

整改后需要持续看以下指标：

1. 报告生成成功率。
2. fallback 触发率。
3. fact_guard 失败率。
4. 每个业态成功率。
5. 用户重试率。
6. 失败自动退款成功率。
7. 报告详情页停留时长。
8. 用户分享/收藏报告比例。
9. 客服咨询中“报告不准”占比。
10. 审核失败次数。
11. 报告反馈提交量和分类占比。
12. 数据不足报告占比。
13. 候选点状态使用率。
14. 点数直购支付成功率。

## 十、优先级排序

### [已完成] P0-A 必须立即做

1. 统一错误提示和退款提示。
2. 增加 request_id 和后台失败日志。
3. fallback 全业态稳定通过。
4. 停止单业态补丁式修复。
5. 用户侧 AI 敏感词清理。

### [已完成] P0-B 紧接执行

1. 生成前预期管理：预计消耗点数、失败退点、报告适用边界。
2. 报告首屏重构：`decision_snapshot` 决策卡片。
3. 简版数据充分度：数据较充分 / 数据一般 / 数据不足。
4. fallback 和分享页使用用户可理解文案，不暴露技术字段。

### [后续] P1 尽快做

1. 统一 direct/substitute/anchor 报告口径。
2. 增加竞品口径说明。
3. 现场核验清单升级为结构化任务。
4. 增加报告质量反馈入口和后台处理状态。
5. 补齐核心业态规则。
6. 建立核心业态回归样本库。

### [后续] P1 后段 / P2 持续优化

1. 候选点池：收藏、备注、状态、租金、转让费、面积、门头情况。
2. 基础多点对比，不做复杂自动排序。
3. 后台业态健康度。
4. 报告质量投诉样本沉淀。
5. 支付链路端到端验收。
6. PDF / 长图导出暂不做，除非后续真实用户高频提出留档或打印需求。

## 十一、[待执行] 真实体验验收后的 P0.5-final 执行方案

本节基于 2026-06-13 真实体验评估和“宝鸡文理学院高新校区 · 麻辣烫 · 小餐饮”样本验收补充。当前 P0.5 主体已经修对：标题去 AI、业态和时间一致、POI 三层半径展示、公交不再恒为 0、竞争评分不再只看 200 米、低分解释更具体、数据充分度和营收测算已具备基础价值。

但真实用户体验仍暴露出几个必须收尾的问题：HTML footer 残留旧口径、normal 报告缺 `decision_snapshot`、经营建议被当成现场核验清单、营收测算缺少模型免责、小餐饮替代消费混入药店/医药超市。P0.5-final 的目标不是重构评分体系，而是把“首屏判断一致、明显错分修正、用户展示口径稳定”这三件事收住。

### 1. P0.5-final 范围边界

本轮必须做：

1. HTML footer 去掉残留 `AI` 字样，包括后台配置旧值兜底。
2. normal / retry / fallback 报告统一补齐 `decision_snapshot`。
3. 营收测算旁增加模型估算免责。
4. 小程序和 HTML 将 `action_plan` 与 `field_checklist` 分开展示。
5. 小餐饮替代消费中过滤药店、医药超市、医疗类 POI，并同步重算三层半径计数。

本轮不要做：

1. 不要大改 prompt 来强制 LLM 输出新字段。
2. 不要放宽或削弱 `report_fact_guard.py`。
3. 不要在 P0.5-final 里做学校/校园归并。
4. 不要在 P0.5-final 里重做小餐饮竞品分层和评分校准。
5. 不要把 PDF、长图、多点对比、候选点工作台塞进本轮。

### 2. 统一首屏决策：新增确定性 `report_decision_service.py`

问题：

- fallback 已有 `decision_snapshot`，但 normal 报告仍可能只有 `executive_summary`、`advantages`、`disadvantages`、`warning` 和 `action_plan`。
- 同一个点位如果一次走 normal、一次走 fallback，首屏结论可能不一致。
- 直接改 prompt 风险较高，可能影响现有 `check_report_fact_guard.py` 和 `check_industry_rigor_rules.py` 回归。

执行方案：

新增后端服务：

```text
backend/services/report_decision_service.py
```

提供统一函数：

```python
compute_decision_snapshot(
    score,
    real_data,
    business_type,
    brand_name="",
    advantages=None,
    disadvantages=None,
    action_plan=None,
    is_fallback=False,
)
```

输出字段：

```json
{
  "verdict": "可优先现场核验 / 谨慎考察 / 应列为低优先级候选点",
  "one_sentence": "一句话说明当前点位为什么可看或为什么要降级",
  "score": 58,
  "top_strength": "最大优势，优先来自真实半径数据或 advantages[0]",
  "top_risk": "最大风险，优先来自 warning / disadvantages[0]",
  "next_action": "下一步最重要的现场核验动作",
  "fit_condition": "什么条件下这个点成立",
  "stop_condition": "什么情况下应降级或暂停投入谈判成本"
}
```

落点：

1. `backend/main.py` 在保存 normal / retry 报告前，如果缺少 `decision_snapshot`，调用 `compute_decision_snapshot()` 补齐。
2. `backend/services/fallback_report_service.py` 不再维护另一套 `_verdict()` 判断，改为调用同一个 `compute_decision_snapshot()`。
3. `uniapp/src/pages/report-detail/index.vue` 优先展示 `decision_snapshot`，并兼容 `fit_condition`、`stop_condition`。
4. `backend/services/storage_service.py` HTML 首屏同样展示 `decision_snapshot`。

验收标准：

- 同一份 `real_data` 下，normal 补全和 fallback 生成的 `verdict` 档位一致。
- `verdict` 不包含 `推荐开店 / 建议推进 / 可以投资 / 值得投资 / 最终决策` 等禁词。
- `check_report_fact_guard.py`、`check_industry_rigor_rules.py`、`check_p05_report_quality.py` 全部通过。
- 用户打开报告首屏能看到：综合判断、一句话结论、最大优势、最大风险、下一步、成立条件、降级条件。

### 3. HTML footer 去 AI：配置和兜底同时处理

问题：

- 标题和 subtitle 已改为“商业选址初筛报告”，但 HTML footer 仍可能从后台旧配置读到 `AI 选址分析 · 商业选址初筛参考`。

执行方案：

1. 更新后台默认配置和 placeholder：

```text
址得选 · 商业选址初筛参考
```

2. `backend/services/storage_service.py` 在构建 HTML footer 时做旧值兜底替换：

```text
AI 选址分析 -> 址得选
AI选址分析 -> 址得选
AI 多维度分析 -> 选址规则分析
```

3. `backend/admin/index.html` 中涉及报告 footer、分享标题、报告描述的默认文案同步去 AI。

验收标准：

- 新生成 HTML 的 title、h1、subtitle、footer 均不出现 `AI`。
- 后台配置仍是旧值时，新 HTML 也不会把 `AI` 字样带到用户可见页面。
- 小程序分享页不暴露 `ai / retry_ai / fallback / request_id` 等内部字段。

### 4. 营收测算增加模型免责

问题：

- 三档营收测算是报告最有价值的内容之一，但也最容易被用户当成承诺。

执行方案：

在小程序和 HTML 的营收测算模块旁增加固定提示：

```text
以上为模型估算，不代表实际经营结果；需结合现场客流、租金、转让费、出餐能力和外卖能力复核。
```

验收标准：

- 小程序报告详情页营收测算附近能看到模型免责。
- HTML 导出版营收测算附近能看到模型免责。
- `report_fact_guard` 不因免责文案触发财务单点数字误判。

### 5. `action_plan` 与 `field_checklist` 分开展示

问题：

- normal 报告常见 `action_plan` 是“发优惠券、推套餐、上线外卖”等经营动作，不是真正的现场核验任务。
- 当前如果前端把旧 `action_plan` 降级渲染成现场核验清单，用户会觉得“核验清单语义错位”。

执行方案：

1. 小程序和 HTML 展示逻辑调整：

```text
有 field_checklist：展示“现场核验清单”
无 field_checklist 但有 action_plan：展示“经营建议”
两者都有：两个模块分别展示
```

2. 不再把 `action_plan` 自动伪装成 `field_checklist`。
3. `field_checklist` 缺失时，首屏 `next_action` 可由 `compute_decision_snapshot()` 给出一条确定性现场核验动作，但不生成完整清单。

验收标准：

- normal 报告没有 `field_checklist` 时，小程序不显示“现场核验清单”标题。
- 经营建议仍能展示，但标题为“经营建议”或“运营建议”。
- fallback 或后续新报告有结构化 `field_checklist` 时，展示时间、动作、记录方式、通过信号、降级/淘汰信号。

### 6. 小餐饮替代消费过滤药店/医疗 POI，并同步重算计数

问题：

- 真实样本 JSON 中 `substitute_list` 出现 `怡康医药超市`、`众信医药超市`。对小餐饮来说，药店、医药超市、医院、诊所不应进入替代消费。
- 如果只从列表里删除 POI，但不重算 `substitute_competitors_*`，会出现“报告说 500 米内 5 家替代消费，但列表只有 3 家”的旧问题。

执行方案：

仅对餐饮/小餐饮/小吃快餐相关业态启用保守过滤：

```text
过滤关键词：
药店、药房、医药、医药超市、药业、药品、药械、医院、诊所、门诊、医疗、卫生室

过滤类别：
pharmacy、hospitals、clinics、medical
```

同步重算这些字段：

```text
substitute_competitors_200m
substitute_competitors_500m
substitute_competitors_1000m
substitute_list
substitute_list_200m
substitute_list_500m
substitute_list_1000m
```

半径列表处理规则：

1. 如果 `substitute_list_200m / 500m / 1000m` 字段存在，必须尊重现有分半径列表，只对对应列表分别过滤。
2. 如果字段存在且值为 `[]`，说明该半径确实为 0，不能触发从总表重拆。
3. 判断字段是否存在必须使用：

```python
"substitute_list_500m" in real_data
```

禁止使用：

```python
not real_data.get("substitute_list_500m")
```

4. 如果某个分半径字段不存在，才允许从 `substitute_list` 按 `distance` 拆出该半径列表。
5. `distance` 缺失或无法解析的 POI 不进入 200 / 500 / 1000 米计数；可保留在总列表或从替代消费中移除，但必须在日志中标记。

验收标准：

```text
len(filtered_substitute_list_200m) == substitute_competitors_200m
len(filtered_substitute_list_500m) == substitute_competitors_500m
len(filtered_substitute_list_1000m) == substitute_competitors_1000m
```

同时验收：

- 小餐饮报告中药店、医药超市、医院、诊所不进入替代消费。
- 报告正文、HTML、小程序展示的替代消费数字与列表一致。
- 空列表 `[]` 被视为合法数据，不被误判为字段缺失。
- `check_industry_rigor_rules.py` 和 `check_report_fact_guard.py` 全部通过。

### 7. P0.5-final 测试清单

新增或补齐测试：

1. normal 报告缺 `decision_snapshot` 时，保存前能确定性补齐。
2. fallback 和 normal 对同一份 `real_data` 的 `verdict` 档位一致。
3. `decision_snapshot` 用户可见字段不包含禁止决策语言。
4. HTML footer 即使读取旧后台配置，也不会出现 `AI`。
5. 小程序没有 `field_checklist` 时不展示“现场核验清单”。
6. 小餐饮替代消费中过滤药店/医药超市/医疗类 POI。
7. 三层半径替代消费计数和过滤后列表数量一致。
8. 空列表字段存在时不触发总表重拆。

回归命令：

```text
python tests/check_report_fact_guard.py
python tests/check_industry_rigor_rules.py
python tests/check_fallback_report.py
python tests/check_p05_report_quality.py
npm run build:mp-weixin
```

真实样本验收：

1. 宝鸡文理学院高新校区 · 麻辣烫 · 小餐饮 · 50 平方米。
2. 高竞品餐饮点。
3. 同品牌分店风险点。
4. 非餐饮业态点。

预期：

- normal 报告首屏有 `decision_snapshot`。
- fallback 报告仍能稳定保存。
- 替代消费不出现药店/医疗类 POI。
- 三种形态：JSON、小程序、HTML 核心判断一致。

## 十二、[后续] P1 体验提升执行方案

P1 的目标是把报告从“可信的初筛报告”提升为“更接近选址决策工具”。P1 可以动展示口径和部分统计口径，但必须分专题做，不能混在 P0.5-final 里。

### 1. 学校/校园客流源展示归并

问题：

- 用户看到“500 米内 13 所学校”会理解成 13 个独立学校；但真实情况可能是一个大学的多个学院、教学楼、服务中心。

P1 方案：

1. 先做展示归并，不急着改底层评分。
2. 保留原始 POI 数量用于内部诊断。
3. 前端和 HTML 增加“校园客流源”视图。

归并规则必须保守：

```text
仅对同一校园内的 POI 做聚合：
名称去掉学院 / 教学楼 / 服务中心 / 校区内设施等后缀后核心名称完全相同
且距离彼此 < 500m
```

禁止粗暴规则：

```text
不能仅因为都包含“宝鸡”或“学校”就归为一个教育集群。
不能把宝鸡中学和宝鸡文理学院归为同一学校。
```

展示示例：

```text
校园客流源：宝鸡文理学院高新校区 1 个
校园内部节点：学院、教学楼、服务中心等 12 个
```

### 2. 小餐饮竞品分层与评分校准

问题：

- 对麻辣烫来说，刀削面、面皮、沙县小吃、水饺更像强替代正餐，不一定是严格同品类直接竞品。
- 如果把它们全部算直接竞品，报告会夸大直接竞争；如果改成强替代，又会影响 competition score，需要重新校准。

P1 方案：

报告和前端展示分三层：

```text
同品类直接竞品：麻辣烫、冒菜、串串、麻辣香锅等
强替代正餐：米线、面皮、沙县、刀削面、水饺、快餐等
弱替代/配套消费：饮品、便利店、零食等
```

执行要求：

1. 不直接把 `direct_competitors_*` 简单降数量后上线。
2. 同步调整 competition score 和 category_advantage score。
3. 补一组小餐饮样本回归：麻辣烫、面皮、米线、炸鸡、快餐。
4. 报告文案说明“强替代正餐会分流消费预算，但不等同于同品类直接竞品”。

验收标准：

- 麻辣烫报告中沙县、刀削面、水饺不再被写成严格同品类直接竞品。
- 评分变化符合产品预期，不因直接竞品下降而过度乐观。
- 用户能理解“直接竞品少但强替代多”是什么意思。

### 3. 数据充分度表达精确化

问题：

- “数据较充分”容易让用户以为经营结论也充分。真实应表达为 POI 数据充分，经营数据仍需核验。

P1 方案：

将用户侧文案改为：

```text
POI 数据较充分，经营数据待现场核验
POI 数据一般，仅适合初筛
POI 数据不足，只能作为保守参考
```

验收标准：

- 小程序、HTML、分享页均使用更精确的数据充分度文案。
- 不再让用户误以为租金、客流、营收已经被充分验证。

### 4. 周边明细默认强相关，弱相关折叠

问题：

- 过长的银行、药店、美容美发、酒店列表会干扰小餐饮用户判断。

P1 方案：

小餐饮默认展示：

```text
学校 / 校园客流源
住宅
办公
公交 / 地铁
停车
同品类直接竞品
强替代正餐
外卖和取餐相关设施
```

默认折叠：

```text
银行
药店
美容美发
低相关酒店
其他泛生活服务
```

验收标准：

- 用户首屏和关键数据区先看到与本业态相关的数据。
- 弱相关 POI 不影响评分解释和首屏判断。

### 5. 公交站去重与弱化停运线路影响

问题：

- 公交站点可能因方向站、招呼站、同名变体、停运线路被重复放大。

P1 方案：

1. 按名称规范化 + 距离近似去重。
2. 对“招呼站”“临时站”“停运”做标记或降权。
3. 展示文案从绝对口径改为保守口径：

```text
500 米内约 8 个公交站点/线路节点，需以实际运营为准
```

验收标准：

- 公交不再恒为 0。
- 公交数量不因重复站点明显虚高。
- 报告说明公共交通数据需现场确认实际运营状态。

## 十三、最终判断

址得选当前最关键的整改，不是继续提高模型文案质量，而是先建立一套用户能信任的报告产品体系。

用户想要的不是一篇看起来专业的长文，而是一份能帮他降低选址风险的初筛工具：

- 看得懂。
- 信得过。
- 知道下一步做什么。
- 失败时不焦虑。
- 结论不过度承诺。

整改方向应该从“生成报告”转向“交付选址判断依据”。
