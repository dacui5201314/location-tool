"""统一计费校验 — 会员订阅 / 点数余额双轨 + 免费点数限时过期
Security: 使用原子化 SQL UPDATE 消除 TOCTOU 竞态条件。
点数额度 UPDATE 的 WHERE 条件同时校验 free_point_expire_at，防止临界点并发漏洞：
  - 免费点数未过期 → 全额可用
  - 免费点数已过期 → 仅已购点数可用（balance - 1）
"""

from datetime import datetime
from sqlalchemy import update, or_
from models.db_models import User


class BillingResult:
    def __init__(self, allowed: bool, reason: str = "", source: str = "",
                 points_before: int = 0, points_after: int = 0):
        self.allowed = allowed
        self.reason = reason
        self.source = source       # "member" / "points" / "blocked"
        self.points_before = points_before
        self.points_after = points_after

    def to_dict(self):
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "source": self.source,
            "points_before": self.points_before,
            "points_after": self.points_after,
        }


def check_billing_access(user: User, cost: int = 1, db_session=None) -> BillingResult:
    """
    统一计费校验，按优先级执行：

    1. 会员优先：membership_expiry 有效期内 → 直接放行，不扣点数
    2. 点数抵扣（含免费点数过期判定）：
       a. 会员过期 + 有效点数 >= cost → 原子化 UPDATE 扣除
       b. 免费点数已过期 + 余额仅为赠送的 1 点 → 拦截
       c. 免费点数已过期 + 用户已充值（余额 > 1）→ 使用已购点数
    3. 拦截：点数不足 → 返回原因

    调用方负责 db_session.commit()。
    Security: 点数扣除使用 UPDATE ... WHERE balance_credits >= cost 原子操作。
    """
    # 第一优先级：会员
    if user.is_member:
        return BillingResult(
            allowed=True,
            reason=f"会员有效（{user.membership_days_left}天后到期），本次免费",
            source="member",
            points_before=user.balance_credits,
            points_after=user.balance_credits,
        )

    # 计算有效点数
    effective = user.balance_credits
    free_expired = False
    if user.free_point_expire_at is not None and not user.free_point_active:
        effective = max(0, user.balance_credits - 1)
        free_expired = True

    if effective < cost:
        if free_expired and user.balance_credits > 0:
            return BillingResult(
                allowed=False,
                reason="您的免费赠送点数已过期（注册后24小时有效），请充值后继续使用",
                source="blocked",
                points_before=user.balance_credits,
                points_after=user.balance_credits,
            )
        return BillingResult(
            allowed=False,
            reason="点数不足且会员已过期，请充值或续费会员",
            source="blocked",
            points_before=user.balance_credits,
            points_after=user.balance_credits,
        )

    # ★ 原子化扣除：消除 TOCTOU 竞态条件 + 免费点数过期原子判定
    # WHERE 条件同时校验：
    #   1. balance_credits >= cost（点数余额充足）
    #   2. 免费点数未过期 OR 无免费点数 OR 已购点数足够
    # 防止：Python 层判定通过后，免费点数在 SQL 执行前瞬间过期导致超扣
    before = user.balance_credits
    result = db_session.execute(
        update(User)
        .where(
            User.id == user.id,
            User.balance_credits >= cost,
            or_(
                User.free_point_expire_at == None,
                User.free_point_expire_at > datetime.now(),
                User.balance_credits - 1 >= cost,
            ),
        )
        .values(balance_credits=User.balance_credits - cost)
    )

    if result.rowcount == 0:
        # 并发冲突：余额在检查和扣款之间被其他请求消耗
        return BillingResult(
            allowed=False,
            reason="操作冲突，请重试",
            source="blocked",
            points_before=before,
            points_after=before,
        )

    # 刷新 ORM 对象以反映数据库最新状态
    db_session.refresh(user)

    return BillingResult(
        allowed=True,
        reason=f"已消耗 {cost} 个分析点数",
        source="points",
        points_before=before,
        points_after=user.balance_credits,
    )


def refund_credits(user_id: int, amount: int = 1):
    """原子化退还点数 — LLM/JSON解析异常时的资损兜底回滚"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance_credits=User.balance_credits + amount)
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
