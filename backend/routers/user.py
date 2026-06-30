"""用户中心 API — JWT 鉴权 + 双轨计费"""
import os, secrets, time, json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.db_models import User, AnalysisRecord, SavedLocation, PaymentOrder
from services.runtime_config import get_user_skus
from auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["用户中心"])

AVATAR_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage", "assets", "user_avatars")
os.makedirs(AVATAR_ROOT, exist_ok=True)
AVATAR_MAX_BYTES = 2 * 1024 * 1024
AVATAR_ALLOWED = {"image/png", "image/jpeg", "image/webp", "image/gif"}

_TEMP_AVATAR_MARKERS = ["__tmp__", "tmp.weixin.qq.com", "127.0.0.1:26205", "http://tmp/"]

def clean_avatar_url(url: str) -> str:
    """过滤微信临时头像 URL，返回空字符串；/assets/ 或合法 http(s) 永久地址原样返回。"""
    if not url or not url.strip():
        return ""
    u = url.strip()
    for marker in _TEMP_AVATAR_MARKERS:
        if marker in u:
            return ""
    return u


@router.get("/profile")
def get_profile(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回当前用户信息、会员状态、点数余额、统计数据（需 JWT）"""
    user_id = user["user_id"]
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    total_reports = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == user_id
    ).count()
    favorite_count = db.query(SavedLocation).filter(
        SavedLocation.user_id == user_id
    ).count()

    tier_labels = {
        "free": "非会员",
        "monthly": "月度会员",
        "quarterly": "季度会员",
        "yearly": "年度会员",
    }
    user_dict = db_user.to_dict()
    raw_av = user_dict.get("avatar_url", "")
    cleaned_av = clean_avatar_url(raw_av)
    # 温和清理：DB 里存的是临时 URL，置空并落库
    if raw_av and not cleaned_av and db_user.avatar_url and db_user.avatar_url.strip():
        db_user.avatar_url = ""
        db.commit()
    user_dict["avatar_url"] = cleaned_av
    return {
        "user": user_dict,
        "membership": {
            "tier": db_user.membership_tier,
            "tier_label": tier_labels.get(db_user.membership_tier, "非会员"),
            "is_member": db_user.is_member,
            "days_left": db_user.membership_days_left,
            "expiry": db_user.membership_expiry.isoformat() if db_user.membership_expiry else None,
        },
        "points": db_user.balance_credits,
        "total_reports": total_reports,
        "favorite_count": favorite_count,
        "is_new_user": False,
        "gift_note": "",
    }


class ProfileUpdateBody(BaseModel):
    avatar_url: str = ""
    nickname: str = ""


@router.put("/profile")
def update_profile(
    body: ProfileUpdateBody,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新用户昵称（小程序 nickname input）。头像应通过 POST /api/user/avatar 上传。"""
    db_user = db.query(User).filter(User.id == user["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 头像：仅接受 /assets/ 开头的永久 URL，拒绝临时路径
    if body.avatar_url and body.avatar_url.strip():
        url = body.avatar_url.strip()
        if url.startswith("/assets/"):
            db_user.avatar_url = url
        # http(s) URL 不再作为小程序主路径，仅做兼容保留
    if body.nickname and body.nickname.strip():
        db_user.nickname = body.nickname.strip()
    db.commit()
    return {"ok": True, "user": db_user.to_dict()}


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传用户头像（需 JWT）。PNG/JPEG/WebP/GIF 输入 → Pillow 解码验证重编码后写入。
    GIF 只保留首帧，重编码为 PNG。限制 2MB（原始上传大小）。"""
    raw_content = await file.read()
    if len(raw_content) > AVATAR_MAX_BYTES:
        raise HTTPException(status_code=400, detail="头像文件不能超过 2MB")

    # ── 魔数校验 ──
    if len(raw_content) < 4:
        raise HTTPException(status_code=400, detail="文件内容无效")
    header = raw_content[:4]
    magic_map = {
        b"\x89PNG": "png",
        b"\xff\xd8\xff": "jpeg",
        b"RIFF": "webp",
        b"GIF8": "gif",
    }
    detected_ext = None
    for magic, e in magic_map.items():
        if header.startswith(magic):
            detected_ext = e
            break
    if detected_ext == "webp" and (len(raw_content) < 12 or raw_content[8:12] != b"WEBP"):
        detected_ext = None
    if detected_ext is None:
        raise HTTPException(status_code=400, detail="无法识别的图片格式")

    # ── Pillow 解码 / 验证 / 重编码（P3-A）──
    import io as _io
    from PIL import Image as _Image
    try:
        img = _Image.open(_io.BytesIO(raw_content))
        img.verify()
        img = _Image.open(_io.BytesIO(raw_content))
    except Exception:
        raise HTTPException(status_code=400, detail="图片格式无效或已损坏")

    is_gif = detected_ext == "gif"
    if is_gif:
        # GIF → 只保留首帧，重编码为 PNG
        if getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1:
            img.seek(0)
        if img.mode not in ("RGB", "RGBA", "L", "P"):
            img = img.convert("RGBA")
        out_ext = "png"
        out_content_type = "image/png"
        out_buf = _io.BytesIO()
        img.save(out_buf, format="PNG")
    else:
        # PNG / JPEG / WebP → 重编码为同格式
        fmt_map = {"png": "PNG", "jpeg": "JPEG", "webp": "WEBP"}
        pil_fmt = fmt_map.get(detected_ext, "PNG")
        if img.mode not in ("RGB", "RGBA", "L"):
            img = img.convert("RGB")
        out_ext = detected_ext
        out_content_type = f"image/{out_ext}"
        out_buf = _io.BytesIO()
        save_kw = {"format": pil_fmt}
        if pil_fmt == "JPEG":
            save_kw["quality"] = 85
        img.save(out_buf, **save_kw)

    reencoded = out_buf.getvalue()

    # ── 本地写入（使用重编码 bytes）──
    uid = int(user["user_id"])
    ts = int(time.time() * 1000)
    token = secrets.token_hex(4)
    filename = f"avatar_{uid}_{ts}_{token}.{out_ext}"
    filepath = os.path.join(AVATAR_ROOT, filename)
    if os.path.abspath(filepath) != filepath or not filepath.startswith(os.path.abspath(AVATAR_ROOT)):
        raise HTTPException(status_code=400, detail="文件名无效")
    with open(filepath, "wb") as f:
        f.write(reencoded)

    avatar_url = f"/assets/user_avatars/{filename}"

    # ── 云存储（使用重编码 bytes）──
    from services.storage_service import save_user_asset_structured
    try:
        result = save_user_asset_structured("avatars", filename, reencoded,
                                             content_type=out_content_type,
                                             metadata={"user_id": uid})
        if result.ok and result.url:
            avatar_url = result.url
    except Exception:
        pass

    # ── 更新数据库 ──
    db_user = db.query(User).filter(User.id == uid).first()
    if db_user:
        db_user.avatar_url = avatar_url
        db.commit()
    return {"ok": True, "avatar_url": avatar_url, "user": db_user.to_dict() if db_user else None}


@router.get("/skus")
def get_visible_skus(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """返回当前用户实际可见套餐：用户专属配置优先，否则继承全局套餐。"""
    user_id = user["user_id"]
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    skus, inherited = get_user_skus(user_id, db)
    return {
        "user_id": user_id,
        "inherited": inherited,
        "skus": [item for item in skus if item.get("visible", True)],
    }


@router.get("/orders")
def list_my_orders(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """当前用户的充值订单列表（最近 50 条）。CREATED 超过 30 分钟自动作废。"""
    user_id = int(user["user_id"])
    rows = db.query(PaymentOrder).filter(
        PaymentOrder.user_id == user_id,
    ).order_by(PaymentOrder.created_at.desc()).limit(50).all()

    cutoff = datetime.now() - timedelta(minutes=30)
    orders = []
    for o in rows:
        # 超时未支付自动作废（虚拟支付可服务器补单，不做前端过期）
        status = o.status or "CREATED"
        if status == "CREATED" and o.created_at and o.created_at < cutoff:
            if o.pay_channel != "WECHAT_VIRTUAL":
                status = "TIMEOUT"
            # WECHAT_VIRTUAL 的 CREATED 保持原状态，前端显示"待支付"
        label = ""
        try:
            snap = json.loads(o.sku_snapshot or "{}")
            label = snap.get("label", "")
        except Exception:
            pass
        orders.append({
            "out_trade_no": o.out_trade_no,
            "sku_label": label,
            "amount_yuan": f"{o.amount_fen / 100:.2f}",
            "credits": o.credits or 0,
            "membership_days": o.membership_days or 0,
            "status": status,
            "pay_channel": o.pay_channel or "",
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })
    return {"orders": orders}


# ── 注意：POST /api/user/consume 已下线 ──
# 点数消耗必须在后端具体业务流中内部调用 check_billing_access()，
# 禁止前端通过 API 主动发起扣款指令。计费入口仅限：
#   - POST /api/analyze（分析扣费）
#   - POST /api/records/{id}/unlock-pdf（PDF 解锁扣费）
