"""Phase 1 生意模型规则测试"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.fallback_report_service import build_fallback_report
from services.report_enrichment_service import enrich_report_business_context
from services.business_model_service import classify_business_model_family


def _base_rd(**overrides):
    base = {
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
    base.update(overrides)
    return base


def _edu_rd(**overrides):
    return _base_rd(
        direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
        substitute_competitors_200m=0, substitute_competitors_500m=0, substitute_competitors_1000m=0,
        traffic_anchors_200m=0, traffic_anchors_500m=2, traffic_anchors_1000m=5,
    )


# T1: 小吃快餐 200m 0 + 1000m 同类多，不能输出强优势
def test_snack_food_no_strong_advantage_zero_comp():
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=3, direct_competitors_1000m=12)
    rd["stats_1000m"]["restaurants"] = 56
    r = build_fallback_report(rd, business_type="小吃快餐", brand_name="砂锅小吃", store_size=50)
    text = json.dumps(r, ensure_ascii=False)
    for phrase in ["竞争环境宽松","先发优势","市场空白明显"]:
        assert phrase not in text, f"小吃快餐不应出现: {phrase}"
    print("T1 snack food no strong advantage: PASS")


# T2: 教育托管 0 POI 竞品, competition/category_advantage 不得 85
def test_edu_childcare_no_inflated_comp_score():
    rd = _edu_rd(
        stats_500m={"residential":4,"office":0,"schools":4,"subway":0,"bus":2,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        stats_1000m={"residential":15,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":9,"parking":28,"shopping":0,"hotels":7,"restaurants":56},
    )
    r = build_fallback_report(rd, business_type="教育培训", brand_name="小学生托管服务", store_size=200)
    comp = [d for d in r.get("dimension_scores",[]) if d["key"]=="competition"]
    cat = [d for d in r.get("dimension_scores",[]) if d["key"]=="category_advantage"]
    if comp:
        assert comp[0]["score"] < 85, f"competition should be < 85, got {comp[0]['score']}"
    if cat:
        assert cat[0]["score"] < 85, f"category_advantage should be < 85, got {cat[0]['score']}"
    print(f"T2 edu childcare scores capped: comp={comp[0]['score'] if comp else 'N/A'}, cat={cat[0]['score'] if cat else 'N/A'} PASS")


# T3: 教育托管 top_strength 不得机械写 200m 竞品 0
def test_edu_childcare_top_strength_not_mechanical():
    rd = _edu_rd(
        stats_500m={"residential":4,"office":0,"schools":4,"subway":0,"bus":2,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        stats_1000m={"residential":15,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":9,"parking":28,"shopping":0,"hotels":7,"restaurants":56},
    )
    r = build_fallback_report(rd, business_type="教育培训", brand_name="小学生托管服务", store_size=200)
    ds = r.get("decision_snapshot", {})
    ts = ds.get("top_strength", "")
    assert "直接竞争压力较小" not in ts, f"top_strength不应机械: {ts}"
    assert "暗竞品" in ts or "小饭桌" in ts or "低收录" in ts or "走访" in ts, \
        f"top_strength应包含暗竞品提示: {ts}"
    print(f"T3 edu childcare top_strength: {ts[:100]}... PASS")


# T4: 教育托管必须出现暗竞品/小饭桌/家庭托管低收录提示
def test_edu_childcare_hidden_competitor_text():
    rd = _edu_rd(
        stats_500m={"residential":4,"office":0,"schools":4,"subway":0,"bus":2,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        stats_1000m={"residential":15,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":9,"parking":28,"shopping":0,"hotels":7,"restaurants":56},
    )
    r = build_fallback_report(rd, business_type="教育培训", brand_name="小学生托管服务", store_size=200)
    text = json.dumps(r, ensure_ascii=False)
    keywords = ["暗竞品","小饭桌","家庭式托管","低收录"]
    found = [k for k in keywords if k in text]
    assert len(found) >= 1, f"应至少包含一个暗竞品关键词: found {found}"
    print(f"T4 hidden competitor text: found {found} PASS")


# T5: 教育托管 field_checklist 不得出现餐饮核验词
def test_edu_childcare_no_food_in_checklist():
    rd = _edu_rd(
        stats_500m={"residential":4,"office":0,"schools":4,"subway":0,"bus":2,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        stats_1000m={"residential":15,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":9,"parking":28,"shopping":0,"hotels":7,"restaurants":56},
    )
    r = build_fallback_report(rd, business_type="教育培训", brand_name="小学生托管服务", store_size=200)
    fc = r.get("field_checklist", [])
    titles = " ".join(item.get("title","") for item in fc)
    for w in ["外卖骑手","取餐","出餐速度","上座率","排队","午晚高峰堂食"]:
        assert w not in titles, f"教育托管checklist不应出现 '{w}'"
    print("T5 edu childcare no food in checklist: PASS")


# T6: 小吃快餐 fit/stop 锋利
def test_snack_food_fit_stop():
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=3, direct_competitors_1000m=8)
    rd["stats_1000m"]["restaurants"] = 40
    r = build_fallback_report(rd, business_type="小吃快餐", brand_name="砂锅小吃", store_size=50)
    ds = r.get("decision_snapshot", {})
    fit = ds.get("fit_condition","")
    stop = ds.get("stop_condition","")
    assert "租金" in fit and ("午市" in fit or "外卖" in fit), f"fit too weak: {fit}"
    assert "租金" in stop and ("晚餐" in stop or "外卖" in stop or "客流" in stop), f"stop too weak: {stop}"
    print("T6 snack food fit/stop: PASS")


# T7: beverage_dessert 半聚集型语义
def test_beverage_dessert_semantics():
    from services.business_model_service import load_business_model, compute_business_model_snapshot

    model = load_business_model("beverage_dessert")
    assert model, "beverage_dessert model not loaded"
    assert model["competition"]["type"] == "半聚集型", f"should be 半聚集型, got {model['competition']['type']}"

    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0)
    snap = compute_business_model_snapshot(rd, "奶茶店", "茶百道", 20)
    assert snap["model_type"] == "beverage_dessert"
    assert "business_model_version" in snap
    assert snap["business_model_version"].startswith("beverage_dessert@")

    # field_checklist 不得套用小吃快餐的"出餐速度、午市刚需"作为核心
    from services.business_model_service import build_business_field_checklist
    fc = build_business_field_checklist(rd, "奶茶店", "茶百道", 20)
    titles = " ".join(item.get("title","") for item in fc)
    assert "出餐速度" not in titles, f"茶饮checklist不应含出餐速度: {titles}"
    assert "午市刚需" not in titles
    assert "上座率" not in titles
    # 应包含步行/外卖/动线
    assert "步行" in titles or "动线" in titles or "外卖" in titles, f"应含步行/外卖/动线: {titles}"

    print(f"T7 beverage_dessert 半聚集型: version={snap['business_model_version']} PASS")


# T8: retail_convenience 排斥型语义
def test_retail_convenience_semantics():
    from services.business_model_service import load_business_model, compute_business_model_snapshot

    model = load_business_model("retail_convenience")
    assert model
    assert model["competition"]["type"] == "排斥型"

    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0)
    snap = compute_business_model_snapshot(rd, "便利店", "全家", 60)
    assert snap["model_type"] == "retail_convenience"

    from services.business_model_service import build_business_field_checklist
    fc = build_business_field_checklist(rd, "便利店", "全家", 60)
    titles = " ".join(item.get("title","") for item in fc)
    # 应包含小区入住率/出入口动线
    assert "住宅" in titles or "入住" in titles or "小区" in titles, f"应含住宅相关: {titles}"
    assert "动线" in titles, f"应含动线: {titles}"
    # 不应只为住宅数量高就推荐
    assert "推荐" not in titles

    print(f"T8 retail_convenience 排斥型: model_type={snap['model_type']} PASS")


# T9: service_beauty 暗竞品型语义
def test_service_beauty_semantics():
    from services.business_model_service import load_business_model, compute_business_model_snapshot

    model = load_business_model("service_beauty")
    assert model
    assert model["competition"]["type"] == "暗竞品型"

    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0)
    snap = compute_business_model_snapshot(rd, "美容美发", "", 40)
    assert snap["model_type"] == "service_beauty"

    from services.business_model_service import build_business_field_checklist
    fc = build_business_field_checklist(rd, "美容美发", "", 40)
    titles = " ".join(item.get("title","") for item in fc)
    # 不应出现餐饮核验项
    for w in ["外卖骑手","出餐速度","上座率","排队","午晚高峰堂食"]:
        assert w not in titles, f"美业checklist不应出现 '{w}'"
    # 应包含消费力/停车/门头/客单价
    assert "消费" in titles or "停车" in titles or "门头" in titles or "客单价" in titles, \
        f"应含消费力/停车/门头相关: {titles}"

    print(f"T9 service_beauty 暗竞品型: model_type={snap['model_type']} PASS")


if __name__ == "__main__":
    test_snack_food_no_strong_advantage_zero_comp()
    test_edu_childcare_no_inflated_comp_score()
    test_edu_childcare_top_strength_not_mechanical()
    test_edu_childcare_hidden_competitor_text()
    test_edu_childcare_no_food_in_checklist()
    test_snack_food_fit_stop()
    test_beverage_dessert_semantics()
    test_retail_convenience_semantics()
    test_service_beauty_semantics()
    print()
    print("ALL BUSINESS MODEL TESTS PASSED")
