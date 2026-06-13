"""
P0.5 报告质量回归测试：公交分类、same_brand 检测、HTML checklist、POI 旧报告兼容。

保护：
- 公交分类：高德公交中文 type 变体全部识别为 "bus"，不丢失到 None。
- same_brand：同品牌自我分流是强风险，评分封顶，top_risk 优先展示。
- HTML checklist：导出 HTML 必须展示 title/pass_hint/eliminate_hint。
- POI 旧报告：新报告三层字段=0 展示 0/0/0；只有旧报告缺三层字段时展示"数据源记录"。
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════════════
# T1: 公交中文 type 分类（保护高德公交变体不丢到 None）
# ═══════════════════════════════════════════════
def test_bus_classification():
    from services.amap_service import classify_poi_type

    bus_cases = [
        ("交通设施服务;公交站",           "标准公交站路径"),
        ("交通设施服务;公交车站",           "高德可能返回'公交车站'"),
        ("交通设施服务;公交车站;公交车站相关", "多级公交车站路径"),
        ("交通设施服务;公交车站;普通公交站",   "普通公交站子分类"),
        ("交通设施服务;公交站;BRT站",       "BRT 快速公交"),
        ("150200",                         "数字 typecode"),
        ("交通设施服务;公交车站;BRT快速公交", "BRT 快速公交变体"),
    ]

    for type_str, desc in bus_cases:
        result = classify_poi_type(type_str)
        assert result == "bus", f"{desc}: {type_str} -> {result} (expected bus)"
    print("T1 bus_classification: ALL", len(bus_cases), "PASS")


# ═══════════════════════════════════════════════
# T1b: 公交 fetch 层 distance 缺失不被丢弃（保护：公交 distance 缺失时不被误计为 0 米，也不被提前丢弃）
# ═══════════════════════════════════════════════
def test_bus_fetch_keep_missing():
    import asyncio
    from unittest.mock import AsyncMock, patch
    from services.amap_service import AmapService

    svc = AmapService()
    bus_poi_missing_dist = {
        "name": "测试公交站",
        "type": "交通设施服务;公交车站",
        "distance": "",
        "location": "108.9,34.2",
        "address": "测试路",
    }

    # --- T1b-1: _fetch_by_keyword 保留缺失距离公交 ---
    async def _run_kw():
        with patch.object(svc, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"pois": [bus_poi_missing_dist]}
            result = await svc._fetch_by_keyword(
                108.9, 34.2, "公交站", radius=1000, max_results=80,
                keep_missing_distance=True, missing_distance_default=999)
            assert len(result) > 0, "bus with missing distance should be kept"
            assert result[0]["distance"] == 999, f"distance should be 999, got {result[0]['distance']}"

    asyncio.run(_run_kw())
    print("T1b-1 _fetch_by_keyword keep missing dist: PASS")

    # --- T1b-2: _fetch_all_pois 保留缺失距离公交 ---
    async def _run_type():
        with patch.object(svc, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = {"pois": [bus_poi_missing_dist]}
            result = await svc._fetch_all_pois(
                108.9, 34.2, types="150200", radius=1000, max_results=100,
                keep_missing_distance=True, missing_distance_default=999)
            assert len(result) > 0, "bus types search should keep missing distance"
            assert result[0]["distance"] == 999, f"types distance should be 999, got {result[0]['distance']}"

    asyncio.run(_run_type())
    print("T1b-2 _fetch_all_pois keep missing dist: PASS")


# ═══════════════════════════════════════════════
# T2: same_brand 检测与评分封顶
# ═══════════════════════════════════════════════
def test_same_brand_detection():
    from services.fallback_report_service import (
        _detect_same_brand_risk, _competition_score,
        _category_advantage_score, build_fallback_report,
    )

    # --- T2a: 去括号匹配 ---
    match, names = _detect_same_brand_risk("陕二丫擀面皮", {
        "direct_competitor_list": [{"name": "陕二丫擀面皮(石坝河店)"}],
    })
    assert match, "陕二丫擀面皮应匹配陕二丫擀面皮(石坝河店)"
    assert "陕二丫擀面皮" in names[0], f"matched name should contain brand core, got {names}"
    print("T2a same_brand match: PASS")

    # --- T2b: 不误杀 ---
    match2, _ = _detect_same_brand_risk("陕二丫擀面皮", {
        "direct_competitor_list": [{"name": "二丫烧烤"}, {"name": "陕二烧烤"}],
    })
    assert not match2, "短子串不应误匹配"
    print("T2b same_brand no false match: PASS")

    # --- T2c: radius list 也能命中 ---
    match3, _ = _detect_same_brand_risk("陕二丫擀面皮", {
        "direct_competitor_list_1000m": [{"name": "陕二丫擀面皮(石坝河店)"}],
    })
    assert match3, "应通过 direct_competitor_list_1000m 命中"
    print("T2c same_brand 1000m list: PASS")

    # --- T2d: same_brand 评分封顶 ---
    cs = _competition_score(2, 3, 6, same_brand_risk=True)
    assert cs <= 45, f"competition same_brand capped at 45, got {cs}"
    print(f"T2d competition same_brand cap: PASS ({cs} <= 45)")

    cs2 = _competition_score(2, 3, 5, same_brand_risk=False)
    assert cs2 <= 60, f"competition dc_1000>=4 capped at 60, got {cs2}"
    print(f"T2e competition dc_1000 cap: PASS ({cs2} <= 60)")

    ca = _category_advantage_score(2, 3, 5, True, 10, 5, 3)
    assert ca <= 40, f"category_advantage same_brand capped at 40, got {ca}"
    print(f"T2f category_advantage same_brand cap: PASS ({ca} <= 40)")

    # --- T2g: 全量 fallback 报告 top_risk 一致性 ---
    real_data = {
        "stats_200m": {"schools": 0, "residential": 2, "office": 1, "hospitals": 0},
        "stats_500m": {"schools": 0, "residential": 10, "office": 3, "hospitals": 0,
                       "subway": 0, "bus": 5, "parking": 0, "shopping": 0, "hotels": 0},
        "stats_1000m": {"schools": 0, "residential": 20, "office": 5, "hospitals": 0,
                        "subway": 0, "bus": 8, "parking": 0, "shopping": 0, "hotels": 0},
        "direct_competitors_200m": 0, "direct_competitors_500m": 0, "direct_competitors_1000m": 2,
        "substitute_competitors_200m": 0, "substitute_competitors_500m": 0, "substitute_competitors_1000m": 0,
        "traffic_anchors_200m": 0, "traffic_anchors_500m": 0, "traffic_anchors_1000m": 0,
        "direct_competitor_list": [{"name": "陕二丫擀面皮(石坝河店)"}],
        "direct_competitor_list_200m": [], "direct_competitor_list_500m": [],
        "direct_competitor_list_1000m": [{"name": "陕二丫擀面皮(石坝河店)"}],
        "substitute_list": [], "traffic_anchor_list": [],
        "poi_lists": {}, "hot_brands": [], "nearby_roads": [],
        "rigor_enabled": False, "subway_applicable": True, "city_has_subway": False,
    }
    rpt = build_fallback_report(real_data, address="测试", business_type="小吃快餐",
                                brand_name="陕二丫擀面皮", store_size=60)
    ds = rpt.get("decision_snapshot", {})
    dis = rpt.get("disadvantages", [])
    es = rpt.get("executive_summary", {})
    top_risk = ds.get("top_risk", "")
    dis0 = dis[0] if dis else ""
    es_risk0 = (es.get("top_risks") or [""])[0] if es.get("top_risks") else ""
    # 保护：同品牌自我分流是强风险，必须优先展示
    assert "自我分流" in top_risk, f"top_risk should mention 自我分流, got: {top_risk}"
    assert "自我分流" in dis0, f"disadvantages[0] should mention 自我分流, got: {dis0}"
    assert "自我分流" in es_risk0, f"executive_summary.top_risks[0] should mention 自我分流, got: {es_risk0}"
    # 保护：评分不能高
    comp_dim = [d for d in rpt.get("dimension_scores", []) if d["key"] == "competition"]
    assert comp_dim and comp_dim[0]["score"] <= 45, f"competition should cap at 45 with same_brand, got {comp_dim}"
    print("T2g fallback top_risk consistency: PASS")


# ═══════════════════════════════════════════════
# T3: HTML checklist 渲染 title/pass_hint/eliminate_hint
# ═══════════════════════════════════════════════
def test_html_checklist_rendering():
    from services.storage_service import _build_report_html

    report_data = {
        "score": 60,
        "summary": "test",
        "field_checklist": [
            {
                "title": "核验午高峰人流",
                "time_window": "11:30-13:00",
                "action": "计数15分钟",
                "risk_type": "客流不足",
                "pass_hint": "目标客群稳定经过",
                "eliminate_hint": "客群明显不足",
            }
        ],
        "decision_snapshot": {},
        "data_sufficiency": {},
        "generated_at": "2026-06-15 14:30",
        "business_type": "测试业态",
    }
    html = _build_report_html(1, report_data, "测试地址", "测试品牌")
    # 保护：HTML 导出必须展示 title/pass_hint/eliminate_hint
    assert "核验午高峰人流" in html, "title not rendered"
    assert "目标客群稳定经过" in html, "pass_hint not rendered"
    assert "客群明显不足" in html, "eliminate_hint not rendered"
    print("T3 html checklist: PASS")


# ═══════════════════════════════════════════════
# T4: POI 旧报告兼容（字段缺失 vs 值=0 的区别）
# ═══════════════════════════════════════════════
def test_poi_old_report_compat():
    from services.storage_service import _build_report_html

    # --- T4a: 新报告，stats key 存在且值=0，不展示"数据源记录" ---
    new_report = {
        "score": 60, "summary": "test",
        "real_data": {
            "stats_200m": {"office": 0, "residential": 5},
            "stats_500m": {"office": 0, "residential": 10},
            "stats_1000m": {"office": 0, "residential": 20},
            "raw_stats_1000m": {"office": 2},  # 不应触发旧版兼容
        },
        "decision_snapshot": {}, "data_sufficiency": {},
        "generated_at": "2026-06-15 14:30", "business_type": "测试",
    }
    html_new = _build_report_html(1, new_report, "addr", "brand")
    # 保护：新报告有效三层字段为 0 时展示 0/0/0，不是"数据源记录"
    assert "0 / 0 / 0" in html_new, "new report with stats=0 should show 0/0/0"
    assert "数据源记录" not in html_new, "new report should NOT show old compat text"
    print("T4a new report stats=0 shows 0/0/0: PASS")

    # --- T4b: 旧报告，缺少 stats_200m/500m/1000m 的 key ---
    old_report = {
        "score": 60, "summary": "test",
        "real_data": {
            "stats_200m": {"residential": 5},
            "stats_500m": {"residential": 10},
            "stats_1000m": {"residential": 20},
            # office 字段完全缺失
            "raw_stats_1000m": {"office": 2},
            "poi_counts": {"office": 2},
        },
        "decision_snapshot": {}, "data_sufficiency": {},
        "generated_at": "2026-06-15 14:30", "business_type": "测试",
    }
    html_old = _build_report_html(1, old_report, "addr", "brand")
    # 保护：旧报告缺三层字段时展示"数据源记录"
    assert "数据源记录 2" in html_old, "old report missing stats field should show data source record"
    print("T4b old report missing field shows data source: PASS")


# ═══════════════════════════════════════════════
# T5: fallback 禁词稳态矩阵（保护：全部 fallback 分支不触发 fact_guard 禁词）
# ═══════════════════════════════════════════════

def _assert_no_banned_words(report, scenario):
    """扫描用户可见字段，确保不包含任何禁止决策语言。"""
    from report_fact_guard import validate_report_fact_consistency, _PROHIBITED_DECISION_PATTERNS
    fe = validate_report_fact_consistency(report, report.get("real_data", {}))
    assert fe == [], f"{scenario}: fact_guard failed: {fe}"

    # 额外扫描 fact_guard 未覆盖的用户可见字段（decision_snapshot / field_checklist 等）
    import json as _json
    visible_keys = ["summary","advantages","disadvantages","details","dimension_scores",
                    "executive_summary","action_plan","decision_snapshot","field_checklist",
                    "caliber_explanation","data_boundary"]
    visible_text = " ".join(
        _json.dumps(report.get(k) or {}, ensure_ascii=False) if isinstance(report.get(k), (dict, list))
        else str(report.get(k) or "")
        for k in visible_keys
    )
    for pat in _PROHIBITED_DECISION_PATTERNS:
        assert pat not in visible_text, f"{scenario}: banned word '{pat}' in user-visible text"

from services.fallback_report_service import build_fallback_report

def _base_data(**overrides):
    """构建最小基础 real_data，调用方覆写特定字段。"""
    base = {
        "stats_200m": {"residential":0,"office":0,"schools":0,"hospitals":0,"subway":0,"bus":0,"parking":0,"shopping":0,"hotels":0},
        "stats_500m": {"residential":0,"office":0,"schools":0,"hospitals":0,"subway":0,"bus":0,"parking":0,"shopping":0,"hotels":0},
        "stats_1000m": {"residential":0,"office":0,"schools":0,"hospitals":0,"subway":0,"bus":0,"parking":0,"shopping":0,"hotels":0},
        "direct_competitors_200m":0,"direct_competitors_500m":0,"direct_competitors_1000m":0,
        "substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,
        "traffic_anchors_200m":0,"traffic_anchors_500m":0,"traffic_anchors_1000m":0,
        "direct_competitor_list":[],"direct_competitor_list_200m":[],"direct_competitor_list_500m":[],"direct_competitor_list_1000m":[],
        "substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
        "rigor_enabled":False,"subway_applicable":True,"city_has_subway":False,
    }
    base.update(overrides)
    return base

SCENARIOS = [
    # 1. low_pop：全部为 0
    ("low_pop", "小餐饮", "麻辣烫", 50,
     _base_data()),

    # 2. mid_pop：中等人口
    ("mid_pop", "小吃快餐", "炸鸡店", 30,
     _base_data(
         stats_500m={"residential":8,"office":5,"schools":2,"hospitals":0,"subway":0,"bus":3,"parking":1,"shopping":1,"hotels":0},
         stats_1000m={"residential":15,"office":10,"schools":4,"hospitals":1,"subway":1,"bus":6,"parking":3,"shopping":2,"hotels":2},
         direct_competitors_500m=3, direct_competitors_1000m=6,
     )),

    # 3. good_pop：较好客流
    ("good_pop", "便利店", "社区便利店", 80,
     _base_data(
         stats_500m={"residential":20,"office":15,"schools":5,"hospitals":2,"subway":2,"bus":10,"parking":5,"shopping":3,"hotels":0},
         stats_1000m={"residential":40,"office":25,"schools":8,"hospitals":3,"subway":3,"bus":15,"parking":8,"shopping":5,"hotels":3},
         direct_competitors_200m=1, direct_competitors_500m=3, direct_competitors_1000m=5,
     )),

    # 4. high_comp：高竞品
    ("high_comp", "中餐", "湘菜馆", 200,
     _base_data(
         stats_500m={"residential":10,"office":8,"schools":1,"hospitals":0,"subway":1,"bus":5,"parking":2,"shopping":2,"hotels":0},
         stats_1000m={"residential":20,"office":15,"schools":3,"hospitals":1,"subway":2,"bus":8,"parking":4,"shopping":3,"hotels":2},
         direct_competitors_200m=18, direct_competitors_500m=25, direct_competitors_1000m=40,
     )),

    # 5. same_brand：同品牌分店
    ("same_brand", "小吃快餐", "陕二丫擀面皮", 60,
     _base_data(
         stats_500m={"residential":8,"office":5,"schools":2,"hospitals":0,"subway":0,"bus":4,"parking":1,"shopping":1,"hotels":0},
         stats_1000m={"residential":15,"office":10,"schools":3,"hospitals":1,"subway":1,"bus":6,"parking":2,"shopping":2,"hotels":1},
         direct_competitors_500m=2, direct_competitors_1000m=5,
         direct_competitor_list=[{"name":"陕二丫擀面皮(石坝河店)"}],
         direct_competitor_list_1000m=[{"name":"陕二丫擀面皮(石坝河店)"}],
     )),

    # 6. small_food：麻辣烫 50㎡
    ("small_food", "小餐饮", "麻辣烫", 50,
     _base_data(
         stats_500m={"residential":5,"office":3,"schools":1,"hospitals":0,"subway":0,"bus":2,"parking":0,"shopping":0,"hotels":0},
         stats_1000m={"residential":10,"office":5,"schools":2,"hospitals":0,"subway":0,"bus":4,"parking":1,"shopping":1,"hotels":0},
         direct_competitors_200m=2, direct_competitors_500m=5, direct_competitors_1000m=8,
     )),

    # 7. non_food：教育培训
    ("non_food", "教育培训", "小学生托管服务", 200,
     _base_data(
         stats_500m={"residential":10,"office":3,"schools":3,"hospitals":1,"subway":1,"bus":5,"parking":2,"shopping":1,"hotels":0},
         stats_1000m={"residential":25,"office":8,"schools":5,"hospitals":2,"subway":2,"bus":10,"parking":5,"shopping":3,"hotels":3},
         direct_competitors_200m=0, direct_competitors_500m=1, direct_competitors_1000m=2,
     )),
]


def test_fallback_banned_word_matrix():
    for name, biz_type, brand, size, rd in SCENARIOS:
        report = build_fallback_report(rd, address="测试地址", business_type=biz_type,
                                       brand_name=brand, store_size=size)
        _assert_no_banned_words(report, name)
        ds = report.get("decision_snapshot", {})
        print(f"T5-{name}: verdict='{ds.get('verdict','?')}' pass")


# ═══════════════════════════════════════════════
# T6: decision_snapshot 一致性（保护：同一 real_data 下 normal 补全和 fallback verdict 档位一致）
# ═══════════════════════════════════════════════
def test_decision_snapshot_consistency():
    from services.report_decision_service import compute_decision_snapshot
    from services.fallback_report_service import build_fallback_report

    rd = _base_data(
        stats_500m={"residential":8,"office":5,"schools":2,"hospitals":0,"subway":0,"bus":3,"parking":1,"shopping":1,"hotels":0},
        stats_1000m={"residential":15,"office":10,"schools":4,"hospitals":1,"subway":1,"bus":6,"parking":3,"shopping":2,"hotels":2},
        direct_competitors_500m=3, direct_competitors_1000m=6)

    # normal 补全
    ds_normal = compute_decision_snapshot(55, rd, business_type="小吃快餐", brand_name="炸鸡店")
    # fallback
    rpt = build_fallback_report(rd, address="测试", business_type="小吃快餐", brand_name="炸鸡店", store_size=30)
    ds_fallback = rpt.get("decision_snapshot", {})

    assert ds_normal["verdict"] == ds_fallback["verdict"], \
        f"verdict mismatch: normal={ds_normal['verdict']} vs fallback={ds_fallback['verdict']}"
    for key in ["fit_condition", "stop_condition"]:
        assert ds_normal.get(key), f"normal missing {key}"
        assert ds_fallback.get(key), f"fallback missing {key}"
    # 禁词检查
    from report_fact_guard import _PROHIBITED_DECISION_PATTERNS
    import json as _json
    text = _json.dumps(ds_normal, ensure_ascii=False)
    for pat in _PROHIBITED_DECISION_PATTERNS:
        assert pat not in text, f"banned '{pat}' in decision_snapshot"
    print("T6 decision_snapshot consistency: PASS")


# ═══════════════════════════════════════════════
# T7: HTML footer 去 AI 兜底（保护：旧后台配置不把 AI 带到用户可见HTML）
# ═══════════════════════════════════════════════
def test_html_footer_no_ai():
    from services.storage_service import _build_report_html
    report = {"score": 60, "summary": "test", "decision_snapshot": {}, "data_sufficiency": {},
              "generated_at": "2026-06-15 14:30", "business_type": "测试"}
    html = _build_report_html(1, report, "addr", "brand")
    assert "AI" not in html, "HTML should not contain AI"
    assert "商业选址初筛报告" in html, "title should use new wording"
    print("T7 html footer no AI: PASS")


# ═══════════════════════════════════════════════
# T8: 小餐饮替代消费过滤药店/医疗 POI + 列表计数一致
# ═══════════════════════════════════════════════
def test_substitute_pharmacy_filter():
    from services.substitute_pharmacy_filter import filter_substitute_pharmacy

    rd = {
        "substitute_list": [
            {"name": "怡康医药超市", "distance": 100},
            {"name": "普通便利店", "distance": 200},
            {"name": "众信医药超市", "distance": 300},
            {"name": "社区超市", "distance": 500},
            {"name": "某医院门诊", "distance": 600},
        ],
        "substitute_list_200m": [
            {"name": "怡康医药超市", "distance": 100},
            {"name": "普通便利店", "distance": 200},
        ],
        "substitute_list_500m": [
            {"name": "怡康医药超市", "distance": 100},
            {"name": "普通便利店", "distance": 200},
            {"name": "众信医药超市", "distance": 300},
            {"name": "社区超市", "distance": 500},
        ],
        "substitute_list_1000m": [
            {"name": "怡康医药超市", "distance": 100},
            {"name": "普通便利店", "distance": 200},
            {"name": "众信医药超市", "distance": 300},
            {"name": "社区超市", "distance": 500},
            {"name": "某医院门诊", "distance": 600},
        ],
        "substitute_competitors_200m": 2,
        "substitute_competitors_500m": 4,
        "substitute_competitors_1000m": 5,
    }
    filtered = filter_substitute_pharmacy(rd, "小餐饮")
    # 计数一致性
    assert filtered["substitute_competitors_200m"] == len(filtered["substitute_list_200m"])
    assert filtered["substitute_competitors_500m"] == len(filtered["substitute_list_500m"])
    assert filtered["substitute_competitors_1000m"] == len(filtered["substitute_list_1000m"])
    # 药店被过滤
    assert len(filtered["substitute_list_500m"]) == 2  # 只剩 普通便利店、社区超市
    assert len(filtered["substitute_list"]) == 2  # 只剩两个非医疗
    print("T8a substitute pharmacy filter counts: PASS")

    # 空列表字段存在时不触发总表重拆
    rd2 = {
        "substitute_list": [{"name": "药店", "distance": 150}],
        "substitute_list_200m": [],
        "substitute_list_500m": [{"name": "药店", "distance": 150}],
        "substitute_list_1000m": [{"name": "药店", "distance": 150}],
        "substitute_competitors_200m": 0,
        "substitute_competitors_500m": 1,
        "substitute_competitors_1000m": 1,
    }
    filtered2 = filter_substitute_pharmacy(rd2, "小吃快餐")
    assert filtered2["substitute_competitors_200m"] == 0
    assert len(filtered2["substitute_list_200m"]) == 0
    assert filtered2["substitute_competitors_500m"] == 0
    print("T8b empty list respected: PASS")

    # 非餐饮业态不过滤
    rd3 = {
        "substitute_list": [{"name": "药店", "distance": 150}],
        "substitute_list_500m": [{"name": "药店", "distance": 150}],
        "substitute_competitors_500m": 1,
    }
    filtered3 = filter_substitute_pharmacy(rd3, "教育培训")
    assert len(filtered3["substitute_list"]) == 1  # 不过滤
    print("T8c non-food not filtered: PASS")


# ═══════════════════════════════════════════════
# T9: verdict 严格阈值测试（保护：verdict 只由 score 决定）
# ═══════════════════════════════════════════════
def test_verdict_strict_thresholds():
    from services.report_decision_service import compute_decision_snapshot
    # 即使数据差，score>=60 就是可优先
    poor_data = _base_data()
    assert compute_decision_snapshot(60, poor_data)["verdict"] == "可优先现场核验"
    assert compute_decision_snapshot(59, poor_data)["verdict"] == "谨慎考察"
    assert compute_decision_snapshot(40, poor_data)["verdict"] == "谨慎考察"
    assert compute_decision_snapshot(39, poor_data)["verdict"] == "应列为低优先级候选点"
    # 即使数据好，score<40 也是低优先级
    good_data = _base_data(
        stats_500m={"residential":30,"office":20,"schools":10,"hospitals":0,"subway":2,"bus":15,"parking":5,"shopping":3,"hotels":0},
        stats_1000m={"residential":50,"office":30,"schools":15,"hospitals":2,"subway":3,"bus":20,"parking":8,"shopping":5,"hotels":5})
    assert compute_decision_snapshot(35, good_data)["verdict"] == "应列为低优先级候选点"
    print("T9 verdict strict thresholds: ALL PASS")


# ═══════════════════════════════════════════════
# T10: decision_snapshot 禁词兜底测试（保护：输入有禁词时输出不含禁词）
# ═══════════════════════════════════════════════
def test_decision_snapshot_sanitize():
    from services.report_decision_service import compute_decision_snapshot
    from report_fact_guard import _PROHIBITED_DECISION_PATTERNS
    import json as _json

    ds = compute_decision_snapshot(
        55, _base_data(),
        advantages=["此处建议推进该点位", "可以投资此商圈"],
        disadvantages=["最终决策需谨慎"],
        action_plan=["推荐开店前先核验客流"]
    )
    text = _json.dumps(ds, ensure_ascii=False)
    for pat in _PROHIBITED_DECISION_PATTERNS:
        assert pat not in text, f"banned '{pat}' leaked into decision_snapshot"
    # 确认替换生效
    assert "后续判断" in ds["top_risk"] or "继续现场核验" in ds["top_strength"] or "需结合现场核验" in ds["next_action"]
    print("T10 decision_snapshot sanitize: PASS")


# ═══════════════════════════════════════════════
# T11: HTML footer 旧后台配置兜底测试（保护：旧配置不把 AI 带到 HTML）
# ═══════════════════════════════════════════════
def test_html_footer_old_config():
    from unittest.mock import patch
    from services import storage_service
    from services.storage_service import _build_report_html
    report = {"score": 60, "summary": "test", "decision_snapshot": {}, "data_sufficiency": {},
              "generated_at": "2026-06-15 14:30", "business_type": "测试"}
    with patch.object(storage_service, "get_pdf_config", return_value={"footer_text": "AI 选址分析 · 商业选址初筛参考"}):
        html = _build_report_html(1, report, "addr", "brand")
    assert "AI" not in html, "HTML must not contain AI even with old config"
    assert "址得选 · 商业选址初筛参考" in html, "footer should show new branding"
    print("T11 html footer old config: PASS")


# ═══════════════════════════════════════════════
# T12: HTML 禁词测试（保护：HTML 不出现最终决策等禁词）
# ═══════════════════════════════════════════════
def test_html_no_banned_words():
    from services.storage_service import _build_report_html
    report = {"score": 60, "summary": "test", "decision_snapshot": {}, "data_sufficiency": {},
              "generated_at": "2026-06-15 14:30", "business_type": "测试"}
    html = _build_report_html(1, report, "addr", "brand")
    assert "最终决策" not in html, "HTML must not contain 最终决策"
    assert "后续判断" in html, "HTML should use 后续判断 instead"
    print("T12 html no banned words: PASS")


# ═══════════════════════════════════════════════
# T13: 非餐饮业态不过滤 + 单字关键词不误伤（保护：皮肤管理等不触发餐饮过滤）
# ═══════════════════════════════════════════════
def test_non_food_no_filter():
    from services.substitute_pharmacy_filter import filter_substitute_pharmacy
    rd = {"substitute_list": [{"name": "药店", "distance": 150}],
          "substitute_list_500m": [{"name": "药店", "distance": 150}],
          "substitute_competitors_500m": 1}
    assert len(filter_substitute_pharmacy(rd, "皮肤管理")["substitute_list"]) == 1
    # "面馆" 应该触发过滤
    rd2 = {"substitute_list": [{"name": "药店", "distance": 150}],
           "substitute_list_500m": [{"name": "药店", "distance": 150}],
           "substitute_competitors_500m": 1}
    assert len(filter_substitute_pharmacy(rd2, "面馆")["substitute_list"]) == 0
    print("T13 non-food no filter + 面馆 triggers: PASS")


if __name__ == "__main__":
    test_bus_classification()
    test_bus_fetch_keep_missing()
    test_same_brand_detection()
    test_html_checklist_rendering()
    test_poi_old_report_compat()
    test_fallback_banned_word_matrix()
    test_decision_snapshot_consistency()
    test_html_footer_no_ai()
    test_substitute_pharmacy_filter()
    test_verdict_strict_thresholds()
    test_decision_snapshot_sanitize()
    test_html_footer_old_config()
    test_html_no_banned_words()
    test_non_food_no_filter()
    print()
    print("ALL P0.5 REGRESSION TESTS PASSED")
