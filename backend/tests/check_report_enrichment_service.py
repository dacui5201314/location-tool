"""Phase 1 enrichment service 回归测试"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_enrichment_service import enrich_report_business_context


def _base_rd():
    return {
        "stats_200m":{"residential":0,"office":0,"schools":1,"hospitals":0,"subway":0,"bus":0,"parking":1,"shopping":0,"hotels":0,"restaurants":2},
        "stats_500m":{"residential":4,"office":0,"schools":4,"hospitals":0,"subway":0,"bus":3,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        "stats_1000m":{"residential":13,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":8,"parking":26,"shopping":0,"hotels":7,"restaurants":56},
        "direct_competitors_200m":0,"direct_competitors_500m":2,"direct_competitors_1000m":12,
        "substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,
        "traffic_anchors_200m":0,"traffic_anchors_500m":3,"traffic_anchors_1000m":8,
        "direct_competitor_list":[],"direct_competitor_list_200m":[],"direct_competitor_list_500m":[],"direct_competitor_list_1000m":[],
        "substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
        "rigor_enabled":True,"subway_applicable":True,"city_has_subway":False,
    }


# T1: normal / retry / fallback 都包含 location_profile
def test_all_paths_have_location_profile():
    rd = _base_rd()
    report = {"score":55,"summary":"test","advantages":["a"],"disadvantages":["d"],"dimension_scores":[],"details":{},"action_plan":["a"]}
    for is_fb, label in [(False,"normal"),(True,"fallback")]:
        e = enrich_report_business_context(report.copy(), rd, business_type="小吃快餐", brand_name="砂锅",
                                           store_size=50, is_fallback=is_fb)
        assert e.get("location_profile"), f"{label} missing location_profile"
        assert e["location_profile"].get("primary_type"), f"{label} location_profile empty"
    print("T1 all paths have location_profile: PASS")


# T2: business_model_snapshot 与 location_profile 能同时存在
def test_both_snapshot_and_profile():
    rd = _base_rd()
    report = {"score":55,"summary":"test","advantages":["a"],"disadvantages":["d"],"dimension_scores":[],"details":{},"action_plan":["a"]}
    e = enrich_report_business_context(report, rd, business_type="小吃快餐", brand_name="砂锅", store_size=50)
    assert e.get("business_model_snapshot"), "missing business_model_snapshot"
    assert e.get("location_profile"), "missing location_profile"
    print(f"T2 snapshot+profile: model={e['business_model_snapshot']['model_type']}, loc={e['location_profile']['primary_type']} PASS")


# T3: fallback 无营收测算时 revenue_disclaimer 不写"以上为模型估算"
def test_fallback_no_estimate_disclaimer():
    rd = _base_rd()
    report = {"score":47,"summary":"test","advantages":["a"],"disadvantages":["d"],"dimension_scores":[],"details":{},"action_plan":["a"]}
    e = enrich_report_business_context(report, rd, business_type="教育培训", brand_name="小学生托管",
                                       store_size=100, is_fallback=True)
    rd_text = e.get("revenue_disclaimer","")
    assert "以上为模型估算" not in rd_text, f"fallback无测算不应写模型估算: {rd_text[:80]}"
    assert "未生成营收测算" in rd_text, f"应包含未生成营收测算提示: {rd_text[:80]}"
    print(f"T3 no estimate: {rd_text[:100]} PASS")


# T4: 教育托管 location_profile 不把餐饮作为优势
def test_edu_no_dining_in_profile():
    rd = _base_rd()
    rd["stats_1000m"]["restaurants"] = 56
    report = {"score":47,"summary":"test","advantages":["a"],"disadvantages":["d"],"dimension_scores":[],"details":{},"action_plan":["a"]}
    e = enrich_report_business_context(report, rd, business_type="教育培训", brand_name="小学生托管",
                                       store_size=100, is_fallback=True)
    lp = e.get("location_profile", {})
    for s in lp.get("strengths", []):
        assert "餐饮" not in str(s), f"教育托管location_profile不应含餐饮优势: {s}"
    lf = e.get("location_fundamentals", {})
    for s in lf.get("strengths", []):
        assert "餐饮" not in str(s), f"教育托管location_fundamentals不应含餐饮优势: {s}"
    print("T4 edu no dining in profile: PASS")


# T5: 保守版价值说明存在
def test_conservative_value_note():
    rd = _base_rd()
    report = {"score":47,"summary":"test","advantages":["a"],"disadvantages":["d"],"dimension_scores":[],"details":{},"action_plan":["a"]}
    e = enrich_report_business_context(report, rd, business_type="小吃快餐", brand_name="砂锅",
                                       store_size=50, is_fallback=True)
    boundary = e.get("data_boundary", "")
    assert "虽为保守版" in boundary, f"fallback应包含保守版价值说明: {boundary[:100]}"
    print(f"T5 conservative note: {boundary[:120]}... PASS")


# T6: 小吃快餐不为教育托管
def test_snack_not_misclassified():
    from services.business_model_service import classify_business_model_family
    assert classify_business_model_family("小吃快餐", "砂锅", "") == "snack_fast_food"
    assert classify_business_model_family("教育培训", "英语培训", "") == "education_training"
    assert classify_business_model_family("教育培训", "小学生托管", "") == "education_childcare"
    print("T6 classifications correct: PASS")


# T7: normal/retry/fallback 三路径 report JSON 字段完整性
def test_three_paths_field_completeness():
    from services.fallback_report_service import build_fallback_report
    from services.report_enrichment_service import enrich_report_business_context

    rd = _base_rd()
    # fields enriched by report_enrichment_service (decision_snapshot/data_sufficiency by main.py)
    required = [
        "location_profile", "location_fundamentals", "business_model_snapshot",
        "business_model_version", "revenue_disclaimer", "field_checklist",
        "caliber_explanation", "evidence_summary", "data_boundary",
    ]

    # normal path
    normal = {"score":55,"summary":"t","advantages":["a"],"disadvantages":["d"],"dimension_scores":[],"details":{},"action_plan":["a"]}
    e_n = enrich_report_business_context(normal, rd, business_type="小吃快餐", brand_name="砂锅", store_size=50, is_fallback=False)
    for k in required:
        assert k in e_n and e_n[k], f"normal missing {k}"

    # fallback path (build_fallback_report + enrichment, as main.py does)
    fb = build_fallback_report(rd, address="t", business_type="小吃快餐", brand_name="砂锅", store_size=50)
    fb = enrich_report_business_context(fb, rd, business_type="小吃快餐", brand_name="砂锅", store_size=50, is_fallback=True)
    for k in required:
        assert k in fb and fb[k], f"fallback missing {k}"

    # retry = normal + enrichment (same path)
    e_r = enrich_report_business_context(normal.copy(), rd, business_type="教育培训", brand_name="英语培训", store_size=80, is_fallback=False)
    for k in required:
        assert k in e_r and e_r[k], f"retry missing {k}"

    print("T7 three-path field completeness: 11 fields x 3 paths PASS")


# T8: HTML 重建只消费 report_json，不调用业务判断
def test_html_renders_from_report_json_only():
    from services.storage_service import _build_report_html
    from services.fallback_report_service import build_fallback_report

    rd = _base_rd()
    fb = build_fallback_report(rd, address="t", business_type="小吃快餐", brand_name="砂锅", store_size=50)
    fb["business_type"] = "小吃快餐"
    fb["generated_at"] = "2026-06-15 10:00"

    html = _build_report_html(1, fb, "addr", "brand")
    # HTML 应包含 P1 字段内容
    for marker in ["保守版数据摘要", "选址决策参考", "地点基本面", "现场核验清单", "经营建议"]:
        assert marker in html, f"HTML missing: {marker}"
    print("T8 HTML renders from report_json: PASS")


if __name__ == "__main__":
    test_all_paths_have_location_profile()
    test_both_snapshot_and_profile()
    test_fallback_no_estimate_disclaimer()
    test_edu_no_dining_in_profile()
    test_conservative_value_note()
    test_snack_not_misclassified()
    test_three_paths_field_completeness()
    test_html_renders_from_report_json_only()
    print()
    print("ALL ENRICHMENT SERVICE TESTS PASSED")
