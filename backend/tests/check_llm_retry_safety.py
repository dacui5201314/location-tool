"""P2-10: LLM retry safety — 5xx/timeout retry, 4xx no retry, log safety"""
import sys, os, re, asyncio, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, AsyncMock, MagicMock
import httpx
from ai_providers.unified import generate_llm_response, _should_retry

p = 0; fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


# ═══ T1: retry logic: 502/503/504 retry, 4xx no retry ═══
print("=== T1: retry rules ===")
check(_should_retry(502), "502 retry")
check(_should_retry(503), "503 retry")
check(_should_retry(504), "504 retry")
check(not _should_retry(400), "400 no retry")
check(not _should_retry(401), "401 no retry")
check(not _should_retry(403), "403 no retry")
check(not _should_retry(200), "200 no retry")
check(not _should_retry(500), "500 no retry (not in list)")
print("T1 PASS")

# ═══ T2: 503 retry succeeds ═══
print("=== T2: 503 retry → 200 ===")
async def _test_503_retry():
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"choices": [{"message": {"content": "retry_ok"}}]}
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.side_effect = [mock_503, mock_200]
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-test", "provider": "deepseek",
             "base_url": "https://test", "model": "test-model", "key_source": "env:TEST"}):
        result = await generate_llm_response("test")
        check(result == "retry_ok", f"retry succeeded: {result}")
        check(client_mock.post.call_count == 2, f"called {client_mock.post.call_count} times")
asyncio.run(_test_503_retry())
print("T2 PASS")

# ═══ T3: timeout retry ═══
print("=== T3: timeout retry ===")
async def _test_timeout_retry():
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"choices": [{"message": {"content": "timeout_ok"}}]}
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.side_effect = [httpx.TimeoutException("timeout"), mock_200]
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-test", "provider": "deepseek",
             "base_url": "https://test", "model": "t", "key_source": "env:TEST"}):
        result = await generate_llm_response("test")
        check(result == "timeout_ok", f"timeout retry ok: {result}")
        check(client_mock.post.call_count == 2, f"called {client_mock.post.call_count} times")
asyncio.run(_test_timeout_retry())
print("T3 PASS")

# ═══ T4: 401 no retry ═══
print("=== T4: 401 no retry ===")
async def _test_401_no_retry():
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mock_401.raise_for_status.side_effect = httpx.HTTPStatusError("401", request=MagicMock(), response=mock_401)
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.return_value = mock_401
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-test", "provider": "openai",
             "base_url": "https://test", "model": "t", "key_source": "env:TEST"}):
        try:
            await generate_llm_response("test")
            check(False, "401 should raise")
        except RuntimeError as e:
            check("拒绝" in str(e) or "401" in str(e), f"401 error: {str(e)[:80]}")
        check(client_mock.post.call_count == 1, f"401 not retried: {client_mock.post.call_count} calls")
asyncio.run(_test_401_no_retry())
print("T4 PASS")

# ═══ T5: double failure → raises ═══
print("=== T5: double fail raises ===")
async def _test_double_fail():
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.side_effect = httpx.TimeoutException("t1")
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-test", "provider": "deepseek",
             "base_url": "https://test", "model": "t", "key_source": "env:TEST"}):
        try:
            await generate_llm_response("test")
            check(False, "should raise after 2 fails")
        except RuntimeError as e:
            check("多次失败" in str(e) or "稍后重试" in str(e), f"exhausted: {str(e)[:80]}")
        check(client_mock.post.call_count == 2, f"called {client_mock.post.call_count} times")
asyncio.run(_test_double_fail())
print("T5 PASS")

# ═══ T6: log safety — no prompt/key/body in logs ═══
print("=== T6: log safety ===")
async def _test_log_safety():
    out = io.StringIO()
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.side_effect = [mock_503, mock_200]
    with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
         patch('ai_providers.unified.get_llm_config', return_value={
             "api_key": "sk-secret-key", "provider": "deepseek",
             "base_url": "https://test", "model": "t", "key_source": "env:TEST"}), \
         contextlib.redirect_stdout(out):
        await generate_llm_response("secret user input 12345")
    logged = out.getvalue()
    check("sk-secret-key" not in logged, "no API key in log")
    check("secret user input 12345" not in logged, "no prompt in log")
    check("Authorization" not in logged, "no auth header in log")
    check("[LLM]" in logged, "log prefix present")
asyncio.run(_test_log_safety())
print("T6 PASS")

# ═══ T7: does not break key priority ═══
print("=== T7: key priority unchanged ===")
mock_200 = MagicMock()
mock_200.status_code = 200
mock_200.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
client_mock = AsyncMock()
client_mock.__aenter__.return_value = client_mock
client_mock.post.return_value = mock_200
with patch('ai_providers.unified.httpx.AsyncClient', return_value=client_mock), \
     patch('ai_providers.unified.get_llm_config', return_value={
         "api_key": "sk-from-env", "provider": "deepseek",
         "base_url": "https://test", "model": "t", "key_source": "env:DEEPSEEK_API_KEY"}):
    # Should not raise about missing/unavailable key
    result = asyncio.run(generate_llm_response("x"))
    check(result == "ok", "key priority unchanged")
print("T7 PASS")

print(f"\n{'='*50}")
print(f"LLM RETRY SAFETY: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
