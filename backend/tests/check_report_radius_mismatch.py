"""Phase 4N 半径错配 + 小数字校验 + final guard split 测试"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from report_fact_guard import check_radius_mismatch, _validate_small_counts, build_user_visible_report_text, validate_report_fact_consistency, split_final_guard_issues
import json

f = 0
p = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")

# ============ 半径错配正例 (T-RM-01 ~ T-RM-02) ============
print("=== T-RM-01: 500m bus=2, claim 5 from 1000m -> block ===")
rd = {"stats_500m": {"bus": 2}, "stats_1000m": {"bus": 5}, "stats_200m": {}}
report = "500米半径内5个公交站点，交通网络密集。"
issues = check_radius_mismatch(report, rd)
check(len(issues) > 0, f"should block: {issues}")

print("=== T-RM-02: 500m office=1, claim 5 from 1000m -> block ===")
rd2 = {"stats_500m": {"office": 1}, "stats_1000m": {"office": 5}, "stats_200m": {}}
report2 = "500米半径内有5栋写字楼。"
issues2 = check_radius_mismatch(report2, rd2)
check(len(issues2) > 0, f"should block office mismatch: {issues2}")

# ============ false-positive 反例 (T-RM-03 ~ T-RM-07) ============
print("=== T-RM-03: correct reference passes ===")
report_ok = "500米半径内2个公交站点，1000米内5个公交站点。"
issues_ok = check_radius_mismatch(report_ok, rd)
check(len(issues_ok) == 0, f"should pass: {issues_ok}")

print("=== T-RM-04: 500m 5 hotels doesnt trigger bus ===")
rd3 = {"stats_500m": {"bus": 2, "hotels": 5}, "stats_1000m": {"bus": 5}}
report3 = "500米内5家酒店，交通便利。"
issues3 = check_radius_mismatch(report3, rd3)
check(len(issues3) == 0, f"hotels should not trigger bus mismatch: {issues3}")

print("=== T-RM-05: 500m 5 parking doesnt trigger bus ===")
rd4 = {"stats_500m": {"bus": 2, "parking": 5}, "stats_1000m": {}}
report4 = "500米内5个停车场。"
issues4 = check_radius_mismatch(report4, rd4)
check(len(issues4) == 0, f"parking should not trigger bus: {issues4}")

print("=== T-RM-06: 500 as radius number not mistaken ===")
rd5 = {"stats_500m": {"bus": 3}, "stats_1000m": {"bus": 8}}
report5 = "500米范围覆盖3个公交站。"
issues5 = check_radius_mismatch(report5, rd5)
check(len(issues5) == 0, f"500 as radius should not trigger: {issues5}")

print("=== T-RM-07: multi-radius sentence split correctly ===")
report7 = "500米内2个公交站，1000米内5个公交站"
issues7 = check_radius_mismatch(report7, rd)
check(len(issues7) == 0, f"multi-radius sentence should pass: {issues7}")

# ============ 小数字校验 (T-RM-08 ~ T-RM-09) ============
print("=== T-RM-08: small count bus=2 inflated to 5 -> block ===")
issues_sm = _validate_small_counts("500米内5个公交站", rd)
check(any("bus=2" in i for i in issues_sm), f"small count should catch: {issues_sm}")

print("=== T-RM-09: small count bus=2 correct -> pass ===")
issues_sm2 = _validate_small_counts("500米内2个公交站", rd)
check(len(issues_sm2) == 0, f"correct small count should pass: {issues_sm2}")

# ============ 统一文本构造器 (T-RM-10 ~ T-RM-11) ============
print("=== T-RM-10: build_user_visible_report_text covers 12 fields ===")
result = {
    "details": {"test": 1}, "advantages": ["a"], "disadvantages": ["d"],
    "executive_summary": {"s": "x"}, "action_plan": ["act"],
    "summary": "s", "location_profile": {"lp": 1},
    "location_fundamentals": {"lf": 1}, "business_model_snapshot": {"bm": 1},
    "decision_snapshot": {"ds": 1}, "field_checklist": [{"fc": 1}],
    "evidence_summary": {"ev": 1},
}
txt = build_user_visible_report_text(result)
for field in ["details","advantages","disadvantages","executive_summary",
              "action_plan","summary","location_profile","location_fundamentals",
              "business_model_snapshot","decision_snapshot","field_checklist","evidence_summary"]:
    check(field.replace("_","") in txt.lower() or json.dumps(result[field])[:5] in txt,
          f"{field} should appear in user_visible_text")

print("=== T-RM-11: validate scans decision_snapshot ===")
rd_test = {"stats_500m": {"bus": 2}, "stats_1000m": {"bus": 5}, "stats_200m": {}}
result_test = {
    "dimension_scores": [{"key":"a","score":50}]*8,
    "decision_snapshot": {"top_strength": "500米半径内5个公交站点"},
    "details": {}, "advantages": [], "disadvantages": [], "executive_summary": {},
    "action_plan": [], "summary": "", "location_profile": {}, "location_fundamentals": {},
    "business_model_snapshot": {}, "field_checklist": [], "evidence_summary": {},
}
fe = validate_report_fact_consistency(result_test, rd_test)
check(any("RADIUS-MISMATCH" in e for e in fe),
      f"decision_snapshot should be scanned: {fe}")

# ============ final guard split 测试 (T-SPLIT-01 ~ T-SPLIT-08) ============
print("=== T-SPLIT-01: [RADIUS-MISMATCH] -> hard_error ===")
hard, warn = split_final_guard_issues(["[RADIUS-MISMATCH] bus=5"])
check(len(hard) == 1 and len(warn) == 0, f"RADIUS-MISMATCH must be hard: h={len(hard)} w={len(warn)}")

print("=== T-SPLIT-02: [SMALL-COUNT] -> hard_error ===")
hard, warn = split_final_guard_issues(["[SMALL-COUNT] 500m bus=2 but report says 5"])
check(len(hard) == 1 and len(warn) == 0, f"SMALL-COUNT must be hard")

print("=== T-SPLIT-03: [DECISION] -> hard_error ===")
hard, warn = split_final_guard_issues(["[DECISION] 推荐开店"])
check(len(hard) == 1 and len(warn) == 0, f"DECISION must be hard")

print("=== T-SPLIT-04: [FINANCE] -> hard_error ===")
hard, warn = split_final_guard_issues(["[FINANCE] 月净利4.7万"])
check(len(hard) == 1 and len(warn) == 0, f"FINANCE must be hard")

print("=== T-SPLIT-05: but report says -> hard_error ===")
hard, warn = split_final_guard_issues(["stats_500m.bus=2 but report says 5"])
check(len(hard) == 1 and len(warn) == 0, f"but report says must be hard")

print("=== T-SPLIT-06: old field -> hard_error ===")
hard, warn = split_final_guard_issues(["has_rigor=True but report references old field"])
check(len(hard) == 1 and len(warn) == 0, f"old field must be hard")

print("=== T-SPLIT-07: dim count -> warning ===")
hard, warn = split_final_guard_issues(["dimension_scores 不足8维"])
check(len(hard) == 0 and len(warn) == 1, f"should be warning: h={len(hard)} w={len(warn)}")

print("=== T-SPLIT-08: mixed -> correct ===")
hard, warn = split_final_guard_issues([
    "[RADIUS-MISMATCH] bus=5", "dimension_scores 不足8维",
    "[SMALL-COUNT] schools=3 but 10", "normal observation"])
check(len(hard) == 2 and len(warn) == 2, f"mixed: h={len(hard)} w={len(warn)}")

# ============ 最终汇总（必须在所有测试之后） ============
print(f"\n{'='*50}")
total = p + f
print(f"RADIUS MISMATCH + SPLIT: {p} PASS, {f} FAIL (total {total})")
if f:
    sys.exit(1)
