"""Phase 0+1 knowledge schema 校验测试"""
import sys, os, yaml, copy
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")


def _load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _validate_required(data, required, label):
    missing = [k for k in required if k not in data]
    assert not missing, f"{label} missing required fields: {missing}"


# ═══════════════ T1: location_profiles.yaml 满足 schema ═══════════════
def test_location_profiles_yaml():
    lp = _load_yaml(os.path.join(KNOWLEDGE_DIR, "location_profiles.yaml"))
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "location_profile_schema.yaml"))
    required = schema["required_top_fields"]
    _validate_required(lp, required, "location_profiles.yaml")
    print("T1 location_profiles.yaml satisfies schema: PASS")


# ═══════════════ T2: business_models/*.yaml 满足 schema ═══════════════
def test_business_model_yamls():
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "business_model_schema.yaml"))
    top_required = schema["required_top_fields"]
    comp_required = schema["competition"]["required"]
    cov_required = schema["coverage"]["required"]
    rev_required = schema["revenue_model"]["required"]
    src_required = schema["sources_item"]["required"]
    comp_types = schema["competition"]["type_enum"]

    models_dir = os.path.join(KNOWLEDGE_DIR, "business_models")
    files = [f for f in os.listdir(models_dir) if f.endswith(".yaml")]
    assert files, "No business model YAML files found"

    for fname in sorted(files):
        path = os.path.join(models_dir, fname)
        data = _load_yaml(path)

        # Top-level required
        _validate_required(data, top_required, fname)

        # competition
        comp = data["competition"]
        _validate_required(comp, comp_required, f"{fname}/competition")
        assert comp["type"] in comp_types, \
            f"{fname}/competition.type '{comp['type']}' not in {comp_types}"

        # coverage
        cov = data["coverage"]
        _validate_required(cov, cov_required, f"{fname}/coverage")

        # revenue_model
        rev = data["revenue_model"]
        _validate_required(rev, rev_required, f"{fname}/revenue_model")

        # sources items
        for i, src in enumerate(data.get("sources", [])):
            _validate_required(src, src_required, f"{fname}/sources[{i}]")

    print(f"T2 all {len(files)} business models satisfy schema: PASS")


# ═══════════════ T3: 缺字段时校验失败 ═══════════════
def test_missing_fields_fails():
    data = _load_yaml(os.path.join(KNOWLEDGE_DIR, "business_models", "01_snack_fast_food.yaml"))
    # 复制并删除必填字段
    broken = copy.deepcopy(data)
    del broken["competition"]
    try:
        _validate_required(broken, ["competition"], "broken")
        assert False, "should have raised on missing competition"
    except AssertionError:
        pass  # expected

    broken2 = copy.deepcopy(data)
    broken2["competition"] = dict(broken2["competition"])
    del broken2["competition"]["type"]
    try:
        _validate_required(broken2["competition"], ["type"], "broken/competition")
        assert False, "should have raised on missing competition.type"
    except AssertionError:
        pass

    print("T3 missing fields correctly fails: PASS")


# ═══════════════ T4: enrichment 保守版说明不重复 ═══════════════
def test_conservative_note_no_duplicate():
    from services.fallback_report_service import build_fallback_report
    from services.report_enrichment_service import enrich_report_business_context

    rd = {
        "stats_200m":{"residential":0,"office":0,"schools":1},
        "stats_500m":{"residential":4,"office":0,"schools":4,"subway":0,"bus":3,"parking":6,"shopping":0,"hotels":2,"restaurants":11},
        "stats_1000m":{"residential":13,"office":0,"schools":9,"restaurants":56},
        "direct_competitors_200m":0,"direct_competitors_500m":2,"direct_competitors_1000m":12,
        "substitute_competitors_200m":0,"substitute_competitors_500m":0,"substitute_competitors_1000m":0,
        "traffic_anchors_200m":0,"traffic_anchors_500m":3,"traffic_anchors_1000m":8,
        "direct_competitor_list":[],"substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},
        "rigor_enabled":True,"subway_applicable":True,"city_has_subway":False,
    }

    fb = build_fallback_report(rd, business_type="小吃快餐", brand_name="砂锅小吃", store_size=50)
    # 第一次 enrichment
    enriched = enrich_report_business_context(
        fb, rd, business_type="小吃快餐", brand_name="砂锅小吃",
        store_size=50, is_fallback=True)

    db = enriched.get("data_boundary", "")
    count = db.count("虽为保守版")
    assert count == 1, f"data_boundary 中'虽为保守版'应出现1次，实际{count}次: ...{db[-200:]}"

    # 第二次 enrichment（幂等）
    enriched2 = enrich_report_business_context(
        enriched, rd, business_type="小吃快餐", brand_name="砂锅小吃",
        store_size=50, is_fallback=True)
    count2 = enriched2.get("data_boundary", "").count("虽为保守版")
    assert count2 == 1, f"幂等调用后应仍为1次，实际{count2}次"

    print("T4 conservative note no duplicate: PASS")


# ═══════════════ T5: source_card_schema.yaml 校验 ═══════════════
def test_source_card_schema():
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "source_card_schema.yaml"))
    required = schema["required_fields"]
    _validate_required(schema, ["schema_version","required_fields","source_type_enum","confidence_enum"], "source_card_schema.yaml")
    assert "source_id" in required
    assert "source_type" in required
    print("T5 source_card_schema.yaml validates: PASS")


# ═══════════════ T6: source_manifest 满足 source_card_schema ═══════════════
def test_source_manifest():
    manifest = _load_yaml(os.path.join(KNOWLEDGE_DIR, "sources", "source_manifest.yaml"))
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "source_card_schema.yaml"))
    required = schema["required_fields"]
    type_enum = schema["source_type_enum"]
    conf_enum = schema["confidence_enum"]
    for src in manifest.get("sources", []):
        _validate_required(src, required, f"source/{src.get('source_id','?')}")
        assert src["source_type"] in type_enum, f"{src['source_id']}: type '{src['source_type']}'"
        assert src["confidence"] in conf_enum, f"{src['source_id']}: confidence '{src['confidence']}'"
    print(f"T6 source_manifest: {len(manifest['sources'])} sources all valid PASS")


# ═══════════════ T7: load_business_model 加载全部 5 个模型 ═══════════════
def test_load_all_models():
    from services.business_model_service import load_business_model, get_model_version
    expected = ["snack_fast_food", "education_childcare", "beverage_dessert",
                "retail_convenience", "service_beauty"]
    for mid in expected:
        model = load_business_model(mid)
        assert model, f"load_business_model({mid}) returned empty"
        assert model.get("model_id") == mid, f"{mid}: model_id mismatch {model.get('model_id')}"
        version = get_model_version(mid)
        assert version.startswith(mid + "@"), f"version format: {version}"
    # 已缓存
    assert load_business_model("snack_fast_food") is not None
    print(f"T7 load_business_model: {len(expected)} models all loaded PASS")


# ═══════════════ T8: 新增 03/04/10 YAML 通过 schema ═══════════════
def test_new_yamls_pass_schema():
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "business_model_schema.yaml"))
    for fname in ["03_beverage_dessert.yaml", "04_convenience_supermarket.yaml",
                  "10_beauty_fitness_pet.yaml"]:
        data = _load_yaml(os.path.join(KNOWLEDGE_DIR, "business_models", fname))
        _validate_required(data, schema["required_top_fields"], fname)
        comp = data["competition"]
        _validate_required(comp, schema["competition"]["required"], f"{fname}/competition")
        assert comp["type"] in schema["competition"]["type_enum"], \
            f"{fname} competition.type: {comp['type']}"
        _validate_required(data["coverage"], schema["coverage"]["required"], f"{fname}/coverage")
        _validate_required(data["revenue_model"], schema["revenue_model"]["required"], f"{fname}/revenue_model")
    print("T8 new 03/04/10 YAMLs pass schema: PASS")


# ═══════════════ T9: 缺字段 copy 必须失败（非假失败） ═══════════════
def test_missing_fields_on_new_yamls():
    data = _load_yaml(os.path.join(KNOWLEDGE_DIR, "business_models", "03_beverage_dessert.yaml"))
    # 删 revenue_model → 必须失败
    broken = copy.deepcopy(data)
    del broken["revenue_model"]
    try:
        _validate_required(broken, ["revenue_model"], "broken-03")
        assert False, "should have raised"
    except AssertionError:
        pass
    # 删 competition.type → 必须失败
    broken2 = copy.deepcopy(data)
    broken2["competition"] = dict(broken2["competition"])
    del broken2["competition"]["type"]
    try:
        _validate_required(broken2["competition"], ["type"], "broken-03/competition")
        assert False, "should have raised"
    except AssertionError:
        pass
    print("T9 missing fields on new YAMLs correctly fails: PASS")


if __name__ == "__main__":
    test_location_profiles_yaml()
    test_business_model_yamls()
    test_missing_fields_fails()
    test_conservative_note_no_duplicate()
    test_source_card_schema()
    test_source_manifest()
    test_load_all_models()
    test_new_yamls_pass_schema()
    test_missing_fields_on_new_yamls()
    print()
    print("ALL KNOWLEDGE SCHEMA TESTS PASSED")
