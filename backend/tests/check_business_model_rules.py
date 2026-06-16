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


# T10: snack_fast_food 吸收规则存在性
def test_snack_food_absorbed_rules():
    from services.business_model_service import load_business_model
    model = load_business_model("snack_fast_food")
    assert model, "snack_fast_food not loaded"

    rf_text = " ".join(model.get("red_flags", []))
    # book_001: 门头遮挡/50m可视
    assert "门头" in rf_text and "50m" in rf_text, f"missing 门头50m rule: {rf_text[:100]}"
    # book_001: 午晚双高峰单一支撑
    assert "单一高峰" in rf_text or "另一时段" in rf_text, f"missing 单一时段 rule: {rf_text[:100]}"
    # book_001/book_002: 租金占比 20%
    assert "月租金超过预估月营收" in rf_text, f"missing 租金红线: {rf_text[:100]}"

    fm_text = " ".join(model.get("forbidden_misreadings", []))
    assert "金角银边" in fm_text, f"missing 金角银边: {fm_text[:100]}"
    assert "午市" in fm_text and "晚市" in fm_text, f"missing 午晚双看: {fm_text[:100]}"

    print("T10 snack_food absorbed rules: PASS")


# T11: retail_convenience 吸收规则存在性
def test_retail_convenience_absorbed_rules():
    from services.business_model_service import load_business_model
    model = load_business_model("retail_convenience")
    assert model

    rf_text = " ".join(model.get("red_flags", []))
    assert "空铺率" in rf_text or "主力店" in rf_text, f"missing 空铺/主力店: {rf_text[:100]}"

    fm_text = " ".join(model.get("forbidden_misreadings", []))
    assert "盒马" in fm_text or "店仓" in fm_text or "配送模型" in fm_text, \
        f"missing 盒马不可套用: {fm_text[:100]}"

    print("T11 retail_convenience absorbed rules: PASS")


# T12: group_dining 半聚集型语义
def test_group_dining_semantics():
    from services.business_model_service import load_business_model, compute_business_model_snapshot
    model = load_business_model("food_service")
    assert model, "food_service not loaded"
    assert model["competition"]["type"] == "半聚集型"
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0)
    snap = compute_business_model_snapshot(rd, "中餐", "湘菜馆", 120)
    assert snap["model_type"] == "food_service"
    rf_text = " ".join(model.get("red_flags", []))
    assert "停车" in rf_text or "排烟" in rf_text or "消防" in rf_text, f"missing: {rf_text[:100]}"
    assert "门头" in rf_text and "50m" in rf_text, f"missing 门头: {rf_text[:100]}"
    refs = model.get("source_refs", [])
    assert len(refs) >= 2, f"source_refs: {len(refs)}"
    print(f"T12 group_dining PASS: source_refs={len(refs)}")


# T13: education_training 聚集型
def test_education_training_semantics():
    from services.business_model_service import load_business_model, compute_business_model_snapshot
    model = load_business_model("education_training")
    assert model and model["competition"]["type"] == "聚集型"
    rd = _base_rd(direct_competitors_200m=0)
    snap = compute_business_model_snapshot(rd, "教育培训", "英语培训", 80)
    assert snap["model_type"] == "education_training"
    fm = " ".join(model.get("forbidden_misreadings", []))
    assert "托管" in fm or "午托" in fm or "小饭桌" in fm or "餐食" in fm, f"禁止托管: {fm[:100]}"
    snap2 = compute_business_model_snapshot(rd, "教育培训", "小学生托管", 100)
    assert snap2["model_type"] == "education_childcare"
    print("T13 education_training PASS")


# T14: laundry_clinic 暗竞品型
def test_laundry_clinic_semantics():
    from services.business_model_service import load_business_model, compute_business_model_snapshot
    model = load_business_model("service_basic")
    assert model and model["competition"]["type"] == "暗竞品型"
    snap = compute_business_model_snapshot(_base_rd(), "洗衣店", "", 30)
    assert snap["model_type"] == "service_basic"
    fm = " ".join(model.get("forbidden_misreadings", []))
    assert "外卖骑手" in fm or "上座率" in fm, f"禁止餐饮: {fm[:100]}"
    rf = " ".join(model.get("red_flags", []))
    assert "合规" in rf or "资质" in rf, f"合规: {rf[:100]}"
    print("T14 laundry_clinic PASS")


def test_pharmacy_semantics():
    from services.business_model_service import classify_business_model_family, load_business_model
    assert classify_business_model_family("药店", "", "") == "pharmacy"
    assert classify_business_model_family("药房", "", "") == "pharmacy"
    assert classify_business_model_family("便利店", "", "") == "retail_convenience"
    model = load_business_model("pharmacy")
    assert model and model["competition"]["type"] == "中性型"
    assert "医院" in " ".join(model.get("forbidden_misreadings", []))
    print("T15 pharmacy PASS")


def test_retail_shopping_semantics():
    from services.business_model_service import load_business_model
    model = load_business_model("retail_shopping")
    assert model and model["competition"]["type"] == "中性型"
    fm = " ".join(model.get("forbidden_misreadings", []))
    assert "孤立" in fm or "电商" in fm or "0 竞品" in fm, f"应含孤立/电商: {fm[:100]}"
    print("T16 retail_shopping PASS")


def test_hotel_semantics():
    from services.business_model_service import load_business_model
    model = load_business_model("hotel")
    assert model and model["competition"]["type"] == "聚集型"
    zp = model["competition"]["zero_competitor_policy"]
    assert "0 竞品" in zp or "不是优势" in zp
    print("T17 hotel PASS")


def test_entertainment_semantics():
    from services.business_model_service import load_business_model
    model = load_business_model("entertainment")
    assert model and model["competition"]["type"] == "聚集型"
    rf = " ".join(model.get("red_flags", []))
    assert "隔音" in rf or "消防" in rf or "扰民" in rf, f"应含隔音/消防/扰民: {rf[:100]}"
    print("T18 entertainment PASS")


def test_ph4g_catering_absorbed():
    from services.business_model_service import load_business_model
    for mid in ["snack_fast_food", "food_service"]:
        m = load_business_model(mid)
        rf = " ".join(m.get("red_flags", []))
        assert "排烟" in rf or "排污" in rf or "燃气" in rf or "消防" in rf, \
            f"{mid} missing kitchen infra: {rf[:120]}"
        fm = " ".join(m.get("forbidden_misreadings", []))
        assert "物业" in fm or "后厨" in fm or "餐饮品类" in fm or "餐饮门店" in fm, \
            f"{mid} missing category-match: {fm[:120]}"
        assert "book_003" in {r["source_id"] for r in m.get("source_refs", [])}
    print("T19 PH4G catering absorbed: PASS")


def test_ph4g_convenience_absorbed():
    from services.business_model_service import load_business_model
    m = load_business_model("retail_convenience")
    rf = " ".join(m.get("red_flags", []))
    assert "出入口" in rf or "动线" in rf, f"missing dongxian: {rf[:120]}"
    fm = " ".join(m.get("forbidden_misreadings", []))
    assert "大卖场" in fm or "覆盖半径" in fm, f"missing cvs logic: {fm[:120]}"
    assert "book_005" in {r["source_id"] for r in m.get("source_refs", [])}
    print("T20 PH4G convenience absorbed: PASS")


def test_ph4g_hotel_absorbed():
    from services.business_model_service import load_business_model
    m = load_business_model("hotel")
    rf = " ".join(m.get("red_flags", []))
    assert "商业热闹" in rf or "过夜需求" in rf, f"missing demand: {rf[:120]}"
    fm = " ".join(m.get("forbidden_misreadings", []))
    assert "价格带" in fm or "客源结构" in fm or "淡旺季" in fm, f"missing positioning: {fm[:120]}"
    hg = " ".join(m.get("hard_gates", []))
    assert "电梯" in hg or "停车" in hg or "出入口" in hg, f"missing property: {hg[:120]}"
    ref_ids = {r["source_id"] for r in m.get("source_refs", [])}
    assert "book_011" in ref_ids and "book_012" in ref_ids, f"missing hotel refs: {ref_ids}"
    print("T21 PH4G hotel absorbed: PASS")


def test_ph4h_childcare_absorbed():
    from services.business_model_service import load_business_model
    m = load_business_model("education_childcare")
    fm = " ".join(m.get("forbidden_misreadings", []))
    assert "外卖骑手" in fm or "堂食" in fm
    assert "product_review_002" in {r["source_id"] for r in m.get("source_refs", [])}
    print("T22 PH4H childcare absorbed: PASS")


def test_ph4h_training_absorbed():
    from services.business_model_service import load_business_model
    m = load_business_model("education_training")
    fm = " ".join(m.get("forbidden_misreadings", []))
    assert "托管" in fm or "午托" in fm or "小饭桌" in fm or "餐食" in fm
    assert "product_review_003" in {r["source_id"] for r in m.get("source_refs", [])}
    print("T23 PH4H training absorbed: PASS")


def test_ph4h_beauty_absorbed():
    from services.business_model_service import load_business_model
    m = load_business_model("service_beauty")
    fm = " ".join(m.get("forbidden_misreadings", []))
    assert "噪音" in fm or "气味" in fm or "宠物" in fm
    assert "product_review_004" in {r["source_id"] for r in m.get("source_refs", [])}
    print("T24 PH4H beauty absorbed: PASS")


def test_ph4h_pharmacy_absorbed():
    from services.business_model_service import load_business_model
    m = load_business_model("pharmacy")
    fm = " ".join(m.get("forbidden_misreadings", []))
    assert "医保" in fm or "GSP" in fm or "竞品少" in fm
    assert "product_review_005" in {r["source_id"] for r in m.get("source_refs", [])}
    print("T25 PH4H pharmacy absorbed: PASS")


def test_ph4h_entertainment_absorbed():
    from services.business_model_service import load_business_model
    m = load_business_model("entertainment")
    rf = " ".join(m.get("red_flags", []))
    assert "消防" in rf or "噪音" in rf or "扰民" in rf
    assert "product_review_006" in {r["source_id"] for r in m.get("source_refs", [])}
    print("T26 PH4H entertainment absorbed: PASS")


# T27: 宠物店 snapshot 必须包含物业/噪音/气味约束
def test_pet_business_snapshot_constraints():
    from services.business_model_service import compute_business_model_snapshot
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
                  stats_500m={"residential":7,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4})
    snap = compute_business_model_snapshot(rd, "宠物店", "", 60)
    assert snap["model_type"] == "service_beauty"

    # must_verify 必须包含物业/噪音/气味相关约束
    mv_text = " ".join(snap.get("must_verify", []))
    assert "物业" in mv_text, f"pet must_verify missing 物业: {mv_text}"
    assert "噪音" in mv_text, f"pet must_verify missing 噪音: {mv_text}"
    assert "气味" in mv_text, f"pet must_verify missing 气味: {mv_text}"

    # stop_condition 必须包含物业/噪音/气味
    sc = snap.get("stop_condition", "")
    assert "物业" in sc or "噪音" in sc or "气味" in sc, f"pet stop missing: {sc}"

    print("T27 pet snapshot constraints: PASS")


# T28: 美容美发 snapshot 不得强塞宠物限制
def test_non_pet_beauty_no_pet_constraints():
    from services.business_model_service import compute_business_model_snapshot
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0)
    snap = compute_business_model_snapshot(rd, "美容美发", "", 40)
    assert snap["model_type"] == "service_beauty"

    # must_verify 不得包含宠物专属的物业/排风约束
    mv_text = " ".join(snap.get("must_verify", []))
    assert "排风" not in mv_text, f"beauty must_verify should not have 排风: {mv_text}"
    assert "宠物" not in mv_text, f"beauty must_verify should not mention 宠物 exclusively: {mv_text}"

    # stop_condition 不得包含宠物专属条件
    sc = snap.get("stop_condition", "")
    assert "宠物业态" not in sc, f"beauty stop should not mention 宠物业态: {sc}"

    print("T28 non-pet beauty no pet constraints: PASS")


# T29: 宠物店 field_checklist 必须包含物业/噪音/气味
def test_pet_business_checklist_constraints():
    from services.business_model_service import build_business_field_checklist
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
                  stats_500m={"residential":7,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4})
    fc = build_business_field_checklist(rd, "宠物店", "", 60)

    # 所有 field_checklist 文本拼接
    all_text = " ".join(
        item.get("title", "") + " " + item.get("action", "") + " " +
        item.get("pass_hint", "") + " " + item.get("eliminate_hint", "")
        for item in fc
    )

    assert "物业" in all_text, f"pet checklist missing 物业: {all_text}"
    assert "噪音" in all_text, f"pet checklist missing 噪音: {all_text}"
    assert "气味" in all_text, f"pet checklist missing 气味: {all_text}"

    print("T29 pet checklist constraints: PASS")


# T30: category-only 宠物店识别 — snapshot + checklist 均需输出物业/噪音/气味
def test_pet_business_category_only():
    from services.business_model_service import compute_business_model_snapshot, build_business_field_checklist
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
                  stats_500m={"residential":7,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4})

    # business_type 不含"宠物", 仅 category 含"宠物店" — 此前会漏识别
    snap = compute_business_model_snapshot(rd, "专业生活服务", "", 60, category="宠物店")
    assert snap["model_type"] == "service_beauty"

    mv_text = " ".join(snap.get("must_verify", []))
    assert "物业" in mv_text, f"category-only pet must_verify missing 物业: {mv_text}"
    assert "噪音" in mv_text, f"category-only pet must_verify missing 噪音: {mv_text}"
    assert "气味" in mv_text, f"category-only pet must_verify missing 气味: {mv_text}"

    sc = snap.get("stop_condition", "")
    assert "物业" in sc or "噪音" in sc or "气味" in sc, f"category-only pet stop missing: {sc}"

    fc = build_business_field_checklist(rd, "专业生活服务", "", 60, category="宠物店")
    all_text = " ".join(
        item.get("title", "") + " " + item.get("action", "") + " " +
        item.get("pass_hint", "") + " " + item.get("eliminate_hint", "")
        for item in fc
    )
    assert "物业" in all_text, f"category-only pet checklist missing 物业: {all_text}"
    assert "噪音" in all_text, f"category-only pet checklist missing 噪音: {all_text}"
    assert "气味" in all_text, f"category-only pet checklist missing 气味: {all_text}"

    print("T30 category-only pet business: PASS")


# T31: 便利店 school 高 res/office 低 → 不输出"学生客群稳定"，consumer_profile 不被 school 抬高
def test_convenience_no_school_advantage():
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
                  stats_500m={"residential":2,"office":1,"schools":8,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":3})
    r = build_fallback_report(rd, business_type="便利店", brand_name="全家", store_size=60)
    text = json.dumps(r, ensure_ascii=False)
    assert "学生客群稳定" not in text, f"便利店不应出现学生客群稳定: {text[:500]}"
    assert "学生" not in text, f"便利店不应出现学生优势: {text[:500]}"
    # consumer_profile 不应被 school 抬高
    cp = [d for d in r.get("dimension_scores", []) if d["key"] == "consumer_profile"]
    if cp:
        assert cp[0]["score"] < 35, f"便利店 consumer_profile 不应被 school 抬高: {cp[0]['score']}"
    print("T31 convenience no school advantage: PASS")


# T32: 酒店 school 高 → 不输出"学生客群稳定"，consumer_profile 不被 school 抬高
def test_hotel_no_school_advantage():
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
                  stats_500m={"residential":3,"office":1,"schools":8,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4})
    r = build_fallback_report(rd, business_type="酒店", brand_name="汉庭", store_size=2000)
    text = json.dumps(r, ensure_ascii=False)
    assert "学生客群稳定" not in text, f"酒店不应出现学生客群稳定: {text[:500]}"
    cp = [d for d in r.get("dimension_scores", []) if d["key"] == "consumer_profile"]
    if cp:
        assert cp[0]["score"] < 35, f"酒店 consumer_profile 不应被 school 抬高: {cp[0]['score']}"
    print("T32 hotel no school advantage: PASS")


# T33: 小吃快餐 school 高 res/office 低 → 如出现学校客流必须带 寒暑假/晚餐/动线核验 之一
def test_snack_school_with_caveat():
    rd = _base_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
                  stats_500m={"residential":2,"office":0,"schools":8,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":5})
    r = build_fallback_report(rd, business_type="小吃快餐", brand_name="砂锅小吃", store_size=50)
    text = json.dumps(r, ensure_ascii=False)
    # 学校优势如果出现必须带至少一个核验词
    if "学校" in text:
        assert any(kw in text for kw in ["寒暑假", "晚餐", "动线核验", "午间动线"]), \
            f"小吃快餐学校优势必须带寒暑假/晚餐/动线核验: {text[:800]}"
    # 不应出现未限定的"学生客群稳定"
    assert "学生客群稳定" not in text, f"小吃快餐不应出现未限定的学生客群稳定: {text[:500]}"
    print("T33 snack school with caveat: PASS")


# T19: 全部前台 business_type 归类覆盖
# ── Master self-mapping keys (not user-facing leaf types) ──
_MASTER_SELF_KEYS = {
    "异国_中高端正餐", "火锅_烧烤", "刚需快餐小吃", "中餐正餐",
    "烘焙甜品", "精品茶饮咖啡", "商务酒店", "民宿青旅",
    "高频刚需零售", "低频目的零售", "专业生活服务", "社区基础服务",
    "夜经济娱乐", "沉浸式社交娱乐",
}

# ═════════ T19A: 前台叶子 business_type 全覆盖 ═════════
def test_leaf_business_type_coverage():
    from prompts.industry_config import BUSINESS_TYPE_TO_MASTER
    from services.business_model_service import classify_business_model_family, load_business_model

    expected_model_ids = {
        "snack_fast_food", "food_service", "beverage_dessert",
        "retail_convenience", "retail_shopping", "pharmacy",
        "education_childcare", "education_training",
        "service_beauty", "service_basic", "hotel", "entertainment",
    }

    leaf_results = {}
    for bt in sorted(BUSINESS_TYPE_TO_MASTER.keys()):
        if bt in _MASTER_SELF_KEYS:
            continue
        family = classify_business_model_family(bt, "", "")
        assert family != "generic", f"leaf type '{bt}' must not be generic"
        assert family in expected_model_ids, f"leaf '{bt}' -> '{family}'"
        leaf_results.setdefault(family, []).append(bt)

    assert classify_business_model_family("药店", "", "") == "pharmacy"
    assert classify_business_model_family("教育培训", "小学生托管", "") == "education_childcare"
    assert classify_business_model_family("教育培训", "午托", "") == "education_childcare"
    assert classify_business_model_family("教育培训", "英语培训", "") == "education_training"

    for mid in expected_model_ids:
        model = load_business_model(mid)
        assert model, f"load_business_model({mid}) empty"
    covered = {mid: len(types) for mid, types in leaf_results.items()}
    print(f"T19A leaf: {sum(covered.values())} types -> {len(covered)} models: {covered} PASS")


# ═════════ T19B: Master self-mapping 不落 generic ═════════
def test_master_keys_not_generic():
    from services.business_model_service import classify_business_model_family
    generic_masters = []
    for mk in sorted(_MASTER_SELF_KEYS):
        if classify_business_model_family(mk, "", "") == "generic":
            generic_masters.append(mk)
    # 这些 master key 文本不含对应族群的 keywords, 无法通过 classify 映射
    KNOWN_AMBIGUOUS = {
        "高频刚需零售",     # 含便利/超市/药店跨族群词, 无法唯一
        "专业生活服务",     # 不含美容/宠物/健身关键词
        "低频目的零售",     # 不含服装/数码/专卖关键词
        "社区基础服务",     # 不含洗衣/诊所/家政关键词
        "沉浸式社交娱乐",   # 不含酒吧/KTV/剧本杀等具体娱乐关键词
    }
    for mk in generic_masters:
        assert mk in KNOWN_AMBIGUOUS, f"master '{mk}' fell to generic — fix or add to KNOWN_AMBIGUOUS"
    print(f"T19B master: {len(_MASTER_SELF_KEYS)} keys, {len(generic_masters)} known-ambiguous PASS")


def test_same_location_different_business():
    from services.location_profile_service import compute_location_profile
    from services.report_enrichment_service import enrich_report_business_context
    import json
    rd = {"stats_200m":{"residential":0,"office":0,"schools":1},"stats_500m":{"residential":4,"office":0,"schools":4,"subway":0,"bus":3,"parking":6,"shopping":0,"hotels":2,"restaurants":11},"stats_1000m":{"residential":13,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":8,"parking":26,"shopping":0,"hotels":7,"restaurants":56},"direct_competitors_200m":0,"direct_competitors_500m":2,"direct_competitors_1000m":12,"substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,"traffic_anchors_200m":0,"traffic_anchors_500m":3,"traffic_anchors_1000m":8,"direct_competitor_list":[],"substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"rigor_enabled":True,"subway_applicable":True,"city_has_subway":False}
    lp = compute_location_profile(rd)
    cases = [("小吃快餐","砂锅小吃","snack_fast_food"),("教育培训","小学生托管","education_childcare"),("教育培训","英语培训","education_training"),("药店","","pharmacy"),("酒店","","hotel"),("酒吧","","entertainment")]
    for bt, bn, em in cases:
        r = {"score":50,"summary":"t","advantages":["a"],"disadvantages":["d"],"dimension_scores":[],"details":{},"action_plan":["a"]}
        e = enrich_report_business_context(r, rd, business_type=bt, brand_name=bn, store_size=50, is_fallback=True)
        assert e["location_profile"]["primary_type"] == lp["primary_type"], f"{bt}: lp mismatch"
        assert e["business_model_snapshot"]["model_type"] == em, f"{bt}: expected {em}, got {e['business_model_snapshot']['model_type']}"
        if em == "education_childcare":
            for s in (e.get("location_fundamentals",{}).get("strengths") or []):
                assert "餐饮" not in str(s), f"edu childcare: {s}"
        if em in ("hotel","entertainment","pharmacy"):
            t = json.dumps(e, ensure_ascii=False)
            for p in ["市场空白明显","先发优势","品类切入空间较好"]: assert p not in t, f"{bt}: {p}"
    print(f"T20 same location {len(cases)} businesses: PASS")


def test_yaml_keyword_classifier_consistency():
    from services.business_model_service import classify_business_model_family
    import os, yaml
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge", "business_models")
    bad = []
    for fname in sorted(os.listdir(models_dir)):
        if not fname.endswith(".yaml"): continue
        with open(os.path.join(models_dir, fname), "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        mid = raw.get("model_id", "")
        for kw in (raw.get("coverage", {}) or {}).get("keywords", [])[:3]:
            family = classify_business_model_family("", kw, "")
            if family != mid:
                bad.append((fname, kw, mid, family))
    assert bad == [], f"keyword mismatches: {bad}"
    print(f"T21 keyword-classifier: 0 mismatches PASS")


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
    test_snack_food_absorbed_rules()
    test_retail_convenience_absorbed_rules()
    test_group_dining_semantics()
    test_education_training_semantics()
    test_laundry_clinic_semantics()
    test_pharmacy_semantics()
    test_retail_shopping_semantics()
    test_hotel_semantics()
    test_entertainment_semantics()
    test_ph4g_catering_absorbed()
    test_ph4g_convenience_absorbed()
    test_ph4g_hotel_absorbed()
    test_ph4h_childcare_absorbed()
    test_ph4h_training_absorbed()
    test_ph4h_beauty_absorbed()
    test_ph4h_pharmacy_absorbed()
    test_ph4h_entertainment_absorbed()
    test_pet_business_snapshot_constraints()
    test_non_pet_beauty_no_pet_constraints()
    test_pet_business_checklist_constraints()
    test_pet_business_category_only()
    test_convenience_no_school_advantage()
    test_hotel_no_school_advantage()
    test_snack_school_with_caveat()
    test_leaf_business_type_coverage()
    test_master_keys_not_generic()
    test_same_location_different_business()
    test_yaml_keyword_classifier_consistency()
    print()
    print("ALL BUSINESS MODEL TESTS PASSED")


# T19: 全部前台 business_type 归类覆盖
