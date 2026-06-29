"""P1-9: LLM key priority — provider env > real DB > LLM_API_KEY, no cross-provider leak"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch
from sqlalchemy.orm import sessionmaker

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _mock_env(**kwargs):
    def fake_getenv(key, default=""):
        return kwargs.get(key, default)
    return patch('services.runtime_config.os.getenv', side_effect=fake_getenv)


# ═══ T1: CORE_CONFIG_DEFAULTS["ai_key"] is "" ═══
print("=== T1: default ai_key is empty ===")
import importlib, services.runtime_config as rc
importlib.reload(rc)
check(rc.CORE_CONFIG_DEFAULTS["ai_key"] == "", f"ai_key default: '{rc.CORE_CONFIG_DEFAULTS['ai_key']}'")
print("T1 PASS")

# ═══ T2: DEEPSEEK_API_KEY wins for deepseek ═══
print("=== T2: DS env > all ===")
with _mock_env(DEEPSEEK_API_KEY="sk-ds-env", LLM_API_KEY="sk-llm"), \
     patch.object(rc, '_read_db_ai_key', return_value="sk-db-old"):
    cfg = rc.get_llm_config()
    check(cfg["api_key"] == "sk-ds-env", f"DS env: {cfg['api_key']}")
    check(cfg["key_source"] == "env:DEEPSEEK_API_KEY", f"source: {cfg['key_source']}")
print("T2 PASS")

# ═══ T3: openai + only DEEPSEEK_API_KEY → key_source=missing ═══
print("=== T3: openai no OPENAI_KEY, only DS key → missing ===")
with _mock_env(DEEPSEEK_API_KEY="sk-ds-only", OPENAI_API_KEY="", LLM_API_KEY=""), \
     patch.object(rc, '_read_db_ai_key', return_value=""), \
     patch.object(rc, 'get_core_config', return_value={"ai_provider": "openai", "ai_key": ""}):
    cfg = rc.get_llm_config()
    check(cfg["api_key"] == "", f"openai + DS key only: api_key='{cfg['api_key']}'")
    check(cfg["key_source"] == "missing", f"source: {cfg['key_source']}")
print("T3 PASS")

# ═══ T4: openai + LLM_API_KEY → falls back ═══
print("=== T4: openai + LLM_API_KEY fallback ===")
with _mock_env(OPENAI_API_KEY="", LLM_API_KEY="sk-llm-only"), \
     patch.object(rc, '_read_db_ai_key', return_value=""), \
     patch.object(rc, 'get_core_config', return_value={"ai_provider": "openai", "ai_key": ""}):
    cfg = rc.get_llm_config()
    check(cfg["api_key"] == "sk-llm-only", f"LLM fallback: {cfg['api_key']}")
    check(cfg["key_source"] == "env:LLM_API_KEY", f"source: {cfg['key_source']}")
print("T4 PASS")

# ═══ T5: DB ai_key mid priority ═══
print("=== T5: DB key mid priority ===")
with _mock_env(OPENAI_API_KEY="", LLM_API_KEY="sk-llm"), \
     patch.object(rc, '_read_db_ai_key', return_value="sk-db-real"), \
     patch.object(rc, 'get_core_config', return_value={"ai_provider": "openai", "ai_key": ""}):
    cfg = rc.get_llm_config()
    check(cfg["api_key"] == "sk-db-real", f"DB key: {cfg['api_key']}")
    check(cfg["key_source"] == "db:ai_key", f"source: {cfg['key_source']}")
print("T5 PASS")

# ═══ T6: provider env > DB ═══
print("=== T6: env still > DB ===")
with _mock_env(DEEPSEEK_API_KEY="sk-ds-env"), \
     patch.object(rc, '_read_db_ai_key', return_value="sk-db-old"):
    cfg = rc.get_llm_config()
    check(cfg["api_key"] == "sk-ds-env", "env beats DB")
    check(cfg["key_source"] == "env:DEEPSEEK_API_KEY", "source correct")
print("T6 PASS")

# ═══ T7: kimi MOONSHOT_API_KEY → key_source accurate ═══
print("=== T7: kimi MOONSHOT source ===")
with _mock_env(KIMI_API_KEY="", MOONSHOT_API_KEY="sk-moon", LLM_API_KEY=""), \
     patch.object(rc, '_read_db_ai_key', return_value=""), \
     patch.object(rc, 'get_core_config', return_value={"ai_provider": "kimi", "ai_key": ""}):
    cfg = rc.get_llm_config()
    check(cfg["api_key"] == "sk-moon", f"moon key: {cfg['api_key']}")
    check(cfg["key_source"] == "env:MOONSHOT_API_KEY", f"MOONSHOT source: {cfg['key_source']}")
# Also check KIMI_API_KEY wins if both set
with _mock_env(KIMI_API_KEY="sk-kimi-env", MOONSHOT_API_KEY="sk-moon", LLM_API_KEY=""), \
     patch.object(rc, '_read_db_ai_key', return_value=""), \
     patch.object(rc, 'get_core_config', return_value={"ai_provider": "kimi", "ai_key": ""}):
    cfg2 = rc.get_llm_config()
    check(cfg2["api_key"] == "sk-kimi-env", f"KIMI_API_KEY wins: {cfg2['api_key']}")
    check(cfg2["key_source"] == "env:KIMI_API_KEY", f"KIMI source: {cfg2['key_source']}")
print("T7 PASS")

# ═══ T8: admin masking shows source, no key ═══
print("=== T8: admin masking safe ===")
from routers.admin import _mask_core_config
with _mock_env(DEEPSEEK_API_KEY="sk-secret-real"), \
     patch.object(rc, '_read_db_ai_key', return_value=""):
    masked = _mask_core_config({"ai_provider": "deepseek", "ai_key": ""})
    check(masked["ai_key"] == "", "ai_key empty")
    check("sk-secret-real" not in str(masked), "no real key")
    check(masked.get("llm_key_source", "").startswith("env:"), f"source: {masked.get('llm_key_source')}")
print("T8 PASS")

# ═══ T9: PROVIDER_RUNTIME_DEFAULTS check ═══
print("=== T9: provider list ===")
from services.runtime_config import PROVIDER_RUNTIME_DEFAULTS
for pname in ["deepseek", "openai", "gemini", "kimi", "minimax", "zhipu"]:
    check(pname in PROVIDER_RUNTIME_DEFAULTS, f"{pname} in defaults")
print("T9 PASS")

# ═══ T10: unknown provider → 400 via save_config ═══
print("=== T10: unknown provider 400 ===")
from routers.admin import save_config, ConfigBody
from sqlalchemy import create_engine, event as sqlevent
db_engine = create_engine("sqlite:///:memory:", echo=False)
@sqlevent.listens_for(db_engine, "connect")
def _sp(dbapi_conn, _r): dbapi_conn.execute("PRAGMA journal_mode=WAL;")
from database import SessionLocal as _SL
_orig_session = _SL
import database
database.SessionLocal = sessionmaker(bind=db_engine)
from database import Base as _B
_B.metadata.create_all(bind=db_engine)
# seed required config
db10 = database.SessionLocal()
from models.db_models import SystemConfig
db10.add(SystemConfig(key="ai_provider", value="deepseek"))
db10.add(SystemConfig(key="wx_notify_url", value="https://x.com/n"))
db10.commit()

body = ConfigBody(ai_provider="unknown_provider_xyz", wx_notify_url="https://x.com/n")
try:
    save_config(body, admin={"user_id": 1, "role": "admin"}, db=db10)
    check(False, "unknown provider should 400")
except Exception as e:
    msg = str(getattr(e, 'detail', str(e)))
    check("不支持" in msg or "400" in str(getattr(e, 'status_code', '')), f"unknown provider rejected: {msg[:80]}")

# restore
database.SessionLocal = _orig_session
print("T10 PASS")

# ═══ T11: admin UI shows key_source ═══
print("=== T11: admin UI key source ===")
admin_html = open(os.path.join(os.path.dirname(__file__), '..', 'admin', 'index.html'), 'r', encoding='utf-8').read()
check("llm_key_source" in admin_html, "UI reads llm_key_source")
check("生效来源" in admin_html or "key_source" in admin_html, "UI displays key source")
check("cfg_aikey_src" in admin_html, "UI has key source element")
print("T11 PASS")

# ═══ T12: README + .env.example audit ═══
print("=== T12: docs audit ===")
readme = open(os.path.join(os.path.dirname(__file__), '..', '..', 'README.md'), 'r', encoding='utf-8').read()
env_ex = open(os.path.join(os.path.dirname(__file__), '..', '.env.example'), 'r', encoding='utf-8').read()
check("OPENAI_API_KEY" in env_ex, ".env.example has OPENAI_API_KEY")
check("MOONSHOT_API_KEY" in env_ex, ".env.example has MOONSHOT_API_KEY")
check("兜底" in env_ex or "兜底" in readme, "doc mentions LLM_API_KEY as fallback")
check("优先级" in readme or "priority" in readme.lower(), "README mentions key priority")
check("DEEPSEEK_API_KEY" in readme or "DEEPSEEK_API_KEY" in env_ex, "docs mention provider-specific keys")
print("T12 PASS")

print(f"\n{'='*50}")
print(f"LLM KEY PRIORITY: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
