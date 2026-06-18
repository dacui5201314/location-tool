"""Phase 3 表达归位 + 矛盾解释测试"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.report_expression_normalizer import (
    normalize_advantage_risk_phrasing,
    add_demand_contradiction_note,
    _has_risk_phrasing,
    _split_advantage_risk,
)

f = 0
p = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")


# ============ T-E-01: 纯优势不变 ============
print("=== T-E-01: pure advantage stays ===")
report = {"advantages": ["500米内6个公交站点，地面交通覆盖较好"]}
result = normalize_advantage_risk_phrasing(report)
check("公交" in str(result["advantages"]), f"pure advantage should stay: {result['advantages']}")
check(len(result.get("risk_notes", [])) == 0, "no risk notes for pure advantage")
print("T-E-01 PASS")

# ============ T-E-02: 带转折的优势拆分 ============
print("=== T-E-02: advantage with 'but' splits ===")
report2 = {
    "advantages": [
        "200m内同品类供给较少，但1000m同类门店5家、餐饮79家，需核验近场空档是否由低客流导致"
    ]
}
result2 = normalize_advantage_risk_phrasing(report2)
adv_text = " ".join(str(a) for a in result2.get("advantages", []))
check("200m内同品类供给较少" in adv_text, f"prefix should stay: {adv_text}")
check("1000m同类门店5家" not in adv_text, f"suffix should move out: {adv_text}")
check(len(result2.get("risk_notes", [])) > 0, "risk notes should exist")
print("T-E-02 PASS")

# ============ T-E-03: top_strength 不选风险句 ============
print("=== T-E-03: top_strength skips risky sentence ===")
report3 = {
    "advantages": ["200m内同品类供给较少"],
    "decision_snapshot": {"top_strength": "200m内同品类供给较少，但需核验低客流风险"}
}
result3 = normalize_advantage_risk_phrasing(report3)
ts3 = result3.get("decision_snapshot", {}).get("top_strength", "")
check("但" not in ts3, f"top_strength must not have 'but': {ts3}")
check("低客流" not in ts3, f"top_strength must not have risk: {ts3}")
print("T-E-03 PASS")

# ============ T-E-04: 整句无独立优势则整体移出 ============
print("=== T-E-04: no standalone prefix -> whole sentence moved ===")
report4 = {
    "advantages": ["只有低租金小档口模型才有继续考察价值"]
}
result4 = normalize_advantage_risk_phrasing(report4)
check("只有" not in str(result4.get("advantages", [])),
      f"conditional-only should leave advantages: {result4['advantages']}")
check(any("低租金" in r for r in result4.get("risk_notes", [])),
       f"conditional should be in risk_notes: {result4.get('risk_notes')}")
print("T-E-04 PASS")

# ============ T-E-05: 附件样例 — 优势归位不删风险 ============
print("=== T-E-05: attachment sample — advantage split, risk kept ===")
rd_att = {
    "stats_500m": {"residential": 1, "office": 0, "bus": 2},
    "stats_1000m": {"restaurants": 79, "hotels": 14, "bus": 5},
    "direct_competitors_200m": 0, "direct_competitors_1000m": 4,
}
report5 = {
    "advantages": [
        "200m内同品类供给较少",
        "200m内同品类供给较少，但1000m同类门店4家、餐饮79家，需核验低客流风险"
    ],
    "disadvantages": ["500米内无地铁覆盖"],
    "decision_snapshot": {"top_strength": "200m内同品类供给较少，但需核验低客流"},
    "business_type": "小吃快餐",
}
result5 = normalize_advantage_risk_phrasing(report5)
result5 = add_demand_contradiction_note(result5, rd_att)

# 断言1: 纯优势保留
adv5 = " ".join(str(a) for a in result5.get("advantages", []))
check("200m内同品类供给较少" in adv5, f"pure advantage kept: {adv5}")
# 断言2: top_strength 不含风险
ts5 = result5.get("decision_snapshot", {}).get("top_strength", "")
check("但" not in ts5, f"top_strength clean: {ts5}")
check("低客流" not in ts5, f"top_strength no risk: {ts5}")
# 断言3: 风险信息移到 risk_notes / disadvantages
all_risks = " ".join(str(r) for r in result5.get("risk_notes", []))
all_dis = " ".join(str(d) for d in result5.get("disadvantages", []))
check("1000m同类门店" in (all_risks + all_dis) or "需核验" in (all_risks + all_dis),
      f"risk info preserved: risks={all_risks[:80]} dis={all_dis[:80]}")
# 断言4: 矛盾解释存在
dn = result5.get("demand_contradiction_note", "")
check("待现场验证" in dn or "须现场核验" in dn or "须核验" in dn,
      f"contradiction note exists: {dn[:80]}")
check("客源" in dn or "客流" in dn or "过路" in dn or "外卖" in dn,
      f"explains demand source: {dn[:80]}")
# 断言5: 评分不受影响（无 dimension_scores 改动）
check("dimension_scores" not in str(result5.keys() - report5.keys()),
      "no scoring fields changed")

print("T-E-05 PASS")

# ============ T-E-06: decision_snapshot top_strength replaced on risk ============
print("=== T-E-06: all advantages risky -> fallback top_strength ===")
report6 = {
    "advantages": ["只有低租金小档口模型才有继续考察价值"],
    "decision_snapshot": {"top_strength": "只有低租金小档口模型才有继续考察价值"},
}
result6 = normalize_advantage_risk_phrasing(report6)
ts6 = result6.get("decision_snapshot", {}).get("top_strength", "")
check("只有" not in ts6, f"risky top_strength replaced: {ts6}")
print("T-E-06 PASS")

# ============ T-E-07: non-dining contradiction note ============
print("=== T-E-07: service contradiction note ===")
rd7 = {"stats_500m": {"residential": 2, "office": 1}, "stats_1000m": {"restaurants": 60, "hotels": 10, "schools": 6, "bus": 12}}
report7 = {"business_type": "美容美发", "advantages": ["a"]}
result7 = add_demand_contradiction_note(report7, rd7)
check("demand_contradiction_note" in result7, "contradiction note added")
check("住宅2" in result7["demand_contradiction_note"], "inner weakness mentioned")
print("T-E-07 PASS")

# ============ T-E-08: no outer activity -> no note ============
print("=== T-E-08: no contradiction -> no note ===")
rd8 = {"stats_500m": {"residential": 10, "office": 5}, "stats_1000m": {"restaurants": 20, "hotels": 2, "schools": 2, "bus": 3}}
report8 = {"business_type": "小吃快餐"}
result8 = add_demand_contradiction_note(report8, rd8)
check("demand_contradiction_note" not in result8, "no contradiction should be added")
print("T-E-08 PASS")

# ============ T-E-09: regex fix — 不过 splits correctly ============
print("=== T-E-09: '不过' splits correctly (not char class) ===")
report9 = {
    "advantages": ["200m内同品类供给较少，不过1000m同类门店5家需核验"]
}
result9 = normalize_advantage_risk_phrasing(report9)
adv9 = " ".join(str(a) for a in result9.get("advantages", []))
check("200m内同品类供给较少" in adv9, f"prefix should stay: {adv9}")
check("1000m同类门店" not in adv9, f"suffix should not stay: {adv9}")
print("T-E-09 PASS")

# ============ T-E-10: storage_service HTML renders contradiction ============
print("=== T-E-10: HTML template renders demand_contradiction_note ===")
svc_src = open(os.path.join(os.path.dirname(__file__), '..', 'services', 'storage_service.py'), 'r', encoding='utf-8').read()
check("demand_contradiction_note" in svc_src, "storage_service reads demand_contradiction_note")
check("contradiction_html" in svc_src, "storage_service has contradiction_html")
check("客源来源待核验" in svc_src or "客源矛盾解释" in svc_src, "HTML section title exists")
print("T-E-10 PASS")

# ============ T-E-11: admin preview renders contradiction ============
print("=== T-E-11: admin/index.html renders demand_contradiction_note ===")
admin_src = open(os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html'), 'r', encoding='utf-8').read()
check("demand_contradiction_note" in admin_src, "admin renders demand_contradiction_note")
check("客源来源待核验" in admin_src or "客源矛盾解释" in admin_src, "admin section title exists")
print("T-E-11 PASS")

# ============ T-E-12: uniapp report-detail parses contradiction ============
print("=== T-E-12: uniapp parses demand_contradiction_note ===")
uniapp_src = open(os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src', 'pages', 'report-detail', 'index.vue'), 'r', encoding='utf-8').read()
check("demand_contradiction_note" in uniapp_src, "uniapp reads demand_contradiction_note")
check("rptDemandContradiction" in uniapp_src, "uniapp has rptDemandContradiction data field")
check("客源来源待核验" in uniapp_src, "uniapp section title exists")
print("T-E-12 PASS")

# ============ T-E-13: fact guard scans demand_contradiction_note ============
print("=== T-E-13: fact guard scans new user-visible fields ===")
from report_fact_guard import build_user_visible_report_text
report13 = {
    "risk_notes": ["需核验低客流风险"],
    "demand_contradiction_note": "外圈活跃但近场弱，须现场验证",
    "details": {}, "advantages": [], "disadvantages": [], "executive_summary": {},
    "action_plan": [], "summary": "", "location_profile": {}, "location_fundamentals": {},
    "business_model_snapshot": {}, "decision_snapshot": {}, "field_checklist": [], "evidence_summary": {},
}
txt13 = build_user_visible_report_text(report13)
check("低客流风险" in txt13, f"risk_notes scanned: {txt13[:80]}")
check("外圈活跃但近场弱" in txt13, f"demand_contradiction_note scanned: {txt13[:80]}")
print("T-E-13 PASS")

# ============ Summary ============
total = p + f
print(f"\n{'='*50}")
print(f"EXPRESSION NORMALIZATION: {p} PASS, {f} FAIL (total {total})")
if f:
    sys.exit(1)
