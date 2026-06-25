"""支付到账原子幂等：claim PAID + 发权益 + 流水 在同一事务。
只允许 CREATED / PROCESSING 状态被抢占，拒绝 REFUNDED/CANCELLED/CLOSED/FAILED。
"""
from datetime import datetime, timedelta
from sqlalchemy import update
from sqlalchemy.orm import Session
from models.db_models import PaymentOrder, User, BillingRecord


def claim_payment_order(db: Session, order: PaymentOrder) -> bool:
    """原子抢占支付订单 PAID 状态。只接受 CREATED 或 PROCESSING。
    返回 True 表示抢占成功（rowcount == 1）。调用方负责在同一事务中发权益。

    如果 rowcount == 0 且订单已是 PAID → 幂等（调用方应返回成功但不发权益）。
    如果 rowcount == 0 且订单是 REFUNDED/CANCELLED/CLOSED/FAILED → 拒绝。
    """
    result = db.execute(
        update(PaymentOrder)
        .where(
            PaymentOrder.id == order.id,
            PaymentOrder.status.in_(["CREATED", "PROCESSING"]),
        )
        .values(status="PAID", paid_at=datetime.now())
    )
    return result.rowcount == 1


def grant_payment_benefits(db: Session, order: PaymentOrder) -> None:
    """发放订单权益（点数 + 会员）。调用前必须先 claim_payment_order 成功。
    与 claim 在同一事务中，异常时由调用方 rollback。"""
    user_id = order.user_id
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise ValueError(f"用户不存在: {user_id}")

    channel = (order.pay_channel or "UNKNOWN")
    ch_prefix = "微信" if "JSAPI" in channel else "虚拟" if "VIRTUAL" in channel else "支付"

    if order.credits > 0:
        db_user.balance_credits += order.credits
        db.add(BillingRecord(
            user_id=user_id, amount=order.credits,
            balance_after=db_user.balance_credits,
            record_type="PURCHASE",
            reason=f"{ch_prefix}支付充值 {order.credits}点 ({order.out_trade_no})",
        ))

    if order.membership_days > 0:
        now = datetime.now()
        if db_user.membership_expiry and db_user.membership_expiry > now:
            db_user.membership_expiry += timedelta(days=order.membership_days)
        else:
            db_user.membership_expiry = now + timedelta(days=order.membership_days)
        db_user.membership_tier = (
            "monthly" if order.membership_days <= 90
            else "quarterly" if order.membership_days <= 180
            else "yearly"
        )
        db.add(BillingRecord(
            user_id=user_id, amount=0,
            balance_after=db_user.balance_credits,
            record_type="MEMBERSHIP",
            reason=f"{ch_prefix}支付开通会员 {order.membership_days}天 ({order.out_trade_no})",
        ))
