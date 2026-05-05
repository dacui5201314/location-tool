"""收藏地址 API — JWT 鉴权"""
from math import radians, cos
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.db_models import SavedLocation, AnalysisRecord
from auth import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["收藏地址"])


class AddFavoriteBody(BaseModel):
    custom_name: str = ""
    address: str = ""
    latitude: float = 0.0
    longitude: float = 0.0


def _find_nearest_report(db: Session, user_id: int, lat: float, lng: float, tolerance_m: int = 200):
    """在分析记录中查找距离最近的报告（容差200米内）"""
    records = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == user_id
    ).all()
    best = None
    best_dist = float('inf')
    for r in records:
        dlat = abs(r.latitude - lat)
        dlng = abs(r.longitude - lng)
        dist_m = ((dlat * 111320) ** 2 + (dlng * 111320 * cos(radians(lat))) ** 2) ** 0.5
        if dist_m < tolerance_m and dist_m < best_dist:
            best_dist = dist_m
            best = r
    return best


@router.get("")
def list_favorites(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户收藏列表，跨表注入 is_analyzed 和 report_id"""
    user_id = user["user_id"]
    locations = db.query(SavedLocation).filter(
        SavedLocation.user_id == user_id
    ).order_by(SavedLocation.created_at.desc()).all()

    result = []
    for loc in locations:
        item = loc.to_dict()
        report = _find_nearest_report(db, user_id, loc.latitude, loc.longitude)
        if report:
            item["is_analyzed"] = True
            item["report_id"] = report.id
            item["report_overall_score"] = report.overall_score
            item["report_created_at"] = report.created_at.isoformat() if report.created_at else None
            item["report_business_type"] = report.business_type or ""
            item["report_store_size"] = report.store_size or 0
            item["report_brand_desc"] = report.brand_desc or ""
            item["report_address"] = report.address or ""
        else:
            item["is_analyzed"] = False
            item["report_id"] = None
            item["report_overall_score"] = None
            item["report_created_at"] = None
            item["report_business_type"] = ""
            item["report_store_size"] = 0
            item["report_brand_desc"] = ""
            item["report_address"] = ""
        result.append(item)
    return {"favorites": result}


@router.get("/check")
def check_favorite(
    user: dict = Depends(get_current_user),
    latitude: float = Query(...),
    longitude: float = Query(...),
    db: Session = Depends(get_db),
):
    """检查指定坐标是否已被收藏，返回收藏ID"""
    user_id = user["user_id"]
    locations = db.query(SavedLocation).filter(
        SavedLocation.user_id == user_id
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
        return {"error": "收藏不存在"}
    db.delete(loc)
    db.commit()
    return {"ok": True, "deleted_id": favorite_id}
