"""
兜底报告回归测试 — 教育培训场景全量 guard 验证。
运行方式：cd backend && python tests/check_fallback_report.py
"""
import sys, os, json as _json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.fallback_report_service import build_fallback_report
from report_fact_guard import validate_report_fact_consistency
from services.poi_name_guard import (
    check_poi_name_hallucination,
    check_poi_context_mismatch,
    check_direct_competitor_count_mismatch,
)


def test_fallback_education():
    """教育培训兜底报告：构造 real_data → build_fallback_report → 全量 guard 验证。"""
    real_data = {
        "stats_200m": {"schools": 1, "residential": 2, "office": 1, "hospitals": 0},
        "stats_500m": {"schools": 3, "residential": 10, "office": 3, "hospitals": 1,
                       "subway": 1, "bus": 6, "parking": 2, "shopping": 1, "hotels": 0},
        "stats_1000m": {"schools": 5, "residential": 25, "office": 8, "hospitals": 2,
                        "subway": 2, "bus": 12, "parking": 5, "shopping": 3, "hotels": 4},
        "poi_counts": {"schools": 5, "residential": 25, "office": 8, "hospitals": 2},
        "direct_competitors_200m": 0,
        "direct_competitors_500m": 0,
        "direct_competitors_1000m": 1,
        "substitute_competitors_200m": 0,
        "substitute_competitors_500m": 2,
        "substitute_competitors_1000m": 5,
        "traffic_anchors_200m": 0,
        "traffic_anchors_500m": 1,
        "traffic_anchors_1000m": 3,
        "direct_competitor_list": [{"name": "新东方培训中心", "distance": 800}],
        "direct_competitor_list_200m": [],
        "direct_competitor_list_500m": [],
        "direct_competitor_list_1000m": [{"name": "新东方培训中心", "distance": 800}],
        "substitute_list": [],
        "traffic_anchor_list": [],
        "poi_lists": {"schools": []},
        "hot_brands": [],
        "nearby_roads": ["中山路"],
        "rigor_enabled": False,
        "subway_applicable": True,
        "city_has_subway": True,
    }

    report = build_fallback_report(real_data, address="测试地址",
                                   business_type="教育培训",
                                   brand_name="小学生托管服务",
                                   store_size=200)

    # 1. validate_report_fact_consistency
    fe = validate_report_fact_consistency(report, real_data)
    if fe:
        raise AssertionError(f"fact_consistency failed: {'; '.join(fe)}")

    # 2. check_poi_name_hallucination (exclude action_plan)
    fb_text = (
        _json.dumps(report.get("details", {}) or {}, ensure_ascii=False) + " " +
        _json.dumps(report.get("advantages", []), ensure_ascii=False) + " " +
        _json.dumps(report.get("disadvantages", []), ensure_ascii=False) + " " +
        _json.dumps(report.get("executive_summary", {}) or {}, ensure_ascii=False) + " " +
        str(report.get("summary", ""))
    )
    p0 = check_poi_name_hallucination(fb_text, real_data, strict=True)
    if p0:
        raise AssertionError(f"P0-NAME failed: {'; '.join(p0)}")

    # 3. check_poi_context_mismatch
    p2 = check_poi_context_mismatch(fb_text, real_data)
    if p2:
        raise AssertionError(f"P2-CTX failed: {'; '.join(p2)}")

    # 4. check_direct_competitor_count_mismatch
    p3 = check_direct_competitor_count_mismatch(fb_text, real_data)
    if p3:
        raise AssertionError(f"P3-COUNT failed: {'; '.join(p3)}")

    print("test_fallback_education: ALL PASS")
    return True


if __name__ == "__main__":
    test_fallback_education()
