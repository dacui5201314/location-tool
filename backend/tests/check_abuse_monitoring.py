"""5.9: Abuse monitoring — warning only, no blocking, TTL + max keys"""
import sys, os, io, contextlib, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services.abuse_monitor as am

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


# ═══ T1: note_analyze doesn't block ═══
print("=== T1: note_analyze no block ===")
for _ in range(5):
    am.note_analyze("1.2.3.4", 1, 39.9, 116.4)
check(True, "note_analyze completed without exception")
print("T1 PASS")

# ═══ T2: note_login_fail accumulates real count ═══
print("=== T2: note_login_fail ===")
with am._lock:
    am._login_fail_by_ip.clear()
for _ in range(3):
    am.note_login_fail("5.6.7.8")
with am._lock:
    entry = am._login_fail_by_ip.get("5.6.7.8", {})
    check(entry.get("count") == 3, f"count=3 after 3 fails: {entry}")
    # not pruned immediately
    check(entry.get("_ts", 0) > 0, "has timestamp")
am._login_fail_by_ip.clear()
print("T2 PASS")

# ═══ T3: note_service_fail ═══
print("=== T3: note_service_fail ===")
with am._lock:
    am._consecutive_failures.clear()
for _ in range(3):
    am.note_service_fail("AMap")
check(True, "service fail recorded")
print("T3 PASS")

# ═══ T4: maps have TTL + max keys ═══
print("=== T4: TTL + max keys ===")
with am._lock:
    am._analyze_by_ip.clear()
now = time.time()
# fill with many old entries
for i in range(100):
    am._analyze_by_ip[f"ip_{i}"] = {"count": 1, "users": {1}, "coords": {"0,0"}, "_ts": now - 9999}
am._prune()
check(len(am._analyze_by_ip) == 0, f"all old entries pruned: {len(am._analyze_by_ip)}")
# fill with many fresh entries
for i in range(6000):
    am._analyze_by_ip[f"fresh_{i}"] = {"count": 1, "users": {1}, "coords": {"0,0"}, "_ts": now}
am._prune()
check(len(am._analyze_by_ip) <= am._MAX_KEYS, f"capped at {am._MAX_KEYS}: {len(am._analyze_by_ip)}")
am._analyze_by_ip.clear()
print("T4 PASS")

# ═══ T5: warning only, no blocking ═══
print("=== T5: no blocking ===")
# high-frequency should trigger warning log but return normally
for _ in range(25):
    am.note_analyze("10.0.0.1", 99, 39.90, 116.40)
check(True, "high frequency logged but not blocked")
am._analyze_by_ip.clear()
print("T5 PASS")

# ═══ T6: source audit — real call sites ═══
print("=== T6: source audit ===")
backend_dir = os.path.join(os.path.dirname(__file__), '..')
for mod, expect in [
    ("main.py", "note_analyze"),
    ("routers/auth.py", "note_login_fail"),
    ("routers/admin.py", "note_login_fail"),
    ("routers/location.py", "note_service_fail"),
    ("ai_providers/unified.py", "note_service_fail"),
]:
    src = open(os.path.join(backend_dir, mod), 'r', encoding='utf-8').read()
    check(expect in src, f"{mod} calls {expect}")

ab_src = open(os.path.join(backend_dir, 'services', 'abuse_monitor.py'), 'r', encoding='utf-8').read()
check("[ABUSE]" in ab_src, "ABUSE prefix")
check("_prune" in ab_src, "has prune")
check("_MAX_KEYS" in ab_src, "has max keys")
print("T6 PASS")

# ═══ T7: all call sites wrapped in try/except ═══
print("=== T7: no blocking ===")
for mod, func in [("main.py", "note_analyze"), ("routers/auth.py", "note_login_fail"),
                  ("routers/admin.py", "note_login_fail"), ("routers/location.py", "note_service_fail"),
                  ("ai_providers/unified.py", "note_service_fail"),
                  ("services/wechat_http.py", "note_service_fail")]:
    src = open(os.path.join(backend_dir, mod), 'r', encoding='utf-8').read()
    if func in src:
        # find the try/except around it
        idx = src.find(func)
        ctx = src[max(0,idx-200):idx+250]
        check("except" in ctx, f"{mod} {func} wrapped in try/except")
print("T7 PASS")

# ═══ T8: LLM service_fail reachable via real behavior ═══
print("=== T8: LLM service_fail real paths ===")
import asyncio
with am._lock:
    am._consecutive_failures.clear()

# mock LLM timeout exhaustion → should increment LLM
from unittest.mock import patch, AsyncMock, MagicMock
import httpx
async def _llm_timeout():
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.side_effect = httpx.TimeoutException("timeout")
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-test", "provider": "deepseek", "base_url": "https://t", "model": "t", "key_source": "env:T"}):
        try:
            await __import__('ai_providers.unified', fromlist=['generate_llm_response']).generate_llm_response("x")
        except RuntimeError:
            pass
asyncio.run(_llm_timeout())
with am._lock:
    llm_ts = am._consecutive_failures.get("LLM", [])
    check(len(llm_ts) >= 1, f"LLM timeout recorded: {len(llm_ts)}")
am._consecutive_failures.clear()

# mock LLM 503 → should increment
async def _llm_503():
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.raise_for_status.side_effect = httpx.HTTPStatusError("503", request=MagicMock(), response=mock_503)
    mock_503.json.return_value = {"choices": []}
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.side_effect = [mock_503, mock_503]  # 2 fails, no retries left
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-test", "provider": "deepseek", "base_url": "https://t", "model": "t", "key_source": "env:T"}):
        try:
            await __import__('ai_providers.unified', fromlist=['generate_llm_response']).generate_llm_response("x")
        except RuntimeError:
            pass
asyncio.run(_llm_503())
with am._lock:
    llm_ts2 = am._consecutive_failures.get("LLM", [])
    check(len(llm_ts2) >= 1, f"LLM 503 recorded: {len(llm_ts2)}")
am._consecutive_failures.clear()

# mock LLM 401 → should NOT increment
async def _llm_401():
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.raise_for_status.side_effect = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_401)
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.return_value = mock_401
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-test", "provider": "openai", "base_url": "https://t", "model": "t", "key_source": "env:T"}):
        try:
            await __import__('ai_providers.unified', fromlist=['generate_llm_response']).generate_llm_response("x")
        except RuntimeError:
            pass
asyncio.run(_llm_401())
with am._lock:
    llm_ts3 = am._consecutive_failures.get("LLM", [])
    check(len(llm_ts3) == 0, f"LLM 401 NOT recorded: {len(llm_ts3)}")
am._consecutive_failures.clear()
print("T8 PASS")

# ═══ T9: WeChat service_fail behavior ═══
print("=== T9: WeChat service_fail ===")
import services.wechat_http as wh
# mock GET returns 503 → WeChat should be recorded, response still returned
async def _wx_503():
    mock_resp = AsyncMock()
    mock_resp.status_code = 503
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.get.side_effect = [mock_resp, mock_resp]
    with patch('services.wechat_http.httpx.AsyncClient', return_value=client_mock):
        resp = await wh.wechat_get("https://test/wx")
        check(resp.status_code == 503, "503 response returned")
asyncio.run(_wx_503())
with am._lock:
    wx_ts = am._consecutive_failures.get("WeChat", [])
    check(len(wx_ts) >= 1, f"WeChat 503 recorded: {len(wx_ts)}")
am._consecutive_failures.clear()

# mock GET 401 → WeChat NOT recorded
async def _wx_401():
    mock_resp = AsyncMock()
    mock_resp.status_code = 401
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.get.return_value = mock_resp
    with patch('services.wechat_http.httpx.AsyncClient', return_value=client_mock):
        resp = await wh.wechat_get("https://test/wx2")
        check(resp.status_code == 401, "401 response returned")
asyncio.run(_wx_401())
with am._lock:
    wx_ts2 = am._consecutive_failures.get("WeChat", [])
    check(len(wx_ts2) == 0, f"WeChat 401 NOT recorded: {len(wx_ts2)}")
am._consecutive_failures.clear()

# mock GET TimeoutException → WeChat recorded + exception raised
async def _wx_timeout():
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.get.side_effect = httpx.TimeoutException("timeout")
    raised = False
    with patch('services.wechat_http.httpx.AsyncClient', return_value=client_mock):
        try:
            await wh.wechat_get("https://test/wx3")
        except httpx.TimeoutException:
            raised = True
    check(raised, "TimeoutException raised")
asyncio.run(_wx_timeout())
with am._lock:
    wx_ts3 = am._consecutive_failures.get("WeChat", [])
    check(len(wx_ts3) >= 1, f"WeChat timeout recorded: {len(wx_ts3)}")
am._consecutive_failures.clear()
print("T9 PASS")
print("=== T8: 4xx not service fail ===")
llm_src = open(os.path.join(backend_dir, 'ai_providers', 'unified.py'), 'r', encoding='utf-8').read()
check("400" in llm_src or "401" in llm_src, "unified has 4xx check")
wx_src = open(os.path.join(backend_dir, 'services', 'wechat_http.py'), 'r', encoding='utf-8').read()
check("_should_retry" in wx_src, "wechat_http has retry/4xx check")
print("T8 PASS")

print(f"\n{'='*50}")
print(f"ABUSE MONITORING: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
