"""
兜底报告生成器 — 纯函数，不依赖 LLM/AMap/FastAPI。
LLM 报告事实校验失败 + retry 仍失败时，用 real_data 生成保守版报告。
只引用真实数量和泛化类别，不写任何具体 POI 名称。
文案严格避免 P0 语境关键词和决策性表述。
P1: 按业态切换生意模型模板，不再所有业态共用一套逻辑。
"""
import json as _json
from services.business_model_service import (
    classify_business_model_family,
    compute_location_fundamentals,
    compute_business_model_snapshot,
    build_business_field_checklist,
    build_business_caliber_explanation,
)


# ═══════════════════════════════════════════════
# 简版 action_plan 生成（从 field_checklist 提取 title）
# ═══════════════════════════════════════════════
def _simple_action_plan(field_checklist, business_type="", brand_name=""):
    """从 field_checklist 的 title 生成简版经营建议。"""
    if not field_checklist or not isinstance(field_checklist, list):
        family = classify_business_model_family(business_type, brand_name)
        return _default_action_plan(family)
    items = []
    for item in field_checklist[:5]:
        if isinstance(item, dict) and item.get("title"):
            items.append(item["title"])
        elif isinstance(item, str):
            items.append(item)
    if len(items) < 3:
        family = classify_business_model_family(business_type, brand_name)
        return _default_action_plan(family)
    return items


def _default_action_plan(family):
    if family == "education_childcare":
        return [
            "确认周边小学距离和放学动线安全性",
            "走访周边托管/小饭桌暗竞品",
            "核验消防/食品/托管合规和空间分区",
            "访谈周边低年级家长托管需求",
            "走访相邻商户了解租金后制定财务模型",
        ]
    if family == "snack_fast_food":
        return [
            "实测午高峰门前客流和动线",
            "走访相邻商户了解真实租金",
            "观察同类门店午高峰经营状态",
            "检查外卖骑手停车和取餐便利度",
            "检查门店门头可见度和道路动线",
        ]
    return [
        "安排时段现场实测目标客群流量",
        "走访相邻商户了解真实租金和经营状况",
        "观察同类门店经营状态和客群特征",
        "检查门店门头可见度和道路动线",
        "线下询价确认租金后制定财务模型",
    ]


def _int(v, default=0):
    try: return int(v)
    except: return default


def build_fallback_report(real_data: dict, address: str = "",
                          business_type: str = "", brand_name: str = "",
                          store_size: int = 0) -> dict:
    """从 real_data 生成纯数据兜底报告。"""

    s2 = real_data.get("stats_200m", {}) or {}
    s5 = real_data.get("stats_500m", {}) or {}
    s10 = real_data.get("stats_1000m", {}) or {}

    dc_200 = _int(real_data.get("direct_competitors_200m", 0))
    dc_500 = _int(real_data.get("direct_competitors_500m", 0))
    dc_1000 = _int(real_data.get("direct_competitors_1000m", 0))
    sub_200 = _int(real_data.get("substitute_competitors_200m", 0))
    sub_500 = _int(real_data.get("substitute_competitors_500m", 0))
    sub_1000 = _int(real_data.get("substitute_competitors_1000m", 0))
    anc_1000 = _int(real_data.get("traffic_anchors_1000m", 0))

    res_500 = _int(s5.get("residential", 0))
    school_500 = _int(s5.get("schools", 0))
    office_500 = _int(s5.get("office", 0))
    hospital_500 = _int(s5.get("hospitals", 0))
    subway_500 = _int(s5.get("subway", 0))
    bus_500 = _int(s5.get("bus", 0))
    parking_500 = _int(s5.get("parking", 0))
    shopping_500 = _int(s5.get("shopping", 0))
    restaurants_1k = _int(s10.get("restaurants", 0))
    hotel_1000 = _int(s10.get("hotels", 0))
    subway_applicable = real_data.get("subway_applicable", True)

    # ── 场景判断（仅用于内部描述，不写入报告正文） ──
    if office_500 >= 20 and shopping_500 >= 5:
        _scene = "商务商业复合区"
    elif office_500 >= 15:
        _scene = "商务办公区"
    elif school_500 >= 8:
        _scene = "学区"
    elif res_500 >= 50:
        _scene = "高密度居住区"
    elif shopping_500 >= 8:
        _scene = "核心商圈"
    elif hotel_1000 >= 15:
        _scene = "旅游商务区"
    else:
        _scene = "综合社区"

    # ── advantages（避免"周边""同类""红利""极低"） ──
    family_adv = classify_business_model_family(business_type, brand_name)
    advantages = []
    if dc_200 <= 3:
        # P1: 小吃快餐 200m 0竞品但远场多时，不能机械写竞争压力小
        if family_adv == "snack_fast_food" and dc_200 == 0 and (dc_1000 >= 8 or restaurants_1k >= 40):
            advantages.append(
                f"200m 内同品类供给较少，但 1000m 同类门店 {dc_1000} 家、餐饮 {restaurants_1k} 家，"
                f"需核验近场空档是否由低客流导致；只有低租金小档口模型才有继续考察价值"
            )
        elif sub_200 > 0 or sub_500 > 0:
            advantages.append(f"200m 直接竞品 {dc_200} 家，直接竞品较少，但替代消费较多，需现场核验分流影响")
        else:
            advantages.append(f"200m 直接竞品 {dc_200} 家，直接竞争压力较小")
    if res_500 >= 10:
        advantages.append(f"500米半径覆盖{dh_count(res_500, '个住宅小区')}，常住人口基数充足")
    if subway_applicable and subway_500 >= 1:
        advantages.append(f"500米内有{sn_count(subway_500, '个地铁站')}，公共交通可导入客群")
    if bus_500 >= 5:
        advantages.append(f"500米内{dh_count(bus_500, '条公交线路')}，地面公交网络较密")
    if school_500 >= 3:
        advantages.append(f"500米半径内{dh_count(school_500, '所教育机构')}，学生客群稳定")
    if shopping_500 >= 3:
        advantages.append(f"500米内有{sn_count(shopping_500, '个商业体')}，可共享商业流量")
    if anc_1000 >= 5:
        advantages.append(f"1000米范围{sn_count(anc_1000, '个流量节点')}，商业活跃度较高")
    if office_500 >= 10:
        advantages.append(f"500米内{dh_count(office_500, '栋办公建筑')}，办公人群午间需求稳定")
    while len(advantages) < 2:
        advantages.append("该位置具备基础商业条件，需线下实地核验补充数据")

    # ── disadvantages（避免"分流""极""不足"） ──
    disadvantages = []
    if dc_200 > 15:
        disadvantages.append(f"200m 直接竞品 {dc_200} 家，竞争较激烈")
    if subway_applicable and subway_500 == 0 and bus_500 == 0:
        disadvantages.append("500米内无地铁和公交覆盖，出行主要依赖步行和自驾")
    elif subway_applicable and subway_500 == 0:
        disadvantages.append("500米内无地铁站，公共交通以公交为主")
    elif not subway_applicable and bus_500 == 0:
        disadvantages.append("500米内无公交线路覆盖，出行依赖步行和自驾")
    if res_500 < 5:
        disadvantages.append(f"500米内仅{sn_count(res_500, '个住宅小区')}，常住人口基数偏小")
    if parking_500 == 0:
        disadvantages.append("500米内无停车设施，自驾客群不易到达")
    if office_500 < 5 and res_500 < 10:
        disadvantages.append("500米内常住和办公人口均偏少，全天客流可能偏低")
    while len(disadvantages) < 1:
        disadvantages.append("部分数据需线下实地核验后补充")

    # ── warning（保守措辞） ──
    if dc_200 > 15:
        warning = "200米内同品类直接竞品密集"
    elif subway_applicable and subway_500 == 0 and bus_500 <= 2:
        warning = "公共交通条件较弱"
    else:
        warning = "需线下实地核验"

    # ── summary ──
    summary = (
        f"该点位选址数据摘要："
        f"直接竞品 200米{dc_200}家、500米{dc_500}家、1000米{dc_1000}家。"
        f"替代消费 200米{sub_200}家、500米{sub_500}家、1000米{sub_1000}家。"
        f"500米内{res_500}个住宅小区、{office_500}栋办公建筑、{school_500}所教育机构。"
        f"本报告为基于采集数据的保守版数据摘要，不替代现场客流、租金和商户经营状态核验。"
    )

    # ── P0.5: 同品牌分店检测（必须在 dims 之前）──
    same_brand_risk, same_brand_matches = _detect_same_brand_risk(brand_name, real_data)
    # P1: category → 使用 brand_name 作为业态细分描述（fallback 无独立 category 字段）
    _category = brand_name or ""

    # ── P0.5: 低维详情辅助函数 ──
    def _traffic_flow_detail(r500, o500, s500, sw500, b500, score):
        family = classify_business_model_family(business_type, brand_name, _category)
        pop = r500 + o500 + s500
        # 教育/托管类：不使用午晚高峰/外卖等餐饮语言
        if family == "education_childcare":
            if pop >= 10:
                txt = f"500米内住宅{r500}个、学校{s500}所，潜在生源基础一般。"
                detail = (f"500米内住宅{r500}个、学校{s500}所。"
                          f"托管客流核心看周边小学低年级学生数量和放学时段动线。"
                          f"现场需在15:30-17:00放学时段观察学生和家长动线方向。"
                          f"如动线不经过且无可调整的引流方式，则该点位客流支撑不足。评分：{score}")
            else:
                txt = f"500米内住宅{r500}个、学校{s500}所，生源基础偏弱。"
                detail = (f"500米内住宅{r500}个、学校{s500}所，生源基础偏弱。"
                          f"现场必须确认周边小学距离和放学动线，如实测学生和家长流量明显不足，"
                          f"需降低为低优先级候选点。评分：{score}")
            return txt, detail
        if family == "education_training":
            if pop >= 10:
                txt = f"500米内住宅{r500}个、学校{s500}所，潜在客源基础一般。"
                detail = (f"500米内住宅{r500}个、学校{s500}所。"
                          f"培训客流需现场核验周末和放学时段的实际到店流量。"
                          f"如客群实测明显不足，需重新评估点位。评分：{score}")
            else:
                txt = f"500米内住宅{r500}个、学校{s500}所，客源基础偏弱。"
                detail = (f"500米内住宅{r500}个、学校{s500}所，客源基础偏弱。"
                          f"现场必须实测目标客群流量，如不足需降低为低优先级候选点。评分：{score}")
            return txt, detail
        # 餐饮/零售等：保留原逻辑
        if pop >= 20:
            txt = f"500米内住宅{r500}个、办公{o500}栋、学校{s500}所，潜在客流基础较好。"
            detail = (f"500米内住宅{r500}个、办公{o500}栋、学校{s500}所，地铁{sw500}站、公交{b500}条。"
                      f"稳定客流来源较充足。现场需在11:30-13:00和18:00-20:00各计数15分钟门前目标客群经过量。"
                      f"如两个时段目标客群都明显不足，则客流推算偏高，需重新评估。评分：{score}")
        elif pop >= 8:
            txt = f"500米内住宅{r500}个、办公{o500}栋、学校{s500}所，客流基础中等。"
            detail = (f"500米内住宅{r500}个、办公{o500}栋、学校{s500}所，地铁{sw500}站、公交{b500}条。"
                      f"稳定客流来源偏中等。现场需在午晚高峰各计数15分钟门前目标客群。"
                      f"如实测客流明显偏低且外卖取餐不便，则该点位客流支撑不足。评分：{score}")
        else:
            txt = f"500米内住宅{r500}个、办公{o500}栋、学校{s500}所，稳定客流来源偏弱。"
            detail = (f"500米内住宅{r500}个、办公{o500}栋、学校{s500}所，稳定客流来源偏弱。"
                      f"现场必须实测午晚高峰门前人流，如15分钟内目标客群明显不足，"
                      f"需降低为低优先级候选点。除非门店本身有强线上引流能力（如知名品牌、外卖爆款）。评分：{score}")
        return txt, detail

    _tf_text, _tf_detail = _traffic_flow_detail(
        res_500, office_500, school_500, subway_500, bus_500,
        _clamp(25, 75, 30 + res_500 // 2 + office_500))

    def _consumer_profile_detail(r500, o500, s500, h1000, score):
        pop = r500 + o500
        if pop >= 25:
            txt = f"居住和办公人口密集，消费层次以周边居民和办公人群为主。"
            detail = (f"500米内住宅{r500}个、办公{o500}栋、学校{s500}所、1000米酒店{h1000}家。"
                      f"人口结构以居住+办公为主，消费层次中等偏上。"
                      f"现场需核验周边小区房价/租金水平和写字楼入驻企业类型，确认消费力与门店客单价匹配度。"
                      f"如周边以老旧小区和低端办公为主而门店客单价偏高，则存在消费力不匹配风险。评分：{score}")
        elif pop >= 10:
            txt = f"居住和办公人口中等，消费层次为混合型。"
            detail = (f"500米内住宅{r500}个、办公{o500}栋。人口结构混合型。"
                      f"现场核验目标客群画像：看周边门店客单价、顾客年龄段、消费时段分布。"
                      f"如目标客群与门店定位明显偏差，应降低预期。评分：{score}")
        else:
            txt = f"居住和办公人口偏少，消费人群基数偏小。"
            detail = (f"500米内住宅{r500}个、办公{o500}栋，人口基数偏小。"
                      f"现场核验目标客群是否仍可达标：看周边是否有未收录的客流来源"
                      f"（如景区、医院、交通枢纽）。如确实缺乏稳定客群来源，应降为低优先级候选点。评分：{score}")
        return txt, detail

    _cp_text, _cp_detail = _consumer_profile_detail(
        res_500, office_500, school_500, hotel_1000,
        _clamp(25, 80, 20 + office_500 + school_500))

    def _cost_estimate_detail(ss, score):
        if ss > 0:
            txt = f"门店{ss}㎡，月租金需线下询价后结合面积测算。"
            detail = (f"门店面积{ss}㎡。建议线下询问3-5家相邻商户实际租金（元/㎡/月），"
                      f"乘以门店面积得出月租金范围。不要只看线上挂牌价，线下实际成交通常低于挂牌。"
                      f"如果月租金占比超过预估月营收的20%，建议重新评估财务模型。评分：{score}")
        else:
            txt = "月租金需线下询价确认。"
            detail = ("建议线下询问相邻商户实际租金（元/㎡/月）。"
                      "如果月租金占比超过预估月营收的20%，建议重新评估财务模型。评分：50")
        return txt, detail

    _cs_text, _cs_detail = _cost_estimate_detail(store_size, 50)

    def _revenue_estimation_detail(bt, ss):
        family = classify_business_model_family(bt, brand_name, _category)
        if family == "education_childcare":
            return (f"托管营收测算需结合周边小学低年级学生数量、托管服务组合"
                    f"（午托/晚托/作业辅导/晚餐）和周边家长支付意愿来估算。"
                    f"建议用保守/中性/乐观三档，分别估算生源数、月收费、"
                    f"空间利用率和盈亏平衡点。本数据摘要不提供未经验证的营收推算。")
        if family == "education_training":
            return (f"培训营收测算需结合目标生源数、课程单价、续费率和满班率来估算。"
                    f"建议用保守/中性/乐观三档，分别估算生源数、月营收和固定成本。"
                    f"本数据摘要不提供未经验证的营收推算。")
        return (f"营收测算需结合线下客流实测和租金询价后完成。"
                f"建议用保守/中性/乐观三档假设分别测算日均单量、客单价、月固定成本和盈亏平衡点。"
                f"本数据摘要不提供未经验证的营收推算。")

    def _site_suggestion_detail(bt):
        family = classify_business_model_family(bt, brand_name, _category)
        if family == "education_childcare":
            return (f"本报告为数据摘要，用于选址初筛参考。"
                    f"建议顺序：① 确认周边小学和放学动线 → ② 走访暗竞品 → "
                    f"③ 核验合规和空间条件 → ④ 访谈家长需求 → ⑤ 制定财务模型。"
                    f"任何单一数据源都不足以支撑选址判断。")
        return (f"本报告为数据摘要，用于选址初筛参考。"
                f"建议顺序：① 现场实测客流（目标客群高峰时段）→ ② 询价租金和转让费 → "
                f"③ 走访同业态商户了解实际经营状况 → ④ 结合以上信息制定财务模型。"
                f"任何单一数据源都不足以支撑选址判断。")

    # ── dimension_scores ──
    dims = [
        {"key": "population_density", "label": "人口密集度",
         "score": _clamp(20, 85, 30 + res_500),
         "text": f"500米内{res_500}个住宅小区、{office_500}栋办公建筑，人口密度{'偏高' if res_500 >= 10 else '中等' if res_500 >= 5 else '偏低'}"},
        {"key": "traffic_accessibility", "label": "交通可达性",
         "score": _traffic_score(subway_500, bus_500, subway_applicable),
         "text": _traffic_text(subway_500, bus_500, subway_applicable)},
        {"key": "traffic_flow", "label": "客流特征",
         "score": _clamp(25, 75, 30 + res_500 // 2 + office_500),
         "text": _tf_text},
        {"key": "consumer_profile", "label": "消费人群",
         "score": _clamp(25, 80, 20 + office_500 + school_500),
         "text": _cp_text},
        {"key": "competition", "label": "竞争环境",
         "score": _competition_score(dc_200, dc_500, dc_1000, same_brand_risk,
                                     res_500, school_500, office_500,
                                     classify_business_model_family(business_type, brand_name, _category)),
         "text": _competition_text(dc_200, dc_500, dc_1000, sub_500, same_brand_risk)},
        {"key": "complementary_businesses", "label": "互补业态",
         "score": _clamp(30, 70, 40 + shopping_500 * 3 + _int(s10.get("convenience", 0))),
         "text": _complementary_text(shopping_500, _int(s10.get("convenience", 0)), _int(s10.get("hotels", 0)))},
        {"key": "category_advantage", "label": "品类优势",
         "score": _category_advantage_score(dc_200, dc_500, dc_1000, same_brand_risk, res_500, office_500, school_500,
                                            classify_business_model_family(business_type, brand_name, _category)),
         "text": _category_advantage_text(business_type, dc_200, dc_500, dc_1000, same_brand_risk, res_500, office_500, school_500, brand_name=brand_name)},
        {"key": "cost_estimate", "label": "成本压力",
         "score": 50,
         "text": _cs_text},
    ]

    # ── details（P0.5: 具体解释为什么低/怎么验证/什么情况淘汰）──
    _tf_text, _tf_detail = _traffic_flow_detail(res_500, office_500, school_500, subway_500, bus_500, dims[2]["score"])
    _cp_text, _cp_detail = _consumer_profile_detail(res_500, office_500, school_500, hotel_1000, dims[3]["score"])
    _cs_text, _cs_detail = _cost_estimate_detail(store_size, dims[7]["score"])
    _rev_detail = _revenue_estimation_detail(business_type, store_size)
    _site_detail = _site_suggestion_detail(business_type)

    details = {
        "population_density": (
            f"500米半径内{res_500}个住宅小区、{office_500}栋办公建筑、"
            f"{school_500}所教育机构、{hospital_500}家医院。"
            f"数据来自高德POI采集，已做名称脱水处理。"
            f"如现场发现数据中未收录的新建小区或写字楼，人口密度可能高于采集结果。评分：{dims[0]['score']}"
        ),
        "traffic_accessibility": _traffic_detail(subway_500, bus_500, parking_500, subway_applicable, dims[1]['score']),
        "traffic_flow": _tf_detail,
        "consumer_profile": _cp_detail,
        "competition": (
            f"直接竞品：200米{dc_200}家、500米{dc_500}家、1000米{dc_1000}家。"
            f"替代消费：200米{sub_200}家、500米{sub_500}家、1000米{sub_1000}家。"
            f"流量节点{sn_count(anc_1000, '个')}。评分：{dims[4]['score']}"
        ),
        "complementary_businesses": (
            f"500米内{shopping_500}个商业体、1000米内{_int(s10.get('convenience', 0))}个便利店/超市、"
            f"{_int(s10.get('hotels', 0))}家酒店。"
            f"配套结构{'较完善' if shopping_500 >= 3 else '偏弱'}，"
            f"建议现场核验商业体实际经营品类和目标客群是否与本店互补。评分：{dims[5]['score']}"
        ),
        "category_advantage": dims[6]["text"],
        "cost_estimate": _cs_detail,
        "revenue_estimation": _rev_detail,
        "site_suggestion": _site_detail,
    }

    # ── P1: field_checklist 统一使用 business_model_service ──
    field_checklist = build_business_field_checklist(
        real_data, business_type, brand_name, store_size, category=_category)

    # ── 简版 action_plan 从 field_checklist 提取 ──
    action_plan = field_checklist  # 保留原始结构化数据供 decision_snapshot 使用

    # ── scores ──
    scores = [d["score"] for d in dims]
    overall = sum(scores) // len(scores) if scores else 50

    # ── P0.5-final: 统一 decision_snapshot（替代旧的 _verdict）──
    from services.report_decision_service import compute_decision_snapshot
    if same_brand_risk:
        brand_names_str = "、".join(same_brand_matches[:3])
        top_risk = f"1000米内疑似已有同品牌/近似品牌门店（{brand_names_str}），存在自我分流风险"
        warning = top_risk
        disadvantages.insert(0, top_risk)
    decision_snapshot = compute_decision_snapshot(
        overall, real_data, business_type=business_type, brand_name=brand_name,
        advantages=advantages, disadvantages=disadvantages, action_plan=field_checklist,
        is_fallback=True)
    top_strength = decision_snapshot.get("top_strength", advantages[0] if advantages else "")
    top_risk = decision_snapshot.get("top_risk", disadvantages[0] if disadvantages else warning)
    next_action = decision_snapshot.get("next_action", "")

    # ── executive_summary（必须在 same_brand_risk 之后，保证 top_risks 一致）──
    executive_summary = {
        "summary": "",  # 占位，后面用结构化字段填充
        "top_strengths": advantages[:3],
        "top_risks": disadvantages[:2],
    }

    # decision_snapshot already set above via compute_decision_snapshot

    # ── P0-A: caliber_explanation ──
    caliber_explanation = build_business_caliber_explanation(
        real_data, business_type, brand_name, category=_category)

    # ── P1: 地点基本面 ──
    location_fundamentals = compute_location_fundamentals(real_data)

    # ── P1: 生意模型快照 ──
    business_model_snapshot = compute_business_model_snapshot(
        real_data, business_type, brand_name, store_size, category=_category)

    # ── P1: 补齐 executive_summary.summary（用结构化字段生成更有用的摘要）──
    executive_summary["summary"] = _build_executive_summary(
        business_type, brand_name, family_adv,
        location_fundamentals, business_model_snapshot,
        dc_200, dc_500, dc_1000, sub_500, res_500, office_500, school_500,
        restaurants_1k)

    # ── P0-A: evidence_summary ──
    evidence_summary = {
        "direct_competitors": {"200m": dc_200, "500m": dc_500, "1000m": dc_1000},
        "substitute_consumption": {"200m": sub_200, "500m": sub_500, "1000m": sub_1000},
        "traffic_anchors": {"200m": _int(real_data.get("traffic_anchors_200m", 0)),
                           "500m": _int(real_data.get("traffic_anchors_500m", 0)),
                           "1000m": anc_1000},
        "key_pois": {
            "residential": {"200m": _int(s2.get("residential", 0)), "500m": res_500,
                           "1000m": _int(s10.get("residential", 0))},
            "schools": {"200m": _int(s2.get("schools", 0)), "500m": school_500,
                       "1000m": _int(s10.get("schools", 0))},
            "office": {"200m": _int(s2.get("office", 0)), "500m": office_500,
                      "1000m": _int(s10.get("office", 0))},
            "transport": {"200m": _int(s2.get("subway", 0)) + _int(s2.get("bus", 0)),
                         "500m": subway_500 + bus_500,
                         "1000m": _int(s10.get("subway", 0)) + _int(s10.get("bus", 0))},
        },
    }

    # ── P0-A: data_sufficiency ──
    from services.report_quality_service import assess_data_sufficiency
    data_sufficiency = assess_data_sufficiency(
        real_data, business_type=business_type, config_key="",
        rigor_enabled=bool(real_data.get("rigor_enabled", False)),
        is_fallback=True, brand_name=brand_name, category=_category)

    # ── P0-A: data_boundary ──
    data_boundary = (
        "数据来源：高德地图POI采集 + 系统规则分析。"
        "覆盖范围：以选址点为中心1000米半径。"
        "数据可能存在更新延迟，店铺经营状态以实际为准。"
        "本报告仅用于选址初筛参考，不替代现场调研、租金测算和实际商业判断。"
    )

    # ── P1: revenue_disclaimer ──
    from services.report_enrichment_service import _build_revenue_disclaimer
    rev_family = classify_business_model_family(business_type, brand_name, _category)
    revenue_disclaimer = _build_revenue_disclaimer(rev_family)

    return {
        # 旧字段（兼容）
        "summary": summary,
        "advantages": advantages[:5],
        "disadvantages": disadvantages[:5],
        "warning": warning,
        "details": details,
        "dimension_scores": dims,
        "executive_summary": executive_summary,
        "action_plan": _simple_action_plan(field_checklist, business_type, brand_name),
        "overall_score": overall,
        "score": overall,
        "total_score": overall,
        "provider": "fallback",
        "real_data": real_data,
        # P0-A 新字段
        "report_type": "fallback",
        "decision_snapshot": decision_snapshot,
        "field_checklist": field_checklist,
        "caliber_explanation": caliber_explanation,
        "evidence_summary": evidence_summary,
        "data_sufficiency": data_sufficiency,
        "data_boundary": data_boundary,
        # P1 新字段
        "location_fundamentals": location_fundamentals,
        "business_model_snapshot": business_model_snapshot,
        "revenue_disclaimer": revenue_disclaimer,
    }


def _detect_same_brand_risk(brand_name: str, real_data: dict) -> tuple:
    """保守检测1000米内同品牌/近似品牌门店。
    先规范化（去括号/空格/常见门店后缀），长度 >= 4 才判定。
    Returns (same_brand_risk: bool, matched_names: list).
    """
    import re as _re

    if not brand_name or len(brand_name.strip()) < 3:
        return False, []

    _STORE_SUFFIXES = ["旗舰店", "总店", "分店", "体验店", "形象店", "直营店",
                       "加盟店", "专卖店", "专营店", "概念店", "快闪店", "店"]

    def _normalize(name: str) -> str:
        """去括号、空格、常见门店后缀，提取品牌主体。"""
        s = _re.sub(r'[（(][^)）]*[)）]', '', name)  # 去括号
        s = _re.sub(r'\s+', '', s)                    # 去空白
        for suf in sorted(_STORE_SUFFIXES, key=len, reverse=True):
            if s.endswith(suf) and len(s) - len(suf) >= 2:
                s = s[:-len(suf)]
                break
        return s.strip()

    brand_norm = _normalize(brand_name)
    if len(brand_norm) < 4:
        return False, []

    matched = []
    _list_keys = [
        "direct_competitor_list", "direct_competitor_list_1000m",
        "direct_competitor_list_500m", "direct_competitor_list_200m",
        "competitor_list",
    ]
    for lst_key in _list_keys:
        entries = real_data.get(lst_key, []) or []
        if not entries:
            continue
        for entry in entries:
            name = (entry.get("name") or "").strip()
            if not name or len(name) < 3:
                continue

            name_norm = _normalize(name)
            if len(name_norm) < 4:
                continue

            # 规则1: 规范化品牌名完整出现在规范化竞品名中
            if brand_norm in name_norm:
                if name_norm not in matched:
                    matched.append(name_norm)
                continue

            # 规则2: 竞品去括号后的主名完整包含规范化品牌名
            name_deparen = _re.sub(r'[（(][^)）]*[)）]', '', name).strip()
            if len(name_deparen) >= 4 and brand_norm in name_deparen:
                if name_norm not in matched:
                    matched.append(name_norm)

    return len(matched) > 0, matched[:5]


def _build_executive_summary(business_type, brand_name, family,
                              location_fundamentals, business_model_snapshot,
                              dc_200, dc_500, dc_1000, sub_500,
                              res_500, office_500, school_500,
                              restaurants_1k):
    """用结构化字段生成有信息量的分析摘要。"""
    loc_summary = (location_fundamentals or {}).get("summary", "")
    core_logic = (business_model_snapshot or {}).get("core_logic", "")

    # 位置特征
    loc_type = (location_fundamentals or {}).get("label", "")

    # 竞品特征
    if dc_1000 == 0 and dc_500 == 0:
        comp_note = "近场无直接竞品记录"
    elif dc_200 == 0 and dc_1000 >= 8:
        comp_note = f"近场竞品少但 1000m 同类 {dc_1000} 家"
    elif dc_200 == 0:
        comp_note = f"近场竞品少，1000m 同类 {dc_1000} 家"
    elif dc_200 > 10:
        comp_note = f"200m 直接竞品 {dc_200} 家，竞争较激烈"
    else:
        comp_note = f"200m 直接竞品 {dc_200} 家、1000m {dc_1000} 家"

    # 客流基础
    pop = res_500 + office_500 + school_500
    if pop >= 20:
        pop_note = "周边人口和客流基础较好"
    elif pop >= 8:
        pop_note = "周边人口和客流基础中等"
    else:
        pop_note = "周边人口和客流基础偏弱"

    # 按族群定制
    if family == "snack_fast_food":
        if dc_200 == 0 and (dc_1000 >= 8 or restaurants_1k >= 40):
            return (
                f"该位置为{loc_type}，{pop_note}。{comp_note}，远场餐饮供给较充分（{restaurants_1k} 家）。"
                f"近场空档需核验是否因低客流导致；若租金低、1-2 人可运营、午市学校客流成立且外卖可覆盖晚餐，"
                f"才有作为小档口候选点的价值。"
            )
        if pop < 5:
            return (
                f"该位置为{loc_type}，{pop_note}。{comp_note}。"
                f"该点不是强客流点，建议优先核验实际午市人流和租金条件。"
            )
        return (
            f"该位置为{loc_type}，{pop_note}。{comp_note}。"
            f"小吃快餐需核验午市客流确定性、租金和外卖能力，不建议在未核验前投入谈判成本。"
        )

    if family == "education_childcare":
        return (
            f"该位置为{loc_type}，{pop_note}。{comp_note}。"
            f"此类选址需走访核验周边小学放学动线、家长接送条件和暗竞品。"
        )

    if family == "education_training":
        return (
            f"该位置为{loc_type}，{pop_note}。{comp_note}。"
            f"教育培训需核验周边生源密度、满班率和品牌差异化空间。"
        )

    # 通用
    return (
        f"该位置为{loc_type}，{pop_note}。{comp_note}。"
        f"建议结合现场客流、租金和周边供给情况核验后判断。"
    )


def _competition_score(dc_200, dc_500, dc_1000, same_brand_risk,
                       res_500=0, school_500=0, office_500=0,
                       business_family=""):
    """P1: 竞争环境评分。教育托管/生活服务等0竞品不能拿高分。"""
    if same_brand_risk:
        return _clamp(10, 45, 45 - dc_200 * 2)
    base = 85 - dc_200 * 2 - dc_500 * 1 - dc_1000 // 2
    if dc_1000 >= 4:
        base = min(base, 60)
    # P1: 教育托管/小饭桌/生活服务等业态，需求侧弱时竞争评分封顶
    if business_family in ("education_childcare", "education_training", "service_beauty"):
        pop = res_500 + school_500 + office_500
        if pop < 8 and dc_1000 == 0:
            # 需求弱且无POI竞品 → 不能高分，因为可能是低需求导致无供给
            base = min(base, 50)
        elif pop < 5:
            base = min(base, 60)
    # 小吃快餐：近场0竞品但远场多时限制
    if business_family == "snack_fast_food":
        if dc_200 == 0 and dc_1000 >= 8:
            base = min(base, 70)
    return _clamp(10, 85, base)


def _competition_text(dc_200, dc_500, dc_1000, sub_500, same_brand_risk):
    """竞争环境描述。避免"家同品类"连续短语被 POI guard 误判。"""
    if same_brand_risk:
        return (f"1000米内疑似已有同品牌/近似品牌门店，存在自我分流风险，竞争评分受限。"
                f"直接竞品 200米{dc_200}家、500米{dc_500}家、1000米{dc_1000}家。"
                f"现场重点核验同品牌分店实际经营状况和客群重叠程度。")
    level = "较激烈" if dc_200 > 10 else ("中等" if dc_200 > 3 else "200米直接竞品较少")
    extra = ""
    if dc_1000 >= 10:
        extra = "但1000米同品类门店较多，整体竞争不可忽视。"
    elif dc_1000 >= 4:
        extra = "1000米范围内同品类门店有一定数量，需关注辐射竞争。"
    return (f"直接竞品 200米{dc_200}家、500米{dc_500}家、1000米{dc_1000}家。"
            f"替代消费500米{sub_500}家，竞争{level}。{extra}")


def _complementary_text(shopping_500, convenience_1k, hotels_1k):
    parts = []
    if shopping_500 >= 3:
        parts.append(f"500米内{shopping_500}个商业体可共享客流")
    if convenience_1k >= 3:
        parts.append(f"1000米内{convenience_1k}个便利店/超市补充日常消费")
    if hotels_1k >= 3:
        parts.append(f"1000米内{hotels_1k}家酒店带来商旅客源")
    if not parts:
        return "500米内商业配套较少，主要依赖自身引流能力。建议现场核验周边是否有未收录的商业体或规划中的配套。"
    return "；".join(parts) + "。建议现场核验商业体实际经营状态和客群匹配度。"


def _category_advantage_score(dc_200, dc_500, dc_1000, same_brand_risk,
                              res_500, office_500, school_500,
                              business_family=""):
    """P1: 品类优势评分。教育托管/生活服务等0竞品在弱需求时不能高分。"""
    if same_brand_risk:
        return _clamp(10, 40, 40 - dc_200 * 2)
    base = 85
    base -= dc_200 * 3
    base -= dc_500 * 1
    if dc_1000 >= 8:
        base -= (dc_1000 - 8) * 2
    # 客流支撑加分
    pop_support = res_500 + office_500 + school_500
    if pop_support >= 15:
        base += 5
    elif pop_support < 5:
        base -= 10
    # P1: 教育托管/生活服务弱需求时封顶
    if business_family in ("education_childcare", "education_training", "service_beauty"):
        if pop_support < 8 and dc_1000 == 0:
            base = min(base, 50)
        elif pop_support < 5:
            base = min(base, 55)
    return _clamp(10, 85, base)


def _category_advantage_text(business_type, dc_200, dc_500, dc_1000,
                             same_brand_risk, res_500, office_500, school_500,
                             brand_name=""):
    """P1: 品类优势描述，按业态区分，禁止0竞品=强优势的机械解释。"""
    family = classify_business_model_family(business_type, brand_name)

    if same_brand_risk:
        return (f"同品牌分店风险导致品类优势受限。该业态在本位置"
                f"需通过差异化产品或服务建立独特竞争力。建议现场核验同品牌门店"
                f"的客单价、排队情况和顾客评价，确认是否存在错位竞争空间。")

    # 教育托管/培训/生活服务等 POI 易漏收录业态：0竞品不能写优势
    if family in ("education_childcare", "education_training", "service_beauty"):
        if dc_1000 == 0 and dc_500 == 0:
            return (
                f"该业态在本位置地图POI未显示明确同类供给。"
                f"但该类业态可能存在未被POI收录的暗竞品（家庭式托管/小饭桌/个人工作室），"
                f"需现场走访学校门口和周边小区确认实际供给。"
                f"POI 显示为 0 不代表没有竞品——也可能反映需求不足或该行业低收录率。"
            )
        if dc_200 == 0 and dc_1000 > 0:
            return (
                f"近场无直接竞品记录，1000m 同类门店：{dc_1000} 家。"
                f"注意：该类业态可能有未收录暗竞品，需现场走访确认。"
            )

    # 小吃快餐 200m 0竞品但远场多
    if family == "snack_fast_food":
        if dc_200 == 0 and dc_1000 >= 8:
            return (
                f"近场无同品类直接竞品，1000m 同类门店：{dc_1000} 家，"
                f"远场供给较充分。近场空档需要判断：是品类机会，还是低客流导致的空白。"
                f"只有低租金、小档口、强午市/外卖模型才值得继续看。"
            )
        if dc_200 <= 3 and dc_1000 <= 5:
            return (
                f"该业态在本位置直接竞品较少。"
                f"现场需核验午高峰实际客流和同类门店经营状态，"
                f"确认是否存在品类差异化机会。"
            )

    # 餐饮/零售等通用逻辑：0竞品但需求侧弱时不给高分
    pop_support = res_500 + office_500 + school_500
    if dc_200 <= 3 and dc_1000 <= 5:
        if pop_support < 5:
            return (
                f"该业态在本位置200米直接竞品仅{dc_200}家，"
                f"但周边人口和客流支撑较弱（住宅{res_500}、办公{office_500}、学校{school_500}），"
                f"0竞品可能反映需求不足而非品类机会。需现场核验目标客群实际存在量。"
            )
        return (
            f"该业态在本位置200米直接竞品仅{dc_200}家，"
            f"品类切入空间需结合客流核验判断。现场需核验500米内同品类门店的客单价和定位，"
            f"确认是否存在价格带空白或品类差异化机会。"
        )
    if dc_1000 >= 10:
        return (
            f"1000m 同品类门店：{dc_1000} 家，品类供给较充分。"
            f"现场需重点核验同品类门店上座率/排队情况，如午晚高峰均满座则仍有切入空间；"
            f"如上座率普遍偏低，则该品类在此区域可能供过于求。"
        )
    return (
        f"该业态在本位置品类竞争中等。"
        f"500米居住{res_500}小区、办公{office_500}栋、学校{school_500}所。"
        f"现场需核验目标客群实际消费偏好与该品类的匹配度。"
    )


def _clamp(lo, hi, v):
    return max(lo, min(hi, v))


def dh_count(n, word):
    """安全的数量+单位。避免"家XXX"连续短语被 POI name guard 误判为 POI 名称。"""
    if word.startswith("家"):
        # "家同类门店" → "同类门店 3 家"
        return f"{word[1:]} {n} 家"
    return f"{n}{word}"


def sn_count(n, word):
    """安全的数量+单位。"""
    if word.startswith("家"):
        return f"{word[1:]} {n} 家"
    return f"{n}{word}"


def _traffic_score(subway_n, bus_n, subway_applicable):
    base = 25
    if subway_applicable:
        base += subway_n * 15
    base += bus_n * 3
    return _clamp(15, 85, base)


def _traffic_text(subway_n, bus_n, subway_applicable):
    if not subway_applicable:
        total = bus_n
        level = "较便利" if total >= 8 else "一般" if total >= 3 else "偏弱"
        return f"本城市暂无地铁系统，500米内{bus_n}条公交线路，交通评估参考公交可达性，公交{level}"
    total = subway_n + bus_n
    level = "较便利" if total >= 5 else "一般" if total > 0 else "偏弱"
    return f"500米内{subway_n}个地铁站、{bus_n}条公交线路，交通{level}"


def _traffic_detail(subway_n, bus_n, parking_n, subway_applicable, score):
    if not subway_applicable:
        return f"本城市暂无地铁系统，交通评估参考公交线路、道路可达性和停车设施。500米内{bus_n}条公交线路、{parking_n}个停车设施。评分：{score}"
    return f"500米内{subway_n}个地铁站、{bus_n}条公交线路、{parking_n}个停车设施。评分：{score}"
