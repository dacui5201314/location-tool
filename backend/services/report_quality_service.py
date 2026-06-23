"""
数据充分度评估 — 确定性函数，不依赖 LLM/AMap。
输入 real_data + 元信息 → 输出 data_sufficiency 对象。
"""
from typing import Any


def _int(v, default=0):
    try: return int(v)
    except: return default


def assess_data_sufficiency(real_data: dict, business_type: str = "",
                            config_key: str = "", rigor_enabled: bool = False,
                            is_fallback: bool = False, brand_name: str = "",
                            category: str = "") -> dict:
    """评估本次报告的数据充分度。

    Returns:
        {
            "level": "sufficient / moderate / insufficient",
            "label": "数据较充分 / 数据一般 / 数据不足",
            "summary": "...",
            "reasons": [...],
            "flags": {...}
        }
    """
    flags = {
        "has_direct_competitors_data": False,
        "has_substitute_data": False,
        "has_traffic_anchor_data": False,
        "rigor_enabled": bool(rigor_enabled),
        "is_fallback": bool(is_fallback),
        "poi_sparse": False,
    }

    reasons = []
    level = "moderate"

    # 直接竞品数据（0 家也是有效采集结果，字段存在即为有数据）
    flags["has_direct_competitors_data"] = (
        "direct_competitors_200m" in real_data or
        "direct_competitors_500m" in real_data or
        "direct_competitors_1000m" in real_data
    )

    # 替代消费数据
    flags["has_substitute_data"] = (
        "substitute_competitors_200m" in real_data or
        "substitute_competitors_500m" in real_data or
        "substitute_competitors_1000m" in real_data
    )

    # 客流锚点数据
    flags["has_traffic_anchor_data"] = (
        "traffic_anchors_200m" in real_data or
        "traffic_anchors_500m" in real_data or
        "traffic_anchors_1000m" in real_data
    )

    # POI 稀疏判断：stats_1000m 有数据但总量少才判稀疏；poi_counts 空不判稀疏
    s10 = real_data.get("stats_1000m", {}) or {}
    total_poi_1km = sum(_int(v) for v in s10.values()) if s10 else 0
    poi_counts = real_data.get("poi_counts", {}) or {}
    total_poi_all = sum(_int(v) for v in poi_counts.values()) if poi_counts else 0
    # 只有在有 stats_1000m 数据且总量确实少时才判稀疏
    flags["poi_sparse"] = (total_poi_1km > 0 and total_poi_1km < 15)

    # === 评分逻辑（确定性规则） ===
    if not flags["rigor_enabled"]:
        reasons.append("当前业态未启用严谨竞品分类规则，分析口径较宽")
        level = "moderate"

    if flags["is_fallback"]:
        reasons.append("本报告为初筛版参考，适合先判断是否值得实地看铺")
        if level == "sufficient":
            level = "moderate"

    if flags["poi_sparse"]:
        reasons.append("周边 POI 数据较少，分析依据有限")
        level = "insufficient"

    if level == "moderate" and not reasons:
        reasons.append("核心竞品和客流数据可用，但部分维度需现场核验补充")

    if not flags["has_direct_competitors_data"] and not flags["has_traffic_anchor_data"]:
        reasons.append("缺少直接竞品和客流锚点字段，仅基于基础设施 POI 评估")
        if level != "insufficient":
            level = "insufficient" if flags["poi_sparse"] else "moderate"

    # fallback 最高只能是 moderate
    if flags["is_fallback"] and level == "sufficient":
        level = "moderate"
        reasons.insert(0, "初筛版参考，适合先判断是否值得实地看铺")

    # 未启用 rigor 且 POI 稀疏 → 直接 insufficient
    if not flags["rigor_enabled"] and flags["poi_sparse"]:
        level = "insufficient"
        if not any("POI 数据较少" in r for r in reasons):
            reasons.append("周边 POI 数据较少，分析依据有限")

    # 数据充足条件
    if (flags["has_direct_competitors_data"] and flags["rigor_enabled"]
            and not flags["poi_sparse"] and not flags["is_fallback"]):
        level = "sufficient"

    # labels
    label_map = {
        "sufficient": "POI数据较充分",
        "moderate": "POI数据一般",
        "insufficient": "POI数据不足",
    }

    summary_map = {
        "sufficient": "POI数据较充分，经营数据待现场核验",
        "moderate": "POI数据一般，仅适合初筛，关键经营信息需现场核验",
        "insufficient": "POI数据不足，只能作为保守参考",
    }

    # P1: 教育托管类需补充托管竞品和合规提示
    from services.business_model_service import classify_business_model_family
    family = classify_business_model_family(business_type, brand_name, category)
    if family == "education_childcare":
        reasons.append("托管竞品、合规资质、招生需求无法仅靠地图POI判断，需现场核验")
        if level == "sufficient":
            level = "moderate"
            label_map["sufficient"] = "POI数据较充分"

    return {
        "level": level,
        "label": label_map.get(level, "POI数据一般"),
        "summary": summary_map.get(level, "POI数据一般，仅适合初筛，关键经营信息需现场核验"),
        "reasons": reasons,
        "flags": flags,
    }
