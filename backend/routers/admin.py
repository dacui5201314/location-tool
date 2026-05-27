"""管理后台 API — JWT 鉴权 + Admin 角色校验"""
import os
import time as _time
import threading
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List
import random, string
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, update, or_
from pydantic import BaseModel, ConfigDict
from database import get_db
from models.db_models import User, AnalysisRecord, SavedLocation, RedeemCode, SystemConfig, OperationLog, BillingRecord
from auth import get_current_admin, get_current_user, create_token
from services.runtime_config import (
    CORE_CONFIG_DEFAULTS,
    PDF_CONFIG_DEFAULTS,
    get_core_config as load_core_config,
    get_pdf_config as load_pdf_config,
    get_skus as load_skus,
    get_user_skus as load_user_skus,
    save_skus as persist_skus,
    save_user_skus as persist_user_skus,
    clear_user_skus,
    set_config_values,
)
from routers.user import clean_avatar_url


router = APIRouter(prefix="/api/admin", tags=["管理后台"])

_ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
_WEAK_ADMIN_PASSWORDS = {"admin123", "admin", "password", "123456", "admin888", "888888", ""}
if _ADMIN_PASSWORD in _WEAK_ADMIN_PASSWORDS:
    raise ValueError(
        "\n" + "=" * 68 + "\n"
        "  SECURITY BLOCK: 检测到弱 ADMIN_PASSWORD！\n"
        "  管理后台密码不可为空，也不可使用常见弱密码。\n"
        "  请在 backend/.env 中设置强密码，例如：\n"
        "  ADMIN_PASSWORD=" + __import__("secrets").token_urlsafe(16) + "\n"
        "  （以上为本次生成的示例，请复制到 .env 中）\n"
        + "=" * 68
    )
ADMIN_PASSWORD = _ADMIN_PASSWORD
QRCODE_CONFIG_KEY = "OFFICIAL_QRCODE_URL"


def _asset_filename(url: str) -> str:
    if not url.startswith("/assets/"):
        return ""
    return url.rsplit("/", 1)[-1]


def _is_foreign_asset_url(url: str, tag: str) -> bool:
    filename = _asset_filename(url)
    if not filename:
        return False
    if tag == "cs" and filename == "official_qrcode.png":
        return True
    known_prefixes = {"brand_", "cs_"}
    return any(filename.startswith(prefix) for prefix in known_prefixes) and not filename.startswith(f"{tag}_")


# ── 管理员登录速率限制（防暴力破解）─────────────────────
_login_attempts: dict[str, list[float]] = {}
_login_lock = threading.Lock()
_LOGIN_RATE_LIMIT = 5       # 每分钟最多尝试次数
_LOGIN_RATE_WINDOW = 60.0   # 窗口（秒）


def _check_login_rate(client_ip: str) -> bool:
    """检查 IP 是否超过速率限制，返回 True=允许 False=拒绝"""
    now = _time.time()
    with _login_lock:
        attempts = _login_attempts.get(client_ip, [])
        # 清理过期记录
        attempts = [t for t in attempts if now - t < _LOGIN_RATE_WINDOW]
        if len(attempts) >= _LOGIN_RATE_LIMIT:
            _login_attempts[client_ip] = attempts  # 保持现状
            return False
        attempts.append(now)
        _login_attempts[client_ip] = attempts
        return True


class LoginBody(BaseModel):
    password: str


@router.post("/login")
def admin_login(body: LoginBody, request: Request):
    """管理员登录：密码校验通过后签发 JWT（role=admin）— 速率限制 5次/分钟"""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not _check_login_rate(client_ip):
        raise HTTPException(
            status_code=429,
            detail="登录尝试过于频繁，请 1 分钟后再试",
            headers={"Retry-After": "60"},
        )
    if body.password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="密码错误")
    token = create_token(user_id=0, role="admin")
    return {"ok": True, "token": token}


@router.get("/stats")
def get_stats(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """仪表盘统计数据（需管理员权限）"""

    total_users = db.query(User).count()
    total_reports = db.query(AnalysisRecord).count()
    today = date.today()
    today_users = db.query(User).filter(func.date(User.created_at) == today).count()
    today_reports = db.query(AnalysisRecord).filter(func.date(AnalysisRecord.created_at) == today).count()
    total_favorites = db.query(SavedLocation).count()

    return {
        "total_users": total_users,
        "total_reports": total_reports,
        "today_users": today_users,
        "today_reports": today_reports,
        "total_favorites": total_favorites,
        "api_remaining": "—",
    }


@router.get("/users")
def list_users(
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    phone: str = Query("", description="手机号或ID筛选"),
    member: str = Query("", description="会员筛选: 1=会员, 0=非会员"),
    channel: str = Query("", description="注册来源筛选"),
    date_from: str = Query("", description="注册起始日期 YYYY-MM-DD"),
    date_to: str = Query("", description="注册截止日期 YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """用户列表（需管理员权限）— 支持多条件筛选"""

    query = db.query(User)
    # 筛选条件
    if phone:
        # ★ 统一搜索：always OR phone + phone_number；纯数字时额外加 id
        conditions = [User.phone.contains(phone), User.phone_number.contains(phone)]
        if phone.isdigit():
            conditions.append(User.id == int(phone))
        query = query.filter(or_(*conditions))
    if member == "1":
        query = query.filter(User.membership_expiry != None, User.membership_expiry > datetime.now())
    elif member == "0":
        query = query.filter((User.membership_expiry == None) | (User.membership_expiry <= datetime.now()))
    if channel:
        query = query.filter(User.channel == channel)
    if date_from:
        try:
            d = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(User.created_at >= d)
        except ValueError:
            pass
    if date_to:
        try:
            d = datetime.strptime(date_to, "%Y-%m-%d")
            query = query.filter(User.created_at < func.date(d, '+1 day'))
        except ValueError:
            pass

    query = query.order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    user_ids = [u.id for u in users]
    report_counts = {}
    if user_ids:
        report_counts = dict(
            db.query(AnalysisRecord.user_id, func.count(AnalysisRecord.id))
            .filter(AnalysisRecord.user_id.in_(user_ids))
            .group_by(AnalysisRecord.user_id)
            .all()
        )

    result = []
    tier_labels = {"free": "非会员", "monthly": "月度", "quarterly": "季度", "yearly": "年度"}
    for u in users:
        result.append({
            "id": u.id,
            "phone": u.phone or u.phone_number or "",
            "phone_number": u.phone_number or "",
            "nickname": (u.nickname or "").strip(),
            "avatar_url": clean_avatar_url(u.avatar_url or ""),
            "balance_credits": u.balance_credits,
            "points": u.points,
            "membership_tier": u.membership_tier,
            "membership_label": tier_labels.get(u.membership_tier, "非会员"),
            "is_member": u.is_member,
            "membership_days_left": u.membership_days_left,
            "membership_expiry": u.membership_expiry.isoformat() if u.membership_expiry else None,
            "report_count": report_counts.get(u.id, 0),
            "channel": u.channel or "",
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })

    return {"total": total, "page": page, "users": result}


class AddCreditsBody(BaseModel):
    amount: int


@router.post("/users/{user_id}/add-credits")
def add_credits(
    user_id: int,
    body: AddCreditsBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """增加用户点数（需管理员权限）— 原子化 UPDATE 防并发覆盖"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # ★ 原子化 SQL：UPDATE ... SET balance_credits = balance_credits + amount
    # 杜绝 Python Read-Modify-Write 竞态——两管理员同时加点不会互相覆盖
    db.execute(
        update(User)
        .where(User.id == user_id)
        .values(balance_credits=User.balance_credits + body.amount)
    )
    db.commit()
    db.refresh(user)
    return {"ok": True, "user_id": user_id, "balance_credits": user.balance_credits}


@router.get("/orders")
def list_orders(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """充值记录列表（需管理员权限）"""
    return {"orders": [], "total": 0}


class ConfigBody(BaseModel):
    amap_key: str = ""
    ai_provider: str = "deepseek"
    ai_key: str = ""
    system_prompt: str = ""
    wx_mch_id: str = ""
    wx_app_id: str = ""
    wx_api_key: str = ""
    wx_cert_sn: str = ""
    wx_notify_url: str = ""
    wx_private_key_pem: str = ""
    wx_platform_cert_pem: str = ""
    clear_wx_private_key_pem: bool = False
    clear_wx_platform_cert_pem: bool = False


def _mask_core_config(raw: dict) -> dict:
    """统一脱敏 helper：GET /config 和 PUT /config 均使用此函数。
    敏感字段（ai_key、wx_api_key、wx_private_key_pem、wx_platform_cert_pem）
    不回传原文，仅返回 masked 指示器或空字符串。"""
    masked = dict(raw)
    # AI key 脱敏
    ai_key = (raw.get("ai_key") or "").strip()
    if ai_key:
        masked["ai_key_masked"] = ai_key[:4] + "****" + ai_key[-4:] if len(ai_key) > 8 else "****"
    masked["ai_key"] = ""
    # APIv3 key 脱敏
    wx_api_key = (raw.get("wx_api_key") or "").strip()
    if wx_api_key:
        masked["wx_api_key_masked"] = "****"
    masked["wx_api_key"] = ""
    # 商户私钥 PEM — 只返回 has 指示器
    if (raw.get("wx_private_key_pem") or "").strip():
        masked["has_wx_private_key_pem"] = True
    else:
        masked["has_wx_private_key_pem"] = False
    masked["wx_private_key_pem"] = ""
    # 平台证书 PEM
    if (raw.get("wx_platform_cert_pem") or "").strip():
        masked["has_wx_platform_cert_pem"] = True
    else:
        masked["has_wx_platform_cert_pem"] = False
    masked["wx_platform_cert_pem"] = ""
    return masked


@router.get("/config")
def get_config(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """获取核心系统配置（需管理员权限）。敏感字段通过 _mask_core_config 脱敏。"""
    return _mask_core_config(load_core_config(db))


@router.put("/config")
def save_config(body: ConfigBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存核心系统配置到数据库（需管理员权限，运行时读取生效）。
    防空值保护：空字符串或 None 的字段自动略过，绝不允许空值覆写真实密钥。
    证书 PEM 字段通过 clear_wx_*_pem 标志支持显式清空。"""
    config_map = {
        "amap_key": body.amap_key,
        "ai_provider": body.ai_provider,
        "ai_key": body.ai_key,
        "system_prompt": body.system_prompt,
        "wx_mch_id": body.wx_mch_id,
        "wx_app_id": body.wx_app_id,
        "wx_api_key": body.wx_api_key,
        "wx_cert_sn": body.wx_cert_sn,
        "wx_notify_url": body.wx_notify_url,
    }
    # ★ 防空值覆盖：strip() 后为空的值一律跳过，禁止空值覆写 DB 中的真实密钥
    filtered_map = {}
    skipped = []
    for key, value in config_map.items():
        if value and str(value).strip():
            filtered_map[key] = str(value).strip()
        else:
            skipped.append(key)
    # ★ PEM 证书字段单独处理：trim 后非空写入；空值保留现有；clear 标志显式清空
    # ★ 使用 cryptography 做真实解析校验，不依赖字符串包含检查
    pem_actions = []
    # 商户私钥
    pk_pem = (body.wx_private_key_pem or "").strip()
    if body.clear_wx_private_key_pem:
        filtered_map["wx_private_key_pem"] = ""
        pem_actions.append("清除商户私钥")
    elif pk_pem:
        try:
            from cryptography.hazmat.primitives import serialization as _ser
            _ser.load_pem_private_key(pk_pem.encode(), password=None)
        except Exception:
            raise HTTPException(status_code=400, detail="商户私钥格式无效")
        filtered_map["wx_private_key_pem"] = pk_pem
        pem_actions.append("更新商户私钥")
    # 平台证书
    plat_pem = (body.wx_platform_cert_pem or "").strip()
    if body.clear_wx_platform_cert_pem:
        filtered_map["wx_platform_cert_pem"] = ""
        pem_actions.append("清除平台证书")
    elif plat_pem:
        try:
            from cryptography import x509 as _x509
            _x509.load_pem_x509_certificate(plat_pem.encode())
        except Exception:
            raise HTTPException(status_code=400, detail="平台证书格式无效")
        filtered_map["wx_platform_cert_pem"] = plat_pem
        pem_actions.append("更新平台证书")
    # 持久化
    if filtered_map:
        set_config_values(filtered_map, {key: f"系统设置-{key}" for key in CORE_CONFIG_DEFAULTS}, db)
    # ★ 操作审计日志 — 只记录字段名，不记录值
    admin_id = admin.get("user_id", 0)
    logged_keys = list(filtered_map.keys()) if filtered_map else []
    if pem_actions:
        logged_keys = logged_keys + [f"PEM:{a}" for a in pem_actions]
    skipped_desc = ", ".join(skipped) if skipped else "无"
    db.add(OperationLog(
        admin_id=admin_id, user_id=0, type="SYSTEM_CONFIG",
        change_amount=", ".join(logged_keys) if logged_keys else "无变更",
        reason=f"系统配置变更 (跳过: {skipped_desc})",
    ))
    db.commit()
    return {
        "ok": True,
        "message": "配置已保存" + (f" ({'; '.join(pem_actions)})" if pem_actions else ""),
        "saved_fields": list(filtered_map.keys()) if filtered_map else [],
        "skipped_fields": skipped,
        "pem_actions": pem_actions,
        "config": _mask_core_config(load_core_config(db)),
    }


# ============================================================
# SKU 套餐管理
# ============================================================
class SkuItem(BaseModel):
    id: int = 0
    type: str = "points"
    label: str = ""
    price: str = "0"
    credits: int = 0
    badge: str = ""
    tier: str = ""
    duration_days: int = 0
    desc: str = ""
    visible: bool = True

class SkuListBody(BaseModel):
    items: List[SkuItem] = []


class ApplyUserSkuBody(BaseModel):
    item: SkuItem


@router.get("/skus")
def get_skus(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取套餐列表（需管理员权限）"""
    return {"skus": load_skus(db)}

@router.put("/skus")
def save_skus(body: SkuListBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存套餐配置（需管理员权限）"""
    items = [item.model_dump() for item in body.items]
    persist_skus(items, db)
    return {"ok": True, "skus": load_skus(db)}


@router.get("/users/{user_id}/skus")
def get_user_sku_config(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取某个用户实际可见套餐；无专属配置时继承全局套餐。"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    skus, inherited = load_user_skus(user_id, db)
    return {"user_id": user_id, "inherited": inherited, "skus": skus}


@router.put("/users/{user_id}/skus")
def save_user_sku_config(
    user_id: int,
    body: SkuListBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """保存某个用户的专属套餐配置；前端用户中心会优先显示这份配置。"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    items = [item.model_dump() for item in body.items]
    persist_user_skus(user_id, items, db)
    skus, inherited = load_user_skus(user_id, db)
    return {"ok": True, "user_id": user_id, "inherited": inherited, "skus": skus}


@router.delete("/users/{user_id}/skus")
def reset_user_sku_config(
    user_id: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """清除某个用户的专属套餐配置，恢复继承全局套餐。"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    clear_user_skus(user_id, db)
    skus, inherited = load_user_skus(user_id, db)
    return {"ok": True, "user_id": user_id, "inherited": inherited, "skus": skus}


@router.post("/users/{user_id}/apply-sku")
def apply_user_sku(
    user_id: int,
    body: ApplyUserSkuBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """把某个套餐实际应用到账户：点数包=加点数，会员套餐=延长会员截止日期。"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    item = body.item
    now = datetime.now()
    if item.type == "membership":
        default_days = {"monthly": 30, "quarterly": 90, "yearly": 365}
        tier = item.tier or "monthly"
        days = item.duration_days or default_days.get(tier, 30)
        base = db_user.membership_expiry if db_user.membership_expiry and db_user.membership_expiry > now else now
        db_user.membership_tier = tier
        db_user.membership_expiry = base + timedelta(days=days)
        message = f"已为用户开通/延长 {days} 天会员"
    else:
        credits = max(0, int(item.credits or 0))
        if credits <= 0:
            raise HTTPException(status_code=400, detail="点数包必须包含大于 0 的点数")
        # ★ 原子化 UPDATE 杜绝并发覆盖
        db.execute(
            update(User)
            .where(User.id == user_id)
            .values(balance_credits=User.balance_credits + credits)
        )
        message = f"已为用户增加 {credits} 点"

    db.commit()
    db.refresh(db_user)
    tier_labels = {"free": "非会员", "monthly": "月度", "quarterly": "季度", "yearly": "年度"}
    return {
        "ok": True,
        "message": message,
        "user": {
            "id": db_user.id,
            "balance_credits": db_user.balance_credits,
            "membership_tier": db_user.membership_tier,
            "membership_label": tier_labels.get(db_user.membership_tier, "非会员"),
            "is_member": db_user.is_member,
            "membership_days_left": db_user.membership_days_left,
            "membership_expiry": db_user.membership_expiry.isoformat() if db_user.membership_expiry else None,
        },
    }


# ============================================================
# 分配套餐（按 packageId 查 SKU 配置自动叠加点数/会员）
# ============================================================
class AssignPackageBody(BaseModel):
    packageId: int
    reason: str = ""


@router.post("/users/{user_id}/package")
def assign_package(
    user_id: int,
    body: AssignPackageBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """分配预设套餐：按 packageId 查找 SKU 配置，自动叠加点数或延长会员"""
    if not body.reason or not body.reason.strip():
        raise HTTPException(status_code=400, detail="操作备注不能为空")
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 从 SKU 配置中查找套餐
    skus = load_skus(db)
    pkg = next((s for s in skus if s.get("id") == body.packageId), None)
    if not pkg:
        raise HTTPException(status_code=404, detail="套餐不存在")
    if not pkg.get("visible", True):
        raise HTTPException(status_code=400, detail="该套餐已下架")

    now = datetime.now()
    if pkg["type"] == "membership":
        days = pkg.get("duration_days", 30)
        tier = pkg.get("tier", "monthly")
        base = db_user.membership_expiry if db_user.membership_expiry and db_user.membership_expiry > now else now
        db_user.membership_tier = tier
        db_user.membership_expiry = base + timedelta(days=days)
        message = f"已开通 {pkg['label']}（{days}天）"
    else:
        credits = pkg.get("credits", 0)
        if credits <= 0:
            raise HTTPException(status_code=400, detail="点数包必须包含大于0的点数")
        db.execute(update(User).where(User.id == user_id).values(balance_credits=User.balance_credits + credits))
        message = f"已分配 {pkg['label']}（+{credits}点）"

    # ★ 操作审计日志
    admin_id = admin.get("user_id", 0)
    db.add(OperationLog(
        admin_id=admin_id, user_id=user_id, type="ASSIGN_PACKAGE",
        before_value=f"点数:{db_user.balance_credits},会员:{db_user.membership_tier}",
        after_value=pkg['label'],
        change_amount=message, reason=body.reason.strip(),
    ))
    db.commit()
    db.refresh(db_user)
    print(f"[AUDIT] ASSIGN_PACKAGE admin={admin_id} user={user_id} pkg={body.packageId} reason={body.reason}", flush=True)
    return {"ok": True, "message": message, "balance_credits": db_user.balance_credits}


# ============================================================
# 调整点数（独立加减，不影响会员状态）
# ============================================================
class AdjustPointsBody(BaseModel):
    points: int
    reason: str = ""


@router.post("/users/{user_id}/points")
def adjust_points(
    user_id: int,
    body: AdjustPointsBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """独立调整点数（支持正负数），需填写操作备注"""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if body.points == 0:
        raise HTTPException(status_code=400, detail="点数不能为0")
    if not body.reason or not body.reason.strip():
        raise HTTPException(status_code=400, detail="操作备注不能为空")

    db.execute(
        update(User).where(User.id == user_id)
        .values(balance_credits=User.balance_credits + body.points)
    )
    # ★ 操作审计日志
    admin_id = admin.get("user_id", 0)
    db.add(OperationLog(
        admin_id=admin_id, user_id=user_id, type="ADJUST_POINTS",
        before_value=f"点数:{db_user.balance_credits}",
        after_value=str(db_user.balance_credits + body.points),
        change_amount=f"{'+' if body.points > 0 else ''}{body.points}点",
        reason=body.reason.strip(),
    ))
    db.commit()
    db.refresh(db_user)
    print(f"[AUDIT] ADJUST_POINTS admin={admin_id} user={user_id} points={body.points} reason={body.reason}", flush=True)
    return {"ok": True, "points_changed": body.points, "balance_credits": db_user.balance_credits, "reason": body.reason}


# ============================================================
# 核心 Prompt — 读取/热更新
# ============================================================
@router.get("/config/core-prompt")
@router.get("/config/get-core-prompt")  # 别名兼容
def get_core_prompt(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """获取当前 System Prompt（需管理员权限）— 若无自定义则返回默认Prompt"""
    prompt = _get_config_value(db, "system_prompt", "")
    if not prompt:
        from prompts.location_analysis import build_system_prompt
        prompt = build_system_prompt("")
    return {"system_prompt": prompt, "length": len(prompt), "is_default": not bool(_get_config_value(db, "system_prompt", ""))}


class PromptBody(BaseModel):
    system_prompt: str = ""


@router.post("/config/prompt")
def save_prompt(body: PromptBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """热更新 System Prompt 并记录审计日志"""
    set_config_values({"system_prompt": body.system_prompt}, {"system_prompt": "System Prompt 热更新"}, db)

    admin_id = admin.get("user_id", 0)
    db.add(OperationLog(
        admin_id=admin_id, user_id=0, type="PROMPT_UPDATE",
        change_amount=f"Prompt长度:{len(body.system_prompt)}字符",
        reason="Prompt热更新",
    ))
    db.commit()
    print(f"[AUDIT] PROMPT_UPDATE admin={admin_id} len={len(body.system_prompt)}", flush=True)
    return {"ok": True, "message": "Prompt 已保存并立即生效"}


# ============================================================
# 操作记录
# ============================================================
@router.get("/operation-logs")
def list_operation_logs(
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """操作审计日志列表（需管理员权限）"""
    query = db.query(OperationLog).order_by(OperationLog.created_at.desc())
    total = query.count()
    logs = query.offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "logs": [log.to_dict() for log in logs]}


# ============================================================
# 系统运行日志
# ============================================================

@router.get("/logs")
def get_logs(
    admin: dict = Depends(get_current_admin),
    level: str = Query("error"),
):
    """系统日志（需管理员权限）— 占位接口，保持前端兼容"""
    return {"logs": [], "total": 0, "deprecated": True, "note": "日志模块开发中"}

# ============================================================
# 全局 UI 配置（公告 / 客服）— DB 持久化 + 内存缓存
# ============================================================
_UI_CONFIG_KEYS = [
    "announcement",
    "cs_wechat",
    "cs_phone",
    "customer_service_name",
]

class UiConfigBody(BaseModel):
    announcement: str = ""
    cs_wechat: str = ""
    cs_phone: str = ""
    customer_service_name: str = ""
    customer_service_qr_url: str = ""


class CustomerServiceQrcodeBody(BaseModel):
    url: str = ""


def _load_ui_config_from_db(db: Session) -> dict:
    """从数据库加载 UI 配置，未配置项回退默认值"""
    cfg = {
        "announcement": "",
        "cs_wechat": "",
        "cs_phone": "",
        "customer_service_name": "",
    }
    for key in _UI_CONFIG_KEYS:
        row = db.query(SystemConfig).filter(SystemConfig.key == f"ui_{key}").first()
        if row and row.value:
            cfg[key] = row.value
    cfg["customer_service_qr_url"] = _get_customer_service_qrcode(db)
    return cfg


def _get_customer_service_qrcode(db: Session) -> str:
    return _get_qrcode_slot(db, "cs")


@router.get("/ui-config")
def get_ui_config(db: Session = Depends(get_db)):
    """获取 UI 配置（公开，从 DB 加载）"""
    return _load_ui_config_from_db(db)


# ═══════════════════════════════════════════
# 小程序分享设置
# ═══════════════════════════════════════════
_SHARE_CONFIG_KEYS = ["share_title", "share_image_url", "report_share_title_template", "share_cta_text"]
_SHARE_CONFIG_DEFAULTS = {
    "share_title": "址得选 - 商铺选址分析工具",
    "share_image_url": "",
    "report_share_title_template": "{address}选址分析报告",
    "share_cta_text": "我也要生成选址报告",
}


def _load_share_config(db: Session) -> dict:
    cfg = {}
    for key in _SHARE_CONFIG_KEYS:
        row = db.query(SystemConfig).filter(SystemConfig.key == f"share_{key}").first()
        cfg[key] = row.value if (row and row.value) else _SHARE_CONFIG_DEFAULTS.get(key, "")
    return cfg


@router.get("/share-config")
def get_share_config_admin(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """管理后台获取分享配置"""
    return _load_share_config(db)


@router.put("/share-config")
def save_share_config(body: dict, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """管理后台保存分享配置"""
    for key in _SHARE_CONFIG_KEYS:
        val = str(body.get(key, "") or "").strip()
        if key == "share_image_url" and val and not val.startswith("/assets/"):
            raise HTTPException(status_code=400, detail="图片路径必须以 /assets/ 开头，请通过上传接口上传")
        row = db.query(SystemConfig).filter(SystemConfig.key == f"share_{key}").first()
        if row:
            row.value = val
        else:
            db.add(SystemConfig(key=f"share_{key}", value=val, description=f"分享配置: {key}"))
    db.commit()
    return {"ok": True}


@router.get("/share-config/public")
def get_share_config_public(db: Session = Depends(get_db)):
    """公开获取分享配置（uni-app 使用）"""
    return _load_share_config(db)


@router.post("/share-config/upload-image")
def upload_share_image(
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """上传分享图片到 assets 目录"""
    import uuid as _uuid
    from pathlib import Path as _Path

    allowed_types = {"image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp"}
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {content_type}，仅支持 PNG/JPG/WebP")

    raw = file.file.read()
    if len(raw) > 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 1MB")

    if content_type == "image/png" and raw[:4] != b'\x89PNG':
        raise HTTPException(status_code=400, detail="无效的 PNG 文件")
    if content_type in ("image/jpeg", "image/jpg") and raw[:3] != b'\xff\xd8\xff':
        raise HTTPException(status_code=400, detail="无效的 JPEG 文件")

    ext = allowed_types[content_type]
    filename = f"share_{_uuid.uuid4().hex[:12]}{ext}"
    assets_dir = _Path("storage/assets/share")
    assets_dir.mkdir(parents=True, exist_ok=True)
    filepath = assets_dir / filename
    filepath.write_bytes(raw)

    url = f"/assets/share/{filename}"
    return {"url": url, "filename": filename}


@router.get("/customer-service-qrcode")
def get_customer_service_qrcode(db: Session = Depends(get_db)):
    """获取客服二维码 URL（公开，从 DB 加载并清洗污染值）"""
    return {"url": _get_customer_service_qrcode(db)}


@router.put("/customer-service-qrcode")
def save_customer_service_qrcode(
    body: CustomerServiceQrcodeBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """保存客服二维码 URL（需管理员权限）。"""
    url = _save_qrcode_slot(db, "cs", body.url)
    return {"ok": True, "url": url}


@router.put("/ui-config")
def save_ui_config(body: UiConfigBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存 UI 配置至数据库（需管理员权限，持久化不丢失）"""
    cfg = {
        "announcement": body.announcement,
        "cs_wechat": body.cs_wechat,
        "cs_phone": body.cs_phone,
        "customer_service_name": body.customer_service_name,
    }
    for key in _UI_CONFIG_KEYS:
        row = db.query(SystemConfig).filter(SystemConfig.key == f"ui_{key}").first()
        if row:
            row.value = cfg[key]
        else:
            db.add(SystemConfig(key=f"ui_{key}", value=cfg[key], description=f"UI配置-{key}"))
    db.commit()
    return {"ok": True, "config": {**cfg, "customer_service_qr_url": _get_customer_service_qrcode(db)}}


# ============================================================
# 兑换码 (CDK) 管理
# ============================================================
class GenCdkBody(BaseModel):
    prefix: str = "AI"
    count: int = 10
    credits: int = 1
    days_valid: int = 90

class ActivateCdkBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str = ""

@router.post("/cdk/generate")
def generate_cdk(body: GenCdkBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """生成兑换码（需管理员权限）"""
    batch_id = f"{body.prefix}-{datetime.now().strftime('%Y%m%d%H%M')}"
    expires = datetime.now() + timedelta(days=body.days_valid)
    codes = []
    for _ in range(body.count):
        chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        suffix = f"{chars[0:4]}-{chars[4:8]}-{chars[8:12]}"
        code_str = f"{body.prefix}-{suffix}"
        c = RedeemCode(code=code_str, credits=body.credits, batch_id=batch_id, expires_at=expires)
        db.add(c)
        codes.append(code_str)
    db.commit()
    return {"ok": True, "batch_id": batch_id, "count": len(codes), "codes": codes}

@router.get("/cdk/list")
def list_cdk(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """兑换码列表（需管理员权限）"""
    codes = db.query(RedeemCode).order_by(RedeemCode.created_at.desc()).limit(100).all()
    return {"codes": [c.to_dict() for c in codes]}

# ── CDK 激活速率限制（防暴力枚举）──────────────────────────
_CDK_RATE_WINDOW = 60      # 窗口：60 秒
_CDK_RATE_LIMIT = 5        # 每窗口最多 5 次尝试
_cdk_rate_map: dict[str, list[float]] = {}  # ip → [timestamps]

def _check_cdk_rate(request: Request) -> None:
    """基于客户端 IP 的滑动窗口速率限制，超出返回 429"""
    now = _time.time()
    ip = request.client.host if request.client else "unknown"
    # 清理过期记录
    window = now - _CDK_RATE_WINDOW
    timestamps = [t for t in _cdk_rate_map.get(ip, []) if t > window]
    if len(timestamps) >= _CDK_RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"尝试次数过多，请 {_CDK_RATE_WINDOW} 秒后再试",
        )
    timestamps.append(now)
    _cdk_rate_map[ip] = timestamps


@router.post("/cdk/activate")
def activate_cdk(
    body: ActivateCdkBody,
    request: Request,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """激活兑换码 — JWT 强身份绑定 + 事务原子性保护。
    流程：查验CDK → 增加点数 → 标记已用 → 审计流水 → 统一提交。
    任一环节失败整笔事务回滚，杜绝资产烧毁。"""
    _check_cdk_rate(request)

    code_str = body.code.strip().upper()
    user_id = int(user["user_id"])  # ★ 仅从 JWT 提取，请求体无 user_id 字段

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="当前用户不存在，请重新登录")

    # ── 1. 查验 CDK 是否存在且未过期 ──
    c = db.query(RedeemCode).filter(RedeemCode.code == code_str).first()
    if not c:
        raise HTTPException(status_code=404, detail="兑换码不存在")
    if c.expires_at and c.expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="该兑换码已过期")

    # ── 2. 给当前 JWT 对应的真实用户增加点数 ──
    db_user.balance_credits += c.credits

    # ── 3. 原子化标记 CDK 已使用（WHERE is_used == 0 消除 TOCTOU 窗口） ──
    result = db.execute(
        update(RedeemCode)
        .where(RedeemCode.code == code_str, RedeemCode.is_used == 0)
        .values(is_used=1, used_by=user_id, used_at=datetime.now())
    )
    if result.rowcount == 0:
        # CDK 已在竞态中被核销 → 回滚事务后报错
        db.rollback()
        raise HTTPException(status_code=400, detail="该兑换码已被使用")

    # ── 4. 写入审计流水 ──
    db.add(BillingRecord(
        user_id=user_id,
        amount=c.credits,
        balance_after=db_user.balance_credits,
        record_type="CDK_REDEEM",
        reason=f"兑换码激活: {code_str}",
    ))

    # ── 5. 所有操作确认无误，最后一步统一提交 ──
    db.commit()
    return {"ok": True, "credits_added": c.credits, "balance": db_user.balance_credits}


# ============================================================
# 搜索趋势看板
# ============================================================
@router.get("/trends")
def get_trends(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """搜索趋势看板（需管理员权限）— SQL 聚合替代全表 Python 遍历"""
    # ★ 使用 SQL GROUP BY + COUNT 在数据库层聚合，只返回 Top 10，杜绝 OOM
    biz_rows = (
        db.query(AnalysisRecord.business_type, func.count(AnalysisRecord.id).label("cnt"))
        .filter(AnalysisRecord.business_type != "", AnalysisRecord.business_type != None)
        .group_by(AnalysisRecord.business_type)
        .order_by(func.count(AnalysisRecord.id).desc())
        .limit(10)
        .all()
    )
    brand_rows = (
        db.query(AnalysisRecord.brand_desc, func.count(AnalysisRecord.id).label("cnt"))
        .filter(AnalysisRecord.brand_desc != "", AnalysisRecord.brand_desc != None)
        .group_by(AnalysisRecord.brand_desc)
        .order_by(func.count(AnalysisRecord.id).desc())
        .limit(10)
        .all()
    )
    return {
        "top_business_types": [{"name": r[0], "count": r[1]} for r in biz_rows],
        "top_brands": [{"name": r[0], "count": r[1]} for r in brand_rows],
    }


# ============================================================
# 仪表盘综合统计
# ============================================================
@router.get("/dashboard/stats")
def get_dashboard_stats(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """仪表盘聚合数据（需管理员权限）— 15天趋势 + 业态/品牌分布"""
    today = date.today()
    dates, counts = [], []
    for i in range(14, -1, -1):
        d = today - timedelta(days=i)
        dates.append(d.strftime("%m-%d"))
        cnt = db.query(func.count(AnalysisRecord.id)).filter(
            func.date(AnalysisRecord.created_at) == d
        ).scalar() or 0
        counts.append(cnt)

    biz_rows = (
        db.query(AnalysisRecord.business_type, func.count(AnalysisRecord.id).label("cnt"))
        .filter(AnalysisRecord.business_type != "", AnalysisRecord.business_type != None)
        .group_by(AnalysisRecord.business_type)
        .order_by(func.count(AnalysisRecord.id).desc())
        .limit(10)
        .all()
    )
    brand_rows = (
        db.query(AnalysisRecord.brand_desc, func.count(AnalysisRecord.id).label("cnt"))
        .filter(AnalysisRecord.brand_desc != "", AnalysisRecord.brand_desc != None)
        .group_by(AnalysisRecord.brand_desc)
        .order_by(func.count(AnalysisRecord.id).desc())
        .limit(5)
        .all()
    )
    return {
        "trend_dates": dates,
        "trend_counts": counts,
        "top_business_types": [{"name": r[0], "count": r[1]} for r in biz_rows],
        "top_brands": [{"name": r[0], "count": r[1]} for r in brand_rows],
    }


class PdfConfigBody(BaseModel):
    logo_url: str = ""
    footer_text: str = ""

@router.get("/pdf-config")
def get_pdf_config(db: Session = Depends(get_db)):
    """获取 PDF 品牌配置（公开：导出报告需要读取页眉页脚品牌信息）"""
    return load_pdf_config(db)

@router.put("/pdf-config")
def save_pdf_config(body: PdfConfigBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存 PDF 品牌配置（需管理员权限，DB 持久化）"""
    cfg = {"logo_url": body.logo_url, "footer_text": body.footer_text}
    set_config_values(cfg, {key: f"PDF配置-{key}" for key in PDF_CONFIG_DEFAULTS}, db)
    return {"ok": True, "config": load_pdf_config(db)}


# ============================================================
# 对象存储配置 (OSS/S3)
# ============================================================
_DEFAULT_STORAGE = {
    "storage_mode": "local",
    "oss_endpoint": "",
    "oss_bucket": "",
    "oss_access_key_id": "",
    "oss_access_key_secret": "",
}


def _load_storage_config(db: Session) -> dict:
    """从数据库加载存储配置"""
    cfg = dict(_DEFAULT_STORAGE)
    rows = db.query(SystemConfig).filter(SystemConfig.key.in_(cfg.keys())).all()
    for r in rows:
        if r.key in cfg:
            cfg[r.key] = r.value
    return cfg


def _save_storage_config(db: Session, cfg: dict):
    """保存存储配置到数据库"""
    for key, value in cfg.items():
        if key not in _DEFAULT_STORAGE:
            continue
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if row:
            row.value = value
        else:
            db.add(SystemConfig(key=key, value=value))
    db.commit()


class StorageConfigBody(BaseModel):
    storage_mode: str = "local"
    oss_endpoint: str = ""
    oss_bucket: str = ""
    oss_access_key_id: str = ""
    oss_access_key_secret: str = ""


@router.get("/storage-config")
def get_storage_config(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """获取对象存储配置（需管理员权限 — 含 OSS 密钥等敏感信息）"""
    return _load_storage_config(db)


@router.put("/storage-config")
def save_storage_config(body: StorageConfigBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存对象存储配置（需管理员权限）"""
    cfg = {
        "storage_mode": body.storage_mode,
        "oss_endpoint": body.oss_endpoint,
        "oss_bucket": body.oss_bucket,
        "oss_access_key_id": body.oss_access_key_id,
        "oss_access_key_secret": body.oss_access_key_secret,
    }
    _save_storage_config(db, cfg)
    return {"ok": True, "config": cfg}


# ============================================================
# 公众号二维码上传 & 获取
# ============================================================
ASSETS_DIR = Path(__file__).resolve().parent.parent / "storage" / "assets"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

class QrcodeBody(BaseModel):
    url: str = ""


class QrcodeSlotBody(BaseModel):
    url: str = ""


def _qrcode_config_key(slot: str) -> str:
    if slot == "brand":
        return QRCODE_CONFIG_KEY
    if slot == "cs":
        return "ui_customer_service_qr_url"
    raise HTTPException(status_code=400, detail="二维码槽位非法，仅支持 brand 或 cs")


def _validate_qrcode_url(url: str):
    if url and not (url.startswith("/assets/") or url.startswith("http://") or url.startswith("https://") or url.startswith("data:image/")):
        raise HTTPException(status_code=400, detail="二维码 URL 非法")


def _get_qrcode_slot(db: Session, slot: str) -> str:
    key = _qrcode_config_key(slot)
    url = _get_config_value(db, key, "").strip()
    opposite = "brand" if slot == "cs" else "cs"
    opposite_url = _get_config_value(db, _qrcode_config_key(opposite), "").strip()
    if url and (_is_foreign_asset_url(url, slot) or (opposite_url and url == opposite_url)):
        _set_config_value(db, key, "")
        return ""
    return url


def _save_qrcode_slot(db: Session, slot: str, url: str) -> str:
    url = url.strip()
    _validate_qrcode_url(url)
    opposite = "brand" if slot == "cs" else "cs"
    opposite_url = _get_config_value(db, _qrcode_config_key(opposite), "").strip()
    if _is_foreign_asset_url(url, slot) or (url and opposite_url and url == opposite_url):
        label = "品牌" if slot == "cs" else "客服"
        target = "客服" if slot == "cs" else "品牌引流"
        raise HTTPException(status_code=400, detail=f"不能把{label}二维码保存为{target}二维码")
    _set_config_value(db, _qrcode_config_key(slot), url)
    return url


def _clamp(value: int, low: int, high: int) -> int:
    return max(low, min(value, high))


def _prepare_rgb_image(img):
    from PIL import Image, ImageOps

    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.getchannel("A"))
        return bg
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def _crop_qrcode_square(img):
    """Crop to a square around dark QR content; fallback to centered square."""
    rgb = _prepare_rgb_image(img)
    width, height = rgb.size
    min_dim = min(width, height)

    def center_square():
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        return rgb.crop((left, top, left + min_dim, top + min_dim))

    # Most QR screenshots are black modules on a white phone screenshot.
    # Build a mask from darker pixels so wide white borders do not survive.
    mask = rgb.convert("L").point(lambda p: 255 if p < 245 else 0)
    bbox = mask.getbbox()
    if not bbox:
        return center_square()

    left, top, right, bottom = bbox
    box_w = right - left
    box_h = bottom - top
    box_area = box_w * box_h
    image_area = width * height
    if box_area < image_area * 0.002 or box_area > image_area * 0.92:
        return center_square()

    content_side = max(box_w, box_h)
    padding = max(12, int(content_side * 0.12))
    side = min(max(content_side + padding * 2, 1), min_dim)
    cx = (left + right) // 2
    cy = (top + bottom) // 2
    crop_left = _clamp(cx - side // 2, 0, width - side)
    crop_top = _clamp(cy - side // 2, 0, height - side)
    return rgb.crop((crop_left, crop_top, crop_left + side, crop_top + side))


def _get_config_value(db: Session, key: str, default: str = "") -> str:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return row.value if row else default


def _set_config_value(db: Session, key: str, value: str):
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row:
        row.value = value
    else:
        db.add(SystemConfig(key=key, value=value))
    db.commit()


async def _store_uploaded_qrcode(file: UploadFile, tag: str) -> dict:
    if tag not in {"brand", "cs"}:
        raise HTTPException(status_code=400, detail="二维码类型非法，仅支持 brand 或 cs")

    # 校验扩展名
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext}，仅允许 {', '.join(ALLOWED_EXTENSIONS)}")

    # 校验大小
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 2MB")

    # 确保目录存在
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Pillow 强制居中正方形裁剪 ──────────────────────────────────
    from io import BytesIO
    from PIL import Image
    import uuid as _uuid

    safe_name = f"{tag}_{_uuid.uuid4().hex}.png"
    dest = ASSETS_DIR / safe_name

    try:
        pil_img = Image.open(BytesIO(content))
        cropped_img = _crop_qrcode_square(pil_img)
        cropped_img.save(str(dest), "PNG")
        final_bytes = dest.read_bytes()

    except Exception as e:
        print(f"[严重错误] Pillow 裁剪崩溃: {e}")
        raise HTTPException(status_code=500, detail=f"图片裁剪失败: {e}")

    asset_url = f"/assets/{safe_name}"

    return {
        "ok": True,
        "tag": tag,
        "filename": safe_name,
        "url": asset_url,
        "size": len(final_bytes),
        "message": "二维码已上传并裁剪为正方形",
    }


@router.post("/upload-customer-service-qrcode")
async def upload_customer_service_qrcode(
    admin: dict = Depends(get_current_admin),
    file: UploadFile = File(...),
):
    """上传客服二维码图片。只返回 cs_ 文件 URL，不触碰品牌配置。"""
    return await _store_uploaded_qrcode(file, "cs")


@router.post("/upload-brand-qrcode")
async def upload_brand_qrcode(
    admin: dict = Depends(get_current_admin),
    file: UploadFile = File(...),
):
    """上传品牌引流二维码图片。只返回 brand_ 文件 URL，不触碰客服配置。"""
    return await _store_uploaded_qrcode(file, "brand")


@router.post("/upload-qrcode")
async def upload_qrcode(
    admin: dict = Depends(get_current_admin),
    file: UploadFile = File(...),
    tag: str = Query("brand", description="标识: brand=品牌引流 / cs=客服"),
):
    """兼容旧入口：上传二维码图片，不触碰数据库。"""
    return await _store_uploaded_qrcode(file, tag)


@router.get("/qrcode")
def get_qrcode(
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """获取当前公众号二维码 URL（需管理员权限）"""
    return get_brand_qrcode(db)


@router.get("/brand-qrcode")
def get_brand_qrcode(db: Session = Depends(get_db)):
    """获取品牌引流二维码 URL（公开，从 DB 加载并清洗污染值）"""
    return {"url": _get_qrcode_slot(db, "brand")}


@router.get("/qrcode-slot/{slot}")
def get_qrcode_slot(slot: str, db: Session = Depends(get_db)):
    """统一二维码槽位读取：brand=PDF引流，cs=客服。"""
    return {"slot": slot, "url": _get_qrcode_slot(db, slot)}


@router.put("/qrcode")
def save_qrcode(body: QrcodeBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存品牌引流二维码 URL（需管理员权限）。"""
    return save_brand_qrcode(body, admin, db)


@router.put("/brand-qrcode")
def save_brand_qrcode(body: QrcodeBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存品牌引流二维码 URL（需管理员权限）。"""
    url = _save_qrcode_slot(db, "brand", body.url)
    return {"ok": True, "url": url}


@router.put("/qrcode-slot/{slot}")
def save_qrcode_slot(
    slot: str,
    body: QrcodeSlotBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """统一二维码槽位保存：brand=PDF引流，cs=客服。"""
    url = _save_qrcode_slot(db, slot, body.url)
    return {"ok": True, "slot": slot, "url": url}


# ============================================================
# 系统参数配置（注册奖励 + 微信各端密钥）— 可视化后台管理
# ============================================================

_SYSTEM_CONFIG_DEFAULTS = {
    "register_bonus": ("3", "新用户注册赠送永久点数"),
    "register_free": ("1", "新用户注册赠送体验点数（24h过期）"),
    "wx_mp_appid": ("", "公众号 AppID"),
    "wx_mp_secret": ("", "公众号 AppSecret"),
    "wx_mini_appid": ("", "小程序 AppID"),
    "wx_mini_secret": ("", "小程序 AppSecret"),
    "wx_service_appid": ("", "服务号 AppID"),
    "wx_service_secret": ("", "服务号 AppSecret"),
}


def _load_all_system_config(db: Session) -> dict:
    """从数据库加载全部系统参数，未配置项回退默认值"""
    result = {}
    for key, (default_val, desc) in _SYSTEM_CONFIG_DEFAULTS.items():
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        result[key] = {
            "value": row.value if row else default_val,
            "description": desc,
        }
    return result


class SystemSettingsBody(BaseModel):
    items: dict[str, str] = {}  # key → value


@router.get("/system-settings")
def get_system_settings(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """获取全部系统参数（需管理员权限）"""
    return {"configs": _load_all_system_config(db)}


@router.put("/system-settings")
def save_system_settings(body: SystemSettingsBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """批量更新系统参数（需管理员权限）"""
    for key, value in body.items.items():
        # 仅允许更新白名单内的配置键
        if key not in _SYSTEM_CONFIG_DEFAULTS:
            continue
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if row:
            row.value = value
        else:
            db.add(SystemConfig(key=key, value=value, description=_SYSTEM_CONFIG_DEFAULTS[key][1]))
    db.commit()
    return {"ok": True, "configs": _load_all_system_config(db)}


# ═══════════════════════════════════════════
# 高德 Web 服务 Key 池管理
# ═══════════════════════════════════════════
from models.db_models import AmapKey as _AmapKey
from pydantic import BaseModel as _BaseModel


class _AmapKeyBody(_BaseModel):
    name: str = ""
    api_key: str = ""
    security_secret: str = ""
    enabled: bool = True
    priority: int = 0
    clear_security_secret: bool = False


@router.get("/amap-keys")
def list_amap_keys(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """Key 池列表 — 不返回明文"""
    rows = db.query(_AmapKey).order_by(_AmapKey.priority, _AmapKey.id).all()
    return {"keys": [r.to_dict_admin() for r in rows], "total": len(rows)}


@router.post("/amap-keys")
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


@router.put("/amap-keys/{key_id}")
def update_amap_key(key_id: int, body: _AmapKeyBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """编辑 Key — 空 api_key 字段表示保留原值"""
    row = db.query(_AmapKey).filter(_AmapKey.id == key_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Key 不存在")
    if body.name.strip():
        row.name = body.name.strip()
    if body.api_key.strip():
        row.api_key = body.api_key.strip()
    if body.security_secret.strip():
        row.security_secret = body.security_secret.strip()
    if body.clear_security_secret:
        row.security_secret = ""
    row.enabled = 1 if body.enabled else 0
    row.priority = body.priority
    db.commit()
    return {"ok": True, "key": row.to_dict_admin()}


@router.delete("/amap-keys/{key_id}")
def delete_amap_key(key_id: int, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """删除 Key"""
    row = db.query(_AmapKey).filter(_AmapKey.id == key_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Key 不存在")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.post("/amap-keys/{key_id}/test")
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
    from datetime import datetime as _dt
    rows = db.query(_AmapKey).filter(_AmapKey.enabled == 1).order_by(_AmapKey.priority, _AmapKey.id).all()
    if rows:
        r = rows[0]
        return r.api_key, (r.security_secret or "")
    # fallback to env
    import os as _os
    return _os.getenv("AMAP_WEB_KEY", _os.getenv("AMAP_KEY", "")), ""


def _report_amap_key_failure(db: Session, key_str: str, status: str, info: str = "", infocode: str = ""):
    """标记 Key 失败状态"""
    from datetime import datetime as _dt
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
