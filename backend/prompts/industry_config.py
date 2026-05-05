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
    "便利店": "高频刚需零售", "超市": "高频刚需零售", "药店": "高频刚需零售",
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

def get_config(business_type: str) -> dict:
    return MASTER_TEMPLATES.get(BUSINESS_TYPE_TO_MASTER.get(business_type, ""), DEFAULT_MASTER)
