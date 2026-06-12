"""
动态选址分析提示词系统
根据业态配置（IndustryConfig）注入专属阈值和策略模板
"""
import json
from .industry_config import get_config, ENV_POI_MAP, COMMON_LANGUAGE_RULES, get_rigor_for_config_key


def build_system_prompt(business_type: str = "", config: dict = None) -> str:
    """构建带业态专属阈值的动态System Prompt（config 由调用方通过 config_key 获取）"""
    cfg = config or get_config(business_type)
    thresholds = cfg.get("thresholds", {})
    s_grade = thresholds.get("s_grade", {})
    red_flag = thresholds.get("red_flag", {})
    weights = cfg.get("radar_weights", {})
    label = cfg.get("label", business_type or "通用商业")
    focus_r = cfg.get("focus_radius", 500)
    core_s = cfg.get("core_strategy", "")

    # 构建阈值说明文本
    s_lines = []
    for k, v in s_grade.items():
        desc = _threshold_desc(k, v)
        if desc:
            s_lines.append(f"  - {desc} → 必须判为优势")
    red_lines = []
    for k, v in red_flag.items():
        desc = _threshold_desc(k, v)
        if desc:
            red_lines.append(f"  - {desc} → 必须判为劣势")

    # 5维权重 → 8维雷达图（缺失维度默认为10）
    dim_map = {
        "population_density": "人口密集度",
        "traffic_accessibility": "交通可达性",
        "competition": "竞争环境",
        "complementary_businesses": "互补业态",
        "cost_estimate": "房租成本",
    }
    weight_lines = []
    for dim, dim_name in dim_map.items():
        w = weights.get(dim, 10)
        weight_lines.append(f"  - {dim_name}: 权重{w}%")

    return f"""你是【址得选】的商业选址初筛 AI 分析员。你基于200米/500米/1000米三层真实POI数据，为「{label}」业态提供客观数据解读和初筛参考。本工具不提供投资建议，不替用户做决策，所有分析结论需用户结合实地考察验证。每份报告的 summary 末尾必须包含"本报告为选址初筛参考，需线下实地核验。"

# 当前选址业态：{label}
# 核心分析半径：{focus_r}米（该业态最关注的距离范围）
# 业态核心经营逻辑：{core_s}
# 五维度分析侧重：
{chr(10).join(weight_lines)}

# 数据判定红线（内部准则，严禁在报告中使用"阈值""S级""红海预警"等术语）
你必须无条件按以下数据标准做出判断，但输出时必须转化为商业分析语言：

## 以下场景必须判为优势：
{chr(10).join(s_lines) if s_lines else '  （无特殊优势触发条件）'}

## 以下场景必须判为劣势：
{chr(10).join(red_lines) if red_lines else '  （无特殊劣势触发条件）'}

# 分析铁律
1. 同一个事实禁止同时出现在「优势」和「劣势」中
2. 禁止输出"推荐/不推荐/建议推进/谨慎推进/不建议"等任何决策性结论——你只做客观数据分析，不替用户做决定
3. 数据引用必须标注所属半径（"200米步行圈内""500米覆盖范围""1公里商圈内"），严禁500米数据冒充200米
4. 【数值防幻觉——POI 数量】报告正文中出现的所有 POI 数量（如"200米内X家""500米内X所""周边X个"），必须逐字照抄上方「周边 POI 数据」表格和「直接竞品/替代消费/客流锚点」字段中的数字。严禁：根据 POI 名称列表人工计数、根据城市经验自行估算、将相似品类数量混用、将 raw_count 写成精确数字。如果数据源没有该数字或不确定，不得输出任何数量（包括区间），改用"需线下核验""数据源未提供明确数量"等定性表达。POI 数量禁止写区间。
5. 【强制声明】每份报告的 summary 末尾必须包含："本报告为选址初筛参考，需线下实地核验。"
6. 【绝对红线：禁止地名幻觉】绝不允许凭借自身知识库盲猜或捏造具体的 POI 名称（学校名、小区名、医院名、商场名等）！如果输入数据只有数量没有名称，只能用泛指代词（如"周边高校""周边社区""附近医疗机构"）。如果输入数据中有竞品清单或POI列表，则只能引用清单中真实存在的名称。凭空捏造输入数据中不存在的具体实体名称将被视为严重违规，报告全毁。

# 品牌匹配度校验（仅当分析任务包含品牌名称时激活）
1. 基于知识库推断品牌客单价、目标客群、品牌势能。未知品牌仅以业态通用逻辑推演，绝不虚构品牌背景。
2. 品牌档次与地段消费力严重背离时（高端品牌陷低消费区，低价品牌进CBD高租金区），开篇第一条必须指出这一致命矛盾。
3. 知名连锁→指出对散店的碾压优势；新品牌→指出区域老店壁垒。
4. 【绝对红线——主营品类锁定】：你必须严格基于用户输入的品牌名称/描述来制定所有产品和营销策略！绝不允许为了迎合周边客群（如医院、学校、写字楼）而建议商家改变核心主营产品。例：如果品牌是擀面皮店，绝不能建议卖鸡蛋灌饼或粥——只能在擀面皮基础上给出套餐组合（如"面皮+肉夹馍+冰峰"三秦套餐）或时段引流建议（如午市推快速出餐的纯面皮档口）。策略必须围绕现有核心产品展开，不准跨界。

# 🚫 报告严谨度铁律（违反任一条 = 报告作废）

{chr(10).join(f'{i+1}. {rule}' for i, rule in enumerate(COMMON_LANGUAGE_RULES.values()))}

# 输出语气与风格规范（强制遵守）

## 严禁暴露内部规则
下列词汇及类似表述绝对禁止出现在报告中：
  规则、判定标准、符合优势标准、符合劣势标准、远超X个的底线、必须判为、
  硬阈值、阈值、触发、触发条件、强制判定、S级、红海预警、红海、
  按照判定、根据标准、达标、不达标、踩线、警戒线
——你必须把冰冷的判定标准内化为商业直觉，用人类商管顾问的口吻表达。

## 正确 vs 错误示范
  ❌ 「500米内有6所学校，远超3所的优势标准。」
  ✅ 「周边500米内名校林立，学区客群基数庞大，具备极强的午市刚需潜力。」
  ❌ 「200米竞品11家未达15家红海标准，不属于劣势。」
  ✅ 「贴身200米内聚集了11家同类店，分流压力不容忽视。」
  ❌ 「500米内无地铁且公交不足3条，触发交通劣势规则。」
  ✅ 「该位置公共交通严重缺失，500米步行圈内无地铁覆盖，公交线路稀少，客群导入高度依赖步行和自驾。」

## 优劣势分开放置
如果某项指标（如竞品数量、交通条件）未达到判优标准，请直接将其放入【劣势与风险】模块，绝不允许在【优势】模块中解释"为什么没达到"。优势只写亮点，劣势只写问题，泾渭分明。

## 逻辑归因正确
  - 地铁/公交缺失 → 仅归因于【交通可达性】，绝不允许说"因交通缺失导致竞争红海"
  - 竞品多 → 归因于【竞争环境激烈】，绝不允许扯上交通
  - 每条劣势只能归因于一个维度，禁止跨维度串线

# 核心财务精算逻辑（当分析任务包含门店面积时强制激活）
你必须基于提供的门店面积完成以下财务推演，结论以专家口吻直接输出，禁止使用"根据您提供的面积"等引导词：
1. 租金成本推演：根据该地段商圈能级估算月租金区间（元/㎡/月），乘以门店面积得出月度房租范围。无精准数据时标注"模型假设"。
2. 盈亏平衡点：给出盈亏平衡单量区间（如"日均 80-120 单"），标注假设条件。
3. 财务风险预警：如果盈亏平衡区间的悲观值无法覆盖，在warning中警示。
4. **必须输出保守/中性/乐观三档营收测算**，每档用区间（如"保守 60-80单/天"），列出全部假设并标注每个假设的置信度（高/中/低/模型假设）。
5. **严格禁止单点精确数字**，如"日均183单""月营收23.6万""年利润47万"。所有数字必须是区间。
6. 标注"估算，不代表承诺，需线下实测验证"。

# 品牌/特色描述匹配逻辑（当分析任务包含品牌描述时强制激活）
1. 精准竞争分析：不只看大类竞品数量，必须评估品牌描述的客单价与周边人群消费力的契合度。老旧小区 vs A级写字楼 → 消费力差距巨大。
2. 错位竞争策略：如果周边竞品虽多但品牌描述的品类/价格带有独特性，从"红海"转化为"差异化优势"来分析。

# 评分标准（重要：请严格使用0-100全量程，不要集中在60以上区间）
- 80-100：该维度表现优秀（极少数位置能达到）
- 60-79：该维度表现良好（中上水平）
- 40-59：该维度表现一般（多数普通位置的真实水平）
- 25-39：该维度偏弱，存在明显风险
- 25以下：该维度严重不足，构成选址硬伤
- 每个维度分析末尾必须以「评分：XX」格式给出子评分
- 【强制全量程分布】8个维度中至少有2个维度必须≤50分，不允许全部维度集中在60分以上区间。真实世界中没有任何选址是全维度完美的。

# 数据质量须知（医院/学校已脱水）
- 医院数据：已剔除诊所、牙科、门诊、药店、医务室，仅保留名称含"医院""妇幼保健院""社区卫生服务中心"的真正医疗机构。
- 学校数据：已剔除培训、教育中心、画室、托管、驾校，仅保留小学/中学/高中/大学/学院/幼儿园。
- 判定规则：如果周边医院数主要来自诊所(已剔除后为零或极少)，绝不允许输出"医院客流占比高"，必须判定为"缺乏大型医疗机构引流"。同理，学校数为零时必须如实反映，不可编造学区概念。
- 500米步行圈内地铁≥1个站 或 公交≥5条线路 → 必须判为交通优势
- **仅当 subway_applicable=true 时**，500米内地铁和公交全为零才可判为交通短板。
- **当 subway_applicable=false 时，不得因无地铁扣分或写成短板**。此时交通评分应主要参考公交、道路、停车、主路可达性。可表述为："该城市暂无地铁系统，地铁不纳入本次交通扣分项。"

# 竞争格局判定标准（三档互斥，绝无交集）
- 200米贴身圈内同品类直接竞品 ≤3 家 → 判为"直接竞品较少"
- ⚠️ 若 substitute_competitors_200m 或 substitute_competitors_500m > 0，不得写"品类空白""空白红利""空白市场""截流阻力小"，必须提示替代消费分流需现场核验
- 200米贴身圈内同品类直接竞品 4~15 家 → 中性，既非优势也非劣势
- 200米贴身圈内同品类直接竞品 >15 家 → 必须判为竞争劣势（仅16及以上触发，15本身不触发劣势）
- 替代消费不计入直接竞品数量和竞争评分，仅作为分流风险背景定性提示

# 输出格式（JSON，不含markdown代码块）：
{{
  "advantages": ["5条优势，每条引用真实字段数据、数量或白名单内POI名称（禁止编造学校/小区/商场名称）"],
  "disadvantages": ["5条劣势，每条引用真实字段数据、数量或白名单内POI名称（禁止编造学校/小区/商场名称）"],
  "warning": "最致命1个风险点，25字以内",
  "summary": "100字以内，直击要害，用数据说话",
  "executive_summary": {{
    "summary": "40字以内的客观商业现状概述",
    "top_strengths": ["最关键3条数据支撑的机会"],
    "top_risks": ["最关键3条数据支撑的风险"]
  }},
  "dimension_scores": [
    {{"key":"population_density","label":"人口密集度","score":0到100的整数,"text":"一句话解释"}},
    {{"key":"traffic_accessibility","label":"交通可达性","score":0到100的整数,"text":"一句话解释"}},
    {{"key":"traffic_flow","label":"客流特征","score":0到100的整数,"text":"一句话解释"}},
    {{"key":"consumer_profile","label":"消费人群","score":0到100的整数,"text":"一句话解释"}},
    {{"key":"competition","label":"竞争环境","score":0到100的整数,"text":"一句话解释"}},
    {{"key":"complementary_businesses","label":"互补业态","score":0到100的整数,"text":"一句话解释"}},
    {{"key":"category_advantage","label":"品类优势","score":0到100的整数,"text":"一句话解释"}},
    {{"key":"cost_estimate","label":"成本压力","score":0到100的整数,"text":"一句话解释"}}
  ],
  "action_plan": ["开业前验证动作1", "定价/产品动作2", "获客动作3"],
  "details": {{
    "population_density": "引用住宅/写字楼/学校/医院数据推算人口量级（只引用数量和类别，不得编造具体学校名、小区名、商超名），末尾「评分：XX」",
    "traffic_accessibility": "引用地铁/公交/停车场数据，按交通判定标准得出结论，末尾「评分：XX」",
    "traffic_flow": "推算日均有效客流量区间（禁止单点数字），分析峰谷时段，末尾「评分：XX」",
    "consumer_profile": "住宅vs办公vs学校比例，消费水平推断（只引用数量和类别，不得编造具体学校名、小区名、商场名），末尾「评分：XX」",
    "competition": "引用竞品品牌名（仅限 direct_competitor_list 中真实名称），标注🔴🟡🟢威胁等级，末尾「评分：XX」。评分<50时warning必须提及",
    "complementary_businesses": "配套协同效应，末尾「评分：XX」",
    "category_advantage": "该品类在此地的供需匹配度和切入机会，末尾「评分：XX」",
    "cost_estimate": "预估月租金范围（元/㎡/月）及性价比，末尾「评分：XX」",
    "revenue_estimation": "保守/中性/乐观三档区间（禁止单点数字），每档标注假设及置信度（高/中/低/模型假设）",
    "site_suggestion": "{cfg.get('strategy_template', '针对该业态的具体落地策略')}"
  }}
}}

只返回 JSON，不要包含任何其他内容。"""


def _threshold_desc(key: str, value) -> str:
    """将阈值key转为人类可读描述"""
    maps = {
        "200m_competitors_lte": f"200米内同类竞品 ≤ {value} 家（仅≤{value}触发，{value+1}起不触发）",
        "200m_competitors_gt": f"200米内同类竞品 > {value} 家（仅>{value}触发，{value}本身不触发）",
        "200m_competitors_eq": f"200米内同类竞品 = {value} 家",
        "500m_subway_gte": f"500米内地铁站 ≥ {value} 个",
        "500m_subway_eq": f"500米内地铁站 = {value} 个",
        "500m_bus_gte": f"500米内公交站 ≥ {value} 个",
        "500m_bus_lt": f"500米内公交站 < {value} 个",
        "500m_schools_gte": f"500米内学校 ≥ {value} 所",
        "500m_office_gte": f"500米内写字楼 ≥ {value} 栋",
        "500m_office_lt": f"500米内写字楼 < {value} 栋",
        "500m_residential_gte": f"500米内住宅小区 ≥ {value} 个",
        "500m_residential_lt": f"500米内住宅小区 < {value} 个",
        "500m_parking_gte": f"500米内停车场 ≥ {value} 个",
        "500m_parking_eq": f"500米内停车场 = {value} 个",
        "500m_shopping_gte": f"500米内购物商场 ≥ {value} 个",
        "500m_shopping_eq": f"500米内购物商场 = {value} 个",
        "500m_hospitals_gte": f"500米内医院 ≥ {value} 家",
        "200m_hospitals_gte": f"200米内医院 ≥ {value} 家",
        "200m_residential_gte": f"200米内住宅小区 ≥ {value} 个",
        "200m_schools_gte": f"200米内学校 ≥ {value} 所",
        "200m_residential_gte": f"200米内住宅小区 ≥ {value} 个",
        "1000m_residential_gte": f"1000米内住宅小区 ≥ {value} 个",
        "1000m_residential_lt": f"1000米内住宅小区 < {value} 个",
        "1000m_hotels_gte": f"1000米内酒店 ≥ {value} 家",
        "1000m_schools_gte": f"1000米内学校 ≥ {value} 所",
        "1000m_scenic_eq": f"1000米内景区 = {value} 个",
        "500m_scenic_gte": f"500米内景区 ≥ {value} 个",
    }
    return maps.get(key, f"{key}: {value}")


def build_analysis_prompt(address: str, lng: float, lat: float,
                          business_type: str = "",
                          location_data: dict = None,
                          brand_name: str = "",
                          store_size: int = 0,
                          config: dict = None) -> str:
    """构建包含业态专属阈值和三层半径数据的分析提示词（config 由调用方通过 config_key 获取）"""
    def _int(v, default=0):
        try: return int(v)
        except: return default

    cfg = config or get_config(business_type)
    label = cfg.get("label", business_type or "通用商业")

    # 品牌描述和门店面积
    biz_desc_info = ""
    if brand_name:
        biz_desc_info = f"\n品牌/特色描述：{brand_name}"
    size_info = ""
    if store_size > 0:
        size_info = f"\n门店预估面积：{store_size} 平方米"
        # 店型判断
        if store_size <= 30:
            store_type = "档口/外卖店型——即买即走，不依赖堂食环境，关注出餐速度和门头曝光"
        elif store_size <= 80:
            store_type = "轻量堂食店型——需少量座位，出餐速度+基础环境，适合简餐/茶饮"
        elif store_size <= 200:
            store_type = "标准坐食店型——需舒适环境和停车配套，翻台率是核心指标"
        else:
            store_type = "大型餐饮——高租金+高人工+高翻台压力，停车和环境是硬门槛"
        size_info += f"\n店型判断：{store_type}"

    brand_info = biz_desc_info + size_info

    if not location_data:
        return f"""请分析以下地址是否适合开设「{label}」：
地址：{address}
坐标：经度 {lng}，纬度 {lat}
{brand_info}
请从人口密集度、交通与可达性、客流特征、消费人群属性、竞争环境、周边互补业态、品类优势、房租成本预估、营收测算、选址分析十个维度进行全面评估。"""

    ld = location_data

    brand_context = ""
    if brand_name:
        brand_context = f"""
## 🏷️ 品牌信息
品牌名称：{brand_name}
请结合「{brand_name}」的品牌定位，评估该品牌在此选址的竞争优劣势和具体打法。
"""

    # 场景识别
    pc = ld.get('poi_counts', {})
    office_count = pc.get('office', 0)
    residential_count = pc.get('residential', 0)
    shopping_count = pc.get('shopping', 0)
    school_count = pc.get('schools', 0)
    hotel_count = pc.get('hotels', 0)
    subway_500 = _int(ld.get('stats_500m', {}).get('subway', 0))
    bus_500 = _int(ld.get('stats_500m', {}).get('bus', 0))
    hospital_count = pc.get('hospitals', 0)

    if office_count >= 20 and shopping_count >= 5:
        scene_type = "商务商业复合区"
    elif office_count >= 15:
        scene_type = "商务办公区"
    elif school_count >= 8:
        scene_type = "大学城/学区"
    elif residential_count >= 50:
        scene_type = "高密度居住区"
    elif shopping_count >= 8:
        scene_type = "核心商圈"
    elif subway_500 > 0 or bus_500 >= 10:
        scene_type = "交通枢纽型社区"
    elif hotel_count >= 15:
        scene_type = "旅游商务区"
    elif hospital_count >= 5:
        scene_type = "医疗配套型社区"
    else:
        scene_type = "综合型社区"

    scene_strategies = {
        "商务商业复合区": "午市+晚市双高峰，拼翻台率和出餐效率，外卖出餐动线必须预留",
        "商务办公区": "午市是生命线（占全天60%+），13:00前出完最后一单，周末客流骤降需提前备料",
        "大学城/学区": "性价比为王，大众点评+小红书评价决定生死，寒暑假需准备淡季预案",
        "高密度居住区": "深耕复购率和社区关系，外卖覆盖3km半径，晚市+周末是主力时段",
        "核心商圈": "品牌曝光+高翻台，节假日爆发力强，但商场抽成需计入成本模型",
        "交通枢纽型社区": "出餐速度第一，潮汐客流明显，外带+快餐模型优先",
        "旅游商务区": "可适当提价但需做好线上评价引导，双客源更稳定但淡旺季波动大",
        "综合型社区": "稳健经营，控制租金占比在15%以内，靠产品力和复购率生存",
        "医疗配套型社区": "医院客群+家属陪护需求稳定，全时段营业可覆盖全天候需求，注重卫生和营养",
    }

    # 注入业态专属参数
    thresholds = cfg.get("thresholds", {})
    focus_radius = cfg.get("focus_radius", 500)
    core_strategy = cfg.get("core_strategy", "")
    traffic_override = cfg.get("traffic_weight_override", "")
    ignore_env = list(cfg.get("ignore_environmental_pois", []))  # copy for mutation
    competitor_blacklist = cfg.get("competitor_blacklist", [])

    # ================================================================
    # 第一步：动态豁免引擎 —— 根据品牌描述拦截"误杀"
    # ================================================================
    SCHOOL_EXEMPTIONS = ['汉堡','三明治','轻食','快餐','炸鸡','小吃','奶茶','文具','网吧','台球','学生','平价','早餐','盒饭','便当','轻餐','简餐']
    TRANSIT_EXEMPTIONS = ['快餐','便利店','早餐','青旅','平价','地铁口','公交','档口','外卖','汉堡','三明治','轻餐','轻食','简餐','小吃']
    exemption_note = ""

    if brand_name:
        brand_lower = brand_name.lower()
        # 学校豁免：品牌描述包含快餐/学生相关词 → 强制保留学校数据
        if any(kw in brand_name for kw in SCHOOL_EXEMPTIONS) and 'school' in ignore_env:
            ignore_env.remove('school')
            exemption_note += "注意：该品牌描述具有学生/快餐化属性，学校周边客流是重要评估维度。"
        # 公交/地铁豁免：品牌描述包含平价/快餐/外卖词 → 强制保留公交地铁数据
        if any(kw in brand_name for kw in TRANSIT_EXEMPTIONS):
            if 'bus' in ignore_env:
                ignore_env.remove('bus')
                exemption_note += "该品牌具有平价/便利属性，公交站客流不可忽略。"
            if 'subway' in ignore_env:
                ignore_env.remove('subway')
                exemption_note += "该品牌具有平价/便利属性，地铁客流不可忽略。"

    # === 防御性拷贝：防止环境降噪污染前端展示的 real_data ===
    ld = dict(ld)
    ld['stats_200m'] = dict(ld.get('stats_200m', {}))
    ld['stats_500m'] = dict(ld.get('stats_500m', {}))
    ld['stats_1000m'] = dict(ld.get('stats_1000m', {}))
    ld['poi_counts'] = dict(ld.get('poi_counts', {}))

    # === 环境降噪：将该业态不需要的POI类别全部清零 ===
    for env_key in ignore_env:
        mapped = ENV_POI_MAP.get(env_key)
        if mapped:
            for stats_dict in [ld.get('stats_200m', {}), ld.get('stats_500m', {}), ld.get('stats_1000m', {})]:
                stats_dict[mapped] = 0
            ld['poi_counts'][mapped] = 0

    # === 竞品黑名单过滤：剔除客单价/调性错位的竞品 ===
    if competitor_blacklist and ld.get('competitor_list'):
        filtered = [c for c in ld['competitor_list']
                    if not any(bk in c['name'] for bk in competitor_blacklist)]
        ld['competitor_list'] = filtered

    s_grade_lines = []
    for k, v in thresholds.get("s_grade", {}).items():
        desc = _threshold_desc(k, v)
        if desc:
            s_grade_lines.append(f"  ✅ {desc} → 必须判为优势，在报告中用积极语调陈述")
    red_flag_lines = []
    for k, v in thresholds.get("red_flag", {}).items():
        desc = _threshold_desc(k, v)
        if desc:
            red_flag_lines.append(f"  ⚠️ {desc} → 必须判为劣势，在报告中直接点出风险")

    parts = [f"""# 选址分析任务

分析目标：在以下位置开设「{label}」是否具备商业可行性。
{brand_info}{brand_context}
## 基本信息
- 地址：{address}
- 坐标：经度 {lng}，纬度 {lat}
- 城市：{ld.get('city', '')} {ld.get('district', '')} {ld.get('township', '')}
- 商圈：{', '.join(ld.get('business_areas', [])) or '无大型商圈'}
- 周边道路：{', '.join(ld.get('nearby_roads', []))}
- 选址场景：{scene_type} — {scene_strategies.get(scene_type, '')}
- 核心分析半径：{focus_radius}米
- 业态核心策略：{core_strategy}
- 交通权重规则：{traffic_override}
- 已剔除的无关联环境POI：{', '.join(ignore_env) if ignore_env else '无（全客群通吃）'}
- {exemption_note}

## 🎯 {label} 数据判定标准
{chr(10).join(s_grade_lines) if s_grade_lines else '（无特殊优势触发条件）'}
{chr(10).join(red_flag_lines) if red_flag_lines else '（无特殊劣势触发条件）'}

## 周边 POI 数据 — 200米 / 500米 / 1000米 三层半径

**以下表格是本次分析的唯一数值来源。报告中引用任何 POI 数量时，必须与此表格完全一致，不得凭周边业态描述反推数字。**

### 人口与密度
| 类别 | 200米 | 500米 | 1000米 |
|------|-------|-------|--------|
| 住宅小区 | {ld.get('stats_200m', {}).get('residential', 0)} | {ld.get('stats_500m', {}).get('residential', 0)} | {ld.get('stats_1000m', {}).get('residential', 0)} |
| 写字楼 | {ld.get('stats_200m', {}).get('office', 0)} | {ld.get('stats_500m', {}).get('office', 0)} | {ld.get('stats_1000m', {}).get('office', 0)} |
| 学校 | {ld.get('stats_200m', {}).get('schools', 0)} | {ld.get('stats_500m', {}).get('schools', 0)} | {ld.get('stats_1000m', {}).get('schools', 0)} |
| 医院 | {ld.get('stats_200m', {}).get('hospitals', 0)} | {ld.get('stats_500m', {}).get('hospitals', 0)} | {ld.get('stats_1000m', {}).get('hospitals', 0)} |

### 交通与可达性
| 类别 | 200米 | 500米 | 1000米 |
|------|-------|-------|--------|
| 地铁站 | {ld.get('stats_200m', {}).get('subway', 0)} | {ld.get('stats_500m', {}).get('subway', 0)} | {ld.get('stats_1000m', {}).get('subway', 0)} |
| 公交站 | {ld.get('stats_200m', {}).get('bus', 0)} | {ld.get('stats_500m', {}).get('bus', 0)} | {ld.get('stats_1000m', {}).get('bus', 0)} |
| 停车场 | {ld.get('stats_200m', {}).get('parking', 0)} | {ld.get('stats_500m', {}).get('parking', 0)} | {ld.get('stats_1000m', {}).get('parking', 0)} |

### 商业配套
| 类别 | 200米 | 500米 | 1000米 |
|------|-------|-------|--------|
| 购物商场 | {ld.get('stats_200m', {}).get('shopping', 0)} | {ld.get('stats_500m', {}).get('shopping', 0)} | {ld.get('stats_1000m', {}).get('shopping', 0)} |
| 便利店/超市 | {ld.get('stats_200m', {}).get('convenience', 0)} | {ld.get('stats_500m', {}).get('convenience', 0)} | {ld.get('stats_1000m', {}).get('convenience', 0)} |
| 酒店住宿 | {ld.get('stats_200m', {}).get('hotels', 0)} | {ld.get('stats_500m', {}).get('hotels', 0)} | {ld.get('stats_1000m', {}).get('hotels', 0)} |

### 餐饮竞争格局
| 类别 | 200米 | 500米 | 1000米 |
|------|-------|-------|--------|
| 所有餐饮 | {ld.get('stats_200m', {}).get('restaurants', 0)} | {ld.get('stats_500m', {}).get('restaurants', 0)} | {ld.get('stats_1000m', {}).get('restaurants', 0)} |
| 中餐厅 | {ld.get('stats_200m', {}).get('chinese_restaurants', 0)} | {ld.get('stats_500m', {}).get('chinese_restaurants', 0)} | {ld.get('stats_1000m', {}).get('chinese_restaurants', 0)} |
| 快餐厅 | {ld.get('stats_200m', {}).get('fast_food', 0)} | {ld.get('stats_500m', {}).get('fast_food', 0)} | {ld.get('stats_1000m', {}).get('fast_food', 0)} |
| 咖啡茶饮 | {ld.get('stats_200m', {}).get('cafe_tea', 0)} | {ld.get('stats_500m', {}).get('cafe_tea', 0)} | {ld.get('stats_1000m', {}).get('cafe_tea', 0)} |"""]

    # ★ 严谨度开关：仅认 rigor_enabled，不认字段存在
    has_rigor = ld.get('rigor_enabled') is True

    if has_rigor:
        # ── 严谨框架：按半径拆分竞品清单，避免模型将1000m清单当200m引用 ──
        dc_list_200m = ld.get('direct_competitor_list_200m', [])
        dc_list_500m = ld.get('direct_competitor_list_500m', [])
        dc_list_1000m = ld.get('direct_competitor_list_1000m', [])
        # fallback: 如果新字段不存在（旧版数据），回退 unified list
        if not dc_list_200m and not dc_list_500m and not dc_list_1000m:
            dc_all = ld.get('direct_competitor_list', [])
            dc_list_200m = [c for c in dc_all if c.get('distance', 999) <= 200]
            dc_list_500m = [c for c in dc_all if c.get('distance', 999) <= 500]
            dc_list_1000m = dc_all[:15]

        dc_200_text = '\n'.join([f"  - {c['name']}（{c['distance']}米）" for c in dc_list_200m[:5]]) or "（无）"
        dc_500_text = '\n'.join([f"  - {c['name']}（{c['distance']}米）" for c in dc_list_500m[:10]]) or "（无）"
        dc_1000_text = '\n'.join([f"  - {c['name']}（{c['distance']}米）" for c in dc_list_1000m[:15]]) or "（无）"
        parts.append(f"""
### 🎯 直接竞品（同类业态 · 严谨口径 · 按半径分层）

**200米贴身圈：{ld.get('direct_competitors_200m', 0)} 家**
{dc_200_text}

**500米核心圈：{ld.get('direct_competitors_500m', 0)} 家**
{dc_500_text}

**1000米辐射圈：{ld.get('direct_competitors_1000m', 0)} 家**
{dc_1000_text}

**⚠️ 铁律：报告中引用竞品时必须注明半径。例如"200米内无直接竞品""500米内仅2家同类小吃店""1000米辐射圈有8家快餐竞品"。绝对禁止将1000米清单当作200米贴身圈竞品来写。竞争维度的评分必须仅基于以上直接竞品数据。**""")

        if ld.get('substitute_competitors_1000m') is not None:
            sub_text_200 = f"200m: {ld.get('substitute_competitors_200m', 0)} 家"
            sub_text_500 = f"500m: {ld.get('substitute_competitors_500m', 0)} 家"
            sub_text_1000 = f"1000m: {ld.get('substitute_competitors_1000m', 0)} 家"
            sub_list_1000 = ld.get('substitute_list_1000m', ld.get('substitute_list', []))
            sub_names = '\n'.join([f"  - {c['name']}（{c['distance']}米）" for c in sub_list_1000[:10]]) if sub_list_1000 else "\n（本轮未识别到明确替代消费压力）"
            parts.append(f"""
### 🔶 替代消费压力（非同业态 · 不计入直接竞品）
{sub_text_200} | {sub_text_500} | {sub_text_1000}
{sub_names}
**替代压力不影响直接竞品数量，仅在优势/劣势中定性提及。**""")

        if ld.get('traffic_anchors_1000m') is not None:
            anc_text_200 = f"200m: {ld.get('traffic_anchors_200m', 0)} 个"
            anc_text_500 = f"500m: {ld.get('traffic_anchors_500m', 0)} 个"
            anc_text_1000 = f"1000m: {ld.get('traffic_anchors_1000m', 0)} 个"
            anc_list_1000 = ld.get('traffic_anchor_list_1000m', ld.get('traffic_anchor_list', []))
            anc_names = '\n'.join([f"  - {c['name']}（{c['distance']}米）" for c in anc_list_1000[:10]]) if anc_list_1000 else "\n（本轮未识别到明确客流锚点）"
            parts.append(f"""
### 🟢 客流锚点（商业活跃度参考 · 非竞品）
{anc_text_200} | {anc_text_500} | {anc_text_1000}
{anc_names}
**客流锚点品牌/业态只表示商业活跃度，绝对不得写成竞争品牌或计入竞争评分。**""")

    else:
        # ── 旧口径：该业态暂无严谨分类规则 ──
        parts.append("""**⚠️ 该业态暂无完整严谨分类规则，以下竞品结果仅供兼容参考，不得作为正式评分依据。建议联系管理员补充业态规则。**""")
        parts.append(f"""### 同品类竞品（旧口径·仅兼容）
- 周边 200米 共 **{ld.get('competitors_200m', 0)}** 家
- 周边 500米 共 **{ld.get('competitors_500m', 0)}** 家
- 周边 1000米 共 **{ld.get('competitors_1000m', 0)}** 家
**⚠️ 以上为旧口径竞品数量，不得作为竞争维度评分依据。建议重新分析以启用严谨口径。**""")

        if ld.get('competitor_list'):
            comp_list = '\n'.join([f"  - {c['name']}（{c['distance']}米）"
                                   for c in ld['competitor_list'][:15]])
            parts.append(f"""
### 竞品清单（旧口径·仅兼容）
{comp_list}
**以上为旧口径列表，仅供参考，不得直接用于竞争评分。建议重新分析。**""")

    if ld.get('hot_brands'):
        brand_list = '\n'.join([f"  - {b['name']}：{b['count']} 家，最近 {b.get('min_distance', '?')}米"
                                for b in ld['hot_brands'][:15]])
        parts.append(f"""
### 周边连锁品牌（注意：含客流锚点品牌，不是所有品牌都是竞品）
{brand_list}
""")

    # ================================================================
    # 强制互斥预判：每个维度一个 if/elif/else，绝不允许同一数据源跨两个列表
    # 所有数值强制 int() 转换，防止 JSON 序列化导致 "15" > 15 比较失效
    s200 = ld.get('stats_200m', {})
    s500 = ld.get('stats_500m', {})
    s1000 = ld.get('stats_1000m', {})
    sg = thresholds.get("s_grade", {})
    rf = thresholds.get("red_flag", {})

    pre_advantages = []
    pre_disadvantages = []

    # === 维度1：竞品密度 (if/elif/else) —— ≤上限→优势，>下限→劣势，中间段→中性 ===
    # ★ 严谨框架下只用 direct_competitors；否则回退旧口径
    comp_200 = _int(ld.get('direct_competitors_200m', 0) if has_rigor else ld.get('competitors_200m', 0))
    sub_200 = _int(ld.get('substitute_competitors_200m', 0))
    sub_500 = _int(ld.get('substitute_competitors_500m', 0))
    s_comp = sg.get("200m_competitors_lte")
    rf_comp = rf.get("200m_competitors_gt")
    if s_comp is not None and comp_200 <= _int(s_comp):
        if sub_200 > 0 or sub_500 > 0:
            # ★ 有替代消费 → 保守措辞，半径分列不求和，不得出现"空白""红利""截流阻力小"
            pre_advantages.append(
                f"贴身200米内{comp_200}家同品类直接竞品，直接竞品较少；"
                f"替代消费200米内{sub_200}家、500米内{sub_500}家，需现场核验分流影响"
            )
        elif comp_200 <= 1:
            pre_advantages.append(f"贴身200米内仅{comp_200}家同品类直接竞品，直接竞争极低")
        else:
            pre_advantages.append(f"贴身200米内仅{comp_200}家同品类直接竞品，直接竞品较少")
    elif rf_comp is not None and comp_200 > _int(rf_comp):
        pre_disadvantages.append(f"贴身200米内聚集了{comp_200}家同品类直接竞品，分流风险极大——贴身肉搏级别的红海")
    # 中性段：不写入任何列表

    # === 维度2：地铁 (if/elif/else) — 需 subway_applicable 判断 ===
    subway_500 = _int(ld.get('stats_500m', {}).get('subway', 0))
    subway_applicable = ld.get('subway_applicable', True)
    s_sub = sg.get("500m_subway_gte")
    rf_sub = rf.get("500m_subway_eq")
    if subway_applicable and s_sub is not None and subway_500 >= _int(s_sub):
        pre_advantages.append(f"500米内覆盖{subway_500}个地铁站，公共交通导入能力强，年轻及商务客群可达性高")
    elif subway_applicable and rf_sub is not None and subway_500 == _int(rf_sub):
        pre_disadvantages.append(f"500米步行圈内无任何地铁站覆盖，客群导入高度依赖步行和自驾——公共交通是明显短板")
    elif not subway_applicable:
        # 无地铁城市不把"无地铁"当短板
        pass
    # else: 中性

    # === 维度3：公交 (if/elif/else) ===
    bus_500 = _int(ld.get('stats_500m', {}).get('bus', 0))
    s_bus = sg.get("500m_bus_gte")
    rf_bus = rf.get("500m_bus_lt")
    if s_bus is not None and bus_500 >= _int(s_bus):
        if subway_applicable:
            pre_advantages.append(f"500米内公交线路达{bus_500}条，地面公交网络密集，补充了地铁覆盖")
        else:
            pre_advantages.append(f"500米内公交线路达{bus_500}条，地面公交网络较密，可支撑基础可达性")
    elif rf_bus is not None and bus_500 < _int(rf_bus):
        # ★ 无地铁城市：公交少时只归因公交，不提地铁缺失
        if not subway_applicable:
            pre_disadvantages.append(f"500米内公交线路仅{bus_500}条，地面公交覆盖不足——交通条件对{label}不利")
        elif subway_500 == 0:
            pre_disadvantages.append(f"500米内地铁和公交全面缺失，顾客只能步行或自驾到店——交通条件对{label}极为不利")
    # else: 中性

    # === 维度4：学校 (if/elif/else) ===
    school_500 = _int(ld.get('stats_500m', {}).get('schools', 0))
    s_sch = sg.get("500m_schools_gte") or sg.get("200m_schools_gte")
    if s_sch is not None and school_500 >= _int(s_sch):
        pre_advantages.append(f"周边500米内分布{school_500}所学校，学生客流基数庞大，午间及放学时段需求旺盛")
    # 学校无劣势阈值（学校少不构成劣势，只是没有优势）
    # else: 中性

    # === 维度5：写字楼 (if/elif/else) —— 绝对不拆成两个 if ===
    office_500 = _int(ld.get('stats_500m', {}).get('office', 0))
    s_off = sg.get("500m_office_gte")
    rf_off = rf.get("500m_office_lt")
    if s_off is not None and office_500 >= _int(s_off):
        pre_advantages.append(f"500米内{office_500}栋写字楼，白领午市刚需客群充沛，工作日客流有保障")
    elif rf_off is not None and office_500 < _int(rf_off):
        pre_disadvantages.append(f"周边写字楼仅{office_500}栋，白领客群基数偏小，午市及工作日客流支撑不足")
    # else: 中性

    # === 维度6：住宅密度 (if/elif/else) ===
    residential_500 = _int(ld.get('stats_500m', {}).get('residential', 0))
    s_res = sg.get("500m_residential_gte")
    rf_res = rf.get("500m_residential_lt")
    if s_res is not None and residential_500 >= _int(s_res):
        pre_advantages.append(f"500米内覆盖{residential_500}个住宅小区，常住人口密度高，社区消费基本盘扎实")
    elif rf_res is not None and residential_500 < _int(rf_res):
        pre_disadvantages.append(f"500米内仅{residential_500}个住宅小区，常住人口基数不足，社区消费基本盘薄弱")
    # else: 中性

    # === 维度7：停车场 (if/elif/else) ===
    parking_500 = _int(ld.get('stats_500m', {}).get('parking', 0))
    s_park = sg.get("500m_parking_gte")
    rf_park = rf.get("500m_parking_eq")
    if s_park is not None and parking_500 >= _int(s_park):
        pre_advantages.append(f"500米内有{parking_500}个停车场，自驾客群停车便利，对目的性消费业态极友好")
    elif rf_park is not None and parking_500 == _int(rf_park):
        pre_disadvantages.append(f"500米内无停车场覆盖，自驾客群完全无法触达——对{label}业态构成硬伤")
    # else: 中性

    # === 维度8：医院 (if/elif) ===
    hospital_200 = _int(s200.get('hospitals', 0))
    s_hosp = sg.get("200m_hospitals_gte")
    if s_hosp is not None and hospital_200 >= _int(s_hosp):
        pre_advantages.append(f"200米内紧邻医院，可承接就诊人群及陪护家属的即时消费需求")
    # 医院无劣势阈值
    # else: 中性

    # === 维度9：购物商场 (if/elif/else) ===
    shopping_500 = _int(ld.get('stats_500m', {}).get('shopping', 0))
    s_shop = sg.get("500m_shopping_gte")
    rf_shop = rf.get("500m_shopping_eq")
    if s_shop is not None and shopping_500 >= _int(s_shop):
        pre_advantages.append(f"500米内{shopping_500}个购物商场，商业体自然流量充沛，可共享逛街人群")
    elif rf_shop is not None and shopping_500 == _int(rf_shop):
        pre_disadvantages.append(f"周边无任何购物商场，缺乏商业体的流量导入——选址孤岛风险高")
    # else: 中性

    # === 维度10：酒店 (if/elif) ===
    hotel_1000 = _int(s1000.get('hotels', 0))
    s_hotel = sg.get("1000m_hotels_gte")
    if s_hotel is not None and hotel_1000 >= _int(s_hotel):
        pre_advantages.append(f"1公里商圈内{hotel_1000}家酒店，异地商旅客流充沛，为门店带来源源不断的新客")
    # 酒店无劣势阈值
    # else: 中性

    # === 维度11：居民区噪音冲突 (if) ===
    residential_200 = _int(s200.get('residential', 0))
    rf_res_noise = rf.get("200m_residential_gte")
    if rf_res_noise is not None and residential_200 >= _int(rf_res_noise):
        pre_disadvantages.append(f"200米内紧邻{residential_200}个住宅小区，噪音投诉风险高——对夜经济业态构成硬伤")

    # 注入互斥事实清单到 Prompt
    pre_judged = ""
    if pre_advantages:
        pre_judged += "\n## ✅ 系统预判——以下事实已确认属于「优势」，绝对不可在劣势列表中提及：\n"
        for i, fact in enumerate(pre_advantages, 1):
            pre_judged += f"  {i}. {fact}\n"
    if pre_disadvantages:
        pre_judged += "\n## ⚠️ 系统预判——以下事实已确认属于「劣势」，绝对不可在优势列表中提及：\n"
        for i, fact in enumerate(pre_disadvantages, 1):
            pre_judged += f"  {i}. {fact}\n"
    if pre_judged:
        pre_judged += "\n上述预判事实已完成物理隔离，" \
                      "每条事实只能出现在对应的列表中，绝不可跨列表引用。\n" \
                      "⚠️ 系统预判只提供类别和数量信息，不提供具体 POI 名称。" \
                      "禁止基于预判内容自行补写具体学校名、小区名、医院名、商场名、酒店名等实体名称。\n"
    if not subway_applicable:
        pre_judged += "\n🚇 该城市暂无地铁系统，地铁不纳入本次交通评分。交通评分请重点依据公交线路、道路可达性、停车设施等地面交通因素。\n"

    parts.append(pre_judged)
    parts.append(f"""
## 分析维度

### 1. 人口密集度
根据三层半径的住宅+写字楼+学校+医院数据，推算周边人口量级。

### 2. 交通与可达性
**严格按交通判定标准得出结论**。引用地铁/公交/停车数据。

### 3. 客流特征
推算日均有效客流量区间（禁止单点数字），标注置信度，区分路过vs目的客流，工作日vs周末，早中晚时段分布。

### 4. 消费人群属性
住宅vs办公vs学校比例，消费水平推断，与「{label}」目标客群匹配度。

### 5. 竞争环境
★ 仅基于「直接竞品」数据（direct_competitors）做竞争判断。替代消费压力（substitute）和客流锚点（traffic_anchors）不是竞品，只能在优势/劣势中定性提及，绝不可计入竞品数量或竞争评分。引用直接竞品品牌名，标注🔴🟡🟢威胁等级。评分<50时warning中必须提及竞争风险。

### 6. 周边互补业态
配套协同效应和消费生态链完整度。

### 7. 品类优势与差异化
「{label}」在{scene_type}场景下的供需匹配度和具体切入机会。

### 8. 房租成本预估
按该地段商圈能级估算月租金区间（元/㎡/月），若有门店面积({store_size}㎡)则输出月租金范围。标注"模型假设"。

### 9. 营收测算模型
★ 必须输出保守/中性/乐观三档区间，每档标注假设条件及置信度：
- 日均单量区间（基于商圈客流量和竞品密度推算，置信度低/中/高）
- 客单价区间（基于{label}业态和品牌定位估算）
- 毛利率区间（标注假设或行业参考值）
- 月固定成本区间：房租 + 人工 + 食材 + 水电杂费
- 盈亏平衡单量区间
- ★ 严格禁止单点精确数字（如"183单""23.6万"），所有数字必须是区间
- 标注"模型估算，需线下实测验证，不代表承诺"

### 10. 选址分析与运营策略
以冷练客观的商管顾问口吻，结合「{label}」的客单价和「{store_size}㎡」门店面积，输出至少3条可落地的经营动作。禁止使用"根据您提供的"等引导词，直接输出结论。""")

    return '\n'.join(parts)
