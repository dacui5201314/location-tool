"""用户意见反馈 + 截图上传 + 1点奖励"""
import json, os, uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import User, Feedback, BillingRecord
from auth import get_current_user, get_current_admin

router = APIRouter(prefix="/api/feedback", tags=["反馈"])

FEEDBACK_ASSETS = Path(__file__).resolve().parent.parent / "storage" / "assets" / "feedback"
FEEDBACK_ASSETS.mkdir(parents=True, exist_ok=True)


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
    fpath = FEEDBACK_ASSETS / fname
    fpath.write_bytes(raw)
    return {"ok": True, "url": f"/assets/feedback/{fname}"}


@router.post("")
async def submit_feedback(
    content: str = Form(""),
    contact: str = Form(""),
    image_urls: str = Form(""),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    content = (content or "").strip()
    if len(content) < 10:
        raise HTTPException(status_code=400, detail="反馈内容至少10个字")
    if len(content) > 1000:
        raise HTTPException(status_code=400, detail="反馈内容不能超过1000字")

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

    # 每人每天限1次领积分
    today = datetime.now().date()
    today_start = datetime(today.year, today.month, today.day)
    existing = db.query(Feedback).filter(
        Feedback.user_id == user_id,
        Feedback.created_at >= today_start,
    ).first()
    already_granted = existing is not None

    fb = Feedback(
        user_id=user_id,
        content=content,
        contact=(contact or "").strip()[:120],
        image_urls=json.dumps(img_list, ensure_ascii=False),
        credits_granted=1 if not already_granted else 0,
    )
    db.add(fb)
    db.flush()

    if not already_granted:
        db_user.balance_credits += 1
        db.add(BillingRecord(
            user_id=user_id,
            amount=1,
            balance_after=db_user.balance_credits,
            record_type="BONUS",
            reason="意见反馈奖励 1点",
        ))

    db.commit()
    msg = "感谢反馈！已赠送 1 点分析额度" if not already_granted else "感谢反馈！今日已领取过奖励，明天再来。"
    return {"ok": True, "message": msg, "credits_granted": 1 if not already_granted else 0, "images": img_list}


@router.get("/admin/list")
def list_feedbacks(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows = db.query(Feedback, User).join(User, Feedback.user_id == User.id).order_by(
        Feedback.created_at.desc()
    ).limit(100).all()

    result = []
    for fb, u in rows:
        imgs = json.loads(fb.image_urls or "[]")
        result.append({
            "id": fb.id,
            "user_id": fb.user_id,
            "phone": u.phone or u.phone_number or "",
            "content": fb.content,
            "contact": fb.contact or "",
            "images": imgs,
            "credits_granted": fb.credits_granted,
            "created_at": fb.created_at.isoformat() if fb.created_at else None,
        })
    return {"feedbacks": result}
