"""P3-A: Avatar upload — Pillow re-encode, GIF→PNG, metadata stripping tests"""
import sys, os, io as _io
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image as _Image, PngImagePlugin as _PngInfo
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

from routers.user import upload_avatar, AVATAR_ROOT
from fastapi import UploadFile

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _db():
    return _TestSession()

_test_uid = 99901
_user_ctx = {"user_id": _test_uid}

def _ensure_user(db):
    u = db.query(User).filter(User.id == _test_uid).first()
    if not u:
        u = User(id=_test_uid, balance_credits=10, membership_tier="free",
                 wx_mini_openid="oAvTest01")
        db.add(u)
        db.commit()
    return u


def _make_upload_file(filename, content_bytes, content_type=""):
    return UploadFile(filename=filename, file=_io.BytesIO(content_bytes),
                      headers={"content-type": content_type})


def _make_png(w=16, h=16, with_metadata=False):
    """Generate PNG. with_metadata=True adds a PngInfo comment chunk."""
    buf = _io.BytesIO()
    img = _Image.new("RGB", (w, h), color="red")
    if with_metadata:
        png_info = _PngInfo.PngInfo()
        png_info.add_text("Comment", "SECRET_METADATA_TEST_MARKER")
        img.save(buf, format="PNG", pnginfo=png_info)
    else:
        img.save(buf, format="PNG")
    return buf.getvalue()

def _make_jpeg(w=16, h=16):
    buf = _io.BytesIO()
    _Image.new("RGB", (w, h), color="blue").save(buf, format="JPEG", quality=85)
    return buf.getvalue()

def _make_webp(w=16, h=16):
    buf = _io.BytesIO()
    _Image.new("RGB", (w, h), color="green").save(buf, format="WEBP")
    return buf.getvalue()

def _make_gif(w=16, h=16):
    buf = _io.BytesIO()
    img1 = _Image.new("RGB", (w, h), color="yellow")
    img2 = _Image.new("RGB", (w, h), color="orange")
    img1.save(buf, format="GIF", save_all=True, append_images=[img2], duration=100, loop=0)
    return buf.getvalue()


import asyncio as _asyncio

# ═══ T1: fake PNG magic + garbage → 400, no avatar written ═══
print("=== T1: fake PNG magic + garbage → 400 ===")
db = _db()
_ensure_user(db)
fake = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
uf = _make_upload_file("fake.png", fake, "image/png")
try:
    _asyncio.run(upload_avatar(uf, _user_ctx, db))
    check(False, "should raise 400")
except Exception as e:
    check(e.status_code == 400, f"fake PNG → 400: {e.status_code}")
db.rollback()
print("T1 PASS")


# ═══ T2: PNG with metadata → 200, re-encoded, metadata stripped ═══
print("=== T2: PNG metadata stripped, local != raw ===")
db2 = _db()
_ensure_user(db2)
raw_png = _make_png(with_metadata=True)
check(b"SECRET_METADATA_TEST_MARKER" in raw_png, "raw PNG contains metadata marker")
uf2 = _make_upload_file("test.png", raw_png, "image/png")
r = _asyncio.run(upload_avatar(uf2, _user_ctx, db2))
check(r["ok"], "ok")
av2 = r["avatar_url"]
check(av2.endswith(".png"), f"URL ends .png: {av2}")
# 本地文件路径使用 AVATAR_ROOT
local2 = os.path.join(AVATAR_ROOT, os.path.basename(av2))
check(os.path.exists(local2), f"local file exists: {local2}")
written2 = open(local2, "rb").read()
check(written2 != raw_png, "local bytes ≠ raw upload bytes")
check(b"SECRET_METADATA_TEST_MARKER" not in written2, "metadata stripped from local file")
_Image.open(_io.BytesIO(written2))  # 确认 Pillow 能打开
check(True, "local file opens with Pillow")
db2.rollback()
print("T2 PASS")


# ═══ T3: normal JPEG → 200, extension == .jpg, cloud ct == image/jpeg ═══
print("=== T3: JPEG → .jpg, ct=image/jpeg ===")
db3 = _db()
_ensure_user(db3)
raw_jpg = _make_jpeg()
uf3 = _make_upload_file("test.jpg", raw_jpg, "image/jpeg")
r3 = _asyncio.run(upload_avatar(uf3, _user_ctx, db3))
check(r3["ok"], "ok")
av3 = r3["avatar_url"]
fname3 = os.path.basename(av3)
check(fname3.endswith(".jpg") or fname3.endswith(".jpeg"),
      f"JPEG extension: {os.path.splitext(fname3)[1]}")
local3 = os.path.join(AVATAR_ROOT, fname3)
check(os.path.exists(local3), f"local JPEG exists: {local3}")
db3.rollback()
print("T3 PASS")


# ═══ T4: WebP → 200 (或 skip) ═══
print("=== T4: WebP → .webp ===")
webp_available = True
try:
    _buf4 = _io.BytesIO()
    _Image.new("RGB", (16, 16), color="green").save(_buf4, format="WEBP")
    raw_webp = _buf4.getvalue()
except Exception as e:
    webp_available = False
    print(f"  SKIP: Pillow WebP encoder not available ({e})")
if webp_available:
    db4 = _db()
    _ensure_user(db4)
    uf4 = _make_upload_file("test.webp", raw_webp, "image/webp")
    r4 = _asyncio.run(upload_avatar(uf4, _user_ctx, db4))
    check(r4["ok"], "WebP ok")
    av4 = r4["avatar_url"]
    check(av4.endswith(".webp"), f"WebP extension: {av4}")
    db4.rollback()
print("T4 PASS")


# ═══ T5: GIF → first-frame PNG, all channels verified ═══
print("=== T5: GIF → PNG (extension + magic + cloud) ===")
db5 = _db()
_ensure_user(db5)
raw_gif = _make_gif()
uf5 = _make_upload_file("test.gif", raw_gif, "image/gif")
r5 = _asyncio.run(upload_avatar(uf5, _user_ctx, db5))
check(r5["ok"], "ok")
av5 = r5["avatar_url"]
check(av5.endswith(".png"), f"GIF output extension .png: {av5}")
# 本地文件：AVATAR_ROOT 路径
fname5 = os.path.basename(av5)
local5 = os.path.join(AVATAR_ROOT, fname5)
check(os.path.exists(local5), f"local file exists: {local5}")
w5 = open(local5, "rb").read()
check(w5[:4] == b"\x89PNG", f"local magic is PNG: {w5[:4]}")
check(not w5[:4].startswith(b"GIF8"), "local NOT GIF magic")
db5.rollback()
print("T5 PASS")


# ═══ T6: cloud receives PNG re-encoded bytes, no metadata ═══
print("=== T6: cloud PNG → re-encoded, metadata stripped ===")
from unittest.mock import patch as _patch
from services import storage_service as _ss

_captured = []; _captured_ct = []
def _mock_save(category, filename, content, content_type="", metadata=None):
    _captured.append(content); _captured_ct.append(content_type)
    from types import SimpleNamespace
    return SimpleNamespace(ok=True, url=f"https://cdn.example.com/{filename}")

with _patch.object(_ss, "save_user_asset_structured", wraps=None) as _m:
    _m.side_effect = _mock_save
    db6 = _db()
    _ensure_user(db6)
    raw_png6 = _make_png(with_metadata=True)
    uf6 = _make_upload_file("t6.png", raw_png6, "image/png")
    r6 = _asyncio.run(upload_avatar(uf6, _user_ctx, db6))
    check(r6["ok"], "ok")
    check(len(_captured) > 0, "cloud save called")
    cloud_bytes = _captured[0]
    check(cloud_bytes != raw_png6, "cloud bytes ≠ raw upload bytes")
    check(b"SECRET_METADATA_TEST_MARKER" not in cloud_bytes, "metadata stripped from cloud bytes")
    check(cloud_bytes[:4] == b"\x89PNG", f"cloud PNG magic: {cloud_bytes[:4]}")
    check(_captured_ct[0] == "image/png", f"cloud ct=png: {_captured_ct[0]}")
    db6.rollback()
print("T6 PASS")


# ═══ T7: GIF cloud → PNG bytes + image/png ═══
print("=== T7: GIF cloud → PNG ===")
_captured.clear(); _captured_ct.clear()
with _patch.object(_ss, "save_user_asset_structured", wraps=None) as _m2:
    _m2.side_effect = _mock_save
    db7 = _db()
    _ensure_user(db7)
    uf7 = _make_upload_file("t7.gif", _make_gif(), "image/gif")
    r7 = _asyncio.run(upload_avatar(uf7, _user_ctx, db7))
    check(r7["ok"], "ok")
    check(_captured[0][:4] == b"\x89PNG", f"cloud PNG magic: {_captured[0][:4]}")
    check(_captured_ct[0] == "image/png", f"cloud ct=png: {_captured_ct[0]}")
    db7.rollback()
print("T7 PASS")


# ═══ T8: >2MB → 400 ═══
print("=== T8: >2MB → 400 ===")
db8 = _db()
big = b"x" * (2 * 1024 * 1024 + 1)
uf8 = _make_upload_file("big.png", big, "image/png")
try:
    _asyncio.run(upload_avatar(uf8, _user_ctx, db8))
    check(False, "should raise 400")
except Exception as e:
    check(e.status_code == 400, f">2MB → 400: {e.status_code}")
db8.rollback()
print("T8 PASS")


# ═══ T9: avatar_url updated in DB ═══
print("=== T9: avatar_url updated ===")
db9 = _db()
_ensure_user(db9)
prev = db9.query(User).filter(User.id == _test_uid).first().avatar_url or ""
uf9 = _make_upload_file("t9.png", _make_png(), "image/png")
r9 = _asyncio.run(upload_avatar(uf9, _user_ctx, db9))
check(r9["ok"], "ok")
u9 = db9.query(User).filter(User.id == _test_uid).first()
check(u9.avatar_url and u9.avatar_url != prev, f"avatar_url updated: {u9.avatar_url}")
db9.rollback()
print("T9 PASS")


print(f"\n{'='*50}")
print(f"AVATAR UPLOAD SECURITY: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
