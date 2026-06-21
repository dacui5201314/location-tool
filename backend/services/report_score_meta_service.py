"""
评分 meta 字段追加 + 候选评分调整 — 确定性函数。
只追加 meta，不改变 dimension_scores[].score、不改变总分。
"""
def _int(v, default=0):
    try: return int(v)
    except: return default


# ═══════════════════════════════════════════════════════════════
# S2: 评分 meta 字段（纯追加）
# ═══════════════════════════════════════════════════════════════

def add_dimension_score_meta(report: dict, real_data: dict, store_size: int = 0) -> dict:
    """为 dimension_scores 追加 meta 信息。不改变 score 值，不改变总分。"""
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))

    dims = report.get("dimension_scores", []) or []
    meta_list = []

    for d in dims:
        key = d.get("key", "")
        meta = {"key": key, "score_basis": "deterministic",
                "score_confidence": "medium", "missing_required_inputs": [],
                "is_score_applicable": True}

        if key == "cost_estimate":
            missing = []
            if store_size <= 0:
                missing.append("store_area")
            # 租金、人工、营收在当前链路几乎一定缺失，保守标记
            missing.append("rent_per_sqm")
            missing.append("labor_cost")
            missing.append("revenue_estimate")
            meta["missing_required_inputs"] = missing
            meta["score_confidence"] = "low"
            meta["score_basis"] = "placeholder_no_inputs"
            meta["is_score_applicable"] = False
            meta["note"] = "不具备成本压力精算依据，50分为占位值"

        elif key == "population_density":
            if res_500 < 3 and office_500 == 0:
                meta["score_confidence"] = "low"
                meta["score_basis"] = "weak_near_field_demand"
                meta["note"] = f"近场住宅{res_500}、办公{office_500}，人口密集度依据偏弱"

        meta_list.append(meta)

    report["dimension_score_meta"] = meta_list
    return report


# ═══════════════════════════════════════════════════════════════
# S3: 候选评分调整（不覆盖原分，仅返回候选建议）
# ═══════════════════════════════════════════════════════════════

def propose_adjusted_dimension_scores(report: dict, real_data: dict, store_size: int = 0) -> dict:
    """候选评分调整。返回 candidate_scores 和 total_delta，不覆盖原分。
    成本维度是否排除以 dimension_score_meta.cost_estimate.is_score_applicable 为准。
    """
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))

    # 先确保 meta 存在
    meta_list = report.get("dimension_score_meta", []) or []
    meta_by_key = {m["key"]: m for m in meta_list}

    dims = report.get("dimension_scores", []) or []
    dim_count = len(dims) if dims else 8
    old_total = sum(d.get("score", 0) for d in dims)
    candidate_scores = {}
    total_delta = 0.0
    exclude_count = 0

    for d in dims:
        key = d.get("key", "")
        old = d.get("score", 0)
        meta = meta_by_key.get(key, {})

        if key == "cost_estimate":
            # 以 meta 为准：缺 rent/labor/revenue 则排除
            if not meta.get("is_score_applicable", True):
                candidate_scores[key] = {"old": old, "candidate": None,
                                          "action": "exclude_from_total",
                                          "reason": "missing_cost_inputs"}
                total_delta -= old
                exclude_count += 1

        elif key == "population_density":
            if meta.get("score_basis") == "weak_near_field_demand":
                new = min(old, 35)
                candidate_scores[key] = {"old": old, "candidate": new,
                                          "action": "cap",
                                          "reason": f"weak_near_field res={res_500} office={office_500}"}
                total_delta += (new - old)

    active_count = dim_count - exclude_count
    candidate_total = round((old_total + total_delta) / active_count) if active_count > 0 else round((old_total + total_delta) / dim_count)

    return {
        "original_total": round(old_total / dim_count),
        "candidate_total": candidate_total,
        "total_delta": round(total_delta),
        "dim_count": dim_count,
        "candidate_scores": candidate_scores,
    }
