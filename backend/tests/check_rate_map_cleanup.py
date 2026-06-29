"""P1-8: Rate map cleanup — TTL prune + max keys eviction"""
import sys, os, time, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


# ═══ T1: _prune_rate_map removes stale entries ═══
print("=== T1: prune stale ===")
from routers.auth import _prune_rate_map, _LOGIN_RATE_WINDOW, _LOGIN_RATE_MAX_KEYS
now = time.time()
rmap = {"a": [now - 120], "b": [now - 5], "c": [now - 10]}
_prune_rate_map(rmap, now, _LOGIN_RATE_WINDOW, _LOGIN_RATE_MAX_KEYS)
check("a" not in rmap, f"stale 'a' removed: {rmap.keys()}")
check("b" in rmap, f"fresh 'b' kept: {rmap.keys()}")
check("c" in rmap, f"fresh 'c' kept: {rmap.keys()}")
print("T1 PASS")

# ═══ T2: _prune_rate_map evicts oldest when over max ═══
print("=== T2: evict oldest ===")
rmap2 = {}
for i in range(100):
    rmap2[f"ip_{i}"] = [now - i * 2]
_prune_rate_map(rmap2, now, _LOGIN_RATE_WINDOW, 10)
check(len(rmap2) <= 10, f"capped at 10: {len(rmap2)}")
check("ip_0" in rmap2, "newest kept")
print("T2 PASS")

# ═══ T3: auth _check_user_login_rate still works ═══
print("=== T3: auth login rate ===")
from routers.auth import _check_user_login_rate, _login_rate_map, _login_rate_lock
with _login_rate_lock:
    _login_rate_map.clear()
from routers.auth import _LOGIN_RATE_MAX
for i in range(_LOGIN_RATE_MAX):
    check(_check_user_login_rate("user_t3"), f"attempt {i+1}/{_LOGIN_RATE_MAX} allowed")
check(not _check_user_login_rate("user_t3"), f"rejected after {_LOGIN_RATE_MAX}")
with _login_rate_lock:
    _login_rate_map.clear()
print("T3 PASS")

# ═══ T4: admin _check_login_rate still works ═══
print("=== T4: admin login rate ===")
from routers.admin import _check_login_rate, _login_attempts, _login_lock
with _login_lock:
    _login_attempts.clear()
for i in range(3):
    check(_check_login_rate("ip_t4"), f"attempt {i+1} allowed")
with _login_lock:
    _login_attempts.clear()
print("T4 PASS")

# ═══ T5: CDK rate — allows then rejects ═══
print("=== T5: CDK rate ===")
from routers.admin import _cdk_rate_map, _cdk_rate_lock, _check_cdk_rate, _CDK_RATE_LIMIT, _CDK_MAX_KEYS
from fastapi import HTTPException
from unittest.mock import MagicMock
with _cdk_rate_lock:
    _cdk_rate_map.clear()
# allow up to limit from same IP
for i in range(_CDK_RATE_LIMIT):
    mock_req = MagicMock()
    mock_req.client = MagicMock()
    mock_req.client.host = "cdk_t5_same"
    mock_req.headers = {}
    try:
        _check_cdk_rate(mock_req)
        check(True, f"CDK attempt {i+1}/{_CDK_RATE_LIMIT} allowed")
    except HTTPException:
        check(False, f"CDK attempt {i+1} should be allowed")
# next one from same IP should 429
try:
    _check_cdk_rate(mock_req)
    check(False, "CDK over limit should raise 429")
except HTTPException as e:
    check(e.status_code == 429, f"CDK over limit 429: {e.status_code}")
with _cdk_rate_lock:
    _cdk_rate_map.clear()
print("T5 PASS")

# ═══ T7: auth map stays ≤ max after full insert ═══
print("=== T7: auth boundary ===")
from routers.auth import _login_rate_map, _login_rate_lock, _check_user_login_rate, _LOGIN_RATE_MAX_KEYS, _LOGIN_RATE_WINDOW
now = time.time()
with _login_rate_lock:
    _login_rate_map.clear()
    for i in range(_LOGIN_RATE_MAX_KEYS):
        _login_rate_map[f"boundary_{i}"] = [now - 1]
_check_user_login_rate("new_key")
with _login_rate_lock:
    check(len(_login_rate_map) <= _LOGIN_RATE_MAX_KEYS,
          f"auth map {len(_login_rate_map)} <= {_LOGIN_RATE_MAX_KEYS}")
    _login_rate_map.clear()
print("T7 PASS")

# ═══ T8: admin login map stays ≤ max after full insert ═══
print("=== T8: admin boundary ===")
from routers.admin import _login_attempts, _login_lock, _check_login_rate, _LOGIN_MAX_KEYS, _LOGIN_RATE_WINDOW as _ADM_WINDOW
now = time.time()
with _login_lock:
    _login_attempts.clear()
    for i in range(_LOGIN_MAX_KEYS):
        _login_attempts[f"boundary_{i}"] = [now - 1]
_check_login_rate("new_ip")
with _login_lock:
    check(len(_login_attempts) <= _LOGIN_MAX_KEYS,
          f"admin map {len(_login_attempts)} <= {_LOGIN_MAX_KEYS}")
    _login_attempts.clear()
print("T8 PASS")

# ═══ T9: CDK map stays ≤ max after full insert ═══
print("=== T9: CDK boundary ===")
from routers.admin import _CDK_RATE_WINDOW
now = time.time()
with _cdk_rate_lock:
    _cdk_rate_map.clear()
    for i in range(_CDK_MAX_KEYS):
        _cdk_rate_map[f"boundary_{i}"] = [now - 1]
mock_req = MagicMock()
mock_req.client = MagicMock()
mock_req.client.host = "cdk_new_ip"
mock_req.headers = {}
try:
    _check_cdk_rate(mock_req)
except HTTPException:
    pass
with _cdk_rate_lock:
    check(len(_cdk_rate_map) <= _CDK_MAX_KEYS,
          f"CDK map {len(_cdk_rate_map)} <= {_CDK_MAX_KEYS}")
    _cdk_rate_map.clear()
print("T9 PASS")

# ═══ T6: source audit — max keys present ═══
print("=== T6: source audit ===")
auth_src = open(os.path.join(os.path.dirname(__file__), '..', 'routers', 'auth.py'), 'r', encoding='utf-8').read()
admin_src = open(os.path.join(os.path.dirname(__file__), '..', 'routers', 'admin.py'), 'r', encoding='utf-8').read()
check("_prune_rate_map" in auth_src, "auth has prune")
check("_LOGIN_RATE_MAX_KEYS" in auth_src, "auth has max keys")
check("_prune_admin_rate_map" in admin_src, "admin has prune")
check("_LOGIN_MAX_KEYS" in admin_src, "admin login has max keys")
check("_CDK_MAX_KEYS" in admin_src, "cdk has max keys")
check("_cdk_rate_lock" in admin_src, "cdk has lock")
print("T6 PASS")

print(f"\n{'='*50}")
print(f"RATE MAP CLEANUP: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
