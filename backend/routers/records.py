"""分析记录 API — 全接口 JWT 鉴权"""
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, update
from database import get_db
from models.db_models import AnalysisRecord, User
from services.storage_service import get_report_content
from services.billing_service import check_billing_access
from auth import get_current_user

router = APIRouter(prefix="/api/records", tags=["分析记录"])


def _get_user_id(user: dict = Depends(get_current_user)) -> int:
    return user["user_id"]


@router.get("")
def list_records(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取当前用户的分析记录列表，按时间倒序"""
    user_id = user["user_id"]
    query = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == user_id
    ).order_by(desc(AnalysisRecord.created_at))

    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "records": [r.to_dict() for r in records],
    }


@router.get("/{record_id}")
def get_record(
    record_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条分析记录详情（含完整报告JSON）"""
    user_id = user["user_id"]
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id,
        AnalysisRecord.user_id == user_id,
    ).first()
    if not record:
        return {"error": "记录不存在"}
    data = record.to_dict()
    data["report_json"] = record.report_json
    data["report_file"] = record.report_file
    data["report_url"] = record.report_url
    return data


@router.delete("/{record_id}")
def delete_record(
    record_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除分析记录"""
    user_id = user["user_id"]
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id,
        AnalysisRecord.user_id == user_id,
    ).first()
    if not record:
        return {"error": "记录不存在"}
    db.delete(record)
    db.commit()
    return {"ok": True, "deleted_id": record_id}


@router.post("/{record_id}/unlock-pdf")
def unlock_pdf(
    record_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """消耗1个点数解锁PDF导出权限"""
    user_id = user["user_id"]
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id,
        AnalysisRecord.user_id == user_id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")
    if record.is_pdf_unlocked:
        return {"ok": True, "already_unlocked": True, "message": "PDF 已解锁，无需重复扣费"}

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    billing = check_billing_access(db_user, cost=1, db_session=db)
    if not billing.allowed:
        raise HTTPException(status_code=402, detail=billing.reason)

    # 原子化更新 is_pdf_unlocked，防止并发双扣
    result = db.execute(
        update(AnalysisRecord)
        .where(AnalysisRecord.id == record_id, AnalysisRecord.is_pdf_unlocked == 0)
        .values(is_pdf_unlocked=1)
    )
    if result.rowcount == 0:
        db.rollback()
        return {"ok": True, "already_unlocked": True, "message": "PDF 已被其他请求解锁，无需重复扣费"}

    db.commit()

    return {
        "ok": True,
        "source": billing.source,
        "balance_credits": billing.points_after,
        "is_pdf_unlocked": True,
        "is_member": db_user.is_member,
        "membership_days_left": db_user.membership_days_left,
        "message": "会员免费解锁" if billing.source == "member" else f"PDF 导出权限已解锁，本次消耗 1 个分析点数",
    }


@router.get("/{record_id}/download")
def download_report_file(
    record_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """动态获取报告文件内容（根据存储模式自动路由 本地/云端）"""
    user_id = user["user_id"]
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == record_id,
        AnalysisRecord.user_id == user_id,
    ).first()
    if not record:
        return HTMLResponse(content="<h2>记录不存在</h2>", status_code=404)

    content = get_report_content(
        record.id,
        report_file=record.report_file,
        report_url=record.report_url,
    )
    if not content and record.report_json:
        import json
        from services.storage_service import _build_report_html
        try:
            data = json.loads(record.report_json)
            html = _build_report_html(record.id, data, record.address, record.brand_desc)
            content = html.encode("utf-8")
        except Exception:
            pass

    if content:
        return HTMLResponse(content=content, status_code=200)
    return HTMLResponse(content="<h2>报告文件不存在</h2>", status_code=404)
