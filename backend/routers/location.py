"""地址联想 / POI 搜索 — 后端代理高德 Web API，小程序端不暴露 Key"""
import os, httpx
from fastapi import APIRouter, Query
from starlette.responses import JSONResponse

from database import SessionLocal
from routers.admin import _get_amap_key_selector

router = APIRouter(prefix="/api/location", tags=["location"])


def _get_key():
    """从 key 池获取当前可用的高德 Key，池空则回退到 .env"""
    db = SessionLocal()
    try:
        key, _ = _get_amap_key_selector(db)
        return key
    finally:
        db.close()


@router.get("/suggest")
async def location_suggest(
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query("", description="城市，可选"),
):
    """地址联想：调用高德输入提示 API，返回候选列表。
    小程序端不保存、不暴露地图服务 Key。
    统一返回 { ok, data/error } + HTTP 状态码。
    """
    amap_key = _get_key()
    if not amap_key:
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": "地图服务未配置（AMAP Key 池为空且 .env 中未设置）"},
        )

    if not keyword.strip():
        return {"ok": True, "data": [], "source": "amap_inputtips"}

    params = {
        "key": amap_key,
        "keywords": keyword.strip(),
        "datatype": "all",
        "output": "JSON",
    }
    if city.strip():
        params["city"] = city.strip()

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://restapi.amap.com/v3/assistant/inputtips",
                params=params,
            )
            data = resp.json()
    except Exception:
        return JSONResponse(
            status_code=502,
            content={"ok": False, "error": "地图服务请求失败，请稍后重试"},
        )

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

    return {
        "ok": True,
        "data": candidates,
        "source": "amap_inputtips",
    }


@router.get("/regeocode")
async def location_regeocode(
    lng: float = Query(..., description="经度"),
    lat: float = Query(..., description="纬度"),
):
    """反向地理编码：经纬度 → 文字地址。小程序端不暴露 Key。"""
    amap_key = _get_key()
    if not amap_key:
        return JSONResponse(status_code=503, content={"ok": False, "error": "地图服务未配置（AMAP Key 池为空且 .env 中未设置）"})

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://restapi.amap.com/v3/geocode/regeo", params={
                "key": amap_key, "location": f"{lng},{lat}", "extensions": "base", "output": "JSON",
            })
            data = resp.json()
    except Exception:
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
