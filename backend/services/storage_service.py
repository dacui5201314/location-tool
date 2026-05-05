"""报告存储服务 — 本地文件 / 云端对象存储"""
import os
import json
import html
from datetime import datetime
from pathlib import Path
from database import SessionLocal
from models.db_models import SystemConfig

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
        rows = db_session.query(SystemConfig).filter(
            SystemConfig.key.like("storage_%")
        ).all()
        for r in rows:
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
    """生成标准分析报告 HTML 文件"""
    score = report_data.get("score", 0)
    summary = report_data.get("summary", "")
    advantages = report_data.get("advantages", [])
    disadvantages = report_data.get("disadvantages", [])
    warning = report_data.get("warning", "")
    details = report_data.get("details", {})

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
            detail_html += f'<div class="dim"><h4>{html.escape(str(label))}</h4><p>{html.escape(str(val))}</p></div>'

    adv_html = "".join(f"<li>{html.escape(str(a))}</li>" for a in advantages)
    dis_html = "".join(f"<li>{html.escape(str(d))}</li>" for d in disadvantages)
    warning_html = f'<div class="warning">⚠️ {html.escape(str(warning))}</div>' if warning else ""

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>选址分析报告 - {html.escape(brand_name or address)}</title>
<style>
  body {{ font-family: -apple-system, "Microsoft YaHei", sans-serif; max-width: 720px; margin: 0 auto; padding: 24px; color: #1e293b; background: #f8fafc; }}
  h1 {{ font-size: 20px; text-align: center; color: #0f172a; }}
  .meta {{ text-align: center; font-size: 12px; color: #94a3b8; margin-bottom: 20px; }}
  .score {{ text-align: center; margin: 16px 0; }}
  .score-num {{ font-size: 48px; font-weight: 900; color: {'#16a34a' if score >= 75 else '#ca8a04' if score >= 60 else '#dc2626'}; }}
  .card {{ background: #fff; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,.05); }}
  .card h3 {{ font-size: 14px; margin: 0 0 8px; }}
  .adv {{ border-left: 3px solid #16a34a; }}
  .dis {{ border-left: 3px solid #dc2626; }}
  .adv h3 {{ color: #16a34a; }}
  .dis h3 {{ color: #dc2626; }}
  .warning {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 10px; font-size: 13px; color: #991b1b; margin-bottom: 12px; }}
  .dim {{ background: #fff; border-radius: 8px; padding: 12px; margin-bottom: 8px; }}
  .dim h4 {{ font-size: 12px; color: #475569; margin: 0 0 4px; }}
  .dim p {{ font-size: 12px; color: #64748b; line-height: 1.6; margin: 0; white-space: pre-wrap; }}
  ul {{ margin: 0; padding-left: 18px; font-size: 13px; line-height: 1.8; color: #475569; }}
  .footer {{ text-align: center; font-size: 10px; color: #94a3b8; margin-top: 24px; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
</style>
</head>
<body>
<h1>选址分析报告</h1>
<div class="meta">地址：{html.escape(address)} | 品牌：{html.escape(brand_name)} | 报告编号：#{record_id}</div>
<div class="score"><div class="score-num">{score}</div><div style="font-size:12px;color:#94a3b8;">综合评分</div></div>
{warning_html}
<div class="card"><h3>分析摘要</h3><p style="font-size:13px;line-height:1.8;color:#475569;">{html.escape(summary)}</p></div>
<div class="card adv"><h3>✅ 优势</h3><ul>{adv_html}</ul></div>
<div class="card dis"><h3>⚠️ 劣势与风险</h3><ul>{dis_html}</ul></div>
<div style="margin-top:16px;"><h3 style="font-size:14px;">各维度详细分析</h3>{detail_html}</div>
<div class="footer">址得选 · AI选址分析决策平台 | 仅供参考，不构成投资建议</div>
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
        pass
    return ""


def _download_from_cloud(url: str) -> bytes:
    """从云端下载报告"""
    import httpx
    try:
        r = httpx.get(url, timeout=15)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return b""
