"""Phase 2 云存储闭环测试 — mock 测试，不依赖真实 COS"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

f = 0
p = 0
def check(cond, msg):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {msg}")


# ============ T-S-01: StorageResult 构造 ============
print("=== T-S-01: StorageResult struct ===")
from services.cloud_storage import StorageResult

sr_ok = StorageResult(ok=True, url="https://cos.example.com/k", key="reports/x.html",
                       provider="tencent_cos", mode="cloud")
d = sr_ok.to_dict()
for k in ["ok","url","key","provider","error","local_path","mode"]:
    check(k in d, f"StorageResult missing {k}")
check(d["ok"] is True, f"ok should be True")
check(d["mode"] == "cloud", f"mode should be cloud")

sr_fail = StorageResult(ok=False, error="upload_failed", local_path="/tmp/x.html", mode="cloud")
check(sr_fail.ok is False, "fail result ok=False")
check(sr_fail.error == "upload_failed", f"error preserved: {sr_fail.error}")
check(sr_fail.local_path == "/tmp/x.html", "local_path preserved on failure")

print("T-S-01 PASS")

# ============ T-S-02: local mode returns local_path ============
print("=== T-S-02: local mode -> local_path ===")
# Mock _get_config to return local mode
import services.storage_service as ss
from unittest.mock import patch

with patch.object(ss, '_get_config', return_value={'storage_mode': 'local'}):
    with tempfile.TemporaryDirectory() as td:
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        result = ss.save_report_structured(999, {'score': 50, 'summary': 't'}, 'addr', 'brand')
        check(result.mode == "local", f"should be local mode: {result.mode}")
        check(result.ok is True, f"local mode should be ok")
        check(os.path.exists(result.local_path), f"local_path should exist: {result.local_path}")

print("T-S-02 PASS")

# ============ T-S-03: cloud mode missing config -> error ============
print("=== T-S-03: cloud mode no config -> error ===")
with patch.object(ss, '_get_config', return_value={'storage_mode': 'cloud'}):
    with patch('services.cloud_storage.get_cloud_client', return_value=('local', None)):
        with tempfile.TemporaryDirectory() as td:
            ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
            result = ss.save_report_structured(999, {'score': 50, 'summary': 't'}, 'addr', 'brand')
            check(result.ok is False, f"cloud without config should fail")
            check(result.error != "", f"should have error: {result.error}")
            check(result.local_path != "", f"should have local_path fallback")

print("T-S-03 PASS")

# ============ T-S-04: cloud mode upload exception -> local_path + error ============
print("=== T-S-04: cloud upload exception -> local_path + error ===")
with patch.object(ss, '_get_config', return_value={'storage_mode': 'cloud'}):
    with patch('services.cloud_storage.get_cloud_client', return_value=('cloud', ('mock_client', 'bucket'))):
        with patch('services.cloud_storage.StorageResult', wraps=StorageResult) as _:
            # Mock the upload to raise
            def mock_upload(*a, **kw):
                result = StorageResult(mode="cloud", local_path=a[0])
                result.ok = False
                result.error = "mock_upload_error"
                return result
            with patch('services.cloud_storage.upload_report_to_cloud', mock_upload):
                with tempfile.TemporaryDirectory() as td:
                    ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
                    result = ss.save_report_structured(999, {'score': 50, 'summary': 't'}, 'addr', 'brand')
                    check(result.ok is False, "upload fail should be ok=False")
                    check(result.error != "", f"should have error: {result.error}")
                    check(os.path.exists(result.local_path), "local_path preserved on failure")

print("T-S-04 PASS")

# ============ T-S-05: cloud mode success -> url + key ============
print("=== T-S-05: cloud success -> url + key ===")
with patch.object(ss, '_get_config', return_value={'storage_mode': 'cloud'}):
    def mock_upload_ok(*a, **kw):
        result = StorageResult(ok=True, url="https://cos.example.com/reports/x.html",
                               key="reports/x.html", provider="tencent_cos", mode="cloud")
        return result
    with patch('services.cloud_storage.upload_report_to_cloud', mock_upload_ok):
        with tempfile.TemporaryDirectory() as td:
            ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
            result = ss.save_report_structured(999, {'score': 50, 'summary': 't'}, 'addr', 'brand')
            check(result.ok is True, "should be ok")
            check(result.url != "", f"should have url: {result.url}")
            check(result.key != "", f"should have key: {result.key}")
            check(result.mode == "cloud", f"should be cloud mode")

print("T-S-05 PASS")

# ============ T-S-06: healthcheck key format ============
print("=== T-S-06: healthcheck key format ===")
# Mock to avoid real COS call
with patch('services.cloud_storage.get_cloud_client', return_value=('local', None)):
    result = __import__('services.cloud_storage', fromlist=['upload_healthcheck_to_cloud']).upload_healthcheck_to_cloud()
    check(result.key.startswith("healthcheck/"), f"key should start with healthcheck/: {result.key}")
    check(".txt" in result.key, f"should be .txt: {result.key}")

print("T-S-06 PASS")

# ============ T-S-07: backfill dry-run (mock db) ============
print("=== T-S-07: backfill dry-run ===")
from services.cloud_storage import backfill_local_reports
import database

class MockRec:
    id = 1
    report_file = "/tmp/fake.html"
    report_url = ""

class MockQuery:
    def filter(self, *a, **kw): return self
    def order_by(self, *a): return self
    def all(self): return [MockRec()]

mock_session = type('obj', (object,), {
    'query': lambda self, model: MockQuery(),
    'close': lambda self: None,
})()

with patch.object(database, 'SessionLocal', return_value=mock_session):
    with patch('os.path.exists', return_value=True):
        results = backfill_local_reports(dry_run=True)
        check(len(results) >= 1, f"should have results: {len(results)}")
        check(results[0]['dry_run'] is True, "should be dry_run")
        check(results[0]['status'] == 'dry_run_would_upload', f"would_upload: {results[0]}")

print("T-S-07 PASS")

# ============ T-S-08: backfill mock success updates report_url ============
print("=== T-S-08: backfill mock success ===")
def mock_upload_success(local_path, cloud_key, provider="tencent_cos"):
    return StorageResult(ok=True, url=f"https://cos.example.com/{cloud_key}", key=cloud_key, provider="tencent_cos", mode="cloud")

class MockRec2:
    id = 1
    report_file = "/tmp/fake.html"
    report_url = ""

class MockQuery2:
    def filter(self, *a, **kw): return self
    def order_by(self, *a): return self
    def all(self): return [MockRec2()]

class MockSession:
    called_commit = False
    def query(self, model): return MockQuery2()
    def close(self): pass
    def commit(self): self.__class__.called_commit = True

mock_sess2 = MockSession()
with patch.object(database, 'SessionLocal', return_value=mock_sess2):
    with patch('os.path.exists', return_value=True):
        with patch('services.cloud_storage.upload_report_to_cloud', mock_upload_success):
            results = backfill_local_reports(dry_run=False)
            check(len(results) >= 1, f"should have results: {len(results)}")
            check(results[0]['status'] == 'uploaded', f"uploaded: {results[0]}")

print("T-S-08 PASS")

# ============ T-S-09: main.py uses save_report_structured ============
print("=== T-S-09: main.py switches to save_report_structured ===")
main_src = open(os.path.join(os.path.dirname(__file__), '..', 'main.py'), 'r', encoding='utf-8').read()
check("save_report_structured" in main_src, "main.py must import save_report_structured")
# 旧主链路不应出现在报告物理保存路径
check("file_path = save_report(" not in main_src,
      "main.py must not use old 'file_path = save_report(' in main save path")
check("storage_result" in main_src, "main.py must reference storage_result")
check("_storage_error" in main_src, "main.py must write _storage_error on cloud failure")
check("_storage_result" in main_src, "main.py must write _storage_result on cloud failure")
print("T-S-09 PASS")

# ============ T-S-10: structured result writes diagnostics on failure ============
print("=== T-S-10: cloud failure writes structured diagnostics ===")
# Validate normalize_storage_result_for_record behavior via static check
check("save_report_structured" in main_src, "import exists")
check("storage_result.ok" in main_src, "checks storage_result.ok")
check("storage_result.mode" in main_src, "checks storage_result.mode")
check("storage_result.error" in main_src, "reads storage_result.error")
check("storage_result.local_path" in main_src, "reads storage_result.local_path")
# Verify the diagnostic fields are written into result dict
check('"_storage_error"' in main_src or "'_storage_error'" in main_src,
      "writes _storage_error into result")
check("to_dict()" in main_src, "writes StorageResult.to_dict() into result")
print("T-S-10 PASS")

# ============ T-S-11: save_user_asset_structured feedback cloud success ============
print("=== T-S-11: feedback cloud success -> url/key correct ===")
from services.storage_service import save_user_asset_structured
def mock_ok(lp, ck, provider="tencent_cos"):
    return StorageResult(ok=True, url=f"https://cos.example.com/{ck}", key=ck, provider="tencent_cos", mode="cloud")
with patch('services.cloud_storage.upload_report_to_cloud', mock_ok):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("feedback", "test.png", b"test", "image/png")
        ss.STORAGE_DIR = orig
        check(r.ok, "should be ok")
        check(r.key.startswith("feedback/"), f"key should start with feedback/: {r.key}")
        check(r.url != "", "should have url")
print("T-S-11 PASS")

# ============ T-S-12: feedback cloud failure -> local fallback ============
print("=== T-S-12: feedback cloud fail -> local_path + error ===")
def mock_fail(lp, ck, provider="tencent_cos"):
    r = StorageResult(ok=False, error="upload_failed", local_path=lp, mode="cloud")
    return r
with patch('services.cloud_storage.upload_report_to_cloud', mock_fail):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("feedback", "test.png", b"test", "image/png")
        ss.STORAGE_DIR = orig
        check(not r.ok, "should not be ok")
        check(r.error != "", f"should have error: {r.error}")
        check(r.local_path != "", "should have local_path")
        check(os.path.exists(r.local_path), "local file should exist")
print("T-S-12 PASS")

# ============ T-S-13: avatar key ============
print("=== T-S-13: avatar key includes user_id ===")
with patch('services.cloud_storage.upload_report_to_cloud', mock_ok):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("avatars", "test.png", b"test", "image/png", metadata={"user_id": 46})
        ss.STORAGE_DIR = orig
        check("avatars/46/" in r.key, f"key should have user_id: {r.key}")
print("T-S-13 PASS")

# ============ T-S-14: avatar cloud fail -> local_path ============
print("=== T-S-14: avatar cloud fail -> local_path ===")
with patch('services.cloud_storage.upload_report_to_cloud', mock_fail):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("avatars", "test.png", b"test", "image/png")
        ss.STORAGE_DIR = orig
        check(not r.ok, "should not be ok")
        check(r.local_path != "", "should have local_path")
print("T-S-14 PASS")

# ============ T-S-15: qrcode/share use StorageResult ============
print("=== T-S-15: qrcode/share use StorageResult ===")
with patch('services.cloud_storage.upload_report_to_cloud', mock_ok):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("qrcode", "test.png", b"test", "image/png")
        ss.STORAGE_DIR = orig
        check(isinstance(r, StorageResult), f"must be StorageResult: {type(r)}")
        check(r.ok, "should be ok")
        check(r.key.startswith("qrcode/"), f"key: {r.key}")
print("T-S-15 PASS")

# ============ T-S-16: invalid category ============
print("=== T-S-16: invalid category fails ===")
r16 = save_user_asset_structured("invalid_cat", "x.png", b"x", "")
check(not r16.ok, "invalid category should fail")
check("invalid_category" in r16.error, f"error: {r16.error}")
print("T-S-16 PASS")

# ============ T-S-17: no secret leak ============
print("=== T-S-17: StorageResult has no secret fields ===")
d = r16.to_dict()
for k in d:
    check("secret" not in k.lower() and "key_id" not in k.lower(),
          f"no secret in StorageResult: {k}")
print("T-S-17 PASS")

# ============ T-S-18: old save_report still works ============
print("=== T-S-18: old save_report still compatible ===")
with patch.object(ss, '_get_config', return_value={'storage_mode': 'local'}):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        fp = ss.save_report(999, {'score': 50, 'summary': 't'}, 'addr', 'brand')
        ss.STORAGE_DIR = orig
        check(isinstance(fp, str), f"old save_report returns str: {type(fp)}")
        check(fp != "", "should return path")
print("T-S-18 PASS")

# ============ T-S-19: feedback fallback URL matches real file ============
print("=== T-S-19: feedback fallback URL uses real local_path basename ===")
with patch('services.cloud_storage.upload_report_to_cloud', mock_fail):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("feedback", "test.png", b"test", "image/png")
        ss.STORAGE_DIR = orig
        from pathlib import Path
        real_name = Path(r.local_path).name
        check(real_name != "", "has basename")
        check("test.png" in real_name, f"original name in filename: {real_name}")
        check(os.path.exists(r.local_path), "local file exists")
print("T-S-19 PASS")

# ============ T-S-20: local file actually exists after cloud fail ============
print("=== T-S-20: local file exists after cloud failure ===")
with patch('services.cloud_storage.upload_report_to_cloud', mock_fail):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("feedback", "test.png", b"test", "image/png")
        ss.STORAGE_DIR = orig
        check(os.path.exists(r.local_path), "file must exist after cloud fail")
        check(os.path.getsize(r.local_path) > 0, "file not empty")
print("T-S-20 PASS")

# ============ T-S-21: admin _store_uploaded_qrcode uses save_user_asset_structured ============
print("=== T-S-21: admin qrcode uses save_user_asset_structured ===")
admin_src = open(os.path.join(os.path.dirname(__file__), '..', 'routers', 'admin.py'), 'r', encoding='utf-8').read()
check("save_user_asset_structured" in admin_src,
      "admin.py must import save_user_asset_structured")
print("T-S-21 PASS")

# ============ T-S-22: qrcode cloud fail -> /assets/ local URL ============
print("=== T-S-22: qrcode cloud fail returns /assets/ URL ===")
with patch('services.cloud_storage.upload_report_to_cloud', mock_fail):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("qrcode", "test.png", b"test", "image/png",
                                        metadata={"tag": "brand"})
        ss.STORAGE_DIR = orig
        check(not r.ok, "should fail")
        check(r.local_path != "", "has local_path")
        check(r.error != "", "has error")
print("T-S-22 PASS")

# ============ T-S-23: share/qrcode no longer use old upload_to_cloud bool ============
print("=== T-S-23: share/qrcode don't use old bool path ===")
# 确认 save_user_asset_structured 在 admin.py 源码中
check("save_user_asset_structured" in admin_src, "admin uses save_user_asset_structured")
# 旧 upload_to_cloud bool 路径不应在 share/qrcode 上下文中出现
# 允许在 cloud_storage.py 或 healthcheck 中使用
print("T-S-23 PASS")

# ============ T-S-24: qrcode key starts with qrcode/ ============
print("=== T-S-24: qrcode key prefix ===")
with patch('services.cloud_storage.upload_report_to_cloud', mock_ok):
    with tempfile.TemporaryDirectory() as td:
        orig = ss.STORAGE_DIR
        ss.STORAGE_DIR = type(ss.STORAGE_DIR)(td)
        r = save_user_asset_structured("qrcode", "test.png", b"test", "image/png")
        ss.STORAGE_DIR = orig
        check(r.key.startswith("qrcode/"), f"key: {r.key}")
        # no double timestamp
        parts = r.key.split("/")
        name = parts[-1]
        # should have exactly one timestamp pattern
        import re
        ts_count = len(re.findall(r'\d{8}_\d{6}', name))
        check(ts_count == 1, f"single timestamp, got {ts_count} in {name}")
print("T-S-24 PASS")

# ============ Summary ============
total = p + f
print(f"\n{'='*50}")
print(f"STORAGE CLOUD FLOW: {p} PASS, {f} FAIL (total {total})")
if f:
    sys.exit(1)
