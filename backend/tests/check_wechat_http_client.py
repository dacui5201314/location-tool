"""5.1A: unified wechat HTTP — timeout, retry, safe logging"""
import sys, os, json, io, contextlib
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock, AsyncMock
import httpx
from services.wechat_http import (
    wechat_get, wechat_post, _should_retry, _safe_log,
    _WECHAT_TIMEOUT, _MAX_RETRIES,
)

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


# ═══ T1: timeout defaults ═══
print("=== T1: timeout config ===")
check(_WECHAT_TIMEOUT.connect == 10.0, f"connect timeout: {_WECHAT_TIMEOUT.connect}")
check(_WECHAT_TIMEOUT.read == 15.0, f"read timeout: {_WECHAT_TIMEOUT.read}")
check(_MAX_RETRIES >= 1, f"retries >= 1: {_MAX_RETRIES}")
print("T1 PASS")

# ═══ T2: retry on 5xx, not on 4xx ═══
print("=== T2: retry logic ===")
for s in (502, 503, 504, 500):
    check(_should_retry(s), f"{s} retry")
for s in (400, 401, 403, 404, 200):
    check(not _should_retry(s), f"{s} no retry")
print("T2 PASS")

# ═══ T3: ReadError retry → succeeds on second attempt ═══
print("=== T3: ReadError retry ===")
async def _test_read_error_retry():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.get.side_effect = [httpx.ReadError("read failed"), mock_resp]
    with patch('services.wechat_http.httpx.AsyncClient', return_value=client_mock):
        resp = await wechat_get("https://test/url")
        check(resp.status_code == 200, f"ReadError retry succeeded: {resp.status_code}")
        check(client_mock.get.call_count == 2, f"called {client_mock.get.call_count} times")
import asyncio
asyncio.run(_test_read_error_retry())
print("T3 PASS")

# ═══ T4: 4xx no retry ═══
print("=== T4: 4xx no retry ===")
async def _test_4xx_no_retry():
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    client_mock = AsyncMock()
    client_mock.__aenter__.return_value = client_mock
    client_mock.post.return_value = mock_resp
    with patch('services.wechat_http.httpx.AsyncClient', return_value=client_mock):
        resp = await wechat_post("https://test/url", json_data={"x": 1})
        check(resp.status_code == 401, f"4xx returned: {resp.status_code}")
        check(client_mock.post.call_count == 1, f"4xx not retried: {client_mock.post.call_count} calls")
asyncio.run(_test_4xx_no_retry())
print("T4 PASS")

# ═══ T5: safe log — no secrets in stdout ═══
print("=== T5: safe log ===")
out = io.StringIO()
with contextlib.redirect_stdout(out):
    _safe_log("GET",
        "https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=wxAppId123&secret=SuperSecret456",
        200, 120)
logged = out.getvalue()
check(len(logged) > 0, "log output non-empty")
check("SuperSecret" not in logged, "secret not in log")
check("wxAppId" not in logged, "appid masked")
check("[WX-HTTP]" in logged, "log prefix present")
check("GET" in logged, "method in log")
check("200" in logged, "status in log")
print("T5 PASS")

# ═══ T6: safe log — regex masks all values, no partial leaks ═══
print("=== T6: safe log extended ===")
cases = [
    ("https://api.weixin.qq.com/xpay/query_order?access_token=AT_abc&pay_sig=SIG_xyz&openid=oTest&api_key=KEY123",
     ["AT_abc", "SIG_xyz", "oTest", "KEY123"],
     ["access_token=***", "pay_sig=***", "openid=***", "api_key=***"]),
    ("https://api.mch.weixin.qq.com/v3/pay?signature=SIG456&paySign=PS_789",
     ["SIG456", "PS_789"],
     ["signature=***", "paysign=***"]),
    ("https://api.weixin.qq.com/xpay/refund?access_token=TOK&secret=SEC&PaySig=PS2",
     ["TOK", "SEC", "PS2"],
     ["access_token=***", "secret=***", "paysig=***"]),
]
for url, secrets, must_have in cases:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        _safe_log("POST", url, 200, 50)
    logged = out.getvalue()
    for s in secrets:
        check(s not in logged, f"'{s}' not in log for {url[:50]}")
    for m in must_have:
        check(m.lower() in logged.lower(), f"'{m}' present in log for {url[:50]}")
# No partial leaks like SIG*** or oTes***
for url, _, _ in cases:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        _safe_log("POST", url, 200, 50)
    logged = out.getvalue()
    check("***" in logged, "*** placeholder present")
    check("SIG***" not in logged, "no SIG*** partial leak")
    check("oTes***" not in logged, "no oTes*** partial leak")
    check("KE***" not in logged, "no KE*** partial leak")
print("T6 PASS")

# ═══ T7: callers audit ═══
print("=== T7: callers audit ===")
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for fname, label in [
    ("routers/pay.py", "pay"),
    ("routers/virtual_pay.py", "vpay"),
]:
    src = open(os.path.join(backend_dir, fname), 'r', encoding='utf-8').read()
    check(("wechat_get" in src or "wechat_post" in src),
          f"{label} uses wechat_http helper")
    check("httpx.get(" not in src and "httpx.post(" not in src,
          f"{label} no raw httpx")
    check("urllib.request.urlopen" not in src,
          f"{label} no raw urllib")
# vpay response logging truncated, RID safe
vpay_src = open(os.path.join(backend_dir, "routers/virtual_pay.py"), 'r', encoding='utf-8').read()
check("[:4000]" not in vpay_src, "vpay no longer logs full response body")
check("rid_diag:" in vpay_src, "RID uses safe summary format")
print("T7 PASS")

# ═══ T8: helper exports ═══
print("=== T8: helper exports ===")
from services.wechat_http import wechat_get_sync, wechat_post_sync
check(callable(wechat_get), "wechat_get callable")
check(callable(wechat_post), "wechat_post callable")
check(callable(wechat_get_sync), "wechat_get_sync callable")
check(callable(wechat_post_sync), "wechat_post_sync callable")
print("T8 PASS")

print(f"\n{'='*50}")
print(f"WECHAT HTTP CLIENT: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
