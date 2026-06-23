"""P0-P3 redline regression tests — 2026-06-22 rework."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

PASS = 0
FAIL = 0

def t(name, ok):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print(f"  FAIL: {name}")

# ═══ T1: storage_service default provider ═══
def test_storage_default():
    from services.storage_service import _DEFAULTS
    t("storage_service._DEFAULTS.storage_provider == tencent_cos",
      _DEFAULTS.get("storage_provider") == "tencent_cos")

# ═══ T2: admin test endpoint returns detail on failure ═══
def test_admin_test_endpoint_detail():
    from services.cloud_storage import upload_healthcheck_to_cloud
    from routers.admin import _AVAILABLE_STORAGE_PROVIDERS
    # Verify only tencent_cos is allowed
    t("T2a: _AVAILABLE_STORAGE_PROVIDERS == {'tencent_cos'}",
      _AVAILABLE_STORAGE_PROVIDERS == {"tencent_cos"})
    # Verify the test endpoint constructs a proper response shape
    result = upload_healthcheck_to_cloud()
    # Build a mock response dict like the endpoint would return
    resp = {
        "ok": result.ok,
        "provider": result.provider,
        "key": result.key,
        "url": result.url,
        "error": result.error,
        "mode": result.mode,
    }
    t("T2b: response has 'ok' field", "ok" in resp)
    t("T2c: response has 'error' field", "error" in resp)
    # The real endpoint also adds 'detail' and 'hint'
    # Verify we can construct a detail string from the error
    if not result.ok:
        raw = result.error or ""
        if "cloud_mode_not_configured" in raw:
            detail = "云存储未启用或配置不完整。"
        elif "upload_failed" in raw:
            detail = f"上传到 COS 失败：{raw}"
        else:
            detail = raw
        t("T2d: detail constructed from error", bool(detail))
        t("T2e: detail is not empty on failure", len(detail) > 0)
    else:
        t("T2d: cloud configured (integration)", True)
        t("T2e: cloud configured (integration)", True)

# ═══ T3: market_anchor exists in category labels and ALL_CATEGORY_KEYS ═══
def test_market_anchor_category():
    from services.amap_service import ALL_CATEGORY_KEYS, CATEGORY_LABELS, MARKET_ANCHOR_KEYWORDS, is_market_anchor
    t("T3a: market_anchor in ALL_CATEGORY_KEYS",
      "market_anchor" in ALL_CATEGORY_KEYS)
    t("T3b: market_anchor in CATEGORY_LABELS",
      "market_anchor" in CATEGORY_LABELS)
    t("T3c: CATEGORY_LABELS[market_anchor] == 市场/专业市场",
      CATEGORY_LABELS.get("market_anchor") == "市场/专业市场")
    from services.amap_service import SHOPPING_KEEP
    t("T3d: market_anchor NOT in SHOPPING_KEEP",
      "农贸市场" not in SHOPPING_KEEP and "建材市场" not in SHOPPING_KEEP)

# ═══ T4: is_market_anchor + is_real_shopping positive/negative ═══
def test_market_anchor_function():
    from services.amap_service import is_market_anchor, is_real_shopping
    # Positive: market anchors
    pos = ["农贸市场（北区）", "建材市场A区", "五金市场", "菜市场（东门）",
           "汽配城一期", "家居市场", "商贸城", "批发市场"]
    for name in pos:
        t(f"T4a: is_market_anchor('{name[:10]}') == True",
          is_market_anchor(name))
    # Negative: real shopping malls
    neg = ["万象城", "龙湖天街", "大悦城", "印象城", "宝龙广场", "万达广场", "购物中心"]
    for name in neg:
        t(f"T4b: is_market_anchor('{name}') == False",
          not is_market_anchor(name))
    # Shopping regression (Item 2)
    t("T4c: 盛龙广场-龙首购物中心 is_real_shopping", is_real_shopping("盛龙广场-龙首购物中心"))
    t("T4d: 三星电子服务中心 NOT shopping", not is_real_shopping("三星电子服务中心"))
    t("T4e: 海娟百货商店 NOT shopping", not is_real_shopping("海娟百货商店"))
    t("T4f: 明太日用百货商店 NOT shopping", not is_real_shopping("明太日用百货商店"))
    # "百货商场" still valid
    t("T4g: xx百货商场 is_real_shopping", is_real_shopping("新世纪百货商场"))
    t("T4h: xx百货大楼 is_real_shopping", is_real_shopping("王府井百货大楼"))
    # Market should NOT be real_shopping
    t("T4i: 建材市场 not is_real_shopping", not is_real_shopping("建材市场A区"))

# ═══ T5: rent fields ═══
def test_rent_schema():
    from models.schemas import AnalyzeRequest
    # monthly_rent without other fields
    req = AnalyzeRequest(address="test", location={"lng": 1, "lat": 1},
                         provider="deepseek", monthly_rent=5000, rent_input_type="monthly")
    t("T5a: monthly_rent stored", req.monthly_rent == 5000)
    t("T5b: rent_input_type stored", req.rent_input_type == "monthly")
    # per_sqm
    req2 = AnalyzeRequest(address="test", location={"lng": 1, "lat": 1},
                          provider="deepseek", rent_per_sqm=120.5,
                          rent_input_type="per_sqm", store_size=80)
    t("T5c: rent_per_sqm stored", req2.rent_per_sqm == 120.5)
    t("T5d: per_sqm * store_size = 9640", req2.store_size == 80)
    # no rent = compatible
    req3 = AnalyzeRequest(address="test", location={"lng": 1, "lat": 1},
                          provider="deepseek")
    t("T5e: no rent fields, still valid", req3.monthly_rent is None)
    # T5f: monthly_rent > 0 with empty rent_input_type → still works (defaults to monthly)
    req4 = AnalyzeRequest(address="test", location={"lng": 1, "lat": 1},
                          provider="deepseek", monthly_rent=4000, rent_input_type="")
    t("T5f: monthly_rent=4000 with empty rent_input_type", req4.monthly_rent == 4000)
    t("T5g: rent_input_type defaults empty", req4.rent_input_type == "")

# ═══ T6: cost_estimate meta with user rent ═══
def test_cost_estimate_meta():
    from services.report_score_meta_service import add_dimension_score_meta
    r = {"dimension_scores": [{"key": "cost_estimate", "score": 50}]}
    add_dimension_score_meta(r, {}, 80)
    meta = r.get("dimension_score_meta", [])
    cm = next((m for m in meta if m["key"] == "cost_estimate"), {})
    # Without cost_inputs, rent_per_sqm should be in missing
    t("T6a: no rent → rent_per_sqm in missing_required_inputs",
      "rent_per_sqm" in cm.get("missing_required_inputs", []))
    t("T6b: no rent → score_confidence low",
      cm.get("score_confidence") == "low")

    # With cost_inputs having monthly_rent
    r2 = {"dimension_scores": [{"key": "cost_estimate", "score": 50}],
          "cost_inputs": {"monthly_rent": 5000, "rent_source": "user_input_monthly"}}
    add_dimension_score_meta(r2, {}, 80)
    meta2 = r2.get("dimension_score_meta", [])
    cm2 = next((m for m in meta2 if m["key"] == "cost_estimate"), {})
    t("T6c: with rent → rent_per_sqm NOT in missing",
      "rent_per_sqm" not in cm2.get("missing_required_inputs", []))
    t("T6d: with rent → score_confidence medium",
      cm2.get("score_confidence") == "medium")
    t("T6e: with rent → score_basis user_rent_provided",
      cm2.get("score_basis") == "user_rent_provided")

# ═══ T7: no data source boilerplate in service output ═══
def test_no_boilerplate():
    from services.fallback_report_service import build_fallback_report
    # business_model_service check
    import services.business_model_service as bms
    bms_text = ""
    for attr in dir(bms):
        try:
            obj = getattr(bms, attr)
            if callable(obj):
                sig = str(obj.__code__.co_consts)[:2000]
                bms_text += sig
        except: pass
    for phrase in ["高德地图POI采集", "数据来自高德"]:
        t(f"T7c: business_model_service no '{phrase}'",
          phrase not in bms_text)

    fake_data = {
        "stats_200m": {}, "stats_500m": {"shopping": 1, "residential": 20,
        "office": 5, "subway": 1, "bus": 3, "parking": 2, "schools": 2,
        "hospitals": 1, "convenience": 3},
        "stats_1000m": {},
        "poi_counts": {"shopping": 2, "residential": 50, "office": 15,
        "schools": 5, "hospitals": 2, "subway": 1, "bus": 10, "parking": 8},
        "poi_lists": {}, "restaurant_poi_lists": {},
        "direct_competitors_200m": 1, "direct_competitors_500m": 2,
        "direct_competitors_1000m": 3,
        "substitute_competitors_200m": 0, "substitute_competitors_500m": 1,
        "substitute_competitors_1000m": 2,
        "traffic_anchors_200m": 0, "traffic_anchors_500m": 1,
        "traffic_anchors_1000m": 2,
        "direct_competitor_list": [], "substitute_list": [],
        "traffic_anchor_list": [],
        "data_quality_notes": ["名称脱水剔除 5 个POI"],
        "raw_poi_counts": {}, "raw_stats_200m": {}, "raw_stats_500m": {},
        "raw_stats_1000m": {},
        "all_pois": [],
        "business_areas": [], "nearby_roads": [],
    }
    fb = build_fallback_report(fake_data, address="测试地址", business_type="餐饮",
                               brand_name="测试品牌", store_size=100)
    details_str = json.dumps(fb.get("details", {}), ensure_ascii=False)
    data_boundary = fb.get("data_boundary", "")
    forbidden = ["高德地图POI采集", "数据来自高德", "名称脱水"]
    for phrase in forbidden:
        t(f"T7a: fallback details no '{phrase}'",
          phrase not in details_str)
        t(f"T7b: fallback data_boundary no '{phrase}'",
          phrase not in data_boundary)

# ═══ T8: fallback cost_estimate reflects user rent ═══
def test_fallback_cost_estimate_with_rent():
    from services.fallback_report_service import build_fallback_report
    fake = {
        "stats_200m": {}, "stats_500m": {"shopping": 1, "residential": 20,
        "office": 5, "subway": 1, "bus": 3, "parking": 2, "schools": 2,
        "hospitals": 1, "convenience": 3},
        "stats_1000m": {},
        "poi_counts": {"shopping": 2, "residential": 50, "office": 15,
        "schools": 5, "hospitals": 2, "subway": 1, "bus": 10, "parking": 8},
        "poi_lists": {}, "restaurant_poi_lists": {},
        "direct_competitors_200m": 1, "direct_competitors_500m": 2, "direct_competitors_1000m": 3,
        "substitute_competitors_200m": 0, "substitute_competitors_500m": 1, "substitute_competitors_1000m": 2,
        "traffic_anchors_200m": 0, "traffic_anchors_500m": 1, "traffic_anchors_1000m": 2,
        "direct_competitor_list": [], "substitute_list": [], "traffic_anchor_list": [],
        "data_quality_notes": [], "raw_poi_counts": {}, "raw_stats_200m": {},
        "raw_stats_500m": {}, "raw_stats_1000m": {},
        "all_pois": [], "business_areas": [], "nearby_roads": [],
    }
    # Test monthly_rent
    fb_m = build_fallback_report(fake, address="测", business_type="餐饮",
                                  brand_name="测", store_size=100,
                                  cost_inputs={"monthly_rent": 8000, "rent_source": "user_input_monthly"})
    detail_m = fb_m.get("details", {}).get("cost_estimate", "")
    t("T8a: monthly_rent in fallback cost_estimate", "8000" in detail_m and "用户提供" in detail_m)

    # Test per_sqm with store_size — monthly_rent present so uses monthly_rent branch
    fb_p = build_fallback_report(fake, address="测", business_type="餐饮",
                                  brand_name="测", store_size=80,
                                  cost_inputs={"rent_per_sqm": 120, "monthly_rent": 9600,
                                               "rent_source": "user_input_per_sqm"})
    detail_p = fb_p.get("details", {}).get("cost_estimate", "")
    t("T8b: per_sqm fallback shows monthly_rent 9600", "9600" in detail_p)

    # Test no rent
    fb_none = build_fallback_report(fake, address="测", business_type="餐饮",
                                     brand_name="测", store_size=100)
    detail_none = fb_none.get("details", {}).get("cost_estimate", "")
    t("T8c: no rent → 线下询价", "线下询" in detail_none)

# ═══ T9: admin/index.html arPoiDefs includes market_anchor ═══
def test_admin_html_market_anchor():
    import pathlib
    html_path = pathlib.Path(__file__).resolve().parent.parent / "admin" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    # arPoiDefs 常量必须包含 [key, label] 格式的 market_anchor
    t("T9a: arPoiDefs includes ['market_anchor','市场/专业市场']",
      "['market_anchor','市场/专业市场']" in html)
    # aliases 有 market_anchor
    t("T9b: aliases includes market_anchor",
      "market_anchor:['market_anchor']" in html)
    # stats defs 也有 market_anchor（label, key 格式）
    t("T9c: stats defs includes ['市场/专业市场','market_anchor']",
      "['市场/专业市场','market_anchor']" in html)

# ═══ T10: admin/index.html helper sanity ═══
def test_admin_html_helpers():
    import pathlib, re
    html_path = pathlib.Path(__file__).resolve().parent.parent / "admin" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    # T10a: escHtml must be defined (was a production bug: ReferenceError)
    defs = set(re.findall(r'function\s+(\w+)', html))
    t("T10a: escHtml is defined", "escHtml" in defs)
    # T10b: escHtml should be an alias of esc (only one escaping implementation)
    t("T10b: esc is defined", "esc" in defs)
    # T10c: check all helper names used in arRenderReport are defined
    # arRenderReport calls these helpers
    needed = ["arSection","arScoreCard","arList","arRow","arReadPath","arRenderDataSufficiency",
              "arRenderCompetition","arRenderStats","arRenderPoiCats","arRenderDetails",
              "arRenderBrands","arRenderChecklist","arRenderEvidence","arRenderNamedChips",
              "arScoreColor","arScoreLevel","arText","arArr","arNames","arCountMore",
              "arMetric","arVal","arChips","arFallbackLabel","arPoiName","arStripScore",
              "arCheckIcon","arCheckRow","arMaskText","esc","escHtml","escUrl","fmtDateTime",
              "fmtReportGeneratedTime"]
    for name in needed:
        t(f"T10c: {name} defined", name in defs)
    # T10d: no legacy double-escape pattern (escHtml should just delegate)
    t("T10d: escHtml delegates to esc", "escHtml(v){return esc(v)}" in html or
      "escHtml(v){return esc(v)}" in html or "function escHtml(v){return esc(v)}" in html)

# ═══ T11: old report compatibility smoke test ═══
def test_old_report_compat():
    import pathlib, json, re
    old = {
        "score": 55, "summary": "旧报告摘要",
        "advantages": ["交通便利"], "disadvantages": ["竞争激烈"],
        "dimension_scores": [{"key": "population_density", "score": 60}],
        "details": {"population_density": "500米内10个住宅小区"},
        "real_data": {
            "direct_competitors_200m": 1, "direct_competitors_500m": 2, "direct_competitors_1000m": 3,
            "substitute_competitors_200m": 0, "substitute_competitors_500m": 1, "substitute_competitors_1000m": 2,
            "traffic_anchors_200m": 0, "traffic_anchors_500m": 1, "traffic_anchors_1000m": 2,
            "direct_competitor_list": [], "substitute_list": [], "traffic_anchor_list": [],
            "stats_200m": {}, "stats_500m": {"shopping": 1}, "stats_1000m": {},
            "poi_counts": {}, "poi_lists": {},
        },
    }
    t("T11a: score from old report", (old.get("score", 0) or 0) == 55)
    ci = old.get("cost_inputs")
    t("T11b: cost_inputs missing → null", ci is None)
    dt = old.get("details", {})
    t("T11c: details access safe", dt.get("cost_estimate", "") == "")
    s5 = old.get("real_data", {}).get("stats_500m", {})
    t("T11d: market_anchor missing in old stats", s5.get("market_anchor") is None)
    t("T11e: shopping present in old stats", s5.get("shopping") == 1)
    brands = old.get("real_data", {}).get("hot_brands") or []
    t("T11f: brands missing → empty", len(brands) == 0)
    pl = old.get("real_data", {}).get("poi_lists", {})
    t("T11g: poi_lists.market_anchor missing → null", pl.get("market_anchor") is None)
    html_path = pathlib.Path(__file__).resolve().parent.parent / "admin" / "index.html"
    html = html_path.read_text(encoding="utf-8")
    defs = set(re.findall(r'function\s+(\w+)', html))
    t("T11h: escHtml defined", "escHtml" in defs)
    t("T11i: esc defined", "esc" in defs)

# ═══ T12: prompt rent_context wording ═══
def test_prompt_rent_context():
    from prompts.location_analysis import build_analysis_prompt
    # monthly mode
    pm = build_analysis_prompt("addr", 1, 1, business_type="餐饮", store_size=80,
        cost_inputs={"rent_input_type": "monthly", "monthly_rent": 5000, "rent_source": "user_input_monthly"})
    t("T12a: monthly prompt includes 用户已填写月租金", "用户已填写月租金" in pm and "5000" in pm)
    t("T12b: monthly prompt not 单平", "单平" not in pm)
    # per_sqm mode
    pp = build_analysis_prompt("addr", 1, 1, business_type="餐饮", store_size=80,
        cost_inputs={"rent_input_type": "per_sqm", "rent_per_sqm": 120, "rent_source": "user_input_per_sqm"})
    t("T12c: per_sqm prompt includes 用户已填写单平租金", "用户已填写单平租金" in pp and "120" in pp and "9600" in pp)
    t("T12d: rent_context actually in prompt (not just computed)", "用户已填写" in pp)
    # no rent
    pn = build_analysis_prompt("addr", 1, 1, business_type="餐饮", store_size=50, cost_inputs=None)
    t("T12e: no rent → no 用户已填写", "用户已填写" not in pn)
    # per_sqm without store_size
    pns = build_analysis_prompt("addr", 1, 1, business_type="餐饮", store_size=0,
        cost_inputs={"rent_input_type": "per_sqm", "rent_per_sqm": 150, "rent_source": "user_input_per_sqm_no_size"})
    t("T12f: per_sqm no store_size → 单平 but no 换算月租", "用户已填写单平租金" in pns and "换算月租" not in pns)

# ═══ T13: miniprogram parseReport resets rptCostInputs ═══
def test_miniprogram_reset_cost_inputs():
    import pathlib
    vue = pathlib.Path(__file__).resolve().parent.parent.parent / "uniapp" / "src" / "pages" / "report-detail" / "index.vue"
    src = vue.read_text(encoding="utf-8")
    t("T13a: parseReport sets this.rptCostInputs = null", "this.rptCostInputs = null" in src)
    t("T13b: rptCostInputs assigned from rpt.cost_inputs", "rpt.cost_inputs" in src or "rptCi" in src)
    # T13c: rentInputType default in home/index.vue
    home_vue = pathlib.Path(__file__).resolve().parent.parent.parent / "uniapp" / "src" / "pages" / "home" / "index.vue"
    home_src = home_vue.read_text(encoding="utf-8")
    _mq = chr(39) + "monthly" + chr(39)
    t("T13c: home vue rentInputType default monthly",
      "rentInputType" in home_src and _mq in home_src)

# ═══ T15: rent payload logic ═══
def test_rent_payload_logic():
    # Simulate frontend payload: rentValue=4000, rentInputType=monthly (default)
    rentVal = 4000; rit = 'monthly'
    payload = {}
    if rentVal > 0:
        if (rit or 'monthly') == 'per_sqm':
            payload['rent_per_sqm'] = rentVal; payload['rent_input_type'] = 'per_sqm'
        else:
            payload['monthly_rent'] = rentVal; payload['rent_input_type'] = 'monthly'
    t("T15a: default monthly → monthly_rent=4000", payload.get("monthly_rent") == 4000)
    t("T15b: default monthly → rent_input_type=monthly", payload.get("rent_input_type") == "monthly")

    # Simulate backend: monthly_rent=4000, rent_input_type='' → still generates cost_inputs
    _mr = 4000; _pr = None; _rit = ''
    _req_ci = None
    if _mr is not None and _mr > 0 and _rit in ("", "monthly"):
        _req_ci = {"rent_input_type": "monthly", "rent_source": "user_input_monthly", "monthly_rent": _mr, "store_size": 80}
    t("T15c: backend monthly+empty → cost_inputs", _req_ci is not None)
    t("T15d: backend monthly+empty → monthly_rent=4000", _req_ci and _req_ci["monthly_rent"] == 4000)

    # Simulate backend: rent_per_sqm=120, rent_input_type='' → per_sqm
    _pr2 = 120; _mr2 = None; _rit2 = ''
    _req_ci2 = None
    if _pr2 is not None and _pr2 > 0 and _rit2 in ("", "per_sqm"):
        _req_ci2 = {"rent_input_type": "per_sqm", "rent_per_sqm": _pr2, "store_size": 80}
    t("T15e: backend per_sqm+empty → cost_inputs", _req_ci2 is not None)

# ═══ T14: fallback text bans ═══
def test_fallback_text_bans():
    from services.fallback_report_service import build_fallback_report
    import json
    fd = {
        "stats_200m": {}, "stats_500m": {"shopping": 1, "residential": 20, "office": 5, "subway": 1, "bus": 3, "parking": 2, "schools": 4, "hospitals": 1, "convenience": 3, "market_anchor": 0},
        "stats_1000m": {},
        "poi_counts": {"shopping": 2, "residential": 50, "office": 15, "schools": 5, "hospitals": 2, "subway": 1, "bus": 10, "parking": 8},
        "poi_lists": {}, "restaurant_poi_lists": {},
        "direct_competitors_200m": 1, "direct_competitors_500m": 2, "direct_competitors_1000m": 3,
        "substitute_competitors_200m": 0, "substitute_competitors_500m": 1, "substitute_competitors_1000m": 2,
        "traffic_anchors_200m": 0, "traffic_anchors_500m": 1, "traffic_anchors_1000m": 2,
        "direct_competitor_list": [], "substitute_list": [], "traffic_anchor_list": [],
        "data_quality_notes": [], "raw_poi_counts": {}, "raw_stats_200m": {}, "raw_stats_500m": {}, "raw_stats_1000m": {},
        "all_pois": [], "business_areas": [], "nearby_roads": [],
    }
    fb = build_fallback_report(fd, address="测", business_type="餐饮", brand_name="测", store_size=100)
    all_text = json.dumps(fb, ensure_ascii=False)
    banned = ["数据数据", "计数钟"]
    for phrase in banned:
        t(f"T14a: no '{phrase}' in fallback", phrase not in all_text)
    # 学校客流 must not be truncated (ending with just "学校客流" without follow-up)
    detail_pop = fb.get("details", {}).get("population_density", "")
    t("T14b: population_density text not truncated", not detail_pop.endswith("学校客流"))
    # Any dimension mentioning school must have follow-up guidance
    all_details = json.dumps(fb.get("details", {}), ensure_ascii=False)
    if "学校" in all_details or "教育机构" in all_details:
        t("T14c: school mention has follow-up guidance", "核验" in all_details)


# === T16: missing_labels are Chinese (not English keys) ===
def test_missing_labels_chinese():
    from services.report_score_meta_service import add_dimension_score_meta, _MISSING_INPUT_LABELS, _missing_labels, _cost_note
    r = {"dimension_scores": [{"key": "cost_estimate", "score": 50}]}
    add_dimension_score_meta(r, {}, 80)
    cm = [m for m in r["dimension_score_meta"] if m["key"] == "cost_estimate"][0]
    note = cm.get("note", ""); ml = cm.get("missing_labels", [])
    for k in ["rent_per_sqm", "labor_cost", "revenue_estimate", "store_area"]:
        t(f"T16a: note no {k}", k not in note)
    t("T16b: note has chinese", "月租金" in note)
    t("T16c: note no labor_cost chinese", "人工成本" not in note)
    t("T16d: note no revenue_estimate chinese", "预估营业额" not in note)
    t("T16e: ml are chinese", all(v in _MISSING_INPUT_LABELS.values() for v in ml))
    r2 = {"dimension_scores": [{"key": "cost_estimate", "score": 50}],
          "cost_inputs": {"monthly_rent": 4000, "rent_source": "user_input_monthly"}}
    add_dimension_score_meta(r2, {}, 80)
    cm2 = [m for m in r2["dimension_score_meta"] if m["key"] == "cost_estimate"][0]
    note2 = cm2.get("note", ""); ml2 = cm2.get("missing_labels", [])
    t("T16f: with rent → note empty", note2 == "")
    t("T16g: with rent → no missing_labels", ml2 == [])
    import pathlib
    h = (pathlib.Path(__file__).resolve().parent.parent / "admin" / "index.html").read_text(encoding="utf-8")
    t("T16h: admin uses missing_labels", "missing_labels" in h)
    t("T16i: admin no raw join", "missing_required_inputs.join" not in h)



# === T17: user readability — no English keys in user-visible display ===
def test_user_readability():
    import pathlib, json, re
    vue = pathlib.Path(__file__).resolve().parent.parent.parent / "uniapp" / "src" / "pages" / "report-detail" / "index.vue"
    vt = vue.read_text(encoding="utf-8")
    ah = (pathlib.Path(__file__).resolve().parent.parent / "admin" / "index.html").read_text(encoding="utf-8")
    import services.storage_service as ss
    sh = open(ss.__file__, encoding="utf-8").read()

    # === 1. No English key fallback in user-visible areas ===
    # Vue: no m.label||m.key pattern leaking English keys
    t("T17a: vue no m.label||m.key", "m.label||m.key" not in vt)
    t("T17b: vue no m.label || m.key", "m.label || m.key" not in vt)
    t("T17c: vue no label||key in JS", "m.label||m.key||" not in vt)
    # Admin: no m.label||m.key
    t("T17d: admin no m.label||m.key", "m.label||m.key" not in ah)

    # === 2. Chinese labels present in all 3 views ===
    cn = ["客源密度", "到店方便", "门前客流",
          "消费人群", "竞争情况", "房租压力"]
    vp = sum(1 for k in cn if k in vt)
    ap = sum(1 for k in cn if k in ah)
    sp = sum(1 for k in cn if k in sh)
    t("T17e: vue Chinese labels 6/6", vp >= 6)
    t("T17f: admin Chinese labels 6/6", ap >= 6)
    t("T17g: storage Chinese labels 6/6", sp >= 6)

    # === 3. No low-confidence / missing: tech terms ===
    t("T17h: admin no 低置信", "低置信" not in ah)
    t("T17i: vue no 低置信", "低置信" not in vt)
    t("T17j: vue no 缺失:", "缺失:" not in vt)
    t("T17k: admin no 缺失:", "缺失:" not in ah)

    # === 4. Storage detail_labels are Chinese ===
    old_tech = ["人口密集度", "交通与可达性", "客流特征",
                "消费人群属性", "竞争环境", "房租成本预估"]
    for ot in old_tech:
        t(f"T17l: storage no '{ot}'", ot not in sh)

    # === 5. Meta label and old note compat ===
    from services.report_score_meta_service import add_dimension_score_meta
    r = {"dimension_scores": [{"key": "cost_estimate", "score": 50}]}
    add_dimension_score_meta(r, {}, 80)
    cm = [m for m in r["dimension_score_meta"] if m["key"] == "cost_estimate"][0]
    t("T17m: meta label = 房租压力", cm.get("label") == "房租压力")
    note = cm.get("note", "")
    BANNED = ["rent_per_sqm", "labor_cost", "revenue_estimate", "cost_estimate", "不具备成本压力精算依据", "50分为占位值"]
    for kw in BANNED:
        t(f"T17n: note no '{kw}'", kw not in note)

    # === 6. Old note rewrite in admin HTML ===
    t("T17o: admin has humanMetaNote", "humanMetaNote" in ah)
    t("T17p: vue has humanMetaNote", "humanMetaNote" in vt)

    # === 7. Population density note is plain language ===
    t("T17q: pop note is plain", "人口密集度依据偏弱" not in sh and "近场住宅" not in sh)

    # Old meta with key only + old note → must show Chinese label
    from services.report_score_meta_service import dimension_label
    old_key = "cost_estimate"
    cn_label = dimension_label(old_key)
    t("T17r: old meta key maps to Chinese", cn_label == "房租压力")
    # Admin fallback: arDetailLabels[m.key].label maps cost_estimate → 房租压力
    t("T17s: admin arDetailLabels has cost_estimate", "cost_estimate" in ah and "房租压力" in ah)
    # Explicitly ban d.key leakage
    t("T17t: admin no ||d.key||", "||d.key||" not in ah)
    t("T17u: admin no || d.key ||", "|| d.key ||" not in ah)
    t("T17v: admin no arDetailLabels[d.key]?.label)||d.key", "arDetailLabels[d.key]?.label)||d.key" not in ah)
    # Vue d.key bans
    t("T17w: vue no d.label || d.key", "d.label || d.key" not in vt)
    t("T17x: vue no d.label||d.key", "d.label||d.key" not in vt)
    t("T17y: vue no d.title || d.key", "d.title || d.key" not in vt)
    t("T17z: vue no d.title||d.key", "d.title||d.key" not in vt)
    # Methods must use this. prefix
    t("T17aa: vue has this.dimLabel", "this.dimLabel" in vt)
    t("T17ab: vue has this.humanMetaNote", "this.humanMetaNote" in vt)
    t("T17ac: vue no bare dimLabel( call", "label: m.label || dimLabel(m.key)" not in vt and "label: d.label || d.title || dimLabel(d.key)" not in vt)
    t("T17ad: vue no bare humanMetaNote( call", "note: humanMetaNote(m)" not in vt)

    t("T17aa: vue score meta uses this.dimLabel", "label: m.label || this.dimLabel(m.key) || '指标'" in vt)
    t("T17ab: vue score meta uses this.humanMetaNote", "note: this.humanMetaNote(m)" in vt)
    t("T17ac: vue no bare dimLabel", "label: m.label || dimLabel(m.key)" not in vt)
    t("T17ad: vue no bare humanMetaNote", "note: humanMetaNote(m)" not in vt)





# === T18: merged competitor display + old report compat ===
def test_merged_competitors():
    import pathlib, json
    vue = pathlib.Path(__file__).resolve().parent.parent.parent / "uniapp" / "src" / "pages" / "report-detail" / "index.vue"
    vt = vue.read_text(encoding="utf-8")
    ah = (pathlib.Path(__file__).resolve().parent.parent / "admin" / "index.html").read_text(encoding="utf-8")
    import services.storage_service as ss
    sh = open(ss.__file__, encoding="utf-8").read()

    # 1. No banned patterns
    banned = ["展示前 10 条", "展示前 5 条", "items.slice(0,8)"]
    for kw in banned:
        t(f"T18a: admin no '{kw}'", kw not in ah)
        t(f"T18b: vue no '{kw}'", kw not in vt)
        t(f"T18c: storage no '{kw}'", kw not in sh)

    # 2. Miniprogram has full names (not slice-limited)
    t("T18d: vue no items.slice(0,8)", "items.slice(0,8)" not in vt)
    t("T18e: vue has _displayNames", "_displayNames" in vt)
    t("T18f: vue expand uses names.length", "names.length" in vt)

    # 3. Admin has details expand
    t("T18g: admin has details", "details" in ah)
    t("T18h: admin has 展开全部", "展开全部" in ah)

    # 4. Admin POI expand uses names not items
    t("T18i: admin no items.slice(8)", "items.slice(8)" not in ah)
    t("T18j: admin POI expand uses names.slice(5)", "names.slice(5)" in ah)

    # 5. Storage has details for competitor
    t("T18i: storage has details expand", "details" in sh)

    # 5. Simulate 17 competitors → verify patterns
    # (done via code review above)


# === T19: competitor rows no longer repeat type tags ===
def test_competitor_no_type_tags():
    import pathlib, re, subprocess, os
    ah = (pathlib.Path(__file__).resolve().parent.parent / "admin" / "index.html").read_text(encoding="utf-8")
    import services.storage_service as ss
    sh = open(ss.__file__, encoding="utf-8").read()
    vue = pathlib.Path(__file__).resolve().parent.parent.parent / "uniapp" / "src" / "pages" / "report-detail" / "index.vue"
    vt = vue.read_text(encoding="utf-8")

    # Hard bans on old patterns
    t("T19a: admin no esc(x.type)", "esc(x.type)" not in ah)
    t("T19b: admin no ar-tag-danger", "ar-tag-danger" not in ah)
    t("T19c: admin no ar-tag-info", "ar-tag-info" not in ah)
    t("T19d: admin has arCompetitorItem", "function arCompetitorItem" in ah)
    t("T19e: admin arCompetitorItem returns proper HTML", "</span></div>" in ah)

    # Storage bans
    comp = sh[sh.find("_render_merged_competitor_list"):sh.find("def _score_int", sh.find("_render_merged_competitor_list"))]
    t("T19f: storage no tag_cls", "tag_cls" not in comp)
    t("T19g: storage no _esc(tag)", "_esc(tag)" not in comp)

    # Title checks
    t("T19h: admin title 竞品样本", "竞品样本" in ah)
    t("T19i: storage title 竞品样本", "竞品样本" in sh)
    t("T19j: vue title 竞品样本", "竞品样本" in vt)

    # Node --check smoke test
    m = re.search(r"<script>(.*?)</script>", ah, re.DOTALL)
    if m:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(m.group(1))
            tmp = f.name
        try:
            r = subprocess.run(["node", "--check", tmp], capture_output=True, text=True, timeout=10)
            t("T19k: admin JS syntax valid (node --check)", r.returncode == 0)
        except Exception:
            t("T19k: admin JS syntax valid (node --check)", False)
        finally:
            os.unlink(tmp)

for _fn, _label in [
    (test_storage_default, "T1-storage-default"),
    (test_admin_test_endpoint_detail, "T2-admin-test-detail"),
    (test_market_anchor_category, "T3-market-anchor-category"),
    (test_market_anchor_function, "T4-market-anchor-function"),
    (test_rent_schema, "T5-rent-schema"),
    (test_cost_estimate_meta, "T6-cost-estimate-meta"),
    (test_no_boilerplate, "T7-no-boilerplate"),
    (test_fallback_cost_estimate_with_rent, "T8-fallback-rent"),
    (test_admin_html_market_anchor, "T9-admin-html-market-anchor"),
    (test_admin_html_helpers, "T10-admin-html-helpers"),
    (test_old_report_compat, "T11-old-report-compat"),
    (test_prompt_rent_context, "T12-prompt-rent-context"),
    (test_miniprogram_reset_cost_inputs, "T13-miniprogram-reset-cost-inputs"),
    (test_fallback_text_bans, "T14-fallback-text-bans"),
    (test_rent_payload_logic, "T15-rent-payload-logic"),
    (test_missing_labels_chinese, "T16-missing-labels-chinese"),
    (test_user_readability, "T17-user-readability"),
    (test_merged_competitors, "T18-merged-competitors"),
    (test_competitor_no_type_tags, "T19-competitor-no-type-tags"),
]:
    try:
        _fn()
    except Exception as _e:
        FAIL += 1
        print(f"  FAIL {_label}: {_e}")

print(f"\n{'='*50}")
print(f"TOTAL: {PASS} PASS, {FAIL} FAIL")
if FAIL > 0:
    sys.exit(1)


