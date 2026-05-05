"""
统一配置中心
切换大模型只需修改 .env 中 LLM_PROVIDER / LLM_MODEL / LLM_BASE_URL / LLM_API_KEY
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# JWT 鉴权配置
# ==========================================
JWT_SECRET = os.getenv("JWT_SECRET", "location-tool-jwt-secret-change-in-production")

# ★ 启动安全断言：禁止使用默认弱密钥启动服务
_DEFAULT_SECRETS = {
    "location-tool-jwt-secret-change-in-production",
    "change-this-to-a-random-secret-in-production",
}
if JWT_SECRET in _DEFAULT_SECRETS:
    raise ValueError(
        "\n" + "=" * 68 + "\n"
        "  CRITICAL: 检测到使用了默认的 JWT_SECRET！\n"
        "  该密钥与 .env.example 中的示例值一致，极易被攻击者伪造 Token。\n"
        "  请立即在 backend/.env 中将 JWT_SECRET 配置为高强度随机字符串。\n"
        "  示例：python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
        + "=" * 68
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "168"))

# ==========================================
# 新用户注册奖励配置
# ==========================================
SIGNUP_BONUS_CREDITS = int(os.getenv("SIGNUP_BONUS_CREDITS", "3"))
SIGNUP_FREE_CREDITS = int(os.getenv("SIGNUP_FREE_CREDITS", "1"))
REGISTER_BONUS_CREDITS = int(os.getenv("REGISTER_BONUS_CREDITS", str(SIGNUP_BONUS_CREDITS)))

# ==========================================
# 微信公众号配置
# ==========================================
WECHAT_MP_APPID = os.getenv("WECHAT_MP_APPID", "")
WECHAT_MP_SECRET = os.getenv("WECHAT_MP_SECRET", "")

# ==========================================
# 当前激活的大模型配置（从 .env 读取）
# ==========================================
LLM_CONFIG = {
    "provider": os.getenv("LLM_PROVIDER", "deepseek"),
    "model": os.getenv("LLM_MODEL", "deepseek-chat"),
    "base_url": os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
    "api_key": os.getenv("LLM_API_KEY", os.getenv("DEEPSEEK_API_KEY", "")),
}

# ==========================================
# 各平台独立 Key（保留兼容）
# ==========================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
KIMI_API_KEY = os.getenv("KIMI_API_KEY", "")
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")

# 各平台独立配置（保留兼容——当用户通过前端指定provider时使用）
PROVIDER_CONFIG = {
    "gemini": {
        "model": "gemini-2.0-flash",
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "model": "moonshot-v1-8k",
    },
    "minimax": {
        "base_url": "https://api.minimax.chat/v1",
        "model": "abab6.5s-chat",
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "model": "glm-4-flash",
    },
}
