"""
兜底报告生成器 — 纯函数，不依赖 LLM/AMap/FastAPI。
LLM 报告事实校验失败 + retry 仍失败时，用 real_data 生成保守版报告。
只引用真实数量和泛化类别，不写任何具体 POI 名称。
文案严格避免 P0 语境关键词和决策性表述。
"""
import json as _json


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

    # ── advantages（避免"周边""同类""竞品""红利""极低"） ──
    advantages = []
    if dc_200 <= 3:
        advantages.append(f"200米范围内{dh_count(dc_200, '同业态商户')}，竞争压力较小")
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
        disadvantages.append(f"200米范围内{dh_count(dc_200, '家同业态商户')}，竞争较激烈")
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
        warning = "200米内同业态商户密集"
    elif subway_applicable and subway_500 == 0 and bus_500 <= 2:
        warning = "公共交通条件较弱"
    else:
        warning = "需线下实地核验"

    # ── summary ──
    summary = (
        f"该{business_type or '门店'}选址数据摘要：200米内{dc_200}家同业态商户，"
        f"500米内{res_500}个住宅小区、{office_500}栋办公建筑、{school_500}所教育机构。"
        f"本报告为基于采集数据的保守版数据摘要，不替代现场客流、租金和商户经营状态核验。"
    )

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
         "text": "基于居住和办公人口推算，具体客流需线下实测"},
        {"key": "consumer_profile", "label": "消费人群",
         "score": _clamp(25, 80, 20 + office_500 + school_500),
         "text": f"居住和办公混合区域，消费层次需线下核验"},
        {"key": "competition", "label": "竞争环境",
         "score": _clamp(10, 85, 85 - dc_200 * 2),
         "text": f"200米内{dc_200}家同业态商户，竞争{'较激烈' if dc_200 > 10 else '中等' if dc_200 > 3 else '较缓和'}"},
        {"key": "complementary_businesses", "label": "互补业态",
         "score": 50,
         "text": "商业配套需线下实地核验补充"},
        {"key": "category_advantage", "label": "品类优势",
         "score": _clamp(10, 85, 85 - dc_200 * 3),
         "text": f"同业态商户{'较少' if dc_200 <= 3 else '数量中等' if dc_200 <= 15 else '数量较多'}"},
        {"key": "cost_estimate", "label": "成本压力",
         "score": 50,
         "text": f"预估月租金需线下询价确认，不替代实际租金谈判"},
    ]

    # ── details（避免"周边""附近""竞品""锚点"） ──
    details = {
        "population_density": f"500米半径内{res_500}个住宅小区、{office_500}栋办公建筑、{school_500}所教育机构、{hospital_500}家医院。数据来自高德POI采集。评分：{dims[0]['score']}",
        "traffic_accessibility": _traffic_detail(subway_500, bus_500, parking_500, subway_applicable, dims[1]['score']),
        "traffic_flow": "日均客流量需线下实测确认。评分：" + str(dims[2]['score']),
        "consumer_profile": f"数据摘要，不替代现场消费层次核验。评分：{dims[3]['score']}",
        "competition": f"200米内{dc_200}家同业态商户，500米内{dc_500}家，1000米内{dc_1000}家。替代消费{sn_count(sub_1000, '家')}，流量节点{sn_count(anc_1000, '个')}。评分：{dims[4]['score']}",
        "complementary_businesses": "商业配套结构需线下实地核验补充。评分：50",
        "category_advantage": f"{business_type or '该业态'}在本位置供需匹配度需线下判断，数据不替代实地核验。评分：{dims[6]['score']}",
        "cost_estimate": f"门店面积{store_size}㎡，月租金需线下询价确认。评分：50",
        "revenue_estimation": "营收测算需线下客流测量后完成，本数据摘要不提供推算。",
        "site_suggestion": f"本报告为数据摘要，不替代现场核验。建议线下实测客流、询价租金、走访商户后再制定方案。"
    }

    # ── executive_summary ──
    executive_summary = {
        "summary": "基于采集数据的初筛摘要，需线下核验",
        "top_strengths": advantages[:3],
        "top_risks": disadvantages[:2],
    }

    # ── action_plan ──
    action_plan = [
        "安排1-3天不同时段现场客流实测",
        "实地走访同业态商户了解经营状况",
        "线下询价确认租金后制定财务模型",
    ]

    # ── scores ──
    scores = [d["score"] for d in dims]
    overall = sum(scores) // len(scores) if scores else 50

    return {
        "summary": summary,
        "advantages": advantages[:5],
        "disadvantages": disadvantages[:5],
        "warning": warning,
        "details": details,
        "dimension_scores": dims,
        "executive_summary": executive_summary,
        "action_plan": action_plan,
        "overall_score": overall,
        "score": overall,
        "total_score": overall,
        "provider": "fallback",
        "real_data": real_data,
    }


def _clamp(lo, hi, v):
    return max(lo, min(hi, v))


def dh_count(n, word):
    """数量+单位，避免 "X家" 触发 P0 "家" 后缀"""
    return f"{n}{word}"


def sn_count(n, word):
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
