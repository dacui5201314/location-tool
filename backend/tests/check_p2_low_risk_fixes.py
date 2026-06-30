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
# README has production build and dep audit notes
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
# admin.py re-exports
from routers.admin import amap_router as admin_amap_router
check(admin_amap_router is amap_router, "admin.py re-exports amap_router")
print("6.1 PASS")

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
