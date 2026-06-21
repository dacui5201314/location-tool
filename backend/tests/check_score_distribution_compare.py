"""Phase S1-S3: 评分分布对比 — 使用 production 服务函数，不重复实现"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.fallback_report_service import build_fallback_report
from services.report_enrichment_service import enrich_report_business_context
from services.report_score_meta_service import add_dimension_score_meta, propose_adjusted_dimension_scores

f = 0
p = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")


def _base_rd(**overrides):
    base = {
        "stats_200m": {"residential":0,"office":0,"schools":1,"hospitals":0,"subway":0,"bus":0,"parking":1,"shopping":0,"hotels":0,"restaurants":2},
        "stats_500m": {"residential":4,"office":0,"schools":4,"hospitals":0,"subway":0,"bus":3,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        "stats_1000m": {"residential":13,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":8,"parking":26,"shopping":0,"hotels":7,"restaurants":56},
        "direct_competitors_200m":0,"direct_competitors_500m":2,"direct_competitors_1000m":12,
        "substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,
        "traffic_anchors_200m":0,"traffic_anchors_500m":3,"traffic_anchors_1000m":8,
        "direct_competitor_list":[],"substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
        "rigor_enabled":True,"subway_applicable":True,"city_has_subway":False,
    }
    base.update(overrides)
    return base


def _verdict(score):
    if score >= 60: return "可优先"
    if score >= 40: return "谨慎"
    return "低优先级"

def _pct(arr, pct_val):
    s = sorted(arr)
    idx = int(len(s) * pct_val / 100)
    return s[min(idx, len(s)-1)]


# ══════════════════ S1: 评分分布对比 ══════════════════
_SCORE_SAMPLES = [
    ("附件样例_弱近场", "小吃快餐", "", 0, _base_rd(
        stats_500m={"residential":1,"office":0,"schools":2,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4},
        stats_1000m={"residential":10,"office":0,"schools":4,"subway":0,"bus":5,"parking":2,"shopping":1,"hotels":14,"restaurants":79},
        direct_competitors_200m=0,direct_competitors_500m=2,direct_competitors_1000m=4,
    )),
    ("普通_中等", "小吃快餐", "", 50, _base_rd()),
    ("便利店_弱", "便利店", "", 60, _base_rd(
        stats_500m={"residential":2,"office":0,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":3})),
    ("酒店_中等", "酒店", "", 2000, _base_rd(
        stats_500m={"residential":5,"office":2,"schools":1,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":0,"restaurants":4})),
    ("中餐_弱", "中餐", "", 120, _base_rd(
        stats_500m={"residential":2,"office":1,"schools":2,"subway":1,"bus":3,"parking":2,"shopping":1,"hotels":1,"restaurants":15})),
    ("奶茶_弱近场", "奶茶店", "", 20, _base_rd(
        stats_500m={"residential":1,"office":1,"schools":2,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":5},
        stats_1000m={"residential":8,"office":3,"schools":4,"subway":0,"bus":5,"parking":2,"shopping":1,"hotels":10,"restaurants":60})),
]

print("=== S1: 评分分布对比 ===")
old_scores = []
cand_scores = []
cost_missing = 0
weak_near_field = 0
sample_details = []

for name, bt, bn, sz, rd in _SCORE_SAMPLES:
    fb = build_fallback_report(rd, business_type=bt, brand_name=bn, store_size=sz)
    enriched = enrich_report_business_context(fb, rd, business_type=bt, brand_name=bn, store_size=sz, is_fallback=True)
    enriched = add_dimension_score_meta(enriched, rd, store_size=sz)

    old_total = enriched.get("score", 0)
    old_scores.append(old_total)

    proposal = propose_adjusted_dimension_scores(enriched, rd, store_size=sz)
    cand_scores.append(proposal["candidate_total"])

    meta_list = enriched.get("dimension_score_meta", [])
    for m in meta_list:
        if m["key"] == "cost_estimate" and not m["is_score_applicable"]:
            cost_missing += 1
        if m["key"] == "population_density" and m["score_basis"] == "weak_near_field_demand":
            weak_near_field += 1

    is_cand_excluded = proposal["candidate_scores"].get("cost_estimate", {}).get("action") == "exclude_from_total"
    sample_details.append({
        "name": name, "old_total": old_total,
        "candidate_total": proposal["candidate_total"],
        "total_delta": proposal["total_delta"],
        "cand_cost_excluded": is_cand_excluded,
    })

print(f"  样本数: {len(old_scores)}")
print(f"  旧总分均值: {sum(old_scores)/len(old_scores):.1f}")
print(f"  旧总分中位数: {_pct(old_scores, 50)}")
print(f"  旧总分 P10/P25/P75/P90: {_pct(old_scores,10)}/{_pct(old_scores,25)}/{_pct(old_scores,75)}/{_pct(old_scores,90)}")
print(f"  候选总分均值: {sum(cand_scores)/len(cand_scores):.1f}")
cand_excluded = sum(1 for sd in sample_details if sd.get("cand_cost_excluded"))
print(f"  成本缺失样本: {cost_missing}/{len(old_scores)}")
print(f"  成本候选排除样本: {cand_excluded}/{len(old_scores)}")
print(f"  弱近场客源样本: {weak_near_field}/{len(old_scores)}")

migrations = 0
for d in sample_details:
    ov = _verdict(d["old_total"])
    cv = _verdict(d["candidate_total"])
    if ov != cv:
        migrations += 1
        print(f"  ⚠ 等级迁移: {d['name']} {ov}({d['old_total']})→{cv}({d['candidate_total']})")
print(f"  推荐等级迁移: {migrations}/{len(old_scores)}")

low_samples = [sd for sd in sample_details if 30 <= sd["old_total"] <= 45]
print(f"  30-45分样本: {len(low_samples)} (old={[sd['old_total'] for sd in low_samples]})")

# ══════════════════ 附件场景当前评分 fixture ══════════════════
print("\n=== 附件场景当前评分 fixture ===")
rd_att = _base_rd(
    stats_500m={"residential":1,"office":0,"schools":2,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4},
    stats_1000m={"residential":10,"office":0,"schools":4,"subway":0,"bus":5,"parking":2,"shopping":1,"hotels":14,"restaurants":79},
    direct_competitors_200m=0,direct_competitors_500m=2,direct_competitors_1000m=4,
)
fb_att = build_fallback_report(rd_att, business_type="小吃快餐", brand_name="", store_size=0)
enr_att = enrich_report_business_context(fb_att, rd_att, business_type="小吃快餐", brand_name="", store_size=0, is_fallback=True)
enr_att = add_dimension_score_meta(enr_att, rd_att, store_size=0)

att_dims = {d["key"]: d["score"] for d in enr_att.get("dimension_scores", [])}
print(f"  dimensions: {att_dims}")
att_score = enr_att.get("score", 0)
print(f"  overall: {att_score}")

# 附件维度分数断言
for k, expected in [("population_density", 31), ("cost_estimate", 50)]:
    got = att_dims.get(k, -1)
    check(got == expected, f"attachment {k} should be {expected}: got {got}")
# overall 由确定性公式计算（31+31+30+25+60+40+73+50=340/8=42.5→42）
check(att_score == 42, f"attachment overall should be 42: got {att_score}")

# 附件 meta
att_meta = {m["key"]: m for m in enr_att.get("dimension_score_meta", [])}
cost_m = att_meta.get("cost_estimate", {})
check(cost_m.get("score_confidence") == "low", "attachment cost low conf")
check(cost_m.get("is_score_applicable") == False, "attachment cost not applicable")

pop_m = att_meta.get("population_density", {})
check(pop_m.get("score_basis") == "weak_near_field_demand", "attachment pop weak near field")

# 候选不覆盖原分
proposal_att = propose_adjusted_dimension_scores(enr_att, rd_att, store_size=0)
check(proposal_att["original_total"] == att_score, "candidate does not change original")
check("cost_estimate" in proposal_att["candidate_scores"], "cost in candidate")
check(proposal_att["candidate_total"] != att_score, "candidate total differs")

# ══════════════════ S2 meta 测试 ══════════════════
print("\n=== S2: meta 字段测试 ===")

# T-M2-01: score numeric
for d in enr_att.get("dimension_scores", []):
    check(isinstance(d.get("score"), (int, float)), f"score numeric: {d['key']}")

# T-M2-02: store_size>0 时 missing 不含 store_area
fb_sz = build_fallback_report(rd_att, business_type="小吃快餐", brand_name="", store_size=60)
enr_sz = enrich_report_business_context(fb_sz, rd_att, business_type="小吃快餐", brand_name="", store_size=60, is_fallback=True)
enr_sz = add_dimension_score_meta(enr_sz, rd_att, store_size=60)
sz_meta = {m["key"]: m for m in enr_sz.get("dimension_score_meta", [])}
sz_cost = sz_meta.get("cost_estimate", {})
check("store_area" not in sz_cost.get("missing_required_inputs", []),
      f"store_size>0 should not miss store_area: {sz_cost.get('missing_required_inputs')}")
check(sz_cost.get("score_confidence") == "low", "cost still low conf (rent/labor/revenue missing)")
# T-M2-02b: store_size=60 + 缺租金/人工/营收 → is_score_applicable=False
check(sz_cost.get("is_score_applicable") == False, "store_size=60 but no rent/labor/revenue → not applicable")

# T-M2-02c: candidate_scores 包含 cost_estimate, action=exclude_from_total
prop_sz = propose_adjusted_dimension_scores(enr_sz, rd_att, store_size=60)
cs_cost = prop_sz.get("candidate_scores", {}).get("cost_estimate", {})
check(cs_cost.get("action") == "exclude_from_total",
      f"store_size=60 with missing inputs should exclude: {cs_cost}")

# T-M2-02d: propose 不修改原 report score
orig_score = enr_sz.get("score")
orig_dim0 = enr_sz["dimension_scores"][0]["score"]
_ = propose_adjusted_dimension_scores(enr_sz, rd_att, store_size=60)
check(enr_sz.get("score") == orig_score, "propose does not change report.score")
check(enr_sz["dimension_scores"][0]["score"] == orig_dim0, "propose does not change dimension_scores[].score")

# T-M2-03: overall_score unchanged
check(enr_att.get("score") == att_score, "meta does not change total")

# T-M2-04: enrichment path has meta
fb_enr = build_fallback_report(rd_att, business_type="小吃快餐", brand_name="", store_size=0)
enr_full = enrich_report_business_context(fb_enr, rd_att, business_type="小吃快餐", brand_name="", store_size=0, is_fallback=True)
check("dimension_score_meta" in enr_full, "enrichment adds dimension_score_meta")
check(isinstance(enr_full.get("dimension_score_meta", []), list), "meta is list")
check(len(enr_full["dimension_score_meta"]) >= 8, f"meta has 8+ entries: {len(enr_full['dimension_score_meta'])}")

# T-M2-05: normal-field pop density is medium confidence
rd_normal = _base_rd()
fb_norm = build_fallback_report(rd_normal, business_type="便利店", brand_name="", store_size=60)
enr_norm = enrich_report_business_context(fb_norm, rd_normal, business_type="便利店", brand_name="", store_size=60, is_fallback=True)
norm_meta = {m["key"]: m for m in enr_norm.get("dimension_score_meta", [])}
norm_pop = norm_meta.get("population_density", {})
check(norm_pop.get("score_confidence") == "medium", f"normal pop should be medium: {norm_pop}")

print(f"\n{'='*50}")
print(f"SCORE DISTRIBUTION: {p} PASS, {f} FAIL (total {p+f})")
if f:
    sys.exit(1)
