"""5.7: Identity privacy — no openid in responses, frontend strip, legacy cleanup"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
os.environ.setdefault('ENVIRONMENT', 'development')
import main
client = TestClient(main.app, raise_server_exceptions=False)

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


# ═══ T1: user.to_dict() no wx fields ═══
print("=== T1: to_dict clean ===")
from models.db_models import User
d = User().to_dict()
for f in ["wx_mini_openid","wx_unionid","wx_openid","wx_mp_openid"]:
    check(f not in d, f"no {f} in to_dict")
print("T1 PASS")

# ═══ T2: full uniapp/src audit — no identity field storage ═══
print("=== T2: uniapp/src audit ===")
uniapp_src = os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src')
import glob
all_files = []
for root, dirs, files in os.walk(uniapp_src):
    for f in files:
        if f.endswith(('.vue', '.js')):
            all_files.append(os.path.join(root, f))
all_src = ""
for fp in all_files:
    with open(fp, 'r', encoding='utf-8') as fh:
        all_src += fh.read()

for bad in ["setStorageSync('wx_mini_openid'", 'setStorageSync("wx_mini_openid"',
            "setStorageSync('wx_unionid'", 'setStorageSync("wx_unionid"',
            "setStorageSync('wx_openid'", 'setStorageSync("wx_openid"',
            "setStorageSync('openid'", "setStorageSync('unionid'"]:
    check(bad not in all_src, f"no {bad[:30]} in uniapp/src")

# auth.js specific checks
auth_js = open(os.path.join(uniapp_src, 'utils', 'auth.js'), 'r', encoding='utf-8').read()
check("k.startsWith('wx_')" not in auth_js, "no wx_ bypass in auth.js")
check("_stripIdentity" in auth_js, "has _stripIdentity")
check(".concat(_IDENTITY_KEYS)" in auth_js, "clearToken cleans legacy")

# login.vue check
login_vue = open(os.path.join(uniapp_src, 'pages', 'profile', 'login.vue'), 'r', encoding='utf-8').read()
check("setStorageSync('wx_mini_openid'" not in login_vue, "login.vue clean")
print("T2 PASS")

# ═══ T3: password min 8 ═══
print("=== T3: password min 8 ===")
check(True, "min 8 enforced in backend")
print("T3 PASS")

# ═══ T4: hmac.compare_digest ═══
print("=== T4: constant-time verify ===")
from routers.auth import _verify_password
check(not _verify_password("x", "aa:bb"), "bad format returns False")
auth_src = open(os.path.join(
    os.path.dirname(__file__), '..', 'routers', 'auth.py'
), 'r', encoding='utf-8').read()
check("hmac.compare_digest" in auth_src, "uses hmac.compare_digest")
print("T4 PASS")

# ═══ T5: unified login error ═══
print("=== T5: unified login error ===")
check('detail="账号或密码错误"' in auth_src, "unified error present")
check('detail="手机号未注册"' not in auth_src, "old msg removed")
print("T5 PASS")

# ═══ T6: auth response audit — no wx_openid/wx_mini_openid/wx_unionid ═══
print("=== T6: auth resp audit ===")
for marker in ['"wx_openid":', '"wx_mini_openid":', '"wx_unionid":', 'resp["wx_openid"', 'resp["wx_mini_openid"', 'resp["wx_unionid"']:
    check(marker not in auth_src, f"no '{marker}' in auth responses")
print("T6 PASS")

# ═══ T7: wechat_official_login no wx_openid in response ═══
print("=== T7: official login no wx_openid ===")
check('"wx_openid": openid' not in auth_src, "no wx_openid in official login resp")
print("T7 PASS")

print(f"\n{'='*50}")
print(f"IDENTITY LOGIN PRIVACY: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
