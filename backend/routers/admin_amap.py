"""AMap Key 池管理路由（从 admin.py 拆分）。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, BaseModel as _BaseModel
from database import get_db
from models.db_models import AmapKey as _AmapKey
from auth import get_current_admin
from datetime import datetime as _dt
import os, httpx, time as _time

_CLEAR_SENTINEL = "__CLEAR__"

amap_router = APIRouter(prefix="/api/admin", tags=["AMap Key 池"])

# ═══════════════════════════════════════════

class _AmapKeyBody(_BaseModel):
    name: str = ""
    api_key: str = ""
    security_secret: str = ""
    enabled: bool = True
    priority: int = 0
    clear_security_secret: bool = False

@amap_router.get("/amap-keys")
def list_amap_keys(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Key 池列表 — 不返回明文"""
    rows = db.query(_AmapKey).order_by(_AmapKey.priority, _AmapKey.id).all()
    return {"keys": [r.to_dict_admin() for r in rows], "total": len(rows)}

@amap_router.post("/amap-keys")
def create_amap_key(body: _AmapKeyBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """新增 Key"""
    if not body.api_key.strip():
        raise HTTPException(status_code=400, detail="API Key 不能为空")
    row = _AmapKey(
        name=body.name.strip(),
        api_key=body.api_key.strip(),
        security_secret=body.security_secret.strip(),
        enabled=1 if body.enabled else 0,
        priority=body.priority,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "key": row.to_dict_admin()}

@amap_router.put("/amap-keys/{key_id}")
def update_amap_key(key_id: int, body: _AmapKeyBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """编辑 Key — 空 api_key 字段表示保留原值"""
    row = db.query(_AmapKey).filter(_AmapKey.id == key_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Key 不存在")
    if body.name.strip():
        row.name = body.name.strip()
    if body.api_key.strip():
        row.api_key = body.api_key.strip()
    if body.security_secret.strip() and body.security_secret.strip() != _CLEAR_SENTINEL:
        row.security_secret = body.security_secret.strip()
    if body.clear_security_secret or body.security_secret.strip() == _CLEAR_SENTINEL:
        row.security_secret = ""
    row.enabled = 1 if body.enabled else 0
    row.priority = body.priority
    db.commit()
    return {"ok": True, "key": row.to_dict_admin()}

@amap_router.delete("/amap-keys/{key_id}")
def delete_amap_key(key_id: int, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """删除 Key"""
    row = db.query(_AmapKey).filter(_AmapKey.id == key_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Key 不存在")
    db.delete(row)
    db.commit()
    return {"ok": True}

@amap_router.post("/amap-keys/{key_id}/test")
def test_amap_key(key_id: int, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """连通性测试 — 调高德逆地理编码轻量接口"""
    row = db.query(_AmapKey).filter(_AmapKey.id == key_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Key 不存在")
    import httpx as _httpx
    from datetime import datetime as _dt

    key = row.api_key
    if not key:
        return {"ok": False, "status": "0", "info": "Key 未配置", "infocode": "KEY_EMPTY", "normalized_status": "INVALID_USER_KEY"}

    params = {"key": key, "location": "116.3975,39.9087"}
    try:
        resp = _httpx.get("https://restapi.amap.com/v3/geocode/regeo", params=params, timeout=10)
        data = resp.json()
        st = str(data.get("status", ""))
        info = str(data.get("info", "") or "")[:200]
        ic = str(data.get("infocode", "") or "")
    except Exception as e:
        st = "0"
        info = str(e)[:200]
        ic = "NETWORK_ERROR"

    _info_upper = info.upper()
    normalized = "OK" if st == "1" else (
        "DAILY_QUERY_OVER_LIMIT" if "OVER_DAILY" in _info_upper or ic in ("10003", "10004") else
        "QPS_EXCEEDED" if "CUQPS" in _info_upper or ic == "10007" else
        "USERKEY_PLAT_NOMATCH" if "PLAT_NOMATCH" in _info_upper or ic == "10005" else
        "INVALID_USER_KEY" if ic in ("10001", "20001", "20002", "20003") else
        "SIGNATURE_REQUIRED" if "SIGN" in _info_upper or ic in ("10006",) else
        "NETWORK_ERROR" if ic == "NETWORK_ERROR" else
        "UNKNOWN_ERROR"
    )

    # Human-readable messages
    _human = {
        "OK": "高德 Web服务 Key 可用",
        "DAILY_QUERY_OVER_LIMIT": "该 Key 今日额度已用完，请添加新的 Web服务 Key 或等待额度恢复",
        "QPS_EXCEEDED": "QPS 超限，系统将自动切换其他 Key",
        "USERKEY_PLAT_NOMATCH": "Key 平台/服务类型不匹配，请使用高德 Web服务 API Key（非微信小程序 Key 或 JS API Key）",
        "INVALID_USER_KEY": "Key 无效，请检查是否复制完整或已过期",
        "SIGNATURE_REQUIRED": "需要安全密钥签名，当前未启用 sig 签名",
        "NETWORK_ERROR": "网络连接失败，请检查服务器网络",
        "UNKNOWN_ERROR": f"未知错误: {info[:60]}",
    }

    row.last_status = normalized
    row.last_info = info
    row.last_infocode = ic
    row.last_checked_at = _dt.utcnow()
    if normalized != "OK":
        row.fail_count = (row.fail_count or 0) + 1
    else:
        row.fail_count = 0
    db.commit()

    return {
        "ok": st == "1",
        "status": st,
        "info": info,
        "infocode": ic,
        "normalized_status": normalized,
        "human_message": _human.get(normalized, _human["UNKNOWN_ERROR"]),
        "source": "direct_test",
    }

# ═══════════════════════════════════════════
# 高德 Key 选择器 — 统一入口
# ═══════════════════════════════════════════
def _get_amap_key_selector(db: Session):
    """返回 (api_key, security_secret) 优先从 DB 池选"""
    rows = db.query(_AmapKey).filter(_AmapKey.enabled == 1).order_by(_AmapKey.priority, _AmapKey.id).all()
    if rows:
        r = rows[0]
        return r.api_key, (r.security_secret or "")
    # fallback to env
    import os as _os
    return _os.getenv("AMAP_WEB_KEY", _os.getenv("AMAP_KEY", "")), ""

def _report_amap_key_failure(db: Session, key_str: str, status: str, info: str = "", infocode: str = ""):
    """标记 Key 失败状态"""
    if not key_str:
        return
    row = db.query(_AmapKey).filter(_AmapKey.api_key == key_str, _AmapKey.enabled == 1).first()
    if row:
        row.last_status = status
        row.last_info = info[:200] if info else ""
        row.last_infocode = infocode[:20] if infocode else ""
        row.last_checked_at = _dt.utcnow()
        row.fail_count = (row.fail_count or 0) + 1
        db.commit()

# ═══════════════════════════════════════════════════════════
# 报告库 — 运营查看所有已生成报告
# ═══════════════════════════════════════════════════════════

def _parse_report_type(report_json_str: str) -> str:
    """从 report_json 安全解析报告类型"""
    if not report_json_str:
        return "ai"
    try:
        rj = json.loads(report_json_str) if isinstance(report_json_str, str) else report_json_str
        if isinstance(rj, dict):
            if rj.get("_fallback_report"):
                return "fallback"
            if rj.get("_fact_retry") and rj.get("_fact_retry_passed"):
                return "retry_ai"
    except Exception:
        pass
    return "ai"

class ReportsQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    q: str = ""
    user_id: int = 0
    business_type: str = ""
    score_min: int = 0
    score_max: int = 100
    date_from: str = ""
    date_to: str = ""
    report_type: str = ""

