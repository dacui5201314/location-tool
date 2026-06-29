"""可信代理感知的客户端 IP 提取。仅信任 loopback / TRUSTED_PROXY_IPS 来源的 X-Forwarded-For。"""
import os, ipaddress
from fastapi import Request

_trusted_raw = (os.getenv("TRUSTED_PROXY_IPS", "127.0.0.1,::1") or "").strip()
_TRUSTED_PROXIES: set = set()
for _item in _trusted_raw.split(","):
    _item = _item.strip()
    if not _item:
        continue
    try:
        _TRUSTED_PROXIES.add(ipaddress.ip_network(_item, strict=False))
    except ValueError:
        # Not a valid IP/CIDR, skip
        pass


def _is_trusted(ip_str: str) -> bool:
    """判断 remote_addr 是否属于可信代理。"""
    if not ip_str:
        return False
    try:
        addr = ipaddress.ip_address(ip_str)
        for net in _TRUSTED_PROXIES:
            if addr in net:
                return True
    except ValueError:
        pass
    return False


def get_client_ip(request: Request) -> str:
    """安全提取客户端真实 IP。
    仅当 remote_addr 明确存在且属于可信代理时，才从 X-Forwarded-For 取第一个合法 IP。
    request.client 缺失或 remote_addr 为空 → 返回 "unknown"，不信任任何 XFF。
    """
    if not request.client:
        return "unknown"
    remote = request.client.host or ""
    if not remote:
        return "unknown"
    if not _is_trusted(remote):
        return remote
    xff = (request.headers.get("X-Forwarded-For") or "").strip()
    if not xff:
        return remote
    for part in xff.split(","):
        candidate = part.strip()
        if not candidate or candidate.lower() == "unknown":
            continue
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            continue
    return remote
