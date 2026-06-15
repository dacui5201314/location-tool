"""
位置基本面服务 — 确定性函数，不依赖 LLM。
只看 real_data，不看业态。同一地址不同业态输出一致的基本面。
P1: 替代旧的 compute_location_fundamentals()，增加 school_anchor_breakdown。
"""
import re as _re


def _int(v, default=0):
    try: return int(v)
    except: return default


# 餐饮供给不作为通用优势的族群
_DINING_NOT_ADVANTAGE = {
    "education_childcare", "education_training",
    "service_beauty", "service_basic", "hotel",
}

# 学校锚点细分关键词
_ELEMENTARY_KW = ["小学", "实验学校", "中心小学", "第一小学", "第二小学", "第三小学",
                  "第四小学", "第五小学", "第六小学", "外国语学校"]
_KINDERGARTEN_KW = ["幼儿园", "幼稚园", "托儿所", "保育院"]
_MIDDLE_HIGH_KW = ["中学", "高中", "初中", "完全中学", "高级中学", "初级中学",
                   "第一中学", "第二中学", "第三中学", "第四中学", "第五中学", "第六中学", "附属中学"]
_UNIVERSITY_KW = ["大学", "学院", "职业技术学院", "高等专科", "师范", "理工"]
_TRAINING_KW = ["培训", "教育", "补习", "辅导", "琴行", "画室", "托管", "早教"]


def _classify_school(name: str) -> str:
    """按名称关键词轻量分类学校类型。不依赖 LLM，不做复杂归并。"""
    n = (name or "").strip()
    if not n:
        return "unknown"
    for kw in _ELEMENTARY_KW:
        if kw in n:
            return "elementary"
    for kw in _KINDERGARTEN_KW:
        if kw in n:
            return "kindergarten"
    for kw in _UNIVERSITY_KW:
        if kw in n:
            return "university"
    for kw in _MIDDLE_HIGH_KW:
        if kw in n:
            return "middle_high"
    for kw in _TRAINING_KW:
        if kw in n:
            return "training"
    return "unknown"


def compute_school_anchor_breakdown(real_data: dict) -> dict:
    """从 poi_lists.schools 或附近学校列表做轻量学校类型细分。"""
    schools_list = []
    poi_lists = real_data.get("poi_lists", {}) or {}
    if "schools" in poi_lists:
        schools_list = poi_lists.get("schools", []) or []
    if not schools_list:
        # 尝试从 stats 和 direct_competitor_list 中的学校提取
        stats = real_data.get("stats_500m", {}) or {}
        if _int(stats.get("schools", 0)) == 0:
            return {"total": 0, "breakdown": {}, "note": "无学校 POI 数据"}

    breakdown = {"elementary": 0, "kindergarten": 0, "middle_high": 0,
                 "university": 0, "training": 0, "unknown": 0}
    total = 0

    if schools_list and len(schools_list) > 0:
        for entry in schools_list:
            name = (entry.get("name") or "").strip()
            if not name:
                continue
            cat = _classify_school(name)
            breakdown[cat] = breakdown.get(cat, 0) + 1
            total += 1
    else:
        # 只有 stats 数量，无法细分
        total = _int((real_data.get("stats_500m", {}) or {}).get("schools", 0))
        breakdown["unknown"] = total

    return {
        "total": total,
        "breakdown": breakdown,
        "note": ("小学/幼儿园/中学/大学/培训机构分类基于名称关键词，"
                 "同一大学多个校区节点可能被计为多个。")
    }


def compute_location_profile(real_data: dict) -> dict:
    """从 real_data 计算与业态无关的位置基本面。"""
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

    # ── 位置类型 ──
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
    elif school_500 >= 3 and bus_500 <= 3 and subway_500 == 0 and subway_applicable:
        location_type = "学区弱交通社区型"
    elif school_500 >= 3 and res_500 >= 5:
        location_type = "学区社区混合型"
    elif res_500 < 5 and office_500 < 5 and school_500 < 3:
        location_type = "弱交通住宅区 / 低密度边缘"
    elif res_500 >= 10:
        location_type = "社区底商 / 居住配套"
    else:
        location_type = "综合混合型"

    # ── 标签 ──
    if res_500 < 5 and office_500 < 3 and school_500 < 3:
        label = "低密度边缘位置"
    elif school_500 >= 3 and bus_500 <= 3 and subway_500 == 0 and subway_applicable:
        label = "学区弱交通社区型"
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

    # ── core_anchors ──
    anchors = []
    if school_500 >= 3:
        anchors.append("学校")
    if res_500 >= 10:
        anchors.append("住宅")
    if office_500 >= 10:
        anchors.append("办公")
    if shopping_500 >= 3:
        anchors.append("商业/商场")
    if subway_500 >= 1:
        anchors.append("地铁")
    if bus_500 >= 5:
        anchors.append("公交")
    if not anchors:
        anchors.append("弱基础设施")

    # ── strengths (通用，不含餐饮供给) ──
    strengths = []
    if school_500 >= 5:
        strengths.append(f"500m 内 {school_500} 所学校，学区客群基础较好")
    if res_500 >= 20:
        strengths.append(f"500m 内 {res_500} 个住宅小区，居住密度较高")
    if office_500 >= 10:
        strengths.append(f"500m 内 {office_500} 栋办公楼，办公人群可支撑午间消费")
    if shopping_500 >= 3:
        strengths.append(f"500m 内 {shopping_500} 个商业体，商业氛围较好")
    if subway_500 >= 1:
        strengths.append(f"500m 内有 {subway_500} 个地铁站，公共交通便捷")
    if bus_500 >= 5:
        strengths.append(f"500m 内 {bus_500} 条公交线路，地面交通覆盖较好")
    if not strengths:
        strengths.append("该位置具备基础商业条件，需线下核验补充判断")

    # ── weaknesses ──
    weaknesses = []
    if res_500 < 5:
        weaknesses.append(f"500m 内仅 {res_500} 个住宅小区，常住人口基础偏弱")
    if office_500 < 3 and school_500 < 3:
        weaknesses.append("周边办公和学校供给不足，全天客流可能偏低")
    if shopping_500 == 0:
        weaknesses.append("500m 内无商业体，商业配套缺失")
    if subway_applicable and subway_500 == 0 and bus_500 <= 2:
        weaknesses.append("公共交通条件较弱，外部导入客流有限")
    if parking_500 == 0:
        weaknesses.append("500m 内无停车设施，自驾可达性受限")
    if not weaknesses:
        weaknesses.append("部分经营数据需线下核验后确认")

    # ── suitable / cautious families ──
    suitable = []
    cautious = []
    if school_500 >= 3:
        suitable.append("education_childcare")
        suitable.append("snack_fast_food")
    if office_500 >= 10:
        suitable.append("snack_fast_food")
        suitable.append("beverage_dessert")
    if res_500 >= 20:
        suitable.append("retail_convenience")
    if shopping_500 >= 3:
        suitable.append("food_service")
        suitable.append("beverage_dessert")
    if office_500 < 5 and school_500 < 3:
        cautious.append("food_service")
        cautious.append("entertainment")
    if bus_500 <= 2 and not (subway_applicable and subway_500 >= 1):
        cautious.append("hotel")
    if res_500 < 10 and school_500 < 3:
        cautious.append("education_childcare")
        cautious.append("education_training")

    # ── evidence ──
    evidence = {
        "schools_500m": school_500,
        "residential_500m": res_500,
        "office_500m": office_500,
        "bus_500m": bus_500,
        "subway_500m": subway_500,
        "restaurants_1000m": restaurants_1k,
        "shopping_500m": shopping_500,
        "parking_500m": parking_500,
        "school_anchor_breakdown": compute_school_anchor_breakdown(r),
    }

    # ── summary ──
    summary = (
        f"该位置为 {location_type}：500m 内 {res_500} 个住宅小区、"
        f"{office_500} 栋办公楼、{school_500} 所学校。"
        f"1000m 内 {restaurants_1k} 家餐饮门店。"
    )

    return {
        "primary_type": location_type,
        "secondary_tags": anchors[:4],
        "label": label,
        "summary": summary,
        "core_anchors": anchors[:4],
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "suitable_business_families": list(set(suitable))[:6],
        "cautious_business_families": list(set(cautious))[:6],
        "evidence": evidence,
    }


def get_dining_not_advantage_families() -> set:
    """返回不应将餐饮供给作为优势的族群集合。"""
    return set(_DINING_NOT_ADVANTAGE)
