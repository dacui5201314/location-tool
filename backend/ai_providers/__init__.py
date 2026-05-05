from .base import BaseProvider
from .gemini import GeminiProvider
from .deepseek import DeepSeekProvider
from .kimi import KimiProvider
from .minimax import MinimaxProvider
from .zhipu import ZhipuProvider


def get_provider(name: str) -> BaseProvider:
    providers = {
        "gemini": GeminiProvider,
        "deepseek": DeepSeekProvider,
        "kimi": KimiProvider,
        "minimax": MinimaxProvider,
        "zhipu": ZhipuProvider,
    }
    if name not in providers:
        raise ValueError(f"Unknown provider: {name}. Available: {list(providers.keys())}")
    return providers[name]()
