"""P2-13/14: Billing rowcount + refund session boundary — behavioral tests"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

engine = create_engine("sqlite://", echo=False)
@event.listens_for(engine, "connect")
def _sp(dbapi, _): dbapi.execute("PRAGMA journal_mode=WAL;")
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

import database
_orig_sl = database.SessionLocal
database.SessionLocal = SessionLocal

from database import Base
from models.db_models import User, BillingRecord
Base.metadata.create_all(bind=engine)

from services.billing_service import check_billing_access, refund_credits

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


# ═══ P2-13: rowcount==0 + refresh sufficient → "操作冲突" ═══
print("=== P2-13: rowcount==0 conflict ===")
db1 = SessionLocal()
u1 = User(id=13001, balance_credits=10, membership_tier="free")
db1.add(u1); db1.commit()

# Only intercept UPDATE executions, pass SELECT through to real DB
from sqlalchemy.sql.dml import Update
real_ex = db1.execute
def smart_exec(stmt, *a, **kw):
    if isinstance(stmt, Update):
        r = MagicMock()
        r.rowcount = 0
        return r
    return real_ex(stmt, *a, **kw)
db1.execute = smart_exec

r = check_billing_access(u1, cost=1, db_session=db1)
check(not r.allowed, "not allowed")
check("操作冲突" in r.reason, f"conflict msg: {r.reason[:50]}")
check(r.points_before == 10, f"points_before preserved: {r.points_before}")
check(r.points_after == 10, f"points_after is refresh balance: {r.points_after}")
db1.execute = real_ex
db1.rollback()
print("P2-13 PASS")

# ═══ P2-13b: insufficient balance path (existing) ═══
print("=== P2-13b: insufficient ===")
db1b = SessionLocal()
u1b = User(id=13002, balance_credits=1, membership_tier="free")
db1b.add(u1b); db1b.commit()
# Deduct elsewhere
db1c = SessionLocal()
db1c.query(User).filter(User.id==13002).update({User.balance_credits: 0})
db1c.commit(); db1c.close()
r1b = check_billing_access(u1b, cost=1, db_session=db1b)
check(not r1b.allowed, "not allowed")
check("操作冲突" not in r1b.reason, f"not conflict: {r1b.reason[:50]}")
db1b.rollback()
print("P2-13b PASS")

# ═══ P2-13c: free point expired → "免费赠送点数已过期" ═══
print("=== P2-13c: free point expired ===")
db1d = SessionLocal()
past = datetime.now() - timedelta(hours=25)
u1d = User(id=13003, balance_credits=1, membership_tier="free",
           free_point_expire_at=past)
db1d.add(u1d); db1d.commit()
r1d = check_billing_access(u1d, cost=1, db_session=db1d)
check(not r1d.allowed, "not allowed")
check("免费赠送点数已过期" in r1d.reason, f"expired msg: {r1d.reason[:50]}")
check("操作冲突" not in r1d.reason, "not a conflict")
db1d.rollback()
print("P2-13c PASS")

# ═══ P2-14: external session — no commit/rollback/close ═══
print("=== P2-14: external session no tx ===")
db2 = SessionLocal()
u2 = User(id=14001, balance_credits=5, membership_tier="free")
db2.add(u2); db2.commit()

# Spy on commit/rollback/close
real_commit = db2.commit
real_rollback = db2.rollback
real_close = db2.close
spy = {"commit": 0, "rollback": 0, "close": 0}
def _spy_commit(): spy["commit"] += 1; real_commit()
def _spy_rollback(): spy["rollback"] += 1; real_rollback()
def _spy_close(): spy["close"] += 1; real_close()
db2.commit = _spy_commit
db2.rollback = _spy_rollback
db2.close = _spy_close

refund_credits(14001, 1, "test", "p214spy", db_session=db2)
check(spy["commit"] == 0, f"commit not called: {spy['commit']}")
check(spy["rollback"] == 0, f"rollback not called: {spy['rollback']}")
check(spy["close"] == 0, f"close not called: {spy['close']}")
# Now commit manually
real_commit()
db3 = SessionLocal()
u3 = db3.query(User).filter(User.id==14001).first()
check(u3.balance_credits == 6, f"commit effective: {u3.balance_credits}")
db3.close(); db2.close()
print("P2-14 PASS")

# ═══ P2-14b: external session exception re-raised ═══
print("=== P2-14b: exception re-raise ===")
db4 = SessionLocal()
u4 = User(id=14002, balance_credits=5, membership_tier="free")
db4.add(u4); db4.commit()

# Spy and break the session
spy4 = {"rollback": 0}
real_rb4 = db4.rollback
def _spy_rb4(): spy4["rollback"] += 1; real_rb4()
db4.rollback = _spy_rb4

# Make query raise via mock
from unittest.mock import patch as mock_patch
orig_query = db4.query
def broken_query(*args, **kwargs):
    raise RuntimeError("simulated DB failure")
db4.query = broken_query

raised = False
try:
    refund_credits(14002, 1, "test", "p214raise", db_session=db4)
except RuntimeError:
    raised = True
check(raised, "exception re-raised to caller")
check(spy4["rollback"] == 0, f"refund_credits did NOT call rollback: {spy4['rollback']}")
db4.rollback = real_rb4
db4.query = orig_query
db4.rollback()
db4.close()
print("P2-14b PASS")

# ═══ P2-14c: own session auto-commit ═══
print("=== P2-14c: own session ===")
db5 = SessionLocal()
u5 = User(id=14003, balance_credits=3, membership_tier="free")
db5.add(u5); db5.commit(); db5.close()
refund_credits(14003, 1, "test", "p214own")
db5b = SessionLocal()
u5b = db5b.query(User).filter(User.id==14003).first()
check(u5b.balance_credits == 4, f"own session committed: {u5b.balance_credits}")
db5b.close()
print("P2-14c PASS")

# ═══ P2-14d: idempotency ═══
print("=== P2-14d: idempotency ===")
db6 = SessionLocal()
u6 = User(id=14004, balance_credits=2, membership_tier="free")
db6.add(u6); db6.commit(); db6.close()
refund_credits(14004, 1, "test", "p214idem")
refund_credits(14004, 1, "test", "p214idem")
db6b = SessionLocal()
u6b = db6b.query(User).filter(User.id==14004).first()
check(u6b.balance_credits == 3, f"idempotent: {u6b.balance_credits}")
br = db6b.query(BillingRecord).filter(
    BillingRecord.user_id==14004, BillingRecord.record_type=="REFUND").count()
check(br == 1, f"1 REFUND: {br}")
db6b.close()
print("P2-14d PASS")

database.SessionLocal = _orig_sl
print(f"\n{'='*50}")
print(f"BILLING P2-13/14: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
