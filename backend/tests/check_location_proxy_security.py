"""Location proxy security: rate limiting, caching, min keyword length"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routers.location import (
    _rate_check, _suggest_rates, _regeocode_rates, _suggest_cache,
    _LOC_SUGGEST_MIN_KEYWORD, _LOC_CACHE_TTL,
    _LOC_SUGGEST_LIMIT_PER_MIN, _LOC_REGEOCODE_LIMIT_PER_MIN,
)

p = 0
f = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")

# ═══ T1: threshold defaults ═══
print("=== T1: threshold defaults ===")
check(_LOC_SUGGEST_MIN_KEYWORD >= 2, f"min keyword >= 2: {_LOC_SUGGEST_MIN_KEYWORD}")
check(_LOC_CACHE_TTL >= 10, f"cache TTL >= 10s: {_LOC_CACHE_TTL}")
check(_LOC_SUGGEST_LIMIT_PER_MIN >= 30, f"suggest limit >= 30: {_LOC_SUGGEST_LIMIT_PER_MIN}")
check(_LOC_REGEOCODE_LIMIT_PER_MIN >= 10, f"regeocode limit >= 10: {_LOC_REGEOCODE_LIMIT_PER_MIN}")
print("T1 PASS")

# ═══ T2: rate_check normal flow ═══
print("=== T2: rate_check normal flow ===")
test_ip = "test_loc_sec_normal"
for k in list(_suggest_rates.keys()):
    if "test_loc_sec" in k:
        del _suggest_rates[k]

for i in range(5):
    ok = _rate_check(_suggest_rates, test_ip, 60, 5000)
    check(ok, f"normal suggest request {i+1}/5 allowed")
del _suggest_rates[test_ip]
print("T2 PASS")

# ═══ T3: rate_check blocks excess ═══
print("=== T3: rate_check blocks excess ===")
test_ip2 = "test_loc_sec_excess"
_suggest_rates[test_ip2] = [time.time() - 0.1] * 60
ok = _rate_check(_suggest_rates, test_ip2, 60, 5000)
check(not ok, "exceeds limit → blocked")
del _suggest_rates[test_ip2]
print("T3 PASS")

# ═══ T4: stale timestamps cleaned ═══
print("=== T4: stale timestamps cleaned ===")
test_ip3 = "test_loc_sec_stale"
_suggest_rates[test_ip3] = [time.time() - 120] * 60  # all 2min old
ok = _rate_check(_suggest_rates, test_ip3, 60, 5000)
check(ok, "stale entries cleaned → new request allowed")
del _suggest_rates[test_ip3]
print("T4 PASS")

# ═══ T5: cache write and hit ═══
print("=== T5: suggest cache ===")
test_ck = "test_cache_key_001"
now = time.time()
_suggest_cache[test_ck] = (now + 30, {"ok": True, "data": [{"name": "cached"}]})
expires, cached = _suggest_cache.get(test_ck, (0, None))
check(now < expires, "cache not expired")
check(cached is not None and cached.get("data") == [{"name": "cached"}], "cache data intact")
# Cleanup
_suggest_cache.pop(test_ck, None)
print("T5 PASS")

# ═══ T6: regeocode rate limiter independent ═══
print("=== T6: regeocode limiter independent ===")
test_ip4 = "test_loc_sec_regeo"
for k in list(_regeocode_rates.keys()):
    if "test_loc_sec" in k:
        del _regeocode_rates[k]

for i in range(3):
    ok = _rate_check(_regeocode_rates, test_ip4, 30, 5000)
    check(ok, f"regeocode request {i+1}/3 allowed")
del _regeocode_rates[test_ip4]
print("T6 PASS")

# ═══ T7: min keyword length ═══
print("=== T7: min keyword check ===")
check(_LOC_SUGGEST_MIN_KEYWORD == 2, "min keyword is 2 chars")
check(len("a") < _LOC_SUGGEST_MIN_KEYWORD, "single char below threshold")
check(len("ab") >= _LOC_SUGGEST_MIN_KEYWORD, "two chars at threshold")
print("T7 PASS")

# ═══ T8: rate map key eviction ═══
print("=== T8: max keys eviction ===")
test_map = {}
for i in range(200):
    _rate_check(test_map, f"evict_test_{i}", 60, 100)
check(len(test_map) <= 100, f"map size capped: {len(test_map)}")
print("T8 PASS")

print(f"\n{'='*50}")
print(f"LOCATION PROXY SECURITY: {p} PASS, {f} FAIL (total {p+f})")
if f: sys.exit(1)
