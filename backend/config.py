"""
统一配置中心
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# JWT 鉴权配置
# ==========================================
JWT_SECRET = os.getenv("JWT_SECRET", "location-tool-jwt-secret-change-in-production")

_DEFAULT_SECRETS = {
    "location-tool-jwt-secret-change-in-production",
    "change-this-to-a-random-secret-in-production",
}
if JWT_SECRET in _DEFAULT_SECRETS:
    raise ValueError(
        "\n" + "=" * 68 + "\n"
        "  CRITICAL: 检测到使用了默认的 JWT_SECRET！\n"
        "  请立即在 backend/.env 中将 JWT_SECRET 配置为高强度随机字符串。\n"
        "  示例：python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
        + "=" * 68
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "168"))
ADMIN_JWT_EXPIRY_HOURS = int(os.getenv("ADMIN_JWT_EXPIRY_HOURS", str(min(JWT_EXPIRY_HOURS, 4))))

# ==========================================
# 新用户注册奖励配置
# ==========================================
SIGNUP_BONUS_CREDITS = int(os.getenv("SIGNUP_BONUS_CREDITS", "3"))
SIGNUP_FREE_CREDITS = int(os.getenv("SIGNUP_FREE_CREDITS", "1"))

# ==========================================
# 微信公众号配置
# ==========================================
WECHAT_MP_APPID = os.getenv("WECHAT_MP_APPID", "")
WECHAT_MP_SECRET = os.getenv("WECHAT_MP_SECRET", "")
