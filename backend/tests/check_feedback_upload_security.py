"""P1-4/N-P2-03: Feedback security — TestClient + frontend audit + safe cleanup"""
import sys, os, struct, zlib, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
os.environ.setdefault('ENVIRONMENT', 'development')
import main
client = TestClient(main.app, raise_server_exceptions=False)

from database import SessionLocal
from models.db_models import User, Feedback

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")

# unique per-run marker
_MARKER = f"fb_test_{int(time.time()*1000)}"
_created_users = []

def _make_token(user_id, role="user"):
    from auth import create_token
    return create_token(user_id, role)

def _create_user():
    """创建测试用户（自增ID），记录 ID 供 cleanup。"""
    db = SessionLocal()
    u = User(balance_credits=0, membership_tier="free", nickname=_MARKER,
             wx_mini_openid=None, phone=None, wx_openid=_MARKER)
    db.add(u); db.commit(); db.refresh(u)
    uid = u.id
    db.close()
    _created_users.append(uid)
    return uid

_uid_a = _create_user()
_uid_b = _create_user()
_uid_admin = _create_user()
tok = _make_token(_uid_a)
tok_b = _make_token(_uid_b, "user")
admin_tok = _make_token(_uid_admin, "admin")

def _make_png(w=1, h=1):
    def chunk(ctype, data):
        c = ctype + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    raw = b'\x00' + b'\xff\x00\x00' * w
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')

# ═══ T1: fake image (HTML) → 400 ═══
print("=== T1: fake image 400 ===")
r = client.post("/api/feedback/upload", files={"file": ("fake.png", b"<html>x</html>")},
                headers={"Authorization": f"Bearer {tok}"})
check(r.status_code == 400, f"fake: {r.status_code}")
print("T1 PASS")

# ═══ T1b: PNG magic + garbage content → 400 ═══
print("=== T1b: magic+garbage 400 ===")
r1b = client.post("/api/feedback/upload",
    files={"file": ("bad.png", b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)},
    headers={"Authorization": f"Bearer {tok}"})
check(r1b.status_code == 400, f"magic+garbage: {r1b.status_code}")
print("T1b PASS")

# ═══ T2: real PNG → image_key ═══
print("=== T2: real PNG → image_key ===")
r2 = client.post("/api/feedback/upload", files={"file": ("test.png", _make_png())},
                 headers={"Authorization": f"Bearer {tok}"})
check(r2.status_code == 200, f"upload: {r2.status_code}")
d2 = r2.json()
check(d2.get("ok"), f"ok: {d2}")
check("image_key" in d2, "has image_key")
img_key = d2.get("image_key", "")
check("/assets/" not in img_key, "no /assets/")
check(img_key.startswith("fb_") and img_key.endswith(".png"), f"key: {img_key}")
print("T2 PASS")

# ═══ T3: oversize → 400 ═══
print("=== T3: oversize 400 ===")
r3 = client.post("/api/feedback/upload",
    files={"file": ("big.png", _make_png() + b'\x00' * (3*1024*1024))},
    headers={"Authorization": f"Bearer {tok}"})
check(r3.status_code == 400, f"oversize: {r3.status_code}")
print("T3 PASS")

# ═══ T4: submit + my list → signed URLs ═══
print("=== T4: submit + my list ===")
r4a = client.post("/api/feedback", data={
    "content": "反馈测试内容必须够十个字才行", "contact": "", "image_keys": img_key},
    headers={"Authorization": f"Bearer {tok}"})
check(r4a.status_code == 200, f"submit: {r4a.status_code}")
fb_id = r4a.json().get("feedback_id", 0)

r4b = client.get("/api/feedback/my", headers={"Authorization": f"Bearer {tok}"})
check(r4b.status_code == 200, f"my list: {r4b.status_code}")
imgs = (r4b.json().get("feedbacks", [{}])[0].get("images", []))
signed_url = imgs[0] if imgs else ""
check("/assets/" not in signed_url, f"no /assets/: {signed_url}")
check("simage" in signed_url or "sig=" in signed_url, f"signed: {signed_url}")
print("T4 PASS")

# ═══ T5: signed image accessible + nosniff ═══
print("=== T5: signed image ===")
r5 = client.get(signed_url)
check(r5.status_code == 200, f"signed: {r5.status_code}")
check("nosniff" in r5.headers.get("x-content-type-options", ""), "nosniff")
check("image/" in r5.headers.get("content-type", ""), "image ct")
print("T5 PASS")

# ═══ T6: unauth → 401/403 ═══
print("=== T6: unauth ===")
r6 = client.get(f"/api/feedback/image/{fb_id}/0")
check(r6.status_code in (401, 403), f"unauth: {r6.status_code}")
print("T6 PASS")

# ═══ T7: cross-user → 403 ═══
print("=== T7: cross-user ===")
r7 = client.get(f"/api/feedback/image/{fb_id}/0", headers={"Authorization": f"Bearer {tok_b}"})
check(r7.status_code == 403, f"cross: {r7.status_code}")
print("T7 PASS")

# ═══ T8: admin → 200 ═══
print("=== T8: admin ===")
r8 = client.get(f"/api/feedback/admin/image/{fb_id}/0", headers={"Authorization": f"Bearer {admin_tok}"})
check(r8.status_code == 200, f"admin: {r8.status_code}")
print("T8 PASS")

# ═══ T9: path traversal ═══
print("=== T9: path traversal ===")
from routers.feedback import _safe_basename
check(_safe_basename("../etc") == "", "../")
check(_safe_basename("fb_a\\..\\x") == "", "..\\")
check(_safe_basename("fb_a%2e%2e") == "", "urlenc")
check(_safe_basename("fb_abc123.png") == "fb_abc123.png", "valid")
print("T9 PASS")

# ═══ T10: admin list safe ═══
print("=== T10: admin list ===")
r10 = client.get("/api/feedback/admin/list", headers={"Authorization": f"Bearer {admin_tok}"})
check(r10.status_code == 200, f"list: {r10.status_code}")
for af in r10.json().get("feedbacks", []):
    for img in af.get("images", []):
        check("/assets/" not in str(img), f"no /assets/: {img}")
print("T10 PASS")

# ═══ T11: frontend audit ═══
print("=== T11: frontend audit ===")
fb_vue_path = os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src', 'pages', 'profile', 'feedback.vue')
fb_vue = open(fb_vue_path, 'r', encoding='utf-8').read()
check("image_key" in fb_vue or "d.image_key" in fb_vue, "reads image_key from upload")
check("image_keys" in fb_vue, "submits image_keys field")
check("image_urls" not in fb_vue, "no longer submits image_urls")
check("tempFiles" in fb_vue or "tempFilePaths" in fb_vue, "uses tempFiles for size check")
check("2MB" in fb_vue or "2 * 1024 * 1024" in fb_vue, "has 2MB limit")
check("PNG" in fb_vue or "JPG" in fb_vue or "WebP" in fb_vue, "format hint present")
print("T11 PASS")

# ── cleanup: only test-created users ──
db_c = SessionLocal()
for uid in _created_users:
    db_c.query(Feedback).filter(Feedback.user_id == uid).delete()
    db_c.query(User).filter(User.id == uid).delete()
db_c.commit()
db_c.close()

print(f"\n{'='*50}")
print(f"FEEDBACK UPLOAD SECURITY: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
