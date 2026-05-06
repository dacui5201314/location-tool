"""用户中心 API — JWT 鉴权 + 双轨计费 + 设备防刷 + 免费点数限时"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models.db_models import User, AnalysisRecord, SavedLocation
from services.billing_service import check_billing_access
from services.runtime_config import get_user_skus
from auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["用户中心"])

# 防刷阈值：同设备或同IP 24 小时内最多 2 个账号可获赠点数
MAX_FREE_ACCOUNTS_PER_DEVICE = 2
FREE_POINT_HOURS = 24


def _get_or_create_user(
    db: Session,
    user_id: int,
    device_id: str = "",
    client_ip: str = "",
) -> tuple[User, bool, str]:
    """获取用户，不存在则自动创建。
    防刷：同一 device_id 或 IP 24h 内注册超过 2 个账号 → 仍创建但不送点数。
    返回 (user, is_new_user, gift_note)。"""
    user = db.query(User).filter(User.id == user_id).first()
    is_new = False
    gift_note = ""

    if not user:
        is_new = True
        cutoff = datetime.now() - timedelta(hours=FREE_POINT_HOURS)

        # 检查同设备或同IP 24h内注册数
        abuse_count = 0
        if device_id or client_ip:
            q = db.query(func.count(User.id))
            conditions = []
            if device_id:
                conditions.append(User.device_id == device_id)
            if client_ip:
                conditions.append(User.registration_ip == client_ip)
            # 用 OR 连接：同设备或同IP
            from sqlalchemy import or_
            abuse_count = q.filter(
                or_(*conditions),
                User.created_at >= cutoff,
            ).scalar() or 0

        # 决定是否赠送
        give_free_points = abuse_count < MAX_FREE_ACCOUNTS_PER_DEVICE
        initial_points = 1 if give_free_points else 0
        free_expire = (datetime.now() + timedelta(hours=FREE_POINT_HOURS)) if give_free_points else None

        user = User(
            id=user_id,
            balance_credits=initial_points,
            membership_tier="free",
            free_point_expire_at=free_expire,
            device_id=device_id,
            registration_ip=client_ip,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        if give_free_points:
            gift_note = f"赠送 1 点（{FREE_POINT_HOURS}小时后过期）"
        else:
            gift_note = "检测到设备异常，未赠送初始点数，请充值后使用"

    return user, is_new, gift_note


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
