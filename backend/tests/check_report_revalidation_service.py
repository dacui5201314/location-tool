"""Phase B: 存量报告重新校验测试"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_revalidation_service import classify_legacy_report_status, revalidate_report_record

f = 0
p = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")


def _make_report(**kw):
    base = {"details":{},"advantages":[],"disadvantages":[],"executive_summary":{},
            "action_plan":[],"summary":"","location_profile":{},"location_fundamentals":{},
            "business_model_snapshot":{},"decision_snapshot":{},"field_checklist":[],"evidence_summary":{},
            "dimension_scores":[{"key":"a","score":50}]*8,"score":50}
    base.update(kw)
    return base

def _make_rd(**kw):
    base = {"stats_200m":{},"stats_500m":{"bus":2},"stats_1000m":{"bus":5},
            "direct_competitors_200m":0,"direct_competitors_500m":0,"direct_competitors_1000m":0,
            "substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,
            "traffic_anchors_200m":0,"traffic_anchors_500m":0,"traffic_anchors_1000m":0,
            "direct_competitor_list":[],"substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
            "rigor_enabled":True,"subway_applicable":True,"city_has_subway":False}
    base.update(kw)
    return base

# ═══ T-RV-01: 新版报告 → current_ok ═══
print("=== T-RV-01: new report with schema_version -> current_ok ===")
rpt1 = _make_report(_report_schema_version="2026-06-report-quality-v1")
rd1 = _make_rd()
res1 = classify_legacy_report_status(rpt1, report_file="/tmp/x.html", real_data=rd1)
check(res1["status"] == "current_ok", f"should be current_ok: {res1['status']}")
print("T-RV-01 PASS")

# ═══ T-RV-02: 旧报告无硬错误 → legacy_warning ═══
print("=== T-RV-02: old report no hard errors -> legacy_warning ===")
rpt2 = _make_report()
rd2 = _make_rd()
res2 = classify_legacy_report_status(rpt2, report_file="/tmp/x.html", real_data=rd2)
check(res2["status"] == "legacy_warning", f"should be legacy_warning: {res2['status']}")
check(res2["legacy_notice"] != "", "should have legacy_notice")
print("T-RV-02 PASS")

# ═══ T-RV-03: 旧报告公交半径错配 → legacy_failed_fact_guard ═══
print("=== T-RV-03: radius mismatch -> legacy_failed_fact_guard ===")
rpt3 = _make_report(
    decision_snapshot={"top_strength": "500米半径内5个公交站点"}
)
rd3 = _make_rd(stats_500m={"bus":2}, stats_1000m={"bus":5})
res3 = classify_legacy_report_status(rpt3, report_file="/tmp/x.html", real_data=rd3)
check(res3["status"] == "legacy_failed_fact_guard", f"should be failed: {res3['status']}")
check(len(res3["hard_errors"]) > 0, f"should have hard errors: {res3['hard_errors']}")
check("口径" in res3["legacy_notice"] or "重新生成" in res3["legacy_notice"],
      f"notice should suggest regenerate: {res3['legacy_notice']}")
print("T-RV-03 PASS")

# ═══ T-RV-04: 缺 real_data → legacy_unchecked ═══
print("=== T-RV-04: no real_data -> legacy_unchecked ===")
rpt4 = _make_report()
res4 = classify_legacy_report_status(rpt4, report_file="/tmp/x.html", real_data=None)
check(res4["status"] == "legacy_unchecked", f"should be unchecked: {res4['status']}")
check("缺少原始事实数据" in res4["legacy_notice"] or "真实数据" in res4["legacy_notice"],
      f"should mention missing data: {res4['legacy_notice']}")
print("T-RV-04 PASS")

# ═══ T-RV-05: report_file 有、report_url 空 → storage_pending ═══
print("=== T-RV-05: has report_file no url -> storage_pending ===")
res5 = classify_legacy_report_status(_make_report(), report_file="/tmp/x.html", report_url="", real_data=_make_rd())
check(res5["storage_sync_status"] == "pending", f"should be pending: {res5['storage_sync_status']}")
print("T-RV-05 PASS")

# ═══ T-RV-06: report_url 有 → storage_synced ═══
print("=== T-RV-06: has report_url -> storage_synced ===")
res6 = classify_legacy_report_status(_make_report(), report_file="", report_url="https://cos/x.html", real_data=_make_rd())
check(res6["storage_sync_status"] == "synced", f"should be synced: {res6['storage_sync_status']}")
print("T-RV-06 PASS")

# ═══ T-RV-07: dry-run 不写库 ═══
print("=== T-RV-07: dry-run does not write ===")
_rd7 = _make_rd(stats_500m={"bus":2}, stats_1000m={"bus":5})
_rpt7 = _make_report(decision_snapshot={"top_strength":"500米半径内5个公交站点"}, real_data=_rd7)

class MockRec:
    def __init__(self, rid, rpt_json, rfile="", rurl=""):
        self.id = rid; self.report_json = rpt_json; self.report_file = rfile; self.report_url = rurl

rec7 = MockRec(1, json.dumps(_rpt7, ensure_ascii=False), "/tmp/x.html", "")
orig_json = rec7.report_json
res7 = revalidate_report_record(rec7, dry_run=True)
check(res7["status"] == "legacy_failed_fact_guard", f"dry_run should detect failure: {res7['status']}")
check(rec7.report_json == orig_json, "dry_run must not modify report_json")
print("T-RV-07 PASS")

# ═══ T-RV-08: run 模式写 _fact_guard_status ═══
print("=== T-RV-08: run writes meta fields ===")
_rpt8 = _make_report(decision_snapshot={"top_strength":"500米半径内5个公交站点"}, real_data=_rd7)
rec8 = MockRec(2, json.dumps(_rpt8, ensure_ascii=False), "/tmp/x.html", "")
res8 = revalidate_report_record(rec8, dry_run=False)
check(res8["status"] == "legacy_failed_fact_guard", f"should be failed: {res8['status']}")
updated = json.loads(rec8.report_json)
check("_fact_guard_status" in updated, "run must write _fact_guard_status")
check("_legacy_report_notice" in updated, "run must write _legacy_report_notice")
check("_report_schema_version" in updated, "run must write _report_schema_version")
check(updated.get("details") is not None, "original fields preserved")
print("T-RV-08 PASS")

# ═══ T-RV-09: 失败报告 run 后，再次 classify 仍是 legacy_failed_fact_guard ═══
print("=== T-RV-09: failed stays failed on re-classify ===")
_rd9 = _make_rd(stats_500m={"bus":2}, stats_1000m={"bus":5})
_rpt9 = _make_report(decision_snapshot={"top_strength":"500米半径内5个公交站点"}, real_data=_rd9)
rec9 = MockRec(9, json.dumps(_rpt9, ensure_ascii=False), "/tmp/x.html", "")
# first run: writes failed meta
revalidate_report_record(rec9, dry_run=False)
# second classify: must still be legacy_failed_fact_guard
res9 = classify_legacy_report_status(json.loads(rec9.report_json), report_file="/tmp/x.html")
check(res9["status"] == "legacy_failed_fact_guard",
      f"second classify must stay failed, got: {res9['status']}")
print("T-RV-09 PASS")

# ═══ T-RV-10: 有 _report_schema_version 但 _fact_guard_status=failed → failed ═══
print("=== T-RV-10: schema_version + fg_status=failed -> legacy_failed ===")
rpt10 = _make_report(_report_schema_version="2026-06-report-quality-v1",
                     _fact_guard_status="failed",
                     _legacy_report_notice="旧版失败", real_data=_rd9)
res10 = classify_legacy_report_status(rpt10, report_file="/tmp/x.html")
check(res10["status"] == "legacy_failed_fact_guard",
      f"schema_version + failed must be legacy_failed: {res10['status']}")
print("T-RV-10 PASS")

# ═══ T-RV-11: 缺 real_data run 后写入 _fact_guard_status=unchecked ═══
print("=== T-RV-11: no real_data run writes unchecked ===")
_rpt11 = _make_report()
rec11 = MockRec(11, json.dumps(_rpt11, ensure_ascii=False), "/tmp/x.html", "")
res11 = revalidate_report_record(rec11, dry_run=False)
check(res11["status"] == "legacy_unchecked", f"should be unchecked: {res11['status']}")
updated11 = json.loads(rec11.report_json)
check(updated11.get("_fact_guard_status") == "unchecked", "unchecked run writes _fact_guard_status")
check(updated11.get("_legacy_report_notice") != "", "unchecked run writes notice")
check("缺少" in updated11.get("_legacy_report_notice", ""), "notice mentions missing data")
print("T-RV-11 PASS")

# ═══ T-RV-12: dry-run 缺 real_data 不修改 report_json ═══
print("=== T-RV-12: dry-run no real_data does not mutate ===")
_rpt12 = _make_report()
rec12 = MockRec(12, json.dumps(_rpt12, ensure_ascii=False), "/tmp/x.html", "")
orig12 = rec12.report_json
revalidate_report_record(rec12, dry_run=True)
check(rec12.report_json == orig12, "dry-run unchecked must not modify report_json")
print("T-RV-12 PASS")

# ═══ T-RV-13: admin limit clamp ═══
print("=== T-RV-13: admin limit clamp ===")
# 静态检查源码
admin_src = open(os.path.join(os.path.dirname(__file__), '..', 'routers', 'admin.py'), 'r', encoding='utf-8').read()
check("max(1, min(body.limit" in admin_src, "admin limit must use max(1, min(...))")
check("limit=limit" in admin_src, "admin must pass clamped limit")
print("T-RV-13 PASS")

print(f"\n{'='*50}")
print(f"REVALIDATION: {p} PASS, {f} FAIL (total {p+f})")
if f: sys.exit(1)
