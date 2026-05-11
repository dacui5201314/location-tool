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

    if mode == "local":
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        filepath = STORAGE_DIR / safe_name
        filepath.write_text(html, encoding="utf-8")
        return str(filepath)
    else:
        # 云端模式：上传到 OSS/S3
        return _upload_to_cloud(cfg, safe_name, html)


def get_report_content(record_id: int, report_file: str = "", report_url: str = "") -> bytes:
    """获取报告文件内容，支持存储模式热切换下的 Try-Fallback：
    - 云端模式优先从云端拉取，失败/404 时回退本地文件
    - 本地模式直接读本地文件，不存在则尝试云端 URL
    - 全部失败返回空字节，调用方应返回友好 404
    """
    mode = get_storage_mode()

    if mode == "cloud" and report_url:
        content = _download_from_cloud(report_url)
        if content:
            return content
        # Fallback: 云端未找到，尝试本地路径
        if report_file and os.path.exists(report_file):
            return Path(report_file).read_bytes()

    elif mode == "local":
        if report_file and os.path.exists(report_file):
            return Path(report_file).read_bytes()
        # Fallback: 本地不存在，尝试云端 URL（可能刚从 OSS 迁移过来）
        if report_url:
            content = _download_from_cloud(report_url)
            if content:
                return content

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
    footer_text = pdf_cfg.get("footer_text") or "AI 选址分析 · 商业数据决策平台"
    logo_url = pdf_cfg.get("logo_url") or ""
    verdict = exec_summary.get("verdict") or ("建议推进" if score >= 60 else "谨慎验证" if score >= 40 else "高风险")
    tone = "#0f8a5f" if score >= 60 else "#b7791f" if score >= 40 else "#dc2626"

    def _list_html(items):
        return "".join(f"<li>{html.escape(str(i))}</li>" for i in (items or []) if str(i).strip())

    def _bar(score_value):
        try:
            n = max(0, min(100, int(score_value or 0)))
        except Exception:
            n = 0
        color = "#0f8a5f" if n >= 60 else "#b7791f" if n >= 40 else "#dc2626"
        return (
            '<div class="bar"><i style="width:%s%%;background:%s"></i></div>'
            % (n, color)
        )

    detail_html = ""
    detail_labels = {
        "population_density": "人口密集度", "traffic_accessibility": "交通与可达性",
        "traffic_flow": "客流特征", "consumer_profile": "消费人群属性",
        "competition": "竞争环境", "complementary_businesses": "周边互补业态",
        "category_advantage": "品类优势与差异化", "cost_estimate": "房租成本预估",
        "revenue_estimation": "营收测算模型", "site_suggestion": "选址分析与运营策略",
    }
    for key, label in detail_labels.items():
        val = details.get(key)
        if val:
            clean_val = str(val).replace("评分：", "评分: ")
            detail_html += f'<div class="dim"><h4>{html.escape(str(label))}</h4><p>{html.escape(clean_val)}</p></div>'

    dim_html = ""
    if dimension_scores:
        for item in dimension_scores[:8]:
            label = html.escape(str(item.get("label") or item.get("key") or "指标"))
            val = int(item.get("score") or 0)
            dim_html += f'<div class="metric"><div><strong>{label}</strong><span>{val or "-"}</span></div>{_bar(val)}</div>'

    adv_html = _list_html(exec_summary.get("top_strengths") or advantages)
    dis_html = _list_html(exec_summary.get("top_risks") or disadvantages)
    action_html = _list_html(action_plan)
    # Build real_data POI HTML
    real_html = ""
    if real_data:
        poi_rows = []
        for label, key in [
            ("🏘️ 住宅小区", "residential"), ("🏢 写字楼", "office"), ("🏫 学校", "schools"),
            ("🏥 医院", "hospitals"), ("🛍️ 购物商场", "shopping"), ("🍽️ 餐饮门店", "restaurants"),
            ("☕ 咖啡茶饮", "cafe_tea"), ("🍔 快餐", "fast_food"), ("🥢 中餐厅", "chinese_restaurants"),
            ("🍝 异国料理", "foreign_restaurants"), ("🏨 酒店住宿", "hotels"), ("🚇 地铁站", "subway"),
            ("🚌 公交站", "bus"), ("🅿️ 停车场", "parking"), ("🏦 银行", "banks"),
            ("🏪 便利店", "convenience"), ("💊 药店", "pharmacy"), ("🍺 酒吧", "bars"),
        ]:
            s200 = (real_data.get("stats_200m") or {}).get(key, 0)
            s500 = (real_data.get("stats_500m") or {}).get(key, 0)
            s1000 = (real_data.get("stats_1000m") or {}).get(key, 0)
            raw1000 = (real_data.get("raw_stats_1000m") or {}).get(key)
            show_raw = raw1000 is not None and raw1000 != s1000
            val_text = f"{s200} / {s500} / {s1000}" if s1000 is not None else f"{s200} 个"
            poi_rows.append(f'<div class="metric"><div><strong>{label}</strong><span>{val_text}</span></div>{"".join(f"<small>(共:{raw1000})</small>" if show_raw else "")}</div>')
        if poi_rows:
            comp_html = ""
            if real_data.get("competitors_1000m", 0) > 0:
                clist = real_data.get("competitor_list") or []
                clist_html = "".join(f"<span>{html.escape(c.get('name',''))}（{c.get('distance','')}m） </span>" for c in clist[:10])
                comp_html = f'<div style="background:#fff7ed;border-radius:6px;padding:10px;margin:8px 0;border:1px solid #fed7aa"><strong style="color:#dc2626">⚔️ 同类竞品</strong><br><span style="font-size:12px;color:#9a3412">200m: {real_data.get("competitors_200m",0)}家 · 500m: {real_data.get("competitors_500m",0)}家 · 1km: {real_data.get("competitors_1000m",0)}家</span><br><span style="font-size:11px;color:#9a3412">{clist_html}</span></div>'
            brand_html = ""
            if real_data.get("hot_brands"):
                brand_html = '<div style="background:#f0fdf4;border-radius:6px;padding:10px;margin:8px 0;border:1px solid #bbf7d0"><strong style="color:#15803d">🏪 周边连锁品牌</strong><br>' + "".join(f'<span style="font-size:11px;margin-right:10px;color:#333"><strong>{html.escape(b.get("name",""))}</strong> ×{b.get("count",0)}</span>' for b in real_data.get("hot_brands", [])[:12]) + '</div>'
            info_line = ""
            if real_data.get("city"):
                info_line = f'<div style="font-size:11px;color:#888;text-align:center;margin-top:6px">📍 {html.escape(real_data.get("city",""))} {html.escape(real_data.get("district",""))} {html.escape(real_data.get("township",""))}</div>'
            real_html = f'<section class="card"><h2>📊 周边POI数据</h2><div class="metrics">{"".join(poi_rows)}</div><p style="font-size:10px;color:#888;margin-top:4px">200m / 500m / 1000m 三层半径实时采集 · 已过滤低关联干扰项</p>{comp_html}{brand_html}{info_line}</section>'

    warning_html = f'<div class="warning">⚠️ {html.escape(str(warning))}</div>' if warning else ""
    logo_html = f'<img class="logo" src="{html.escape(logo_url)}" alt="logo">' if logo_url else '<div class="logo-fallback">址</div>'
    qr_html = f'<img class="qr" src="{html.escape(brand_qr)}" alt="品牌二维码">' if brand_qr else '<div class="qr empty"></div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>选址分析报告 - {html.escape(brand_name or address)}</title>
<style>
  body {{ font-family: -apple-system, "Microsoft YaHei", "PingFang SC", sans-serif; max-width: 860px; margin: 0 auto; color: #1e293b; background: #eef3f8; }}
  .cover {{ background:#0f172a; color:white; padding:34px 40px; border-radius:0 0 18px 18px; }}
  .cover-top {{ display:flex; justify-content:space-between; gap:24px; align-items:flex-start; }}
  .eyebrow {{ color:#93c5fd; font-size:11px; letter-spacing:4px; margin-bottom:10px; }}
  h1 {{ font-size:28px; line-height:1.25; margin:0; }}
  .meta {{ font-size:12px; color:#cbd5e1; line-height:1.8; margin-top:10px; }}
  .logo,.logo-fallback {{ width:58px; height:58px; border-radius:10px; background:white; object-fit:contain; padding:6px; box-sizing:border-box; }}
  .logo-fallback {{ display:flex; align-items:center; justify-content:center; color:#2563eb; font-weight:900; font-size:24px; }}
  .hero-grid {{ display:grid; grid-template-columns:1.1fr .9fr; gap:18px; margin-top:26px; }}
  .score-card {{ background:white; color:#0f172a; border-radius:14px; padding:20px; }}
  .score-num {{ font-size:56px; font-weight:900; color:{tone}; line-height:.9; }}
  .verdict {{ display:inline-block; font-size:12px; font-weight:800; color:{tone}; background:#f8fafc; padding:5px 10px; border-radius:999px; }}
  main {{ padding:26px 40px 38px; }}
  .card {{ background:#fff; border-radius:12px; padding:18px; margin-bottom:16px; box-shadow:0 1px 4px rgba(15,23,42,.06); border:1px solid #e2e8f0; }}
  .split {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
  h2 {{ font-size:16px; margin:0 0 12px; color:#0f172a; }}
  .adv {{ border-color:#bbf7d0; background:#f8fffb; }}
  .dis {{ border-color:#fecaca; background:#fffafa; }}
  .adv h2 {{ color:#047857; }}
  .dis h2 {{ color:#b91c1c; }}
  .warning {{ background:#fef2f2; border:1px solid #fecaca; border-radius:10px; padding:12px 14px; font-size:13px; color:#991b1b; margin-bottom:16px; font-weight:700; }}
  .metrics {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }}
  .metric {{ border:1px solid #e2e8f0; border-radius:10px; padding:12px; background:white; }}
  .metric div:first-child {{ display:flex; justify-content:space-between; gap:8px; align-items:center; }}
  .metric strong {{ font-size:12px; color:#334155; }}
  .metric span {{ font-size:16px; font-weight:900; color:#0f172a; }}
  .bar {{ height:6px; border-radius:99px; background:#e5e7eb; margin-top:8px; overflow:hidden; }}
  .bar i {{ display:block; height:100%; }}
  .dim {{ background:#f8fafc; border-radius:10px; padding:14px; margin-bottom:10px; border-left:3px solid #2563eb; }}
  .dim h4 {{ font-size:13px; color:#0f172a; margin:0 0 6px; }}
  .dim p {{ font-size:13px; color:#475569; line-height:1.75; margin:0; white-space:pre-wrap; }}
  ul,ol {{ margin:0; padding-left:20px; font-size:13px; line-height:1.85; color:#334155; }}
  .footer {{ display:flex; gap:22px; align-items:center; margin-top:24px; padding:20px; border-top:3px solid #0f172a; background:#f8fafc; border-radius:12px; }}
  .footer-copy {{ flex:1; font-size:11px; color:#64748b; line-height:1.8; }}
  .qr {{ width:112px; height:112px; object-fit:contain; border-radius:8px; border:1px solid #e2e8f0; background:white; }}
  .qr.empty {{ border-style:dashed; }}
</style>
</head>
<body>
<section class="cover">
  <div class="cover-top">
    <div>
      <div class="eyebrow">AI LOCATION INTELLIGENCE</div>
      <h1>{html.escape(brand_name or "选址分析报告")}</h1>
      <div class="meta">地址：{html.escape(address)}<br>报告编号：#{record_id} · 生成时间：{datetime.now().strftime("%Y-%m-%d")}</div>
    </div>
    {logo_html}
  </div>
  <div class="hero-grid">
    <div class="score-card">
      <div style="font-size:12px;color:#64748b;margin-bottom:8px;">综合评分</div>
      <div><span class="score-num">{score or "-"}</span> <span class="verdict">{html.escape(verdict)}</span></div>
      <p style="font-size:13px;line-height:1.8;color:#334155;margin:16px 0 0;">{html.escape(exec_summary.get("summary") or summary or "暂无摘要")}</p>
    </div>
    <div style="border:1px solid rgba(255,255,255,.18);border-radius:14px;padding:18px;color:#cbd5e1;font-size:12px;line-height:2;">
      <div>品牌：{html.escape(brand_name or "-")}</div>
      <div>结论：{html.escape(verdict)}</div>
      <div>数据结构：结论卡 / 指标卡 / 分模块分析</div>
    </div>
  </div>
</section>
<main>
  {warning_html}
  <div class="split">
    <section class="card adv"><h2>关键机会</h2><ol>{adv_html}</ol></section>
    <section class="card dis"><h2>主要风险</h2><ol>{dis_html}</ol></section>
  </div>
  {f'<section class="card"><h2>指标卡</h2><div class="metrics">{dim_html}</div></section>' if dim_html else ''}
  {f'<section class="card"><h2>落地行动清单</h2><ol>{action_html}</ol></section>' if action_html else ''}
  {f'{real_html}' if real_html else ''}
  <section class="card"><h2>分模块详细分析</h2>{detail_html}</section>
  <section class="footer">
    <div class="footer-copy">
      <strong style="color:#0f172a;font-size:14px;">址得选 AI 选址分析报告</strong><br>
      {html.escape(footer_text)}<br>
      本报告由系统自动生成，仅供商业决策参考，不构成投资建议。
    </div>
    <div>{qr_html}<div style="font-size:10px;text-align:center;color:#1d4ed8;font-weight:800;margin-top:7px;">扫码获取更多测算</div></div>
  </section>
</main>
</body>
</html>"""


def _upload_to_cloud(cfg: dict, filename: str, content: str) -> str:
    """上传到 OSS/S3 兼容存储，返回 URL"""
    import httpx
    endpoint = cfg.get("oss_endpoint", "").rstrip("/")
    bucket = cfg.get("oss_bucket", "")
    key_id = cfg.get("oss_access_key_id", "")
    key_secret = cfg.get("oss_access_key_secret", "")
    if not endpoint or not bucket:
        return ""
    # 简单 S3 兼容 PUT 上传
    url = f"{endpoint}/{bucket}/reports/{filename}"
    try:
        r = httpx.put(url, content=content.encode("utf-8"),
                       headers={"Content-Type": "text/html; charset=utf-8"},
                       auth=(key_id, key_secret), timeout=30)
        if r.status_code in (200, 201):
            return url
    except Exception:
        import traceback
        print(f"[CRITICAL] 云端 OSS 上传失败: {filename}", flush=True)
        traceback.print_exc()
    return ""


def _download_from_cloud(url: str) -> bytes:
    """从云端下载报告"""
    import httpx
    try:
        r = httpx.get(url, timeout=15)
        if r.status_code == 200:
            return r.content
    except Exception:
        import traceback
        print(f"[CRITICAL] 云端 OSS 下载失败: {url}", flush=True)
        traceback.print_exc()
    return b""
