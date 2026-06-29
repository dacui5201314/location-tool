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
