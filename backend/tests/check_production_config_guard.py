"""Production startup guard: CORS + ALLOW_CLIENT_REALDATA_FALLBACK"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import _validate_startup_config

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")

def raises(env, cors, fallback):
    """Return True if _validate_startup_config raises RuntimeError."""
    try:
        _validate_startup_config(env, cors, fallback)
        return False
    except RuntimeError:
        return True

# ═══ T1: production + missing CORS_ORIGINS → fail ═══
print("=== T1: production missing CORS → fail ===")
check(raises("production", "", ""), "production with empty CORS fails")
check(raises("production", "", "false"), "production + empty CORS + fallback=off fails")
print("T1 PASS")

# ═══ T2: production + CORS_ORIGINS="*" → fail ═══
print("=== T2: production CORS=* → fail ===")
check(raises("production", "*", ""), "production with CORS=* fails")
check(raises("production", "*,https://example.com", ""), "production with CORS=*,domain fails")
print("T2 PASS")

# ═══ T3: production + valid CORS → pass ═══
print("=== T3: production valid CORS → pass ===")
check(not raises("production", "https://example.com", ""), "production with specific CORS passes")
check(not raises("production", "https://a.com,https://b.com", ""), "production with multiple domains passes")
print("T3 PASS")

# ═══ T4: production + ALLOW_CLIENT_REALDATA_FALLBACK=true → fail ═══
print("=== T4: production fallback=true → fail ===")
check(raises("production", "https://example.com", "true"), "production + fallback=true fails")
check(raises("production", "https://example.com", "1"), "production + fallback=1 fails")
check(raises("production", "https://example.com", "yes"), "production + fallback=yes fails")
check(raises("production", "https://example.com", " true "), "production + fallback=' true ' (whitespace) fails")
print("T4 PASS")

# ═══ T5: production + fallback=false/empty → pass ═══
print("=== T5: production fallback=off → pass ===")
check(not raises("production", "https://example.com", "false"), "production + fallback=false passes")
check(not raises("production", "https://example.com", "0"), "production + fallback=0 passes")
check(not raises("production", "https://example.com", "no"), "production + fallback=no passes")
check(not raises("production", "https://example.com", ""), "production + fallback empty passes")
print("T5 PASS")

# ═══ T6: development + fallback=true → pass ═══
print("=== T6: dev fallback=true → pass ===")
check(not raises("development", "", "true"), "dev with fallback=true passes")
check(not raises("development", "", "1"), "dev with fallback=1 passes")
print("T6 PASS")

# ═══ T7: development + missing CORS → pass (defaults to *) ═══
print("=== T7: dev missing CORS → pass ===")
check(not raises("development", "", ""), "dev with empty CORS passes")
check(not raises("development", "*", ""), "dev with CORS=* passes")
print("T7 PASS")

print(f"\n{'='*50}")
print(f"PRODUCTION CONFIG GUARD: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
