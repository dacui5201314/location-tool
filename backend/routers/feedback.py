"""用户意见反馈、截图上传与运营回复。安全：Pillow 重编码 + 签名下载 + nosniff + 越权防护。"""
import json, uuid, io, hmac, hashlib, time as _time, struct
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Query
from fastapi.responses import Response
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import get_db
from models.db_models import User, Feedback
from auth import get_current_user, get_current_admin
from config import JWT_SECRET

router = APIRouter(prefix="/api/feedback", tags=["反馈"])

FEEDBACK_ASSETS = Path(__file__).resolve().parent.parent / "storage" / "assets" / "feedback"
FEEDBACK_ASSETS.mkdir(parents=True, exist_ok=True)

_MAX_IMAGE_BYTES = 2 * 1024 * 1024
_SIGNED_URL_TTL = 600  # 签名 URL 10 分钟有效

# ── 真实图片 magic bytes ──
_IMAGE_MAGIC = {
    b'\x89PNG\r\n\x1a\n': ("png", "image/png"),
    b'\xff\xd8\xff': ("jpg", "image/jpeg"),
    b'RIFF': ("webp", "image/webp"),
}


def _detect_image_type(raw: bytes) -> tuple:
    for magic, (ext, ct) in _IMAGE_MAGIC.items():
        if raw[:len(magic)] == magic:
            if ext == "webp" and raw[8:12] != b"WEBP":
                continue
            return ext, ct
    return None, None


def _safe_basename(url_or_name: str) -> str:
    """从 URL 或旧路径提取安全 basename：仅允许 fb_<hex>.(png|jpg|jpeg|webp)。"""
    if not url_or_name:
        return ""
    name = url_or_name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1].split("?")[0]
    # 拒绝路径穿越
    if ".." in name or "/" in name or "\\" in name or "%" in name:
        return ""
    import re
    if not re.match(r'^fb_[a-f0-9]+\.(png|jpg|jpeg|webp)$', name, re.I):
        return ""
    return name


def _save_feedback_image(raw: bytes, ext: str) -> str:
    """Pillow 重编码图片去元数据，保存到本地。失败直接抛异常，不保存原始数据。"""
    from PIL import Image
    img = Image.open(io.BytesIO(raw))
    img.verify()  # 校验图片完整性
    # reopen after verify
    img = Image.open(io.BytesIO(raw))
    if img.mode not in ("RGB", "RGBA", "L"):
        img = img.convert("RGB")
    out = io.BytesIO()
    fmt = "JPEG" if ext == "jpg" else ext.upper()
    img.save(out, format=fmt, quality=85)
    raw = out.getvalue()
    fname = f"fb_{uuid.uuid4().hex[:12]}.{ext}"
    (FEEDBACK_ASSETS / fname).write_bytes(raw)
    return fname


def _sign_image_url(fb_id: int, idx: int, fname: str) -> str:
    """生成短期签名图片 URL（可免 Authorization 访问）。"""
    exp = int(_time.time()) + _SIGNED_URL_TTL
    payload = f"{fb_id}|{idx}|{fname}|{exp}"
    sig = hmac.new(JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    return f"/api/feedback/simage/{fb_id}/{idx}?sig={sig}&exp={exp}"


def _verify_signed_url(fb_id: int, idx: int, sig: str, exp_str: str) -> bool:
    try:
        exp = int(exp_str)
        if _time.time() > exp:
            return False
        # reconstruct payload from DB — we just verify sig matches after loading
        return bool(sig) and len(sig) >= 8
    except (ValueError, TypeError):
        return False


def _image_urls_for_fb(fb: Feedback, is_admin: bool = False) -> list:
    """为反馈生成安全图片 URL 列表。"""
    try:
        stored = json.loads(fb.image_urls or "[]")
    except Exception:
        return []
    if not isinstance(stored, list):
        return []
    result = []
    for i, item in enumerate(stored):
        fname = _safe_basename(str(item)) if isinstance(item, str) else ""
        if not fname:
            # 旧数据兼容：尝试从 item URL 提取
            continue
        if is_admin:
            result.append(_sign_image_url(fb.id, i, fname))
        else:
            result.append(_sign_image_url(fb.id, i, fname))
    return result


# ═══════════ 路由 ═══════════



@router.post("/upload")
async def upload_feedback_image(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """上传反馈截图：magic bytes + Pillow 重编码 + 大小限制。返回 image_key。"""
    raw = await file.read()
    if len(raw) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="图片不能超过2MB")
    ext, ct = _detect_image_type(raw)
    if not ext:
        raise HTTPException(status_code=400, detail="仅支持 PNG / JPEG / WebP 格式图片")
    try:
        fname = _save_feedback_image(raw, ext)
    except Exception:
        raise HTTPException(status_code=400, detail="图片格式无效或已损坏，请重新选择")
    return {"ok": True, "image_key": fname}


@router.post("")
async def submit_feedback(
    content: str = Form(""),
    contact: str = Form(""),
    image_keys: str = Form(""),
    report_uuid: str = Form(""),
    report_title: str = Form(""),
    report_address: str = Form(""),
    source: str = Form("profile"),
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """提交反馈。image_keys 为逗号分隔的安全文件名列表。"""
    content = (content or "").strip()
    if len(content) < 10:
        raise HTTPException(status_code=400, detail="反馈内容至少10个字")
    if len(content) > 1000:
        raise HTTPException(status_code=400, detail="反馈内容不能超过1000字")

    user_id = int(user["user_id"])
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 解析 image_keys
    keys = []
    raw_keys = (image_keys or "").strip()
    if raw_keys:
        parts = raw_keys.split(",")
        keys = [_safe_basename(p.strip()) for p in parts if _safe_basename(p.strip())]

    safe_source = (source or "profile").strip()[:40] or "profile"
    if safe_source not in ("profile", "report_detail"):
        safe_source = "profile"

    fb = Feedback(
        user_id=user_id, content=content,
        contact=(contact or "").strip()[:120],
        image_urls=json.dumps(keys, ensure_ascii=False),
        credits_granted=0,
        report_uuid=(report_uuid or "").strip()[:64],
        report_title=(report_title or "").strip()[:200],
        report_address=(report_address or "").strip()[:500],
        source=safe_source, status="pending", updated_at=datetime.utcnow(),
    )
    db.add(fb)
    db.commit()
    return {"ok": True, "message": "感谢反馈，我们会尽快处理。", "feedback_id": fb.id, "credits_granted": 0}


# ── 签名图片访问（免 Authorization，用于 previewImage）──
@router.get("/simage/{fb_id}/{idx}")
def signed_feedback_image(
    fb_id: int, idx: int,
    sig: str = Query(""), exp: str = Query(""),
    db: Session = Depends(get_db),
):
    """短期签名 URL 访问反馈截图。"""
    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="反馈不存在")
    try:
        exp_int = int(exp)
        if _time.time() > exp_int:
            raise HTTPException(status_code=410, detail="签名已过期")
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="签名无效")

    try:
        stored = json.loads(fb.image_urls or "[]")
    except Exception:
        raise HTTPException(status_code=404, detail="截图不存在")
    if not isinstance(stored, list) or idx < 0 or idx >= len(stored):
        raise HTTPException(status_code=404, detail="截图不存在")
    fname = _safe_basename(str(stored[idx]))
    if not fname:
        raise HTTPException(status_code=404, detail="截图不存在")

    # 验证签名
    payload = f"{fb_id}|{idx}|{fname}|{exp_int}"
    expected = hmac.new(JWT_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]
    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=403, detail="签名无效")

    img_path = FEEDBACK_ASSETS / fname
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="截图不存在")
    raw = img_path.read_bytes()
    _, ct = _detect_image_type(raw)
    if not ct:
        ct = "image/png"
    return Response(content=raw, media_type=ct, headers={
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=600",
    })


# ── 鉴权下载 ──
@router.get("/image/{fb_id}/{idx}")
def download_feedback_image(
    fb_id: int, idx: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """鉴权下载反馈截图。"""
    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="反馈不存在")
    user_id = int(user["user_id"])
    if user.get("role") != "admin" and fb.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权访问该反馈截图")

    try:
        stored = json.loads(fb.image_urls or "[]")
    except Exception:
        raise HTTPException(status_code=404, detail="截图不存在")
    if not isinstance(stored, list) or idx < 0 or idx >= len(stored):
        raise HTTPException(status_code=404, detail="截图不存在")
    fname = _safe_basename(str(stored[idx]))
    if not fname:
        raise HTTPException(status_code=404, detail="截图不存在")
    img_path = FEEDBACK_ASSETS / fname
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="截图不存在")
    raw = img_path.read_bytes()
    _, ct = _detect_image_type(raw)
    if not ct:
        ct = "image/png"
    return Response(content=raw, media_type=ct, headers={
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=3600",
    })


@router.get("/admin/image/{fb_id}/{idx}")
def admin_feedback_image(
    fb_id: int, idx: int,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理员下载反馈截图。"""
    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="反馈不存在")
    try:
        stored = json.loads(fb.image_urls or "[]")
    except Exception:
        raise HTTPException(status_code=404, detail="截图不存在")
    if not isinstance(stored, list) or idx < 0 or idx >= len(stored):
        raise HTTPException(status_code=404, detail="截图不存在")
    fname = _safe_basename(str(stored[idx]))
    if not fname:
        raise HTTPException(status_code=404, detail="截图不存在")
    img_path = FEEDBACK_ASSETS / fname
    if not img_path.exists():
        raise HTTPException(status_code=404, detail="截图不存在")
    raw = img_path.read_bytes()
    _, ct = _detect_image_type(raw)
    if not ct:
        ct = "image/png"
    return Response(content=raw, media_type=ct, headers={
        "X-Content-Type-Options": "nosniff", "Cache-Control": "private, max-age=3600",
    })


# ── 列表输出 ──

def _feedback_to_dict(fb: Feedback, user_obj: Optional[User] = None, is_admin: bool = False):
    imgs = _image_urls_for_fb(fb, is_admin=is_admin)
    return {
        "id": fb.id, "user_id": fb.user_id,
        "phone": (user_obj.phone or user_obj.phone_number or "") if user_obj else "",
        "content": fb.content, "contact": fb.contact or "",
        "images": imgs,
        "credits_granted": fb.credits_granted or 0,
        "report_uuid": fb.report_uuid or "",
        "report_title": fb.report_title or "",
        "report_address": fb.report_address or "",
        "source": fb.source or "profile", "status": fb.status or "pending",
        "admin_reply": fb.admin_reply or "",
        "replied_at": fb.replied_at.isoformat() if fb.replied_at else None,
        "updated_at": fb.updated_at.isoformat() if fb.updated_at else None,
        "created_at": fb.created_at.isoformat() if fb.created_at else None,
    }


@router.get("/my")
def list_my_feedbacks(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Feedback).filter(Feedback.user_id == int(user["user_id"])).order_by(
        Feedback.created_at.desc()).limit(100).all()
    return {"feedbacks": [_feedback_to_dict(fb) for fb in rows]}


@router.get("/admin/list")
def list_feedbacks(admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = db.query(Feedback, User).join(User, Feedback.user_id == User.id).order_by(
        Feedback.created_at.desc()).limit(100).all()
    result = [_feedback_to_dict(fb, u, is_admin=True) for fb, u in rows]
    return {"feedbacks": result}


@router.post("/admin/{fb_id}/reply")
def reply_feedback(fb_id: int, payload: dict = Body(...),
                   admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    reply = (payload.get("reply") or "").strip()
    if len(reply) < 2: raise HTTPException(status_code=400, detail="回复内容至少2个字")
    if len(reply) > 1000: raise HTTPException(status_code=400, detail="回复内容不能超过1000字")
    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb: raise HTTPException(status_code=404, detail="反馈不存在")
    now = datetime.utcnow()
    fb.admin_reply = reply; fb.status = "replied"; fb.replied_at = now; fb.updated_at = now
    db.commit()
    return {"ok": True, "feedback": _feedback_to_dict(fb, is_admin=True)}


@router.delete("/admin/{fb_id}")
def delete_feedback(fb_id: int, admin: dict = Depends(get_current_admin), db: Session = Depends(get_db)):
    fb = db.query(Feedback).filter(Feedback.id == fb_id).first()
    if not fb: raise HTTPException(status_code=404, detail="反馈不存在")
    db.delete(fb); db.commit()
    return {"ok": True}
