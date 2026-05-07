"""业态专属规则引擎 — 管理后台 CRUD + 前台匹配接口"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import update
from pydantic import BaseModel

from database import get_db
from models.db_models import BusinessIndustry, OperationLog
from auth import get_current_admin

router = APIRouter(prefix="/api/admin/industries", tags=["业态规则管理"])

public_router = APIRouter(prefix="/api/industries", tags=["业态公开接口"])


# ── Request Bodies ────────────────────────────────────────

class IndustryCreateBody(BaseModel):
    name: str
    exclusive_prompt: str = ""
    is_active: int = 1
    sort_order: int = 0
    reason: str = ""


class IndustryUpdateBody(BaseModel):
    name: str = ""
    exclusive_prompt: str | None = None
    is_active: int | None = None
    sort_order: int | None = None
    reason: str = ""


# ── Admin CRUD ────────────────────────────────────────────

@router.get("")
def list_industries(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """业态列表（按 sort_order 排序）"""
    items = db.query(BusinessIndustry).order_by(
        BusinessIndustry.sort_order.asc(),
        BusinessIndustry.id.asc()
    ).all()
    return {"industries": [item.to_dict() for item in items]}


@router.post("")
def create_industry(
    body: IndustryCreateBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """新增业态"""
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="业态名称不能为空")
    existing = db.query(BusinessIndustry).filter(BusinessIndustry.name == body.name.strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"业态「{body.name}」已存在")

    item = BusinessIndustry(
        name=body.name.strip(),
        exclusive_prompt=body.exclusive_prompt,
        is_active=body.is_active,
        sort_order=body.sort_order,
    )
    db.add(item)
    db.add(OperationLog(
        admin_id=admin.get("user_id", 0), user_id=0, type="INDUSTRY_CREATE",
        after_value=body.name.strip(),
        change_amount=f"排序:{body.sort_order}",
        reason=body.reason.strip() or "新增业态",
    ))
    db.commit()
    db.refresh(item)
    return {"ok": True, "industry": item.to_dict()}


@router.put("/{industry_id}")
def update_industry(
    industry_id: int,
    body: IndustryUpdateBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """更新业态信息（部分更新）"""
    item = db.query(BusinessIndustry).filter(BusinessIndustry.id == industry_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="业态不存在")

    changes = []
    if body.name and body.name.strip() and body.name.strip() != item.name:
        other = db.query(BusinessIndustry).filter(
            BusinessIndustry.name == body.name.strip(),
            BusinessIndustry.id != industry_id
        ).first()
        if other:
            raise HTTPException(status_code=400, detail=f"业态「{body.name}」已存在")
        item.name = body.name.strip()
        changes.append(f"名称→{body.name.strip()}")
    if body.exclusive_prompt is not None:
        item.exclusive_prompt = body.exclusive_prompt
        changes.append(f"专属Prompt({len(body.exclusive_prompt)}字符)")
    if body.is_active is not None:
        item.is_active = body.is_active
        changes.append(f"状态→{'启用' if body.is_active else '停用'}")
    if body.sort_order is not None:
        item.sort_order = body.sort_order
        changes.append(f"排序→{body.sort_order}")
    if body.reason and body.reason.strip():
        changes.append(f"备注:{body.reason.strip()}")

    if changes:
        db.add(OperationLog(
            admin_id=admin.get("user_id", 0), user_id=0, type="INDUSTRY_UPDATE",
            before_value=item.name,
            change_amount=", ".join(changes),
            reason=body.reason.strip() or "业态更新",
        ))
    db.commit()
    db.refresh(item)
    return {"ok": True, "industry": item.to_dict()}


@router.delete("/{industry_id}")
def delete_industry(
    industry_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """删除业态"""
    item = db.query(BusinessIndustry).filter(BusinessIndustry.id == industry_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="业态不存在")

    name = item.name
    db.add(OperationLog(
        admin_id=admin.get("user_id", 0), user_id=0, type="INDUSTRY_DELETE",
        before_value=name,
        change_amount="已删除",
    ))
    db.delete(item)
    db.commit()
    return {"ok": True, "message": f"已删除「{name}」"}


# ── 前台公开接口 ──────────────────────────────────────────

@public_router.get("/active")
def list_active_industries(db: Session = Depends(get_db)):
    """前台获取启用业态列表（供匹配用）"""
    items = db.query(BusinessIndustry).filter(
        BusinessIndustry.is_active == 1
    ).order_by(
        BusinessIndustry.sort_order.asc(),
        BusinessIndustry.id.asc()
    ).all()
    return {
        "industries": [
            {"id": item.id, "name": item.name or "", "sort_order": item.sort_order}
            for item in items
        ]
    }
