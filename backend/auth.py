"""JWT 鉴权工具 — Token 签发、校验、FastAPI 依赖注入"""
import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, Header

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS, ADMIN_JWT_EXPIRY_HOURS


def create_token(user_id: int, role: str = "user") -> str:
    """签发 JWT Token。admin 角色使用更短的过期时间。"""
    expiry_hours = ADMIN_JWT_EXPIRY_HOURS if role == "admin" else JWT_EXPIRY_HOURS
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=expiry_hours),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """校验并解码 JWT Token，无效/过期时抛出 401"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="无效的 Token")


def get_current_user(authorization: str = Header("")) -> dict:
    """FastAPI 依赖：从 Authorization: Bearer <token> 解析当前用户。
    返回 {"user_id": int, "role": str}，鉴权失败抛出 401。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="需要 Bearer Token")
    token = authorization[7:]
    payload = decode_token(token)
    return {"user_id": payload["user_id"], "role": payload.get("role", "user")}


def get_current_admin(user: dict = Depends(get_current_user)) -> dict:
    """FastAPI 依赖：要求当前用户具有 admin 角色，否则 403"""
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user
