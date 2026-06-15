"""
P1 生意模型质量回归测试。

覆盖：
1. 所有业态都能归类到模型族群
2. 教育/托管 fallback 不含餐饮核验词
3. 教育/托管 field_checklist 包含托管核心核验项
4. 教育/托管 0竞品不得输出市场空白/品类切入/先发优势
5. 餐饮 200m 0竞品但1000m同类多时不得输出竞争宽松/先发优势
6. 小吃快餐结论表达低租金/午市/外卖成立条件
7. 同一 real_data 切换 business_type 时 location_fundamentals 一致
8. HTML 渲染包含 fallback 标识/evidence_summary/caliber_explanation/data_boundary
9. 数据充分度表达克制
"""
import json as _json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _int(v, default=0):
    try: return int(v)
    except: return default


# ═══════════════════════════════════════════════
# 测试数据
# ═══════════════════════════════════════════════

def _base_rd(**overrides):
    """九悦香都地址的典型 real_data。"""
    base = {
        "stats_200m": {"residential": 0, "office": 0, "schools": 1, "hospitals": 0,
                       "subway": 0, "bus": 0, "parking": 1, "shopping": 0, "hotels": 0,
                       "restaurants": 2, "cafe_tea": 0},
        "stats_500m": {"residential": 4, "office": 0, "schools": 4, "hospitals": 0,
                       "subway": 0, "bus": 3, "parking": 6, "shopping": 0, "hotels": 2,
                       "restaurants": 11, "cafe_tea": 1},
        "stats_1000m": {"residential": 13, "office": 0, "schools": 9, "hospitals": 1,
                        "subway": 0, "bus": 8, "parking": 26, "shopping": 0, "hotels": 7,
                        "restaurants": 56, "cafe_tea": 9, "banks": 2, "convenience": 0},
        "direct_competitors_200m": 0, "direct_competitors_500m": 2, "direct_competitors_1000m": 12,
        "substitute_competitors_200m": 0, "substitute_competitors_500m": 0, "substitute_competitors_1000m": 0,
        "traffic_anchors_200m": 0, "traffic_anchors_500m": 3, "traffic_anchors_1000m": 8,
        "direct_competitor_list": [
            {"name": "尤家八亩沟擀面皮(朝阳华城店)", "distance": 400},
            {"name": "彩虹美味小吃", "distance": 450},
            {"name": "老八米线卧龙寺店", "distance": 600},
        ],
        "direct_competitor_list_200m": [],
        "direct_competitor_list_500m": [
            {"name": "尤家八亩沟擀面皮(朝阳华城店)", "distance": 400},
            {"name": "彩虹美味小吃", "distance": 450},
        ],
        "direct_competitor_list_1000m": [
            {"name": "尤家八亩沟擀面皮(朝阳华城店)", "distance": 400},
            {"name": "彩虹美味小吃", "distance": 450},
            {"name": "老八米线卧龙寺店", "distance": 600},
        ],
        "substitute_list": [],
        "traffic_anchor_list": [],
        "poi_lists": {},
        "hot_brands": [],
        "nearby_roads": [],
        "rigor_enabled": False,
        "subway_applicable": True,
        "city_has_subway": False,
    }
    base.update(overrides)
    return base


_EDUCATION_RD = {
    "stats_200m": {"residential": 0, "office": 0, "schools": 1, "hospitals": 0,
                   "subway": 0, "bus": 0, "parking": 1, "shopping": 0, "hotels": 0,
                   "restaurants": 2, "cafe_tea": 0},
    "stats_500m": {"residential": 4, "office": 0, "schools": 4, "hospitals": 0,
                   "subway": 0, "bus": 2, "parking": 6, "shopping": 0, "hotels": 2,
                   "restaurants": 11, "cafe_tea": 1},
    "stats_1000m": {"residential": 15, "office": 0, "schools": 9, "hospitals": 1,
                    "subway": 0, "bus": 9, "parking": 28, "shopping": 0, "hotels": 7,
                    "restaurants": 56, "cafe_tea": 9, "banks": 2, "convenience": 0},
    "direct_competitors_200m": 0, "direct_competitors_500m": 0, "direct_competitors_1000m": 0,
    "substitute_competitors_200m": 0, "substitute_competitors_500m": 0, "substitute_competitors_1000m": 0,
    "traffic_anchors_200m": 0, "traffic_anchors_500m": 2, "traffic_anchors_1000m": 5,
    "direct_competitor_list": [],
    "direct_competitor_list_200m": [],
    "direct_competitor_list_500m": [],
    "direct_competitor_list_1000m": [],
    "substitute_list": [],
    "traffic_anchor_list": [],
    "poi_lists": {},
    "hot_brands": [],
    "nearby_roads": [],
    "rigor_enabled": False,
    "subway_applicable": True,
    "city_has_subway": False,
}


# ═══════════════════════════════════════════════
# T1: 所有业态归类测试
# ═══════════════════════════════════════════════
def test_classify_all_business_types():
    from services.business_model_service import classify_business_model_family

    cases = [
        ("小餐饮", "", "snack_fast_food"),
        ("小吃快餐", "", "snack_fast_food"),
        ("面馆", "", "snack_fast_food"),
        ("麻辣烫", "", "snack_fast_food"),
        ("砂锅小吃", "", "snack_fast_food"),
        ("炸鸡店", "", "snack_fast_food"),
        ("奶茶店", "", "beverage_dessert"),
        ("咖啡店", "", "beverage_dessert"),
        ("中餐", "", "food_service"),
        ("火锅店", "", "food_service"),
        ("西餐", "", "food_service"),
        ("便利店", "", "retail_convenience"),
        ("超市", "", "retail_convenience"),
        ("药店", "", "retail_convenience"),
        ("生鲜店", "", "retail_convenience"),
        ("服装店", "", "retail_shopping"),
        ("数码店", "", "retail_shopping"),
        ("美容美发", "", "service_beauty"),
        ("宠物店", "", "service_beauty"),
        ("健身房", "", "service_beauty"),
        ("洗衣店", "", "service_basic"),
        ("诊所", "", "service_basic"),
        ("酒店", "", "hotel"),
        ("民宿", "", "hotel"),
        ("酒吧", "", "entertainment"),
        ("KTV", "", "entertainment"),
        ("剧本杀", "", "entertainment"),
        # 教育托管类（优先于教育普通类）
        ("教育培训", "小学生托管服务", "education_childcare"),
        ("教育培训", "小饭桌", "education_childcare"),
        ("教育培训", "作业辅导", "education_childcare"),
        ("教育培训", "午托", "education_childcare"),
        ("教育培训", "晚托", "education_childcare"),
        ("教育培训", "课后服务", "education_childcare"),
        # 教育非托管
        ("教育培训", "英语培训", "education_training"),
        ("教育培训", "美术培训", "education_training"),
        ("琴行", "", "education_training"),
        # 通用
        ("未知业态", "", "generic"),
    ]

    for bt, bn, expected in cases:
        result = classify_business_model_family(bt, bn)
        assert result == expected, f"classify({bt}, {bn}) = {result}, expected {expected}"
    print(f"T1 classify_all: {len(cases)} PASS")


# ═══════════════════════════════════════════════
# T2: 教育托管 fallback 不含餐饮核验词
# ═══════════════════════════════════════════════
def test_education_childcare_no_food_words():
    from services.fallback_report_service import build_fallback_report

    FOOD_BANNED = [
        "外卖骑手", "取餐", "出餐速度", "上座率", "排队",
        "午晚高峰堂食", "午高峰堂食", "晚高峰堂食",
    ]

    rd = _base_rd(**_EDUCATION_RD)
    report = build_fallback_report(rd, address="九悦香都",
                                   business_type="教育培训",
                                   brand_name="小学生课后托管服务就餐与作业辅导",
                                   store_size=100)

    # 扫描 report JSON 中所有字符串
    report_text = _json.dumps(report, ensure_ascii=False)

    for word in FOOD_BANNED:
        assert word not in report_text, f"教育托管报告不应出现 '{word}'"

    # 必须出现托管核心词
    childcare_required = ["托管", "放学"]
    found = []
    for w in childcare_required:
        if w in report_text:
            found.append(w)
    assert len(found) >= 1, f"教育托管报告应至少包含 {childcare_required} 之一"

    print("T2 edu_childcare no food words: PASS")


# ═══════════════════════════════════════════════
# T3: 教育托管 field_checklist 包含核心核验项
# ═══════════════════════════════════════════════
def test_education_childcare_checklist():
    from services.fallback_report_service import build_fallback_report

    rd = _base_rd(**_EDUCATION_RD)
    report = build_fallback_report(rd, address="九悦香都",
                                   business_type="教育培训",
                                   brand_name="小学生课后托管服务就餐与作业辅导",
                                   store_size=100)

    fc = report.get("field_checklist", [])
    assert len(fc) >= 5, f"field_checklist 至少5条，实际{len(fc)}"

    titles = " ".join(item.get("title", "") for item in fc)
    actions = " ".join(item.get("action", "") for item in fc)
    combined = titles + " " + actions

    required = [
        ("放学动线", "放学"),
        ("家长接送/临停", "接送"),
        ("合规/消防/食品/安全", "消防"),
        ("托管/小饭桌暗竞品走访", "暗竞品"),
        ("空间分区", "空间"),
    ]

    for name, kw in required:
        assert kw in combined, f"field_checklist 应包含 '{name}' (keyword: {kw})"

    print(f"T3 edu_childcare checklist: {len(fc)} items, ALL required present")


# ═══════════════════════════════════════════════
# T4: 教育托管 0竞品不得输出强优势表达
# ═══════════════════════════════════════════════
def test_education_childcare_zero_competitor_safe():
    from services.fallback_report_service import build_fallback_report

    DANGER_PHRASES = [
        "品类切入空间较好",
        "市场空白明显",
        "先发优势明显",
        "先发优势",
    ]

    REQUIRED_CAUTION = [
        "POI可能漏收录",
        "需现场走访",
        "POI 可能漏收录",
        "需现场走访确认",
    ]

    rd = _base_rd(**_EDUCATION_RD)
    # 确保0竞品
    rd["direct_competitors_200m"] = 0
    rd["direct_competitors_500m"] = 0
    rd["direct_competitors_1000m"] = 0

    report = build_fallback_report(rd, address="九悦香都",
                                   business_type="教育培训",
                                   brand_name="小学生托管服务",
                                   store_size=100)

    report_text = _json.dumps(report, ensure_ascii=False)

    for phrase in DANGER_PHRASES:
        assert phrase not in report_text, f"教育托管0竞品不得出现 '{phrase}'"

    # 至少有一种保守表达
    found_caution = any(p in report_text for p in REQUIRED_CAUTION)
    assert found_caution, f"教育托管0竞品必须包含保守提示: {REQUIRED_CAUTION}"

    print("T4 edu_childcare zero competitor safe: PASS")


# ═══════════════════════════════════════════════
# T5: 小吃快餐 200m 0竞品但1000m同类多时表达谨慎
# ═══════════════════════════════════════════════
def test_snack_food_200m_zero_but_1000m_many():
    from services.fallback_report_service import build_fallback_report

    DANGER_PHRASES = [
        "竞争环境宽松",
        "先发优势明显",
        "先发优势",
    ]

    rd = _base_rd(
        direct_competitors_200m=0,
        direct_competitors_500m=3,
        direct_competitors_1000m=12,
    )

    report = build_fallback_report(rd, address="九悦香都",
                                   business_type="小吃快餐",
                                   brand_name="砂锅小吃店",
                                   store_size=50)

    report_text = _json.dumps(report, ensure_ascii=False)

    for phrase in DANGER_PHRASES:
        assert phrase not in report_text, f"小吃快餐200m0竞品但1000m多时不得出现 '{phrase}'"

    # 应提示远场竞争或需要验证
    assert "远场" in report_text or "辐射" in report_text or "1000米" in report_text, \
        "应提示远场同类供给"

    # competition score 不能太高（12家远场竞品时）
    comp_dim = [d for d in report.get("dimension_scores", []) if d.get("key") == "competition"]
    if comp_dim:
        cs = comp_dim[0].get("score", 0)
        assert cs <= 75, f"competition score should be capped when 1000m has 12 competitors, got {cs}"

    print("T5 snack food 200m 0 but 1000m many: PASS")


# ═══════════════════════════════════════════════
# T6: 小吃快餐结论锋利（fit/stop）
# ═══════════════════════════════════════════════
def test_snack_food_fit_stop_sharp():
    from services.fallback_report_service import build_fallback_report
    from services.report_decision_service import compute_decision_snapshot

    rd = _base_rd(
        direct_competitors_200m=0,
        direct_competitors_500m=3,
        direct_competitors_1000m=8,
    )

    # fallback report
    report = build_fallback_report(rd, address="九悦香都",
                                   business_type="小吃快餐",
                                   brand_name="砂锅小吃",
                                   store_size=40)

    ds = report.get("decision_snapshot", {})
    fit = ds.get("fit_condition", "")
    stop = ds.get("stop_condition", "")

    # fit 至少包含两个小吃快餐核心要素
    fit_elements = ["租金", "午市", "外卖", "小档口", "低人工", "低租金"]
    fit_hits = sum(1 for e in fit_elements if e in fit)
    assert fit_hits >= 2, f"fit_condition 应包含至少2个小吃快餐核心要素: {fit}"

    # stop 至少包含两个降级要素
    stop_elements = ["租金高", "晚餐", "外卖", "客流", "高租金"]
    stop_hits = sum(1 for e in stop_elements if e in stop)
    assert stop_hits >= 2, f"stop_condition 应包含至少2个降级要素: {stop}"

    print(f"T6 snack food fit/stop sharp: fit={fit[:60]}... stop={stop[:60]}...")


# ═══════════════════════════════════════════════
# T7: 同一地址不同业态 location_fundamentals 一致
# ═══════════════════════════════════════════════
def test_location_fundamentals_consistency():
    from services.business_model_service import compute_location_fundamentals

    rd = _base_rd()

    lf1 = compute_location_fundamentals(rd)
    lf2 = compute_location_fundamentals(rd)

    assert lf1["label"] == lf2["label"]
    assert lf1["summary"] == lf2["summary"]
    assert lf1["strengths"] == lf2["strengths"]
    assert lf1["risks"] == lf2["risks"]

    # 切换业态不影响地点基本面
    rd2 = _base_rd(**{k: v for k, v in _EDUCATION_RD.items()
                       if not k.startswith("direct_competitor")})
    lf3 = compute_location_fundamentals(rd2)
    assert lf1["label"] == lf3["label"], f"location label should be same: {lf1['label']} vs {lf3['label']}"

    print(f"T7 location_fundamentals consistency: label='{lf1['label']}' PASS")


# ═══════════════════════════════════════════════
# T8: HTML 渲染包含核心模块
# ═══════════════════════════════════════════════
def test_html_renders_all_modules():
    from services.storage_service import _build_report_html
    from services.fallback_report_service import build_fallback_report

    rd = _base_rd(**_EDUCATION_RD)
    report = build_fallback_report(rd, address="九悦香都",
                                   business_type="教育培训",
                                   brand_name="小学生托管服务",
                                   store_size=100)

    report["business_type"] = "教育培训"
    report["generated_at"] = "2026-06-15 10:00"

    html = _build_report_html(1, report, "九悦香都", "小学生托管")

    required_modules = [
        "保守版数据摘要",       # fallback 标识
        "选址决策参考",          # decision_snapshot
        "地点基本面",            # location_fundamentals
        "行业生意模型",          # business_model_snapshot
        "竞品口径说明",          # caliber_explanation
        "关键证据摘要",          # evidence_summary
        "现场核验清单",          # field_checklist
        "数据说明与风险提示",    # data_boundary
        "经营建议",              # action_plan
    ]

    for mod in required_modules:
        assert mod in html, f"HTML 缺少模块: '{mod}'"

    print(f"T8 HTML all modules: {len(required_modules)} modules all present")


# ═══════════════════════════════════════════════
# T9: 数据充分度文案克制
# ═══════════════════════════════════════════════
def test_data_sufficiency_wording():
    from services.report_quality_service import assess_data_sufficiency

    # sufficient
    rd_suff = _base_rd()
    rd_suff["rigor_enabled"] = True
    ds = assess_data_sufficiency(rd_suff, business_type="小餐饮",
                                 rigor_enabled=True, is_fallback=False)
    assert "经营数据待现场核验" in ds["summary"], f"sufficient 应提示经营数据待核验: {ds['summary']}"
    assert "数据较充分" not in ds["label"] or ds["summary"] != "核心竞品和客流数据可用，可用于选址初筛", \
        "sufficient 不应再使用旧文案"

    # moderate
    ds2 = assess_data_sufficiency(rd_suff, business_type="小餐饮",
                                  rigor_enabled=False, is_fallback=True)
    assert ds2["level"] in ("moderate", "insufficient"), f"fallback 最高 moderate: {ds2['level']}"
    assert "初筛" in ds2["summary"] or "保守" in ds2["summary"], \
        f"moderate/insufficient 应提示初筛或保守: {ds2['summary']}"

    # 教育托管补充提示
    ds3 = assess_data_sufficiency(_EDUCATION_RD, business_type="教育培训",
                                  rigor_enabled=False, is_fallback=True,
                                  brand_name="小学生托管服务")
    reasons_text = " ".join(ds3.get("reasons", []))
    assert "托管" in reasons_text or "合规" in reasons_text, \
        f"教育托管应补充托管竞品/合规提示: {reasons_text}"

    print("T9 data_sufficiency wording: PASS")


# ═══════════════════════════════════════════════
# T10: 非餐饮非教育业态不被托管/小吃模板误伤
# ═══════════════════════════════════════════════
def test_non_food_non_edu_not_misclassified():
    from services.business_model_service import classify_business_model_family, \
        compute_business_model_snapshot

    # 便利店
    assert classify_business_model_family("便利店", "") == "retail_convenience"
    snap = compute_business_model_snapshot(_base_rd(), "便利店", "社区便利店", 60)
    assert snap["model_type"] == "retail_convenience"

    # 美容美发
    assert classify_business_model_family("美容美发", "") == "service_beauty"
    snap2 = compute_business_model_snapshot(_base_rd(), "美容美发", "", 40)
    assert snap2["model_type"] == "service_beauty"

    # 酒店
    assert classify_business_model_family("酒店", "") == "hotel"
    snap3 = compute_business_model_snapshot(_base_rd(), "酒店", "汉庭酒店", 2000)
    assert snap3["model_type"] == "hotel"

    print("T10 non-food non-edu not misclassified: PASS")


# ═══════════════════════════════════════════════
# T11: competition/category_advantage 不虚高
# ═══════════════════════════════════════════════
def test_competition_score_not_inflated():
    from services.fallback_report_service import build_fallback_report

    # 教育托管：住宅少、学校少、0竞品 → competition 不能满分
    rd_weak_edu = _base_rd(**_EDUCATION_RD)
    rd_weak_edu["stats_500m"]["residential"] = 2
    rd_weak_edu["stats_500m"]["schools"] = 1
    rd_weak_edu["direct_competitors_200m"] = 0
    rd_weak_edu["direct_competitors_500m"] = 0
    rd_weak_edu["direct_competitors_1000m"] = 0

    report = build_fallback_report(rd_weak_edu, address="弱位置",
                                   business_type="教育培训",
                                   brand_name="小学生托管",
                                   store_size=100)

    comp = [d for d in report.get("dimension_scores", []) if d["key"] == "competition"]
    cag = [d for d in report.get("dimension_scores", []) if d["key"] == "category_advantage"]

    if comp:
        cs = comp[0]["score"]
        assert cs < 85, f"弱需求+0竞品时competition不应满分级: got {cs}"
    if cag:
        cas = cag[0]["score"]
        assert cas < 85, f"教育托管弱需求时category_advantage不应85: got {cas}"

    print(f"T11 competition not inflated: comp={comp[0]['score'] if comp else 'N/A'}, cat={cag[0]['score'] if cag else 'N/A'}")


# ═══════════════════════════════════════════════
# T12: 生意模型快照包含必核验项 + fit/stop
# ═══════════════════════════════════════════════
def test_business_model_snapshot_fields():
    from services.business_model_service import compute_business_model_snapshot

    for bt, bn, family in [
        ("小吃快餐", "砂锅小吃", "snack_fast_food"),
        ("教育培训", "小学生托管", "education_childcare"),
        ("教育培训", "英语培训", "education_training"),
        ("便利店", "", "retail_convenience"),
        ("美容美发", "", "service_beauty"),
        ("酒店", "", "hotel"),
    ]:
        snap = compute_business_model_snapshot(_base_rd(), bt, bn, 50)
        assert snap.get("model_type") == family, f"{bt}/{bn} model_type: {snap.get('model_type')} != {family}"
        assert snap.get("core_logic"), f"{bt} 缺少 core_logic"
        assert snap.get("must_verify"), f"{bt} 缺少 must_verify"
        assert len(snap.get("must_verify", [])) >= 2, f"{bt} must_verify 至少2条"
        assert snap.get("fit_condition"), f"{bt} 缺少 fit_condition"
        assert snap.get("stop_condition"), f"{bt} 缺少 stop_condition"

    print("T12 business_model_snapshot fields: 6 families verified")


# ═══════════════════════════════════════════════
# T13: fallback 全业态 guard 通过 + 教育托管不含餐饮词
# ═══════════════════════════════════════════════
def test_all_families_fallback_clean():
    from services.fallback_report_service import build_fallback_report

    FOOD_BANNED = ["外卖骑手", "出餐速度", "上座率", "午晚高峰堂食"]

    families = [
        ("小吃快餐", "砂锅小吃", 50, "snack_fast_food"),
        ("教育培训", "小学生托管", 100, "education_childcare"),
        ("教育培训", "英语培训", 80, "education_training"),
        ("便利店", "社区便利店", 60, "retail_convenience"),
        ("美容美发", "", 40, "service_beauty"),
        ("酒店", "汉庭酒店", 2000, "hotel"),
        ("酒吧", "", 200, "entertainment"),
    ]

    for bt, bn, size, family in families:
        report = build_fallback_report(_base_rd(), address="测",
                                       business_type=bt, brand_name=bn,
                                       store_size=size)
        text = _json.dumps(report, ensure_ascii=False)

        if family == "education_childcare":
            for w in FOOD_BANNED:
                assert w not in text, f"{bt}/{bn} 不应出现 '{w}'"

        # 确保 report_type 存在
        assert report.get("report_type") == "fallback", f"{bt} report_type missing"

        # 确保 caliber_explanation 存在
        assert report.get("caliber_explanation"), f"{bt} caliber_explanation missing"

        # 确保 evidence_summary 存在
        assert report.get("evidence_summary"), f"{bt} evidence_summary missing"

        # 确保 data_boundary 存在
        assert report.get("data_boundary"), f"{bt} data_boundary missing"

    print("T13 all families fallback clean: 7 families verified")


# ═══════════════════════════════════════════════
# T14: category-only 托管识别
# ═══════════════════════════════════════════════
def test_category_only_childcare():
    from services.business_model_service import classify_business_model_family

    # brand_name 为空，但 category 包含托管关键词 → 应识别为 education_childcare
    r = classify_business_model_family("教育培训", "", category="小学生课后托管服务就餐与作业辅导")
    assert r == "education_childcare", f"category-only childcare should be education_childcare, got {r}"

    # brand_name 和 category 都为空 → education_training
    r2 = classify_business_model_family("教育培训", "", "")
    assert r2 == "education_training", f"plain 教育培训 should be education_training, got {r2}"

    # category 包含小饭桌 → education_childcare
    r3 = classify_business_model_family("", "", category="小饭桌午托晚托")
    assert r3 == "education_childcare", f"category 小饭桌 should be education_childcare, got {r3}"

    print("T14 category-only childcare: PASS")


# ═══════════════════════════════════════════════
# T15: normal/retry enrichment 包含所有 P1 模块
# ═══════════════════════════════════════════════
def test_enrichment_all_modules():
    from services.report_enrichment_service import enrich_report_business_context

    rd = _base_rd(
        direct_competitors_200m=2, direct_competitors_500m=5, direct_competitors_1000m=8,
    )

    # 模拟 normal 报告（只有 LLM 字段，没有 P1 字段）
    normal_report = {
        "score": 55,
        "summary": "test summary",
        "advantages": ["adv1", "adv2"],
        "disadvantages": ["dis1"],
        "dimension_scores": [],
        "details": {},
        "action_plan": ["action1", "action2"],
    }

    enriched = enrich_report_business_context(
        normal_report, rd,
        business_type="小吃快餐", brand_name="砂锅小吃",
        store_size=50, is_fallback=False)

    required = [
        "location_fundamentals",
        "business_model_snapshot",
        "caliber_explanation",
        "evidence_summary",
        "data_boundary",
        "revenue_disclaimer",
    ]
    for key in required:
        assert enriched.get(key), f"enriched normal report missing {key}"
        assert isinstance(enriched[key], (dict, str)), f"{key} wrong type: {type(enriched[key])}"

    # revenue_disclaimer 应包含小吃快餐关键词
    rd_text = enriched["revenue_disclaimer"]
    assert "出餐" in rd_text or "外卖" in rd_text, f"snack food disclaimer: {rd_text}"

    # 重复调用应为幂等
    enriched2 = enrich_report_business_context(enriched, rd, business_type="小吃快餐")
    assert enriched2["location_fundamentals"] is enriched["location_fundamentals"]
    assert enriched2["revenue_disclaimer"] == enriched["revenue_disclaimer"]

    print("T15 enrichment all modules: PASS")


# ═══════════════════════════════════════════════
# T16: revenue_disclaimer 存在且按业态不同
# ═══════════════════════════════════════════════
def test_revenue_disclaimer_per_family():
    from services.fallback_report_service import build_fallback_report

    # 小吃快餐: 应包含出餐/外卖
    r1 = build_fallback_report(_base_rd(
        direct_competitors_500m=3, direct_competitors_1000m=8,
    ), address="test", business_type="小吃快餐", brand_name="砂锅小吃", store_size=50)
    assert "revenue_disclaimer" in r1
    assert "出餐" in r1["revenue_disclaimer"] or "外卖" in r1["revenue_disclaimer"]

    # 教育托管: 不应包含出餐/外卖
    r2 = build_fallback_report(_base_rd(**_EDUCATION_RD), address="test",
                               business_type="教育培训", brand_name="小学生托管", store_size=100)
    assert "revenue_disclaimer" in r2
    assert "出餐" not in r2["revenue_disclaimer"]
    assert "外卖" not in r2["revenue_disclaimer"]
    assert "目标小学" in r2["revenue_disclaimer"] or "生源" in r2["revenue_disclaimer"]

    # 酒店
    r3 = build_fallback_report(_base_rd(), address="test",
                               business_type="酒店", brand_name="汉庭", store_size=2000)
    assert "revenue_disclaimer" in r3
    assert "入住率" in r3["revenue_disclaimer"] or "ADR" in r3["revenue_disclaimer"] or "OTA" in r3["revenue_disclaimer"]

    print("T16 revenue_disclaimer per family: PASS")


# ═══════════════════════════════════════════════
# T17: 全部 12 个模型族群覆盖 business_model_snapshot + field_checklist
# ═══════════════════════════════════════════════
def test_all_12_families_coverage():
    from services.business_model_service import (
        classify_business_model_family,
        compute_business_model_snapshot,
        build_business_field_checklist,
    )

    expected_families = {
        "snack_fast_food", "education_childcare", "education_training",
        "food_service", "beverage_dessert", "retail_convenience",
        "retail_shopping", "service_beauty", "service_basic",
        "hotel", "entertainment", "generic",
    }

    test_cases = [
        ("小吃快餐", "砂锅", ""),
        ("教育培训", "小学生托管", ""),
        ("教育培训", "英语培训", ""),
        ("中餐", "湘菜馆", ""),
        ("奶茶店", "一点点", ""),
        ("便利店", "全家", ""),
        ("服装店", "优衣库", ""),
        ("美容美发", "", ""),
        ("洗衣店", "", ""),
        ("酒店", "汉庭", ""),
        ("酒吧", "精酿酒吧", ""),
        ("未知业态", "", ""),
    ]

    rd = _base_rd()
    tested_families = set()

    for bt, bn, cat in test_cases:
        family = classify_business_model_family(bt, bn, cat)
        tested_families.add(family)

        snap = compute_business_model_snapshot(rd, bt, bn, 50)
        assert snap.get("model_type") == family
        assert snap.get("core_logic")
        assert snap.get("must_verify")
        assert len(snap.get("must_verify", [])) >= 2

        fc = build_business_field_checklist(rd, bt, bn, 50)
        assert isinstance(fc, list)
        assert len(fc) >= 3, f"{bt}/{bn} field_checklist too short: {len(fc)}"
        for item in fc:
            assert item.get("title"), f"{bt} checklist item missing title"

    missing = expected_families - tested_families
    assert not missing, f"Missing families: {missing}"
    print(f"T17 all {len(expected_families)} families covered: PASS")


# ═══════════════════════════════════════════════
# T18: 教育托管 brand_name 空但 category=托管 → 不得有餐饮词
# ═══════════════════════════════════════════════
def test_education_childcare_category_only_no_food():
    from services.fallback_report_service import build_fallback_report
    import json as _json

    FOOD_BANNED = ["外卖骑手", "取餐", "出餐速度", "上座率", "午晚高峰堂食"]

    rd = _base_rd(**_EDUCATION_RD)
    # brand_name 为空
    report = build_fallback_report(rd, address="test",
                                   business_type="教育培训",
                                   brand_name="",  # 空！
                                   store_size=100)

    text = _json.dumps(report, ensure_ascii=False)
    for w in FOOD_BANNED:
        assert w not in text, f"brand_name=空的教育培训不应出现 '{w}'"

    print("T18 edu childcare no brand no food words: PASS")


# ═══════════════════════════════════════════════
# T19: HTML 使用 report 中的 revenue_disclaimer
# ═══════════════════════════════════════════════
def test_html_uses_revenue_disclaimer():
    from services.storage_service import _build_report_html

    unique_marker = "TEST_MARKER_ABCD1234"
    report = {
        "score": 60, "summary": "test",
        "decision_snapshot": {"verdict": "test-v", "one_sentence": "test", "score": 60},
        "data_sufficiency": {"level": "moderate", "label": "test", "summary": "test"},
        "generated_at": "2026-06-15 10:00",
        "business_type": "snack_food",
        "revenue_disclaimer": f"disclaimer with {unique_marker}",
        "dimension_scores": [{"key": "competition", "label": "c", "score": 60}],
        "details": {"competition": "test detail"},
    }
    html = _build_report_html(1, report, "addr", "brand")
    assert unique_marker in html, f"HTML should use report revenue_disclaimer, marker not found: {unique_marker}"
    print("T19 HTML uses revenue_disclaimer: PASS")


# ═══════════════════════════════════════════════
# T20: 全部 12 族群 strict guard 检查通过
# ═══════════════════════════════════════════════
def test_all_families_strict_guard_clean():
    from services.fallback_report_service import build_fallback_report
    from services.poi_name_guard import check_poi_name_hallucination
    import json as _json

    cases = [
        ("小吃快餐", "砂锅小吃", 50),
        ("教育培训", "小学生托管", 100),
        ("教育培训", "英语培训", 80),
        ("中餐", "湘菜馆", 120),
        ("精品茶饮", "星巴克咖啡", 20),
        ("商超零售", "全家", 60),
        ("购物零售", "", 80),
        ("生活服务", "", 40),
        ("生活服务", "", 30),
        ("住宿酒店", "汉庭", 2000),
        ("休闲娱乐", "", 200),
        ("通用业态", "", 50),
    ]

    rd = _base_rd(
        direct_competitors_200m=1, direct_competitors_500m=3, direct_competitors_1000m=5,
    )

    for bt, bn, size in cases:
        report = build_fallback_report(rd, address="test",
                                       business_type=bt, brand_name=bn,
                                       store_size=size)
        fb_text = (
            _json.dumps(report.get("details", {}) or {}, ensure_ascii=False) + " " +
            _json.dumps(report.get("advantages", []), ensure_ascii=False) + " " +
            _json.dumps(report.get("disadvantages", []), ensure_ascii=False) + " " +
            _json.dumps(report.get("executive_summary", {}) or {}, ensure_ascii=False) + " " +
            str(report.get("summary", ""))
        )
        p0 = check_poi_name_hallucination(fb_text, rd, strict=True)
        assert not p0, f"{bt}/{bn} strict guard failed: {p0[:2]}"

    print(f"T20 all {len(cases)} families strict guard: PASS")


# ═══════════════════════════════════════════════
# T21: category-only 教育托管全模块一致性
# ═══════════════════════════════════════════════
def test_category_only_childcare_all_modules():
    from services.report_enrichment_service import enrich_report_business_context
    import json as _json

    rd = _base_rd(**_EDUCATION_RD)
    # 关键场景: business_type=教育培训, brand_name="", category=托管描述
    report = {
        "score": 47, "summary": "test",
        "advantages": ["a1"], "disadvantages": ["d1"],
        "dimension_scores": [], "details": {},
        "action_plan": ["act1"],
    }
    enriched = enrich_report_business_context(
        report, rd,
        business_type="教育培训",
        brand_name="",
        category="小学生课后托管服务就餐与作业辅导",
        store_size=100, is_fallback=False)

    # 1. business_model_snapshot.model_type 必须是 education_childcare
    snap = enriched["business_model_snapshot"]
    assert snap["model_type"] == "education_childcare", \
        f"model_type should be education_childcare, got {snap['model_type']}"

    # 2. field_checklist 包含托管核心项
    fc = enriched.get("field_checklist", [])
    titles = " ".join(item.get("title", "") for item in fc)
    childcare_kw = ["放学", "接送", "暗竞品", "合规", "消防"]
    found = [kw for kw in childcare_kw if kw in titles]
    assert len(found) >= 1, f"field_checklist 缺少托管关键词: got {found} from {titles}"

    # 3. field_checklist 不得出现餐饮词
    FOOD_BANNED = ["外卖骑手", "取餐", "出餐速度", "上座率", "排队", "午晚高峰堂食"]
    for w in FOOD_BANNED:
        assert w not in titles, f"托管checklist不应出现 '{w}'"

    # 4. caliber_explanation 体现托管/小饭桌漏收录
    cal = enriched.get("caliber_explanation", "")
    assert "托管" in cal or "小饭桌" in cal or "家庭" in cal or "漏收录" in cal or "未被收录" in cal, \
        f"caliber 应体现托管漏收录: {cal[:100]}"

    # 5. revenue_disclaimer 是托管口径
    rd_text = enriched.get("revenue_disclaimer", "")
    assert "出餐" not in rd_text, f"托管revenue不应含出餐: {rd_text}"
    assert "外卖" not in rd_text, f"托管revenue不应含外卖: {rd_text}"
    assert "目标小学" in rd_text or "生源" in rd_text or "托管" in rd_text or "服务组合" in rd_text, \
        f"托管revenue应包含托管相关词: {rd_text}"

    # 6. data_sufficiency reasons 包含托管竞品/合规提示
    from services.report_quality_service import assess_data_sufficiency
    ds = assess_data_sufficiency(rd, business_type="教育培训",
                                 rigor_enabled=False, is_fallback=False,
                                 brand_name="", category="小学生课后托管服务就餐与作业辅导")
    reasons_text = " ".join(ds.get("reasons", []))
    assert "托管" in reasons_text or "合规" in reasons_text, \
        f"data_sufficiency reasons 应包含托管/合规提示: {reasons_text}"

    print("T21 category-only childcare all modules: PASS")


# ═══════════════════════════════════════════════
# T22: 教育培训非托管不误走 education_childcare
# ═══════════════════════════════════════════════
def test_education_training_not_misclassified():
    from services.business_model_service import classify_business_model_family
    from services.report_enrichment_service import enrich_report_business_context

    # 纯教育培训，无托管关键词
    assert classify_business_model_family("教育培训", "英语培训", "") == "education_training"
    assert classify_business_model_family("教育培训", "", "") == "education_training"

    rd = _base_rd(**_EDUCATION_RD)
    report = {"score": 60, "summary": "test", "advantages": ["a"], "disadvantages": ["d"],
              "dimension_scores": [], "details": {}, "action_plan": ["a"]}
    enriched = enrich_report_business_context(
        report, rd, business_type="教育培训", brand_name="英语培训", category="",
        store_size=80, is_fallback=False)
    snap = enriched["business_model_snapshot"]
    assert snap["model_type"] == "education_training", \
        f"英语培训 should be education_training, got {snap['model_type']}"

    # brand_name="" 且 category="" → education_training
    enriched2 = enrich_report_business_context(
        report.copy(), rd, business_type="教育培训", brand_name="", category="",
        store_size=80, is_fallback=False)
    assert enriched2["business_model_snapshot"]["model_type"] == "education_training", \
        "empty brand+category should still be education_training"

    print("T22 education training not misclassified: PASS")


if __name__ == "__main__":
    test_classify_all_business_types()
    test_education_childcare_no_food_words()
    test_education_childcare_checklist()
    test_education_childcare_zero_competitor_safe()
    test_snack_food_200m_zero_but_1000m_many()
    test_snack_food_fit_stop_sharp()
    test_location_fundamentals_consistency()
    test_html_renders_all_modules()
    test_data_sufficiency_wording()
    test_non_food_non_edu_not_misclassified()
    test_competition_score_not_inflated()
    test_business_model_snapshot_fields()
    test_all_families_fallback_clean()
    # P1 返工新增测试
    test_category_only_childcare()
    test_enrichment_all_modules()
    test_revenue_disclaimer_per_family()
    test_all_12_families_coverage()
    test_education_childcare_category_only_no_food()
    test_html_uses_revenue_disclaimer()
    test_all_families_strict_guard_clean()
    # P1 category 传播专项测试
    test_category_only_childcare_all_modules()
    test_education_training_not_misclassified()
    print()
    print("ALL P1 BUSINESS MODEL QUALITY TESTS PASSED")
