"""P2-B: /api/auth/token device_id validation + rate limiting behavior tests"""
import sys, os, time as _time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine as _ce, event as _ev
from sqlalchemy.orm import sessionmaker as _sm

_engine = _ce("sqlite://", echo=False)
@_ev.listens_for(_engine, "connect")
def _pragma(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA journal_mode=WAL;")
_TestSession = _sm(bind=_engine)

from models.db_models import User, BillingRecord, SystemConfig
from database import Base
Base.metadata.create_all(bind=_engine)

from routers.auth import get_token, _validate_device_id, _check_token_rate

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _db():
    return _TestSession()


# ═══ T1-T8: _validate_device_id ═══
print("=== T1: empty → 400 ===")
try: _validate_device_id(""); check(False, "should raise")
except Exception as e: check(e.status_code == 400, f"400: {e.status_code}")
print("T1 PASS")

print("=== T2: whitespace → 400 ===")
try: _validate_device_id("        "); check(False, "raise")
except Exception as e: check(e.status_code == 400, f"400: {e.status_code}")
print("T2 PASS")

print("=== T3: len<8 → 400 ===")
try: _validate_device_id("abc1234"); check(False, "raise")
except Exception as e: check(e.status_code == 400, f"400: {e.status_code}")
print("T3 PASS")

print("=== T4: len>100 → 400 ===")
try: _validate_device_id("x"*101); check(False, "raise")
except Exception as e: check(e.status_code == 400, f"400: {e.status_code}")
print("T4 PASS")

print("=== T5: space in middle → 400 ===")
try: _validate_device_id("abc12345 def"); check(False, "raise")
except Exception as e:
    check(e.status_code == 400, "400")
    check("无效字符" in e.detail, "无效字符")
print("T5 PASS")

print("=== T6: Chinese → 400 ===")
try: _validate_device_id("设备ID12345678"); check(False, "raise")
except Exception as e: check(e.status_code == 400, "400")
print("T6 PASS")

print("=== T7: slash → 400 ===")
try: _validate_device_id("abcd/12345678"); check(False, "raise")
except Exception as e: check(e.status_code == 400, "400")
print("T7 PASS")

print("=== T8: @ → 400 ===")
try: _validate_device_id("abcd@12345678"); check(False, "raise")
except Exception as e: check(e.status_code == 400, "400")
print("T8 PASS")

# ═══ T9: valid → strips, returns stripped ═══
print("=== T9: valid → stripped ===")
v = _validate_device_id("MyDevice.123:test-456")
check(v == "MyDevice.123:test-456", f"returns stripped: {v}")
v2 = _validate_device_id("  TestDev20240629.dev  ")
check(v2 == "TestDev20240629.dev", f"stripped: '{v2}'")
print("T9 PASS")

# ═══ T10: boundary lengths → ok ═══
print("=== T10: boundaries → ok ===")
_validate_device_id("abcd1234")
_validate_device_id("x" * 100)
check(True, "8 and 100 ok")
print("T10 PASS")

# ═══ T11: endpoint — valid → 200, stored stripped ═══
print("=== T11: endpoint valid → 200 ===")
db = _db()
r = get_token(device_id="MyDevice.123:test-456", channel="web", db=db)
check(r["token"], "token")
check(r["is_new_user"], "new")
u11 = db.query(User).filter(User.device_id == "MyDevice.123:test-456").first()
check(u11 is not None and u11.device_id == "MyDevice.123:test-456", "stored stripped")
db.close()
print("T11 PASS")

# ═══ T12: endpoint — repeat → existing ═══
print("=== T12: endpoint repeat → existing ===")
db = _db()
r1 = get_token(device_id="RepeatDev001.test", channel="web", db=db)
uid = r1["user"]["id"]
r2 = get_token(device_id="RepeatDev001.test", channel="web", db=db)
check(r2["user"]["id"] == uid, "same id")
check(not r2["is_new_user"], "not new")
db.close()
print("T12 PASS")

# ═══ T13: endpoint — whitespace padding → stripped in DB ═══
print("=== T13: endpoint padded → stripped ===")
db = _db()
r = get_token(device_id="  PaddedDev2024.test  ", channel="web", db=db)
check(r["token"], "token")
u = db.query(User).filter(User.device_id == "PaddedDev2024.test").first()
check(u is not None, "stored without whitespace")
check(True, "response ok")  # device_id validated via DB query above
db.close()
print("T13 PASS")

# ═══ T14: endpoint — empty → 400 ═══
print("=== T14: endpoint empty → 400 ===")
db = _db()
try: get_token(device_id="", channel="web", db=db); check(False, "raise")
except Exception as e: check(e.status_code == 400, "400")
db.close()
print("T14 PASS")

# ═══ T15: endpoint — bad chars → 400 ═══
print("=== T15: endpoint bad chars → 400 ===")
db = _db()
try: get_token(device_id="bad@device.id", channel="web", db=db); check(False, "raise")
except Exception as e: check(e.status_code == 400, "400")
db.close()
print("T15 PASS")


# ═══ T15b: endpoint — exactly 100 chars → 200 (DB field alignment) ═══
print("=== T15b: endpoint 100 chars → 200 ===")
db100 = _db()
dev100 = "d" * 100
r100 = get_token(device_id=dev100, channel="web", db=db100)
check(r100["token"], "token returned for 100-char device_id")
u100 = db100.query(User).filter(User.device_id == dev100).first()
check(u100 is not None, "100-char device_id stored in DB (String(100))")
db100.close()
print("T15b PASS")

# ═══ T15c: endpoint — exactly 101 chars → 400 ═══
print("=== T15c: endpoint 101 chars → 400 ===")
db101 = _db()
try:
    get_token(device_id="d" * 101, channel="web", db=db101)
    check(False, "should raise 400 for 101 chars")
except Exception as e:
    check(e.status_code == 400, f"101 chars → 400: {e.status_code}")
db101.close()
print("T15c PASS")

# ═══ T16: rate limit — device dimension → 429 ═══
print("=== T16: device rate limit → 429 ===")
from routers.auth import _token_device_rate_map, _token_ip_rate_map, _token_rate_lock
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
from routers import auth as _am
_orig_dl = _am._TOKEN_DEVICE_LIMIT_PER_MIN
_am._TOKEN_DEVICE_LIMIT_PER_MIN = 3
hit = False
for i in range(10):
    try:
        _check_token_rate("RateDev001.test", "127.0.0.1")
    except Exception as e:
        if e.status_code == 429:
            hit = True; check("过于频繁" in e.detail, "user-friendly"); break
_am._TOKEN_DEVICE_LIMIT_PER_MIN = _orig_dl
check(hit, "device 429 triggered")
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
print("T16 PASS")

# ═══ T17: rate limit — IP dimension → 429 ═══
print("=== T17: IP rate limit → 429 ===")
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
_orig_il = _am._TOKEN_IP_LIMIT_PER_MIN
_orig_dl2 = _am._TOKEN_DEVICE_LIMIT_PER_MIN
_am._TOKEN_IP_LIMIT_PER_MIN = 4; _am._TOKEN_DEVICE_LIMIT_PER_MIN = 100
hit = False
for i in range(10):
    try:
        _check_token_rate(f"IPDev{i:03d}.test", "127.0.0.1")
    except Exception as e:
        if e.status_code == 429:
            hit = True; break
_am._TOKEN_IP_LIMIT_PER_MIN = _orig_il; _am._TOKEN_DEVICE_LIMIT_PER_MIN = _orig_dl2
check(hit, "IP 429 triggered")
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
print("T17 PASS")

# ═══ T18: different IPs → no cross-limit ═══
print("=== T18: cross-IP → independent ===")
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
_am._TOKEN_DEVICE_LIMIT_PER_MIN = 2
_check_token_rate("CrossDev.test", "10.0.0.1")
_check_token_rate("CrossDev.test", "10.0.0.1")
try: _check_token_rate("CrossDev2.test", "10.0.0.2")
except Exception: check(False, "IP2 should not be limited")
finally: check(True, "IP2 ok")
_am._TOKEN_DEVICE_LIMIT_PER_MIN = _orig_dl
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
print("T18 PASS")

# ═══ T19: different devices same IP → independent ═══
print("=== T19: diff devices → independent ===")
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
_am._TOKEN_DEVICE_LIMIT_PER_MIN = 2; _am._TOKEN_IP_LIMIT_PER_MIN = 100
_check_token_rate("DevA.test", "127.0.0.1")
_check_token_rate("DevA.test", "127.0.0.1")
try: _check_token_rate("DevB.test", "127.0.0.1")
except Exception: check(False, "DevB should not be limited")
finally: check(True, "DevB ok")
_am._TOKEN_DEVICE_LIMIT_PER_MIN = _orig_dl; _am._TOKEN_IP_LIMIT_PER_MIN = _orig_il
with _token_rate_lock:
    _token_device_rate_map.clear()
    _token_ip_rate_map.clear()
print("T19 PASS")

# ═══ T20: pruning + capacity ═══
print("=== T20: pruning + capacity ===")
from routers.auth import _TOKEN_RATE_MAX_KEYS, _prune_token_rate_maps
with _token_rate_lock:
    _token_device_rate_map.clear()
    for i in range(500):
        _token_device_rate_map[f"old:{i}"] = [_time.time() - 120]
    _token_device_rate_map["recent"] = [_time.time()]
    _prune_token_rate_maps(_time.time())
    check(len(_token_device_rate_map) <= 2, f"pruned: {len(_token_device_rate_map)}")
    check("recent" in _token_device_rate_map, "recent kept")
    for i in range(_TOKEN_RATE_MAX_KEYS + 50):
        _token_device_rate_map[f"cap:{i}"] = [_time.time()]
    _prune_token_rate_maps(_time.time())
    check(len(_token_device_rate_map) <= _TOKEN_RATE_MAX_KEYS, f"capped: {len(_token_device_rate_map)}")
    _token_device_rate_map.clear()
print("T20 PASS")


print(f"\n{'='*50}")
print(f"AUTH TOKEN GUARD: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
