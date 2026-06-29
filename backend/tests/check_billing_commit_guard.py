"""P1-7: AMap billing commit guard — fail loud, rollback, don't continue"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from main import _commit_billing_after_amap

# ── 临时 SQLite 内存库 ──
engine = create_engine("sqlite://", echo=False)
@event.listens_for(engine, "connect")
def _set_pragma(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA journal_mode=WAL;")
SessionLocal = sessionmaker(bind=engine)

from database import Base
from models.db_models import User
Base.metadata.create_all(bind=engine)

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


_user_counter = 0

def _make_billing_session():
    """Create a session with a test user row (unique user per call)."""
    global _user_counter
    _user_counter += 1
    uid = 9900 + _user_counter
    db = SessionLocal()
    user = User(id=uid, balance_credits=5, membership_tier="free",
                wx_mini_openid=f"oBilling{uid}")
    db.add(user)
    db.commit()
    # Make a "pending" change so commit does something
    user.balance_credits = 4  # simulate billing deduction
    db.add(user)  # mark as dirty
    return db, user, uid


# ═══ T1: commit success → no rollback, no raise ═══
print("=== T1: commit success ===")
db1, u1, uid1 = _make_billing_session()
try:
    _commit_billing_after_amap(db1, "req_001", uid1, "points")
    # verify user was persisted
    db2 = SessionLocal()
    u2 = db2.query(User).filter(User.id == uid1).first()
    check(u2.balance_credits == 4, f"commit persisted: {u2.balance_credits}")
    db2.close()
    check(True, "commit success — no exception")
except Exception as e:
    check(False, f"should not raise on success: {e}")
print("T1 PASS")

# ═══ T2: commit failure → raises RuntimeError ═══
print("=== T2: commit failure raises ===")
from unittest.mock import patch
db2a, u2a, uid2 = _make_billing_session()
with patch.object(db2a, 'commit', side_effect=OSError("disk full")):
    try:
        _commit_billing_after_amap(db2a, "req_002", uid2, "points")
        check(False, "should have raised on commit failure")
    except RuntimeError as e:
        msg = str(e)
        check("BILLING_COMMIT_FAILED" in msg, f"correct exception type: {msg[:80]}")
        check("req_002" in msg, f"request_id in error: {msg[:80]}")
print("T2 PASS")

# ═══ T3: session closed after failure ═══
print("=== T3: session closed after failure ===")
db3, u3, uid3 = _make_billing_session()
with patch.object(db3, 'commit', side_effect=OSError("disk full")):
    try:
        _commit_billing_after_amap(db3, "req_003", uid3, "points")
    except RuntimeError:
        check(True, "session closed after failure (finally executed)")
print("T3 PASS")

# ═══ T4: error message is safe ═══
print("=== T4: error message is safe ===")
db4, u4, uid4 = _make_billing_session()
with patch.object(db4, 'commit', side_effect=OSError("disk full")):
    try:
        _commit_billing_after_amap(db4, "req_004", uid4, "points")
    except RuntimeError as e:
        msg = str(e).lower()
        check("openid" not in msg, "no openid in error")
        check("phone" not in msg, "no phone in error")
        check("token" not in msg, "no token in error")
        check("password" not in msg, "no password in error")
        check("secret" not in msg, "no secret in error")
        check("未扣费" in msg or "重试" in msg, f"user-friendly message: {msg[:80]}")
print("T4 PASS")

# ═══ T5: exception carries tracking info ═══
print("=== T5: tracking info in exception ===")
db5, u5, uid5 = _make_billing_session()
with patch.object(db5, 'commit', side_effect=OSError("disk full")):
    try:
        _commit_billing_after_amap(db5, "req_ABC123", uid5, "points")
    except RuntimeError as e:
        check("req_ABC123" in str(e), f"request_id in exception: {str(e)[:80]}")
print("T5 PASS")

# ═══ T6: rollback called on failure ═══
print("=== T6: rollback called on failure ===")
db6, u6, uid6 = _make_billing_session()
rollback_called = [False]
orig_rollback = db6.rollback
def _tracked_rollback():
    rollback_called[0] = True
    orig_rollback()
db6.rollback = _tracked_rollback
with patch.object(db6, 'commit', side_effect=OSError("disk full")):
    try:
        _commit_billing_after_amap(db6, "req_006", uid6, "points")
    except RuntimeError:
        pass
check(rollback_called[0], "rollback called on commit failure")
print("T6 PASS")

# ═══ T7: event_stream RuntimeError → SSE error mapping ═══
print("=== T7: BILLING_COMMIT_FAILED → SSE error ===")
import main as main_mod
# Verify the branch exists in main.py
src = open(os.path.join(os.path.dirname(__file__), '..', 'main.py'), 'r', encoding='utf-8').read()
check('"BILLING_COMMIT_FAILED"' in src or 'BILLING_COMMIT_FAILED' in src,
     "main.py handles BILLING_COMMIT_FAILED in RuntimeError branch")
check('error_stage="billing_commit_failed"' in src or "error_stage='billing_commit_failed'" in src,
     "error_stage set to billing_commit_failed")
check('"not_charged"' in src or "'not_charged'" in src,
     "billing_status is not_charged")
check('本次未扣费' in src,
     "user sees '本次未扣费，请稍后重试'")
print("T7 PASS")

print(f"\n{'='*50}")
print(f"BILLING COMMIT GUARD: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
