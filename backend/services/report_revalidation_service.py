"""
存量报告重新校验服务 — 分级识别，不删除旧报告。
dry-run 不写库；run 只更新 report_json 内部 meta 字段。
"""
import json as _json
from datetime import datetime

_CURRENT_SCHEMA_VERSION = "2026-06-report-quality-v1"


def classify_legacy_report_status(report_json: dict, report_file: str = "",
                                   report_url: str = "", real_data: dict | None = None) -> dict:
    """分类旧报告状态。_fact_guard_status 决定最终状态，不因 schema_version 抹平失败。"""
    rpt = report_json or {}
    prev_fg_status = rpt.get("_fact_guard_status", "")
    prev_legacy_status = rpt.get("_legacy_report_status", "")
    has_real_data = bool(real_data)

    result = {
        "status": "legacy_unchecked",
        "fact_guard_status": "",
        "storage_sync_status": "local_only" if report_file else "unknown",
        "legacy_notice": rpt.get("_legacy_report_notice", ""),
        "hard_errors": [],
        "warnings": [],
        "should_update": False,
        "updates": {},
    }

    # ── 存储状态 ──
    if report_url:
        result["storage_sync_status"] = "synced"
    elif report_file:
        result["storage_sync_status"] = "pending"

    # ── 有 schema_version 但无 _fact_guard_status → 新版未校验，标记 current_ok ──
    schema_ver = rpt.get("_report_schema_version", "")
    if schema_ver and not prev_fg_status and not prev_legacy_status:
        result["status"] = "current_ok"
        result["fact_guard_status"] = "passed"
        return result

    # ── 已有历史校验结果 → 保留原状态 ──
    if prev_fg_status == "failed" or prev_legacy_status == "legacy_failed_fact_guard":
        result["status"] = "legacy_failed_fact_guard"
        result["fact_guard_status"] = "failed"
        result["legacy_notice"] = rpt.get("_legacy_report_notice") or "该报告由旧版本生成，部分数据口径需重新校验，建议重新生成"
        result["hard_errors"] = rpt.get("_fact_guard_errors", [])[:5]
        result["warnings"] = rpt.get("_fact_guard_warnings", [])[:5]
        return result

    if prev_fg_status == "unchecked" or prev_legacy_status == "legacy_unchecked":
        result["status"] = "legacy_unchecked"
        result["fact_guard_status"] = "unchecked"
        result["legacy_notice"] = rpt.get("_legacy_report_notice") or "缺少原始事实数据，建议重新生成"
        return result

    if prev_fg_status in ("passed", "passed_with_warnings") or prev_legacy_status == "legacy_warning":
        result["status"] = "legacy_warning"
        result["fact_guard_status"] = prev_fg_status
        result["legacy_notice"] = rpt.get("_legacy_report_notice") or "历史版本，可重新生成新版报告"
        return result

    # ── 首次校验：无历史状态 ──
    if not has_real_data:
        result["status"] = "legacy_unchecked"
        result["fact_guard_status"] = "unchecked"
        result["legacy_notice"] = "缺少原始事实数据，建议重新生成"
        result["warnings"].append("no_real_data_for_revalidation")
        result["should_update"] = True
        result["updates"] = {
            "_report_schema_version": _CURRENT_SCHEMA_VERSION,
            "_fact_guard_status": "unchecked",
            "_legacy_report_status": "legacy_unchecked",
            "_storage_sync_status": result["storage_sync_status"],
            "_last_revalidated_at": datetime.now().isoformat(),
            "_legacy_report_notice": result["legacy_notice"],
        }
        return result

    # ── 首次校验：有 real_data → 跑 fact guard ──
    try:
        from report_fact_guard import validate_report_fact_consistency, split_final_guard_issues
        issues = validate_report_fact_consistency(rpt, real_data)
        hard, warnings = split_final_guard_issues(issues)

        result["hard_errors"] = hard
        result["warnings"] = result["warnings"] + warnings
        result["should_update"] = True
        result["updates"] = {
            "_report_schema_version": _CURRENT_SCHEMA_VERSION,
            "_last_revalidated_at": datetime.now().isoformat(),
            "_storage_sync_status": result["storage_sync_status"],
            "_fact_guard_errors": hard[:5],
            "_fact_guard_warnings": warnings[:5],
        }

        if hard:
            result["status"] = "legacy_failed_fact_guard"
            result["fact_guard_status"] = "failed"
            result["legacy_notice"] = "该报告由旧版本生成，部分数据口径需重新校验，建议重新生成"
            result["updates"]["_fact_guard_status"] = "failed"
            result["updates"]["_legacy_report_status"] = "legacy_failed_fact_guard"
            result["updates"]["_legacy_report_notice"] = result["legacy_notice"]
        else:
            result["status"] = "legacy_warning"
            result["fact_guard_status"] = "passed" if not warnings else "passed_with_warnings"
            result["legacy_notice"] = "历史版本，可重新生成新版报告"
            result["updates"]["_fact_guard_status"] = result["fact_guard_status"]
            result["updates"]["_legacy_report_status"] = "legacy_warning"
            result["updates"]["_legacy_report_notice"] = result["legacy_notice"]
    except Exception as e:
        result["status"] = "legacy_unchecked"
        result["fact_guard_status"] = "unchecked"
        result["warnings"].append(f"revalidation_error: {e}")
        result["should_update"] = True
        result["updates"] = {
            "_report_schema_version": _CURRENT_SCHEMA_VERSION,
            "_fact_guard_status": "unchecked",
            "_legacy_report_status": "legacy_unchecked",
            "_storage_sync_status": result["storage_sync_status"],
            "_last_revalidated_at": datetime.now().isoformat(),
            "_legacy_report_notice": result["legacy_notice"] or "缺少原始事实数据，建议重新生成",
        }

    return result


def revalidate_report_record(report, dry_run: bool = True) -> dict:
    """校验单条 AnalysisRecord。report 为 DB 对象（需有 report_json, report_file, report_url）。"""
    try:
        rpt = _json.loads(report.report_json or "{}")
    except Exception:
        rpt = {}

    result = classify_legacy_report_status(
        rpt,
        report_file=getattr(report, "report_file", "") or "",
        report_url=getattr(report, "report_url", "") or "",
        real_data=rpt.get("real_data"),
    )
    result["report_id"] = getattr(report, "id", None)

    if not dry_run and result.get("should_update") and result.get("updates"):
        updates = result["updates"]
        for k, v in updates.items():
            rpt[k] = v
        report.report_json = _json.dumps(rpt, ensure_ascii=False)

    return result


def scan_legacy_reports(db, dry_run: bool = True, limit: int = 100) -> dict:
    """批量扫描旧报告。返回 summary + samples。"""
    from models.db_models import AnalysisRecord

    records = db.query(AnalysisRecord).order_by(AnalysisRecord.id.desc()).limit(limit).all()

    summary = {
        "total_scanned": len(records),
        "current_ok": 0, "legacy_warning": 0, "legacy_failed_fact_guard": 0,
        "legacy_unchecked": 0, "storage_pending": 0, "storage_synced": 0,
    }
    samples = []

    for rec in records:
        r = revalidate_report_record(rec, dry_run=dry_run)
        status = r.get("status", "legacy_unchecked")
        if status in summary:
            summary[status] += 1
        if r.get("storage_sync_status") == "synced":
            summary["storage_synced"] += 1
        elif r.get("storage_sync_status") == "pending":
            summary["storage_pending"] += 1
        if len(samples) < 5:
            samples.append({"id": r.get("report_id"), "status": r.get("status"),
                            "hard_errors": r.get("hard_errors", [])[:2],
                            "legacy_notice": r.get("legacy_notice", "")})

    if not dry_run:
        db.commit()

    return {"ok": True, "dry_run": dry_run, "summary": summary, "samples": samples}
