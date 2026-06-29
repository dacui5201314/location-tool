"""地址联想 / POI 搜索 — 后端代理高德 Web API，小程序端不暴露 Key
Key 池完整 failover：第一个 key 日限额/QPS 时自动尝试下一个。
安全：IP 限流、关键词最小长度、同 IP+词缓存。
"""
import os, httpx, time, hashlib
from fastapi import APIRouter, Query, Request
from starlette.responses import JSONResponse

from database import SessionLocal
from routers.admin import _get_amap_key_selector

router = APIRouter(prefix="/api/location", tags=["location"])

# ── 可配阈值 ──
_LOC_SUGGEST_MIN_KEYWORD = int(os.getenv("LOCATION_SUGGEST_MIN_LEN", "2"))
_LOC_CACHE_TTL = int(os.getenv("LOCATION_CACHE_TTL_SECONDS", "30"))
_LOC_SUGGEST_LIMIT_PER_MIN = int(os.getenv("LOCATION_SUGGEST_LIMIT_PER_MIN", "60"))
_LOC_REGEOCODE_LIMIT_PER_MIN = int(os.getenv("LOCATION_REGEOCODE_LIMIT_PER_MIN", "30"))

# ── 轻量内存缓存 + 限流 ──
_suggest_cache: dict[str, tuple[float, dict]] = {}   # key → (expires_at, result)
_suggest_cache_max = 2000
_suggest_rates: dict[str, list[float]] = {}
_suggest_rates_max = 5000
_regeocode_rates: dict[str, list[float]] = {}
_regeocode_rates_max = 5000


def _rate_check(rate_map: dict, client_ip: str, max_per_min: int, max_keys: int) -> bool:
    """IP 限流检查。返回 True 表示允许通过。"""
    now = time.time()
    timestamps = rate_map.get(client_ip, [])
    timestamps = [t for t in timestamps if t > now - 60]
    rate_map[client_ip] = timestamps
    if len(rate_map) > max_keys:
        oldest = min(rate_map, key=lambda k: rate_map[k][0] if rate_map[k] else now + 1)
        del rate_map[oldest]
    if len(timestamps) >= max_per_min:
        return False
    timestamps.append(now)
    return True


def _cache_key(cat: str, ip: str, kw: str, city: str = "") -> str:
    raw = f"{cat}|{ip}|{kw}|{city}"
    return hashlib.md5(raw.encode()).hexdigest()


def _get_all_keys():
    """从 DB Key 池取所有启用的 Key，按优先级排序。池空回退到 .env"""
    keys = []
    db = SessionLocal()
    try:
        from models.db_models import AmapKey
        rows = db.query(AmapKey).filter(AmapKey.enabled == 1).order_by(AmapKey.priority, AmapKey.id).all()
        for r in rows:
            if r.api_key:
                keys.append((r.api_key, r.security_secret or ""))
    finally:
        db.close()
    # env fallback
    env_key = os.getenv("AMAP_WEB_KEY", os.getenv("AMAP_KEY", ""))
    if env_key and not any(k == env_key for k, _ in keys):
        keys.append((env_key, ""))
    return keys


def _is_retryable_amap_error(data: dict) -> bool:
    """判断高德错误是否可重试（日限额 / QPS 超限）"""
    info = str(data.get("info", "") or "").upper()
    ic = str(data.get("infocode", "") or "")
    return "OVER_DAILY" in info or ic in ("10003", "10004") or "CUQPS" in info or ic == "10007"


async def _amap_request_with_retry(path: str, params: dict) -> dict:
    """使用完整 Key 池发起高德请求，遇日限额/QPS 自动切换下一个 Key。
    返回响应 JSON dict；全部 Key 失败时抛出 Exception。
    """
    all_keys = _get_all_keys()
    if not all_keys:
        raise Exception("AMAP_KEY_UNAVAILABLE: 无可用高德 Key")

    last_data = None
    for key, _sec in all_keys:
        p = {**params, "key": key}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://restapi.amap.com/v3{path}", params=p)
                data = resp.json()
                if data.get("status") == "1":
                    return data
                if _is_retryable_amap_error(data):
                    last_data = data
                    continue
                # 不可重试错误（如 INVALID_KEY），直接返回给调用方
                return data
        except Exception:
            continue

    if last_data:
        return last_data
    raise Exception("AMAP_ALL_KEYS_EXHAUSTED: 所有 Key 均不可用")


@router.get("/suggest")
async def location_suggest(
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query("", description="城市，可选"),
    request: Request = None,
):
    """地址联想：调用高德输入提示 API，返回候选列表。
    小程序端不保存、不暴露地图服务 Key。
    安全：最小关键词长度、IP 限流、同 IP+词缓存。
    Key 池完整 failover：日限额/QPS 超限自动切换下一个 Key。
    """
    keyword = (keyword or "").strip()
    city = (city or "").strip()
    from services.client_ip import get_client_ip
    client_ip = get_client_ip(request) if request else "127.0.0.1"

    # ── IP 限流 ──
    if not _rate_check(_suggest_rates, client_ip, _LOC_SUGGEST_LIMIT_PER_MIN, _suggest_rates_max):
        return JSONResponse(status_code=429, content={"ok": False, "error": "请求过于频繁，请稍后再试"})

    # ── 空关键词 ──
    if not keyword:
        return {"ok": True, "data": [], "source": "amap_inputtips"}

    # ── 最小关键词长度 ──
    if len(keyword) < _LOC_SUGGEST_MIN_KEYWORD:
        return {"ok": True, "data": [], "source": "amap_inputtips"}

    # ── 缓存 ──
    ck = _cache_key("suggest", client_ip, keyword, city)
    now = time.time()
    if ck in _suggest_cache:
        expires, cached_data = _suggest_cache[ck]
        if now < expires:
            return cached_data

    params = {
        "keywords": keyword,
        "datatype": "all",
        "output": "JSON",
    }
    if city:
        params["city"] = city

    try:
        data = await _amap_request_with_retry("/assistant/inputtips", params)
    except Exception as e:
        err_msg = str(e)
        if "AMAP_KEY_UNAVAILABLE" in err_msg or "AMAP_ALL_KEYS_EXHAUSTED" in err_msg:
            try:
                from services.abuse_monitor import note_service_fail
                note_service_fail("AMap")
            except Exception: pass
            return JSONResponse(status_code=503, content={"ok": False, "error": "地图服务未配置或所有 Key 已耗尽"})
        return JSONResponse(status_code=502, content={"ok": False, "error": "地图服务请求失败，请稍后重试"})

    if data.get("status") != "1":
        info = data.get("info", "unknown error")
        return JSONResponse(
            status_code=502,
            content={"ok": False, "error": f"地图服务返回错误：{info}"},
        )

    tips = data.get("tips")
    if not isinstance(tips, list):
        tips = []

    candidates = []
    for tip in tips:
        if not isinstance(tip, dict):
            continue
        loc_str = tip.get("location", "")
        if not loc_str:
            continue
        parts = loc_str.split(",")
        if len(parts) != 2:
            continue
        try:
            lng = float(parts[0])
            lat = float(parts[1])
        except (ValueError, TypeError):
            continue
        candidates.append({
            "name": tip.get("name", ""),
            "address": tip.get("address", "") or tip.get("district", ""),
            "location": {"lng": lng, "lat": lat},
        })

    result = {
        "ok": True,
        "data": candidates,
        "source": "amap_inputtips",
    }
    # ── 写缓存 ──
    if len(_suggest_cache) > _suggest_cache_max:
        oldest_ck = min(_suggest_cache, key=lambda k: _suggest_cache[k][0])
        del _suggest_cache[oldest_ck]
    _suggest_cache[ck] = (now + _LOC_CACHE_TTL, result)
    return result


@router.get("/regeocode")
async def location_regeocode(
    lng: float = Query(..., description="经度"),
    lat: float = Query(..., description="纬度"),
    request: Request = None,
):
    """反向地理编码：经纬度 → 文字地址。小程序端不暴露 Key。
    Key 池完整 failover：日限额/QPS 超限自动切换下一个 Key。
    """
    from services.client_ip import get_client_ip
    client_ip = get_client_ip(request) if request else "127.0.0.1"

    # ── IP 限流 ──
    if not _rate_check(_regeocode_rates, client_ip, _LOC_REGEOCODE_LIMIT_PER_MIN, _regeocode_rates_max):
        return JSONResponse(status_code=429, content={"ok": False, "error": "请求过于频繁，请稍后再试"})

    try:
        data = await _amap_request_with_retry("/geocode/regeo", {
            "location": f"{lng},{lat}", "extensions": "base", "output": "JSON",
        })
    except Exception as e:
        err_msg = str(e)
        if "AMAP_KEY_UNAVAILABLE" in err_msg or "AMAP_ALL_KEYS_EXHAUSTED" in err_msg:
            try:
                from services.abuse_monitor import note_service_fail
                note_service_fail("AMap")
            except Exception: pass
            return JSONResponse(status_code=503, content={"ok": False, "error": "地图服务未配置或所有 Key 已耗尽"})
        return JSONResponse(status_code=502, content={"ok": False, "error": "地图服务请求失败，请稍后重试"})

    if data.get("status") != "1":
        info = data.get("info", "unknown error")
        return JSONResponse(status_code=502, content={"ok": False, "error": f"地图服务返回错误：{info}"})

    regeo = data.get("regeocode", {})
    addr = regeo.get("addressComponent", {}) if isinstance(regeo, dict) else {}
    formatted = regeo.get("formatted_address", "") if isinstance(regeo, dict) else ""
    district = addr.get("district", "") if isinstance(addr, dict) else ""
    address = formatted or (district + (addr.get("township", "") if isinstance(addr, dict) else ""))

    return {
        "ok": True,
        "data": {
            "address": address or formatted,
            "formatted_address": formatted,
            "lng": lng,
            "lat": lat,
        },
        "source": "amap_regeocode",
    }
