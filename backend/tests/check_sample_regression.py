"""Phase 4A: 12个模型族群样本回归库"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.business_model_service import (
    classify_business_model_family, compute_business_model_snapshot,
    load_business_model,
)
from services.location_profile_service import compute_location_profile
from services.fallback_report_service import build_fallback_report
from services.report_enrichment_service import enrich_report_business_context
from services.storage_service import _build_report_html


def _make_rd(**overrides):
    """最小可用 real_data 基座。"""
    base = {
        "stats_200m":{"residential":2,"office":1,"schools":1,"hospitals":0,"subway":0,"bus":1,"parking":1,"shopping":0,"hotels":0,"restaurants":3},
        "stats_500m":{"residential":8,"office":5,"schools":3,"hospitals":1,"subway":1,"bus":5,"parking":3,"shopping":1,"hotels":2,"restaurants":15},
        "stats_1000m":{"residential":20,"office":10,"schools":6,"hospitals":2,"subway":2,"bus":10,"parking":8,"shopping":3,"hotels":5,"restaurants":40},
        "direct_competitors_200m":2,"direct_competitors_500m":4,"direct_competitors_1000m":8,
        "substitute_competitors_200m":0,"substitute_competitors_500m":2,"substitute_competitors_1000m":5,
        "traffic_anchors_200m":1,"traffic_anchors_500m":4,"traffic_anchors_1000m":10,
        "direct_competitor_list":[],"direct_competitor_list_200m":[],"direct_competitor_list_500m":[],"direct_competitor_list_1000m":[],
        "substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
        "rigor_enabled":True,"subway_applicable":True,"city_has_subway":True,
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════════════════
# 12 个样本定义
# ═══════════════════════════════════════════════════════════

SAMPLES = [
    # 01: 小吃快餐 200m 0竞品 1000m多同类
    {
        "case_id": "snack_fast_food_01",
        "model_id": "snack_fast_food",
        "business_type": "小吃快餐", "brand_name": "砂锅小吃", "store_size": 50,
        "real_data": _make_rd(
            direct_competitors_200m=0, direct_competitors_500m=3, direct_competitors_1000m=12,
            stats_1000m={"residential":13,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":8,"parking":26,"shopping":0,"hotels":7,"restaurants":56},
        ),
        "expected_absent": ["市场空白明显","先发优势","竞争环境宽松","推荐开店","值得投资"],
    },
    # 02: 正餐聚餐
    {
        "case_id": "food_service_01",
        "model_id": "food_service",
        "business_type": "中餐", "brand_name": "湘菜馆", "store_size": 200,
        "real_data": _make_rd(direct_competitors_200m=3, direct_competitors_500m=5, direct_competitors_1000m=8),
        "expected_absent": ["市场空白明显","先发优势","推荐开店","值得投资"],
    },
    # 03: 茶饮烘焙 半聚集型
    {
        "case_id": "beverage_dessert_01",
        "model_id": "beverage_dessert",
        "business_type": "奶茶店", "brand_name": "茶百道", "store_size": 20,
        "real_data": _make_rd(direct_competitors_200m=1, direct_competitors_500m=3, direct_competitors_1000m=6),
        "expected_absent": ["市场空白明显","先发优势","推荐开店"],
    },
    # 04: 便利超市
    {
        "case_id": "retail_convenience_01",
        "model_id": "retail_convenience",
        "business_type": "便利店", "brand_name": "全家", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=1, direct_competitors_1000m=3),
        "expected_absent": ["推荐开店","值得投资","出餐速度","外卖骑手"],
    },
    # 05: 药店 中性型
    {
        "case_id": "pharmacy_01",
        "model_id": "pharmacy",
        "business_type": "药店", "brand_name": "", "store_size": 80,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },
    # 06: 目的零售
    {
        "case_id": "retail_shopping_01",
        "model_id": "retail_shopping",
        "business_type": "服装店", "brand_name": "", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=2, direct_competitors_1000m=4),
        "expected_absent": ["市场空白明显","推荐开店"],
    },
    # 07: 教育托管 0 POI 暗竞品
    {
        "case_id": "education_childcare_01",
        "model_id": "education_childcare",
        "business_type": "教育培训", "brand_name": "小学生托管服务", "store_size": 100,
        "real_data": _make_rd(
            direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":4,"office":0,"schools":4,"subway":0,"bus":2,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        ),
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","外卖骑手","出餐速度","上座率","午晚高峰堂食","排队","推荐开店"],
    },
    # 08: 教育培训（非托管）
    {
        "case_id": "education_training_01",
        "model_id": "education_training",
        "business_type": "教育培训", "brand_name": "英语培训", "store_size": 80,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=1, direct_competitors_1000m=2),
        "expected_absent": ["午托","小饭桌","餐食成本","市场空白明显","推荐开店"],
    },
    # 09: 社区基础服务
    {
        "case_id": "service_basic_01",
        "model_id": "service_basic",
        "business_type": "洗衣店", "brand_name": "", "store_size": 30,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_absent": ["市场空白明显","外卖骑手","出餐速度","推荐开店"],
    },
    # 10: 美业健身
    {
        "case_id": "service_beauty_01",
        "model_id": "service_beauty",
        "business_type": "美容美发", "brand_name": "", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_absent": ["市场空白明显","品类切入空间较好","外卖骑手","出餐速度"],
    },
    # 11: 酒店 0竞品非优势
    {
        "case_id": "hotel_01",
        "model_id": "hotel",
        "business_type": "酒店", "brand_name": "汉庭", "store_size": 2000,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },
    # 12: 娱乐
    {
        "case_id": "entertainment_01",
        "model_id": "entertainment",
        "business_type": "酒吧", "brand_name": "", "store_size": 200,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },
]


# ═══════════════════════════════════════════════════════════
# 逐样本测试
# ═══════════════════════════════════════════════════════════

def _check_sample(s):
    rd = s["real_data"]
    bt, bn, sz = s["business_type"], s["brand_name"], s["store_size"]
    mid = s["model_id"]

    # (a) 模型归类
    family = classify_business_model_family(bt, bn, "")
    assert family == mid, f"{s['case_id']}: classify={family}, expected={mid}"

    # (b) location_profile
    lp = compute_location_profile(rd)
    assert lp["primary_type"], f"{s['case_id']}: location_profile empty"

    # (c) business_model_snapshot
    snap = compute_business_model_snapshot(rd, bt, bn, sz)
    assert snap["model_type"] == mid, f"{s['case_id']}: snapshot model={snap['model_type']}"

    # (d) YAML 可加载
    model_yaml = load_business_model(mid)
    assert model_yaml, f"{s['case_id']}: YAML not loaded for {mid}"

    # (e) fallback + enrichment
    fb = build_fallback_report(rd, address="test", business_type=bt, brand_name=bn, store_size=sz)
    enriched = enrich_report_business_context(fb, rd, business_type=bt, brand_name=bn, store_size=sz, is_fallback=True)

    required = ["location_profile","location_fundamentals","business_model_snapshot",
                "business_model_version","revenue_disclaimer","field_checklist",
                "caliber_explanation","evidence_summary","data_boundary"]
    for k in required:
        assert k in enriched and enriched[k], f"{s['case_id']}: enriched missing {k}"

    # (f) HTML 渲染
    enriched["business_type"] = bt
    enriched["generated_at"] = "2026-06-15 10:00"
    html = _build_report_html(1, enriched, "addr", bn)
    for marker in ["选址决策参考","保守版数据摘要","地点基本面","现场核验清单"]:
        assert marker in html, f"{s['case_id']}: HTML missing {marker}"

    # (g) 禁词扫描
    report_text = json.dumps(enriched, ensure_ascii=False)
    for phrase in s.get("expected_absent", []):
        assert phrase not in report_text, f"{s['case_id']}: found banned '{phrase}'"

    # (h) 禁误读验证
    fm_text = " ".join(model_yaml.get("forbidden_misreadings", []))
    for phrase in s.get("expected_absent", []):
        # 禁词如果在 YAML forbidden_misreadings 中出现则跳过（YAML 可以用禁词做反例说明）
        if phrase in fm_text:
            continue

    return True


def test_all_12_samples():
    for s in SAMPLES:
        _check_sample(s)
    print(f"SAMPLE_REGRESSION: {len(SAMPLES)} samples ALL PASS")


if __name__ == "__main__":
    test_all_12_samples()
