"""
统一大模型调用入口
generate_llm_response(prompt) —— 业务代码只调用这一个函数
切换模型只需修改 .env 中 LLM_PROVIDER / LLM_MODEL / LLM_BASE_URL / LLM_API_KEY
安全重试：timeout/5xx/网络异常最多额外重试 1 次，4xx 不重试。
"""
import httpx, time
from services.runtime_config import get_llm_config

_MAX_RETRIES = 1  # 额外重试次数


def _should_retry(status: int) -> bool:
    """5xx / timeout / 网络异常可重试，4xx 不重试。"""
    return status in (502, 503, 504)


async def generate_llm_response(prompt: str) -> str:
    """调用当前激活的大模型，返回响应文本。timeout/5xx/网络异常最多重试 1 次。"""
    cfg = get_llm_config()
    if not cfg.get("api_key"):
        provider = cfg.get("provider", "LLM")
        src = cfg.get("key_source", "missing")
        if src == "missing":
            raise RuntimeError(
                f"{provider} API Key 未配置。请设置环境变量 {provider.upper()}_API_KEY "
                f"或在后台「核心配置」中填写 AI Key"
            )
        raise RuntimeError(
            f"{provider} API Key 不可用（当前来源: {src}），"
            f"请检查对应配置是否正确"
        )
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 6144,
    }

    url = f"{cfg['base_url']}/chat/completions"
    provider = cfg.get("provider", "?")
    last_exc = None

    for attempt in range(_MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=90) as client:
                t0 = time.time()
                resp = await client.post(url, headers=headers, json=body)
                elapsed_ms = int((time.time() - t0) * 1000)
                status = resp.status_code

                if status < 400:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]

                # 4xx / 5xx
                if _should_retry(status) and attempt < _MAX_RETRIES:
                    print(f"[LLM] {provider} {status} retry attempt={attempt+1} elapsed={elapsed_ms}ms", flush=True)
                    continue

                resp.raise_for_status()

        except (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError,
                httpx.ReadError, httpx.NetworkError) as e:
            last_exc = e
            err_type = type(e).__name__
            if attempt < _MAX_RETRIES:
                print(f"[LLM] {provider} {err_type} retry attempt={attempt+1}", flush=True)
                continue
            print(f"[LLM] {provider} {err_type} exhausted attempts={attempt+1}", flush=True)
            try:
                from services.abuse_monitor import note_service_fail
                note_service_fail("LLM")
            except Exception: pass
            raise RuntimeError(
                f"{provider} 请求失败（{err_type}），请稍后重试"
            ) from e

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if 400 <= status < 500:
                raise RuntimeError(
                    f"{provider} 请求被拒绝（HTTP {status}），请检查 API Key 和模型配置"
                ) from e
            if _should_retry(status) and attempt < _MAX_RETRIES:
                print(f"[LLM] {provider} {status} retry attempt={attempt+1}", flush=True)
                continue
            try:
                from services.abuse_monitor import note_service_fail
                note_service_fail("LLM")
            except Exception: pass
            raise RuntimeError(
                f"{provider} 服务暂不可用（HTTP {status}），请稍后重试"
            ) from e

    if last_exc:
        raise RuntimeError(f"{provider} 请求多次失败，请稍后重试") from last_exc
    raise RuntimeError(f"{provider} 请求多次失败，请稍后重试")
