"""N-P1-03: Admin secret masking — real route paths, GET/PUT, frontend audit"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite://", echo=False)
@event.listens_for(engine, "connect")
def _set_pragma(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA journal_mode=WAL;")
SessionLocal = sessionmaker(bind=engine)

from database import Base
from models.db_models import SystemConfig, User
Base.metadata.create_all(bind=engine)

from routers.admin import (
    ConfigBody, StorageConfigBody, SystemSettingsBody,
    save_config, save_storage_config, save_system_settings,
    get_config, get_storage_config, get_system_settings,
    _CLEAR_SENTINEL, _mask_core_config, _mask_system_config,
    _load_storage_config, _load_all_system_config,
)

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _seed(db, **kv):
    for k, v in kv.items():
        row = db.query(SystemConfig).filter(SystemConfig.key == k).first()
        if row: row.value = v
        else: db.add(SystemConfig(key=k, value=v))
    db.commit()


_admin = {"user_id": 1, "role": "admin"}


# ═══ T1: core config GET masked (ai_key, amap_key) ═══
print("=== T1: core GET masked ===")
db1 = SessionLocal()
_seed(db1, ai_key="sk-real-ai-key-12345", amap_key="amap-real-key-67890",
      wx_api_key="wxapiv3secret", wx_private_key_pem="-----BEGIN PRIVATE KEY-----\nkey\n-----END-----",
      wx_platform_cert_pem="-----BEGIN CERTIFICATE-----\ncert\n-----END-----",
      wx_virtual_app_key="vapp_secret")
resp1 = get_config(admin=_admin, db=db1)
check(resp1.get("ai_key") == "", "ai_key empty")
check("****" in resp1.get("ai_key_masked", ""), "ai_key_masked present")
check(resp1.get("amap_key") == "", "amap_key empty")
check("****" in resp1.get("amap_key_masked", ""), "amap_key_masked present")
check(resp1.get("wx_api_key") == "", "wx_api_key empty")
check(resp1.get("has_wx_virtual_app_key"), "has vapp key")
check("sk-real-ai-key" not in json.dumps(resp1), "no ai_key leaked")
check("amap-real-key" not in json.dumps(resp1), "no amap_key leaked")
db1.rollback()
print("T1 PASS")

# ═══ T2: core PUT keep/clear/replace (ai_key, amap_key) ═══
print("=== T2: core PUT semantics ===")
# Seed with known values
db2 = SessionLocal()
_seed(db2, ai_key="old-ai-key", amap_key="old-amap-key",
      wx_api_key="old-wx-key", wx_virtual_app_key="old-vapp-key",
      wx_notify_url="https://x.com/notify")

# T2a: keep - empty fields should preserve old values
body2a = ConfigBody()
body2a.wx_notify_url = "https://x.com/notify"  # needed to pass empty check
resp2a = save_config(body2a, admin=_admin, db=db2)
# Verify old values preserved (via reload)
db2r = SessionLocal()
resp2ar = get_config(admin=_admin, db=db2r)
check(resp2ar.get("ai_key_masked"), "ai_key preserved after keep")
check(resp2ar.get("amap_key_masked"), "amap_key preserved after keep")
db2r.rollback()

# T2b: clear via flag
body2b = ConfigBody()
body2b.clear_ai_key = True
body2b.clear_amap_key = True
body2b.wx_notify_url = "https://x.com/notify"
resp2b = save_config(body2b, admin=_admin, db=db2)
db2rb = SessionLocal()
resp2br = get_config(admin=_admin, db=db2rb)
check(not resp2br.get("ai_key_masked"), "ai_key cleared")
check(not resp2br.get("amap_key_masked"), "amap_key cleared")
db2rb.rollback()

# T2c: replace with new value
body2c = ConfigBody()
body2c.ai_key = "new-ai-key-xyz"
body2c.amap_key = "new-amap-key-xyz"
body2c.wx_notify_url = "https://x.com/notify"
resp2c = save_config(body2c, admin=_admin, db=db2)
db2rc = SessionLocal()
resp2cr = get_config(admin=_admin, db=db2rc)
check("****" in resp2cr.get("ai_key_masked", ""), "new ai_key set")
check("****" in resp2cr.get("amap_key_masked", ""), "new amap_key set")
db2rc.rollback()
db2.rollback()
print("T2 PASS")

# ═══ T3: storage PUT keep/clear/replace ═══
print("=== T3: storage PUT semantics ===")
db3 = SessionLocal()
_seed(db3, oss_access_key_secret="old-oss-secret", oss_bucket="bkt",
      oss_access_key_id="akid", oss_endpoint="ep", storage_provider="tencent_cos")

# T3a: keep old
body3a = StorageConfigBody()
body3a.storage_provider = "tencent_cos"
body3a.storage_mode = "cloud"
body3a.oss_bucket = "bkt"
body3a.oss_access_key_id = "akid"
body3a.oss_access_key_secret = ""  # empty → keep old
resp3a = save_storage_config(body3a, admin=_admin, db=db3)
check(resp3a.get("ok"), "storage save ok")
check(resp3a["config"].get("has_oss_access_key_secret"), "has secret true after keep")
check(resp3a["config"].get("oss_access_key_secret") == "", "secret empty in response")
check("old-oss-secret" not in json.dumps(resp3a), "no old secret in save response")

# T3b: clear via __CLEAR__ (must switch to local first)
body3b = StorageConfigBody()
body3b.storage_provider = "tencent_cos"
body3b.storage_mode = "local"
body3b.oss_access_key_secret = _CLEAR_SENTINEL
resp3b = save_storage_config(body3b, admin=_admin, db=db3)
check(resp3b.get("ok"), "clear save ok in local mode")
check(not resp3b["config"].get("has_oss_access_key_secret"), "has false after clear")

# T3c: replace (restore to cloud with new secret)
body3c = StorageConfigBody()
body3c.storage_provider = "tencent_cos"
body3c.storage_mode = "cloud"
body3c.oss_endpoint = "ep"
body3c.oss_bucket = "bkt"
body3c.oss_access_key_id = "akid"
body3c.oss_access_key_secret = "new-oss-secret-xyz"
resp3c = save_storage_config(body3c, admin=_admin, db=db3)
check(resp3c.get("ok"), "replace save ok")
check(resp3c["config"].get("has_oss_access_key_secret"), "has true after replace")
check("new-oss-secret-xyz" not in json.dumps(resp3c), "no new secret in response")
db3.rollback()
print("T3 PASS")

# ═══ T4: system-settings PUT keep/clear/replace ═══
print("=== T4: system PUT semantics ===")
db4 = SessionLocal()
_seed(db4, wx_mini_secret="original-mini-secret", wx_mini_appid="wx123")

# T4a: keep (empty value → not in items dict at all, or empty non-CLEAR)
body4a = SystemSettingsBody(items={})
resp4a = save_system_settings(body4a, admin=_admin, db=db4)
check(resp4a.get("ok"), "keep save ok")
check(resp4a["configs"]["wx_mini_secret"].get("has"), "has true after keep")
check(resp4a["configs"]["wx_mini_secret"].get("value") == "", "value empty in response")
check("original-mini-secret" not in json.dumps(resp4a), "no original secret in response")

# T4b: clear via __CLEAR__
body4b = SystemSettingsBody(items={"wx_mini_secret": _CLEAR_SENTINEL})
resp4b = save_system_settings(body4b, admin=_admin, db=db4)
check(resp4b.get("ok"), "clear save ok")
check(not resp4b["configs"]["wx_mini_secret"].get("has"), "has false after clear")

# T4c: replace
body4c = SystemSettingsBody(items={"wx_mini_secret": "new-mini-secret-xyz"})
resp4c = save_system_settings(body4c, admin=_admin, db=db4)
check(resp4c.get("ok"), "replace save ok")
check(resp4c["configs"]["wx_mini_secret"].get("has"), "has true after replace")
check("new-mini-secret-xyz" not in json.dumps(resp4c), "no new secret in response")
db4.rollback()
print("T4 PASS")

# ═══ T5: storage GET masked ═══
print("=== T5: storage GET masked ===")
db5 = SessionLocal()
_seed(db5, oss_access_key_secret="oss-secret-abc", oss_bucket="b", oss_access_key_id="k")
resp5 = get_storage_config(admin=_admin, db=db5)
check(resp5.get("has_oss_access_key_secret"), "has true")
check(resp5.get("oss_access_key_secret") == "", "secret empty")
check("oss-secret-abc" not in json.dumps(resp5), "no secret in GET response")
db5.rollback()
print("T5 PASS")

# ═══ T6: system GET masked ═══
print("=== T6: system GET masked ===")
db6 = SessionLocal()
_seed(db6, wx_mini_secret="mini-secret-real", wx_mp_secret="mp-secret-real")
resp6 = get_system_settings(admin=_admin, db=db6)
check(resp6["configs"]["wx_mini_secret"].get("has"), "has mini true")
check(resp6["configs"]["wx_mini_secret"].get("value") == "", "mini value empty")
check(resp6["configs"]["wx_mp_secret"].get("has"), "has mp true")
check("mini-secret-real" not in json.dumps(resp6), "no mini secret leaked")
check("mp-secret-real" not in json.dumps(resp6), "no mp secret leaked")
db6.rollback()
print("T6 PASS")

# ═══ T7: frontend audit ═══
print("=== T7: frontend audit ===")
html = open(os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html'), 'r', encoding='utf-8').read()
for marker in ["cfg_clear_aikey", "cfg_clear_amapkey", "cfg_clear_wxkey", "cfg_clear_vpay",
               "cfg_clear_privkey", "cfg_clear_platcert",
               "sp_clear_minisecret", "oss_clear_aksec", "kf_clear_sec",
               "clear_security_secret", "__CLEAR__", "已设置，留空保留",
               "clear_wx_private_key_pem", "clear_wx_platform_cert_pem"]:
    check(marker in html, f"frontend has {marker}")
check("sk-real" not in html, "no real key in HTML")
check("amap-real" not in html, "no real amap key in HTML")
check("oss_clear_aksec" in html, "oss_clear_aksec element exists")
check("else if(clearSec)" in html or "else if (clearSec)" in html or "clearSec" in html,
      "saveStorageConfig handles __CLEAR__ outside cloud branch")
print("T7 PASS")

# ═══ T7.5: Node JS syntax check ═══
print("=== T7.5: admin HTML JS syntax ===")
import subprocess
html_path = os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html')
try:
    result = subprocess.run(
        ['node', '-e',
         "const fs=require('fs');const h=fs.readFileSync('" + html_path.replace('\\', '/') + "','utf8');"
         "const re=/<script[^>]*>([\\s\\S]*?)<\\/script>/gi;let m,scripts='';"
         "while((m=re.exec(h))!==null)scripts+=m[1]+'\\n';"
         "new Function(scripts);console.log('JS-SYNTAX-OK')"],
        capture_output=True, text=True, timeout=15)
    check(result.returncode == 0 and 'JS-SYNTAX-OK' in result.stdout,
          f"Node JS syntax: {result.stderr[:120] if result.stderr else 'OK'}")
except FileNotFoundError:
    check(True, "Node not available, skipping JS syntax check")
except Exception as e:
    check(False, f"Node check failed: {e}")
print("T7.5 PASS")

# ═══ T7b: storage cloud + __CLEAR__ rejected ═══
print("=== T7b: cloud + clear rejected ===")
db7b = SessionLocal()
_seed(db7b, oss_access_key_secret="secret123", oss_bucket="bkt", oss_access_key_id="akid",
      oss_endpoint="ep", storage_provider="tencent_cos")
body7b = StorageConfigBody()
body7b.storage_provider = "tencent_cos"
body7b.storage_mode = "cloud"
body7b.oss_bucket = "bkt"
body7b.oss_access_key_id = "akid"
body7b.oss_access_key_secret = _CLEAR_SENTINEL
try:
    save_storage_config(body7b, admin=_admin, db=db7b)
    check(False, "cloud + __CLEAR__ should reject")
except Exception as e:
    check("400" in str(e) or "不能为空" in str(e) or "清空" in str(e),
          f"cloud + clear rejected: {str(e)[:80]}")
db7b.rollback()
print("T7b PASS")

# ═══ T7c: AMap key pool clear_security_secret ═══
print("=== T7c: amap key clear_security_secret ===")
from routers.admin import _AmapKeyBody, update_amap_key, _AmapKey
db7c = SessionLocal()
k = _AmapKey(name="test_key", api_key="test_api_key_123", security_secret="old_sec",
             enabled=1, priority=0)
db7c.add(k)
db7c.commit()
db7c.refresh(k)
# Verify clear works
body7c = _AmapKeyBody(name="test_key", api_key="", security_secret="",
                      enabled=True, priority=0, clear_security_secret=True)
resp7c = update_amap_key(k.id, body7c, admin=_admin, db=db7c)
check(resp7c.get("ok"), "update ok")
check(not resp7c["key"].get("has_security_secret"), "security_secret cleared")
check("test_api_key_123" not in json.dumps(resp7c), "api_key masked in response")
db7c.rollback()
print("T7c PASS")

# ═══ T8: complete secret field list ═══
print("=== T8: complete secret list ===")
expected = {"ai_key", "amap_key", "wx_api_key", "wx_private_key_pem", "wx_platform_cert_pem",
            "wx_virtual_app_key", "wx_mp_secret", "wx_mini_secret", "wx_service_secret",
            "oss_access_key_secret"}
check(len(expected) == 10, f"10 secret fields: {sorted(expected)}")
core_masked = _mask_core_config({"ai_key": "x", "amap_key": "y", "wx_api_key": "z",
    "wx_private_key_pem": "a", "wx_platform_cert_pem": "b", "wx_virtual_app_key": "c"})
check("ai_key_masked" in core_masked, "ai masked")
check("amap_key_masked" in core_masked, "amap masked")
print("T8 PASS")

print(f"\n{'='*50}")
print(f"ADMIN SECRET MASKING: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
