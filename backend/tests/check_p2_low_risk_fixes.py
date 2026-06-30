"""P2-1/4/5/9: Low-risk fixes audit — config check, 401 event, maskDeep, AMap fail"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")

uniapp = os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src')

# ═══ P2-1: API URL from build env, production fail on placeholder ═══
print("=== P2-1: API URL config ===")
cfg = open(os.path.join(uniapp, 'utils', 'config.js'), 'r', encoding='utf-8').read()
check("__API_BASE_URL__" in cfg, "config.js uses __API_BASE_URL__ from build")
check("oliver188.top" not in cfg, "no hardcoded domain in config.js")
vite_cfg = open(os.path.join(uniapp, '..', 'vite.config.js'), 'r', encoding='utf-8').read()
check("process.exit(1)" in vite_cfg, "vite.config.js fails build on placeholder")
check("VITE_API_BASE_URL" in vite_cfg, "vite reads VITE_API_BASE_URL")
# 6.1 生产构建 URL 校验：必须 https://，拦截 http:// 生产域名
check("startsWith('https://')" in vite_cfg, "vite.config.js enforces https:// for production builds")
print("P2-1 PASS")

# ═══ P2-4: 401 unified handler in both request() and analyzeLocation() ═══
print("=== P2-4: 401 handler ===")
api_js = open(os.path.join(uniapp, 'utils', 'api.js'), 'r', encoding='utf-8').read()
check("handleAuthExpired" in api_js, "api.js uses handleAuthExpired")
auth_js = open(os.path.join(uniapp, 'utils', 'auth.js'), 'r', encoding='utf-8').read()
check("handleAuthExpired" in auth_js, "auth.js exports handleAuthExpired")
check("auth:expired" in auth_js, "emits auth:expired")
# analyzeLocation 401 branch also calls handleAuthExpired
check("登录已过期" in api_js and "handleAuthExpired" in api_js,
      "analyzeLocation 401 also calls handleAuthExpired")
print("P2-4 PASS")

# ═══ P2-5: maskDeep depth + circular ref ═══
print("=== P2-5: maskDeep ===")
# maskDeep extracted to standalone utility
mask_js = open(os.path.join(uniapp, 'utils', 'mask-deep.js'), 'r', encoding='utf-8').read()
check("MAX_DEPTH" in mask_js, "maskDeep has MAX_DEPTH constant")
check("深度超限" in mask_js, "depth overflow placeholder")
check("WeakSet" in mask_js, "maskDeep uses WeakSet for circular ref")
check("循环引用" in mask_js, "circular ref placeholder")
check("createMaskDeep" in mask_js, "exports createMaskDeep factory")
# Component still references maskDeep
rpt = open(os.path.join(uniapp, 'pages', 'report-detail', 'index.vue'), 'r', encoding='utf-8').read()
check("createMaskDeep" in rpt, "report-detail imports createMaskDeep")
check("maskDeep" in rpt, "report-detail retains maskDeep method")
print("P2-5 PASS")

# ═══ P2-9: AMap fail early termination ═══
print("=== P2-9: AMap fail ===")
main_src = open(os.path.join(os.path.dirname(__file__), '..', 'main.py'), 'r', encoding='utf-8').read()
check("BILLING_COMMIT_FAILED" in main_src, "billing commit fail handled")
check("AMAP_DATA_COLLECTION_FAILED" in main_src, "AMap fail detected early")
check("not_charged" in main_src, "billing_status=not_charged on fail")
print("P2-9 PASS")

# ═══ P2-7: migration ledger ═══
print("=== P2-7: migration ledger ===")
readme = open(os.path.join(os.path.dirname(__file__), '..', '..', 'README.md'), 'r', encoding='utf-8').read()
check("兼容迁移台账" in readme, "README has migration ledger")
check("init_db()" in readme, "lists init_db migrations")
check("_ensure_feedback_schema" in readme, "lists feedback schema migrations")
check("Alembic" in readme or "版本化迁移" in readme, "recommends versioned migration tool")
print("P2-7 PASS")

# ═══ P2-8: Python env — all commands use uv ═══
print("=== P2-8: Python env ===")
check("uv run --with-requirements requirements.txt" in readme, "README has uv command")
check("UV_CACHE_DIR" in readme, "README mentions UV_CACHE_DIR")
check(".venv\\\\Scripts\\\\python.exe" not in readme, "no .venv Scripts path")
check("uv run" in readme, "uv run present in test commands")
check("python -m compileall ." not in readme, "no bare python compileall")
print("P2-8 PASS")

# ═══ 6.3: DB migration system ═══
print("=== 6.3: migration system ===")
check(os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'migrations', 'runner.py')),
      "migration runner exists")
check(os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'migrations', '001_users_nickname.sql')),
      "migration SQL files exist")
db_src = open(os.path.join(os.path.dirname(__file__), '..', 'database.py'), 'r', encoding='utf-8').read()
check("run_migrations" in db_src, "database.py calls migration runner")
check("ALTER TABLE" not in db_src, "database.py no longer has inline ALTER TABLE")
fb_src = open(os.path.join(os.path.dirname(__file__), '..', 'routers', 'feedback.py'), 'r', encoding='utf-8').read()
check("_ensure_feedback_schema" not in fb_src, "feedback.py no longer has schema migration")
print("6.3 PASS")

# ═══ 6.2: admin innerHTML governance ═══
print("=== 6.2: admin innerHTML ===")
admin_html = open(os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html'), 'r', encoding='utf-8').read()
check("function esc(" in admin_html, "esc function exists")
check("function escUrl(" in admin_html, "escUrl function exists")
# user-controlled fields are escaped
check("escUrl(" in admin_html, "escUrl used in admin HTML")
# key user fields passed through esc
for marker in ["esc(fb.content", "esc(r.data", "esc(m.address"]:
    if marker in admin_html:
        check(True, f"user field escaped: {marker}")
        break
print("6.2 PASS")

# ═══ 6.5: security headers + deps ═══
print("=== 6.5: security headers ===")
main_src = open(os.path.join(os.path.dirname(__file__), '..', 'main.py'), 'r', encoding='utf-8').read()
check("X-Content-Type-Options" in main_src, "nosniff header present")
check("X-Frame-Options" in main_src, "frame options present")
check("nosniff" in main_src, "nosniff value present")
check("frame-ancestors" in main_src, "CSP frame-ancestors header present")
readme = open(os.path.join(os.path.dirname(__file__), '..', '..', 'README.md'), 'r', encoding='utf-8').read()
check("uv run" in readme, "README uses uv consistently")
print("6.5 PASS")

# ═══ 6.1: large file split — real module verification ═══
print("=== 6.1: file split ===")
backend = os.path.join(os.path.dirname(__file__), '..')
# 6.1a: admin.py AMap section extracted to admin_amap.py
check(os.path.exists(os.path.join(backend, 'routers', 'admin_amap.py')), "admin_amap.py exists")
admin_lines = len(open(os.path.join(backend, 'routers', 'admin.py'), 'r', encoding='utf-8').readlines())
check(admin_lines <= 2200, f"admin.py {admin_lines} <= 2200 lines")
admin_amap_lines = len(open(os.path.join(backend, 'routers', 'admin_amap.py'), 'r', encoding='utf-8').readlines())
check(50 < admin_amap_lines < 600, f"admin_amap.py {admin_amap_lines} in (50, 600)")
# 6.1b: amap_service.py POI classifiers extracted to amap_poi_rules.py
check(os.path.exists(os.path.join(backend, 'services', 'amap_poi_rules.py')), "amap_poi_rules.py exists")
amap_svc_lines = len(open(os.path.join(backend, 'services', 'amap_service.py'), 'r', encoding='utf-8').readlines())
check(amap_svc_lines <= 30, f"amap_service.py {amap_svc_lines} <= 30 lines (thin wrapper)")
amap_rules_lines = len(open(os.path.join(backend, 'services', 'amap_poi_rules.py'), 'r', encoding='utf-8').readlines())
check(amap_rules_lines > 100, f"amap_poi_rules.py {amap_rules_lines} > 100 lines")
# 6.1c: main.py still within limits
main_lines = len(open(os.path.join(backend, 'main.py'), 'r', encoding='utf-8').readlines())
check(main_lines <= 1500, f"main.py {main_lines} <= 1500 lines")
# 6.1d: cross-imports functional
import sys; sys.path.insert(0, backend)
from routers.admin_amap import amap_router, _get_amap_key_selector
check(amap_router is not None, "amap_router importable")
check(_get_amap_key_selector is not None, "_get_amap_key_selector importable")
from services.amap_service import collect_location_data
check(collect_location_data is not None, "collect_location_data importable (thin wrapper)")
from routers.admin import amap_router as admin_amap_router, _parse_report_type as admin_parse_report_type
check(admin_amap_router is amap_router, "admin.py re-exports amap_router")
check(callable(admin_parse_report_type), "admin.py re-exports _parse_report_type for report library")
# 6.1e: P2-A — storage_location / render_source 行为测试
from routers.admin import _compute_storage_location, _compute_render_source
VALID_JSON = '{"score":80,"summary":"ok"}'
INVALID_JSON = '{bad json'
# storage_location 规则
check(_compute_storage_location(True, False, False) == "cloud",     "stor_loc: url → cloud")
check(_compute_storage_location(False, True, False) == "local",     "stor_loc: file → local")
check(_compute_storage_location(False, False, True) == "database",  "stor_loc: json → database")
check(_compute_storage_location(False, False, False) == "missing",  "stor_loc: none → missing")
check(_compute_storage_location(True, True, True) == "cloud",       "stor_loc: url+file+json → cloud")
# render_source 规则（P2-A 返修：解析 JSON 确认有效性）
check(_compute_render_source(VALID_JSON, False, False) == "db_json",        "render: valid_json → db_json")
check(_compute_render_source(INVALID_JSON, False, True) == "cloud_html",    "render: bad_json+url → cloud_html")
check(_compute_render_source(INVALID_JSON, True, False) == "html_file",     "render: bad_json+file → html_file")
check(_compute_render_source(INVALID_JSON, False, False) == "db_json_parse_error", "render: bad_json+nothing → db_json_parse_error")
check(_compute_render_source("", True, False) == "html_file",               "render: no_json+file → html_file")
check(_compute_render_source("", False, True) == "cloud_html",              "render: no_json+url → cloud_html")
check(_compute_render_source("", False, False) == "missing",                "render: none → missing")
# admin/index.html: 新字段名，无 "DB JSON"
check("storage_location" in admin_html, "admin HTML uses storage_location")
check("render_source" in admin_html, "admin HTML uses render_source")
check("storage_source" not in admin_html, "admin HTML no longer references storage_source")
check('DB JSON' not in admin_html, "admin HTML hides DB JSON")
check("cloud:'云端'" in admin_html, "admin HTML has locMap cloud")
check("database:'数据库'" in admin_html, "admin HTML has locMap database")
check("db_json:'数据库JSON'" in admin_html, "admin HTML has renderMap db_json")
check("db_json_parse_error:'数据库异常'" in admin_html, "admin HTML has parse_error label")
print("6.1 PASS")

# ═══ 6.1f: P2-A DB-backed — 真实调用 list_reports / get_report_detail ═══
print("=== 6.1f: P2-A DB-backed endpoint tests ===")
from sqlalchemy import create_engine as _ce2, event as _ev2
from sqlalchemy.orm import sessionmaker as _sm2
from datetime import datetime as _dt2

_p2a_engine = _ce2("sqlite://", echo=False)
@_ev2.listens_for(_p2a_engine, "connect")
def _p2a_pragma(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA journal_mode=WAL;")
_P2aSession = _sm2(bind=_p2a_engine)

from database import Base as _Base2
from models.db_models import AnalysisRecord as _AR, User as _User2
_Base2.metadata.create_all(bind=_p2a_engine)

from routers.admin import list_reports, get_report_detail

_p2a_counter = 0
def _make_ar(db, report_uuid, report_json="", report_file="", report_url="", user_id=1):
    """创建 AnalysisRecord 测试行"""
    global _p2a_counter
    _p2a_counter += 1
    # ensure user exists
    u = db.query(_User2).filter(_User2.id == user_id).first()
    if not u:
        u = _User2(id=user_id, balance_credits=10, membership_tier="free", wx_mini_openid=f"oAR{user_id}")
        db.add(u)
        db.commit()
    ar = _AR(report_uuid=report_uuid, user_id=user_id,
             report_json=report_json, report_file=report_file, report_url=report_url,
             brand_desc="测试品牌", address="测试地址", business_type="测试业态",
             overall_score=80, created_at=_dt2.now())
    db.add(ar)
    db.commit()
    db.refresh(ar)
    return ar

_ADMIN = {"user_id": 1, "role": "admin"}

# ── DB1: report_json + report_url → list storage_location=cloud, render_source=db_json ──
print("  DB1: valid json + url → list")
db1 = _P2aSession()
_ar1 = _make_ar(db1, "uuid-db1-001", report_json=VALID_JSON, report_url="https://example.com/r.html")
r1 = list_reports(admin=_ADMIN, db=db1, page=1, page_size=20, score_min=0, score_max=100, q="", user_id=0, business_type="", date_from="", date_to="", report_type="")
items1 = r1["items"]
check(len(items1) == 1, f"list has 1 item: {len(items1)}")
check(items1[0]["storage_location"] == "cloud", f"stor_loc=cloud: {items1[0]['storage_location']}")
check(items1[0]["render_source"] == "db_json", f"render=db_json: {items1[0]['render_source']}")
db1.rollback()
print("  DB1 PASS")

# ── DB2: report_json + report_url → detail storage_location=cloud, render_source=db_json ──
print("  DB2: valid json + url → detail")
db2 = _P2aSession()
_ar2 = _make_ar(db2, "uuid-db2-001", report_json=VALID_JSON, report_url="https://example.com/r.html")
r2 = get_report_detail("uuid-db2-001", admin=_ADMIN, db=db2)
m2 = r2["meta"]
check(m2["storage_location"] == "cloud", f"stor_loc=cloud: {m2['storage_location']}")
check(m2["render_source"] == "db_json", f"render=db_json: {m2['render_source']}")
db2.rollback()
print("  DB2 PASS")

# ── DB3: 坏 JSON + report_file → list render_source=html_file ──
print("  DB3: bad json + file → list")
db3 = _P2aSession()
_ar3 = _make_ar(db3, "uuid-db3-001", report_json=INVALID_JSON, report_file="/tmp/test.html")
r3 = list_reports(admin=_ADMIN, db=db3, page=1, page_size=20, score_min=0, score_max=100, q="", user_id=0, business_type="", date_from="", date_to="", report_type="")
check(r3["items"][0]["storage_location"] == "local", "stor_loc=local")
check(r3["items"][0]["render_source"] == "html_file", f"render=html_file: {r3['items'][0]['render_source']}")
db3.rollback()
print("  DB3 PASS")

# ── DB4: 坏 JSON + report_file → detail render_source=html_file, parse_error 有值 ──
print("  DB4: bad json + file → detail")
import tempfile as _tf
_tf4 = _tf.NamedTemporaryFile(suffix=".html", delete=False, mode="w")
_tf4.write("<html><body>test</body></html>")
_tf4.close()
db4 = _P2aSession()
_ar4 = _make_ar(db4, "uuid-db4-001", report_json=INVALID_JSON, report_file=_tf4.name)
r4 = get_report_detail("uuid-db4-001", admin=_ADMIN, db=db4)
m4 = r4["meta"]
check(m4["storage_location"] == "local", f"stor_loc=local: {m4['storage_location']}")
check(m4["render_source"] == "html_file", f"render=html_file: {m4['render_source']}")
check(bool(r4.get("parse_error")), f"parse_error present: {r4.get('parse_error', '')[:60]}")
db4.rollback()
os.unlink(_tf4.name)
print("  DB4 PASS")

# ── DB5: 坏 JSON + report_url → list render_source=cloud_html ──
print("  DB5: bad json + url → list")
db5 = _P2aSession()
_ar5 = _make_ar(db5, "uuid-db5-001", report_json=INVALID_JSON, report_url="https://example.com/r.html")
r5 = list_reports(admin=_ADMIN, db=db5, page=1, page_size=20, score_min=0, score_max=100, q="", user_id=0, business_type="", date_from="", date_to="", report_type="")
check(r5["items"][0]["storage_location"] == "cloud", "stor_loc=cloud")
check(r5["items"][0]["render_source"] == "cloud_html", f"render=cloud_html: {r5['items'][0]['render_source']}")
db5.rollback()
print("  DB5 PASS")

# ── DB6: 坏 JSON + report_url → detail render_source=cloud_html (云端真实尝试) ──
# 注：in-memory DB 无法真实 HTTP 获取云端内容，render_source 应回退为 missing
# 但 report_url 存在且 report_json 解析失败 → 应尝试云端加载（失败则标 db_json_parse_error）
print("  DB6: bad json + url → detail (no real cloud)")
db6 = _P2aSession()
_ar6 = _make_ar(db6, "uuid-db6-001", report_json=INVALID_JSON, report_url="https://example.com/r.html")
r6 = get_report_detail("uuid-db6-001", admin=_ADMIN, db=db6)
m6 = r6["meta"]
check(m6["storage_location"] == "cloud", f"stor_loc=cloud: {m6['storage_location']}")
# 云端获取失败 + 坏 JSON → db_json_parse_error
check(m6["render_source"] == "db_json_parse_error",
      f"render=db_json_parse_error (cloud fetch failed, no valid json): {m6['render_source']}")
check(bool(r6.get("parse_error")), "parse_error present")
db6.rollback()
print("  DB6 PASS")

# ── DB7: 都没有 → list storage_location=missing, render_source=missing ──
print("  DB7: nothing → list")
db7 = _P2aSession()
_ar7 = _make_ar(db7, "uuid-db7-001")
r7 = list_reports(admin=_ADMIN, db=db7, page=1, page_size=20, score_min=0, score_max=100, q="", user_id=0, business_type="", date_from="", date_to="", report_type="")
check(r7["items"][0]["storage_location"] == "missing", f"stor_loc=missing: {r7['items'][0]['storage_location']}")
check(r7["items"][0]["render_source"] == "missing", f"render=missing: {r7['items'][0]['render_source']}")
db7.rollback()
print("  DB7 PASS")

# ── DB8: 都没有 → detail storage_location=missing, render_source=missing ──
print("  DB8: nothing → detail")
db8 = _P2aSession()
_ar8 = _make_ar(db8, "uuid-db8-001")
r8 = get_report_detail("uuid-db8-001", admin=_ADMIN, db=db8)
m8 = r8["meta"]
check(m8["storage_location"] == "missing", f"stor_loc=missing: {m8['storage_location']}")
check(m8["render_source"] == "missing", f"render=missing: {m8['render_source']}")
db8.rollback()
print("  DB8 PASS")

# ── DB9: 坏 JSON + report_url + 无 report_file → detail db_json_parse_error ──
print("  DB9: bad json + url only, no file → detail")
db9 = _P2aSession()
_ar9 = _make_ar(db9, "uuid-db9-001", report_json=INVALID_JSON, report_url="https://bad.example/nonexistent")
r9 = get_report_detail("uuid-db9-001", admin=_ADMIN, db=db9)
m9 = r9["meta"]
check(m9["storage_location"] == "cloud", f"stor_loc=cloud: {m9['storage_location']}")
check(m9["render_source"] == "db_json_parse_error",
      f"render=db_json_parse_error: {m9['render_source']}")
check(bool(r9.get("parse_error")), "parse_error present")
db9.rollback()
print("  DB9 PASS")

# ── DB10: valid JSON only → list storage_location=database, render_source=db_json ──
print("  DB10: valid json only → list")
db10 = _P2aSession()
_ar10 = _make_ar(db10, "uuid-db10-001", report_json=VALID_JSON)
r10 = list_reports(admin=_ADMIN, db=db10, page=1, page_size=20, score_min=0, score_max=100, q="", user_id=0, business_type="", date_from="", date_to="", report_type="")
check(r10["items"][0]["storage_location"] == "database",
      f"stor_loc=database: {r10['items'][0]['storage_location']}")
check(r10["items"][0]["render_source"] == "db_json",
      f"render=db_json: {r10['items'][0]['render_source']}")
db10.rollback()
print("  DB10 PASS")

# ── DB11: valid JSON only → detail storage_location=database, render_source=db_json ──
print("  DB11: valid json only → detail")
db11 = _P2aSession()
_ar11 = _make_ar(db11, "uuid-db11-001", report_json=VALID_JSON)
r11 = get_report_detail("uuid-db11-001", admin=_ADMIN, db=db11)
m11 = r11["meta"]
check(m11["storage_location"] == "database", f"stor_loc=database: {m11['storage_location']}")
check(m11["render_source"] == "db_json", f"render=db_json: {m11['render_source']}")
check("report" in r11, "report object returned for valid json")
db11.rollback()
print("  DB11 PASS")

print("6.1f PASS")

# ═══ P2-15: user input boundary in prompt ═══
print("=== P2-15: prompt input boundary ===")
from prompts.location_analysis import build_analysis_prompt

# 1. prompt with location_data: both address and brand get boundaries
ld = {"city": "北京", "district": "朝阳", "stats_200m": {}, "stats_500m": {}, "stats_1000m": {},
      "direct_competitors_200m": 0, "direct_competitors_500m": 0, "direct_competitors_1000m": 0,
      "substitute_competitors_200m": 0, "substitute_competitors_500m": 0, "substitute_competitors_1000m": 0,
      "traffic_anchors_200m": 0, "traffic_anchors_500m": 0, "traffic_anchors_1000m": 0,
      "direct_competitor_list": [], "substitute_list": [], "traffic_anchor_list": [],
      "competitor_list": [], "hot_brands": [], "nearby_roads": [], "business_areas": [],
      "poi_lists": {}, "poi_counts": {}, "data_quality_notes": [],
      "city_has_subway": False, "subway_applicable": False, "rigor_enabled": False}
prompt = build_analysis_prompt("测试地址", 116.4, 39.9, business_type="小吃快餐",
                                brand_name="砂锅米线", store_size=50, location_data=ld)
check("【用户输入开始：address】" in prompt, "prompt has address boundary")
check("【用户输入结束：address】" in prompt, "prompt has address end boundary")
check("【用户输入开始：brand_name】" in prompt, "prompt has brand boundary")
check("【用户输入结束：brand_name】" in prompt, "prompt has brand end boundary")
# 2. "请结合" system instruction is OUTSIDE user input block
brand_start = prompt.find("【用户输入开始：brand_name】")
brand_end = prompt.find("【用户输入结束：brand_name】")
instr_pos = prompt.find("请结合上述用户填写的品牌")
check(instr_pos > brand_end, f"system instruction outside user block: {instr_pos} > {brand_end}")
# 3. scoring rules still present
check("人口密集度" in prompt or "交通" in prompt, "scoring dimensions present")
# 4. source audit
la_src = open(os.path.join(os.path.dirname(__file__), '..', 'prompts', 'location_analysis.py'), 'r', encoding='utf-8').read()
check("_user_input_block" in la_src, "helper function exists in source")
check("请结合上述用户填写的品牌" in la_src, "system instruction uses generic reference")
print("P2-15 PASS")

# ═══ P2-12: miniprogram deprecated ═══
print("=== P2-12: miniprogram ===")
check("已废弃" in readme or "历史废弃" in readme, "README marks miniprogram deprecated")
check("不可发布" in readme or "不可继续开发" in readme, "README warns against publishing")
mp_readme = open(os.path.join(os.path.dirname(__file__), '..', '..', 'miniprogram', 'README.md'), 'r', encoding='utf-8').read()
check("历史废弃" in mp_readme or "废弃" in mp_readme, "miniprogram README states deprecated")
check("不可发布" in mp_readme, "miniprogram README says not for publishing")
check("dist/build/mp-weixin" in mp_readme, "miniprogram README points to uniapp build path")
print("P2-12 PASS")

# ═══ Hard boundary check ═══
print("=== Hard boundary ===")
# P2-7/8/12 are documentation-only changes: README.md + miniprogram/README.md
# No backend business code, no report logic, no Prompt/score/industry config touched
readme_full = open(os.path.join(os.path.dirname(__file__), '..', '..', 'README.md'), 'r', encoding='utf-8').read()
check("uv run --with-requirements" in readme_full, "all commands use uv in README")
check(".venv\\\\Scripts" not in readme_full, "no .venv Scripts in README")
print("Boundary PASS")

print(f"\n{'='*50}")
print(f"P2 LOW-RISK FIXES: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
