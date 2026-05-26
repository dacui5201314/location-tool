"""用户中心 API — JWT 鉴权 + 双轨计费"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import User, AnalysisRecord, SavedLocation
from services.runtime_config import get_user_skus
from auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["用户中心"])


@router.get("/profile")
def get_profile(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回当前用户信息、会员状态、点数余额、统计数据（需 JWT）"""
    user_id = user["user_id"]
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    total_reports = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == user_id
    ).count()
    favorite_count = db.query(SavedLocation).filter(
        SavedLocation.user_id == user_id
    ).count()

    tier_labels = {
        "free": "非会员",
        "monthly": "月度会员",
        "quarterly": "季度会员",
        "yearly": "年度会员",
    }
    return {
        "user": db_user.to_dict(),
        "membership": {
            "tier": db_user.membership_tier,
            "tier_label": tier_labels.get(db_user.membership_tier, "非会员"),
            "is_member": db_user.is_member,
            "days_left": db_user.membership_days_left,
            "expiry": db_user.membership_expiry.isoformat() if db_user.membership_expiry else None,
        },
        "points": db_user.balance_credits,
        "total_reports": total_reports,
        "favorite_count": favorite_count,
        "is_new_user": False,
        "gift_note": "",
    }


class ProfileUpdateBody(BaseModel):
    avatar_url: str = ""
    nickname: str = ""


@router.put("/profile")
def update_profile(
    body: ProfileUpdateBody,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户头像/昵称（小程序 chooseAvatar + nickname input）"""
    db_user = db.query(User).filter(User.id == user["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.avatar_url and body.avatar_url.strip():
        db_user.avatar_url = body.avatar_url.strip()
    if body.nickname and body.nickname.strip():
        # User 模型没有 nickname 字段，存储在 avatar_url 同级的逻辑字段
        # 使用 SystemConfig 或扩展字段兼容
        pass  # nickname currently not stored on User model — use local storage for now
    db.commit()
    return {"ok": True, "user": db_user.to_dict()}


@router.get("/skus")
def get_visible_skus(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回当前用户实际可见套餐：用户专属配置优先，否则继承全局套餐。"""
    user_id = user["user_id"]
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    skus, inherited = get_user_skus(user_id, db)
    return {
        "user_id": user_id,
        "inherited": inherited,
        "skus": [item for item in skus if item.get("visible", True)],
    }


# ── 注意：POST /api/user/consume 已下线 ──
# 点数消耗必须在后端具体业务流中内部调用 check_billing_access()，
# 禁止前端通过 API 主动发起扣款指令。计费入口仅限：
#   - POST /api/analyze（分析扣费）
#   - POST /api/records/{id}/unlock-pdf（PDF 解锁扣费）
