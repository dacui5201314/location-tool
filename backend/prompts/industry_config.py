"""
千店千面 · 全业态选址配置 (Industry Config Master v4)
14个业态集群 × 5维参数 × 客群折叠/环境降噪/竞品黑名单
"""
# ============================================================
# 14个业态集群
# ============================================================
MASTER_TEMPLATES = {

    # ================= 1. 异国/中高端正餐 =================
    "异国_中高端正餐": {
        "label": "西餐/日料/高端正餐",
        "focus_radius": 1000,
        "competitor_amap_types": "050200",
        "radar_weights": {"population_density":10,"traffic_accessibility":20,"competition":15,"complementary_businesses":35,"cost_estimate":20},
        "target_keywords": ["西餐","牛排","披萨","日料","寿司","刺身","法餐","意餐","私房","公馆","海鲜","料理"],
        "competitor_blacklist": ["快餐","小吃","面馆","黄焖鸡","沙县","米线","麻辣烫","汉堡","炸鸡","食堂","盒饭","盖浇饭","兰州拉面","螺蛳粉"],
        "ignore_environmental_pois": ["hospital","school","bus"],
        "traffic_weight_override": "该业态为目的性消费。完全忽略公交站缺失，将停车场数量视为交通唯一判定标准。无停车场=硬伤。",
        "core_strategy": "主打中高客单价的约会与商务社交。极其依赖商场、A级写字楼和高端社区。周边如有大量廉价快餐不视作竞争，但可能意味着商圈消费力不足。环境投入≥总投入25%。绝不套用中餐翻台率逻辑。",
        "price_range": (80, 200),
        "thresholds": {
            "s_grade": {"500m_subway_gte":1,"500m_shopping_gte":3,"500m_parking_gte":5,"200m_competitors_lte":2},
            "red_flag": {"200m_competitors_gt":5,"500m_parking_eq":0,"500m_shopping_eq":0},
        },
    },

    # ================= 2. 火锅/烧烤 =================
    "火锅_烧烤": {
        "label": "火锅/烧烤",
        "focus_radius": 1000,
        "competitor_amap_types": "050100",
        "radar_weights": {"population_density":15,"traffic_accessibility":15,"competition":25,"complementary_businesses":15,"cost_estimate":30},
        "target_keywords": ["火锅","烧烤","烤串","烤肉","涮肉","羊蝎子","烤鱼","小龙虾","大排档"],
        "competitor_blacklist": ["快餐","小吃","面馆","包子","食堂","盒饭"],
        "ignore_environmental_pois": [],
        "traffic_weight_override": "晚市+夜宵业态。停车场是核心加分项，公共交通次之。无停车场判为严重短板。",
        "core_strategy": "主攻晚市和宵夜，翻台率1.2-1.5。极度依赖停车便利度和周边KTV/酒吧/台球厅的连带消费。注意排烟和噪音控制防投诉。绝不使用午市快餐逻辑。",
        "price_range": (50, 120),
        "thresholds": {
            "s_grade": {"500m_parking_gte":10,"200m_competitors_lte":3,"1000m_hotels_gte":10},
            "red_flag": {"200m_competitors_gt":10,"500m_parking_eq":0,"200m_residential_gte":10},
        },
    },

    # ================= 3. 刚需快餐小吃 =================
    "刚需快餐小吃": {
        "label": "快餐/小吃/面馆",
        "focus_radius": 200,
        "competitor_amap_types": "050000",
        "radar_weights": {"population_density":30,"traffic_accessibility":20,"competition":30,"complementary_businesses":10,"cost_estimate":10},
        "target_keywords": ["面","皮","粉","饭","包","粥","小吃","麻辣烫","炸鸡","米线","凉皮","肉夹馍","饺子","馄饨","煎饼","便当","盖浇","砂锅","冒菜","串串","卤味","鸭脖","鸡排","汉堡","披萨","拉面","拌面","酸辣粉","螺蛳粉","热干面","泡馍","擀面皮","锅贴","生煎","小笼","麻辣拌"],
        "competitor_blacklist": ["大酒楼","海鲜","高档西餐","星级酒店","私房菜","公馆","怀石","omakase"],
        "ignore_environmental_pois": [],
        "traffic_weight_override": "高度依赖密集便捷的公共交通。公交站和地铁站是核心加分项，停车场数量不重要。",
        "core_strategy": "主攻午市刚需和高频低客单价。出餐速度90秒内。对周边学校、医院、老旧密集小区的依赖度极高。必须用盈亏平衡点和翻台率评估生死线。外卖占比40%+。",
        "price_range": (8, 25),
        "thresholds": {
            "s_grade": {"200m_competitors_lte":3,"500m_subway_gte":1,"500m_schools_gte":3,"500m_office_gte":10},
            "red_flag": {"200m_competitors_gt":15,"500m_subway_eq":0,"500m_bus_lt":3},
        },
    },

    # ================= 4. 中餐正餐 =================
    "中餐正餐": {
        "label": "中餐/正餐/酒楼",
        "focus_radius": 1000,
        "competitor_amap_types": "050100",
        "radar_weights": {"population_density":20,"traffic_accessibility":15,"competition":25,"complementary_businesses":10,"cost_estimate":30},
        "target_keywords": ["酒楼","宴","中餐","湘菜","川菜","粤菜","西北菜","东北菜","本帮菜","私房","烤鸭"],
        "competitor_blacklist": ["快餐","小吃","面馆","麻辣烫","汉堡","食堂"],
        "ignore_environmental_pois": [],
        "traffic_weight_override": "停车场是核心，公共交通辅助。无停车场=重大缺陷。",
        "core_strategy": "主攻晚市及周末目的性聚餐。包厢需求≥2间。翻台率1.5-2.0。停车便利度决定生死。",
        "price_range": (45, 120),
        "thresholds": {
            "s_grade": {"200m_competitors_lte":5,"500m_subway_gte":1,"500m_parking_gte":5,"500m_office_gte":10},
            "red_flag": {"200m_competitors_gt":10,"500m_parking_eq":0},
        },
    },

    # ================= 5. 烘焙甜品 =================
    "烘焙甜品": {
        "label": "烘焙/甜品",
        "focus_radius": 500,
        "competitor_amap_types": "050600",
        "radar_weights": {"population_density":40,"traffic_accessibility":20,"competition":20,"complementary_businesses":20,"cost_estimate":0},
        "target_keywords": ["烘焙","面包","蛋糕","甜点","泡芙","蛋挞","慕斯","马卡龙","曲奇","冰淇淋"],
        "competitor_blacklist": ["包子","馒头","大饼","油条","食堂"],
        "ignore_environmental_pois": [],
        "traffic_weight_override": "重度依赖步行可达性和社区主入口曝光，地铁口和学校门口是S级选址。",
        "core_strategy": "强依赖女性客群、学生及社区家庭。适合小区主出入口或商场一楼动线。橱窗展示面≥3米。每周推季节限定。",
        "price_range": (12, 40),
        "thresholds": {
            "s_grade": {"200m_competitors_lte":2,"500m_residential_gte":20,"500m_schools_gte":2},
            "red_flag": {"200m_competitors_gt":6,"500m_residential_lt":10},
        },
    },

    # ================= 6. 精品茶饮咖啡 =================
    "精品茶饮咖啡": {
        "label": "茶饮/咖啡/饮品",
        "focus_radius": 200,
        "competitor_amap_types": "050500",
        "radar_weights": {"population_density":20,"traffic_accessibility":30,"competition":30,"complementary_businesses":20,"cost_estimate":0},
        "target_keywords": ["奶茶","咖啡","茶","果饮","柠檬","酸奶","星巴克","瑞幸","喜茶","奈雪","蜜雪冰城","茶百道","古茗","霸王茶姬","Manner"],
        "competitor_blacklist": ["包子铺","馒头店","大饼","油条","食堂"],
        "ignore_environmental_pois": ["hospital"],
        "traffic_weight_override": "极度依赖地铁口或写字楼底层的步行可达性。公交站次要。停车场完全忽略。",
        "core_strategy": "冲动型消费，极度依赖核心动线曝光和年轻客流。商场首层/地铁口/学校门口=S级。外卖占比50%+。会员储值锁复购。",
        "price_range": (8, 25),
        "thresholds": {
            "s_grade": {"200m_competitors_lte":2,"500m_subway_gte":1,"500m_schools_gte":2,"200m_schools_gte":1},
            "red_flag": {"200m_competitors_gt":8,"500m_subway_eq":0},
        },
    },

    # ================= 7. 商务酒店 =================
    "商务酒店": {
        "label": "商务酒店/宾馆",
        "focus_radius": 1500,
        "competitor_amap_types": "100000",
        "radar_weights": {"population_density":0,"traffic_accessibility":50,"competition":20,"complementary_businesses":20,"cost_estimate":10},
        "target_keywords": ["酒店","宾馆","汉庭","如家","全季","亚朵","希尔顿","万豪"],
        "competitor_blacklist": ["招待所","农家乐","洗浴","日租房","钟点房"],
        "ignore_environmental_pois": ["school"],
        "traffic_weight_override": "交通枢纽（火车站/机场/地铁核心站）是绝对核心。停车场次之。公交站不重要。",
        "core_strategy": "绝对目的性消费，依赖交通枢纽/商务区/会展中心。地铁站<500米=S级。美团+携程+飞猪三平台。免费接站换好评。",
        "price_range": (150, 500),
        "thresholds": {
            "s_grade": {"500m_subway_gte":1,"500m_office_gte":10,"1000m_hotels_gte":20},
            "red_flag": {"200m_competitors_gt":10,"500m_subway_eq":0},
        },
    },

    # ================= 8. 民宿青旅 =================
    "民宿青旅": {
        "label": "民宿/青年旅舍",
        "focus_radius": 1500,
        "competitor_amap_types": "100000",
        "radar_weights": {"population_density":0,"traffic_accessibility":40,"competition":25,"complementary_businesses":25,"cost_estimate":10},
        "target_keywords": ["民宿","旅舍","客栈","青旅","背包客"],
        "competitor_blacklist": ["星级酒店","希尔顿","万豪","洲际","商务酒店"],
        "ignore_environmental_pois": ["school"],
        "traffic_weight_override": "极度依赖地铁/火车站和知名景区。停车场不重要。",
        "core_strategy": "极致性价比+社交属性。小红书+抖音获客。公共空间是灵魂——必须设置社交区/共享厨房。不套用商务酒店OTA逻辑。",
        "price_range": (60, 300),
        "thresholds": {
            "s_grade": {"500m_subway_gte":1,"1000m_hotels_gte":10,"200m_competitors_lte":5},
            "red_flag": {"500m_subway_eq":0,"200m_competitors_gt":10},
        },
    },

    # ================= 9. 高频刚需零售 =================
    "高频刚需零售": {
        "label": "便利店/超市/药店",
        "focus_radius": 300,
        "competitor_amap_types": "060200|060300|090400",
        "radar_weights": {"population_density":50,"traffic_accessibility":10,"competition":30,"complementary_businesses":10,"cost_estimate":0},
        "target_keywords": ["便利店","超市","药","生鲜","711","罗森","全家","便利蜂","永辉","盒马"],
        "competitor_blacklist": ["批发","建材","五金"],
        "ignore_environmental_pois": [],
        "traffic_weight_override": "完全依赖社区内部人口，公共交通/停车场均不重要。",
        "core_strategy": "吃透社区最后一公里。200米内住宅≥5个是硬门槛。鲜食占比30%+。药店需医保定点资质。",
        "price_range": (3, 300),
        "thresholds": {
            "s_grade": {"200m_residential_gte":5,"200m_competitors_lte":1,"200m_hospitals_gte":1},
            "red_flag": {"200m_competitors_gt":3,"500m_residential_lt":5},
        },
    },

    # ================= 10. 低频目的零售 =================
    "低频目的零售": {
        "label": "服装/数码/专卖",
        "focus_radius": 1000,
        "competitor_amap_types": "060100|060400",
        "radar_weights": {"population_density":10,"traffic_accessibility":30,"competition":10,"complementary_businesses":50,"cost_estimate":0},
        "target_keywords": ["服装","数码","专卖","手机","电脑","家电","眼镜","珠宝"],
        "competitor_blacklist": ["批发","建材","五金","农贸"],
        "ignore_environmental_pois": ["hospital","school"],
        "traffic_weight_override": "依赖商业综合体/步行街流量池。孤立社区底商=极高风险。",
        "core_strategy": "同行扎堆形成逛街效应。商圈内同类≥5家才考虑进驻。小红书+抖音同城获客。私域复购。",
        "price_range": (50, 2000),
        "thresholds": {
            "s_grade": {"500m_shopping_gte":3,"200m_competitors_lte":2},
            "red_flag": {"500m_shopping_eq":0},
        },
    },

    # ================= 11. 专业生活服务 =================
    "专业生活服务": {
        "label": "美容/宠物/健身",
        "focus_radius": 800,
        "competitor_amap_types": "070000|080000",
        "radar_weights": {"population_density":60,"traffic_accessibility":10,"competition":20,"complementary_businesses":0,"cost_estimate":10},
        "target_keywords": ["美容","美发","宠物","健身","瑜伽","舞蹈"],
        "competitor_blacklist": ["快剪","街边理发","10元店","平价"],
        "ignore_environmental_pois": ["hospital","school","bus","subway"],
        "traffic_weight_override": "完全依赖社区内循环或自驾（停车场）。无需流动人口。公交/地铁完全忽略。",
        "core_strategy": "做3公里内的会员储值生意。极致依赖周边中高档住宅小区入住率和消费力。周边全是老旧小区或城中村=强制红海风险。",
        "price_range": (50, 500),
        "thresholds": {
            "s_grade": {"500m_residential_gte":30,"200m_competitors_lte":1},
            "red_flag": {"200m_competitors_gt":5,"500m_residential_lt":15},
        },
    },

    # ================= 12. 社区基础服务 =================
    "社区基础服务": {
        "label": "教育/洗衣/诊所",
        "focus_radius": 800,
        "competitor_amap_types": "141200|070000",
        "radar_weights": {"population_density":55,"traffic_accessibility":15,"competition":20,"complementary_businesses":0,"cost_estimate":10},
        "target_keywords": ["培训","教育","洗衣","诊所","琴行","画室","早教","托管"],
        "competitor_blacklist": ["驾校","职业培训"],
        "ignore_environmental_pois": [],
        "traffic_weight_override": "依赖周边小区家庭客群。公共交通辅助。",
        "core_strategy": "做社区刚需服务。教育培训需关注放学动线。洗衣店需上门取送。诊所需执业许可证。口碑和转介绍为核心获客方式。",
        "price_range": (30, 800),
        "thresholds": {
            "s_grade": {"500m_residential_gte":30,"200m_competitors_eq":0,"500m_schools_gte":2},
            "red_flag": {"200m_competitors_gt":3,"500m_residential_lt":10},
        },
    },

    # ================= 13. 夜经济娱乐 =================
    "夜经济娱乐": {
        "label": "酒吧/KTV/网吧",
        "focus_radius": 1000,
        "competitor_amap_types": "050400|080000",
        "radar_weights": {"population_density":10,"traffic_accessibility":10,"competition":20,"complementary_businesses":30,"cost_estimate":30},
        "target_keywords": ["酒吧","KTV","网咖","LiveHouse","清吧","精酿","威士忌","电竞"],
        "competitor_blacklist": ["网咖","台球","棋牌"],
        "ignore_environmental_pois": ["hospital"],
        "traffic_weight_override": "重度依赖停车场和地铁深夜可达性。公交站不重要。",
        "core_strategy": "组局目的性极强，重资产投入。隔音投入≥装修15%。【绝对红线】：周边高密度紧贴老旧住宅且<100米→极易扰民投诉，环保/消防办证风险极大，必须触发劣势预警。",
        "price_range": (48, 200),
        "thresholds": {
            "s_grade": {"500m_schools_gte":2,"500m_subway_gte":1,"200m_competitors_lte":1,"1000m_hotels_gte":10},
            "red_flag": {"200m_competitors_gt":3,"500m_subway_eq":0,"200m_residential_gte":10},
        },
    },

    # ================= 14. 沉浸式社交娱乐 =================
    "沉浸式社交娱乐": {
        "label": "剧本杀/密室/台球",
        "focus_radius": 1000,
        "competitor_amap_types": "080000",
        "radar_weights": {"population_density":10,"traffic_accessibility":20,"competition":20,"complementary_businesses":30,"cost_estimate":20},
        "target_keywords": ["剧本杀","密室","台球","桌游","轰趴","VR","电玩"],
        "competitor_blacklist": ["棋牌","麻将馆"],
        "ignore_environmental_pois": ["hospital"],
        "traffic_weight_override": "地铁站是年轻客群生命线。停车场次要。公交站不重要。",
        "core_strategy": "强社交组局，停留2-4小时。大学城/地铁站1km=S级。储备8-12个剧本每月更新。周末四场排满。年轻人多坐地铁来，不依赖停车。",
        "price_range": (39, 200),
        "thresholds": {
            "s_grade": {"500m_subway_gte":1,"500m_schools_gte":2,"1000m_schools_gte":5,"200m_competitors_lte":1},
            "red_flag": {"500m_subway_eq":0,"200m_competitors_gt":3},
        },
    },
}

# ============================================================
# 前端32个业态 → 14个集群映射
# ============================================================
BUSINESS_TYPE_TO_MASTER = {
    # 餐饮
    "小餐饮": "刚需快餐小吃", "小吃店": "刚需快餐小吃", "快餐店": "刚需快餐小吃",
    "大餐饮": "中餐正餐", "中餐": "中餐正餐",
    "火锅店": "火锅_烧烤", "烧烤店": "火锅_烧烤",
    "西餐": "异国_中高端正餐", "日餐": "异国_中高端正餐",
    # 茶饮咖啡
    "奶茶店": "精品茶饮咖啡", "咖啡店": "精品茶饮咖啡", "饮品店": "精品茶饮咖啡",
    "甜品店": "烘焙甜品", "烘焙店": "烘焙甜品",
    # 酒店
    "酒店": "商务酒店", "民宿": "民宿青旅", "青年旅舍": "民宿青旅",
    # 零售
    "便利店": "高频刚需零售", "小超市": "高频刚需零售", "超市": "高频刚需零售", "药店": "高频刚需零售",
    "生鲜店": "高频刚需零售", "水果店": "高频刚需零售", "菜店": "高频刚需零售",
    "烟酒店": "高频刚需零售", "烟酒行": "高频刚需零售",
    "日用百货": "高频刚需零售", "百货店": "高频刚需零售", "杂货店": "高频刚需零售",
    "零售店": "低频目的零售", "服装店": "低频目的零售", "数码店": "低频目的零售",
    # 生活服务
    "美容美发": "专业生活服务", "宠物店": "专业生活服务", "健身房": "专业生活服务",
    "教育培训": "社区基础服务", "洗衣店": "社区基础服务", "诊所": "社区基础服务",
    # 休闲娱乐
    "酒吧": "夜经济娱乐", "KTV": "夜经济娱乐", "网吧": "夜经济娱乐",
    "剧本杀": "沉浸式社交娱乐", "台球厅": "沉浸式社交娱乐",
}

# ============================================================
# 环境POI key映射
# ============================================================
ENV_POI_MAP = {
    "hospital": "hospitals", "school": "schools", "bus": "bus",
    "subway": "subway", "office": "office", "shopping": "shopping",
}

DEFAULT_MASTER = {
    "label":"通用","focus_radius":500,"competitor_amap_types":"",
    "radar_weights":{"population_density":20,"traffic_accessibility":20,"competition":20,"complementary_businesses":20,"cost_estimate":20},
    "target_keywords":[],"competitor_blacklist":[],"ignore_environmental_pois":[],
    "traffic_weight_override":"","core_strategy":"灵活制定运营策略。",
    "price_range":(10,100),
    "thresholds":{"s_grade":{"500m_subway_gte":1},"red_flag":{"200m_competitors_gt":15}},
}

# ═══════════════════════════════════════════════════════════════
# ★ 业态严谨度配置框架 (Rigor Framework v1)
# 每个行业集群定义：直接竞品、替代竞品、客流锚点、无关POI、
# 评分依据、营收模型、报告语言规则
# ═══════════════════════════════════════════════════════════════

# ── 通用报告语言规则（所有业态共享）──
COMMON_LANGUAGE_RULES = {
    "forbidden_raw_as_valid": "禁止把 raw_count 写成有效判断依据。所有数字默认引用 valid_count。若必须提原始数据，标注'原始POI，未参与评分'。",
    "forbidden_anchor_as_competitor": "禁止把客流锚点品牌/业态写成竞品。",
    "forbidden_substitute_as_direct": "禁止把替代性竞品写成直接竞品。",
    "forbidden_same_fact_both_sides": "同一事实禁止同时出现在优势和风险中，除非明确拆分为需求端/供给端/执行端并标注边界。",
    "forbidden_fabricated_numbers": "禁止无依据的精确客流/精确利润数字。若无实测数据，写'缺少实测客流，需线下验证'。",
    "hypothesis_format": "所有运营建议必须写成'待验证假设 + 验证动作'格式，不得输出推荐/不推荐结论。",
    "data_insufficient": "数据不足时明确写'数据不足，需线下验证'，不得用 AI 常识补 POI 名称或数字。",
}

# ── 通用营收假设模板（各业态可覆盖）──
DEFAULT_REVENUE_MODEL = {
    "scenario_count": 3,
    "scenarios": ["保守", "中性", "乐观"],
    "required_assumptions": ["日客流量", "转化率", "客单价", "毛利率", "人工成本", "月租金", "水电杂费", "库存资金", "爬坡期(月)"],
    "output_format": "输出三档月营收区间、月净利区间、回本周期区间（禁止单点精确值，如'23.6万'），每档标注置信度和模型假设，标注'估算，不代表承诺，需线下实测验证'。",
}

# ═══════════════════════════════════════════════════════════════
# 14 个行业集群 → 严谨度规则
# ═══════════════════════════════════════════════════════════════
INDUSTRY_RIGOR = {
    # ========== 1. 异国/中高端正餐 ==========
    "异国_中高端正餐": {
        "direct_competitor_rules": {
            "amap_codes": ["050100", "050200"],
            "require_name_keyword_for_code": True,
            "substitute_before_direct": True,
            "name_keywords": ["西餐","日料","法餐","意餐","私房","公馆","海鲜","料理","牛扒","铁板烧","omakase","怀石","牛排","披萨","扒房","刺身","天妇罗","韩式","韩国","东南亚","泰国","越南"],
            "exclude_names": ["快餐","小吃","面馆","食堂","麻辣烫","汉堡","炸鸡","米线","黄焖鸡","烧烤","烤串","大排档","茶饮","咖啡","奶茶","甜品","烘焙"],
        },
        "substitute_competitor_rules": {
            "description": "中高端中餐/火锅可能分流部分宴请客群，但不算直接竞品",
            "name_keywords": ["酒楼","宴","中餐","湘菜","川菜","粤菜","火锅","东北菜","西北菜","本帮菜","烤鸭"],
        },
        "traffic_anchor_rules": {
            "description": "高档商场/写字楼/高端酒店/停车场为客流锚点",
            "categories": ["shopping","office","hotels","parking"],
            "name_keywords": ["购物中心","百货","写字楼","国际中心","酒店","希尔顿","万豪","洲际"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["快餐","小吃","面馆","麻辣烫","汉堡","炸鸡","食堂","盒饭","盖浇饭","黄焖鸡","沙县","兰州拉面","桂林米粉","米线"],
            "categories_excluded": ["schools","hospitals","bus"],
        },
        "scoring_rules": {
            "population_density": "周边1km内住宅+写字楼+酒店的有效人口估算",
            "traffic_accessibility": "停车场数量+地铁站+主干道可达性（该业态目的性消费，停车权重最高）",
            "competition": "仅基于 direct_competitors 的密度和品牌势能",
            "cost_estimate": "按中高端餐饮标准：租金占比≤15%，人工占比25-30%，食材成本30-35%",
        },
        "revenue_model": {
            "logic": "桌数×翻台率×人均消费×月营业天数；晚市占60%+营收",
            "key_metrics": ["桌数","午市翻台","晚市翻台","人均消费","包厢数","酒水占比"],
        },
    },

    # ========== 2. 火锅/烧烤 ==========
    "火锅_烧烤": {
        "direct_competitor_rules": {
            "amap_codes": ["050100"],
            "require_name_keyword_for_code": True,
            "name_keywords": ["火锅","烧烤","烤串","烤肉","涮肉","羊蝎子","烤鱼","小龙虾","大排档","串串香","麻辣烫"],
            "exclude_names": ["快餐","小吃","面馆","包子","食堂","盒饭","茶饮","咖啡","奶茶","西餐","日料","日本料理","寿司"],
        },
        "substitute_competitor_rules": {
            "description": "中餐正餐/大排档/夜市可分流部分聚餐需求",
            "name_keywords": ["中餐","湘菜","川菜","大排档","夜市","排档"],
        },
        "traffic_anchor_rules": {
            "description": "KTV/酒吧/台球厅/酒店为夜经济锚点；停车场为核心加分项",
            "categories": ["bars","hotels","parking"],
            "name_keywords": ["KTV","酒吧","酒店","停车场"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["茶饮","咖啡","奶茶","西餐","日料","日本料理","寿司","快餐","小吃","面馆","包子","食堂"],
            "categories_excluded": [],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors（火锅/烧烤/烤鱼等），餐饮/快餐不计入",
            "cost_estimate": "火锅：租金≤12%，人工18-22%，食材35-40%；翻台率1.2-1.5",
        },
        "revenue_model": {
            "logic": "桌数×翻台率×人均×天数；晚市+宵夜占70%+；重点核查排烟/燃气/电力",
        },
    },

    # ========== 3. 刚需快餐小吃 ==========
    "刚需快餐小吃": {
        "direct_competitor_rules": {
            "amap_codes": ["050300"],
            "require_name_keyword_for_code": True,  # ★ 050300 是大类，必须同时命中关键词才算 direct
            "substitute_before_direct": True,  # ★ 鸭脖/卤味/炸鸡/汉堡优先进 substitute，不进 direct
            # ★ 收紧关键词：不用单字(面/皮/粉/饭/包/粥)，只用明确小吃/快餐品类词组
            "name_keywords": [
                "擀面皮","面皮","凉皮","米皮","烙面皮",
                "米线","酸辣粉","螺蛳粉","热干面","麻辣烫","麻辣拌",
                "肉夹馍","包子","饺子","馄饨","锅贴","生煎","小笼",
                "砂锅","冒菜","煎饼","烤冷面","手抓饼","鸡蛋灌饼",
                "拉面","拌面","刀削面","汤面","干拌","臊子面","油泼面","蘸水面","饸饹",
                "泡馍","水盆","biangbiang",
                "快餐","小吃","便当","盖浇","云饺","水饺",
            ],
            "exclude_names": [
                "酒楼","海鲜","西餐","私房菜","公馆","大饭店","自助餐",
                "火锅","烤肉","烧烤","烤鱼","大排档",
                "韩国料理","日料","寿司","刺身","韩式","韩餐",
                "茶饮","咖啡","奶茶","甜品","烘焙","蛋糕",
                "鸭脖","卤味","串串","炸鸡","汉堡","披萨",
                "星级酒店","星级",
            ],
        },
        "substitute_competitor_rules": {
            "description": "便利店鲜食/超市熟食/食堂可替代部分午市刚需。鸭脖/卤味/炸鸡/汉堡为邻近品类替代。",
            "categories": ["convenience"],
            "name_keywords": ["便利店","超市","食堂","单位食堂","学校食堂","鸭脖","卤味","炸鸡","汉堡","鸡排"],
        },
        "traffic_anchor_rules": {
            "description": "写字楼/学校/医院/公交站/地铁站为核心客流锚点",
            "categories": ["office","schools","hospitals","subway","bus"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": [
                "大酒楼","海鲜酒楼","星级酒店","高端西餐","法餐","日料","怀石",
                "火锅","烤肉","韩国料理","寿司","茶饮","咖啡","奶茶","甜品",
            ],
            "categories_excluded": [],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors 中同名/同品类门店密度",
            "cost_estimate": "快餐：租金≤15%，人工15-20%，食材30-35%；外卖占比30-50%",
        },
        "revenue_model": {
            "logic": "日均单量×客单价×30天；午市占60%+；外卖/堂食分算；翻台率3-5次",
        },
    },

    # ========== 4. 中餐正餐 ==========
    "中餐正餐": {
        "direct_competitor_rules": {
            "amap_codes": ["050100"],
            "require_name_keyword_for_code": True,
            "substitute_before_direct": True,
            "name_keywords": ["酒楼","宴","中餐","湘菜","川菜","粤菜","西北菜","东北菜","本帮菜","私房","烤鸭","海鲜","鲁菜","苏菜","淮扬","淮扬菜","闽菜","浙菜","徽菜","中式","土菜"],
            "exclude_names": ["快餐","小吃","面馆","麻辣烫","汉堡","食堂","大排档","茶饮","咖啡","奶茶","西餐","日料","日本料理","韩式","韩国","韩国料理","东南亚","泰国","越南","茶餐厅","简餐"],
        },
        "substitute_competitor_rules": {
            "description": "火锅/烧烤可能分流聚餐需求",
            "name_keywords": ["火锅","烧烤","烤肉"],
        },
        "traffic_anchor_rules": {
            "categories": ["shopping","office","parking","subway"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["快餐","小吃","面馆","麻辣烫","汉堡","炸鸡","米线","食堂","大排档"],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors；停车位数量影响可达性评分",
        },
        "revenue_model": {
            "logic": "桌数×翻台率×人均×天数；晚市占65%+；包厢数≥2为加分项",
        },
    },

    # ========== 5. 烘焙甜品 ==========
    "烘焙甜品": {
        "direct_competitor_rules": {
            "amap_codes": ["050600"],
            "require_name_keyword_for_code": True,
            "substitute_before_direct": True,
            "name_keywords": ["烘焙","面包","蛋糕","甜点","泡芙","蛋挞","慕斯","马卡龙","曲奇","冰淇淋","甜品"],
            "exclude_names": ["包子","馒头","大饼","油条","煎饼","食堂","便利店","超市","火锅","烧烤","茶饮","咖啡","奶茶"],
        },
        "substitute_competitor_rules": {
            "description": "咖啡/茶饮店甜品可部分替代",
            "name_keywords": ["咖啡","茶饮","奶茶"],
        },
        "traffic_anchor_rules": {
            "categories": ["residential","schools","subway","shopping"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["包子铺","馒头店","大饼","油条","食堂","快餐","火锅","烧烤","便利店","超市","煎饼"],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors；学校/地铁口权重加分",
        },
        "revenue_model": {
            "logic": "日均客流×转化率×客单价；冲动消费为主；橱窗展示面≥3米",
        },
    },

    # ========== 6. 精品茶饮咖啡 ==========
    "精品茶饮咖啡": {
        "direct_competitor_rules": {
            "amap_codes": ["050500"],
            "require_name_keyword_for_code": True,
            "substitute_before_direct": True,
            "name_keywords": ["奶茶","咖啡","茶饮","果饮","柠檬","酸奶","星巴克","瑞幸","喜茶","奈雪","蜜雪冰城","茶百道","古茗","霸王茶姬","Manner","库迪","幸运咖","一点点","CoCo","书亦","益禾堂"],
            "exclude_names": ["酒吧","茶馆","棋牌","甜品","冰淇淋","便利店","超市","火锅","烧烤"],
        },
        "substitute_competitor_rules": {
            "description": "便利店饮料/甜品店/冰淇淋可部分替代",
            "categories": ["convenience"],
            "name_keywords": ["便利店","超市","甜品","冰淇淋"],
        },
        "traffic_anchor_rules": {
            "categories": ["office","schools","subway","shopping","residential"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["酒吧","KTV","棋牌","网吧"],
            "categories_excluded": ["hospitals"],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors，便利店/甜品不算直接竞品",
        },
        "revenue_model": {
            "logic": "日均杯量×客单价×30天；外卖占比30-50%；会员储值锁复购",
        },
    },

    # ========== 7-8. 酒店/民宿 ==========
    "商务酒店": {
        "direct_competitor_rules": {
            "amap_codes": ["100000"],
            "require_name_keyword_for_code": True,  # ★ 100000 是大类，必须同时命中酒店关键词
            "substitute_before_direct": True,
            "strict_exclude_names": ["洗浴","足浴","会所","KTV","餐饮","写字楼","公寓销售","日租房","钟点房","农家乐"],
            "name_keywords": ["酒店","宾馆","汉庭","如家","全季","亚朵","希尔顿","万豪","洲际","维也纳","丽枫","锦江","格林豪泰","尚客优","旅店","快捷酒店","连锁酒店","商务酒店"],
            "exclude_names": ["招待所","农家乐","洗浴","日租房","钟点房","民宿","旅舍","客栈","公寓","青旅","电竞"],
        },
        "substitute_competitor_rules": {
            "description": "民宿/公寓/钟点房/电竞酒店可部分替代",
            "name_keywords": ["民宿","公寓","青旅","电竞酒店","日租房"],
        },
        "traffic_anchor_rules": {
            "description": "交通枢纽/商务区/医院/会展/景区为客流锚点",
            "categories": ["office","shopping","subway","hospitals"],
            "name_keywords": ["火车站","汽车站","机场","会展","医院","商务中心"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["招待所","农家乐","洗浴","日租房","钟点房","足浴","会所","KTV"],
            "categories_excluded": ["schools"],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors 中同档次酒店",
        },
        "revenue_model": {
            "logic": "房间数×入住率×ADR×30天；RevPAR为核心指标",
        },
    },
    "民宿青旅": {
        "direct_competitor_rules": {
            "amap_codes": ["100000"],
            "require_name_keyword_for_code": True,  # ★ 100000 是大类，必须同时命中民宿/青旅关键词
            "substitute_before_direct": True,
            "strict_exclude_names": ["洗浴","足浴","会所","KTV","日租房","钟点房","农家乐","招待所"],
            "name_keywords": ["民宿","旅舍","客栈","青旅","背包客","青年旅舍","背包旅舍","背包客栈","家庭旅馆"],
            "exclude_names": ["星级酒店","希尔顿","万豪","洲际","商务酒店","温泉酒店","电竞酒店","公寓","宾馆"],
        },
        "substitute_competitor_rules": {
            "description": "经济型酒店/公寓/电竞酒店可替代",
            "name_keywords": ["汉庭","如家","公寓","电竞酒店","快捷酒店","经济型酒店"],
        },
        "traffic_anchor_rules": {
            "categories": ["subway","shopping"],
            "name_keywords": ["景区","地铁站","火车站","步行街","大学城"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["星级酒店","希尔顿","万豪","洲际","洗浴","足浴","KTV"],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors",
        },
        "revenue_model": {
            "logic": "床位/房间×入住率×客单价×30天；小红书+抖音获客权重高",
        },
    },

    # ========== 9. 高频刚需零售（便利店/超市/药店）==========
    "高频刚需零售": {
        "direct_competitor_rules": {
            "note": "★ subtypes 实现子业态独立规则，inherit master strict_exclude",
            "require_name_keyword_for_code": True,   # ★ 所有 subtype 继承
            "substitute_before_direct": True,
            "strict_exclude_names": ["会计","律所","律师","广告","装饰","装修","房产","地产","中介","科技","企业服务","SPA","美容","美发","理发","培训","教育","公司","政府","机关","社区服务中心","党群","便民服务中心","彩票","福彩","体彩","充电站","充电桩","旅行社","劳务","人力","家政","搬家","开锁","疏通","驾校","文印","照相","刻章","缝纫","修理","修鞋","配钥匙","干洗","皮具","擦鞋","美甲","纹身","按摩","采耳","洗浴","汗蒸","推拿","艾灸","拔罐","眼镜","养生","足疗","足道","建材","五金","批发","农贸","汽配","家具","灯饰","石材","印刷","旧货","二手","废品","回收"],
            "subtypes": {
                "supermarket": {
                    "match_keywords": ["超市","便利店","小超市","永辉","盒马","711","罗森","全家","便利蜂","美宜佳","大润发","华润万家","物美","沃尔玛","联华"],
                    "name_keywords": ["便利店","超市","小卖部","便利","永辉","盒马","711","罗森","全家","便利蜂","美宜佳","大润发","华润万家","物美","沃尔玛","联华","社区超市","便民超市"],
                    "exclude_names": ["建材","五金","批发","农贸","汽配","家具","灯饰","石材","旧货","二手","废品","回收","百货大楼","购物中心","商场","药房","药店","大药房","医院","诊所"],
                },
                "fresh": {
                    "match_keywords": ["生鲜","水果","蔬菜","肉禽","蛋奶","水产","海鲜"],
                    "name_keywords": ["生鲜","水果","蔬菜","鲜肉","水产","海鲜","果品","鲜果","蔬果","果蔬","菜店","菜场","菜市场"],
                    "exclude_names": ["便利店","百货","五金","建材","批发","冷库","物流","餐饮","饭店","食堂","药房","药店"],
                },
                "pharmacy2": {
                    "match_keywords": ["药店","药房","医药","中药"],
                    "name_keywords": ["药店","药房","大药房","医药","同仁堂","老百姓","益丰","一心堂","健之佳","海王星辰","大参林","国药"],
                    "exclude_names": ["器械","体验中心","门诊","诊所","医院","眼科","视光","助听器","医美","皮肤","理疗","体检","康复","牙科","口腔"],
                },
                "tobacco_liquor": {
                    "match_keywords": ["烟酒","名烟","名酒","酒类","酒行"],
                    "name_keywords": ["烟酒","名烟","名酒","酒行","酒类","烟草","酒庄","1919","酒便利","烟酒店","烟酒行","酒水商行"],
                    "exclude_names": ["超市","便利店","百货","酒吧","餐厅","KTV","茶叶","茶庄"],
                },
                "daily_goods": {
                    "match_keywords": ["百货","日用","杂货","日杂","副食","粮油"],
                    "name_keywords": ["百货","日用","杂货","日杂","副食","粮油","两元店","十元店","日用品"],
                    "exclude_names": ["建材","五金","批发","农贸","商场","购物中心","服装","鞋帽","家电","数码","便利店","超市"],
                },
            },
        },
        "substitute_competitor_rules": {
            "description": "餐饮/快餐/咖啡/茶饮仅影响便当、饮品、熟食等即时消费品类",
            "categories": ["fast_food","cafe_tea","restaurants"],
            "name_keywords": ["快餐","小吃","咖啡","茶饮","奶茶","炸鸡","汉堡"],
            "impact_scope": "仅限即时鲜食/饮品/熟食子品类，不影响日杂百货核心品类",
        },
        "traffic_anchor_rules": {
            "description": "住宅/学校/写字楼/医院/公交站为社区客流锚点",
            "categories": ["residential","office","schools","hospitals","subway","bus"],
            "name_keywords": ["肯德基","麦当劳","瑞幸","星巴克","酒店","汉庭","如家"],
            "note": "连锁餐饮/酒店品牌仅表示商业活跃度，不是便利店竞品",
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["会计","律所","律师","广告","装饰","装修","房产","地产","中介","科技","企业服务","SPA","美容","美发","理发","培训","教育","公司","政府","机关","社区服务中心","党群","便民服务中心","彩票","福彩","体彩","充电站","旅行社","劳务","人力","家政","搬家","开锁","疏通","驾校","文印","照相","刻章","缝纫","修理","修鞋","配钥匙","干洗","皮具","擦鞋","美甲","纹身","按摩","采耳","洗浴","汗蒸","推拿","艾灸","拔罐","眼镜","养生","足疗","足道","建材","五金","批发","农贸","汽配","家具","灯饰","石材","印刷","旧货","二手","废品","回收"],
        },
        "scoring_rules": {
            "population_density": "周边500m内住宅+学校+写字楼+医院的有效人口估算",
            "competition": "★ 仅基于 direct_competitors，餐饮/咖啡/茶饮不得计入竞争维度评分",
            "complementary_businesses": "学校/写字楼/医院/公交站视为客流锚点，不代表直接竞争",
        },
        "revenue_model": {
            "logic": "日均客流×转化率×客单价×30天；毛利率20-30%；损耗率3-8%；库存周转15-30天；鲜食占比提升毛利率但增加损耗",
            "key_metrics": ["日均进店人数","转化率","客单价","毛利率","鲜食占比","损耗率","库存资金","日补货频次"],
        },
    },

    # ========== 10. 低频目的零售（服装/数码/专卖）==========
    "低频目的零售": {
        "direct_competitor_rules": {
            "amap_codes": ["060100", "060400"],
            "require_name_keyword_for_code": True,
            "substitute_before_direct": True,
            "name_keywords": ["服装","鞋帽","数码","手机","电脑","家电","眼镜","珠宝","名创优品","屈臣氏","优衣库"],
            "exclude_names": ["批发","建材","五金","农贸","汽配","超市","便利店","水果","生鲜","菜市场","杂货","维修","彩票"],
        },
        "substitute_competitor_rules": {
            "description": "电商/综合商场可分流",
        },
        "traffic_anchor_rules": {
            "categories": ["shopping","subway","office"],
            "name_keywords": ["购物中心","百货","步行街"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["批发","建材","五金","农贸","汽配","超市","便利店","水果","生鲜","菜市场","杂货","维修","彩票","美甲","快递","手机维修","黄金回收"],
        },
        "scoring_rules": {
            "competition": "仅基于 direct_competitors；同类聚集（扎堆）为正相关",
        },
        "revenue_model": {
            "logic": "日均进店×转化率×客单价×复购周期；注意库存周转率和资金占用",
        },
    },

    # ========== 11. 专业生活服务（美容/宠物/健身）==========
    "专业生活服务": {
        "direct_competitor_rules": {
            "note": "★ 通过 subtypes 实现子业态独立规则，美容/宠物/健身互不污染",
            "require_name_keyword_for_code": True,
            "subtypes": {
                "beauty": {
                    "match_keywords": ["美容","美发","美甲","美体","SPA"],
                    "name_keywords": ["美容","美发","美甲","美睫","美体","SPA","皮肤管理","造型","形象设计","护肤"],
                    "exclude_names": ["宠物","动物","健身","瑜伽","舞蹈","足疗","按摩","推拿","艾灸","拔罐","洗浴","汗蒸","医美","整形","皮肤科","口腔","牙科"],
                },
                "pets": {
                    "match_keywords": ["宠物","猫舍","犬舍"],
                    "name_keywords": ["宠物","宠物店","宠物用品","宠物美容","猫舍","犬舍","宠物生活馆"],
                    "exclude_names": ["美容","美发","健身","动物医院","宠物医院","兽医","兽药"],
                    "substitute_before_direct": True,
                    "substitute_keywords": ["宠物医院","宠物美容"],
                },
                "fitness": {
                    "match_keywords": ["健身","瑜伽","舞蹈","普拉提","私教"],
                    "name_keywords": ["健身","瑜伽","舞蹈","普拉提","私教","游泳","拳击","CrossFit","操课","体能","力量"],
                    "exclude_names": ["宠物","美容","美发","足疗","按摩","推拿","体育用品","体育器材","培训","教育","少儿","儿童"],
                    "substitute_before_direct": True,
                    "substitute_keywords": ["动感单车","搏击","跆拳道"],
                },
            },
        },
        "substitute_competitor_rules": {
            "description": "社区理发/平价快剪可替代部分美发服务；家庭健身/户外替代部分健身房需求",
            "name_keywords": ["快剪","平价","社区理发","家庭健身","户外跑步"],
        },
        "traffic_anchor_rules": {
            "categories": ["residential","office","shopping","parking"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["快剪","街边理发","10元店","平价","足疗","按摩","推拿","洗浴","汗蒸","医美","整形"],
        },
        "scoring_rules": {
            "competition": "仅基于同品类 direct_competitors。美容不能把宠物店/健身/按摩算竞品。",
        },
        "revenue_model": {
            "logic": "到店频次×项目客单×会员转化率；复购周期决定现金流稳定性",
        },
    },

    # ========== 12. 社区基础服务（教育/洗衣/诊所）==========
    "社区基础服务": {
        "direct_competitor_rules": {
            "note": "★ 通过 subtypes 实现子业态独立规则，教育/洗衣/诊所互不污染",
            "require_name_keyword_for_code": True,
            "subtypes": {
                "education": {
                    "match_keywords": ["培训","教育","琴行","画室","早教","托管","辅导","补习","学"],
                    "name_keywords": ["培训","教育","琴行","画室","早教","托管","辅导","补习","驾校","职业技能","语言培训","美术","音乐","舞蹈培训","书法"],
                    "exclude_names": ["洗衣","诊所","门诊","学校","幼儿园","小学","中学","大学","文具","书店","办公用品"],
                },
                "laundry": {
                    "match_keywords": ["洗衣","干洗","洗护"],
                    "name_keywords": ["洗衣","干洗","清洗","护理","洗护","洗衣店","干洗店"],
                    "exclude_names": ["培训","教育","诊所","家政","维修","皮具护理","擦鞋"],
                    "substitute_before_direct": True,
                    "substitute_keywords": ["家政","维修"],
                },
                "clinic": {
                    "match_keywords": ["诊所","门诊","卫生所","医务室"],
                    "name_keywords": ["诊所","门诊","卫生所","社区卫生","卫生室","医务室","中医诊所","中西医结合"],
                    "exclude_names": ["培训","教育","洗衣","宠物","动物","医院","口腔医院","眼科医院","医美","体检","助听器","药店","大药房"],
                    "substitute_before_direct": True,
                    "substitute_keywords": ["药店","保健"],
                },
            },
        },
        "substitute_competitor_rules": {
            "description": "学校课后托管可替代培训机构；社区洗衣房/自助洗衣可替代",
        },
        "traffic_anchor_rules": {
            "categories": ["residential","schools","office"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["驾校","职业培训","医院","药店"],
        },
        "scoring_rules": {
            "competition": "仅基于同品类 direct_competitors。培训不能把洗衣店/诊所/学校算竞品。",
        },
        "revenue_model": {
            "logic": "教育培训：生源数×客单价×续费率；洗衣：日均订单×客单价×复购率",
        },
    },

    # ========== 13. 夜经济娱乐（酒吧/KTV/网吧）==========
    "夜经济娱乐": {
        "direct_competitor_rules": {
            "note": "★ subtypes 实现酒吧/KTV/网吧互不污染。050400/080000 需 keyword 锁。",
            "amap_codes": ["050400", "080000"],
            "require_name_keyword_for_code": True,
            "substitute_before_direct": True,
            "strict_exclude_names": ["学校","医院","幼儿园","小学","中学"],
            "subtypes": {
                "bar": {
                    "match_keywords": ["酒吧","清吧","酒馆","精酿","威士忌","夜店","LiveHouse"],
                    "name_keywords": ["酒吧","清吧","酒馆","精酿","威士忌","夜店","LiveHouse","鸡尾酒"],
                    "exclude_names": ["KTV","网吧","网咖","台球","棋牌","餐厅","咖啡","茶","书店"],
                },
                "ktv": {
                    "match_keywords": ["KTV","歌厅","练歌房"],
                    "name_keywords": ["KTV","歌厅","练歌房","量贩KTV","卡拉OK"],
                    "exclude_names": ["酒吧","网吧","网咖","台球","棋牌","餐厅"],
                },
                "internet_cafe": {
                    "match_keywords": ["网吧","网咖","电竞馆","电竞酒店"],
                    "name_keywords": ["网吧","网咖","电竞馆","电竞酒店","电竞"],
                    "exclude_names": ["酒吧","KTV","台球","棋牌"],
                },
            },
        },
        "substitute_competitor_rules": {
            "description": "台球/棋牌/夜市/轰趴可分流部分夜间娱乐需求",
            "name_keywords": ["台球","棋牌","桌游","轰趴","夜市"],
        },
        "traffic_anchor_rules": {
            "categories": ["hotels","parking","subway"],
            "name_keywords": ["酒店","停车场","地铁站","酒吧街"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["学校","医院"],
            "categories_excluded": ["hospitals"],
        },
        "scoring_rules": {
            "competition": "仅基于同品类 direct_competitors。酒吧不能把 KTV/网吧算竞品。",
        },
        "revenue_model": {
            "logic": "周末/节假日权重高；人均消费×座位数×翻台率；隔音+消防硬成本",
        },
    },

    # ========== 14. 沉浸式社交娱乐（剧本杀/密室/台球/桌游/电玩）==========
    "沉浸式社交娱乐": {
        "direct_competitor_rules": {
            "note": "★ subtypes 实现剧本杀/密室/台球/桌游/电玩 互不污染",
            "require_name_keyword_for_code": True,
            "substitute_before_direct": True,
            "strict_exclude_names": ["麻将馆","KTV","酒吧","网吧","网咖","电竞酒店"],
            "subtypes": {
                "jubensha": {
                    "match_keywords": ["剧本杀","推理馆","谋杀之谜"],
                    "name_keywords": ["剧本杀","推理馆","谋杀之谜","沉浸式剧场","实景搜证"],
                    "exclude_names": ["密室","桌游","台球","电玩","VR","KTV","酒吧","网吧"],
                },
                "escape_room": {
                    "match_keywords": ["密室逃脱","密室","沉浸式密室"],
                    "name_keywords": ["密室逃脱","密室","沉浸式密室","机械密室","恐怖密室"],
                    "exclude_names": ["剧本杀","桌游","台球","电玩","VR","KTV","酒吧","网吧"],
                },
                "billiards": {
                    "match_keywords": ["台球","桌球","台球厅"],
                    "name_keywords": ["台球","桌球","台球厅","台球俱乐部","桌球室"],
                    "exclude_names": ["棋牌","桌游","剧本杀","密室","KTV","酒吧","网吧"],
                },
                "board_game": {
                    "match_keywords": ["桌游","棋牌","轰趴","轰趴馆","棋牌室"],
                    "name_keywords": ["桌游","棋牌","轰趴","轰趴馆","棋牌室","狼人杀","三国杀","德扑"],
                    "exclude_names": ["剧本杀","密室","台球","电玩","VR","KTV","酒吧","网吧"],
                },
                "arcade_vr": {
                    "match_keywords": ["电玩","VR","游戏厅","娱乐体验"],
                    "name_keywords": ["电玩","VR","虚拟现实","游戏厅","娱乐体验馆","主机游戏"],
                    "exclude_names": ["剧本杀","密室","台球","桌游","KTV","酒吧","网吧","电竞酒店"],
                },
            },
        },
        "substitute_competitor_rules": {
            "description": "KTV/网吧/酒吧/电竞酒店可部分替代社交娱乐需求",
            "name_keywords": ["KTV","网吧","酒吧","电竞酒店"],
        },
        "traffic_anchor_rules": {
            "categories": ["subway","schools","office"],
            "name_keywords": ["大学城","地铁站","写字楼"],
        },
        "irrelevant_poi_rules": {
            "name_blacklist": ["麻将馆"],
            "categories_excluded": ["hospitals"],
        },
        "scoring_rules": {
            "competition": "仅基于同品类 direct_competitors。剧本杀不能把密室/台球/KTV/酒吧算竞品。",
        },
        "revenue_model": {
            "logic": "周末四场×人均×容纳人数；剧本更新频率影响复购；台球按桌时计费",
        },
    },
}

# ═══════════════════════════════════════════════════════════════
# ★ 严谨度规则查询 API
# ═══════════════════════════════════════════════════════════════

def _get_rigor(config_key: str) -> dict:
    """获取指定行业集群的严谨度配置，缺失时返回空字典"""
    return INDUSTRY_RIGOR.get(config_key, {})

def get_rigor_for_business(business_type: str) -> dict:
    """通过 business_type（如 奶茶店）获取严谨度配置"""
    master_key = BUSINESS_TYPE_TO_MASTER.get(business_type, "")
    return _get_rigor(master_key)

def get_rigor_for_config_key(config_key: str) -> dict:
    """直接通过 MASTER_TEMPLATES key 获取严谨度配置"""
    return _get_rigor(config_key)

def get_config(business_type: str) -> dict:
    """通过 business_type（如 奶茶店）→ master_key → 返回配置"""
    return MASTER_TEMPLATES.get(BUSINESS_TYPE_TO_MASTER.get(business_type, ""), DEFAULT_MASTER)

def get_config_by_key(config_key: str) -> dict:
    """直接通过 MASTER_TEMPLATES 的 key 获取配置（数据驱动模式下使用）"""
    return MASTER_TEMPLATES.get(config_key, DEFAULT_MASTER)

def get_full_config(business_type: str) -> dict:
    """合并基础配置 + 严谨度配置 + 通用规则"""
    base = get_config(business_type)
    rigor = get_rigor_for_business(business_type)
    return {
        **base,
        "rigor": rigor,
        "language_rules": COMMON_LANGUAGE_RULES,
        "revenue_model": rigor.get("revenue_model", DEFAULT_REVENUE_MODEL),
    }
