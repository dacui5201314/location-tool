"""Phase E: 评分 meta 用户可见化测试"""
import sys, os, json, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.fallback_report_service import build_fallback_report
from services.report_enrichment_service import enrich_report_business_context
from services.storage_service import _build_report_html
from report_fact_guard import build_user_visible_report_text

f = 0
p = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")


def _base_rd(**kw):
    base = {
        "stats_200m":{"residential":0,"office":0,"schools":1,"subway":0,"bus":0,"parking":1,"shopping":0,"hotels":0,"restaurants":2},
        "stats_500m":{"residential":1,"office":0,"schools":2,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4},
        "stats_1000m":{"residential":10,"office":0,"schools":4,"subway":0,"bus":5,"parking":2,"shopping":1,"hotels":14,"restaurants":79},
        "direct_competitors_200m":0,"direct_competitors_500m":2,"direct_competitors_1000m":4,
        "substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,
        "traffic_anchors_200m":0,"traffic_anchors_500m":3,"traffic_anchors_1000m":8,
        "direct_competitor_list":[],"substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
        "rigor_enabled":True,"subway_applicable":True,"city_has_subway":False,
    }
    base.update(kw)
    return base


rd = _base_rd()
fb = build_fallback_report(rd, business_type="小吃快餐", brand_name="", store_size=0)
enr = enrich_report_business_context(fb, rd, business_type="小吃快餐", brand_name="", store_size=0, is_fallback=True)

# T-SM-01: enrichment has dimension_score_meta
print("=== T-SM-01: enrichment has meta ===")
check("dimension_score_meta" in enr, "enrichment must have meta")
meta = enr.get("dimension_score_meta", [])
check(len(meta) >= 8, f"meta has 8+ entries: {len(meta)}")
print("T-SM-01 PASS")

# T-SM-02: cost_estimate low confidence
print("=== T-SM-02: cost low confidence ===")
cost_m = [m for m in meta if m["key"] == "cost_estimate"]
check(len(cost_m) == 1, "cost meta exists")
check(cost_m[0]["score_confidence"] == "low", "cost is low conf")
check(not cost_m[0]["is_score_applicable"], "cost not applicable")
print("T-SM-02 PASS")

# T-SM-03: HTML renders cost low confidence notice
print("=== T-SM-03: HTML shows low confidence notice ===")
html = _build_report_html(1, enr, "addr", "brand")
check("仅供参考" in html or "粗略参考" in html, "HTML must show low confidence indicator")
check("粗略参考" in html or "仅供参考" in html, "HTML shows placeholder notice")
check("占位参考" not in html, "HTML must not use old placeholder wording")
print("T-SM-03 PASS")

# T-SM-04: HTML renders population_density weak
print("=== T-SM-04: HTML shows weak near field ===")
pop_m = [m for m in meta if m["key"] == "population_density"]
if pop_m and pop_m[0].get("score_basis") == "weak_near_field_demand":
    check("客源密度" in html or "客源数据不足" in html, "HTML should have pop note")
print("T-SM-04 PASS")

# T-SM-05: scores unchanged
print("=== T-SM-05: scores still numeric ===")
for d in enr.get("dimension_scores", []):
    check(isinstance(d.get("score"), (int, float)), f"score numeric: {d['key']}")
check(isinstance(enr.get("score"), (int, float)), "overall_score numeric")
print("T-SM-05 PASS")

# T-SM-06: old report no meta does not crash HTML
print("=== T-SM-06: old report no meta OK ===")
old_report = {"score": 50, "summary": "t", "advantages": [], "disadvantages": [],
              "dimension_scores": [{"key":"a","score":50}]*8, "details": {},
              "action_plan": [], "executive_summary": {}, "location_fundamentals": {},
              "location_profile": {}, "business_model_snapshot": {}, "decision_snapshot": {},
              "field_checklist": [], "evidence_summary": {}, "real_data": {}}
old_html = _build_report_html(1, old_report, "addr", "brand")
check(len(old_html) > 0, "old report renders")
check("dimension_score_meta" not in old_report, "old has no meta")
print("T-SM-06 PASS")

# T-SM-07: admin/index.html reads dimension_score_meta
print("=== T-SM-07: admin reads score meta ===")
admin_src = open(os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html'), 'r', encoding='utf-8').read()
check("dimension_score_meta" in admin_src, "admin reads meta")
check("score_confidence" in admin_src, "admin reads confidence")
print("T-SM-07 PASS")

# T-SM-08: uniapp reads dimension_score_meta
print("=== T-SM-08: uniapp reads score meta ===")
uniapp_src = open(os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src', 'pages', 'report-detail', 'index.vue'), 'r', encoding='utf-8').read()
check("dimension_score_meta" in uniapp_src, "uniapp reads meta")
check("rptScoreMeta" in uniapp_src, "uniapp has rptScoreMeta")
check("需要补充的信息" in uniapp_src, "uniapp shows low confidence hint")
print("T-SM-08 PASS")

# T-SM-09: meta text doesn't cause new guard false positives
print("=== T-SM-09: meta in guard scan without new issues ===")
txt = build_user_visible_report_text(enr)
check(len(txt) > 0, "text built")
# Build with clean real_data that has no radius mismatches
rd_clean = _base_rd(stats_500m={"residential":1,"office":0,"schools":2,"bus":2,"subway":0},
                    stats_1000m={"residential":10,"office":0,"schools":4,"bus":5,"restaurants":79,"hotels":14})
fb_c = build_fallback_report(rd_clean, business_type="小吃快餐", brand_name="", store_size=0)
enr_c = enrich_report_business_context(fb_c, rd_clean, business_type="小吃快餐", brand_name="", store_size=0, is_fallback=True)
txt_c = build_user_visible_report_text(enr_c)
# score meta keywords should not trigger radius mismatch
from report_fact_guard import check_radius_mismatch
rm = check_radius_mismatch(txt_c, rd_clean)
# Filter: only check for score-meta placeholder / confidence related mismatches, not legitimate data mismatches
meta_related = [e for e in rm if "占位" in e or "低置信" in e or "score" in e.lower()]
check(len(meta_related) == 0, f"meta text should not trigger radius mismatch: {meta_related}")
print("T-SM-09 PASS")

# T-SM-10: meta item missing key doesn't crash HTML
print("=== T-SM-10: meta missing key does not crash ===")
dirty1 = copy.deepcopy(enr)
dirty1["dimension_score_meta"] = [{"score_confidence": "low"}]
try:
    h = _build_report_html(1, dirty1, "addr", "brand")
    check(len(h) > 0, "HTML renders with bad meta")
except Exception as e:
    check(False, f"should not crash: {e}")
print("T-SM-10 PASS")

# T-SM-11: mixed valid/invalid meta items
print("=== T-SM-11: mixed meta items -> cost still shows ===")
dirty2 = copy.deepcopy(enr)
dirty2["dimension_score_meta"] = [
    "bad_string", None,
    {"key": "cost_estimate", "score_confidence": "low", "is_score_applicable": False},
    {"score_confidence": "low"}
]
try:
    h2 = _build_report_html(1, dirty2, "addr", "brand")
    check("仅供参考" in h2 or "粗略参考" in h2, f"cost note still renders in mixed meta: {'found' if '仅供参考' in h2 or '粗略参考' in h2 else 'missing'}")
except Exception as e:
    check(False, f"mixed meta should not crash: {e}")
print("T-SM-11 PASS")

# T-SM-12: admin/index.html meta safety check
print("=== T-SM-12: admin meta safety ===")
admin_src = open(os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html'), 'r', encoding='utf-8').read()
check("typeof m==='object'" in admin_src, "admin checks meta item is object")
check("Array.isArray(m.missing_required_inputs)" in admin_src, "admin checks missing is array")
print("T-SM-12 PASS")

# T-SM-13: uniapp meta safety check
print("=== T-SM-13: uniapp meta safety ===")
uniapp_src = open(os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src', 'pages', 'report-detail', 'index.vue'), 'r', encoding='utf-8').read()
check("typeof m === 'object'" in uniapp_src, "uniapp filters non-object meta")
check("Array.isArray(m.missing_required_inputs)" in uniapp_src, "uniapp checks missing is array")
check("unknown" in uniapp_src, "uniapp has fallback key")
print("T-SM-13 PASS")

# T-SM-14: scores still numeric after dirty meta
print("=== T-SM-14: scores numeric with dirty meta ===")
for d in dirty2.get("dimension_scores", []):
    check(isinstance(d.get("score"), (int, float)), f"score numeric: {d['key']}")
print("T-SM-14 PASS")

# T-SM-15: dirty missing_required_inputs normalization (P1-6 regression)
print("=== T-SM-15: dirty missing_required_inputs ===")
# 15a: int value
dirty_int = copy.deepcopy(enr)
dirty_int["dimension_score_meta"] = [
    {"key": "cost_estimate", "score_confidence": "low", "is_score_applicable": False,
     "missing_required_inputs": 123}
]
try:
    hi = _build_report_html(1, dirty_int, "addr", "brand")
    check(len(hi) > 0, "int missing_required_inputs does not crash")
    check("仅供参考" in hi or "粗略参考" in hi, "int missing shows fallback")
    check("rent_per_sqm" not in hi, "int missing does not leak rent_per_sqm")
except Exception as e:
    check(False, f"int missing_required_inputs should not crash: {e}")

# 15b: string value
dirty_str = copy.deepcopy(enr)
dirty_str["dimension_score_meta"] = [
    {"key": "cost_estimate", "score_confidence": "low", "is_score_applicable": False,
     "missing_required_inputs": "rent_per_sqm"}
]
try:
    hs = _build_report_html(1, dirty_str, "addr", "brand")
    check(len(hs) > 0, "str missing_required_inputs does not crash")
    check("rent_per_sqm" not in hs, "str missing does not leak rent_per_sqm")
    check("仅供参考" in hs or "粗略参考" in hs, "str missing shows fallback")
except Exception as e:
    check(False, f"str missing_required_inputs should not crash: {e}")

# 15c: dict value
dirty_dict = copy.deepcopy(enr)
dirty_dict["dimension_score_meta"] = [
    {"key": "cost_estimate", "score_confidence": "low", "is_score_applicable": False,
     "missing_required_inputs": {"rent_per_sqm": True}}
]
try:
    hd = _build_report_html(1, dirty_dict, "addr", "brand")
    check(len(hd) > 0, "dict missing_required_inputs does not crash")
    check("rent_per_sqm" not in hd, "dict missing does not leak rent_per_sqm")
except Exception as e:
    check(False, f"dict missing_required_inputs should not crash: {e}")

# 15d: None value
dirty_none = copy.deepcopy(enr)
dirty_none["dimension_score_meta"] = [
    {"key": "cost_estimate", "score_confidence": "low", "is_score_applicable": False,
     "missing_required_inputs": None}
]
try:
    hn = _build_report_html(1, dirty_none, "addr", "brand")
    check(len(hn) > 0, "None missing_required_inputs does not crash")
except Exception as e:
    check(False, f"None missing_required_inputs should not crash: {e}")

# 15e: mixed dirty + valid still renders
dirty3 = copy.deepcopy(enr)
dirty3["dimension_score_meta"] = [
    "bad_string", None,
    {"key": "cost_estimate", "score_confidence": "low", "is_score_applicable": False,
     "missing_required_inputs": 999},
    {"key": "population_density", "score_confidence": "medium", "is_score_applicable": True,
     "missing_required_inputs": ["rent_per_sqm"]},
    {"score_confidence": "low", "missing_required_inputs": "garbage"}
]
try:
    h3 = _build_report_html(1, dirty3, "addr", "brand")
    check(len(h3) > 0, "mixed dirty missing does not crash")
    check("rent_per_sqm" not in h3, "mixed dirty does not leak rent_per_sqm")
    check("仅供参考" in h3 or "粗略参考" in h3, "mixed dirty has fallback")
except Exception as e:
    check(False, f"mixed dirty missing_required_inputs should not crash: {e}")
print("T-SM-15 PASS")

print(f"\n{'='*50}")
print(f"SCORE META DISPLAY: {p} PASS, {f} FAIL (total {p+f})")
if f: sys.exit(1)
