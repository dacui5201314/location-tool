"""分析记录 API — 全接口 JWT 鉴权 + UUID 防遍历"""
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


@router.get("")
def list_records(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取当前用户的分析记录列表（返回 report_uuid 供后续操作）"""
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


def _get_record_by_uuid(report_uuid: str, user_id: int, db: Session) -> AnalysisRecord | None:
    """通过 report_uuid 获取记录，同时校验归属用户"""
    if not report_uuid or len(report_uuid) != 32:
        return None
    return db.query(AnalysisRecord).filter(
        AnalysisRecord.report_uuid == report_uuid,
        AnalysisRecord.user_id == user_id,
    ).first()


@router.get("/{report_uuid}")
def get_record(
    report_uuid: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条分析记录详情（含完整报告JSON）— 通过 UUID 访问"""
    user_id = user["user_id"]
    record = _get_record_by_uuid(report_uuid, user_id, db)
    if not record:
        return {"error": "记录不存在"}
    data = record.to_dict()
    data["report_json"] = record.report_json
    data["report_file"] = record.report_file
    data["report_url"] = record.report_url
    return data


@router.post("/{report_uuid}/share-token")
def create_share_token(
    report_uuid: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """为报告生成或获取分享令牌。仅 owner 可操作。"""
    import secrets

    user_id = user["user_id"]
    record = _get_record_by_uuid(report_uuid, user_id, db)
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    if record.share_token:
        return {"share_token": record.share_token, "is_new": False}

    # 生成唯一随机 token
    for _ in range(5):
        token = secrets.token_urlsafe(24)  # 32 chars
        exists = db.query(AnalysisRecord).filter(
            AnalysisRecord.share_token == token
        ).first()
        if not exists:
            break
    else:
        raise HTTPException(status_code=500, detail="生成分享令牌失败，请重试")

    record.share_token = token
    db.commit()
    return {"share_token": token, "is_new": True}


@router.delete("/{report_uuid}")
def delete_record(
    report_uuid: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除分析记录 — 通过 UUID 访问"""
    user_id = user["user_id"]
    record = _get_record_by_uuid(report_uuid, user_id, db)
    if not record:
        return {"error": "记录不存在"}
    record_id = record.id
    db.delete(record)
    db.commit()
    return {"ok": True, "deleted_uuid": report_uuid}


@router.post("/{report_uuid}/unlock-pdf")
def unlock_pdf(
    report_uuid: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """消耗1个点数解锁PDF导出权限 — 通过 UUID 访问"""
    user_id = user["user_id"]
    record = _get_record_by_uuid(report_uuid, user_id, db)
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

    # ★ Phase 13: 原子化并发安全
    # check_billing_access 已执行 UPDATE（未 commit，与下方共享同一 db session 事务）。
    # 若下方 rowcount==0，说明并发请求已抢先解锁。db.rollback() 会回滚整个事务，
    # 包括 check_billing_access 的计费 UPDATE → 用户不会被扣点。
    # 会员用户同样在 rollback 中撤销；无需额外 refund_credits（避免双倍退款）。
    result = db.execute(
        update(AnalysisRecord)
        .where(AnalysisRecord.id == record.id, AnalysisRecord.is_pdf_unlocked == 0)
        .values(is_pdf_unlocked=1)
    )
    if result.rowcount == 0:
        db.rollback()
        print(f"[PDF Guard] 并发解锁已处理: user_id={user_id} record={record.id} — 计费已回滚", flush=True)
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


@router.get("/{report_uuid}/download")
def download_report_file(
    report_uuid: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """动态获取报告 HTML — 优先用 report_json 重建，防止旧 HTML 输出过期口径"""
    user_id = user["user_id"]
    record = _get_record_by_uuid(report_uuid, user_id, db)
    if not record:
        return HTMLResponse(content="<h2>记录不存在</h2>", status_code=404)

    content = None
    if record.report_json:
        import json
        from services.storage_service import _build_report_html
        try:
            data = json.loads(record.report_json)
            # ★ 存在 report_json 时优先动态重建，确保 rigor 等新口径生效
            html = _build_report_html(record.id, data, record.address, record.brand_desc)
            content = html.encode("utf-8")
        except Exception:
            pass

    if not content:
        content = get_report_content(
            record.id,
            report_file=record.report_file,
            report_url=record.report_url,
        )

    if content:
        return HTMLResponse(content=content, status_code=200)
    return HTMLResponse(content="<h2>报告文件不存在</h2>", status_code=404)
