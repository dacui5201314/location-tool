"""地址联想 / POI 搜索 — 后端代理高德 Web API，小程序端不暴露 Key"""
import os, httpx
from fastapi import APIRouter, Query, HTTPException

router = APIRouter(prefix="/api/location", tags=["location"])

AMAP_KEY = os.getenv("AMAP_WEB_KEY", os.getenv("AMAP_KEY", ""))


@router.get("/suggest")
async def location_suggest(
    keyword: str = Query(..., description="搜索关键词"),
    city: str = Query("", description="城市，可选"),
):
    """地址联想：调用高德输入提示 API，返回候选列表。
    小程序端不保存、不暴露地图服务 Key。
    """
    if not AMAP_KEY:
        raise HTTPException(status_code=503, detail="地图服务未配置（AMAP_WEB_KEY 缺失）")

    if not keyword.strip():
        return {"ok": True, "data": [], "source": "amap_inputtips"}

    params = {
        "key": AMAP_KEY,
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
        raise HTTPException(status_code=502, detail="地图服务请求失败，请稍后重试")

    if data.get("status") != "1":
        info = data.get("info", "unknown error")
        raise HTTPException(status_code=502, detail=f"地图服务返回错误：{info}")

    tips = data.get("tips", [])
    # 只返回有 location 的候选项
    candidates = []
    for tip in tips:
        loc_str = tip.get("location", "")
        if not loc_str:
            continue
        parts = loc_str.split(",")
        if len(parts) != 2:
            continue
        try:
            lng = float(parts[0])
            lat = float(parts[1])
        except ValueError:
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
