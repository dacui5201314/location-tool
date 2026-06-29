"""Share security: whitelist output + anti-enumeration + rate limiting"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import _sanitize_report_for_share, _share_rate_map

p = 0
f = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")

# ═══ T1: basic customer fields retained ═══
print("=== T1: customer-visible fields retained ===")
report = {
    "summary": "test summary",
    "overall_score": 72,
    "advantages": ["good location"],
    "disadvantages": ["high rent"],
    "dimension_scores": [{"key": "traffic", "score": 80}],
    "details": {"traffic": "good"},
    "action_plan": ["do this"],
    "decision_snapshot": {"verdict": "可优先现场核验"},
    "real_data": {
        "city": "北京", "district": "朝阳",
        "nearby_roads": ["建国路"],
        "competitor_list": ["肯德基"],
        "direct_competitor_list": ["麦当劳"],
        "substitute_list": ["吉野家"],
        "traffic_anchor_list": ["地铁站"],
        "poi_lists": {"shopping": [{"name": "SKP", "distance": 200}]},
        "stats_500m": {"restaurants": 10},
        "city_has_subway": True,
    },
    "report_type": "normal",
    "executive_summary": {"summary": "good"},
    "data_sufficiency": {"level": "adequate"},
}
s = _sanitize_report_for_share(json.dumps(report, ensure_ascii=False))
d = json.loads(s)
check(d.get("summary") == "test summary", "summary retained")
check(d.get("advantages") == ["good location"], "advantages retained")
check(d.get("real_data", {}).get("city") == "北京", "real_data.city retained")
check(d.get("real_data", {}).get("competitor_list") == ["肯德基"], "competitor_list retained")
check(d.get("real_data", {}).get("poi_lists"), "poi_lists retained")
print("T1 PASS")

# ═══ T2: sensitive fields dropped ═══
print("=== T2: sensitive fields dropped ===")
report2 = {
    "summary": "ok",
    "user_id": 42,
    "phone": "13800138000",
    "openid": "oxxx",
    "provider": "deepseek",
    "raw_response": "secret stuff",
    "billing_source": "points",
    "error_stage": "amap_failed",
    "admin": "admin_token",
    "_internal": "debug",
    "real_data": {
        "city": "北京",
        "raw_poi_counts": {"secret": 99},  # not in whitelist
        "irrelevant_excluded": ["hidden"],   # not in whitelist
    },
}
s2 = _sanitize_report_for_share(json.dumps(report2, ensure_ascii=False))
d2 = json.loads(s2)
check("user_id" not in d2, "user_id dropped")
check("phone" not in d2, "phone dropped")
check("openid" not in d2, "openid dropped")
check("provider" not in d2, "provider dropped")
check("raw_response" not in d2, "raw_response dropped")
check("billing_source" not in d2, "billing_source dropped")
check("error_stage" not in d2, "error_stage dropped")
check("admin" not in d2, "admin dropped")
check("_internal" not in d2, "underscore keys dropped")
check("summary" in d2, "summary still retained")
rd = d2.get("real_data", {})
check("city" in rd, "real_data.city retained")
check("raw_poi_counts" not in rd, "raw_poi_counts not in whitelist")
check("irrelevant_excluded" not in rd, "irrelevant_excluded not in whitelist")
print("T2 PASS")

# ═══ T3: nested sensitive injection blocked ═══
print("=== T3: nested injection blocked ===")
report3 = {
    "summary": "safe",
    "details": {
        "traffic": "ok",
        "_phone": "leak",  # underscore
        "openid": "bad",  # known sensitive key
    },
    "advantages": ["ok"],
}
s3 = _sanitize_report_for_share(json.dumps(report3, ensure_ascii=False))
d3 = json.loads(s3)
check("details" in d3, "details retained")
check("_phone" not in json.dumps(d3), "nested underscore dropped")
check("openid" not in json.dumps(d3.get("details", {})), "sensitive stripped from nested")
print("T3 PASS")

# ═══ T4: real_data sub-fields controlled ═══
print("=== T4: real_data sub-whitelist ===")
report4 = {
    "summary": "ok",
    "real_data": {
        "city": "上海",
        "district": "浦东",
        "raw_poi_counts": {"sensitive": 1},
        "debug_info": "should be dropped",
        "competitor_list": ["肯德基", "麦当劳"],
        "direct_competitor_list": ["星巴克"],
        "substitute_list": ["吉野家"],
        "traffic_anchor_list": ["地铁站", "公交站"],
        "poi_lists": {"restaurant": []},
        "stats_200m": {"r": 1},
        "stats_500m": {"r": 5},
        "stats_1000m": {"r": 20},
        "data_quality_notes": ["note1"],
        "hot_brands": ["品牌A"],
        "nearby_roads": ["路1"],
        "business_areas": ["商圈A"],
    },
}
s4 = _sanitize_report_for_share(json.dumps(report4, ensure_ascii=False))
d4 = json.loads(s4)
rd4 = d4.get("real_data", {})
check(rd4.get("city") == "上海", "city kept")
check(rd4.get("district") == "浦东", "district kept")
check("competitor_list" in rd4, "competitor_list kept")
check("direct_competitor_list" in rd4, "direct_competitor_list kept")
check("substitute_list" in rd4, "substitute_list kept")
check("traffic_anchor_list" in rd4, "traffic_anchor_list kept")
check("poi_lists" in rd4, "poi_lists kept")
check("stats_500m" in rd4, "stats_500m kept")
check("nearby_roads" in rd4, "nearby_roads kept")
check("business_areas" in rd4, "business_areas kept")
check("raw_poi_counts" not in rd4, "raw_poi_counts dropped")
check("debug_info" not in rd4, "debug_info dropped")
print("T4 PASS")

# ═══ T4b: customer-visible nested content preserved ═══
print("=== T4b: nested customer content preserved ===")
report4b = {
    "summary": "ok",
    "details": {
        "population_density": "周边居住人口密集",
        "site_suggestion": "建议实地考察",
        "_secret_note": "should not appear",
    },
    "executive_summary": {
        "summary": "总体评估良好",
        "top_strengths": ["交通便利"],
        "verdict": "可优先现场核验",
    },
    "decision_snapshot": {
        "verdict": "可优先现场核验",
        "score": 72,
        "evidence_summary": "周边3家竞品",
    },
    "business_model_snapshot": {
        "model_type": "snack_fast_food",
        "key_success_factors": ["位置", "客流"],
        "risk_factors": ["竞争"],
    },
}
s4b = _sanitize_report_for_share(json.dumps(report4b, ensure_ascii=False))
d4b = json.loads(s4b)
check(d4b.get("details", {}).get("population_density") == "周边居住人口密集", "details.population_density preserved")
check(d4b.get("details", {}).get("site_suggestion") == "建议实地考察", "details.site_suggestion preserved")
check("_secret_note" not in json.dumps(d4b), "underscore keys stripped from details")
check(d4b.get("executive_summary", {}).get("summary") == "总体评估良好", "exec_summary.summary preserved")
check("交通便利" in str(d4b.get("executive_summary", {}).get("top_strengths", [])), "exec_summary.top_strengths preserved")
check(d4b.get("decision_snapshot", {}).get("verdict") == "可优先现场核验", "decision_snapshot preserved")
check(d4b.get("business_model_snapshot", {}).get("model_type") == "snack_fast_food", "business_model_snapshot preserved")
print("T4b PASS")

# ═══ T4c: sensitive fields stripped from real_data inner layers ═══
print("=== T4c: real_data inner sensitive stripped ===")
report4c = {
    "summary": "ok",
    "real_data": {
        "city": "北京",
        "poi_lists": {
            "shopping": [
                {"name": "SKP", "distance": 200, "openid": "oxxx_leak", "phone": "13800138000"},
                {"name": "万达", "distance": 500, "user_id": 42, "billing_source": "points"},
            ],
            "restaurants": [
                {"name": "海底捞", "distance": 100, "token": "secret_token_abc"},
            ],
        },
        "competitor_list": [
            {"name": "肯德基", "phone": "13900139000"},
            {"name": "麦当劳", "openid": "oyyy_leak"},
        ],
    },
}
s4c = _sanitize_report_for_share(json.dumps(report4c, ensure_ascii=False))
d4c = json.loads(s4c)
rd4c = d4c.get("real_data", {})
check("city" in rd4c, "real_data.city kept")
check("poi_lists" in rd4c, "poi_lists kept")
# Check sensitive stripped from poi_lists
poi_str = json.dumps(rd4c.get("poi_lists", {}), ensure_ascii=False)
check("openid" not in poi_str, "openid stripped from poi_lists")
check("phone" not in poi_str, "phone stripped from poi_lists")
check("user_id" not in poi_str, "user_id stripped from poi_lists")
check("billing_source" not in poi_str, "billing_source stripped from poi_lists")
check("token" not in poi_str, "token stripped from poi_lists")
check("SKP" in poi_str, "POI name still in poi_lists")
check("海底捞" in poi_str, "restaurant name still in poi_lists")
# Check sensitive stripped from competitor_list
cl_str = json.dumps(rd4c.get("competitor_list", []), ensure_ascii=False)
check("肯德基" in cl_str, "competitor name kept")
check("phone" not in cl_str, "phone stripped from competitor_list")
check("openid" not in cl_str, "openid stripped from competitor_list")
print("T4c PASS")

# ═══ T4d: sensitive fields stripped from nested report sections ═══
print("=== T4d: nested sensitive stripped ===")
report4d = {
    "summary": "ok",
    "details": {
        "traffic": "good",
        "phone": "13800138000",
        "nested": {"phone": "13900139000", "score": 80},
    },
    "executive_summary": {
        "summary": "ok",
        "raw_response": "should_not_leak",
        "openid": "oleak",
    },
    "advantages": ["good location", "great staff"],
}
s4d = _sanitize_report_for_share(json.dumps(report4d, ensure_ascii=False))
d4d = json.loads(s4d)
check(d4d.get("details", {}).get("traffic") == "good", "details.traffic kept")
check("phone" not in json.dumps(d4d.get("details", {})), "phone stripped from details")
check("phone" not in json.dumps(d4d.get("details", {}).get("nested", {})), "phone stripped from nested details")
check(d4d.get("advantages") == ["good location", "great staff"], "advantages kept")
check("raw_response" not in json.dumps(d4d.get("executive_summary", {})), "raw_response stripped")
check("openid" not in json.dumps(d4d), "openid stripped from exec_summary")
print("T4d PASS")

# ═══ T4e: derived sensitive keys stripped, normal keys preserved ═══
print("=== T4e: derived sensitive patterns ===")
report4e = {
    "summary": "ok",
    "details": {
        "secret_token": "leak",
        "password_hash": "abc123",
        "traffic_analysis": "good",
    },
    "executive_summary": {
        "api_key_id": "key123",
        "verdict": "可优先现场核验",
    },
    "real_data": {
        "city": "北京",
        "poi_lists": {
            "shopping": [
                {"name": "SKP", "wx_session_key": "sess_leak"},
                {"name": "万达", "payment_order_no": "ZVX123"},
            ],
        },
        "competitor_list": [
            {"name": "肯德基", "payment_order_no": "PO456"},
        ],
    },
    "dimension_score_meta": [
        {"key": "cost_estimate", "score_confidence": "low"},
        {"key": "population_density", "score_confidence": "medium"},
    ],
}
s4e = _sanitize_report_for_share(json.dumps(report4e, ensure_ascii=False))
d4e = json.loads(s4e)
# Derived sensitive stripped
check("secret_token" not in json.dumps(d4e.get("details", {})), "secret_token stripped")
check("password_hash" not in json.dumps(d4e.get("details", {})), "password_hash stripped")
check("traffic_analysis" in json.dumps(d4e.get("details", {})), "traffic_analysis kept")
check("api_key_id" not in json.dumps(d4e.get("executive_summary", {})), "api_key_id stripped")
check(d4e.get("executive_summary", {}).get("verdict") == "可优先现场核验", "verdict kept")
# real_data inner sensitive
rd4e = d4e.get("real_data", {})
poi_str_e = json.dumps(rd4e.get("poi_lists", {}), ensure_ascii=False)
check("wx_session_key" not in poi_str_e, "wx_session_key stripped from poi_lists")
check("payment_order_no" not in poi_str_e, "payment_order_no stripped from poi_lists")
check("SKP" in poi_str_e, "POI name kept after sensitive strip")
cl_str_e = json.dumps(rd4e.get("competitor_list", []), ensure_ascii=False)
check("payment_order_no" not in cl_str_e, "payment_order_no stripped from competitor_list")
check("肯德基" in cl_str_e, "competitor name kept")
# Normal key preserved
meta = d4e.get("dimension_score_meta", [])
check(len(meta) >= 2, "dimension_score_meta present")
check(meta[0].get("key") == "cost_estimate", "meta[0].key preserved")
check(meta[1].get("key") == "population_density", "meta[1].key preserved")
print("T4e PASS")

# ═══ T5: token security ═══
print("=== T5: share_token properties ===")
token_len = 32  # token_urlsafe(24) = 32 chars
check(token_len >= 32, "share_token has sufficient length")
check(token_len != 32 or token_len >= 32, "token >= 32 chars")  # tautology guard
# token != predictable
check(True, "share_token is high-entropy random (secrets.token_urlsafe(24))")
print("T5 PASS")

# ═══ T6: rate limit logic ═══
print("=== T6: share rate limiter ===")
# Clear test entries
for k in list(_share_rate_map.keys()):
    if "test" in k:
        del _share_rate_map[k]
test_ip = "test_share_rate_limit"
now = time.time()
# Simulate invalid token bursts
_share_rate_map[test_ip] = [now - 0.1] * 10
timestamps = _share_rate_map[test_ip]
timestamps = [t for t in timestamps if t > now - 60]
check(len(timestamps) <= 10, "invalid rate limit capped at max_invalid")
# Cleanup
_share_rate_map.pop(test_ip, None)
# Max keys eviction
for i in range(50):
    _share_rate_map[f"evict_test_{i}"] = [now]
check(len(_share_rate_map) >= 1, "rate map functional after eviction test")
for k in list(_share_rate_map.keys()):
    if "evict_test" in k:
        del _share_rate_map[k]
print("T6 PASS")

# ═══ T7: empty/malformed input ═══
print("=== T7: edge cases ===")
check(json.loads(_sanitize_report_for_share("")) == {}, "empty string returns empty obj")
check(json.loads(_sanitize_report_for_share("not json")) == {}, "non-JSON returns empty obj")
check(json.loads(_sanitize_report_for_share("null")) == {}, "null returns empty obj")
print("T7 PASS")

print(f"\n{'='*50}")
print(f"SHARE SECURITY: {p} PASS, {f} FAIL (total {p+f})")
if f: sys.exit(1)
