"""Payment idempotency: atomic claim + same-transaction grant + concurrency safety"""
import sys, os, threading, time
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
from models.db_models import PaymentOrder, User, BillingRecord
Base.metadata.create_all(bind=engine)

from services.payment_idempotency import claim_payment_order, grant_payment_benefits

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _make_order(db, out_trade_no, status="CREATED", credits=10, days=0, user_id=1, amount_fen=1000, pay_channel="WECHAT_JSAPI"):
    order = PaymentOrder(out_trade_no=out_trade_no, user_id=user_id, sku_id=1,
                         credits=credits, membership_days=days,
                         amount_fen=amount_fen, status=status,
                         pay_channel=pay_channel,
                         created_at=datetime.now() - timedelta(minutes=5))
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def _make_user(db, user_id=1, credits=0, mini_openid=None):
    if mini_openid is None:
        mini_openid = f"oTest{user_id:03d}"
    user = User(id=user_id, balance_credits=credits, membership_tier="free",
                wx_mini_openid=mini_openid)
    db.add(user)
    db.commit()
    return user


# ═══ T1: basic claim CREATED → PAID ═══
print("=== T1: claim CREATED → PAID ===")
db = SessionLocal()
user = _make_user(db, user_id=1)
order = _make_order(db, "TEST_CLAIM_001", user_id=1)
claimed = claim_payment_order(db, order)
check(claimed, "claim CREATED succeeds")
db.refresh(order)
check(order.status == "PAID", "status is PAID after claim")
db.rollback()
print("T1 PASS")

# ═══ T2: claim PROCESSING → PAID ═══
print("=== T2: claim PROCESSING → PAID ===")
db2 = SessionLocal()
user2 = _make_user(db2, user_id=2)
order2 = _make_order(db2, "TEST_CLAIM_002", status="PROCESSING", user_id=2)
claimed2 = claim_payment_order(db2, order2)
check(claimed2, "claim PROCESSING succeeds")
db2.refresh(order2)
check(order2.status == "PAID", "status is PAID after claim")
db2.rollback()
print("T2 PASS")

# ═══ T3: claim PAID returns False ═══
print("=== T3: claim PAID rejected ===")
db3 = SessionLocal()
user3 = _make_user(db3, user_id=3)
order3 = _make_order(db3, "TEST_CLAIM_003", status="PAID", user_id=3)
claimed3 = claim_payment_order(db3, order3)
check(not claimed3, "claim PAID returns False")
db3.refresh(order3)
check(order3.status == "PAID", "status still PAID")
db3.rollback()
print("T3 PASS")

# ═══ T4: claim REFUNDED rejected ═══
print("=== T4: claim REFUNDED rejected ===")
db4 = SessionLocal()
user4 = _make_user(db4, user_id=4)
order4 = _make_order(db4, "TEST_CLAIM_004", status="REFUNDED", user_id=4)
claimed4 = claim_payment_order(db4, order4)
check(not claimed4, "claim REFUNDED returns False")
db4.rollback()
print("T4 PASS")

# ═══ T5: claim CANCELLED/CLOSED/FAILED all rejected ═══
print("=== T5: claim other terminal states ===")
for idx, st in enumerate(["CANCELLED", "CLOSED", "FAILED"]):
    db5 = SessionLocal()
    uid = 50 + idx
    user5 = _make_user(db5, user_id=uid)
    order5 = _make_order(db5, f"TEST_CLAIM_{st}", status=st, user_id=uid)
    claimed5 = claim_payment_order(db5, order5)
    check(not claimed5, f"claim {st} returns False")
    db5.rollback()
print("T5 PASS")

# ═══ T6: claim + grant same transaction ═══
print("=== T6: claim + grant same transaction ===")
db6 = SessionLocal()
user6 = _make_user(db6, user_id=6, credits=5)
order6 = _make_order(db6, "TEST_CLAIM_006", credits=3, days=0, user_id=6)
claimed6 = claim_payment_order(db6, order6)
check(claimed6, "claim succeeds")
grant_payment_benefits(db6, order6)
db6.commit()
db6.refresh(user6)
check(user6.balance_credits == 8, f"credits 5+3=8: {user6.balance_credits}")
# BillingRecord
br = db6.query(BillingRecord).filter(
    BillingRecord.user_id == 6, BillingRecord.record_type == "PURCHASE"
).first()
check(br is not None, "PURCHASE billing record written")
check(br.amount == 3, f"billing amount=3: {br.amount}")
db6.rollback()
print("T6 PASS")

# ═══ T7: grant rolls back on exception ═══
print("=== T7: grant rolls back on exception ===")
db7 = SessionLocal()
user7 = _make_user(db7, user_id=7, credits=5)
order7 = _make_order(db7, "TEST_CLAIM_007", credits=3, user_id=7)
claimed7 = claim_payment_order(db7, order7)
check(claimed7, "claim succeeds")
# Force error by deleting user
db7.delete(user7)
db7.flush()
try:
    grant_payment_benefits(db7, order7)
    check(False, "should have raised")
except ValueError:
    db7.rollback()
    check(True, "ValueError caught, rolled back")
# Verify order rolled back
db7.refresh(order7)
check(order7.status != "PAID", f"order not PAID after rollback: {order7.status}")
db7.rollback()
print("T7 PASS")

# ═══ T8: concurrent claim — only one wins ═══
print("=== T8: concurrent claim only one wins ===")
db8a = SessionLocal()
user8 = _make_user(db8a, user_id=8, credits=10)
order8 = _make_order(db8a, "TEST_CONCURRENT", credits=5, user_id=8)
db8a.commit()

# Two independent sessions to simulate concurrent requests
db8b = SessionLocal()
order8b = db8b.query(PaymentOrder).filter(PaymentOrder.out_trade_no == "TEST_CONCURRENT").first()

c1 = claim_payment_order(db8a, order8)
c2 = claim_payment_order(db8b, order8b)
check(c1 or c2, "at least one claim succeeds")
check(not (c1 and c2), "not both claims succeed — only one wins")

# Grant on winner
winner_db = db8a if c1 else db8b
winner_order = order8 if c1 else order8b
if c1:
    db8a.refresh(user8)
    grant_payment_benefits(db8a, order8)
    db8a.commit()
else:
    user8b = db8b.query(User).filter(User.id == 8).first()
    grant_payment_benefits(db8b, order8b)
    db8b.commit()

# Verify only one PURCHASE record
# Need a fresh session to see committed state
winner_db.refresh(winner_order)
db_check = SessionLocal()
br_count = db_check.query(BillingRecord).filter(
    BillingRecord.user_id == 8, BillingRecord.record_type == "PURCHASE"
).count()
check(br_count == 1, f"only 1 PURCHASE billing record: {br_count}")
db_check.rollback()
db8a.rollback()
db8b.rollback()
print("T8 PASS")

# ═══ T9: double _grant_order only grants once ═══
print("=== T9: double grant idempotent ===")
db9 = SessionLocal()
user9 = _make_user(db9, user_id=9, credits=0)
order9 = _make_order(db9, "TEST_DOUBLE_GRANT", credits=5, user_id=9)

# simulate _grant_order call
from services.payment_idempotency import claim_payment_order as _cpo, grant_payment_benefits as _gpb

def sim_grant(db, order, uid):
    if order.status == "PAID":
        return True
    if order.status in ("REFUNDED", "CANCELLED", "CLOSED", "FAILED"):
        return False
    claimed = _cpo(db, order)
    if not claimed:
        db.refresh(order)
        return order.status == "PAID"
    try:
        user = db.query(User).filter(User.id == uid).first()
        _gpb(db, order)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False

r1 = sim_grant(db9, order9, 9)
check(r1, "first grant succeeds")
db9.refresh(user9)
check(user9.balance_credits == 5, f"credits 0+5=5: {user9.balance_credits}")
# Second grant (simulate concurrent callback)
order9b = db9.query(PaymentOrder).filter(PaymentOrder.out_trade_no == "TEST_DOUBLE_GRANT").first()
r2 = sim_grant(db9, order9b, 9)
check(r2, "second grant returns True (idempotent)")
db9.refresh(user9)
check(user9.balance_credits == 5, f"credits still 5 after second grant: {user9.balance_credits}")
br9 = db9.query(BillingRecord).filter(
    BillingRecord.user_id == 9, BillingRecord.record_type == "PURCHASE"
).count()
check(br9 == 1, f"only 1 PURCHASE record after double grant: {br9}")
db9.rollback()
print("T9 PASS")

# ═══ T10: grant with membership days ═══
print("=== T10: membership grant ===")
db10 = SessionLocal()
user10 = _make_user(db10, user_id=10, credits=3)
user10.membership_tier = "free"
order10 = _make_order(db10, "TEST_MEMBER", credits=0, days=30, user_id=10)
claimed10 = _cpo(db10, order10)
check(claimed10, "claim succeeds")
_gpb(db10, order10)
db10.commit()
db10.refresh(user10)
check(user10.membership_tier != "free", f"tier upgraded: {user10.membership_tier}")
check(user10.balance_credits == 3, "credits unchanged for membership-only order")
mem_br = db10.query(BillingRecord).filter(
    BillingRecord.user_id == 10, BillingRecord.record_type == "MEMBERSHIP"
).first()
check(mem_br is not None, "MEMBERSHIP billing record written")
db10.rollback()
print("T10 PASS")

# ═══ T11: real pay.py notify openid validation ═══
print("=== T11: real notify openid validation ===")
from routers.pay import _process_notify_grant

# T11a: payer.openid missing → no crash, no UnboundLocalError
db11a = SessionLocal()
user11a = _make_user(db11a, user_id=111, mini_openid="oMatch111")
order11a = _make_order(db11a, "TEST_OPENID_A", user_id=111, amount_fen=500, pay_channel="WECHAT_JSAPI")
r11a = _process_notify_grant(db11a, "TEST_OPENID_A", "txn_11a", {"amount": {"total": 500}})
check(r11a["http_status"] == 200, f"missing payer.openid OK: {r11a}")
check(r11a["claimed"], "missing payer.openid → claimed")
db11a.commit()
db11a.refresh(user11a)
check(user11a.balance_credits > 0, "credits granted when openid missing")
db11a.rollback()

# T11b: payer.openid matches → success
db11b = SessionLocal()
user11b = _make_user(db11b, user_id=112, mini_openid="oMatch112")
order11b = _make_order(db11b, "TEST_OPENID_B", user_id=112, amount_fen=500, pay_channel="WECHAT_JSAPI")
r11b = _process_notify_grant(db11b, "TEST_OPENID_B", "txn_11b", {"amount": {"total": 500}, "payer": {"openid": "oMatch112"}})
check(r11b["http_status"] == 200, f"matching openid OK: {r11b}")
check(r11b["claimed"], "matching openid → claimed")
db11b.commit()
db11b.refresh(user11b)
check(user11b.balance_credits > 0, "credits granted on openid match")
db11b.rollback()

# T11c: payer.openid != wx_mini_openid → rejected, not claimed
db11c = SessionLocal()
user11c = _make_user(db11c, user_id=113, mini_openid="oMatch113")
order11c = _make_order(db11c, "TEST_OPENID_C", user_id=113, amount_fen=500, pay_channel="WECHAT_JSAPI")
r11c = _process_notify_grant(db11c, "TEST_OPENID_C", "txn_11c", {"amount": {"total": 500}, "payer": {"openid": "oWrong"}})
check(r11c["http_status"] == 400, f"mismatch openid rejected: {r11c}")
check(not r11c["claimed"], "mismatch openid → NOT claimed")
db11c.refresh(order11c)
check(order11c.status != "PAID", "order still not PAID after openid mismatch")
db11c.rollback()

# T11d: payer.openid exists but db_user.wx_mini_openid empty → rejected
db11d = SessionLocal()
user11d = _make_user(db11d, user_id=114, mini_openid="")
order11d = _make_order(db11d, "TEST_OPENID_D", user_id=114, amount_fen=500, pay_channel="WECHAT_JSAPI")
r11d = _process_notify_grant(db11d, "TEST_OPENID_D", "txn_11d", {"amount": {"total": 500}, "payer": {"openid": "oNonEmpty"}})
check(r11d["http_status"] == 400, f"payer has openid but user has none → rejected: {r11d}")
check(not r11d["claimed"], "empty user openid but payer has openid → NOT claimed")
db11d.refresh(order11d)
check(order11d.status != "PAID", "order not PAID when user has no openid")
db11d.rollback()
print("T11 PASS")

# ═══ T12: real reconcile PROCESSING + terminal state protection ═══
print("=== T12: real reconcile paths ===")
from unittest.mock import patch
import routers.virtual_pay as vpay_mod

# T12a: PROCESSING order reconcile with wx confirming PAID → succeeds
db12a = SessionLocal()
user12a = _make_user(db12a, user_id=1201, credits=2)
order12a = _make_order(db12a, "TEST_RECONCILE_P", status="PROCESSING", credits=4, user_id=1201, pay_channel="WECHAT_VIRTUAL")
db12a.commit()
# Mock _wx_query_virtual_order to return PAID
with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="PAID"):
    result12a = vpay_mod.reconcile_order("TEST_RECONCILE_P",
        user={"user_id": 1201}, db=db12a)
check(result12a.get("ok"), f"PROCESSING reconcile ok: {result12a}")
check(result12a.get("status") == "PAID", f"PROCESSING → PAID: {result12a.get('status')}")
check(result12a.get("synced"), "synced=True for PROCESSING reconcile")
db12a.refresh(user12a)
check(user12a.balance_credits == 6, f"credits 2+4=6: {user12a.balance_credits}")
check(order12a.status == "PAID", "order status is PAID")
db12a.rollback()

# T12b: REFUNDED → reconcile raises HTTPException (400), no grant
db12b = SessionLocal()
user12b = _make_user(db12b, user_id=1301, credits=2)
order12b = _make_order(db12b, "TEST_RECONCILE_REF", status="REFUNDED", credits=4, user_id=1301, pay_channel="WECHAT_VIRTUAL")
db12b.commit()
try:
    with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="PAID"):
        vpay_mod.reconcile_order("TEST_RECONCILE_REF", user={"user_id": 1301}, db=db12b)
    check(False, "REFUNDED should raise HTTPException")
except Exception as e:
    check("400" in str(e) or "REFUNDED" in str(e), f"REFUNDED rejected: {e}")
db12b.refresh(user12b)
check(user12b.balance_credits == 2, f"credits unchanged for REFUNDED: {user12b.balance_credits}")
db12b.rollback()

# T12c: CANCELLED → rejected
db12c = SessionLocal()
user12c = _make_user(db12c, user_id=1401, credits=1)
order12c = _make_order(db12c, "TEST_RECONCILE_CXL", status="CANCELLED", credits=4, user_id=1401, pay_channel="WECHAT_VIRTUAL")
db12c.commit()
try:
    with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="PAID"):
        vpay_mod.reconcile_order("TEST_RECONCILE_CXL", user={"user_id": 1401}, db=db12c)
    check(False, "CANCELLED should raise HTTPException")
except Exception as e:
    check("400" in str(e), f"CANCELLED rejected: {e}")
db12c.rollback()

# T12d: CLOSED → rejected
db12d = SessionLocal()
user12d = _make_user(db12d, user_id=1501, credits=1)
order12d = _make_order(db12d, "TEST_RECONCILE_CLS", status="CLOSED", credits=4, user_id=1501, pay_channel="WECHAT_VIRTUAL")
db12d.commit()
try:
    with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="PAID"):
        vpay_mod.reconcile_order("TEST_RECONCILE_CLS", user={"user_id": 1501}, db=db12d)
    check(False, "CLOSED should raise HTTPException")
except Exception as e:
    check("400" in str(e), f"CLOSED rejected: {e}")
db12d.rollback()

# T12e: FAILED → rejected
db12e = SessionLocal()
user12e = _make_user(db12e, user_id=1601, credits=1)
order12e = _make_order(db12e, "TEST_RECONCILE_FAIL", status="FAILED", credits=4, user_id=1601, pay_channel="WECHAT_VIRTUAL")
db12e.commit()
try:
    with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="PAID"):
        vpay_mod.reconcile_order("TEST_RECONCILE_FAIL", user={"user_id": 1601}, db=db12e)
    check(False, "FAILED should raise HTTPException")
except Exception as e:
    check("400" in str(e), f"FAILED rejected: {e}")
db12e.rollback()
print("T12 PASS")

# ═══ T13: BillingRecord reason has channel prefix ═══
print("=== T13: reason channel prefix ===")
db13 = SessionLocal()
user13 = _make_user(db13, user_id=13, credits=0)
order13a = _make_order(db13, "TEST_CHAN_JSAPI", credits=3, user_id=13, pay_channel="WECHAT_JSAPI")
claimed13a = claim_payment_order(db13, order13a)
check(claimed13a, "claim JSAPI succeeds")
grant_payment_benefits(db13, order13a)
db13.commit()
br13a = db13.query(BillingRecord).filter(BillingRecord.user_id == 13, BillingRecord.record_type == "PURCHASE").first()
check("微信" in (br13a.reason or ""), f"JSAPI reason has 微信 prefix: {br13a.reason[:40]}")
db13.rollback()

db13b = SessionLocal()
user13b = _make_user(db13b, user_id=14, credits=0)
order13b = _make_order(db13b, "TEST_CHAN_VIRT", credits=5, user_id=14, pay_channel="WECHAT_VIRTUAL")
claimed13b = claim_payment_order(db13b, order13b)
check(claimed13b, "claim VIRTUAL succeeds")
grant_payment_benefits(db13b, order13b)
db13b.commit()
br13b = db13b.query(BillingRecord).filter(BillingRecord.user_id == 14, BillingRecord.record_type == "PURCHASE").first()
check("虚拟" in (br13b.reason or ""), f"VIRTUAL reason has 虚拟 prefix: {br13b.reason[:40]}")
db13b.rollback()
print("T13 PASS")

print(f"\n{'='*50}")
print(f"PAYMENT IDEMPOTENCY: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
