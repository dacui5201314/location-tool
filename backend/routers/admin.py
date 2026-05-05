"""管理后台 API — JWT 鉴权 + Admin 角色校验"""
import os
import shutil
import base64
import time as _time
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List
import random, string
from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, update
from pydantic import BaseModel
from database import get_db
from models.db_models import User, AnalysisRecord, SavedLocation, RedeemCode, SystemConfig
from auth import get_current_admin, create_token

# === 内存存储（后续迁移至 SQLite 表） ===
# 双轨 SKU：会员档位 + 点数档位
_SKU_STORE: list[dict] = [
    # 会员档位
    {"id": 1, "type": "membership", "label": "月度会员", "price": "88", "tier": "monthly", "duration_days": 30, "badge": "", "desc": "30天无限次分析"},
    {"id": 2, "type": "membership", "label": "季度会员", "price": "218", "tier": "quarterly", "duration_days": 90, "badge": "推荐", "desc": "90天无限次分析"},
    {"id": 3, "type": "membership", "label": "年度会员", "price": "888", "tier": "yearly", "duration_days": 365, "badge": "最值", "desc": "365天无限次分析"},
    # 点数档位
    {"id": 11, "type": "points", "label": "体验包", "price": "9.9", "credits": 1, "badge": "", "desc": "1次分析"},
    {"id": 12, "type": "points", "label": "标准包", "price": "29.9", "credits": 5, "badge": "", "desc": "5次分析"},
    {"id": 13, "type": "points", "label": "专业包", "price": "99", "credits": 25, "badge": "热销", "desc": "25次分析"},
    {"id": 14, "type": "points", "label": "企业包", "price": "299", "credits": 100, "badge": "最值", "desc": "100次分析"},
]

_ERROR_LOGS: list[dict] = [
    {"time": "2026-04-30 10:23:15", "user_id": 1, "type": "API", "msg": "DeepSeek API 超时重试中 (attempt 2/3)"},
    {"time": "2026-04-30 09:47:02", "user_id": 0, "type": "PAYMENT", "msg": "支付回调验签失败: signature mismatch"},
    {"time": "2026-04-29 18:30:44", "user_id": 1, "type": "AMAP", "msg": "高德POI搜索返回空结果 (radius=1000, types=050000)"},
]

_UI_CONFIG: dict = {
    "announcement": "",
    "cs_wechat": "",
    "cs_phone": "",
    "customer_service_name": "",
    "customer_service_qr_url": "",
}

router = APIRouter(prefix="/api/admin", tags=["管理后台"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


class LoginBody(BaseModel):
    password: str


@router.post("/login")
def admin_login(body: LoginBody):
    """管理员登录：密码校验通过后签发 JWT（role=admin）"""
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
    db: Session = Depends(get_db),
):
    """用户列表（需管理员权限）"""

    query = db.query(User).order_by(User.created_at.desc())
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    tier_labels = {"free": "非会员", "monthly": "月度", "quarterly": "季度", "yearly": "年度"}
    for u in users:
        report_count = db.query(AnalysisRecord).filter(AnalysisRecord.user_id == u.id).count()
        result.append({
            "id": u.id,
            "phone": u.phone or u.phone_number or "",
            "phone_number": u.phone_number or "",
            "balance_credits": u.balance_credits,
            "points": u.points,
            "membership_tier": u.membership_tier,
            "membership_label": tier_labels.get(u.membership_tier, "非会员"),
            "is_member": u.is_member,
            "membership_days_left": u.membership_days_left,
            "membership_expiry": u.membership_expiry.isoformat() if u.membership_expiry else None,
            "report_count": report_count,
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
    """增加用户点数（需管理员权限）"""

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.balance_credits += body.amount
    db.commit()
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


@router.put("/config")
def save_config(body: ConfigBody, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """保存系统配置到数据库（需管理员权限）"""
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
    for key, value in config_map.items():
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if row:
            row.value = value
        else:
            db.add(SystemConfig(key=key, value=value, description=f"系统设置-{key}"))
    db.commit()
    return {"ok": True, "message": "配置已保存"}


# ============================================================
# SKU 套餐管理
# ============================================================
class SkuItem(BaseModel):
    id: int = 0
    label: str = ""
    price: str = "0"
    credits: int = 0
    badge: str = ""

class SkuListBody(BaseModel):
    items: List[SkuItem] = []

@router.get("/skus")
def get_skus():
    """获取套餐列表（前端充值弹窗动态拉取）"""
    return {"skus": _SKU_STORE}

@router.put("/skus")
def save_skus(body: SkuListBody, admin: dict = Depends(get_current_admin)):
    """保存套餐配置（需管理员权限）"""
    global _SKU_STORE
    _SKU_STORE = [item.model_dump() for item in body.items]
    return {"ok": True, "skus": _SKU_STORE}


# ============================================================
# 系统运行日志
# ============================================================
@router.get("/logs")
def get_logs(
    admin: dict = Depends(get_current_admin),
    level: str = Query("error"),
):
    """系统日志（需管理员权限）"""
    return {"logs": _ERROR_LOGS, "total": len(_ERROR_LOGS)}


# ============================================================
# 全局 UI 配置（公告 / 客服）
# ============================================================
class UiConfigBody(BaseModel):
    announcement: str = ""
    cs_wechat: str = ""
    cs_phone: str = ""
    customer_service_name: str = ""
    customer_service_qr_url: str = ""

@router.get("/ui-config")
def get_ui_config():
    return _UI_CONFIG

@router.put("/ui-config")
def save_ui_config(body: UiConfigBody, admin: dict = Depends(get_current_admin)):
    """保存 UI 配置（需管理员权限）"""
    global _UI_CONFIG
    _UI_CONFIG = {
        "announcement": body.announcement,
        "cs_wechat": body.cs_wechat,
        "cs_phone": body.cs_phone,
        "customer_service_name": body.customer_service_name,
        "customer_service_qr_url": body.customer_service_qr_url,
    }
    return {"ok": True, "config": _UI_CONFIG}


# ============================================================
# 兑换码 (CDK) 管理
# ============================================================
class GenCdkBody(BaseModel):
    prefix: str = "AI"
    count: int = 10
    credits: int = 1
    days_valid: int = 90

class ActivateCdkBody(BaseModel):
    code: str = ""
    user_id: int = 1

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
def activate_cdk(body: ActivateCdkBody, request: Request, db: Session = Depends(get_db)):
    """激活兑换码 — 原子化 UPDATE 防一码多充 + IP 速率限制防暴力枚举"""
    _check_cdk_rate(request)

    code_str = body.code.strip().upper()

    # 先查询兑换码是否存在、是否过期（非竞态路径，仅用于友好错误提示）
    c = db.query(RedeemCode).filter(RedeemCode.code == code_str).first()
    if not c:
        raise HTTPException(status_code=404, detail="兑换码不存在")
    if c.expires_at and c.expires_at < datetime.now():
        raise HTTPException(status_code=400, detail="该兑换码已过期")

    # ★ 原子化 UPDATE：WHERE is_used == 0 消除 TOCTOU 竞态窗口
    result = db.execute(
        update(RedeemCode)
        .where(RedeemCode.code == code_str, RedeemCode.is_used == 0)
        .values(is_used=1, used_by=body.user_id, used_at=datetime.now())
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=400, detail="该兑换码已被使用")

    # 点数充值
    user = db.query(User).filter(User.id == body.user_id).first()
    if user:
        user.balance_credits += c.credits
    db.commit()
    return {"ok": True, "credits_added": c.credits, "balance": user.balance_credits if user else 0}


# ============================================================
# 搜索趋势看板
# ============================================================
@router.get("/trends")
def get_trends(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    """搜索趋势看板（需管理员权限）"""
    records = db.query(AnalysisRecord).all()
    biz_counter = {}
    brand_counter = {}
    for r in records:
        bt = r.business_type or ""
        if bt: biz_counter[bt] = biz_counter.get(bt, 0) + 1
        bd = r.brand_desc or ""
        if bd: brand_counter[bd] = brand_counter.get(bd, 0) + 1
    top_biz = sorted(biz_counter.items(), key=lambda x: -x[1])[:10]
    top_brands = sorted(brand_counter.items(), key=lambda x: -x[1])[:10]
    return {"top_business_types": [{"name": k, "count": v} for k, v in top_biz],
            "top_brands": [{"name": k, "count": v} for k, v in top_brands]}


# ============================================================
# PDF 白标配置
# ============================================================
_PDF_CONFIG = {"logo_url": "", "footer_text": "AI 选址分析 · 商业数据决策平台"}

class PdfConfigBody(BaseModel):
    logo_url: str = ""
    footer_text: str = ""

@router.get("/pdf-config")
def get_pdf_config(admin: dict = Depends(get_current_admin)):
    """获取 PDF 品牌配置（需管理员权限）"""
    return _PDF_CONFIG

@router.put("/pdf-config")
def save_pdf_config(body: PdfConfigBody, admin: dict = Depends(get_current_admin)):
    """保存 PDF 品牌配置（需管理员权限）"""
    global _PDF_CONFIG
    _PDF_CONFIG = {"logo_url": body.logo_url, "footer_text": body.footer_text}
    return {"ok": True, "config": _PDF_CONFIG}


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
    rows = db.query(SystemConfig).filter(SystemConfig.key.like("storage_%")).all()
    for r in rows:
        if r.key in cfg:
            cfg[r.key] = r.value
    return cfg


def _save_storage_config(db: Session, cfg: dict):
    """保存存储配置到数据库"""
    for key, value in cfg.items():
        if not key.startswith("storage_"):
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
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}
MAX_UPLOAD_SIZE = 2 * 1024 * 1024  # 2MB

QRCODE_CONFIG_KEY = "OFFICIAL_QRCODE_URL"


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


@router.post("/upload-qrcode")
async def upload_qrcode(
    admin: dict = Depends(get_current_admin),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """上传公众号二维码图片（需管理员权限）"""

    # 校验扩展名
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in (file.filename or "") else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式: {ext}，仅允许 {', '.join(ALLOWED_EXTENSIONS)}")

    # 校验大小
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 2MB")

    # 保存文件
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"official_qrcode.{ext}"
    dest = ASSETS_DIR / safe_name
    dest.write_bytes(content)

    # 存储路径到数据库（存储为静态可访问的相对路径 + base64 备用）
    b64 = base64.b64encode(content).decode("utf-8")
    data_uri = f"data:image/{'svg+xml' if ext == 'svg' else ext.replace('jpg', 'jpeg')};base64,{b64}"

    # 存 base64 data URI 到数据库（前端 PDF 导出可直接使用）
    _set_config_value(db, QRCODE_CONFIG_KEY, data_uri)

    return {
        "ok": True,
        "filename": safe_name,
        "size": len(content),
        "message": "二维码已上传，将自动应用到导出的 PDF 报告中",
    }


@router.get("/qrcode")
def get_qrcode(db: Session = Depends(get_db)):
    """获取当前公众号二维码 (base64 data URI)"""
    url = _get_config_value(db, QRCODE_CONFIG_KEY, "")
    return {"url": url}


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
