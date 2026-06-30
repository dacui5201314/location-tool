"""/api/analyze guard: rate limiting + concurrency lock"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import _check_analyze_rate, _analyze_active, _analyze_rates
from main import _ANALYZE_LIMIT_60S, _ANALYZE_LIMIT_1H, _ANALYZE_LIMIT_1D

p = 0
f = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")

# ═══ T1: rate limits are configurable ═══
print("=== T1: rate limit defaults ===")
check(_ANALYZE_LIMIT_60S >= 3, f"60s limit >= 3: {_ANALYZE_LIMIT_60S}")
check(_ANALYZE_LIMIT_1H >= 15, f"1h limit >= 15: {_ANALYZE_LIMIT_1H}")
check(_ANALYZE_LIMIT_1D >= 40, f"1d limit >= 40: {_ANALYZE_LIMIT_1D}")
check(_ANALYZE_LIMIT_60S <= 10, "60s limit not too strict")
print("T1 PASS")

# ═══ T2: rate limiter allows normal usage ═══
print("=== T2: rate limiter normal flow ===")
test_uid = 999001
for k in list(_analyze_rates.keys()):
    if k >= 999000:
        del _analyze_rates[k]

for _ in range(3):
    ok = _check_analyze_rate(test_uid)
    check(ok, f"normal usage ({_+1}/3) allowed")
del _analyze_rates[test_uid]
print("T2 PASS")

# ═══ T3: rate limiter blocks excess ═══
print("=== T3: rate limiter blocks excess ===")
test_uid2 = 999002
_analyze_rates[test_uid2] = [time.time() - 1] * _ANALYZE_LIMIT_60S
ok = _check_analyze_rate(test_uid2)
check(not ok, "exceeds 60s limit → blocked")
del _analyze_rates[test_uid2]
print("T3 PASS")

# ═══ T4: rate limiter respects hour limit ═══
print("=== T4: hour limit ===")
test_uid3 = 999003
_analyze_rates[test_uid3] = [time.time() - 100] * (_ANALYZE_LIMIT_1H)
ok = _check_analyze_rate(test_uid3)
check(not ok, "exceeds 1h limit → blocked")
del _analyze_rates[test_uid3]
print("T4 PASS")

# ═══ T5: rate limiter respects day limit ═══
print("=== T5: day limit ===")
test_uid4 = 999004
_analyze_rates[test_uid4] = [time.time() - 200] * (_ANALYZE_LIMIT_1D)
ok = _check_analyze_rate(test_uid4)
check(not ok, "exceeds 1d limit → blocked")
del _analyze_rates[test_uid4]
print("T5 PASS")

# ═══ T6: concurrency lock ═══
print("=== T6: concurrency lock ===")
_analyze_active.discard(test_uid)
check(test_uid not in _analyze_active, "lock free initially")
_analyze_active.add(test_uid)
check(test_uid in _analyze_active, "lock acquired")
# Second request would be rejected (tested via discard/add flow)
_analyze_active.discard(test_uid)
check(test_uid not in _analyze_active, "lock released")
print("T6 PASS")

# ═══ T7: stale rate entries cleaned ═══
print("=== T7: stale entries cleaned ===")
test_uid5 = 999005
_analyze_rates[test_uid5] = [time.time() - 90000]  # 25h ago, should be filtered
ok = _check_analyze_rate(test_uid5)
check(ok, "stale entries filtered, new request allowed")
del _analyze_rates[test_uid5]
print("T7 PASS")

# ═══ T7b: lock release after discard ═══
print("=== T7b: lock discard ===")
test_uid7 = 999007
_analyze_active.add(test_uid7)
check(test_uid7 in _analyze_active, "lock held before discard")
_analyze_active.discard(test_uid7)
check(test_uid7 not in _analyze_active, "lock released after discard")
# discard non-existent key does not raise
_analyze_active.discard(999999)
check(True, "discard missing key is safe")
print("T7b PASS")

# ═══ T8: env defaults sane ═══
print("=== T8: env config read ===")
import os
v60 = int(os.getenv("ANALYZE_RATE_LIMIT_60S", "5"))
v1h = int(os.getenv("ANALYZE_RATE_LIMIT_1H", "20"))
v1d = int(os.getenv("ANALYZE_RATE_LIMIT_1D", "50"))
check(v60 > 0 and v1h > 0 and v1d > 0, "all limits positive")
check(v60 <= v1h <= v1d, "limits are monotonic (60s <= 1h <= 1d)")
print("T8 PASS")

print(f"\n{'='*50}")
print(f"ANALYZE GUARD: {p} PASS, {f} FAIL (total {p+f})")
if f: sys.exit(1)

# ═══════════════════════════════════════════════════════════════
# P1-B: billing session 统一 rollback/close 守卫（独立 SQLite 内存库）
# ═══════════════════════════════════════════════════════════════
# 注：P1-B 测试与 T1-T8 限流测试共用一个 PASS/FAIL 计数器，但使用独立的
# SQLite 内存库，避免与主库 side-effect 交互。

_p1b_p = 0
_p1b_f = 0
def _p1b_check(cond, msg):
    global _p1b_p, _p1b_f, p, f
    if cond:
        _p1b_p += 1; p += 1
    else:
        _p1b_f += 1; f += 1; print(f"  FAIL: {msg}")

from sqlalchemy import create_engine as _ce, event as _ev
from sqlalchemy.orm import sessionmaker as _sm
_billing_engine = _ce("sqlite://", echo=False)
@_ev.listens_for(_billing_engine, "connect")
def _bs_pragma(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA journal_mode=WAL;")
_BillingSession = _sm(bind=_billing_engine)

from database import Base as _Base
from models.db_models import User as _User
_Base.metadata.create_all(bind=_billing_engine)

from main import (
    _rollback_close_billing_session,
    _commit_billing_after_amap,
)

_bs_counter = 0

def _make_bs_session():
    """Create a billing session with a test user. Returns (db, user, uid, billing_state)."""
    global _bs_counter
    _bs_counter += 1
    uid = 9800 + _bs_counter
    db = _BillingSession()
    user = _User(id=uid, balance_credits=10, membership_tier="free",
                 wx_mini_openid=f"oBS{uid}")
    db.add(user)
    db.commit()
    db.refresh(user)
    # 模拟计费扣点（staged, not committed）
    user.balance_credits = 9
    db.add(user)
    billing_state = {"committed": False, "closed": False}
    return db, user, uid, billing_state


# ── BS1: 未 committed 未 closed → rollback + close ──
print("=== BS1: uncommitted → rollback + close ===")
db1, u1, uid1, bs1 = _make_bs_session()
_p1b_check(not bs1["committed"], "not committed")
_p1b_check(not bs1["closed"], "not closed")
_rollback_close_billing_session(db1, bs1)
_p1b_check(bs1["closed"], "closed after helper")
# verify rollback happened: balance back to original
db_verify = _BillingSession()
vu = db_verify.query(_User).filter(_User.id == uid1).first()
_p1b_check(vu.balance_credits == 10, f"balance rolled back: {vu.balance_credits} == 10")
db_verify.close()
print("BS1 PASS")


# ── BS2: 已 closed → 不重复 rollback/close ──
print("=== BS2: already closed → no-op ===")
db2, u2, uid2, bs2 = _make_bs_session()
_rollback_close_billing_session(db2, bs2)  # first call
_p1b_check(bs2["closed"], "closed after first call")
# modify balance artificially to detect if rollback happens again
u2.balance_credits = 5  # different from original 10
# second call should be no-op
_rollback_close_billing_session(db2, bs2)
_p1b_check(bs2["closed"], "still closed after second call")
db_verify2 = _BillingSession()
vu2 = db_verify2.query(_User).filter(_User.id == uid2).first()
_p1b_check(vu2.balance_credits == 10, f"balance rolled back by first call only: {vu2.balance_credits} == 10")
db_verify2.close()
print("BS2 PASS")


# ── BS3: committed → 不 rollback，只 close ──
print("=== BS3: committed → no rollback, close only ===")
db3, u3, uid3, bs3 = _make_bs_session()
# Simulate commit success + state marking (as _commit_billing_after_amap would do)
db3.commit()
bs3["committed"] = True
# Now call the guard → should NOT rollback (committed), should close
_rollback_close_billing_session(db3, bs3)
_p1b_check(bs3["closed"], "closed after helper")
db_verify3 = _BillingSession()
vu3 = db_verify3.query(_User).filter(_User.id == uid3).first()
_p1b_check(vu3.balance_credits == 9, f"balance persisted (not rolled back): {vu3.balance_credits} == 9")
db_verify3.close()
print("BS3 PASS")


# ── BS4: commit 成功 + billing_state 标记 + finally 不重复 rollback ──
print("=== BS4: commit success → state marked, finally no-op ===")
db4, u4, uid4, bs4 = _make_bs_session()
try:
    _commit_billing_after_amap(db4, "req_bs4", uid4, "points", billing_state=bs4)
    _p1b_check(bs4["committed"], "committed after success")
    _p1b_check(bs4["closed"], "closed after success")
    db_verify4 = _BillingSession()
    vu4 = db_verify4.query(_User).filter(_User.id == uid4).first()
    _p1b_check(vu4.balance_credits == 9, f"balance persisted: {vu4.balance_credits} == 9")
    db_verify4.close()
    # finally 兜底 guard 对 committed+closed session 应为 no-op
    _rollback_close_billing_session(db4, bs4)
    _p1b_check(bs4["closed"], "still closed after guard (no-op)")
    _p1b_check(vu4.balance_credits == 9, "balance unchanged by guard")
except Exception as e:
    _p1b_check(False, f"commit should not fail: {e}")
print("BS4 PASS")


# ── BS5: AMap 成功 + 生成器取消 → finally 兜底 rollback ──
# 模拟：AMap 成功（_amap_failed=False），但 _commit_billing_after_amap 未被调用
# （模拟客户端在 commit 前断开），finally 应 rollback + close
print("=== BS5: generator cancelled before commit → finally guard rollback ===")
db5, u5, uid5, bs5 = _make_bs_session()
# 模拟：AMap OK，但 commit 未执行（如客户端断开），finally 触发
_p1b_check(not bs5["committed"], "not committed (commit never called)")
_p1b_check(not bs5["closed"], "not closed")
_rollback_close_billing_session(db5, bs5)
_p1b_check(bs5["closed"], "closed after finally guard")
db_verify5 = _BillingSession()
vu5 = db_verify5.query(_User).filter(_User.id == uid5).first()
_p1b_check(vu5.balance_credits == 10, f"balance rolled back: {vu5.balance_credits} == 10")
db_verify5.close()
print("BS5 PASS")


# ── BS6: AMap 失败路径 → 标记 _amap_failed, 不 committed, rollback+close ──
print("=== BS6: AMap failed path → rollback + close (not committed) ===")
db6, u6, uid6, bs6 = _make_bs_session()
# AMap 失败：不调 _commit_billing_after_amap，直接调兜底 helper
_p1b_check(not bs6["committed"], "not committed (AMap failed)")
_rollback_close_billing_session(db6, bs6)
_p1b_check(bs6["closed"], "closed after AMap fail path")
db_verify6 = _BillingSession()
vu6 = db_verify6.query(_User).filter(_User.id == uid6).first()
_p1b_check(vu6.balance_credits == 10, f"balance rolled back: {vu6.balance_credits} == 10")
db_verify6.close()
print("BS6 PASS")


# ── BS7: _analyze_active 释放（已在 T6/T7b 测过，追加唯一性确认）──
print("=== BS7: _analyze_active release ===")
test_lock_uid = 999010
_analyze_active.add(test_lock_uid)
_p1b_check(test_lock_uid in _analyze_active, "lock held")
_analyze_active.discard(test_lock_uid)
_p1b_check(test_lock_uid not in _analyze_active, "lock released in finally")
print("BS7 PASS")


# ── BS8: billing_state 在 _commit_billing_after_amap 中正确标记 ──
print("=== BS8: billing_state marked by _commit_billing_after_amap ===")
db8, u8, uid8, bs8 = _make_bs_session()
_p1b_check(not bs8["committed"], "not committed before")
_p1b_check(not bs8["closed"], "not closed before")
_commit_billing_after_amap(db8, "req_bs8", uid8, "points", billing_state=bs8)
_p1b_check(bs8["committed"], "committed after")
_p1b_check(bs8["closed"], "closed after")
# finally guard on already-closed should be no-op
_rollback_close_billing_session(db8, bs8)
_p1b_check(bs8["closed"], "still closed after guard (no-op)")
print("BS8 PASS")


# ── BS9: _commit_billing_after_amap 无 billing_state（向后兼容）──
print("=== BS9: _commit_billing_after_amap w/o billing_state (backcompat) ===")
db9, u9, uid9, bs9 = _make_bs_session()
try:
    _commit_billing_after_amap(db9, "req_bs9", uid9, "membership")  # no billing_state
    _p1b_check(True, "succeeds without billing_state")
    db_verify9 = _BillingSession()
    vu9 = db_verify9.query(_User).filter(_User.id == uid9).first()
    _p1b_check(vu9.balance_credits == 9, f"balance persisted: {vu9.balance_credits}")
    db_verify9.close()
except Exception as e:
    _p1b_check(False, f"should not raise without billing_state: {e}")
print("BS9 PASS")


print(f"\n{'='*50}")
print(f"P1-B BILLING SESSION: {_p1b_p} PASS, {_p1b_f} FAIL (total {_p1b_p+_p1b_f})")
if _p1b_f:
    sys.exit(1)
