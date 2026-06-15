"""
P1 报告业务上下文统一补全服务 — 确定性函数，不依赖 LLM。
所有报告（normal / retry / fallback）在保存前调用 enrich_report_business_context()，
确保 P1 模块（地点基本面、生意模型快照、竞品口径说明、证据摘要、数据边界、营收免责）
在所有三条链路上一致存在，避免 normal/retry 缺失 P1 模块。
"""
from services.business_model_service import (
    classify_business_model_family,
    compute_location_fundamentals,
    compute_business_model_snapshot,
    build_business_field_checklist,
    build_business_caliber_explanation,
)


def _int(v, default=0):
    try: return int(v)
    except: return default


def enrich_report_business_context(report: dict, real_data: dict,
                                    business_type: str = "",
                                    brand_name: str = "",
                                    category: str = "",
                                    store_size: int = 0,
                                    is_fallback: bool = False) -> dict:
    """对报告补齐 P1 业务上下文模块。幂等：已有字段不覆盖。"""
    r = real_data or {}
    rd = {} if not isinstance(r, dict) else r

    # ── 地点基本面（同一地址不同业态共享）──
    if not report.get("location_fundamentals") or not isinstance(report.get("location_fundamentals"), dict) or not report["location_fundamentals"].get("label"):
        report["location_fundamentals"] = compute_location_fundamentals(rd)

    # ── 生意模型快照 ──
    if not report.get("business_model_snapshot") or not isinstance(report.get("business_model_snapshot"), dict) or not report["business_model_snapshot"].get("model_type"):
        report["business_model_snapshot"] = compute_business_model_snapshot(
            rd, business_type, brand_name, store_size, category=category)

    # ── 竞品口径说明 ──
    if not report.get("caliber_explanation") or not isinstance(report.get("caliber_explanation"), str) or len(report.get("caliber_explanation", "")) < 20:
        report["caliber_explanation"] = build_business_caliber_explanation(
            rd, business_type, brand_name, category=category)

    # ── 证据摘要 ──
    if not report.get("evidence_summary") or not isinstance(report.get("evidence_summary"), dict):
        s2 = rd.get("stats_200m", {}) or {}
        s5 = rd.get("stats_500m", {}) or {}
        s10 = rd.get("stats_1000m", {}) or {}
        report["evidence_summary"] = {
            "direct_competitors": {
                "200m": _int(rd.get("direct_competitors_200m", 0)),
                "500m": _int(rd.get("direct_competitors_500m", 0)),
                "1000m": _int(rd.get("direct_competitors_1000m", 0)),
            },
            "substitute_consumption": {
                "200m": _int(rd.get("substitute_competitors_200m", 0)),
                "500m": _int(rd.get("substitute_competitors_500m", 0)),
                "1000m": _int(rd.get("substitute_competitors_1000m", 0)),
            },
            "traffic_anchors": {
                "200m": _int(rd.get("traffic_anchors_200m", 0)),
                "500m": _int(rd.get("traffic_anchors_500m", 0)),
                "1000m": _int(rd.get("traffic_anchors_1000m", 0)),
            },
            "key_pois": {
                "residential": {"200m": _int(s2.get("residential", 0)), "500m": _int(s5.get("residential", 0)), "1000m": _int(s10.get("residential", 0))},
                "schools": {"200m": _int(s2.get("schools", 0)), "500m": _int(s5.get("schools", 0)), "1000m": _int(s10.get("schools", 0))},
                "office": {"200m": _int(s2.get("office", 0)), "500m": _int(s5.get("office", 0)), "1000m": _int(s10.get("office", 0))},
                "transport": {"200m": _int(s2.get("subway", 0)) + _int(s2.get("bus", 0)),
                             "500m": _int(s5.get("subway", 0)) + _int(s5.get("bus", 0)),
                             "1000m": _int(s10.get("subway", 0)) + _int(s10.get("bus", 0))},
            },
        }

    # ── 数据边界 ──
    if not report.get("data_boundary") or not isinstance(report.get("data_boundary"), str) or len(report.get("data_boundary", "")) < 20:
        report["data_boundary"] = (
            "数据来源：高德地图POI采集 + 系统规则分析。"
            "覆盖范围：以选址点为中心1000米半径。"
            "数据可能存在更新延迟，店铺经营状态以实际为准。"
            "本报告仅用于选址初筛参考，不替代现场调研、租金测算和实际商业判断。"
        )

    # ── 营收免责（按业态区分）──
    if not report.get("revenue_disclaimer") or not isinstance(report.get("revenue_disclaimer"), str) or len(report.get("revenue_disclaimer", "")) < 10:
        family = classify_business_model_family(business_type, brand_name, category)
        report["revenue_disclaimer"] = _build_revenue_disclaimer(family)

    # ── field_checklist 业态纠偏：如果 normal/retry 生成的 checklist 仍有餐饮词 ──
    fc = report.get("field_checklist")
    if fc and isinstance(fc, list):
        family = classify_business_model_family(business_type, brand_name, category)
        if family == "education_childcare":
            titles = " ".join(
                (t.get("title", "") if isinstance(t, dict) else str(t))
                for t in fc[:5]
            )
            FOOD_SIGNAL = ["外卖骑手", "出餐速度", "上座率", "取餐", "午晚高峰堂食"]
            if any(w in titles for w in FOOD_SIGNAL):
                report["field_checklist"] = build_business_field_checklist(
                    rd, business_type, brand_name, store_size, category=category)
    # fallback 的 field_checklist 在 fallback_report_service.py 中已用 business_model_service 生成；
    # 这里也为 normal/retry 提供防御性补齐
    family_check = classify_business_model_family(business_type, brand_name, category)
    if (not report.get("field_checklist") or not isinstance(report.get("field_checklist"), list) or len(report.get("field_checklist", [])) < 3) and family_check in (
        "education_childcare", "snack_fast_food", "education_training"
    ):
        report["field_checklist"] = build_business_field_checklist(
            rd, business_type, brand_name, store_size, category=category)

    return report


def _build_revenue_disclaimer(family: str) -> str:
    """按生意模型族群生成营收模型免责。"""
    base = "以上为模型估算，不代表实际经营结果；需结合"
    disclaimers = {
        "education_childcare": base + "周边小学距离、生源数、托管服务组合、合规资质和租金复核。",
        "education_training": base + "生源数、课程单价、续费率、满班率和租金复核。",
        "snack_fast_food": base + "现场客流、租金、转让费、出餐能力和外卖能力复核。",
        "food_service": base + "现场客流、租金、停车条件、翻台率和食材成本复核。",
        "beverage_dessert": base + "现场步行客流、租金、外卖平台竞争和品牌势能复核。",
        "retail_convenience": base + "周边社区客流、客单价、复购率、租金和供货能力复核。",
        "retail_shopping": base + "商圈客流、坪效、库存周转率和租金复核。",
        "service_beauty": base + "周边消费力、会员转化率、复购频次、技师/人员能力和租金复核。",
        "service_basic": base + "社区人口规模、需求饱和度、合规资质和租金复核。",
        "hotel": base + "入住率、ADR、OTA获客成本、物业条件和消防/证照要求复核。",
        "entertainment": base + "年轻客群密度、深夜可达性、隔音/消防合规和租金复核。",
        "generic": base + "现场客流、租金和实际经营条件复核。",
    }
    return disclaimers.get(family, disclaimers["generic"])
