"""P1-A: Virtual pay refund/cancel guard — 未发放权益不得误扣余额/会员。

测试结构：
  Unit (T1-T7): 底层 helper 级断言（保留）
  Integration (T8-T14): 真实通知分支 — 全部穿过 _handle_refund_cancel_notify（virtual_notify 实际调用的分支入口）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

# ── 临时 SQLite 内存库 ──
engine = create_engine("sqlite://", echo=False)

@event.listens_for(engine, "connect")
def _set_pragma(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA journal_mode=WAL;")

SessionLocal = sessionmaker(bind=engine)

# 建表
from database import Base
from models.db_models import PaymentOrder, User, BillingRecord, SystemConfig
Base.metadata.create_all(bind=engine)

from routers.virtual_pay import (
    _order_has_granted_benefits, _revoke_order, _grant_order,
    _mark_order_refunded_no_revoke,
    _handle_refund_cancel_notify,   # ★ 真实通知分支入口
)

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _make_user(db, user_id=1, credits=50, mini_openid=None):
    if mini_openid is None:
        mini_openid = f"oTest{user_id:04d}"
    existing = db.query(User).filter(User.id == user_id).first()
    if existing:
        return existing
    user = User(id=user_id, balance_credits=credits, membership_tier="free",
                wx_mini_openid=mini_openid,
                membership_expiry=datetime.now() + timedelta(days=30))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_order(db, out_trade_no, status="CREATED", credits=10, days=0,
                user_id=1, amount_fen=1000, pay_channel="WECHAT_VIRTUAL"):
    order = PaymentOrder(out_trade_no=out_trade_no, user_id=user_id, sku_id=1,
                         credits=credits, membership_days=days,
                         amount_fen=amount_fen, status=status,
                         pay_channel=pay_channel,
                         created_at=datetime.now() - timedelta(minutes=5))
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _add_purchase_record(db, order, credits=10):
    """手动写入 PURCHASE 账本记录，模拟已发放权益"""
    user = db.query(User).filter(User.id == order.user_id).first()
    record = BillingRecord(
        user_id=order.user_id,
        amount=credits,
        balance_after=(user.balance_credits if user else 0),
        record_type="PURCHASE",
        reason=f"虚拟支付充值 {credits}点 ({order.out_trade_no})",
    )
    db.add(record)
    db.commit()
    return record


# ═══════════════════════════════════════════════════════════════
# 第一段：Unit — Helper 级断言（保留）
# ═══════════════════════════════════════════════════════════════

print("=== UNIT T1: CREATED → _order_has_granted_benefits=False ===")
db = SessionLocal()
user = _make_user(db, user_id=1, credits=100)
order = _make_order(db, "TEST_UNIT_001", status="CREATED", credits=10, user_id=1)
check(not _order_has_granted_benefits(db, order), "no benefits for CREATED without records")
db.rollback()
print("T1 PASS")

print("=== UNIT T2: PAID → _order_has_granted_benefits=True ===")
db2 = SessionLocal()
user2 = _make_user(db2, user_id=2, credits=100)
order2 = _make_order(db2, "TEST_UNIT_002", status="PAID", credits=10, user_id=2)
check(_order_has_granted_benefits(db2, order2), "has benefits for PAID")
db2.rollback()
print("T2 PASS")

print("=== UNIT T3: PROCESSING + PURCHASE record → has benefits ===")
db3 = SessionLocal()
user3 = _make_user(db3, user_id=3, credits=100)
order3 = _make_order(db3, "TEST_UNIT_003", status="PROCESSING", credits=10, user_id=3)
_add_purchase_record(db3, order3, credits=10)
db3.refresh(order3)
check(_order_has_granted_benefits(db3, order3), "has benefits with PURCHASE record")
db3.rollback()
print("T3 PASS")

print("=== UNIT T4: other order PURCHASE → no benefits for this order ===")
db4 = SessionLocal()
user4 = _make_user(db4, user_id=4, credits=100)
order4a = _make_order(db4, "TEST_UNIT_004A", status="PAID", credits=10, user_id=4)
_add_purchase_record(db4, order4a, credits=10)
order4b = _make_order(db4, "TEST_UNIT_004B", status="CREATED", credits=10, user_id=4)
check(_order_has_granted_benefits(db4, order4a), "order A has benefits")
check(not _order_has_granted_benefits(db4, order4b),
      "order B does NOT have benefits (other order's PURCHASE not matched)")
db4.rollback()
print("T4 PASS")


# ═══════════════════════════════════════════════════════════════
# 第二段：Integration — 真实通知分支（全部穿过 _handle_refund_cancel_notify）
# ═══════════════════════════════════════════════════════════════

# ── T5: CREATED + refund notify → ErrCode 0, REFUNDED, 余额不变, 无负向账本 ──
print("=== T5: CREATED + refund notify (via _handle_refund_cancel_notify) ===")
db5 = SessionLocal()
user5 = _make_user(db5, user_id=5, credits=100)
order5 = _make_order(db5, "TEST_BRANCH_REFUND_CREATED", status="CREATED", credits=10, user_id=5)

pre_balance5 = user5.balance_credits
result5 = _handle_refund_cancel_notify(db5, order5, user5, is_refund=True, is_cancel=False)
db5.refresh(order5)
db5.refresh(user5)

check(result5["ErrCode"] == 0, f"ErrCode=0: got {result5['ErrCode']}")
check(order5.status == "REFUNDED", f"status=REFUNDED: got {order5.status}")
check(user5.balance_credits == pre_balance5,
      f"balance unchanged: {user5.balance_credits} == {pre_balance5}")
refund5 = db5.query(BillingRecord).filter(
    BillingRecord.user_id == 5,
    BillingRecord.record_type.in_(["REFUND", "REFUND_SHORTFALL"]),
).all()
check(len(refund5) == 0, f"no REFUND/REFUND_SHORTFALL records: got {len(refund5)}")
db5.rollback()
print("T5 PASS")


# ── T6: PROCESSING + refund notify → ErrCode 0, REFUNDED, 余额不变 ──
print("=== T6: PROCESSING + refund notify (via _handle_refund_cancel_notify) ===")
db6 = SessionLocal()
user6 = _make_user(db6, user_id=6, credits=100)
order6 = _make_order(db6, "TEST_BRANCH_REFUND_PROCESSING", status="PROCESSING", credits=10, user_id=6)

pre_balance6 = user6.balance_credits
result6 = _handle_refund_cancel_notify(db6, order6, user6, is_refund=True, is_cancel=False)
db6.refresh(order6)
db6.refresh(user6)

check(result6["ErrCode"] == 0, f"ErrCode=0: got {result6['ErrCode']}")
check(order6.status == "REFUNDED", f"status=REFUNDED: got {order6.status}")
check(user6.balance_credits == pre_balance6, "balance unchanged")
refund6 = db6.query(BillingRecord).filter(
    BillingRecord.user_id == 6,
    BillingRecord.record_type.in_(["REFUND", "REFUND_SHORTFALL"]),
).all()
check(len(refund6) == 0, f"no REFUND/REFUND_SHORTFALL records: got {len(refund6)}")
db6.rollback()
print("T6 PASS")


# ── T7: PAID + refund notify → ErrCode 0, 正常扣回, 重复幂等 ──
print("=== T7: PAID + refund notify (via _handle_refund_cancel_notify) ===")
db7 = SessionLocal()
user7 = _make_user(db7, user_id=7, credits=100)
order7 = _make_order(db7, "TEST_BRANCH_REFUND_PAID", status="PAID", credits=10, user_id=7, days=30)

pre_balance7 = user7.balance_credits
result7 = _handle_refund_cancel_notify(db7, order7, user7, is_refund=True, is_cancel=False)
db7.refresh(order7)
db7.refresh(user7)

check(result7["ErrCode"] == 0, f"ErrCode=0: got {result7['ErrCode']}")
check(order7.status == "REFUNDED", f"status=REFUNDED: got {order7.status}")
check(user7.balance_credits == pre_balance7 - 10,
      f"credits deducted: {user7.balance_credits} == {pre_balance7 - 10}")

refund7a = db7.query(BillingRecord).filter(
    BillingRecord.user_id == 7,
    BillingRecord.record_type == "REFUND",
    BillingRecord.reason.contains(order7.out_trade_no),
).first()
check(refund7a is not None, "REFUND billing record exists")
check(refund7a.amount < 0, f"REFUND amount negative: {refund7a.amount}")

# 重复 notify → 幂等
refund_count_before = db7.query(BillingRecord).filter(
    BillingRecord.user_id == 7, BillingRecord.record_type == "REFUND",
).count()
balance_before_repeat = user7.balance_credits
result7b = _handle_refund_cancel_notify(db7, order7, user7, is_refund=True, is_cancel=False)
db7.refresh(user7)
check(result7b["ErrCode"] == 0, f"repeat ErrCode=0: got {result7b['ErrCode']}")
check(user7.balance_credits == balance_before_repeat,
      f"idempotent: credits unchanged after repeat: {user7.balance_credits}")
refund_count_after = db7.query(BillingRecord).filter(
    BillingRecord.user_id == 7, BillingRecord.record_type == "REFUND",
).count()
check(refund_count_after == refund_count_before,
      f"idempotent: REFUND count unchanged: {refund_count_after} == {refund_count_before}")
db7.rollback()
print("T7 PASS")


# ── T8: PROCESSING + 本订单 PURCHASE 账本 + refund → 允许扣回 ──
print("=== T8: PROCESSING + PURCHASE + refund notify (via _handle_refund_cancel_notify) ===")
db8 = SessionLocal()
user8 = _make_user(db8, user_id=8, credits=100)
order8 = _make_order(db8, "TEST_BRANCH_REFUND_PURCHASE", status="PROCESSING", credits=10, user_id=8)
_add_purchase_record(db8, order8, credits=10)
db8.refresh(order8)

check(order8.status == "PROCESSING", "status still PROCESSING before notify")
pre_balance8 = user8.balance_credits

result8 = _handle_refund_cancel_notify(db8, order8, user8, is_refund=True, is_cancel=False)
db8.refresh(order8)
db8.refresh(user8)

check(result8["ErrCode"] == 0, f"ErrCode=0: got {result8['ErrCode']}")
check(order8.status == "REFUNDED", f"status=REFUNDED: got {order8.status}")
check(user8.balance_credits == pre_balance8 - 10,
      f"credits deducted: {user8.balance_credits} == {pre_balance8 - 10}")
db8.rollback()
print("T8 PASS")


# ── T9: 同用户其他订单 PURCHASE + 当前订单 refund → 不误扣, 只 REFUNDED ──
print("=== T9: other-order PURCHASE + refund → no revoke (via _handle_refund_cancel_notify) ===")
db9 = SessionLocal()
user9 = _make_user(db9, user_id=9, credits=100)
order9_other = _make_order(db9, "TEST_BRANCH_OTHER_A", status="PAID", credits=10, user_id=9)
_add_purchase_record(db9, order9_other, credits=10)
order9_this = _make_order(db9, "TEST_BRANCH_OTHER_B", status="CREATED", credits=10, user_id=9)

pre_balance9 = user9.balance_credits
result9 = _handle_refund_cancel_notify(db9, order9_this, user9, is_refund=True, is_cancel=False)
db9.refresh(order9_this)
db9.refresh(user9)

check(result9["ErrCode"] == 0, f"ErrCode=0: got {result9['ErrCode']}")
check(order9_this.status == "REFUNDED", f"status=REFUNDED: got {order9_this.status}")
check(user9.balance_credits == pre_balance9, f"balance unchanged: {user9.balance_credits} == {pre_balance9}")

refund9 = db9.query(BillingRecord).filter(
    BillingRecord.user_id == 9,
    BillingRecord.record_type.in_(["REFUND", "REFUND_SHORTFALL"]),
    BillingRecord.reason.contains(order9_this.out_trade_no),
).all()
check(len(refund9) == 0, f"no REFUND records for this order: got {len(refund9)}")
db9.rollback()
print("T9 PASS")


# ── T10: CREATED + cancel notify → ErrCode 0, CANCELLED, 余额/会员不变, 无负向账本 ──
print("=== T10: CREATED + cancel notify (via _handle_refund_cancel_notify) ===")
db10 = SessionLocal()
user10 = _make_user(db10, user_id=10, credits=100)
order10 = _make_order(db10, "TEST_BRANCH_CANCEL_CREATED", status="CREATED", credits=10, user_id=10, days=30)

pre_balance10 = user10.balance_credits
pre_membership10 = user10.membership_expiry
result10 = _handle_refund_cancel_notify(db10, order10, user10, is_refund=False, is_cancel=True)
db10.refresh(order10)
db10.refresh(user10)

check(result10["ErrCode"] == 0, f"ErrCode=0: got {result10['ErrCode']}")
check(order10.status == "CANCELLED", f"status=CANCELLED: got {order10.status}")
check(user10.balance_credits == pre_balance10, "credits unchanged")
check(user10.membership_expiry == pre_membership10, "membership unchanged")

cancel_refund10 = db10.query(BillingRecord).filter(
    BillingRecord.user_id == 10,
    BillingRecord.record_type.in_(["REFUND", "REFUND_SHORTFALL"]),
).all()
check(len(cancel_refund10) == 0, f"no REFUND/REFUND_SHORTFALL from cancel: got {len(cancel_refund10)}")
db10.rollback()
print("T10 PASS")


# ── T11: PAID + cancel notify → ErrCode 1, 状态保持 PAID, 余额/会员不变 ──
print("=== T11: PAID + cancel notify → rejected (via _handle_refund_cancel_notify) ===")
db11 = SessionLocal()
user11 = _make_user(db11, user_id=11, credits=100)
order11 = _make_order(db11, "TEST_BRANCH_CANCEL_PAID", status="PAID", credits=10, user_id=11, days=30)

pre_status11 = order11.status
pre_balance11 = user11.balance_credits
pre_membership11 = user11.membership_expiry

result11 = _handle_refund_cancel_notify(db11, order11, user11, is_refund=False, is_cancel=True)
db11.refresh(order11)
db11.refresh(user11)

check(result11["ErrCode"] == 1, f"ErrCode=1 (rejected): got {result11['ErrCode']}")
check("refund" in result11.get("ErrMsg", "").lower(),
      f"ErrMsg mentions refund: {result11.get('ErrMsg', '')}")
check(order11.status == pre_status11, f"status unchanged: {order11.status} == {pre_status11}")
check(user11.balance_credits == pre_balance11, "credits unchanged by cancel reject")
check(user11.membership_expiry == pre_membership11, "membership unchanged by cancel reject")

all_refund11 = db11.query(BillingRecord).filter(
    BillingRecord.user_id == 11,
    BillingRecord.record_type.in_(["REFUND", "REFUND_SHORTFALL"]),
).all()
check(len(all_refund11) == 0, f"no REFUND records from cancel: got {len(all_refund11)}")
db11.rollback()
print("T11 PASS")


# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print(f"VIRTUAL PAY REFUND GUARD: {p} PASS, {fails} FAIL (total {p+fails})")
if fails:
    sys.exit(1)
