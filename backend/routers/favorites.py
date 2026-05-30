"""收藏地址 API — JWT 鉴权"""
from math import radians, cos
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.db_models import SavedLocation, AnalysisRecord
from auth import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["收藏地址"])

TOLERANCE_M = 200  # 分析记录匹配容差（米）


class AddFavoriteBody(BaseModel):
    custom_name: str = ""
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


def _haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """近似哈弗辛距离（米），误差 < 0.5% 在 2km 范围内"""
    dlat = abs(lat1 - lat2)
    dlng = abs(lng1 - lng2)
    return ((dlat * 111320) ** 2 + (dlng * 111320 * cos(radians((lat1 + lat2) / 2))) ** 2) ** 0.5


def _match_reports_sql(db: Session, user_id: int, locations: list) -> list[dict]:
    """SQL bounding-box 预筛选 + Python 精确哈弗辛匹配。
    对每页 20 个收藏，仅加载其附近 ~200m 范围的报告候选，
    避免全量拉取用户所有历史报告导致 OOM。"""
    from sqlalchemy import and_, or_

    if not locations:
        return []

    # 构造 bounding-box OR 条件：每个收藏周围 ±0.002° (≈200m)
    box_conds = []
    for loc in locations:
        box_conds.append(and_(
            AnalysisRecord.user_id == user_id,
            AnalysisRecord.latitude.between(loc.latitude - 0.002, loc.latitude + 0.002),
            AnalysisRecord.longitude.between(loc.longitude - 0.002, loc.longitude + 0.002),
        ))

    candidates = db.query(AnalysisRecord).filter(or_(*box_conds)).all()

    # 精确哈弗辛匹配
    result = []
    for loc in locations:
        best = None
        best_dist = float('inf')
        for r in candidates:
            dist = _haversine_m(loc.latitude, loc.longitude, r.latitude, r.longitude)
            if dist < TOLERANCE_M and dist < best_dist:
                best_dist = dist
                best = r
        if best:
            result.append(_enriched_fav(loc, best))
        else:
            result.append(_empty_fav(loc))
    return result


def _enriched_fav(loc: SavedLocation, report: AnalysisRecord) -> dict:
    return {
        **loc.to_dict(),
        "is_analyzed": True,
        "report_id": report.id,
        "report_uuid": report.report_uuid or "",  # ★ 公开 UUID，供前端跳转
        "report_overall_score": report.overall_score,
        "report_created_at": report.created_at.isoformat() if report.created_at else None,
        "report_business_type": report.business_type or "",
        "report_store_size": report.store_size or 0,
        "report_brand_desc": report.brand_desc or "",
        "report_address": report.address or "",
    }


def _empty_fav(loc: SavedLocation) -> dict:
    return {
        **loc.to_dict(),
        "is_analyzed": bool(loc.latest_report_uuid),
        "report_uuid": loc.latest_report_uuid or "",
        "report_id": None,
        "report_overall_score": None,
        "report_created_at": None,
        "report_business_type": "",
        "report_store_size": 0,
        "report_brand_desc": "",
        "report_address": "",
    }


@router.get("")
def list_favorites(
    user: dict = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取用户收藏列表，跨表注入 is_analyzed 和 report_id。
    ★ SQL 层面完成关联匹配：Lat/Lng 约束做 bounding-box 预筛选，
    仅对候选记录做精确哈弗辛匹配，分页在 DB 层完成，杜绝 OOM。"""
    user_id = user["user_id"]

    # ── 收藏列表分页（SQL 层 offset/limit）──
    query = db.query(SavedLocation).filter(
        SavedLocation.user_id == user_id
    ).order_by(SavedLocation.created_at.desc())

    total = query.count()
    locations = query.offset((page - 1) * page_size).limit(page_size).all()

    if not locations:
        return {"favorites": [], "total": total, "page": page, "page_size": page_size}

    # ── SQL bounding-box 预筛选：仅拉取收藏附近 (~200m) 的报告 ──
    enriched = _match_reports_sql(db, user_id, locations)

    return {"favorites": enriched, "total": total, "page": page, "page_size": page_size}


@router.get("/check")
def check_favorite(
    user: dict = Depends(get_current_user),
    latitude: float = Query(...),
    longitude: float = Query(...),
    db: Session = Depends(get_db),
):
    """检查指定坐标是否已被收藏，返回收藏ID。
    ★ SQL bounding-box 预筛选：仅查询坐标 ±0.001° (≈100m) 范围内的收藏，
    再在 Python 做精确哈弗辛匹配，杜绝全量加载。"""
    user_id = user["user_id"]
    locations = db.query(SavedLocation).filter(
        SavedLocation.user_id == user_id,
        SavedLocation.latitude.between(latitude - 0.001, latitude + 0.001),
        SavedLocation.longitude.between(longitude - 0.001, longitude + 0.001),
    ).all()
    best = None
    best_dist = float('inf')
    for loc in locations:
        dlat = abs(loc.latitude - latitude)
        dlng = abs(loc.longitude - longitude)
        dist_m = ((dlat * 111320) ** 2 + (dlng * 111320 * cos(radians(latitude))) ** 2) ** 0.5
        if dist_m < 100 and dist_m < best_dist:
            best_dist = dist_m
            best = loc
    if best:
        return {"is_favorited": True, "favorite_id": best.id}
    return {"is_favorited": False, "favorite_id": None}


@router.post("")
def add_favorite(body: AddFavoriteBody, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """添加收藏"""
    user_id = user["user_id"]
    loc = SavedLocation(
        user_id=user_id,
        custom_name=body.custom_name,
        address=body.address,
        latitude=body.latitude,
        longitude=body.longitude,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return {"ok": True, "favorite": loc.to_dict()}


@router.delete("/{favorite_id}")
def delete_favorite(
    favorite_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """取消收藏"""
    user_id = user["user_id"]
    loc = db.query(SavedLocation).filter(
        SavedLocation.id == favorite_id,
        SavedLocation.user_id == user_id,
    ).first()
    if not loc:
        raise HTTPException(status_code=404, detail="收藏不存在")
    db.delete(loc)
    db.commit()
    return {"ok": True, "deleted_id": favorite_id}
