"""Runtime configuration helpers backed by SystemConfig."""
import json
import os
import re
from typing import Any

from database import SessionLocal
from models.db_models import SystemConfig


CORE_CONFIG_DEFAULTS = {
    "amap_key": os.getenv("AMAP_WEB_KEY", os.getenv("AMAP_KEY", "")),
    "ai_provider": os.getenv("LLM_PROVIDER", "deepseek"),
    "ai_key": os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
    "system_prompt": "",
    "wx_mch_id": "",
    "wx_app_id": "",
    "wx_api_key": "",
    "wx_cert_sn": "",
    "wx_notify_url": "",
    "wx_private_key_pem": "",
    "wx_platform_cert_pem": "",
    # 虚拟支付
    "wx_virtual_pay_enabled": "0",
    "wx_virtual_offer_id": "",
    "wx_virtual_app_key": "",
    "wx_virtual_env": "1",
    "wx_virtual_currency_type": "CNY",
}

PDF_CONFIG_DEFAULTS = {
    "logo_url": "",
    "footer_text": "AI 选址分析 · 商业选址初筛参考",
}

DEFAULT_SKUS = [
    {"id": 1, "type": "membership", "label": "月度会员", "price": "88", "tier": "monthly", "duration_days": 30, "credits": 0, "badge": "", "desc": "30天无限次分析", "visible": True},
    {"id": 2, "type": "membership", "label": "季度会员", "price": "218", "tier": "quarterly", "duration_days": 90, "credits": 0, "badge": "推荐", "desc": "90天无限次分析", "visible": True},
    {"id": 3, "type": "membership", "label": "年度会员", "price": "888", "tier": "yearly", "duration_days": 365, "credits": 0, "badge": "最值", "desc": "365天无限次分析", "visible": True},
    {"id": 11, "type": "points", "label": "体验包", "price": "9.9", "credits": 1, "tier": "", "duration_days": 0, "badge": "", "desc": "1次分析", "visible": True},
    {"id": 12, "type": "points", "label": "标准包", "price": "29.9", "credits": 5, "tier": "", "duration_days": 0, "badge": "", "desc": "5次分析", "visible": True},
    {"id": 13, "type": "points", "label": "专业包", "price": "99", "credits": 25, "tier": "", "duration_days": 0, "badge": "热销", "desc": "25次分析", "visible": True},
    {"id": 14, "type": "points", "label": "企业包", "price": "299", "credits": 100, "tier": "", "duration_days": 0, "badge": "最值", "desc": "100次分析", "visible": True},
]

PROVIDER_RUNTIME_DEFAULTS = {
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai", "model": "gemini-2.0-flash"},
    "kimi": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "minimax": {"base_url": "https://api.minimax.chat/v1", "model": "abab6.5s-chat"},
    "zhipu": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
}


def _read_config(db, key: str, default: str = "") -> str:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return row.value if row and row.value is not None else default


def get_config_value(key: str, default: str = "") -> str:
    db = SessionLocal()
    try:
        return _read_config(db, key, default)
    finally:
        db.close()


def set_config_values(values: dict[str, str], descriptions: dict[str, str] | None = None, db_session=None) -> None:
    db = db_session or SessionLocal()
    close_db = db_session is None
    try:
        for key, value in values.items():
            row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if row:
                row.value = value
            else:
                db.add(SystemConfig(key=key, value=value, description=(descriptions or {}).get(key, "")))
        db.commit()
    finally:
        if close_db:
            db.close()


def get_core_config(db_session=None) -> dict[str, str]:
    db = db_session or SessionLocal()
    close_db = db_session is None
    try:
        return {key: _read_config(db, key, default) for key, default in CORE_CONFIG_DEFAULTS.items()}
    finally:
        if close_db:
            db.close()


def get_pdf_config(db_session=None) -> dict[str, str]:
    db = db_session or SessionLocal()
    close_db = db_session is None
    try:
        return {key: _read_config(db, key, default) for key, default in PDF_CONFIG_DEFAULTS.items()}
    finally:
        if close_db:
            db.close()


def _normalize_sku_item(item: dict[str, Any], fallback_id: int) -> dict[str, Any]:
    sku_type = str(item.get("type") or "points")
    return {
        "id": int(item.get("id") or fallback_id),
        "type": "membership" if sku_type == "membership" else "points",
        "label": str(item.get("label") or ""),
        "price": str(item.get("price") or "0"),
        "credits": int(item.get("credits") or 0),
        "badge": str(item.get("badge") or ""),
        "tier": str(item.get("tier") or ""),
        "duration_days": int(item.get("duration_days") or 0),
        "desc": str(item.get("desc") or ""),
        "visible": bool(item.get("visible", True)),
    }


def _normalize_skus(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [_normalize_sku_item(item, index + 1) for index, item in enumerate(items)]


def _user_sku_key(user_id: int) -> str:
    return f"user_sku_store:{int(user_id)}"


def get_skus(db_session=None) -> list[dict[str, Any]]:
    db = db_session or SessionLocal()
    close_db = db_session is None
    try:
        raw = _read_config(db, "sku_store", "")
        if not raw:
            return _normalize_skus([dict(item) for item in DEFAULT_SKUS])
        data = json.loads(raw)
        if isinstance(data, list):
            return _normalize_skus(data)
    except Exception:
        pass
    finally:
        if close_db:
            db.close()
    return _normalize_skus([dict(item) for item in DEFAULT_SKUS])


def save_skus(items: list[dict[str, Any]], db_session=None) -> None:
    set_config_values({"sku_store": json.dumps(_normalize_skus(items), ensure_ascii=False)}, {"sku_store": "套餐与定价配置"}, db_session)


def get_user_skus(user_id: int, db_session=None) -> tuple[list[dict[str, Any]], bool]:
    db = db_session or SessionLocal()
    close_db = db_session is None
    try:
        raw = _read_config(db, _user_sku_key(user_id), "")
        if not raw:
            return get_skus(db), True
        data = json.loads(raw)
        if isinstance(data, list):
            return _normalize_skus(data), False
    except Exception:
        pass
    finally:
        if close_db:
            db.close()
    return get_skus(), True


def save_user_skus(user_id: int, items: list[dict[str, Any]], db_session=None) -> None:
    set_config_values(
        {_user_sku_key(user_id): json.dumps(_normalize_skus(items), ensure_ascii=False)},
        {_user_sku_key(user_id): f"用户 {user_id} 专属套餐配置"},
        db_session,
    )


def clear_user_skus(user_id: int, db_session=None) -> None:
    db = db_session or SessionLocal()
    close_db = db_session is None
    try:
        row = db.query(SystemConfig).filter(SystemConfig.key == _user_sku_key(user_id)).first()
        if row:
            db.delete(row)
            db.commit()
    finally:
        if close_db:
            db.close()


def get_llm_config() -> dict[str, str]:
    cfg = get_core_config()
    provider = (cfg.get("ai_provider") or "deepseek").strip() or "deepseek"
    defaults = PROVIDER_RUNTIME_DEFAULTS.get(provider, PROVIDER_RUNTIME_DEFAULTS["deepseek"])
    env_key = os.getenv("LLM_API_KEY") or os.getenv(f"{provider.upper()}_API_KEY", "")
    return {
        "provider": provider,
        "base_url": defaults["base_url"].rstrip("/"),
        "model": defaults["model"],
        "api_key": (cfg.get("ai_key") or env_key or "").strip(),
    }


def _as_list(value: Any, limit: int = 5) -> list[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()][:limit]
    if not value:
        return []
    text = str(value)
    parts = re.split(r"[；;\n]+", text)
    return [p.strip(" -•\t") for p in parts if p.strip(" -•\t")][:limit]


def _score_from_detail(value: Any) -> int:
    if isinstance(value, dict):
        value = value.get("score", 0)
    m = re.search(r"(\d{1,3})\s*分?", str(value))
    if not m:
        return 0
    return max(0, min(100, int(m.group(1))))


def normalize_report_result(result: dict[str, Any], weights: dict[str, int] = None) -> dict[str, Any]:
    """Add stable report fields while keeping legacy fields untouched.
    ★ 强制数学接管 overall_score：决不允许 LLM 捏造总分，维度加权平均分即最终得分。"""
    details = result.get("details") or {}
    if not isinstance(details, dict):
        details = {}
        result["details"] = details

    # ═══════════════════════════════════════════
    # ★ 雷达图维度强制固定顺序——彻底杜绝张冠李戴
    # ═══════════════════════════════════════════
    FIXED_DIM_ORDER = [
        ("population_density", "人口密集度"),
        ("traffic_accessibility", "交通可达性"),
        ("traffic_flow", "客流特征"),
        ("consumer_profile", "消费人群"),
        ("competition", "竞争环境"),
        ("complementary_businesses", "互补业态"),
        ("category_advantage", "品类优势"),
        ("cost_estimate", "成本压力"),
    ]

    # ── 从 LLM 原始 dimension_scores 构建 key→score 查找表 ──
    llm_score_map = {}
    llm_text_map = {}
    llm_dims = result.get("dimension_scores")
    if isinstance(llm_dims, list):
        for d in llm_dims:
            if isinstance(d, dict) and d.get("key"):
                raw = d.get("score", 0)
                try:
                    llm_score_map[d["key"]] = int(raw) if raw is not None else 0
                except (ValueError, TypeError):
                    llm_score_map[d["key"]] = 0
                llm_text_map[d["key"]] = str(d.get("text", "") or "")

    # ── 按固定顺序重建 dimension_scores，缺失维度从 detail 补分 ──
    rebuilt_dims = []
    valid_scores = []
    for key, label in FIXED_DIM_ORDER:
        if key in llm_score_map:
            score = llm_score_map[key]
        else:
            score = _score_from_detail(str(details.get(key, "") or ""))
        score = max(0, min(100, score))
        valid_scores.append(score)  # include all 8 dims, zeros penalize skipped dimensions
        text = llm_text_map.get(key) or str(details.get(key, "") or "")
        rebuilt_dims.append({"key": key, "label": label, "score": score, "text": text})

    # ★ 无条件覆写：前端拿到的永远是固定顺序的数组
    result["dimension_scores"] = rebuilt_dims

    # ★ 强制覆写总分 —— 支持业态权重加权平均
    if weights:
        dim_weights = {
            "population_density": weights.get("population_density", 20),
            "traffic_accessibility": weights.get("traffic_accessibility", 20),
            "traffic_flow": 15,
            "consumer_profile": 15,
            "competition": weights.get("competition", 20),
            "complementary_businesses": weights.get("complementary_businesses", 20),
            "category_advantage": 10,
            "cost_estimate": weights.get("cost_estimate", 10),
        }
        total_w = sum(dim_weights.get(d["key"], 10) for d in rebuilt_dims)
        weighted_sum = sum(d["score"] * dim_weights.get(d["key"], 10) for d in rebuilt_dims)
        calculated_score = round(weighted_sum / total_w) if total_w > 0 else 0
    else:
        calculated_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0
    result["score"] = calculated_score
    result["overall_score"] = calculated_score
    result["total_score"] = calculated_score
    print(f"[Backend Calculation] 维度数={len(valid_scores)}, 各维度={valid_scores}, 平均分={calculated_score}, 已强制覆写 AI 原始总分!", flush=True)

    # ── 客观结构化摘要（不包含建议/推荐/推进等主观判断）──
    if "executive_summary" not in result:
        result["executive_summary"] = {
            "summary": str(result.get("summary") or ""),
            "top_strengths": _as_list(result.get("advantages"), 3),
            "top_risks": _as_list(result.get("disadvantages"), 3),
        }
    # 如果 LLM 返回了 executive_summary，清除其中可能存在的 verdict 字段
    if "verdict" in result.get("executive_summary", {}):
        del result["executive_summary"]["verdict"]

    if "action_plan" not in result:
        result["action_plan"] = [
            "先实地复核客流高峰、门头可见度和竞品排队情况。",
            "用最小模型测算房租、人效与日均订单的盈亏平衡线。",
            "围绕优势客群设计开业前三周的引流活动和复购机制。",
        ]
    return result
