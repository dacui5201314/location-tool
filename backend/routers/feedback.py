"""用户意见反馈、截图上传与运营回复"""
import json, uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import User, Feedback
from auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/feedback", tags=["反馈"])

FEEDBACK_ASSETS = Path(__file__).resolve().parent.parent / "storage" / "assets" / "feedback"
FEEDBACK_ASSETS.mkdir(parents=True, exist_ok=True)

FEEDBACK_COLUMN_MIGRATIONS = [
    ("image_urls", "TEXT DEFAULT '[]'"),
    ("credits_granted", "INTEGER DEFAULT 0"),
    ("report_uuid", "VARCHAR(64) DEFAULT ''"),
    ("report_title", "VARCHAR(200) DEFAULT ''"),
    ("report_address", "TEXT DEFAULT ''"),
    ("source", "VARCHAR(40) DEFAULT 'profile'"),
    ("status", "VARCHAR(20) DEFAULT 'pending'"),
    ("admin_reply", "TEXT DEFAULT ''"),
    ("replied_at", "DATETIME DEFAULT NULL"),
    ("updated_at", "DATETIME DEFAULT NULL"),
]


def _ensure_feedback_schema(db: Session):
    """接口级兜底迁移，避免线上旧库缺列导致反馈链路 500。"""
    rows = db.execute(text("PRAGMA table_info(feedbacks)")).fetchall()
    cols = {row[1] for row in rows}
    changed = False
    for col_name, col_def in FEEDBACK_COLUMN_MIGRATIONS:
        if col_name not in cols:
            db.execute(text(f"ALTER TABLE feedbacks ADD COLUMN {col_name} {col_def}"))
            cols.add(col_name)
            changed = True
    if changed:
        db.commit()


@router.post("/upload")
async def upload_feedback_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """单张反馈截图上传（微信小程序 uni.uploadFile 仅支持单文件）"""
    raw = await file.read()
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片不能超过2MB")
    ext = (file.filename or "").rsplit(".", 1)[-1].lower() or "jpg"
    if ext not in ("png", "jpg", "jpeg", "webp"):
        ext = "jpg"
    fname = f"fb_{uuid.uuid4().hex[:10]}.{ext}"
    from services.storage_service import save_user_asset_structured
    result = save_user_asset_structured("feedback", fname, raw, content_type=f"image/{ext}")
    if result.ok and result.url:
        return {"ok": True, "url": result.url}
    # 云失败回退本地 — 使用 result.local_path 对应的真实文件名
    from pathlib import Path
    real_name = Path(result.local_path).name if result.local_path else fname
    return {"ok": True, "url": f"/assets/feedback/{real_name}",
            "storage_error": result.error}


@router.post("")
async def submit_feedback(
    content: str = Form(""),
    contact: str = Form(""),
    image_urls: str = Form(""),
    report_uuid: str = Form(""),
    report_title: str = Form(""),
    report_address: str = Form(""),
    source: str = Form("profile"),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = (content or "").strip()
    if len(content) < 10:
        raise HTTPException(status_code=400, detail="反馈内容至少10个字")
    if len(content) > 1000:
        raise HTTPException(status_code=400, detail="反馈内容不能超过1000字")

    _ensure_feedback_schema(db)

    user_id = int(user["user_id"])
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 解析前端传入的已上传图片 URL 列表
    img_list = []
    try:
        img_list = json.loads(image_urls) if image_urls else []
    except (json.JSONDecodeError, TypeError):
        img_list = []

    if not isinstance(img_list, list):
        img_list = []
    safe_source = (source or "profile").strip()[:40] or "profile"
    if safe_source not in ("profile", "report_detail"):
        safe_source = "profile"

    fb = Feedback(
        user_id=user_id,
        content=content,
        contact=(contact or "").strip()[:120],
        image_urls=json.dumps(img_list, ensure_ascii=False),
        credits_granted=0,
        report_uuid=(report_uuid or "").strip()[:64],
        report_title=(report_title or "").strip()[:200],
        report_address=(report_address or "").strip()[:500],
        source=safe_source,
        status="pending",
        updated_at=datetime.utcnow(),
    )
    db.add(fb)
    db.commit()
    return {
        "ok": True,
        "message": "感谢反馈，我们会尽快处理。",
        "feedback_id": fb.id,
        "credits_granted": 0,
        "images": img_list,
    }


def _feedback_to_dict(fb: Feedback, user_obj: Optional[User] = None):
    try:
        imgs = json.loads(fb.image_urls or "[]")
    except (json.JSONDecodeError, TypeError):
        imgs = []
    if not isinstance(imgs, list):
        imgs = []
    return {
        "id": fb.id,
        "user_id": fb.user_id,
        "phone": (user_obj.phone or user_obj.phone_number or "") if user_obj else "",
        "content": fb.content,
        "contact": fb.contact or "",
        "images": imgs,
        "credits_granted": fb.credits_granted or 0,
        "report_uuid": fb.report_uuid or "",
        "report_title": fb.report_title or "",
        "report_address": fb.report_address or "",
        "source": fb.source or "profile",
        "status": fb.status or "pending",
        "admin_reply": fb.admin_reply or "",
        "replied_at": fb.replied_at.isoformat() if fb.replied_at else None,
        "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
    }


@router.get("/my")
def list_my_feedbacks(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _ensure_feedback_schema(db)
    user_id = int(user["user_id"])
    rows = db.query(Feedback).filter(Feedback.user_id == user_id).order_by(
        Feedback.created_at.desc()
    ).limit(100).all()
    return {"feedbacks": [_feedback_to_dict(fb) for fb in rows]}


@router.get("/admin/list")
def list_feedbacks(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _ensure_feedback_schema(db)
    rows = db.query(Feedback, User).join(User, Feedback.user_id == User.id).order_by(
        Feedback.created_at.desc()
    ).limit(100).all()

    result = []
    for fb, u in rows:
        result.append(_feedback_to_dict(fb, u))
    return {"feedbacks": result}


@router.post("/admin/{fb_id}/reply")
def reply_feedback(
    fb_id: int,
    payload: dict = Body(...),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _ensure_feedback_schema(db)
    reply = (payload.get("reply") or "").strip()
    if len(reply) < 2:
        raise HTTPException(status_code=400, detail="回复内容至少2个字")
    if len(reply) > 1000:
        raise HTTPException(status_code=400, detail="回复内容不能超过1000字")

    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="反馈不存在")
    now = datetime.utcnow()
    fb.admin_reply = reply
    fb.status = "replied"
    fb.replied_at = now
    fb.updated_at = now
    db.commit()
    return {"ok": True, "feedback": _feedback_to_dict(fb)}


@router.delete("/admin/{fb_id}")
def delete_feedback(
    fb_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    _ensure_feedback_schema(db)
    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="反馈不存在")
    db.delete(fb)
    db.commit()
    return {"ok": True}
