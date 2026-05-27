"""
统一大模型调用入口
generate_llm_response(prompt) —— 业务代码只调用这一个函数
切换模型只需修改 .env 中 LLM_PROVIDER / LLM_MODEL / LLM_BASE_URL / LLM_API_KEY
"""
import httpx
from services.runtime_config import get_llm_config


async def generate_llm_response(prompt: str) -> str:
    """调用当前激活的大模型，返回响应文本"""
    cfg = get_llm_config()
    if not cfg.get("api_key"):
        raise RuntimeError(f"{cfg.get('provider', 'LLM')} API Key 未配置，请在后台核心配置中填写")
    headers = {
        "Authorization": f"Bearer {cfg['api_key']}",
        "Content-Type": "application/json",
    }
    body = {
        "model": cfg["model"],
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 6144,  # 选址报告 JSON 体量大（8 维 + POI 数据 + 财务测算），4096 可能截断 retry
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            f"{cfg['base_url']}/chat/completions",
            headers=headers,
            json=body,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
