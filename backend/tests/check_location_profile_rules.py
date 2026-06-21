"""Phase 0 位置基本面规则测试"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.location_profile_service import (
    compute_location_profile, compute_school_anchor_breakdown,
    get_dining_not_advantage_families, _classify_school,
    _k12_school_count, dedup_bus_count, build_location_fact_snapshot,
)


def _base_rd(**overrides):
    base = {
        "stats_200m": {"residential":0,"office":0,"schools":1,"hospitals":0,"subway":0,"bus":0,"parking":1,"shopping":0,"hotels":0,"restaurants":2},
        "stats_500m": {"residential":4,"office":0,"schools":4,"hospitals":0,"subway":0,"bus":3,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        "stats_1000m": {"residential":13,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":8,"parking":26,"shopping":0,"hotels":7,"restaurants":56},
        "direct_competitors_200m":0,"direct_competitors_500m":2,"direct_competitors_1000m":12,
        "substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,
        "traffic_anchors_200m":0,"traffic_anchors_500m":3,"traffic_anchors_1000m":8,
        "substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
        "rigor_enabled":True,"subway_applicable":True,"city_has_subway":False,
    }
    base.update(overrides)
    return base


# T1: 同一 real_data 切换业态 location_profile 一致
def test_location_profile_consistent():
    rd = _base_rd()
    lp1 = compute_location_profile(rd)
    lp2 = compute_location_profile(rd)
    assert lp1["primary_type"] == lp2["primary_type"]
    assert lp1["label"] == lp2["label"]
    assert lp1["strengths"] == lp2["strengths"]
    assert lp1["weaknesses"] == lp2["weaknesses"]
    print(f"T1 location_profile consistent: primary_type={lp1['primary_type']} PASS")


# T2: 九悦香都不能把餐饮门店多作为教育托管核心优势
def test_no_dining_as_edu_advantage():
    from services.report_enrichment_service import enrich_report_business_context

    rd = _base_rd()
    report = {"score":47,"summary":"test","advantages":["a"],"disadvantages":["d"],
              "dimension_scores":[],"details":{},"action_plan":["a"]}
    enriched = enrich_report_business_context(
        report, rd, business_type="教育培训", brand_name="小学生托管",
        store_size=100, is_fallback=True)

    lf = enriched.get("location_fundamentals") or {}
    strengths = lf.get("strengths") or []
    for s in strengths:
        assert "餐饮" not in str(s), f"教育托管location_fundamentals不应含餐饮优势: {s}"

    lp = enriched.get("location_profile") or {}
    strengths_p = lp.get("strengths") or []
    for s in strengths_p:
        assert "餐饮" not in str(s), f"教育托管location_profile不应含餐饮优势: {s}"

    print("T2 no dining as edu advantage: PASS")


# T3: location_profile 输出 evidence 完整
def test_location_profile_evidence():
    rd = _base_rd()
    lp = compute_location_profile(rd)
    evidence = lp.get("evidence", {})
    required = ["schools_500m","residential_500m","office_500m","bus_500m","subway_500m","restaurants_1000m","school_anchor_breakdown"]
    for k in required:
        assert k in evidence, f"evidence missing {k}"
    sab = evidence.get("school_anchor_breakdown", {})
    assert "total" in sab
    assert "breakdown" in sab
    print(f"T3 evidence complete: {sorted(evidence.keys())} PASS")


# T4: school_anchor_breakdown 分类正确
def test_school_classification():
    cases = [
        ("宝鸡高新第一小学", "elementary"),
        ("阳光幼儿园", "kindergarten"),
        ("宝鸡中学", "middle_high"),
        ("宝鸡文理学院", "university"),
        ("新东方培训中心", "training"),
        ("某某学校", "unknown"),
        ("未知机构", "unknown"),
    ]
    for name, expected in cases:
        result = _classify_school(name)
        assert result == expected, f"{name}: expected {expected}, got {result}"
    print(f"T4 school classification: {len(cases)} cases PASS")


# T5: 学校数据有值时能返回细分
def test_school_breakdown_with_data():
    rd = _base_rd()
    rd["poi_lists"] = {
        "schools": [
            {"name": "宝鸡高新第一小学"},
            {"name": "宝鸡文理学院"},
            {"name": "宝鸡文理学院第二教学楼"},
            {"name": "阳光幼儿园"},
            {"name": "宝鸡中学"},
            {"name": "新东方培训中心"},
        ]
    }
    sab = compute_school_anchor_breakdown(rd)
    assert sab["total"] == 6
    bd = sab["breakdown"]
    assert bd.get("elementary", 0) >= 1
    assert bd.get("university", 0) >= 2
    assert bd.get("kindergarten", 0) >= 1
    print(f"T5 school breakdown: {bd} PASS")


# T6: dining_not_advantage 集合
def test_dining_not_advantage():
    families = get_dining_not_advantage_families()
    assert "education_childcare" in families
    assert "education_training" in families
    assert "snack_fast_food" not in families
    print(f"T6 dining not advantage: {sorted(families)} PASS")


# T7: 全是大学/培训机构，schools>=8 → 不得判定为学区
def test_university_only_not_school_zone():
    rd = _base_rd()
    rd["stats_500m"]["schools"] = 10
    rd["poi_lists"] = {
        "schools": [
            {"name": "宝鸡文理学院"},
            {"name": "宝鸡职业技术学院"},
            {"name": "某师范学院"},
            {"name": "某理工学校"},
            {"name": "新东方培训中心"},
            {"name": "某琴行"},
            {"name": "某画室"},
            {"name": "某大学城校区"},
            {"name": "某高等专科学校"},
            {"name": "某培训学校"},
        ]
    }
    lp = compute_location_profile(rd)
    # primary_type 不得为"学区及周边"
    assert "学区" not in lp["primary_type"], f"全大学不应判学区: {lp['primary_type']}"
    # label 不得含"学区"
    assert "学区" not in lp["label"], f"全大学 label 不应含学区: {lp['label']}"
    # strengths 不得出现"学区客群基础较好"
    strengths_text = " ".join(lp.get("strengths", []))
    assert "学区客群" not in strengths_text, f"全大学不应有学区客群优势: {strengths_text}"
    # evidence 仍保留原始 schools_500m
    assert lp["evidence"]["schools_500m"] == 10
    # school_anchor_breakdown 仍输出
    sab = lp["evidence"]["school_anchor_breakdown"]
    assert sab["total"] >= 8
    # education_childcare 不应出现在 suitable 中
    assert "education_childcare" not in lp.get("suitable_business_families", [])
    print(f"T7 university-only not school zone: type={lp['primary_type']} label={lp['label']} PASS")


# T8: 小学/中学足够多 → 学区判定保留
def test_k12_schools_still_school_zone():
    rd = _base_rd()
    rd["stats_500m"]["schools"] = 8
    rd["poi_lists"] = {
        "schools": [
            {"name": "宝鸡高新第一小学"},
            {"name": "宝鸡市实验小学"},
            {"name": "宝鸡中学"},
            {"name": "某附属中学"},
            {"name": "阳光幼儿园"},
            {"name": "宝鸡文理学院"},
            {"name": "宝鸡文理学院第二校区"},
            {"name": "新东方培训中心"},
        ]
    }
    lp = compute_location_profile(rd)
    # K12 schools: elementary(2) + middle_high(2) + kindergarten(1) = 5 >= 5 → 学区判定应保留
    assert "学区" in lp["primary_type"], f"K12学校应判学区: {lp['primary_type']}"
    # strengths 应含学区客群
    strengths_text = " ".join(lp.get("strengths", []))
    assert "学区客群基础较好" in strengths_text, f"K12应有学区优势: {strengths_text}"
    # education_childcare 应出现在 suitable
    assert "education_childcare" in lp.get("suitable_business_families", [])
    # evidence 仍保留原始 schools_500m
    assert lp["evidence"]["schools_500m"] == 8
    print(f"T8 K12 schools still school zone: type={lp['primary_type']} PASS")


# T9: bus dedup — 5条线路指向同一站 → 只计1个公交站
def test_bus_dedup_same_station():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 5
    rd["poi_lists"] = {
        "bus_stops": [
            {"name": "宝鸡文理学院(上行)"},
            {"name": "宝鸡文理学院(下行)"},
            {"name": "宝鸡文理学院"},
            {"name": "宝鸡文理学院站牌东"},
            {"name": "宝鸡文理学院东侧"},
        ]
    }
    lp = compute_location_profile(rd)
    # evidence bus_500m 保留原始值
    assert lp["evidence"]["bus_500m"] == 5, "raw bus_500m 应保留原始值"
    # bus_deduped 应为1
    assert lp["evidence"]["bus_deduped"] == 1, f"dedup 后应为1，got {lp['evidence']['bus_deduped']}"
    # bus 不应出现在 anchors
    assert "公交" not in lp.get("core_anchors", []), "同一站不应视为公交锚点"
    # strengths 不应出现"公交线路"
    strengths_text = " ".join(lp.get("strengths", []))
    assert "公交" not in strengths_text, f"同一站不应写公交优势: {strengths_text}"
    print("T9 bus dedup same station: PASS")


# T10: real multi-station — 不同站名仍计多个，东区≠主站
def test_bus_multi_station():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 6
    rd["poi_lists"] = {
        "bus_stops": [
            {"name": "宝鸡文理学院"},
            {"name": "高新人民医院"},
            {"name": "高新管委会"},
            {"name": "宝鸡文理学院东区"},
            {"name": "天下汇"},
            {"name": "高新广场"},
        ]
    }
    lp = compute_location_profile(rd)
    deduped = lp["evidence"]["bus_deduped"]
    # 6个不同站 → 必须等于6，东区≠主站
    assert deduped == 6, f"6个不同站 deduped 必须等于6: got {deduped}"
    # bus 应出现在 anchors（>=5）
    assert "公交" in lp.get("core_anchors", []), f"多站应含公交锚点: {lp['core_anchors']}"
    print(f"T10 bus multi-station: deduped={deduped} PASS")


# T11: traffic_anchor_list 地铁/汽车站不得误当公交站
def test_non_bus_anchors_not_counted():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 2
    # 无 poi_lists.bus_stops，仅 traffic_anchor_list 含地铁/汽车站
    rd["traffic_anchor_list"] = [
        {"name": "高新大道地铁站", "category": "地铁站"},
        {"name": "宝鸡汽车站", "category": "汽车站"},
    ]
    result = dedup_bus_count(rd)
    assert result["deduped"] == 2, f"traffic_anchor_list 无公交站时 deduped 应回退 raw=2: {result}"
    print(f"T11 non-bus anchors not counted: {result} PASS")


# T12: traffic_anchor_list category="交通设施服务", type="公交站" → 使用站名去重
def test_bus_anchor_by_type():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 4
    rd["traffic_anchor_list"] = [
        {"name": "宝鸡文理学院(上行)", "category": "交通设施服务", "type": "公交站"},
        {"name": "宝鸡文理学院(下行)", "category": "交通设施服务", "type": "公交车站"},
        {"name": "高新管委会(上行)", "category": "交通设施服务", "type": "公交站"},
        {"name": "高新管委会(下行)", "category": "交通设施服务", "type": "公交站"},
    ]
    result = dedup_bus_count(rd)
    # 2个不同站→去重后为2，不回退 raw=4
    assert result["deduped"] == 2, f"type 含公交应触发去重: got {result}"
    print(f"T12 bus anchor by type: deduped={result['deduped']} PASS")


# T13: bus dedup cap — 站名去重后数量不得大于 raw
def test_bus_dedup_cap():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 2
    # 5 个不同站名但 raw=2 → 必须 cap 为 2
    rd["poi_lists"] = {
        "bus_stops": [
            {"name": "宝鸡文理学院"},
            {"name": "高新人民医院"},
            {"name": "高新管委会"},
            {"name": "天下汇"},
            {"name": "高新广场"},
        ]
    }
    result = dedup_bus_count(rd)
    assert result["deduped"] == 2, f"cap 后必须为2: got {result}"
    assert result["raw"] == 2
    print(f"T13 bus dedup cap: deduped={result['deduped']} (raw={result['raw']}) PASS")


def test_bus_distance_filter():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 10
    rd["poi_lists"] = {"bus_stops": [
        {"name": "站A", "distance": 300}, {"name": "站B", "distance": 450},
        {"name": "站C", "distance": 800}, {"name": "站D", "distance": 1200}]}
    r = dedup_bus_count(rd, max_distance=500)
    assert r["deduped"] == 2, f"only 2 within 500m: {r}"
    print(f"T14 distance filter: deduped={r['deduped']} PASS")


def test_bus_distance_string_parse():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 6
    rd["poi_lists"] = {"bus_stops": [
        {"name": "站A", "distance": "480m"}, {"name": "站B", "distance": "300"}]}
    r = dedup_bus_count(rd, max_distance=500)
    assert r["deduped"] == 2, f"string distances: {r}"
    print("T15 string distance parse: PASS")


def test_bus_partial_distance():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 6
    rd["poi_lists"] = {"bus_stops": [
        {"name": "站A", "distance": 300}, {"name": "站B"}, {"name": "站C", "distance": 800}]}
    r = dedup_bus_count(rd, max_distance=500)
    assert r["deduped"] == 2, f"A(300)+B(missing): {r}"
    print(f"T16 partial distance: deduped={r['deduped']} PASS")


def test_bus_distance_with_cap():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 2
    rd["poi_lists"] = {"bus_stops": [
        {"name": "站A", "distance": 300}, {"name": "站B", "distance": 400},
        {"name": "站C", "distance": 450}, {"name": "站D", "distance": 200}]}
    r = dedup_bus_count(rd, max_distance=500)
    assert r["deduped"] <= 2, f"cap at raw=2: {r}"
    print(f"T17 cap after distance: deduped={r['deduped']} PASS")


def test_bus_no_max_distance_old_behavior():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 5
    rd["poi_lists"] = {"bus_stops": [
        {"name": "宝鸡文理学院(上行)", "distance": 300},
        {"name": "宝鸡文理学院(下行)", "distance": 400},
        {"name": "高新管委会(上行)", "distance": 200},
        {"name": "高新管委会(下行)", "distance": 250},
        {"name": "高新广场", "distance": 600}]}
    r = dedup_bus_count(rd)
    assert r["deduped"] >= 2, f"old behavior: {r}"
    print(f"T18 old behavior: deduped={r['deduped']} PASS")


def test_location_fact_snapshot_consistency():
    from services.business_model_service import compute_location_fundamentals
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 2
    rd["stats_1000m"]["bus"] = 5
    rd["poi_lists"] = {"bus_stops": [
        {"name": "站A", "distance": 300}, {"name": "站B", "distance": 450},
        {"name": "站C", "distance": 800}, {"name": "站D", "distance": 1200},
        {"name": "站E", "distance": 900}]}
    snap = build_location_fact_snapshot(rd)
    lp = compute_location_profile(rd)
    lf = compute_location_fundamentals(rd)
    assert snap["bus_500m_deduped"] == 2, f"snap deduped: {snap['bus_500m_deduped']}"
    assert lp["evidence"].get("bus_deduped") == 2, f"lp deduped: {lp['evidence']}"
    lf_text = str(lf.get("summary", "")) + " " + " ".join(lf.get("strengths", []))
    assert "5个公交站" not in lf_text
    assert "5 个公交" not in lf_text
    print("T19 fact snapshot consistency: PASS")


def test_attachment_bus_not_leak_500m():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 2
    rd["stats_1000m"]["bus"] = 5
    rd["poi_lists"] = {"bus_stops": [
        {"name": "站A", "distance": 300}, {"name": "站B", "distance": 450},
        {"name": "站C", "distance": 800}, {"name": "站D", "distance": 1200},
        {"name": "站E", "distance": 900}]}
    lp = compute_location_profile(rd)
    from services.business_model_service import compute_location_fundamentals
    lf = compute_location_fundamentals(rd)
    # location_profile
    strengths = " ".join(lp.get("strengths", []))
    assert "5个公交站" not in strengths
    assert lp["evidence"].get("bus_deduped", 0) <= 2
    # location_fundamentals
    lf_text = str(lf.get("summary", "")) + " " + " ".join(lf.get("strengths", []))
    assert "5个公交站" not in lf_text
    # fallback report
    from services.fallback_report_service import build_fallback_report
    fb = build_fallback_report(rd, business_type="小吃快餐", brand_name="", store_size=50)
    from report_fact_guard import build_user_visible_report_text
    fb_text = build_user_visible_report_text(fb)
    assert "500米内5个公交" not in fb_text
    assert "500米内 5 个公交" not in fb_text
    print("T20 attachment bus not leak: PASS")


def test_fallback_uses_fact_snapshot():
    rd = _base_rd()
    rd["stats_500m"]["bus"] = 2
    rd["stats_1000m"]["bus"] = 8
    rd["poi_lists"] = {"bus_stops": [
        {"name": "站A", "distance": 300}, {"name": "站B", "distance": 450},
        {"name": "站C", "distance": 900}, {"name": "站D", "distance": 900},
        {"name": "站E", "distance": 900}]}
    from services.fallback_report_service import build_fallback_report
    from report_fact_guard import build_user_visible_report_text
    fb = build_fallback_report(rd, business_type="小吃快餐", brand_name="", store_size=50)
    text = build_user_visible_report_text(fb)
    assert "500米内5个公交" not in text
    assert "500米内 5 个公交" not in text
    # 2个在500m内的站，去重后不应超过2
    assert "500米内8个公交" not in text
    print("T21 fallback uses fact snapshot: PASS")


def test_production_paths_no_direct_dedup():
    import os
    lp_src = open(os.path.join(os.path.dirname(__file__), '..', 'services', 'location_profile_service.py'), 'r', encoding='utf-8').read()
    bm_src = open(os.path.join(os.path.dirname(__file__), '..', 'services', 'business_model_service.py'), 'r', encoding='utf-8').read()
    fb_src = open(os.path.join(os.path.dirname(__file__), '..', 'services', 'fallback_report_service.py'), 'r', encoding='utf-8').read()
    # compute_location_profile 不应直接调用 dedup_bus_count(r)（应走 helper）
    assert "dedup_bus_count(r)" not in lp_src
    # compute_location_fundamentals 不应直接调用 dedup_bus_count(real_data)
    assert "dedup_bus_count(real_data)" not in bm_src
    # fallback 不应直接调用 dedup_bus_count(real_data)["deduped"]
    assert 'dedup_bus_count(real_data)["deduped"]' not in fb_src
    print("T22 no direct dedup calls: PASS")


if __name__ == "__main__":
    test_location_profile_consistent()
    test_no_dining_as_edu_advantage()
    test_location_profile_evidence()
    test_school_classification()
    test_school_breakdown_with_data()
    test_dining_not_advantage()
    test_university_only_not_school_zone()
    test_k12_schools_still_school_zone()
    test_bus_dedup_same_station()
    test_bus_multi_station()
    test_non_bus_anchors_not_counted()
    test_bus_anchor_by_type()
    test_bus_dedup_cap()
    test_bus_distance_filter()
    test_bus_distance_string_parse()
    test_bus_partial_distance()
    test_bus_distance_with_cap()
    test_bus_no_max_distance_old_behavior()
    test_location_fact_snapshot_consistency()
    test_attachment_bus_not_leak_500m()
    test_fallback_uses_fact_snapshot()
    test_production_paths_no_direct_dedup()
    print()
    print("ALL LOCATION PROFILE TESTS PASSED")
