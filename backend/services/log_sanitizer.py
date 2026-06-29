"""轻量日志脱敏：mask 手机号/openid/token/key/secret/完整地址。不误伤普通单词。"""
import re

# 仅 mask key=value 或 Authorization: Bearer 上下文中的敏感值
_PARAM_MASK = re.compile(
    r'(?i)((?:[?&]|^)(?:access_token|pay_sig|paysig|paysign|pay_sign|secret|api_key|token|unionid|wx_unionid)=)[^&\s]*'
)
_AUTH_BEARER = re.compile(r'(Authorization:\s*Bearer\s+)[^\s,;]+', re.I)
_PHONE = re.compile(r'\b(1[3-9]\d)\d{4}(\d{4})\b')
_OPENID = re.compile(r'\b(o[A-Za-z0-9_-]{6})[A-Za-z0-9_-]{6,}\b')
_SK_KEY = re.compile(r'\b(sk-[A-Za-z0-9]{4})[A-Za-z0-9]{6,}\b')
_JWT_BODY = re.compile(r'(eyJ[A-Za-z0-9_-]{6})[A-Za-z0-9._-]{15,}')


def sanitize_log(msg: str) -> str:
    """脱敏日志消息：key=value 参数、Authorization Bearer、手机号/openid/sk-key/JWT。"""
    msg = _PARAM_MASK.sub(r'\1***', msg)
    msg = _AUTH_BEARER.sub(r'Authorization: Bearer ***', msg)
    msg = _OPENID.sub(r'\1***', msg)
    msg = _JWT_BODY.sub(r'\1***', msg)
    msg = _SK_KEY.sub(r'\1***', msg)
    msg = _PHONE.sub(r'\1****\2', msg)
    return msg


def safe_user_id(uid) -> str:
    return f"u={uid}"


def safe_report_uuid(ruuid: str) -> str:
    return f"rpt={ruuid[:8]}" if ruuid else "rpt=?"


def safe_addr(addr: str) -> str:
    return (addr or "")[:6] + "..." if addr and len(addr) > 6 else (addr or "")


def safe_log(prefix: str, **fields) -> None:
    parts = [prefix]
    for k, v in fields.items():
        if v is None:
            continue
        sv = str(v)
        if k in ("phone", "openid", "unionid", "address"):
            sv = safe_addr(sv) if k == "address" else "***"
        elif k in ("token", "api_key", "secret", "access_token", "pay_sig"):
            sv = "***"
        elif len(sv) > 200:
            sv = sv[:200] + "..."
        parts.append(f"{k}={sv}")
    print(sanitize_log(" ".join(parts)), flush=True)
