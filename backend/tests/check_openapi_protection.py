"""N-P1-04: production /docs /redoc /openapi.json disabled (404), dev available (200)"""
import sys, os, subprocess, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ═══ T1: dev env — /docs /redoc /openapi.json return 200 ═══
print("=== T1: dev has docs (200) ===")
from fastapi.testclient import TestClient
os.environ.setdefault('ENVIRONMENT', 'development')
import main as main_dev
client_dev = TestClient(main_dev.app, raise_server_exceptions=False)
r_docs = client_dev.get('/docs')
check(r_docs.status_code == 200, f"dev /docs: {r_docs.status_code}")
r_redoc = client_dev.get('/redoc')
check(r_redoc.status_code == 200, f"dev /redoc: {r_redoc.status_code}")
r_openapi = client_dev.get('/openapi.json')
check(r_openapi.status_code == 200, f"dev /openapi.json: {r_openapi.status_code}")
print("T1 PASS")

# ═══ T2: production — routes absent and return 404 ═══
print("=== T2: production docs 404 ===")
test_script = r"""
import os, sys
os.environ['ENVIRONMENT'] = 'production'
os.environ['CORS_ORIGINS'] = 'https://example.com'
os.environ['ALLOW_CLIENT_REALDATA_FALLBACK'] = 'false'
sys.path.insert(0, r'{backend_dir}')
import main as m
from fastapi.testclient import TestClient

client = TestClient(m.app, raise_server_exceptions=False)

# verify routes not registered
route_paths = [r.path for r in m.app.routes]
has_docs = '/docs' in route_paths
has_redoc = '/redoc' in route_paths
has_openapi = '/openapi.json' in route_paths
print(f'ROUTES: /docs={has_docs} /redoc={has_redoc} /openapi.json={has_openapi}')

# GET returns 404, NOT 500
r1 = client.get('/docs')
r2 = client.get('/redoc')
r3 = client.get('/openapi.json')
print(f'STATUS: /docs={r1.status_code} /redoc={r2.status_code} /openapi.json={r3.status_code}')
print('OK')
""".replace('{backend_dir}', backend_dir.replace('\\', '/'))

result = subprocess.run(
    [sys.executable, '-c', test_script],
    capture_output=True, text=True, timeout=30,
    cwd=backend_dir
)
check(result.returncode == 0, f"subprocess OK: {result.stderr[:120] if result.stderr else ''}")
check('OK' in result.stdout, f"production import success: {result.stdout[:300]}")
# Routes absent
check('/docs=False' in result.stdout or '/docs=False'.lower() in result.stdout.lower(),
      f"/docs not registered: {result.stdout[:200]}")
check('/redoc=False' in result.stdout or '/redoc=False'.lower() in result.stdout.lower(),
      f"/redoc not registered: {result.stdout[:200]}")
check('/openapi.json=False' in result.stdout or '/openapi.json=False'.lower() in result.stdout.lower(),
      f"/openapi.json not registered: {result.stdout[:200]}")
# 404, not 500
check('/docs=404' in result.stdout, f"/docs 404: {result.stdout[:200]}")
check('/redoc=404' in result.stdout, f"/redoc 404: {result.stdout[:200]}")
check('/openapi.json=404' in result.stdout, f"/openapi.json 404: {result.stdout[:200]}")
check('500' not in result.stdout, "no 500 in production")
print("T2 PASS")

print(f"\n{'='*50}")
print(f"OPENAPI PROTECTION: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
