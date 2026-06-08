"""报告存储服务 — 本地文件 / 云端对象存储"""
import os
import html
from datetime import datetime
from pathlib import Path
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


def get_storage_mode() -> str:
    """返回当前存储模式: local 或 cloud"""
    return _get_config().get("storage_mode", "local")


def save_report(record_id: int, report_data: dict, address: str = "", brand_name: str = "") -> str:
    """将分析报告保存为 HTML 文件，返回文件路径（本地模式）或 URL（云端模式）"""
    cfg = _get_config()
    mode = cfg.get("storage_mode", "local")
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = f"report_{record_id}_{ts}.html"

    html = _build_report_html(record_id, report_data, address, brand_name)

    # 始终先存本地（兜底）
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    local_path = STORAGE_DIR / safe_name
    local_path.write_text(html, encoding="utf-8")

    # 云端模式：同时上传到 COS
    cloud_url = ""
    if mode == "cloud":
        try:
            from services.cloud_storage import get_cloud_client, upload_to_cloud, get_cloud_url
            _, client_data = get_cloud_client()
            if client_data:
                cloud_key = f"reports/{safe_name}"
                if upload_to_cloud(str(local_path), cloud_key, client_data):
                    cloud_url = get_cloud_url(cloud_key, client_data)
        except Exception as e:
            print(f"[StorageService] 云端报告上传失败: {e}", flush=True)

    return cloud_url or str(local_path)


def get_report_content(record_id: int, report_file: str = "", report_url: str = "") -> bytes:
    """获取报告文件内容，支持本地+云端 Try-Fallback"""
    # 本地文件优先
    if report_file and os.path.exists(report_file):
        return Path(report_file).read_bytes()

    # 云端模式：从 COS 下载
    if report_url:
        try:
            from services.cloud_storage import get_cloud_client
            import httpx
            # 先尝试直接 HTTP 下载
            r = httpx.get(report_url, timeout=15)
            if r.status_code == 200:
                return r.content
        except Exception:
            pass

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
    pdf_cfg = get_pdf_config()
    brand_qr = get_config_value("OFFICIAL_QRCODE_URL", "")
    footer_text = pdf_cfg.get("footer_text") or "AI 选址分析 · 商业选址初筛参考"

    def _esc(value):
        return html.escape(str(value or ""))

    def _score_int(value):
        try:
            return max(0, min(100, int(value or 0)))
        except Exception:
            return 0

    score_num = _score_int(score)
    score_color = "#18bf82" if score_num >= 70 else "#f59e0b" if score_num >= 50 else "#ef4444"
    score_note = exec_summary.get("verdict") or ("可重点核验" if score_num >= 70 else "需线下验证" if score_num >= 45 else "需谨慎评估")
    city_line = " ".join(str(real_data.get(k) or "").strip() for k in ["city", "district", "township"]).strip()
    business_type = report_data.get("business_type") or report_data.get("industry") or report_data.get("category") or "-"
    created_date = datetime.now().strftime("%Y-%m-%d")

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

    dim_cards = ""
    for item in (dimension_scores or [])[:8]:
        label = _dimension_name(item)
        val = _score_int(item.get("score"))
        dim_cards += f"""
        <div class="metric-card">
          <div class="metric-row"><strong>{_esc(label)}</strong><b style="color:{'#18bf82' if val >= 70 else '#f59e0b' if val >= 50 else '#ef4444'}">{val}</b></div>
          {_bar(val)}
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
            s200 = (real_data.get("stats_200m") or {}).get(key, 0)
            s500 = (real_data.get("stats_500m") or {}).get(key, 0)
            s1000 = (real_data.get("stats_1000m") or {}).get(key, 0)
            raw = (real_data.get("raw_stats_1000m") or {}).get(key)
            total = raw if raw is not None and key not in {"parking", "banks"} else s1000
            zero_class = " poi-zero" if s200 == 0 and s500 == 0 and s1000 == 0 else ""
            warn_class = " poi-warn" if key == "subway" and s1000 == 0 else ""
            poi_cards += f"""
            <div class="poi-card{zero_class}{warn_class}">
              <div class="poi-label">{icon} {_esc(label)}</div>
              <div class="poi-value">{s200} / {s500} / {s1000}</div>
              <div class="poi-sub">200m / 500m / 1000m</div>
              {f'<div class="poi-total">合计 {total}</div>' if total not in (None, s1000) else ''}
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

    warning_html = f'<div class="risk-banner">🚨 风险提示：{_esc(warning)}</div>' if warning else ""
    adv_html = _list_html(exec_summary.get("top_strengths") or advantages)
    dis_html = _list_html(exec_summary.get("top_risks") or disadvantages)
    action_html = _ordered_html(action_plan)
    summary_text = exec_summary.get("summary") or summary or "暂无摘要，建议结合现场客流、租金和商户经营状态核验。"
    score_desc = exec_summary.get("score_explanation") or summary_text
    qr_html = f'<img class="qr" src="{_esc(brand_qr)}" alt="二维码">' if brand_qr else '<div class="qr empty"></div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>址得选 · AI选址分析报告 - {_esc(brand_name or address)}</title>
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
  .poi-total {{ margin-top:4px; font-size:11px; color:#64748b; }}
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
  <h1 class="title">址得选 · AI选址分析报告</h1>
  <div class="subtitle">商业选址数据决策平台 | 基于实时 POI 数据 + AI 多维度分析 | {datetime.now().strftime("%Y/%m/%d %H:%M")}</div>
  <div class="rule"></div>

  <section class="info-box">
    <div class="info-row"><b>📍 分析地址</b>{_esc(address)}</div>
    <div class="info-row"><b>🏷️ 分析品牌</b>{_esc(brand_name or "-")}</div>
    <div class="info-row"><b>🏪 选址业态</b>{_esc(business_type)}</div>
    <div class="info-row"><b>📅 生成日期</b>{created_date}</div>
    <div class="info-row"><b>🗺️ 所属区域</b>{_esc(city_line or "-")}</div>
  </section>

  <div class="notice notice-yellow">⚠️ 本工具不提供“推荐/不推荐”结论，各维度评分仅供参考，最终决策请结合实地考察</div>
  {warning_html}

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

  {f'<section class="section"><h2>📊 指标雷达与维度评分</h2><div class="dimension-wrap"><div></div><div class="metrics">{dim_cards}</div></div></section>' if dim_cards else ''}

  {f'<section class="section"><h2>📊 周边真实数据（200m / 500m / 1000m 三层半径采集）</h2><div class="poi-grid">{poi_cards}</div>{notes_html}{comp_html}</section>' if poi_cards else ''}

  {f'<section class="section"><h2>📝 各维度详细分析</h2>{detail_blocks}</section>' if detail_blocks else ''}

  {f'<section class="section"><h2>📋 选址分析与运营策略</h2><div class="detail-block" style="border-left-color:#ef4444">{action_html}</div></section>' if action_plan else ''}

  <section class="footer">
    <div>
      <strong>址得选 · AI 选址分析报告</strong>
      <p>{_esc(footer_text)}<br>本报告由系统自动生成，仅供商业决策参考，不构成投资建议。</p>
    </div>
    <div>{qr_html}<div style="font-size:11px;text-align:center;color:#1f4aa8;font-weight:900;margin-top:8px;">扫码获取更多测算</div></div>
  </section>
</main>
</body>
</html>"""

