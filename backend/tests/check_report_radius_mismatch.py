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

# ============ 服务器真实触发句子回归 (T-SRV-01 ~ T-SRV-05) ============
rd_srv = {"stats_500m": {"residential": 1, "office": 0, "schools": 4, "hospitals": 0, "bus": 6, "subway": 0},
          "stats_1000m": {"residential": 3, "office": 0, "schools": 8, "hospitals": 1, "bus": 12, "hotels": 2},
          "stats_200m": {}}

# T-SRV-01: server fallback trigger sentence must NOT false-positive
print("=== T-SRV-01: server fallback hospitals=0 not mismatched ===")
s1 = "500米半径内1个住宅小区、0栋办公建筑、4所教育机构、0家医院"
issues1 = check_radius_mismatch(s1, rd_srv)
check(len(issues1) == 0, f"server fallback sentence must pass: {issues1}")

# T-SRV-02: real 500m bus=2, 1000m bus=5, claim 5 at 500m still blocked
print("=== T-SRV-02: 500m bus=2 claim 5 from 1000m still blocked ===")
rd_bus = {"stats_500m": {"bus": 2}, "stats_1000m": {"bus": 5}, "stats_200m": {}}
s2 = "500米内5个公交站"
issues2 = check_radius_mismatch(s2, rd_bus)
check(len(issues2) > 0, f"real mismatch must be blocked: {issues2}")

# T-SRV-03: "5个小区、2个公交站" must not confuse residential with bus
print("=== T-SRV-03: 5个小区 not confused with bus ===")
rd_mix = {"stats_500m": {"residential": 5, "bus": 2}, "stats_1000m": {"residential": 20, "bus": 8}, "stats_200m": {}}
s3 = "500米内5个小区、2个公交站"
issues3 = check_radius_mismatch(s3, rd_mix)
check(len(issues3) == 0, f"mixed categories must not cross-match: {issues3}")

# T-SRV-04: "500米内2个公交站，1000米内5个公交站" still passes
print("=== T-SRV-04: correct multi-radius still passes ===")
s4 = "500米内2个公交站，1000米内5个公交站"
issues4 = check_radius_mismatch(s4, rd_bus)
check(len(issues4) == 0, f"correct multi-radius must pass: {issues4}")

# T-SRV-05: same radius appears twice in JSON-serialized string
print("=== T-SRV-05: dual 500m in JSON text splits correctly ===")
s5 = '1000米范围5个流量节点，商业活跃度较高"] ["500米内无地铁站，公共交通以公交为主", "500米内仅4个住宅小区'
issues5 = check_radius_mismatch(s5, rd_srv)
# "500米内仅4个住宅小区" has 500m residential=4 which matches rd_srv stats_500m.residential=1? No, rd_srv has res=1.
# Actually rd_srv stats_500m.residential=1. Claimed=4. Other radius: 1000m residential=3. 4 != 3 either. So no mismatch.
# Let's use matching data
rd_s5 = {"stats_500m": {"residential": 4, "bus": 0}, "stats_1000m": {"residential": 15, "bus": 8}, "stats_200m": {}}
issues5 = check_radius_mismatch(s5, rd_s5)
# "500米内仅4个住宅小区" should not trigger because 500m residential=4 matches claim=4
check(len(issues5) == 0, f"JSON dual-radius split must pass: {issues5}")

# ============ LLM 长句 + 1公里变体 (T-SRV-06 ~ T-SRV-08) ============
rd_srv2 = {"stats_500m": {"residential": 1, "office": 0, "schools": 4, "hospitals": 0},
           "stats_1000m": {"residential": 3, "schools": 8, "hospitals": 1},
           "stats_200m": {}}

# T-SRV-06: LLM mixes 500m and 1公里 in one sentence — must not FP
print("=== T-SRV-06: 1公里 splits correctly, hospitals not attributed to 500m ===")
s6 = "500米覆盖范围内仅有1个住宅小区、4所学校（含中学和幼儿园），1公里商圈内住宅增至3个、学校增至8所、医院1家"
issues6 = check_radius_mismatch(s6, rd_srv2)
check(len(issues6) == 0, f"1公里 must split from 500m: {issues6}")

# T-SRV-07: "500米内无医院，1公里内仅1家医疗机构" — doctors keyword variant
print("=== T-SRV-07: 医疗机构 matches hospitals, 1公里 splits ===")
s7 = "500米内无医院，1公里内仅1家医疗机构"
issues7 = check_radius_mismatch(s7, rd_srv2)
check(len(issues7) == 0, f"医疗机构 at 1km must not FP: {issues7}")

# T-SRV-08: "500米覆盖范围内医院为0，1公里商圈内仅1家医疗机构"
print("=== T-SRV-08: 500米覆盖范围 + 1公里商圈 both split ===")
s8 = "500米覆盖范围内医院为0，1公里商圈内仅1家医疗机构，缺少医院陪护及探病客流"
issues8 = check_radius_mismatch(s8, rd_srv2)
check(len(issues8) == 0, f"two LLM radius variants must split: {issues8}")

# ============ 全业态 validate_report_fact_consistency (T-MBT-01 ~ T-MBT-05) ============
from report_fact_guard import validate_report_fact_consistency

def _mk_rpt(**kw):
    b = {"dimension_scores":[{"key":"a","score":50}]*8,"details":{},"advantages":[],"disadvantages":[],
         "executive_summary":{},"action_plan":[],"summary":"","location_profile":{},"location_fundamentals":{},
         "business_model_snapshot":{},"decision_snapshot":{},"field_checklist":[],"evidence_summary":{}}
    b.update(kw)
    return b

# T-MBT-01: bus mismatch in validate
print("=== T-MBT-01: validate catches bus 500m=2 claim 5 ===")
rd1 = {"stats_500m":{"bus":2},"stats_1000m":{"bus":5},"stats_200m":{}}
rpt1 = _mk_rpt(decision_snapshot={"top_strength":"500米内5个公交站，交通便利"})
fe1 = validate_report_fact_consistency(rpt1, rd1)
check(any("bus" in e.lower() or "5" in e.split("but report says")[-1] if "but report says" in e else False for e in fe1) or any("bus=2 but report says 5" in e or "stats_500m.bus=2 but" in e for e in fe1), f"must catch bus mismatch: {fe1}")

# T-MBT-02: correct multi-radius passes validate
print("=== T-MBT-02: validate passes correct multi-radius ===")
rpt2 = _mk_rpt(summary="500米内2个公交站，1公里内5个公交站")
fe2 = validate_report_fact_consistency(rpt2, rd1)
check(not any("RADIUS-MISMATCH" in e for e in fe2), f"correct must pass: {fe2}")

# T-MBT-03: 教育 — schools + bus in validate
print("=== T-MBT-03: education schools+residential+bus ===")
rd3 = {"stats_500m":{"schools":4,"residential":3,"bus":3},"stats_1000m":{"schools":9,"residential":10,"bus":8},"stats_200m":{"schools":1}}
rpt3 = _mk_rpt(summary="500米内4所学校、3个小区、3个公交站，1公里内9所学校")
fe3 = validate_report_fact_consistency(rpt3, rd3)
check(not any("RADIUS-MISMATCH" in e for e in fe3), f"edu multi-radius must pass: {fe3}")

# T-MBT-04: 酒店 — hotels + parking + bus in validate
print("=== T-MBT-04: hotel hotels+parking+bus multi-radius ===")
rd4 = {"stats_500m":{"hotels":2,"parking":3,"bus":4},"stats_1000m":{"hotels":8,"parking":15,"bus":12},"stats_200m":{}}
rpt4 = _mk_rpt(summary="500米内2家酒店、3个停车场、4个公交站，1公里内8家酒店")
fe4 = validate_report_fact_consistency(rpt4, rd4)
check(not any("RADIUS-MISMATCH" in e for e in fe4), f"hotel multi-radius must pass: {fe4}")

# T-MBT-05: 零售便利 — shopping/office/bus in validate, 1公里变体
print("=== T-MBT-05: retail shopping+office+bus 1公里 ===")
rd5 = {"stats_500m":{"shopping":1,"office":2,"bus":3},"stats_1000m":{"shopping":4,"office":8,"bus":10},"stats_200m":{}}
rpt5 = _mk_rpt(summary="500米内1个商场、2栋写字楼、3个公交站，1公里商圈内4个商场、8栋写字楼")
fe5 = validate_report_fact_consistency(rpt5, rd5)
check(not any("RADIUS-MISMATCH" in e for e in fe5), f"retail 1km must pass: {fe5}")

# T-MBT-06: 医疗/药店 — hospitals+clinics 多半径
print("=== T-MBT-06: medical hospitals+clinics multi-radius ===")
rd6 = {"stats_500m":{"hospitals":0},"stats_1000m":{"hospitals":1},"stats_200m":{}}
rpt6_ok = _mk_rpt(summary="500米内无医院，1公里内1家医疗机构")
fe6_ok = validate_report_fact_consistency(rpt6_ok, rd6)
check(not any("RADIUS-MISMATCH" in e for e in fe6_ok), f"medical correct must pass: {fe6_ok}")
rpt6_bad = _mk_rpt(summary="500米内1家诊所")
fe6_bad = validate_report_fact_consistency(rpt6_bad, rd6)
check(any("hospitals=0 but" in e or "RADIUS-MISMATCH" in e for e in fe6_bad),
      f"medical 500m claim 1 with 0 actual must be caught: {fe6_bad}")

# T-MBT-07: 服务/娱乐 — direct_competitors 口径
print("=== T-MBT-07: service direct_competitors multi-radius ===")
rd7 = {"direct_competitors_500m":0,"direct_competitors_1000m":4,"direct_competitors_200m":0,
       "stats_500m":{},"stats_1000m":{},"stats_200m":{}}
rpt7_ok = _mk_rpt(summary="500米内无直接竞品，1公里内4家同类竞品")
fe7_ok = validate_report_fact_consistency(rpt7_ok, rd7)
check(not any("RADIUS-MISMATCH" in e for e in fe7_ok), f"service correct multi-radius must pass: {fe7_ok}")
rpt7_bad = _mk_rpt(summary="500米内4家同类竞品")
fe7_bad = validate_report_fact_consistency(rpt7_bad, rd7)
check(any("direct_competitors_500m=0 but" in e for e in fe7_bad),
      f"service 500m claim 4 with 0 actual must be caught: {fe7_bad}")

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
