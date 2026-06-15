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

    # 删除必填字段 → 必须触发 AssertionError
    broken = copy.deepcopy(data)
    del broken["competition"]
    failed = False
    try:
        _validate_required(broken, ["competition"], "broken")
    except AssertionError:
        failed = True
    assert failed, "missing competition should have raised"

    broken2 = copy.deepcopy(data)
    broken2["competition"] = dict(broken2["competition"])
    del broken2["competition"]["type"]
    failed2 = False
    try:
        _validate_required(broken2["competition"], ["type"], "broken/competition")
    except AssertionError:
        failed2 = True
    assert failed2, "missing competition.type should have raised"

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
    _validate_required(schema, ["schema_version","required_fields","source_type_enum",
                                "confidence_enum","internal_source_types",
                                "external_source_types","external_compliance_fields"],
                       "source_card_schema.yaml")
    assert "source_id" in required
    assert "source_type" in required
    # 外部来源类型必须是 source_type_enum 子集
    ext_types = set(schema["external_source_types"])
    all_types = set(schema["source_type_enum"])
    assert ext_types.issubset(all_types), f"external types not subset: {ext_types - all_types}"
    print("T5 source_card_schema.yaml validates: PASS")


# ═══════════════ T6: source_manifest 满足 source_card_schema ═══════════════
def test_source_manifest():
    manifest = _load_yaml(os.path.join(KNOWLEDGE_DIR, "sources", "source_manifest.yaml"))
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "source_card_schema.yaml"))
    required = schema["required_fields"]
    type_enum = schema["source_type_enum"]
    conf_enum = schema["confidence_enum"]
    for src in manifest.get("sources", []):
        inline_only = src.get("inline_manifest_only", False)
        # inline_manifest_only 条目的完整数据在独立 card 文件中，manifest 只存元数据
        req = required if not inline_only else ["source_id","source_type","title","confidence","inline_manifest_only"]
        _validate_required(src, req, f"source/{src.get('source_id','?')}")
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
    failed = False
    try:
        _validate_required(broken, ["revenue_model"], "broken-03")
    except AssertionError:
        failed = True
    assert failed, "missing revenue_model should have raised"

    # 删 competition.type → 必须失败
    broken2 = copy.deepcopy(data)
    broken2["competition"] = dict(broken2["competition"])
    del broken2["competition"]["type"]
    failed2 = False
    try:
        _validate_required(broken2["competition"], ["type"], "broken-03/competition")
    except AssertionError:
        failed2 = True
    assert failed2, "missing competition.type should have raised"

    print("T9 missing fields on new YAMLs correctly fails: PASS")


# ═══════════════ T10: 蒸馏来源卡满足 schema + 合规校验 ═══════════════
def test_distilled_source_cards():
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "source_card_schema.yaml"))
    required = schema["required_fields"]
    external_types = set(schema["external_source_types"])
    compliance_fields = set(schema["external_compliance_fields"])
    sources_dir = os.path.join(KNOWLEDGE_DIR, "sources")
    cards = [f for f in os.listdir(sources_dir)
             if f.endswith(".yaml") and f != "source_manifest.yaml"]
    assert cards, "no distilled source cards found"

    for fname in sorted(cards):
        card = _load_yaml(os.path.join(sources_dir, fname))
        st = card.get("source_type", "")
        _validate_required(card, required, f"sources/{fname}")
        assert st in schema["source_type_enum"], f"sources/{fname}: type '{st}'"

        # 外部来源：必须 derived_rule_only=true 或 copyright_note 非空
        if st in external_types:
            has_compliance = any(card.get(f) for f in compliance_fields)
            assert has_compliance, (
                f"sources/{fname}: external type '{st}' missing {compliance_fields}"
            )
            # derived_rule_only 如存在必须为 true
            if "derived_rule_only" in card:
                assert card["derived_rule_only"] is True, (
                    f"sources/{fname}: derived_rule_only must be true, got {card['derived_rule_only']}"
                )

        # 所有规则：dict 必须有 'rule' 键；str 直接作为 rule 内容
        rules = card.get("extracted_rules", {})
        for section in ["red_flags", "data_blind_spots", "demand_sources",
                        "fit_signals", "field_checklist_additions", "forbidden_misreadings"]:
            for item in rules.get(section, []):
                if isinstance(item, dict):
                    assert "rule" in item, f"sources/{fname}/{section}: dict missing 'rule'"
                    # 不得出现长段原文（rule + caveat 合计不超过 300 字）
                    full_text = item.get("rule", "") + item.get("caveat", "")
                    assert len(full_text) < 300, (
                        f"sources/{fname}/{section}: rule text too long ({len(full_text)} chars), "
                        f"可能是原文复制"
                    )
                elif isinstance(item, str):
                    assert len(item) < 300, (
                        f"sources/{fname}/{section}: str item too long ({len(item)} chars)"
                    )

    print(f"T10 {len(cards)} distilled source cards satisfy schema + compliance: PASS")


# ═══════════════ T11: 蒸馏规则可追溯回已有 YAML ═══════════════
def test_distilled_rules_traceable():
    from services.business_model_service import load_business_model

    # internal_sample_001 → snack_fast_food YAML 应存在对应规则
    snack = load_business_model("snack_fast_food")
    assert snack, "snack_fast_food not loaded"
    # demand_sources 中的学校午市规则
    ds_names = [d["name"] for d in snack.get("demand_sources", [])]
    assert "学校午市" in ds_names, f"snack_fast_food demand_sources: {ds_names}"
    # red_flags 中的三弱规则
    rf_text = " ".join(snack.get("red_flags", []))
    assert "两个高峰" in rf_text or "寒暑假" in rf_text or "1000m" in rf_text, \
        f"snack_fast_food red_flags should cover known risks: {rf_text[:100]}"
    # forbidden_misreadings 中的 200m 无竞品规则
    fm_text = " ".join(snack.get("forbidden_misreadings", []))
    assert "200m" in fm_text or "竞品" in fm_text, \
        f"snack_fast_food forbidden_misreadings: {fm_text[:100]}"

    # product_review_001 → 5 个模型都应加载
    for mid in ["education_childcare", "retail_convenience", "service_beauty"]:
        model = load_business_model(mid)
        assert model, f"{mid} not loaded"
        comp_type = model.get("competition", {}).get("type", "")
        assert comp_type, f"{mid} missing competition.type"

    print("T11 distilled rules traceable to YAMLs: PASS")


# ═══════════════ T12: 外部来源（独立卡 + manifest inline）合规 ═══════════════
def test_external_source_compliance():
    schema = _load_yaml(os.path.join(KNOWLEDGE_DIR, "source_card_schema.yaml"))
    external_types = set(schema["external_source_types"])
    compliance_fields = set(schema["external_compliance_fields"])
    sources_dir = os.path.join(KNOWLEDGE_DIR, "sources")

    # (a) 独立 source card 文件
    cards = [f for f in os.listdir(sources_dir)
             if f.endswith(".yaml") and f != "source_manifest.yaml"]
    for fname in sorted(cards):
        card = _load_yaml(os.path.join(sources_dir, fname))
        st = card.get("source_type", "")
        if st not in external_types:
            continue
        has_compliance = any(card.get(f) for f in compliance_fields)
        assert has_compliance, (
            f"sources/{fname}: external type '{st}' must have one of {compliance_fields}"
        )

    # (b) source_manifest 中的 inline_manifest_only 来源
    manifest = _load_yaml(os.path.join(sources_dir, "source_manifest.yaml"))
    for src in manifest.get("sources", []):
        st = src.get("source_type", "")
        if st not in external_types:
            continue
        has_compliance = any(src.get(f) for f in compliance_fields)
        assert has_compliance, (
            f"manifest source_id={src.get('source_id','?')}: "
            f"external type '{st}' must have one of {compliance_fields}"
        )

    # (c) 构造型负向测试：manifest 中的外部来源缺合规必失败
    broken_manifest = {
        "source_id": "test_book_001",
        "source_type": "book",
        "title": "测试书籍来源",
        "confidence": "B",
        "applicable_models": ["snack_fast_food"],
        "extracted_rules": {"demand_sources": [], "red_flags": []},
    }
    failed = False
    try:
        st = broken_manifest["source_type"]
        if st in external_types:
            if not any(broken_manifest.get(f) for f in compliance_fields):
                raise AssertionError("missing compliance for external type")
    except AssertionError:
        failed = True
    assert failed, "book type without copyright_note/derived_rule_only should fail"

    print("T12 external source compliance (cards + manifest inline + negative): PASS")


# ═══════════════ T13: source_id 一致性 ─═
def test_source_id_uniqueness():
    manifest = _load_yaml(os.path.join(KNOWLEDGE_DIR, "sources", "source_manifest.yaml"))
    sources_dir = os.path.join(KNOWLEDGE_DIR, "sources")
    cards = [f for f in os.listdir(sources_dir)
             if f.endswith(".yaml") and f != "source_manifest.yaml"]

    manifest_ids = set()
    for src in manifest.get("sources", []):
        sid = src.get("source_id", "")
        assert sid, "manifest entry missing source_id"
        assert sid not in manifest_ids, f"duplicate source_id in manifest: {sid}"
        manifest_ids.add(sid)

    card_ids = set()
    for fname in cards:
        card = _load_yaml(os.path.join(sources_dir, fname))
        sid = card.get("source_id", "")
        assert sid, f"sources/{fname} missing source_id"
        assert sid not in card_ids, f"duplicate source_id among cards: {sid}"
        card_ids.add(sid)

    # manifest 中引用的 source_id 必须在独立卡中存在，或标记 inline_manifest_only
    for src in manifest.get("sources", []):
        sid = src["source_id"]
        in_cards = sid in card_ids
        inline_only = src.get("inline_manifest_only", False)
        assert in_cards or inline_only, (
            f"source_id '{sid}' in manifest not found in any card file; "
            f"add inline_manifest_only: true or create card file"
        )

    print(f"T13 source_id uniqueness: manifest={len(manifest_ids)}, cards={len(card_ids)} PASS")


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
    test_distilled_source_cards()
    test_distilled_rules_traceable()
    test_external_source_compliance()
    test_source_id_uniqueness()
    print()
    print("ALL KNOWLEDGE SCHEMA TESTS PASSED")
