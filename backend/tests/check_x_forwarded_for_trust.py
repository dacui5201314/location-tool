"""N-P1-05: X-Forwarded-For trust boundary — only trusted proxy XFF accepted"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock
from services.client_ip import get_client_ip, _is_trusted, _TRUSTED_PROXIES

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _req(remote="10.0.0.1", xff=None):
    r = MagicMock()
    r.client = MagicMock()
    r.client.host = remote
    r.headers = {}
    if xff is not None:
        r.headers["X-Forwarded-For"] = xff
    return r


# ═══ T1: direct request with forged XFF → remote_addr used ═══
print("=== T1: forged XFF ignored ===")
r1 = _req(remote="1.2.3.4", xff="10.0.0.1")
ip1 = get_client_ip(r1)
check(ip1 == "1.2.3.4", f"forged XFF ignored, uses remote: {ip1}")
print("T1 PASS")

# ═══ T2: trusted proxy (127.0.0.1) with XFF → XFF used ═══
print("=== T2: trusted proxy XFF accepted ===")
r2 = _req(remote="127.0.0.1", xff="1.2.3.4")
ip2 = get_client_ip(r2)
check(ip2 == "1.2.3.4", f"trusted proxy XFF used: {ip2}")
print("T2 PASS")

# ═══ T3: XFF chain → first valid client ═══
print("=== T3: XFF chain ===")
r3 = _req(remote="127.0.0.1", xff="1.2.3.4, 10.0.0.1, 172.16.0.1")
ip3 = get_client_ip(r3)
check(ip3 == "1.2.3.4", f"first XFF used: {ip3}")
print("T3 PASS")

# ═══ T4: empty XFF → remote_addr ═══
print("=== T4: empty XFF ===")
r4 = _req(remote="127.0.0.1", xff="")
ip4 = get_client_ip(r4)
check(ip4 == "127.0.0.1", f"empty XFF fallback: {ip4}")
r4b = _req(remote="127.0.0.1", xff="unknown, , ")
ip4b = get_client_ip(r4b)
check(ip4b == "127.0.0.1", f"invalid XFF fallback: {ip4b}")
print("T4 PASS")

# ═══ T4b: request.client=None → no XFF ═══
print("=== T4b: missing client ===")
r4c = _req(remote=None, xff="8.8.8.8")
r4c.client = None
ip4c = get_client_ip(r4c)
check(ip4c == "unknown", f"client=None returns unknown, not XFF: {ip4c}")
r4d = _req(remote="", xff="8.8.8.8")
r4d.client.host = ""
ip4d = get_client_ip(r4d)
check(ip4d == "unknown", f"empty host returns unknown: {ip4d}")
print("T4b PASS")

# ═══ T5: is_trusted and TRUSTED_PROXY_IPS ═══
print("=== T5: trust checks ===")
check(_is_trusted("127.0.0.1"), "loopback trusted")
check(_is_trusted("::1"), "::1 trusted")
check(not _is_trusted("1.2.3.4"), "external not trusted")
check(not _is_trusted(""), "empty not trusted")
check(len(_TRUSTED_PROXIES) >= 2, f"at least 2 trusted nets: {len(_TRUSTED_PROXIES)}")
print("T5 PASS")

# ═══ T6: callers use get_client_ip, no raw XFF ═══
print("=== T6: callers audit ===")
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for fname, label in [
    ("routers/auth.py", "auth"),
    ("routers/admin.py", "admin"),
    ("routers/location.py", "location"),
    ("main.py", "main share"),
]:
    path = os.path.join(backend_dir, fname)
    src = open(path, 'r', encoding='utf-8').read()
    check("get_client_ip" in src, f"{label} uses get_client_ip")
    check('headers.get("X-Forwarded-For")' not in src and "headers.get('X-Forwarded-For')" not in src,
          f"{label} no raw XFF header read")
    check("request.client.host" not in src,
          f"{label} no raw request.client.host")
print("T6 PASS")

# ═══ T6b: custom TRUSTED_PROXY_IPS via subprocess ═══
print("=== T6b: custom TRUSTED_PROXY_IPS ===")
import subprocess
test_script = r"""
import os, sys
os.environ['TRUSTED_PROXY_IPS'] = '10.0.0.0/24'
sys.path.insert(0, r'{backend_dir}')
from services.client_ip import _is_trusted, _TRUSTED_PROXIES
print(f'trusted_nets={len(_TRUSTED_PROXIES)}')
print(f'10.0.0.1={_is_trusted("10.0.0.1")}')
print(f'10.0.1.1={_is_trusted("10.0.1.1")}')
print(f'127.0.0.1={_is_trusted("127.0.0.1")}')
print('OK')
""".replace('{backend_dir}', backend_dir.replace('\\', '/'))
result = subprocess.run(
    [sys.executable, '-c', test_script],
    capture_output=True, text=True, timeout=30,
    cwd=backend_dir
)
check(result.returncode == 0, f"subprocess OK: {result.stderr[:100] if result.stderr else ''}")
check('10.0.0.1=True' in result.stdout, f"10.0.0.0/24 trusts 10.0.0.1: {result.stdout[:200]}")
check('10.0.1.1=False' in result.stdout, f"10.0.0.0/24 rejects 10.0.1.1: {result.stdout[:200]}")
check('OK' in result.stdout, f"subprocess success: {result.stdout[:200]}")
print("T6b PASS")

# ═══ T7: README Nginx XFF fix ═══
print("=== T7: README Nginx ===")
readme = open(os.path.join(backend_dir, '..', 'README.md'), 'r', encoding='utf-8').read()
check("proxy_set_header X-Forwarded-For $remote_addr" in readme,
      "README Nginx uses $remote_addr for XFF")
check("$proxy_add_x_forwarded_for" not in readme.replace(
    "不可使用 `$proxy_add_x_forwarded_for`", ""),
      "README Nginx example does not use $proxy_add_x_forwarded_for")
env_ex = open(os.path.join(backend_dir, '.env.example'), 'r', encoding='utf-8').read()
check("TRUSTED_PROXY_IPS" in env_ex, ".env.example has TRUSTED_PROXY_IPS")
print("T7 PASS")

print(f"\n{'='*50}")
print(f"X-FORWARDED-FOR TRUST: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
