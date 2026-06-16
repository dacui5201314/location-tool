"""Phase 0 位置基本面规则测试"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.location_profile_service import (
    compute_location_profile, compute_school_anchor_breakdown,
    get_dining_not_advantage_families, _classify_school,
    _k12_school_count,
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


if __name__ == "__main__":
    test_location_profile_consistent()
    test_no_dining_as_edu_advantage()
    test_location_profile_evidence()
    test_school_classification()
    test_school_breakdown_with_data()
    test_dining_not_advantage()
    test_university_only_not_school_zone()
    test_k12_schools_still_school_zone()
    print()
    print("ALL LOCATION PROFILE TESTS PASSED")
