"""轻量微信外部 HTTP 封装：统一 timeout、有限 retry、安全日志。"""
import httpx, time, re
from services.log_sanitizer import sanitize_log

_WECHAT_TIMEOUT = httpx.Timeout(connect=10.0, read=15.0, write=10.0, pool=10.0)
_MAX_RETRIES = 1

_MASK_RE = re.compile(
    r'(?i)([?&](?:access_token|pay_sig|paysig|paysign|appid|secret|openid|api_key|signature)=)[^&]*'
)


def _safe_log(method: str, url: str, status: int, elapsed_ms: int, err: str = "") -> None:
    safe_url = _MASK_RE.sub(r'\1***', url)
    msg = sanitize_log(f"[WX-HTTP] {method} {safe_url[:160]} -> {status} {elapsed_ms}ms {err}")
    print(msg, flush=True)


async def wechat_get(url: str, timeout: httpx.Timeout = None, headers: dict = None) -> httpx.Response:
    """微信 GET 请求，带 retry。"""
    t = timeout or _WECHAT_TIMEOUT
    last_exc = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=t) as client:
                start = time.time()
                resp = await client.get(url, headers=headers or {})
                elapsed = int((time.time() - start) * 1000)
                _safe_log("GET", url, resp.status_code, elapsed)
                if _should_retry(resp.status_code):
                    if attempt < _MAX_RETRIES:
                        continue
                    try:
                        from services.abuse_monitor import note_service_fail
                        note_service_fail("WeChat")
                    except Exception: pass
                return resp
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as e:
            last_exc = e
            _safe_log("GET", url, 0, 0, type(e).__name__)
            if attempt < _MAX_RETRIES:
                continue
            try:
                from services.abuse_monitor import note_service_fail
                note_service_fail("WeChat")
            except Exception: pass
            raise
    return resp  # unreachable but safe


async def wechat_post(url: str, content: bytes = None, json_data: dict = None,
                      timeout: httpx.Timeout = None, headers: dict = None) -> httpx.Response:
    """微信 POST 请求，带 retry。"""
    t = timeout or _WECHAT_TIMEOUT
    if headers is None:
        headers = {}
    if "Content-Type" not in headers:
        headers["Content-Type"] = "application/json"
    last_exc = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=t) as client:
                start = time.time()
                resp = await client.post(url, content=content, json=json_data, headers=headers)
                elapsed = int((time.time() - start) * 1000)
                _safe_log("POST", url, resp.status_code, elapsed)
                if _should_retry(resp.status_code):
                    if attempt < _MAX_RETRIES:
                        continue
                    try:
                        from services.abuse_monitor import note_service_fail
                        note_service_fail("WeChat")
                    except Exception: pass
                return resp
        except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError) as e:
            last_exc = e
            _safe_log("POST", url, 0, 0, type(e).__name__)
            if attempt < _MAX_RETRIES:
                continue
            try:
                from services.abuse_monitor import note_service_fail
                note_service_fail("WeChat")
            except Exception: pass
            raise
    return resp


def _should_retry(status: int) -> bool:
    return status in (502, 503, 504) or status >= 500


# ── sync 包装（用于同步函数中调用）──

def wechat_get_sync(url: str, timeout: httpx.Timeout = None, headers: dict = None) -> httpx.Response:
    """同步 GET，带 retry。"""
    import asyncio
    return asyncio.run(wechat_get(url, timeout, headers))


def wechat_post_sync(url: str, content: bytes = None, json_data: dict = None,
                     timeout: httpx.Timeout = None, headers: dict = None) -> httpx.Response:
    """同步 POST，带 retry。"""
    import asyncio
    return asyncio.run(wechat_post(url, content, json_data, timeout, headers))
