"""报告存储服务 — 本地文件 / 云端对象存储"""
import os
import html
from datetime import datetime, timezone, timedelta
from pathlib import Path

CHINA_TZ = timezone(timedelta(hours=8))
from database import SessionLocal
from models.db_models import SystemConfig
from services.runtime_config import get_config_value, get_pdf_config

STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage" / "reports"

# 默认配置
_DEFAULTS = {
    "storage_mode": "local",
    "storage_provider": "aliyun_oss",
    "oss_endpoint": "",
    "oss_bucket": "",
    "oss_access_key_id": "",
    "oss_access_key_secret": "",
}


def _get_config(db_session=None) -> dict:
    """从数据库读取存储配置，未设置则返回默认值"""
    cfg = dict(_DEFAULTS)
    close_db = False
    if db_session is None:
        db_session = SessionLocal()
        close_db = True
    try:
        rows = db_session.query(SystemConfig).filter(SystemConfig.key.in_(cfg.keys())).all()
        for r in rows:
            if r.key in cfg:
                cfg[r.key] = r.value
    finally:
        if close_db:
            db_session.close()
    return cfg


_ASSET_CATEGORIES = {"feedback", "avatars", "qrcode", "share", "reports", "healthcheck"}


def save_user_asset_structured(category: str, filename: str, content_bytes: bytes,
                                content_type: str = "", metadata: dict | None = None) -> "StorageResult":
    """通用用户生成文件云存储入口。返回 StorageResult，云失败保留本地兜底。"""
    from services.cloud_storage import StorageResult, upload_report_to_cloud

    if category not in _ASSET_CATEGORIES:
        return StorageResult(ok=False, error=f"invalid_category: {category}",
                             mode="local")

    # 本地兜底
    asset_dir = STORAGE_DIR.parent / "assets" / category
    asset_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    actual_name = f"{ts}-{filename}"
    local_path = asset_dir / actual_name
    local_path.write_bytes(content_bytes)

    # 构造 COS key（单次 timestamp）
    if category == "feedback":
        cloud_key = f"feedback/{actual_name}"
    elif category == "avatars":
        uid = str((metadata or {}).get("user_id", "anonymous"))
        cloud_key = f"avatars/{uid}/{actual_name}"
    elif category == "qrcode":
        cloud_key = f"qrcode/{actual_name}"
    elif category == "share":
        cloud_key = f"share/{actual_name}"
    elif category == "healthcheck":
        cloud_key = f"healthcheck/{ts}.txt"
    else:
        cloud_key = f"reports/{actual_name}"

    result = upload_report_to_cloud(str(local_path), cloud_key)
    if not result.ok:
        result.local_path = str(local_path)
    return result


def get_storage_mode() -> str:
    """返回当前存储模式: local 或 cloud"""
    return _get_config().get("storage_mode", "local")


def save_report(record_id: int, report_data: dict, address: str = "", brand_name: str = "") -> str:
    """将分析报告保存为 HTML 文件。
    返回云端 URL（成功时）或本地文件路径（云端未配置/失败时）。
    兼容旧调用方（返回字符串）。
    """
    cfg = _get_config()
    mode = cfg.get("storage_mode", "local")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"report_{record_id}_{ts}.html"

    html = _build_report_html(record_id, report_data, address, brand_name)

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = STORAGE_DIR / safe_name
    local_path.write_text(html, encoding="utf-8")

    if mode == "cloud":
        from services.cloud_storage import upload_report_to_cloud
        cloud_key = f"reports/{safe_name}"
        result = upload_report_to_cloud(str(local_path), cloud_key)
        if result.ok and result.url:
            return result.url
        # 云模式失败：保留本地文件 + 打印错误
        print(f"[StorageService] 云端报告上传失败: {result.error}，保留本地文件: {local_path}", flush=True)
        return str(local_path)

    return str(local_path)


def save_report_structured(record_id: int, report_data: dict, address: str = "", brand_name: str = ""):
    """与 save_report 相同，但返回 StorageResult 对象供 main.py 使用。"""
    from services.cloud_storage import StorageResult, upload_report_to_cloud

    cfg = _get_config()
    mode = cfg.get("storage_mode", "local")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"report_{record_id}_{ts}.html"

    html = _build_report_html(record_id, report_data, address, brand_name)

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = STORAGE_DIR / safe_name
    local_path.write_text(html, encoding="utf-8")

    if mode != "cloud":
        return StorageResult(ok=True, local_path=str(local_path), mode="local")

    cloud_key = f"reports/{safe_name}"
    result = upload_report_to_cloud(str(local_path), cloud_key)
    # 云模式失败时保留 local_path
    if not result.ok:
        result.local_path = str(local_path)
    return result


def get_report_content(record_id: int, report_file: str = "", report_url: str = "") -> bytes:
    """获取报告文件内容，支持本地+云端 Try-Fallback"""
    # 云端 URL 优先；云端失败时再回退本地兜底。
    if report_url:
        try:
            import httpx
            r = httpx.get(report_url, timeout=15)
            if r.status_code == 200:
                return r.content
        except Exception:
            pass

    if report_file and os.path.exists(report_file):
        return Path(report_file).read_bytes()

    return b""


def _build_report_html(record_id: int, report_data: dict, address: str, brand_name: str) -> str:
    """生成可直接浏览的标准分析报告 HTML 文件。"""
    score = report_data.get("score", 0)
    summary = report_data.get("summary", "")
    advantages = report_data.get("advantages", [])
    disadvantages = report_data.get("disadvantages", [])
    warning = report_data.get("warning", "")
    details = report_data.get("details", {})
    exec_summary = report_data.get("executive_summary") or {}
    dimension_scores = report_data.get("dimension_scores") or []
    action_plan = report_data.get("action_plan") or []
    real_data = report_data.get("real_data") or {}
    decision_snapshot = report_data.get("decision_snapshot") or {}
    field_checklist = report_data.get("field_checklist") or []
    data_sufficiency = report_data.get("data_sufficiency") or {}
    pdf_cfg = get_pdf_config()
    brand_qr = get_config_value("OFFICIAL_QRCODE_URL", "")
    footer_text = pdf_cfg.get("footer_text") or "商业选址初筛参考"
    # 旧后台配置兜底替换：不把 AI 字样带到用户可见页面
    for old, new in [("AI 选址分析", "址得选"), ("AI选址分析", "址得选"),
                     ("AI 多维度分析", "选址规则分析")]:
        footer_text = footer_text.replace(old, new)

    def _esc(value):
        return html.escape(str(value or ""))

    def _score_int(value):
        try:
            return max(0, min(100, int(value or 0)))
        except Exception:
            return 0

    score_num = _score_int(score)
    score_color = "#18bf82" if score_num >= 70 else "#f59e0b" if score_num >= 50 else "#ef4444"
    score_note = decision_snapshot.get("verdict") or exec_summary.get("verdict") or ("可重点核验" if score_num >= 70 else "需线下验证" if score_num >= 45 else "需谨慎评估")
    city_line = " ".join(str(real_data.get(k) or "").strip() for k in ["city", "district", "township"]).strip()
    business_type = report_data.get("business_type") or report_data.get("industry") or report_data.get("category") or ""
    report_type = report_data.get("report_type") or ""  # P1: fallback 标识
    generated_raw = report_data.get("generated_at") or report_data.get("created_at") or ""
    if generated_raw:
        generated_display = generated_raw[:16] if len(generated_raw) >= 16 else generated_raw
    else:
        generated_display = datetime.now(CHINA_TZ).strftime("%Y-%m-%d %H:%M")  # 仅兜底
    # ── P1: fallback 标识 ──
    fallback_badge_html = ""
    if report_type == "fallback":
        fallback_badge_html = '<div class="notice" style="background:#fef3c7;color:#92400e;border:1px solid #fde68a;margin-bottom:28px;">📋 保守版数据摘要 — 基于采集数据生成，深度分析未展开。建议结合现场核验。</div>'

    # ── P1: 地点基本面 ──
    location_fundamentals = report_data.get("location_fundamentals") or {}
    loc_fund_html = ""
    if location_fundamentals:
        lf_label = _esc(location_fundamentals.get("label") or "")
        lf_summary = _esc(location_fundamentals.get("summary") or "")
        lf_strengths = "".join(f"<p>✓ {_esc(s)}</p>" for s in (location_fundamentals.get("strengths") or [])[:4])
        lf_risks = "".join(f"<p>⚠ {_esc(r)}</p>" for r in (location_fundamentals.get("risks") or [])[:4])
        loc_fund_html = f"""
  <section class="section">
    <h2>📍 地点基本面</h2>
    <div class="info-box" style="background:#f8fafc;border:1px solid #e2e8f0;">
      <div class="info-row"><b>位置类型</b>{lf_label}</div>
      <p style="margin:12px 0 8px;font-size:15px;line-height:1.85;">{lf_summary}</p>
    </div>
    <div class="split" style="margin-top:16px;">
      <div class="soft-card good"><h2>✅ 位置优势</h2>{lf_strengths}</div>
      <div class="soft-card bad"><h2>⚠ 位置风险</h2>{lf_risks}</div>
    </div>
  </section>"""

    # ── P1: 生意模型快照 ──
    biz_snapshot = report_data.get("business_model_snapshot") or {}
    biz_snap_html = ""
    if biz_snapshot:
        bs_core = _esc(biz_snapshot.get("core_logic") or "")
        bs_comp = _esc(biz_snapshot.get("competitor_note") or "")
        bs_fit = _esc(biz_snapshot.get("fit_condition") or "")
        bs_stop = _esc(biz_snapshot.get("stop_condition") or "")
        bs_score = _esc(biz_snapshot.get("score_explanation") or "")
        must_verify = biz_snapshot.get("must_verify") or []
        mv_items = "".join(f"<p>{i+1}. {_esc(v)}</p>" for i, v in enumerate(must_verify[:6]))
        biz_snap_html = f"""
  <section class="section">
    <h2>🏪 行业生意模型：{_esc(business_type or '选址')}</h2>
    <div class="info-box" style="background:#f0fdf4;border:1px solid #bbf7d0;">
      <p style="margin:0;font-size:15px;line-height:1.9;"><b>核心逻辑：</b>{bs_core}</p>
      {f'<p style="margin:12px 0 0;font-size:14px;line-height:1.9;color:#64748b;">{bs_comp}</p>' if bs_comp else ''}
    </div>
    {f'<div class="info-box" style="background:#fff;border:1px solid #e2e8f0;margin-top:14px;"><h3 style="margin:0 0 10px;">📋 必核验项</h3>{mv_items}</div>' if mv_items else ''}
    {f'<div class="info-row" style="color:#16a34a;margin-top:10px;"><b>成立条件</b>{bs_fit}</div>' if bs_fit else ''}
    {f'<div class="info-row" style="color:#dc2626;margin-top:6px;"><b>降级条件</b>{bs_stop}</div>' if bs_stop else ''}
    {f'<p style="margin-top:10px;font-size:14px;color:#64748b;">{bs_score}</p>' if bs_score else ''}
  </section>"""

    # ── P1: 竞品口径说明 ──
    caliber_explanation = report_data.get("caliber_explanation") or ""
    caliber_html = ""
    if caliber_explanation:
        caliber_html = f"""
  <section class="section">
    <h2>📖 竞品口径说明</h2>
    <div class="detail-block" style="border-left-color:#3b82f6;">
      <p>{_esc(caliber_explanation)}</p>
    </div>
  </section>"""

    # ── P1: 证据摘要 ──
    evidence_summary = report_data.get("evidence_summary") or {}
    evidence_html = ""
    if evidence_summary:
        dc = evidence_summary.get("direct_competitors") or {}
        sc = evidence_summary.get("substitute_consumption") or {}
        ta = evidence_summary.get("traffic_anchors") or {}
        kp = evidence_summary.get("key_pois") or {}
        evidence_html = f"""
  <section class="section">
    <h2>📊 关键证据摘要</h2>
    <div class="poi-grid" style="grid-template-columns:repeat(3,1fr);">
      <div class="poi-card">
        <div class="poi-label">直接竞品</div>
        <div class="poi-value">{dc.get('200m', 0)} / {dc.get('500m', 0)} / {dc.get('1000m', 0)}</div>
        <div class="poi-sub">200m / 500m / 1000m</div>
      </div>
      <div class="poi-card">
        <div class="poi-label">替代消费</div>
        <div class="poi-value">{sc.get('200m', 0)} / {sc.get('500m', 0)} / {sc.get('1000m', 0)}</div>
        <div class="poi-sub">200m / 500m / 1000m</div>
      </div>
      <div class="poi-card">
        <div class="poi-label">客流锚点</div>
        <div class="poi-value">{ta.get('200m', 0)} / {ta.get('500m', 0)} / {ta.get('1000m', 0)}</div>
        <div class="poi-sub">200m / 500m / 1000m</div>
      </div>
    </div>
    {f'<div class="note-line">住宅: {kp.get("residential", {}).get("200m", 0)}/{kp.get("residential", {}).get("500m", 0)}/{kp.get("residential", {}).get("1000m", 0)} | 学校: {kp.get("schools", {}).get("200m", 0)}/{kp.get("schools", {}).get("500m", 0)}/{kp.get("schools", {}).get("1000m", 0)} | 办公: {kp.get("office", {}).get("200m", 0)}/{kp.get("office", {}).get("500m", 0)}/{kp.get("office", {}).get("1000m", 0)}</div>' if kp else ''}
  </section>"""

    # ── Phase 3: 客源矛盾解释 ──
    demand_contradiction_note = report_data.get("demand_contradiction_note") or ""
    contradiction_html = ""
    if demand_contradiction_note:
        contradiction_html = f"""
  <section class="section">
    <h2>🔍 客源来源待核验</h2>
    <div class="detail-block" style="border-left-color:#f59e0b;">
      <p>{_esc(demand_contradiction_note)}</p>
    </div>
  </section>"""

    # ── P1: 数据边界 ──
    data_boundary = report_data.get("data_boundary") or ""
    boundary_html = ""
    if data_boundary:
        boundary_html = f"""
  <section class="section disc-section">
    <h2>📌 数据说明与风险提示</h2>
    <div class="detail-block" style="border-left-color:#94a3b8;">
      <p>{_esc(data_boundary)}</p>
    </div>
  </section>"""

    # ── P1: 营收测算说明优先使用 report 中的 revenue_disclaimer ──
    rev_disclaimer = report_data.get("revenue_disclaimer") or ""
    if not rev_disclaimer:
        from services.business_model_service import classify_business_model_family
        rev_family = classify_business_model_family(business_type or "", brand_name or "")
        if rev_family == "education_childcare":
            rev_disclaimer = "以上为模型估算，不代表实际经营结果；需结合周边小学距离、生源数、托管服务组合和租金复核。"
        elif rev_family == "snack_fast_food":
            rev_disclaimer = "以上为模型估算，不代表实际经营结果；需结合现场客流、租金、转让费、出餐能力和外卖能力复核。"
        else:
            rev_disclaimer = "以上为模型估算，不代表实际经营结果；需结合现场客流、租金、转让费和实际经营条件复核。"
    if generated_raw:
        generated_display = generated_raw[:16] if len(generated_raw) >= 16 else generated_raw
    else:
        generated_display = datetime.now(CHINA_TZ).strftime("%Y-%m-%d %H:%M")  # 仅兜底

    def _list_html(items):
        rows = [str(i).strip() for i in (items or []) if str(i).strip()]
        return "".join(f"<p>{_esc(i)}</p>" for i in rows) or "<p>暂无明确结论，建议结合现场核验补充判断。</p>"

    def _ordered_html(items):
        rows = [str(i).strip() for i in (items or []) if str(i).strip()]
        return "".join(f"<p>{idx}. {_esc(item)}</p>" for idx, item in enumerate(rows, 1)) or "<p>暂无行动建议。</p>"

    def _bar(score_value):
        n = _score_int(score_value)
        color = "#18bf82" if n >= 70 else "#f59e0b" if n >= 50 else "#ef4444"
        return f'<div class="bar"><i style="width:{n}%;background:{color}"></i></div>'

    def _dimension_name(item):
        return str(item.get("label") or item.get("name") or item.get("key") or "指标")

    # ── P0.5: 决策快照卡片 ──
    decision_html = ""
    if decision_snapshot:
        ds_verdict = _esc(decision_snapshot.get("verdict") or "")
        ds_one = _esc(decision_snapshot.get("one_sentence") or "")
        ds_strength = _esc(decision_snapshot.get("top_strength") or "")
        ds_risk = _esc(decision_snapshot.get("top_risk") or "")
        ds_next = _esc(decision_snapshot.get("next_action") or "")
        ds_fit = _esc(decision_snapshot.get("fit_condition") or "")
        ds_stop = _esc(decision_snapshot.get("stop_condition") or "")
        decision_html = f"""
  <section class="section">
    <h2>📌 选址决策参考</h2>
    <div class="info-box" style="background:#fff;border:2px solid #1f4aa8;">
      <div class="info-row"><b>综合判断</b><span style="font-weight:900;color:{score_color}">{ds_verdict or '待核验'}</span></div>
      <div class="info-row"><b>一句话结论</b>{ds_one}</div>
      {f'<div class="info-row"><b>最大优势</b>{ds_strength}</div>' if ds_strength else ''}
      {f'<div class="info-row"><b>最大风险</b>{ds_risk}</div>' if ds_risk else ''}
      {f'<div class="info-row"><b>下一步</b>{ds_next}</div>' if ds_next else ''}
      {f'<div class="info-row" style="color:#16a34a"><b>成立条件</b>{ds_fit}</div>' if ds_fit else ''}
      {f'<div class="info-row" style="color:#dc2626"><b>降级条件</b>{ds_stop}</div>' if ds_stop else ''}
    </div>
  </section>"""

    # ── 数据充分度 ──
    suff_html = ""
    if data_sufficiency:
        suff_level = data_sufficiency.get("label") or ""
        suff_summary = _esc(data_sufficiency.get("summary") or "")
        suff_html = f'<div class="notice" style="background:#f0fdf4;color:#047857;border:1px solid #bbf7d0;margin-bottom:28px;">📊 数据充分度：{_esc(suff_level)} — {suff_summary}</div>'

    score_meta_list = report_data.get("dimension_score_meta") or []
    score_meta_by_key = {}
    if isinstance(score_meta_list, list):
        for m in score_meta_list:
            if not isinstance(m, dict):
                continue
            k = str(m.get("key") or "").strip()
            if not k:
                continue
            score_meta_by_key[k] = m

    dim_cards = ""
    for item in (dimension_scores or [])[:8]:
        label = _dimension_name(item)
        val = _score_int(item.get("score"))
        key = str(item.get("key") or "").strip()
        meta = score_meta_by_key.get(key, {})
        low_note = ""
        if meta.get("score_confidence") == "low":
            note_text = _esc(meta.get("note") or "")
            if key == "cost_estimate":
                note_text = "低置信：缺少租金、人工、营收测算，当前分数为占位参考"
            elif key == "population_density":
                note_text = _esc(meta.get("note") or "低置信：近场客源依据偏弱")
            if note_text:
                low_note = f'<div style="font-size:11px;color:#f59e0b;margin-top:4px">⚠ {note_text}</div>'
        dim_cards += f"""
        <div class="metric-card">
          <div class="metric-row"><strong>{_esc(label)}</strong><b style="color:{'#18bf82' if val >= 70 else '#f59e0b' if val >= 50 else '#ef4444'}">{val}</b></div>
          {_bar(val)}
          {low_note}
        </div>"""

    detail_labels = {
        "population_density": ("🏘️", "人口密集度"),
        "traffic_accessibility": ("🚇", "交通与可达性"),
        "traffic_flow": ("🚶", "客流特征"),
        "consumer_profile": ("🛍️", "消费人群属性"),
        "competition": ("⚔️", "竞争环境"),
        "complementary_businesses": ("🤝", "周边互补业态"),
        "category_advantage": ("🌟", "品类优势与差异化"),
        "cost_estimate": ("💰", "房租成本预估"),
        "revenue_estimation": ("💵", "营收测算模型"),
        "site_suggestion": ("📋", "选址分析与运营策略"),
    }
    detail_blocks = ""
    for key, (icon, label) in detail_labels.items():
        val = details.get(key)
        if val:
            text = str(val).replace("评分：", "评分: ")
            color = "#18bf82"
            if key in {"traffic_accessibility", "revenue_estimation", "site_suggestion"}:
                color = "#ef4444"
            elif key in {"consumer_profile", "cost_estimate"}:
                color = "#f59e0b"
            detail_blocks += f"""
            <div class="detail-block" style="border-left-color:{color}">
              <h3>{icon} {_esc(label)}</h3>
              <p>{_esc(text)}</p>
            </div>"""

    poi_cards = ""
    if real_data:
        poi_defs = [
            ("🏘️", "住宅小区", "residential"), ("🏢", "写字楼", "office"),
            ("🍽️", "餐饮门店", "restaurants"), ("☕", "咖啡茶饮", "cafe_tea"),
            ("🛍️", "购物商场", "shopping"), ("🏫", "学校", "schools"),
            ("🏥", "医院", "hospitals"), ("🚇", "地铁站", "subway"),
            ("🚌", "公交站", "bus"), ("🏨", "酒店", "hotels"),
            ("🏦", "银行", "banks"), ("🅿️", "停车场", "parking"),
        ]
        for icon, label, key in poi_defs:
            s2 = real_data.get("stats_200m") or {}
            s5 = real_data.get("stats_500m") or {}
            s10 = real_data.get("stats_1000m") or {}
            s200 = s2.get(key, 0)
            s500 = s5.get(key, 0)
            s1000 = s10.get(key, 0)
            # 旧报告兼容：只有当三层字段均缺失时才回退 raw/poi_counts（保护：值=0 的新报告不误触）
            has_triple = (key in s2) or (key in s5) or (key in s10)
            if not has_triple:
                raw_val = (real_data.get("raw_stats_1000m") or {}).get(key)
                cnt_val = (real_data.get("poi_counts") or {}).get(key)
                fallback = raw_val if raw_val is not None else (cnt_val if cnt_val is not None else 0)
                if fallback > 0:
                    poi_cards += f"""
            <div class="poi-card poi-zero">
              <div class="poi-label">{icon} {_esc(label)}</div>
              <div class="poi-value">数据源记录 {fallback}</div>
              <div class="poi-sub">旧版数据（无三层半径明细）</div>
            </div>"""
                    continue
            zero_class = " poi-zero" if s200 == 0 and s500 == 0 and s1000 == 0 else ""
            warn_class = " poi-warn" if key == "subway" and s1000 == 0 else ""
            poi_cards += f"""
            <div class="poi-card{zero_class}{warn_class}">
              <div class="poi-label">{icon} {_esc(label)}</div>
              <div class="poi-value">{s200} / {s500} / {s1000}</div>
              <div class="poi-sub">200m / 500m / 1000m</div>
            </div>"""

    comp_html = ""
    if real_data:
        direct = real_data.get("direct_competitor_list") or real_data.get("competitor_list") or []
        if direct:
            brands = "、".join(_esc(x.get("name", "")) for x in direct[:4] if x.get("name"))
            comp_html = f"""
            <div class="chain-card">
              <h3>🏬 周边连锁品牌</h3>
              <p>{brands or "暂无明确连锁品牌"}{f" ×{len(direct)}" if len(direct) else ""}</p>
            </div>"""

    notes_html = ""
    notes = real_data.get("data_quality_notes") or []
    if notes:
        notes_html = '<div class="note-line">注：' + "；".join(_esc(n) for n in notes) + "</div>"

    # ── P0.5: 现场核验清单 ──
    checklist_html = ""
    if field_checklist:
        cl_rows = ""
        for idx, item in enumerate(field_checklist[:8], 1):
            # 字符串兼容
            if isinstance(item, str):
                cl_rows += f"<p>{idx}. {_esc(item)}</p>"
                continue
            if not isinstance(item, dict):
                continue
            title = _esc(item.get("title") or item.get("text") or "")
            time_win = _esc(item.get("time_window") or "")
            action = _esc(item.get("action") or "")
            risk = _esc(item.get("risk_type") or "")
            p_hint = _esc(item.get("pass_hint") or "")
            e_hint = _esc(item.get("eliminate_hint") or "")
            cl_rows += f"""<div class="detail-block" style="border-left-color:#3b82f6;margin-bottom:14px;">
              <h3>{idx}. {title}</h3>
              {f'<p><b>建议时间：</b>{time_win}</p>' if time_win else ''}
              {f'<p><b>核验动作：</b>{action}</p>' if action else ''}
              {f'<p><b>风险类型：</b>{risk}</p>' if risk else ''}
              {f'<p style="color:#047857"><b>通过信号：</b>{p_hint}</p>' if p_hint else ''}
              {f'<p style="color:#b91c1c"><b>淘汰信号：</b>{e_hint}</p>' if e_hint else ''}
            </div>"""
        checklist_html = f"""
  <section class="section">
    <h2>📋 现场核验清单</h2>
    {cl_rows}
  </section>"""

    warning_html = f'<div class="risk-banner">🚨 风险提示：{_esc(warning)}</div>' if warning else ""
    adv_html = _list_html(exec_summary.get("top_strengths") or advantages)
    dis_html = _list_html(exec_summary.get("top_risks") or disadvantages)
    action_html = _ordered_html(action_plan)
    summary_text = exec_summary.get("summary") or summary or "暂无摘要，建议结合现场客流、租金和商户经营状态核验。"
    # 优先使用 decision_snapshot.one_sentence 作为评分描述
    score_desc = decision_snapshot.get("one_sentence") or exec_summary.get("score_explanation") or summary_text
    qr_html = f'<img class="qr" src="{_esc(brand_qr)}" alt="二维码">' if brand_qr else '<div class="qr empty"></div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>址得选 · 商业选址初筛报告 - {_esc(brand_name or address)}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#f7f9fc; color:#475569; font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",Arial,sans-serif; }}
  .page {{ width:960px; margin:0 auto; background:#f7f9fc; padding:38px 58px 52px; border-left:1px solid #e5e7eb; border-right:1px solid #e5e7eb; }}
  .title {{ text-align:center; color:#1f4aa8; font-size:26px; font-weight:900; letter-spacing:.5px; margin:0 0 8px; }}
  .subtitle {{ text-align:center; color:#94a3b8; font-size:12px; font-weight:700; margin-bottom:18px; }}
  .rule {{ height:1px; background:#e2e8f0; margin-bottom:20px; }}
  .info-box {{ background:#eef6ff; border-radius:12px; padding:22px 28px; margin-bottom:28px; line-height:2.05; font-size:15px; }}
  .info-row b {{ color:#1f4aa8; margin-right:12px; }}
  .notice {{ text-align:center; border-radius:8px; padding:10px 14px; margin:0 0 28px; font-size:13px; font-weight:800; }}
  .notice-yellow {{ color:#92400e; background:#fffbeb; border:1px solid #fde68a; }}
  .risk-banner {{ color:#b91c1c; background:#fff1f2; border:1px solid #fecaca; border-radius:8px; padding:12px 18px; margin:0 0 28px; text-align:center; font-weight:900; }}
  .score-panel {{ display:grid; grid-template-columns:230px 1fr; gap:28px; align-items:center; background:#fff; border:1px solid #e2e8f0; border-radius:14px; padding:22px 24px; margin-bottom:34px; }}
  .score-circle {{ width:170px; height:170px; border-radius:50%; margin:0 auto; display:flex; align-items:center; justify-content:center; flex-direction:column; background:conic-gradient({score_color} {score_num * 3.6}deg,#e5e7eb 0); position:relative; }}
  .score-circle:before {{ content:""; position:absolute; inset:18px; background:#fff; border-radius:50%; }}
  .score-circle strong {{ position:relative; z-index:1; font-size:46px; color:{score_color}; line-height:1; }}
  .score-circle span {{ position:relative; z-index:1; font-size:16px; color:#94a3b8; font-weight:800; }}
  .score-side {{ border-left:1px dashed #cbd5e1; padding-left:26px; }}
  .score-side p {{ margin:0 0 16px; font-size:15px; line-height:1.85; }}
  h2 {{ color:#0f172a; font-size:20px; margin:0 0 18px; font-weight:900; }}
  h3 {{ color:#0f172a; font-size:18px; margin:0 0 10px; font-weight:900; }}
  .split {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; margin-bottom:36px; }}
  .soft-card {{ border-radius:16px; padding:26px 28px; min-height:300px; line-height:1.9; font-size:15px; }}
  .soft-card p {{ margin:0 0 14px; }}
  .good {{ background:#effdf5; border:1px solid #bbf7d0; }}
  .bad {{ background:#fff5f5; border:1px solid #fecaca; }}
  .good h2 {{ color:#047857; }}
  .bad h2 {{ color:#b91c1c; }}
  .section {{ margin:36px 0; }}
  .dimension-wrap {{ display:grid; grid-template-columns:1fr 1fr; gap:18px; align-items:center; }}
  .metrics {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
  .metric-card {{ background:#fff; border:1px solid #e2e8f0; border-radius:10px; padding:12px 14px; }}
  .metric-row {{ display:flex; align-items:center; justify-content:space-between; gap:12px; color:#334155; font-weight:900; }}
  .metric-row b {{ font-size:22px; }}
  .bar {{ height:6px; border-radius:999px; background:#e5e7eb; overflow:hidden; margin-top:8px; }}
  .bar i {{ height:100%; display:block; }}
  .poi-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }}
  .poi-card {{ background:#fff; border-radius:10px; padding:14px 10px; min-height:88px; text-align:center; border:1px solid #edf2f7; box-shadow:0 1px 8px rgba(15,23,42,.025); }}
  .poi-card.poi-warn {{ background:#fff1f2; }}
  .poi-card.poi-zero {{ opacity:.58; }}
  .poi-label {{ font-size:12px; color:#64748b; font-weight:800; margin-bottom:6px; }}
  .poi-value {{ font-size:18px; line-height:1.15; color:#0f172a; font-weight:900; font-variant-numeric:tabular-nums; }}
  .poi-sub {{ font-size:10px; color:#a8b0bd; margin-top:4px; }}
  .note-line {{ text-align:center; color:#94a3b8; font-size:11px; margin-top:14px; }}
  .chain-card {{ background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; margin-top:18px; padding:16px; text-align:center; }}
  .chain-card h3 {{ color:#047857; font-size:17px; }}
  .chain-card p {{ margin:0; font-size:15px; font-weight:800; color:#64748b; }}
  .detail-block {{ border-left:4px solid #18bf82; padding:12px 0 12px 22px; margin:0 0 26px; }}
  .detail-block p {{ margin:0; font-size:16px; line-height:1.95; color:#526173; }}
  .footer {{ margin-top:34px; background:#fff; border:1px solid #e2e8f0; border-radius:12px; padding:20px 24px; display:flex; align-items:center; justify-content:space-between; }}
  .footer strong {{ color:#1f4aa8; font-size:17px; }}
  .footer p {{ margin:8px 0 0; color:#94a3b8; font-size:13px; line-height:1.8; }}
  .qr {{ width:104px; height:104px; object-fit:contain; border:1px solid #e2e8f0; border-radius:10px; background:#fff; }}
  .qr.empty {{ border-style:dashed; }}
  @media (max-width: 900px) {{ .page {{ width:auto; padding:28px 18px; }} .score-panel,.split,.dimension-wrap {{ grid-template-columns:1fr; }} .score-side {{ border-left:0; padding-left:0; border-top:1px dashed #cbd5e1; padding-top:18px; }} .poi-grid {{ grid-template-columns:repeat(2,1fr); }} }}
</style>
</head>
<body>
<main class="page">
  <h1 class="title">址得选 · 商业选址初筛报告</h1>
  <div class="subtitle">商业选址初筛参考 | 基于周边 POI 数据与选址规则 | 生成时间：{_esc(generated_display)}</div>
  <div class="rule"></div>

  <section class="info-box">
    <div class="info-row"><b>📍 分析地址</b>{_esc(address)}</div>
    <div class="info-row"><b>🏷️ 分析品牌</b>{_esc(brand_name or "-")}</div>
    <div class="info-row"><b>🏪 选址业态</b>{_esc(business_type or "-")}</div>
    <div class="info-row"><b>📅 生成时间</b>{_esc(generated_display)}</div>
    <div class="info-row"><b>🗺️ 所属区域</b>{_esc(city_line or "-")}</div>
  </section>

  <div class="notice notice-yellow">⚠️ 本报告为选址初筛参考，不提供投资建议，各维度评分仅供参考，后续判断请结合实地考察</div>
  {fallback_badge_html}
  {warning_html}
  {decision_html}
  {suff_html}
  {loc_fund_html}

  <section class="score-panel">
    <div>
      <h2 style="text-align:center;margin-bottom:14px">📊 综合评分</h2>
      <div class="score-circle"><strong>{score_num or "-"}</strong><span>/ 100</span></div>
    </div>
    <div class="score-side">
      <p>{_esc(score_desc)}</p>
      <h3>📋 分析摘要</h3>
      <p>{_esc(summary_text)}</p>
    </div>
  </section>

  <section class="split">
    <div class="soft-card good"><h2>✅ 关键优势</h2>{adv_html}</div>
    <div class="soft-card bad"><h2>⚠️ 主要风险</h2>{dis_html}</div>
  </section>

  {f'<section class="section"><h2>📊 关键维度评分</h2><div class="dimension-wrap"><div></div><div class="metrics">{dim_cards}</div></div></section>' if dim_cards else ''}

  {f'<section class="section"><h2>📊 周边真实数据（200m / 500m / 1000m 三层半径采集）</h2><div class="poi-grid">{poi_cards}</div>{notes_html}{comp_html}</section>' if poi_cards else ''}

  {biz_snap_html}
  {caliber_html}
  {evidence_html}
  {contradiction_html}

  {f'<section class="section"><h2>📝 各维度详细分析</h2>{detail_blocks}</section>' if detail_blocks else ''}

  {f'<section class="section disc-section"><h2>📌 营收测算说明</h2><p>{rev_disclaimer}</p></section>' if detail_blocks else ''}

  {checklist_html}

  {f'<section class="section"><h2>💡 经营建议</h2><div class="detail-block" style="border-left-color:#ef4444">{action_html}</div></section>' if action_plan else ''}

  {boundary_html}

  <section class="footer">
    <div>
      <strong>址得选 · 商业选址初筛报告</strong>
      <p>{_esc(footer_text)}<br>本报告由系统自动生成，仅供商业决策参考，不构成投资建议。</p>
    </div>
    <div>{qr_html}<div style="font-size:11px;text-align:center;color:#1f4aa8;font-weight:900;margin-top:8px;">扫码获取更多测算</div></div>
  </section>
</main>
</body>
</html>"""
