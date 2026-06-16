"""
P1 分业态生意模型服务 — 确定性函数，不依赖 LLM。
为不同业态提供差异化商业判断模板，解决"餐饮逻辑套用所有业态"的问题。
Phase 1: 支持 YAML 模型加载，business_model_version 注入快照。
"""
import re as _re
import os as _os
import yaml as _yaml

# P2: 小吃快餐学校午休动线按 K12 触发，需学校类型细分
from services.location_profile_service import compute_school_anchor_breakdown

_KNOWLEDGE_DIR = _os.path.join(_os.path.dirname(__file__), "..", "knowledge")
_MODELS_DIR = _os.path.join(_KNOWLEDGE_DIR, "business_models")

# 模型缓存
_model_cache = {}


def _int(v, default=0):
    try: return int(v)
    except: return default


def load_business_model(model_id: str) -> dict:
    """从 backend/knowledge/business_models/*.yaml 加载生意模型。"""
    if model_id in _model_cache:
        return _model_cache[model_id]
    # 按 model_id 匹配文件
    for fname in _os.listdir(_MODELS_DIR) if _os.path.isdir(_MODELS_DIR) else []:
        if not fname.endswith(".yaml"):
            continue
        path = _os.path.join(_MODELS_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = _yaml.safe_load(f)
            if data and data.get("model_id") == model_id:
                _model_cache[model_id] = data
                return data
        except Exception:
            pass
    return {}


def get_model_version(model_id: str) -> str:
    """获取模型版本字符串，例如 snack_fast_food@2026-06-15.v1。"""
    model = load_business_model(model_id)
    version = (model or {}).get("model_version", "unknown")
    return f"{model_id}@{version}"


# ═══════════════════════════════════════════════════════════
# 生意模型族群分类
# ═══════════════════════════════════════════════════════════

_EDUCATION_CHILDCARE_KW = [
    "托管", "小饭桌", "课后", "作业辅导", "午托", "晚托", "接送",
    "小学生托管", "学生托管", "课后服务", "儿童之家", "托辅",
]

_EDUCATION_TRAINING_KW = [
    "培训", "教育", "补习", "琴行", "画室", "早教", "辅导",
    "语言", "美术", "音乐", "舞蹈培训", "书法", "驾校",
    "职业技能", "学科", "奥数", "英语",
]

_SNACK_FAST_FOOD_KW = [
    "小吃", "快餐", "小餐饮", "面馆", "粉店", "米线", "麻辣烫",
    "砂锅", "炸鸡", "包子", "饺子", "便当", "盖浇饭", "肉夹馍",
    "凉皮", "擀面皮", "酸辣粉", "螺蛳粉", "热干面", "锅贴",
    "生煎", "小笼", "煎饼", "烤冷面", "手抓饼", "鸡蛋灌饼",
    "卤味", "鸭脖", "鸡排", "麻辣拌", "冒菜",
]

_FOOD_SERVICE_KW = [
    "餐饮", "中餐", "正餐", "酒楼", "火锅", "烧烤", "烤鱼",
    "西餐", "日料", "日餐", "海鲜", "牛排", "私房", "公馆",
    "湘菜", "川菜", "粤菜", "西北菜", "东北菜",
    "串串", "涮锅",
]

_BEVERAGE_DESSERT_KW = [
    "奶茶", "咖啡", "茶饮", "饮品", "果饮", "柠檬",
    "烘焙", "面包", "蛋糕", "甜点", "甜品", "冰淇淋",
    "星巴克", "瑞幸", "喜茶", "蜜雪冰城",
]

_RETAIL_CONVENIENCE_KW = [
    "便利店", "超市", "小超市", "生鲜", "水果店",
    "烟酒", "菜店", "日用", "百货", "杂货",
]

_PHARMACY_KW = [
    "药店", "药房", "医药", "中药", "大药房",
    "同仁堂", "老百姓", "益丰", "一心堂", "健之佳",
]

_RETAIL_SHOPPING_KW = [
    "服装", "数码", "专卖", "手机", "电脑", "家电", "眼镜", "珠宝",
    "零售店",
]

_SERVICE_BEAUTY_KW = [
    "美容", "美发", "美甲", "SPA", "宠物", "健身", "瑜伽", "舞蹈",
    "皮肤管理", "造型",
]

_SERVICE_BASIC_KW = [
    "洗衣", "干洗", "诊所", "家政", "维修", "开锁",
]

_HOTEL_KW = [
    "酒店", "宾馆", "民宿", "青旅", "旅舍", "客栈",
]

_ENTERTAINMENT_KW = [
    "酒吧", "KTV", "网吧", "网咖", "剧本杀", "密室", "台球",
    "桌游", "电玩", "轰趴", "VR", "夜经济",
]

_PET_KW = ["宠物", "猫舍", "犬舍"]


def _is_pet_business(business_type: str = "", brand_name: str = "", category: str = "") -> bool:
    """检测是否为宠物业态（非美容/美发/健身）。"""
    combined = f"{business_type or ''} {brand_name or ''} {category or ''}"
    for kw in _PET_KW:
        if kw in combined:
            return True
    return False


def classify_business_model_family(business_type: str, brand_name: str = "",
                                   category: str = "") -> str:
    """将 business_type 归入生意模型族群。使用 business_type + brand_name + category 三者。"""
    bt = (business_type or "").strip()
    bn = (brand_name or "").strip()
    cat = (category or "").strip()
    # 三者拼接：category 可能携带 industry_name / config_key 的专属业态名
    combined = f"{bt} {bn} {cat}"

    # 教育托管优先于教育培训
    for kw in _EDUCATION_CHILDCARE_KW:
        if kw in combined:
            return "education_childcare"
    for kw in _EDUCATION_TRAINING_KW:
        if kw in combined:
            return "education_training"

    for kw in _SNACK_FAST_FOOD_KW:
        if kw in combined:
            return "snack_fast_food"
    for kw in _BEVERAGE_DESSERT_KW:
        if kw in combined:
            return "beverage_dessert"
    for kw in _FOOD_SERVICE_KW:
        if kw in combined:
            return "food_service"
    for kw in _RETAIL_CONVENIENCE_KW:
        if kw in combined:
            return "retail_convenience"
    for kw in _PHARMACY_KW:
        if kw in combined:
            return "pharmacy"
    for kw in _RETAIL_SHOPPING_KW:
        if kw in combined:
            return "retail_shopping"
    for kw in _SERVICE_BEAUTY_KW:
        if kw in combined:
            return "service_beauty"
    for kw in _SERVICE_BASIC_KW:
        if kw in combined:
            return "service_basic"
    for kw in _HOTEL_KW:
        if kw in combined:
            return "hotel"
    for kw in _ENTERTAINMENT_KW:
        if kw in combined:
            return "entertainment"

    return "generic"


# ═══════════════════════════════════════════════════════════
# 地点基本面（同一地址不同业态共享）
# ═══════════════════════════════════════════════════════════

def compute_location_fundamentals(real_data: dict) -> dict:
    """从 real_data 计算与业态无关的地点基本面。"""
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    s10 = r.get("stats_1000m", {}) or {}
    s2 = r.get("stats_200m", {}) or {}

    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))
    school_500 = _int(s5.get("schools", 0))
    shopping_500 = _int(s5.get("shopping", 0))
    parking_500 = _int(s5.get("parking", 0))
    subway_500 = _int(s5.get("subway", 0))
    bus_500 = _int(s5.get("bus", 0))
    restaurants_1k = _int(s10.get("restaurants", 0))
    subway_applicable = r.get("subway_applicable", True)

    # 判定地点类型
    if school_500 >= 8:
        location_type = "学区及周边"
    elif office_500 >= 20 and shopping_500 >= 5:
        location_type = "商务商业复合区"
    elif office_500 >= 15:
        location_type = "商务办公区"
    elif res_500 >= 50:
        location_type = "高密度居住区"
    elif shopping_500 >= 8:
        location_type = "核心商圈"
    elif school_500 >= 3 and res_500 >= 5:
        location_type = "学区边缘 / 社区混合区"
    elif res_500 < 5 and office_500 < 5 and school_500 < 3:
        location_type = "弱交通住宅区 / 低密度边缘"
    elif res_500 >= 10:
        location_type = "社区底商 / 居住配套"
    else:
        location_type = "综合社区"

    # 标签
    if res_500 < 5 and office_500 < 3 and school_500 < 3:
        label = "低密度边缘位置"
    elif school_500 >= 5:
        label = "学区边缘位置"
    elif office_500 >= 15:
        label = "办公商圈位置"
    elif res_500 >= 30:
        label = "成熟居住区位置"
    elif shopping_500 >= 5:
        label = "商业中心位置"
    else:
        label = "社区混合位置"

    strengths = []
    risks = []

    if school_500 >= 5:
        strengths.append(f"500米内{school_500}所学校，学区客群基础较好")
    if res_500 >= 20:
        strengths.append(f"500米内{res_500}个住宅小区，居住密度较高")
    if office_500 >= 10:
        strengths.append(f"500米内{office_500}栋办公楼，办公人群可支撑午间消费")
    if shopping_500 >= 3:
        strengths.append(f"500米内{shopping_500}个商业体，商业氛围较好")
    if subway_500 >= 1:
        strengths.append(f"500米内有{subway_500}个地铁站，公共交通便捷")
    if bus_500 >= 5:
        strengths.append(f"500米内{bus_500}条公交线路，地面交通覆盖较好")
    if restaurants_1k >= 30:
        strengths.append(f"1000米内{restaurants_1k}家餐饮门店，餐饮生态活跃")

    if res_500 < 5:
        risks.append(f"500米内仅{res_500}个住宅小区，常住人口基础偏弱")
    if office_500 < 3 and school_500 < 3:
        risks.append("周边办公和学校供给不足，全天客流可能偏低")
    if shopping_500 == 0:
        risks.append("500米内无商业体，商业配套缺失")
    if subway_applicable and subway_500 == 0 and bus_500 <= 2:
        risks.append("公共交通条件较弱，客群导入依赖步行和自驾")
    if parking_500 == 0:
        risks.append("500米内无停车设施，自驾客群可达性受限")

    if not strengths:
        strengths.append("位置具备基础商业条件，需线下核验补充判断")
    if not risks:
        risks.append("部分经营数据需线下核验后确认")

    summary = (
        f"该位置为{location_type}：500米内{res_500}个住宅小区、"
        f"{office_500}栋办公楼、{school_500}所学校。"
        f"1000米内{restaurants_1k}家餐饮门店。"
    )

    return {
        "label": label,
        "type": location_type,
        "summary": summary,
        "strengths": strengths[:4],
        "risks": risks[:4],
    }


# ═══════════════════════════════════════════════════════════
# 生意模型快照（按业态不同）
# ═══════════════════════════════════════════════════════════

def compute_business_model_snapshot(real_data: dict, business_type: str,
                                     brand_name: str = "",
                                     store_size: int = 0,
                                     category: str = "") -> dict:
    """生成业态相关的生意模型快照。"""
    family = classify_business_model_family(business_type, brand_name, category)
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    s10 = r.get("stats_1000m", {}) or {}
    dc_200 = _int(r.get("direct_competitors_200m", 0))
    dc_500 = _int(r.get("direct_competitors_500m", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))
    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))
    school_500 = _int(s5.get("schools", 0))

    handlers = {
        "education_childcare": _snapshot_education_childcare,
        "education_training": _snapshot_education_training,
        "snack_fast_food": _snapshot_snack_fast_food,
        "food_service": _snapshot_food_service,
        "beverage_dessert": _snapshot_beverage_dessert,
        "retail_convenience": _snapshot_retail_convenience,
        "pharmacy": _snapshot_pharmacy,
        "retail_shopping": _snapshot_retail_shopping,
        "service_beauty": _snapshot_service_beauty,
        "service_basic": _snapshot_service_basic,
        "hotel": _snapshot_hotel,
        "entertainment": _snapshot_entertainment,
        "generic": _snapshot_generic,
    }
    handler = handlers.get(family, _snapshot_generic)
    if family == "service_beauty":
        result = handler(real_data, business_type, brand_name, store_size, category=category)
    else:
        result = handler(real_data, business_type, brand_name, store_size)
    # 注入模型版本
    if "business_model_version" not in result:
        result["business_model_version"] = get_model_version(family)
    return result


def _snapshot_education_childcare(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    s2 = r.get("stats_200m", {}) or {}
    dc_200 = _int(r.get("direct_competitors_200m", 0))
    dc_500 = _int(r.get("direct_competitors_500m", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))
    res_500 = _int(s5.get("residential", 0))
    school_500 = _int(s5.get("schools", 0))
    school_200 = _int(s2.get("schools", 0))

    core_logic = (
        "托管/小饭桌生意的核心是：离周边小学近、放学动线经过、"
        "家长接送方便、空间满足分区需求、合规资质到位。"
        "托管需求由周边小学低年级学生数量和家长工作时间决定。"
    )

    # 竞品表达必须谨慎
    if dc_1000 == 0:
        competitor_note = (
            "地图POI未发现明确同类托管/小饭桌。但托管行业大量为非标准收录，"
            "可能存在暗竞品，需现场走访周边小区和学校门口确认是否有家庭式托管。"
        )
    elif dc_200 == 0 and dc_500 == 0 and dc_1000 > 0:
        competitor_note = (
            f"200米内无直接托管竞品，1000米内{dc_1000}家。"
            f"但托管竞品POI可能漏收录，需现场走访确认。"
        )
    else:
        competitor_note = (
            f"200米内{dc_200}家、500米内{dc_500}家托管类竞品。"
            f"注意：部分小饭桌和家庭托管可能未被POI收录。"
        )

    must_verify = [
        "从周边小学到店步行路线是否安全（不过主干道、有人行道）",
        "工作日15:30-17:00放学时段观察学生和家长动线是否经过门店",
        "家长接送临时停车是否方便",
        "周边是否有家庭式托管/小饭桌暗竞品（走访学校门口和小区）",
        "消防/食品/托管合规资质是否满足",
        "室内空间是否可分活动区、就餐区、作业区、卫生间",
        "周边家长是否有托管需求（访谈3-5位低年级家长）",
    ]

    fit_condition = (
        "步行5分钟内可达周边小学且动线安全，周边低年级家庭密度足够，"
        "空间可分3+功能区，合规资质可办理，租金可控且前期投入在预算内"
    )
    stop_condition = (
        "周边小学距离偏远或动线不安全，周边家庭密度不足，"
        "已有3家以上成熟托管且无差异化空间，合规资质无法办理，"
        "或月租金占比超预期"
    )

    # 评分解释
    if school_500 < 3 and res_500 < 10:
        score_explanation = (
            "周边小学和住宅均不足，竞争和品类评分均需谨慎看待。"
            "即使直接竞品数量为0，也不代表需求充足——需现场核验周边家庭实际托管需求。"
        )
    else:
        score_explanation = (
            "评分需结合周边小学距离和家庭密度综合判断。"
            "竞争维度仅反映POI收录的直接竞品数量，"
            "实际可能存在未被收录的暗竞品，不可仅凭表面数据决策。"
        )

    return {
        "model_type": "education_childcare",
        "core_logic": core_logic,
        "competitor_note": competitor_note,
        "must_verify": must_verify,
        "fit_condition": fit_condition,
        "stop_condition": stop_condition,
        "score_explanation": score_explanation,
    }


def _snapshot_education_training(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    res_500 = _int(s5.get("residential", 0))
    school_500 = _int(s5.get("schools", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))

    if dc_1000 == 0:
        competitor_note = (
            "地图POI未发现明确同类教育培训。部分小型培训机构可能未被收录，"
            "需现场走访社区和学校周边确认。"
        )
    else:
        competitor_note = f"1000米内{dc_1000}家教育培训门店，需现场核验其品类、客单价和满班率。"

    fit_condition = "周边家庭密度足够、目标客群（学龄儿童/成人）基数达标、交通便利、租金可控"
    stop_condition = "周边家庭密度不足、目标客群太少、已有成熟品牌覆盖、租金占比过高"

    must_verify = [
        "工作日放学后和周末观察学生/家长流量",
        "走访同类培训机构了解满班率和客单价",
        "确认周边3公里家庭消费力",
        "核验办学资质和消防要求",
        "考察停车和公共交通便利度",
    ]
    score_explanation = "评分需结合周边家庭密度和学生数量综合判断。竞争维度仅反映POI收录情况。"

    if school_500 >= 3 and res_500 < 5:
        must_verify.append("走访周边小区评估家庭消费力（房价/租金/车辆档次），确认与课程客单价匹配")
        score_explanation = (
            f"周边学校{school_500}所但住宅仅{res_500}个，学校数量不等同于有效生源。"
            f"需核验周边家庭消费力、客单价承受能力、续费意愿和满班率，不可仅凭学校数判断生源规模。"
        )

    return {
        "model_type": "education_training",
        "core_logic": "教育培训核心看周边家庭/学生密度、交通可达性和品牌差异化。续费和转介绍是核心获客方式。",
        "competitor_note": competitor_note,
        "must_verify": must_verify,
        "fit_condition": fit_condition,
        "stop_condition": stop_condition,
        "score_explanation": score_explanation,
    }


def _snapshot_snack_fast_food(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    s10 = r.get("stats_1000m", {}) or {}
    dc_200 = _int(r.get("direct_competitors_200m", 0))
    dc_500 = _int(r.get("direct_competitors_500m", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))
    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))
    school_500 = _int(s5.get("schools", 0))
    restaurants_1k = _int(s10.get("restaurants", 0))

    # 核心逻辑
    if dc_200 == 0 and dc_1000 >= 8:
        competitor_note = (
            f"200米内无同品类直接竞品，但1000米同类门店数量为 {dc_1000}，"
            f"餐饮门店 {restaurants_1k} 家。近场空档可能来自低客流或商圈未成熟，"
            f"不能简单判断为市场空白。需现场核验午晚高峰实际人流和同类门店经营状况。"
        )
    elif dc_200 == 0:
        competitor_note = (
            f"200米内无直接竞品，近场存在品类空白。但需核验是否因低人流导致无供给。"
            f"同类门店 500米{dc_500}家、1000米{dc_1000}家。"
        )
    elif dc_1000 >= 10:
        competitor_note = (
            f"1000米同类门店数量为 {dc_1000}，餐饮门店 {restaurants_1k} 家，"
            f"整体餐饮竞争较充分。适合小档口、低租金、强午市模型。"
        )
    else:
        competitor_note = (
            f"同类门店 200米{dc_200}家、500米{dc_500}家、1000米{dc_1000}家。"
        )

    # fit / stop 更锋利
    fit_condition = (
        "租金低、1-2人可运营、午市学校/办公客流实测成立、"
        "外卖可覆盖晚餐缺口、出餐速度快适合档口模型"
    )
    stop_condition = (
        "租金高、晚餐和周末客流弱、外卖出单不足、"
        "或远场同类供给过多导致价格竞争激烈时，不应作为优先候选点"
    )

    # 评分解释
    if dc_200 == 0 and dc_1000 >= 8:
        score_explanation = (
            f"竞争评分看似高（近场无人竞争），但1000米同类门店数量为 {dc_1000}，"
            f"辐射范围竞争不可忽视。总分受住宅({res_500})、"
            f"办公({office_500})、交通等维度拉低。"
        )
    else:
        score_explanation = (
            "评分需结合近场竞品密度和远场辐射竞争综合判断。"
            "小吃快餐的核心是午市客流的确定性，不能仅看竞品数量。"
        )

    return {
        "model_type": "snack_fast_food",
        "core_logic": "小吃快餐生意的核心：午市刚需客流确定性、出餐速度、低租金小档口、外卖补晚餐。翻台率和盈亏平衡单量决定生死。",
        "competitor_note": competitor_note,
        "must_verify": [
            "工作日11:30-13:00午高峰实测门前人流",
            "观察200m内和1000m内同类门店午高峰上座率",
            "走访相邻商户了解真实租金和转让费",
            "检查外卖骑手停车和取餐便利度",
            "观察门头可见度和道路动线",
        ],
        "fit_condition": fit_condition,
        "stop_condition": stop_condition,
        "score_explanation": score_explanation,
    }


def _snapshot_food_service(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s10 = r.get("stats_1000m", {}) or {}
    dc_200 = _int(r.get("direct_competitors_200m", 0))
    dc_500 = _int(r.get("direct_competitors_500m", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))
    restaurants_1k = _int(s10.get("restaurants", 0))

    if dc_1000 == 0 and dc_500 == 0:
        competitor_note = (
            f"1000米内未检出同品类正餐门店，周边餐饮{restaurants_1k}家。"
            f"正餐为半聚集型，0竞品不简单等于竞争压力低——需核验停车便利度、"
            f"周边餐饮生态成熟度和自身品质支撑，不可简单视为品类机会。"
        )
    elif dc_200 == 0 and dc_1000 >= 6:
        competitor_note = (
            f"近场无直接竞品，但1000米同类{dc_1000}家、餐饮{restaurants_1k}家。"
            f"正餐半聚集型需看停车条件和晚市聚餐需求是否成立。"
        )
    elif dc_200 == 0:
        competitor_note = (
            f"近场无直接竞品，1000米同类{dc_1000}家。"
            f"需核验停车、晚市客流和周边餐饮生态。"
        )
    else:
        competitor_note = (
            f"200米直接竞品{dc_200}家、500米{dc_500}家、1000米{dc_1000}家。"
        )

    return {
        "model_type": "food_service",
        "core_logic": "正餐/火锅依赖晚市和周末聚餐，停车便利度、包厢数量、品牌势能是关键。",
        "competitor_note": competitor_note,
        "must_verify": [
            "晚市高峰18:00-20:00观察门口人流和停车情况",
            "走访同品类门店了解翻台率和客单价",
            "确认停车便利度和公共交通可达性",
            "核验排烟/消防/电力设施",
            "了解周边社区的消费力和外出就餐习惯",
        ],
        "fit_condition": "停车便利、晚市客流成立、租金占比合理、品牌有差异化",
        "stop_condition": "停车条件差、晚市客流明显不足、竞品密集且无差异化空间",
        "score_explanation": "正餐评分重点看晚市客流和停车便利度，不能仅看人口密度和竞品数量。",
    }


def _snapshot_beverage_dessert(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    s10 = r.get("stats_1000m", {}) or {}
    school_500 = _int(s5.get("schools", 0))
    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))
    dc_200 = _int(r.get("direct_competitors_200m", 0))
    dc_500 = _int(r.get("direct_competitors_500m", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))
    restaurants_1k = _int(s10.get("restaurants", 0))
    hot_brands = r.get("hot_brands", []) or []

    if dc_1000 == 0 and dc_500 == 0:
        brand_hint = ""
        if hot_brands:
            brand_hint = "周边存在强品牌门店覆盖，外卖平台需单独评估竞品密度。"
        competitor_note = (
            f"1000米内未检出同品类茶饮/咖啡门店，周边餐饮{restaurants_1k}家。"
            f"茶饮为半聚集型，0竞品不简单等于竞争压力低——需核验步行动线、"
            f"外卖平台强品牌覆盖和年轻客群实际存在量，不可简单视为品类机会。"
            + (f" {brand_hint}" if brand_hint else "")
        )
    elif dc_200 == 0 and dc_1000 >= 5:
        competitor_note = (
            f"近场无直接竞品，但1000米同类{dc_1000}家、餐饮{restaurants_1k}家。"
            f"茶饮半聚集型需核验步行动线和外卖平台强品牌覆盖。"
        )
    elif dc_200 == 0:
        competitor_note = (
            f"近场无直接竞品，1000米同类{dc_1000}家。"
            f"需核验步行动线、外卖平台排名和周边年轻客群密度。"
        )
    else:
        competitor_note = (
            f"200米直接竞品{dc_200}家、500米{dc_500}家、1000米{dc_1000}家。"
        )

    must_verify = [
        "工作日全天观察门前步行人流量",
        "观察最近地铁/公交出口到门店的动线",
        "走访同品类门店了解日均杯量/客单价",
        "确认外卖平台上的周边竞品排名和月销量",
    ]
    score_explanation = "茶饮咖啡重点看步行客流和动线曝光，人口密度和停车权重较低。"
    if school_500 >= 3 and res_500 < 5 and office_500 < 5:
        must_verify.append("核验最近学校校门口到门店的放学时段步行动线（学校客流≠步行动线客流）")
        score_explanation += "周边学校数量多但住宅/办公偏少，学校客流需核验校门口步行动线和放学时段实测，不可仅凭学校数判断年轻客群。"

    return {
        "model_type": "beverage_dessert",
        "core_logic": "茶饮/咖啡/烘焙依赖冲动消费和步行客流，核心看地铁口/学校门口/写字楼底层曝光位置。",
        "competitor_note": competitor_note,
        "must_verify": must_verify,
        "fit_condition": "位于核心动线上、步行客流充足、品牌有辨识度、外卖可覆盖",
        "stop_condition": "动线偏僻、步行客流不足、竞品密集且品牌势能弱",
        "score_explanation": score_explanation,
    }


def _snapshot_retail_convenience(real_data, business_type, brand_name, store_size):
    return {
        "model_type": "retail_convenience",
        "core_logic": "便利店/超市/生鲜做社区最后一公里生意，核心看周边住宅密度和小区出入口位置。",
        "competitor_note": "",
        "must_verify": [
            "统计周边500m内住宅小区数量和户数",
            "观察小区主出入口到门店的动线",
            "走访同类门店了解日均客流和客单价",
            "确认是否有新开或即将开业的竞品",
        ],
        "fit_condition": "周边住宅密度高、位于小区主出入口动线上、竞品不超过2家",
        "stop_condition": "住宅密度不足、竞品密集、或小区主出入口动线不经过",
        "score_explanation": "社区零售核心看人口密度和动线位置。评分受住宅数量主导。",
    }


def _snapshot_pharmacy(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    hospital_500 = _int(s5.get("hospitals", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))

    if dc_1000 == 0:
        competitor_note = (
            "地图 POI 未检出同类药店。但医院药房、社区卫生中心药房、线上药店"
            "（京东健康/阿里健康）不在 POI 收录范围，需现场走访确认。"
        )
    else:
        competitor_note = f"1000m 同类药店 {dc_1000} 家。"

    if hospital_500 >= 1:
        competitor_note += f" 500m 内 {hospital_500} 家医院/诊所可作为处方锚点。"

    return {
        "model_type": "pharmacy",
        "core_logic": "药店做社区刚需生意，核心看常住人口基数、年龄结构、医院/诊所锚点和医保资质。线上药店分流不可忽视。",
        "competitor_note": competitor_note,
        "must_verify": [
            "统计周边 500m 常住人口和年龄结构",
            "确认 500m 内医院/诊所数量和处方外流情况",
            "核验药品经营许可、执业药师和 GSP 认证条件",
            "评估线上药店对该区域的配送覆盖强度",
            "走访同类药店了解日均客流和客单价",
        ],
        "fit_condition": "周边常住人口 >= 5000、有医院/诊所锚点、医保资质可办理、竞品不超过 2 家",
        "stop_condition": "常住人口不足、已有 3+ 家同类且客流一般、或线上药店已充分覆盖",
        "score_explanation": "药店评分重点看人口基数和医院/诊所锚点，0 竞品不等于优势。",
    }


def _snapshot_retail_shopping(real_data, business_type, brand_name, store_size):
    return {
        "model_type": "retail_shopping",
        "core_logic": "目的性零售依赖商圈集聚效应和交通可达性。孤立选址风险极高。",
        "competitor_note": "对于服装/数码等品类，同类聚集（扎堆）是正向信号，不是负面竞争。",
        "must_verify": [
            "确认所在商圈/商业体的整体客流和租金水平",
            "走访同品类门店了解坪效和客单价",
            "评估周边交通可达性和停车条件",
            "确认电商对该品类的替代程度",
        ],
        "fit_condition": "位于成熟商圈内、交通便利、同类聚集形成逛街效应",
        "stop_condition": "孤立选址、商圈客流不足、租售比过高",
        "score_explanation": "目的性零售评分重点看商圈成熟度和同类聚集，不适用人口密度简单模型。",
    }


def _snapshot_service_beauty(real_data, business_type, brand_name, store_size, category=""):
    dc_1000 = _int((real_data or {}).get("direct_competitors_1000m", 0))
    if dc_1000 == 0:
        competitor_note = (
            "地图POI未发现同类门店。美容/宠物/健身等生活服务业态中，"
            "部分小型工作室可能未被POI收录，需现场走访确认。"
        )
    else:
        competitor_note = ""

    is_pet = _is_pet_business(business_type, brand_name, category)

    must_verify = [
        "走访周边中高档住宅小区评估消费力",
        "观察同类门店客流和会员活跃度",
        "询价周边商铺租金",
        "确认停车条件和门头可见度",
    ]
    if is_pet:
        must_verify.extend([
            "确认物业是否允许宠物业态经营（噪音/气味/排风硬约束）",
            "评估邻里投诉和物业限制风险",
        ])

    stop_condition = "周边消费力不足、竞品密集、或租金占比超预期"
    if is_pet:
        stop_condition += "、物业不允许宠物业态、或噪音/气味/排风条件不满足"

    return {
        "model_type": "service_beauty",
        "core_logic": "美业/宠物/健身做3公里内会员储值生意，核心看周边中高消费力住宅密度。",
        "competitor_note": competitor_note,
        "must_verify": must_verify,
        "fit_condition": "周边中高消费力住宅充足、停车方便、竞品不超过2家、租金可控",
        "stop_condition": stop_condition,
        "score_explanation": "美业/健身评分重点看周边消费力，人口数量不等同于消费匹配。",
    }


def _snapshot_service_basic(real_data, business_type, brand_name, store_size):
    return {
        "model_type": "service_basic",
        "core_logic": "洗衣/诊所/家政做社区刚需服务，核心看周边人口密度和社区成熟度。",
        "competitor_note": "",
        "must_verify": [
            "评估周边社区人口规模和消费习惯",
            "确认同类服务的覆盖范围和服务能力",
            "核验诊所/家政等执照和合规要求",
        ],
        "fit_condition": "社区成熟、人口密度足够、同类服务未饱和",
        "stop_condition": "社区人口不足、已有成熟服务商覆盖、合规门槛高",
        "score_explanation": "社区基础服务评分重在看社区人口和需求饱和度。",
    }


def _snapshot_hotel(real_data, business_type, brand_name, store_size):
    return {
        "model_type": "hotel",
        "core_logic": "酒店依赖交通枢纽/商务区/景区客流，核心看位置可见度和OTA渠道能力。",
        "competitor_note": "",
        "must_verify": [
            "确认周边交通枢纽、商务区、景区的实际客流量",
            "走访同档次酒店了解入住率和ADR",
            "评估酒店选址的可见度和可达性",
            "确认OTA平台的竞争格局",
        ],
        "fit_condition": "位于交通枢纽/商务区/景区核心圈、同档次竞品不过度饱和",
        "stop_condition": "位置偏僻、客源不足、同档次竞品严重过剩",
        "score_explanation": "酒店评分重点看交通枢纽距离和商圈成熟度，人口密度权重低。",
    }


def _snapshot_entertainment(real_data, business_type, brand_name, store_size):
    return {
        "model_type": "entertainment",
        "core_logic": "夜经济/娱乐业态依赖年轻客群聚集效应和深夜可达性。隔音/消防是红线。",
        "competitor_note": "",
        "must_verify": [
            "观察周末/节假日夜间客流量",
            "确认深夜公共交通/停车条件",
            "核验隔音/消防/环保/治安要求",
            "评估周边居民投诉风险",
        ],
        "fit_condition": "位于商圈/大学城/交通节点、深夜可达、合规条件满足",
        "stop_condition": "靠近高密度住宅<100m、深夜交通不便、合规条件不满足",
        "score_explanation": "夜经济评分重点看年轻客群密度和深夜可达性，不适用常规人口模型。",
    }


def _snapshot_generic(real_data, business_type, brand_name, store_size):
    return {
        "model_type": "generic",
        "core_logic": "通用商业选址评估。建议结合具体业态做针对性的现场核验。",
        "competitor_note": "",
        "must_verify": [
            "现场实测目标客群流量",
            "走访相邻商户了解租金和经营状况",
            "观察周边同类门店经营状态",
            "检查门头可见度和交通动线",
            "确认合规资质和经营许可要求",
        ],
        "fit_condition": "目标客群实测达标、租金可控、业态匹配周边需求",
        "stop_condition": "客群实测不足、租金占比过高、业态与周边需求不匹配",
        "score_explanation": "通用模型评分，需结合具体业态特点做更精细判断。",
    }


# ═══════════════════════════════════════════════════════════
# 行业口径说明
# ═══════════════════════════════════════════════════════════

def build_business_caliber_explanation(real_data: dict, business_type: str,
                                        brand_name: str = "",
                                        category: str = "") -> str:
    """生成该业态的竞品口径说明。"""
    family = classify_business_model_family(business_type, brand_name, category)

    base = (
        "直接竞品：与您的门店品类相同、直接争夺同一客群的周边门店。"
        "替代消费：品类不同但可能分流顾客消费预算的周边门店。"
        "客流锚点：本身不是竞品但能带来客流的设施。"
    )

    family_notes = {
        "education_childcare": (
            "托管/小饭桌/作业辅导的竞品包括各类学生托管、课后服务。"
            "注意：地图POI对小饭桌、家庭式托管的收录率较低，"
            "0家竞品不表示没有暗竞品，必须现场走访确认。"
        ),
        "education_training": (
            "教育培训竞品包括各类学科辅导、艺术培训、早教等。"
            "部分小型培训班可能未被POI收录。"
        ),
        "snack_fast_food": (
            "小吃快餐直接竞品为同品类门店。替代消费包括便利店鲜食、超市熟食、"
            "以及邻近品类的鸭脖/卤味/炸鸡/汉堡等。"
            "0竞品不等于市场空白——需判断是否因低客流导致无供给。"
        ),
        "food_service": (
            "正餐/火锅直接竞品为同品类门店。替代消费包括其他菜系中餐、"
            "高端快餐等可能分流聚餐预算的业态。"
        ),
        "beverage_dessert": (
            "茶饮/咖啡直接竞品为同品类门店。替代消费包括便利店饮料、甜品店、冰淇淋店。"
        ),
        "retail_convenience": (
            "便利店/超市直接竞品为同类型零售门店。"
            "替代消费包括餐饮/快餐对鲜食品类的分流。"
        ),
        "retail_shopping": (
            "服装/数码等目的性零售中，同类聚集（扎堆）是正向信号，"
            "不是负面竞争。核心竞争来自电商和商圈外同类门店。"
        ),
        "service_beauty": (
            "美容/宠物/健身的竞品为同品类门店。"
            "注意：小型工作室/个人工作室可能未被POI收录。"
        ),
        "service_basic": (
            "洗衣/诊所/家政为社区刚需服务，竞品为同类型门店。"
        ),
        "hotel": (
            "酒店直接竞品为同档次住宿设施。替代消费包括民宿/公寓/日租房。"
        ),
        "entertainment": (
            "酒吧/KTV/剧本杀等直接竞品为同品类门店。"
            "注意：该类业态对隔音/消防/环保有特殊要求。"
        ),
        "generic": (
            "本报告基于高德地图POI数据采集和系统规则分析。数据可能存在更新延迟。"
            "建议结合现场核验确认实际经营状态。"
        ),
    }

    note = family_notes.get(family, family_notes["generic"])
    return f"{base} {note} 本报告基于高德地图POI数据采集和系统规则分析，数据可能存在更新延迟。"


# ═══════════════════════════════════════════════════════════
# 现场核验清单（按业态）
# ═══════════════════════════════════════════════════════════

def build_business_field_checklist(real_data: dict, business_type: str,
                                    brand_name: str = "",
                                    store_size: int = 0,
                                    category: str = "") -> list:
    """按业态生成结构化现场核验清单（对象数组）。"""
    family = classify_business_model_family(business_type, brand_name, category)
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    school_500 = _int(s5.get("schools", 0))
    dc_200 = _int(r.get("direct_competitors_200m", 0))

    handlers = {
        "education_childcare": _checklist_education_childcare,
        "education_training": _checklist_education_training,
        "snack_fast_food": _checklist_snack_fast_food,
        "food_service": _checklist_food_service,
        "beverage_dessert": _checklist_beverage_dessert,
        "retail_convenience": _checklist_retail_convenience,
        "pharmacy": _checklist_pharmacy,
        "service_beauty": _checklist_service_beauty,
        "generic": _checklist_generic,
    }
    handler = handlers.get(family, _checklist_generic)
    if family == "service_beauty":
        items = handler(real_data, business_type, brand_name, store_size, category=category)
    else:
        items = handler(real_data, business_type, brand_name, store_size)
    return [
        {
            "title": t.get("title", ""),
            "time_window": t.get("time_window", ""),
            "action": t.get("action", ""),
            "record_method": t.get("record_method", []),
            "risk_type": t.get("risk_type", ""),
            "pass_hint": t.get("pass_hint", ""),
            "eliminate_hint": t.get("eliminate_hint", ""),
        }
        for t in items
    ]


def _make_item(title, time_window, action, risk_type, pass_hint, eliminate_hint,
               record_method=None):
    return {
        "title": title, "time_window": time_window, "action": action,
        "risk_type": risk_type, "pass_hint": pass_hint,
        "eliminate_hint": eliminate_hint,
        "record_method": record_method or ["拍照", "备注"],
    }


def _checklist_education_childcare(real_data, business_type, brand_name, store_size):
    items = [
        _make_item(
            "从周边小学步行至门店确认路线安全性",
            "工作日下午15:00-17:00",
            "沿周边小学主要出入口步行至门店，确认路线是否有人行道、是否需过主干道、是否有安全隐患",
            "动线不安全",
            "步行路线安全、人行道完整、无需横穿主干道",
            "需横穿无信号灯的快速路或主干道，或步行距离超过10分钟",
        ),
        _make_item(
            "观察放学时段学生和家长动线",
            "工作日15:30-17:00",
            "在校门口和门店之间观察学生和家长的放学动线，确认是否自然经过门店",
            "学区客群导入不足",
            "放学动线经过门店且家长有明显等待空间",
            "学生和家长动线完全不经过门店且无可调整的引流方式",
        ),
        _make_item(
            "核验家长接送临时停车条件",
            "工作日15:30-17:00",
            "观察门店附近是否有临时停车位/停车区，家长接孩子时是否方便停车等候",
            "家长接送不便",
            "门店附近有临时停车条件或停车设施，家长可方便等候",
            "无任何停车条件且道路狭窄，家长只能即停即走或无法停车",
        ),
        _make_item(
            "走访周边托管/小饭桌暗竞品",
            "工作日下午或周末",
            "走访周边小区门口、学校门口，询问是否有家庭式托管/小饭桌/作业辅导",
            "暗竞品未被收录",
            "未发现未被POI收录的托管暗竞品",
            "发现多家家庭式托管/小饭桌已稳定运营且有固定生源",
        ),
        _make_item(
            "核验消防/食品/托管合规条件",
            "工作日白天",
            "确认门店是否符合消防双通道、食品经营许可、托管备案等合规要求",
            "合规不达标",
            "消防/食品/托管合规条件满足，可办理相关资质",
            "消防或食品条件不满足且无法改造，或当地托管备案门槛过高",
        ),
        _make_item(
            "评估空间分区和硬件条件",
            "任意时段",
            "确认室内面积是否足够分区：活动区、就餐区、作业区、午休区、卫生间",
            "空间条件不足",
            "空间可满足3+功能分区且通风采光良好",
            "空间过于局促无法分区，或无独立卫生间",
        ),
        _make_item(
            "访谈周边家长托管需求",
            "工作日放学时段15:30-17:00",
            "在校门口访谈3-5位低年级学生家长，了解托管需求、预算和选择标准",
            "需求不足",
            "多数家长表示有托管需求且对现有托管不满意",
            "多数家长表示不需要托管或已有固定托管且不考虑更换",
        ),
        _make_item(
            "走访相邻商户了解租金和物业条件",
            "工作日白天",
            "询问3-5家相邻商户实际租金、物业费、转让费",
            "租金过高",
            "租金在预算范围内且占比合理",
            "月租金超过预估月营收20%且无议价空间",
        ),
    ]
    return items[:8]


def _checklist_education_training(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    school_500 = _int(s5.get("schools", 0))
    res_500 = _int(s5.get("residential", 0))
    items = [
        _make_item(
            "观察工作日放学后学生/家长流量",
            "工作日15:30-17:00",
            "观察校门口和门店周边的学生和家长流量",
            "客群不足",
            "放学后有明显学生和家长流量经过",
            "放学后流量稀疏且学生年龄与培训项目不匹配",
        ),
        _make_item(
            "走访同类培训机构",
            "周末白天",
            "走访500m内同类培训机构，了解满班率、客单价和续费率",
            "竞品饱和",
            "同类培训满班率高，说明需求旺盛且仍有空间",
            "同类培训空位多、客单价持续走低、转租转让频繁",
        ),
        _make_item(
            "核验办学资质和消防要求",
            "工作日",
            "确认当地教育培训办学许可、消防验收和营业执照要求",
            "合规门槛高",
            "资质可正常办理",
            "办学许可无法办理或消防不达标",
        ),
        _make_item(
            "评估停车和公共交通条件",
            "任意时段",
            "确认门店附近是否有停车位、公交站或地铁站",
            "交通不便",
            "停车和公交均可满足家长接送需求",
            "无停车条件且公共交通不便",
        ),
        _make_item(
            "询价周边商铺租金",
            "工作日白天",
            "询问3-5家相邻商户实际租金和转让费",
            "租金过高",
            "实际租金在预算范围内",
            "月租金超过预估月营收20%",
        ),
    ]
    if school_500 >= 3 and res_500 < 5:
        items.append(_make_item(
            "走访周边小区评估家庭消费力",
            "周末白天或工作日傍晚",
            "走访周边小区，观察车辆档次、房价水平、居民消费习惯，确认家庭消费力与课程客单价匹配度",
            "消费力不匹配",
            "周边以中高消费力家庭为主，客单价在承受范围内",
            "周边以老旧小区/城中村为主，家庭消费力明显低于课程定价区间",
        ))
    return items[:8]


def _checklist_snack_fast_food(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    school_500 = _int(s5.get("schools", 0))
    dc_200 = _int(r.get("direct_competitors_200m", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))

    # P2: 学校午休动线仅按 K12 触发，全大学/培训不得触发
    sab = compute_school_anchor_breakdown(r)
    bd = (sab or {}).get("breakdown", {}) or {}
    k12 = bd.get("elementary", 0) + bd.get("middle_high", 0) + bd.get("kindergarten", 0)
    _use_k12 = (sab.get("total", 0) > 0 and bd.get("unknown", 0) < sab.get("total", 0))
    _trigger_school = k12 if _use_k12 else school_500

    items = [
        _make_item(
            "实测午高峰门前人流",
            "工作日11:30-13:00",
            "在门店固定位置观察15分钟，记录经过正面动线的目标客群人数",
            "客流不足",
            "午高峰门前有稳定目标客群经过",
            "15分钟内目标客群不足10人",
        ),
        _make_item(
            "观察1000米内同类门店午高峰经营状态",
            "工作日11:30-13:00",
            f"走访 {dc_1000} 家同类门店，观察上座率、排队情况和出餐速度" if dc_1000 > 0 else "走访最近2-3家同类餐饮门店，观察午高峰经营状态",
            "远场竞争激烈",
            "同类门店午高峰普遍满座，说明品类需求旺盛",
            "同类门店午高峰仍有空位较多，说明区域内该品类需求可能饱和",
        ),
        _make_item(
            "询价相邻商户真实租金",
            "工作日白天",
            "询问3-5家相邻商户实际租金、转让费、物业费",
            "租金过高",
            "实际租金在预算范围内且占比合理",
            "月租金超过预估月营收20%且无议价空间",
        ),
        _make_item(
            "检查外卖骑手停车和取餐便利度",
            "午高峰11:30-13:00",
            "观察门店附近是否有外卖骑手停车区，取餐是否需要上楼或绕路",
            "外卖运营受限",
            "骑手可便利停靠且取餐流程顺畅",
            "骑手无法停车且周边无任何便利取餐条件",
        ),
        _make_item(
            "观察门店门头可见度和道路动线",
            "任意时段",
            "从道路对侧、50米外观察门头是否清晰可见，是否有树木/广告牌遮挡",
            "门头曝光不足",
            "门头在50米外清晰可见，无遮挡",
            "门头被树木/广告牌/建筑完全遮挡且无法改善",
        ),
    ]
    if _trigger_school >= 2:
        items.insert(1, _make_item(
            "确认学校午休放学动线和学生餐饮习惯",
            "工作日11:30-12:30",
            "观察学校门口到门店的动线，确认学生午间外出就餐的流向和规模（仅限中小学，不含大学/培训机构）",
            "学校客流落空",
            "学生午间外出就餐动线经过门店",
            "学校封闭管理学生不得外出，或动线完全不经过门店",
        ))
    return items[:8]


def _checklist_food_service(real_data, business_type, brand_name, store_size):
    return [
        _make_item("实测晚高峰门前客流", "工作日18:00-20:00",
                   "在门店固定位置观察15分钟，记录经过的目标客群", "客流不足",
                   "晚高峰有稳定目标客群经过", "目标客群明显不足"),
        _make_item("检查停车便利度", "晚高峰18:00-20:00",
                   "确认停车场距离和可用车位数量", "停车不便",
                   "步行3分钟内有充足停车位", "附近无停车场且路边无法停车"),
        _make_item("走访同品类门店了解翻台率和客单价", "晚高峰18:00-20:00",
                   "走访同类门店，观察翻台率和客单价", "竞品饱和",
                   "同类门店上座率高且有一定差异化空间", "竞品上座率低且客单价持续走低"),
        _make_item("询价相邻商户租金", "工作日白天",
                   "询问3-5家相邻商户实际租金", "租金过高",
                   "租金在预算范围内", "月租金超过预估月营收20%"),
        _make_item("核验排烟/消防/电力设施", "任意时段",
                   "确认排烟系统安装条件、消防验收和电力容量", "硬件不达标",
                   "排烟/消防/电力条件满足", "无法安装排烟或不满足消防要求"),
    ]


def _checklist_beverage_dessert(real_data, business_type, brand_name, store_size):
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    school_500 = _int(s5.get("schools", 0))
    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))

    items = [
        _make_item("全天观察门前步行人流量", "工作日8:00-20:00",
                   "在门店固定位置分段观察步行人流", "客流不足",
                   "全天步行人流充足", "步行人流稀疏"),
        _make_item("观察地铁/公交出口到门店动线", "工作日早晚高峰",
                   "从最近地铁/公交站步行至门店，检查动线是否通畅", "动线不畅",
                   "通勤人群自然经过门店", "动线偏离通勤主流方向"),
        _make_item("走访同类门店了解日均销量", "任意时段",
                   "走访同类茶饮/咖啡门店了解日均杯量和客单价", "竞品势能强",
                   "同类门店销量好且仍有差异化空间", "品牌势能强的竞品已充分覆盖"),
        _make_item("检查外卖平台竞品表现", "任意时段",
                   "查看外卖平台周边竞品的月销量和评分", "外卖竞争激烈",
                   "外卖平台同品类竞争适中", "头部品牌月销远超一般门店可达到的水平"),
        _make_item("询价相邻商户租金", "工作日白天",
                   "询问相邻商户实际租金", "租金过高",
                   "租金在预算范围内", "月租金占比过高"),
    ]
    if school_500 >= 3 and res_500 < 5 and office_500 < 5:
        items.append(_make_item(
            "核验校门口到门店放学时段步行动线",
            "工作日15:30-17:00",
            "从最近学校校门口步行至门店，确认放学时段学生动线是否自然经过门店",
            "学校客流落空",
            "放学动线经过门店且门店在50m内可见",
            "学校动线完全不经过门店且门店不在校门口可视范围内",
        ))
    return items


def _checklist_retail_convenience(real_data, business_type, brand_name, store_size):
    return [
        _make_item("统计周边500m内住宅小区和户数", "任意时段",
                   "走访周边小区确认实际入住率和住户数量", "人口不足",
                   "周边500m内有5+住宅小区且入住率高", "住宅小区不足3个或入住率低"),
        _make_item("确认小区主出入口到门店动线", "任意时段",
                   "观察小区主出入口到门店的步行路线", "动线不佳",
                   "门店位于小区主出入口步行动线上", "动线完全偏离且无可调整方式"),
        _make_item("走访同类门店了解日均客流", "工作日晚上和周末",
                   "走访同类便利店/超市了解日均客流和客单价", "竞品饱和",
                   "同类门店客流充足且仍有空间", "已有2家以上同类门店且客流一般"),
        _make_item("询价相邻商户租金", "工作日白天",
                   "询问相邻商户实际租金", "租金过高",
                   "租金可控", "月租金占比过高"),
    ]


def _checklist_pharmacy(real_data, business_type, brand_name, store_size):
    return [
        _make_item("统计周边常住人口和年龄结构", "任意时段",
                   "走访周边小区了解常住人口、年龄分布和慢性病用药需求", "人口不足",
                   "周边常住人口 >= 5000 且老龄化比例较高", "常住人口不足 3000 且以年轻人为主"),
        _make_item("确认医院/诊所锚点", "工作日白天",
                   "走访 500m 内医院/诊所，确认处方外流情况和患者购药动线", "锚点缺失",
                   "500m 内有医院或社区诊所可导出处方客流", "500m 内无任何医疗机构"),
        _make_item("核验药品经营许可和执业药师", "工作日",
                   "确认 GSP 认证、药品经营许可和执业药师注册条件", "合规不达标",
                   "证照和药师条件可满足", "许可或药师无法到位"),
        _make_item("走访同类药店了解客流", "工作日全天",
                   "走访同类药店了解日均客流、客单价和医保定点情况", "竞品饱和",
                   "同类药店客流充足且仍有空间", "已有 3+ 家同类且客流一般"),
        _make_item("询价相邻商户租金", "工作日白天",
                   "询问相邻商户实际租金", "租金过高",
                   "租金在预算范围内", "月租金占比过高"),
    ]


def _checklist_service_beauty(real_data, business_type, brand_name, store_size, category=""):
    is_pet = _is_pet_business(business_type, brand_name, category)
    items = [
        _make_item("评估周边社区消费力", "工作日晚上和周末",
                   "走访周边小区，观察车辆档次、居民消费习惯", "消费力不足",
                   "周边以中高档小区为主，消费力匹配", "周边以老旧小区/城中村为主，消费力不匹配"),
        _make_item("走访同类门店", "周末白天",
                   "走访同类美容/美发/健身门店，了解客流和客单价", "竞品饱和",
                   "同类门店客流充足且仍有差异空间", "已有 3 家以上同类门店且同质化严重"),
        _make_item("检查停车条件和门头可见度", "任意时段",
                   "确认门店附近停车条件和门头曝光度", "展示条件差",
                   "停车方便且门头清晰可见", "无停车条件且门头严重遮挡"),
        _make_item("询价相邻商户租金", "工作日白天",
                   "询问相邻商户实际租金", "租金过高",
                   "租金在预算范围内", "月租金占比过高"),
    ]
    if is_pet:
        items.append(_make_item(
            "核验物业宠物业态许可与噪音/气味约束",
            "工作日白天",
            "向物业确认是否允许宠物店经营，检查排风/隔音/气味处理条件，了解邻里投诉历史",
            "物业限制",
            "物业允许宠物品类、排风/隔音/气味条件满足、无历史投诉",
            "物业不允许宠物业态，或排风/隔音/气味条件无法满足",
        ))
    return items


def _checklist_generic(real_data, business_type, brand_name, store_size):
    return [
        _make_item("现场实测目标客群流量", "选择目标客群最活跃的时段",
                   "在门店固定位置观察15分钟，记录经过目标客群人数", "客流不足",
                   "目标客群实测达标", "目标客群明显不足"),
        _make_item("走访相邻商户了解租金", "工作日白天",
                   "询问3-5家相邻商户实际租金、转让费", "租金过高",
                   "租金在预算范围内", "月租金超过预估月营收20%"),
        _make_item("观察周边同类门店经营状态", "目标客群活跃时段",
                   "走访同类门店观察上座率/客流/客单价", "竞品饱和",
                   "同类门店经营良好且有差异化空间", "同类门店多数经营不佳"),
        _make_item("检查门头可见度和道路动线", "任意时段",
                   "观察门头是否清晰可见，通行动线是否顺畅", "展示条件差",
                   "门头清晰、动线顺畅", "门头严重遮挡或动线不畅"),
        _make_item("核验合规资质", "工作日",
                   "确认经营所需的各类证照和合规条件", "合规不达标",
                   "证照可正常办理", "关键证照无法办理"),
    ]
