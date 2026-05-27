"""认证路由 — JWT 签发、设备指纹、微信授权、手机号注册/登录、新用户奖励（多端兼容）"""
import hashlib
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel

from database import get_db
from models.db_models import User, BillingRecord, SystemConfig
from auth import create_token, get_current_user
from config import (
    SIGNUP_BONUS_CREDITS as _ENV_SIGNUP_BONUS,
    SIGNUP_FREE_CREDITS as _ENV_SIGNUP_FREE,
    WECHAT_MP_APPID,
    WECHAT_MP_SECRET,
)

router = APIRouter(prefix="/api/auth", tags=["认证"])

MAX_FREE_ACCOUNTS_PER_DEVICE = 2
FREE_POINT_HOURS = 24


def _hash_password(password: str) -> str:
    """PBKDF2-SHA256 密码哈希"""
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + dk.hex()


def _verify_password(password: str, stored: str) -> bool:
    """校验密码"""
    try:
        salt_hex, dk_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return dk.hex() == dk_hex
    except (ValueError, AttributeError):
        return False


def _get_config_int(db: Session, key: str, default: int) -> int:
    """从 SystemConfig 表中读取整数配置，未设置则回退默认值"""
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row and row.value:
        try:
            return int(row.value)
        except ValueError:
            pass
    return default


def _get_config_str(db: Session, key: str, default: str = "") -> str:
    """从 SystemConfig 表中读取字符串配置，未设置则回退默认值"""
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row and row.value:
        return row.value.strip()
    return default


def _get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else ""


def find_user_by_phone(db: Session, phone: str) -> User | None:
    """统一手机号查询：OR 匹配 phone 和 phone_number 两个字段"""
    if not phone:
        return None
    return db.query(User).filter(
        or_(User.phone == phone, User.phone_number == phone)
    ).first()


# ================================================================
# 共享 Helper：用户查找 / 创建 / 防刷 / 奖励
# ================================================================
def _find_or_create_user(
    db: Session,
    *,
    wx_openid: str = "",
    wx_mini_openid: str = "",
    wx_unionid: str = "",
    phone: str = "",
    device_id: str = "",
    channel: str = "web",
    client_ip: str = "",
) -> tuple[User, bool, str]:
    """查找已有用户，不存在则创建。
    新用户自动执行防刷检查 + 新手礼包 + BONUS 流水。
    返回 (user, is_new, gift_note)。
    """
    # ── 按优先级匹配已有用户 (Phase 16: +wx_mini_openid / +wx_unionid) ──
    user = None
    # a. unionid 跨应用统一标识优先
    if wx_unionid:
        user = db.query(User).filter(User.wx_unionid == wx_unionid).first()
    # b. 小程序 openid
    if not user and wx_mini_openid:
        user = db.query(User).filter(User.wx_mini_openid == wx_mini_openid).first()
    # c. 公众号 openid
    if not user and wx_openid:
        user = db.query(User).filter(User.wx_openid == wx_openid).first()
    if not user and phone:
        user = find_user_by_phone(db, phone)
    if not user and device_id:
        user = db.query(User).filter(User.device_id == device_id).first()

    if user:
        # 增量绑定缺失的身份字段（Phase 16: +wx_mini_openid / +wx_unionid）
        updated = False
        for field, val in [
            ("wx_unionid", wx_unionid),
            ("wx_mini_openid", wx_mini_openid),
            ("wx_openid", wx_openid),
            ("phone", phone),
            ("phone_number", phone),
        ]:
            if val and not getattr(user, field, None):
                try:
                    setattr(user, field, val)
                    db.flush()
                    updated = True
                except IntegrityError:
                    db.rollback()
                    raise HTTPException(
                        status_code=409,
                        detail="微信身份已绑定其他账号，请联系客服处理",
                    )
        if updated:
            db.commit()
            db.refresh(user)
        return user, False, ""

    # ── 新用户创建 ──
    cutoff = datetime.now() - timedelta(hours=FREE_POINT_HOURS)

    abuse_count = 0
    if device_id or client_ip:
        conditions = []
        if device_id:
            conditions.append(User.device_id == device_id)
        if client_ip:
            conditions.append(User.registration_ip == client_ip)
        abuse_count = db.query(func.count(User.id)).filter(
            or_(*conditions),
            User.created_at >= cutoff,
        ).scalar() or 0

    give_free_points = abuse_count < MAX_FREE_ACCOUNTS_PER_DEVICE

    if give_free_points:
        # ★ 从数据库 SystemConfig 读取奖励点数（运营可在后台可视化调整）
        bonus_credits = _get_config_int(db, "register_bonus", _ENV_SIGNUP_BONUS)
        free_credits = _get_config_int(db, "register_free", _ENV_SIGNUP_FREE)
        total_points = bonus_credits + free_credits
        free_expire = datetime.now() + timedelta(hours=FREE_POINT_HOURS)
    else:
        bonus_credits = 0
        free_credits = 0
        total_points = 0
        free_expire = None

    user = User(
        balance_credits=total_points,
        membership_tier="free",
        free_point_expire_at=free_expire,
        device_id=device_id,
        registration_ip=client_ip,
        wx_openid=wx_openid or None,
        wx_mini_openid=wx_mini_openid or None,
        wx_unionid=wx_unionid or None,
        phone=phone or None,
        phone_number=phone or None,
        channel=channel,
        is_new_user=True,
    )
    db.add(user)
    db.flush()

    if give_free_points:
        db.add(BillingRecord(
            user_id=user.id,
            amount=bonus_credits,
            balance_after=total_points,
            record_type="BONUS",
            reason="新用户注册奖励",
        ))
        db.add(BillingRecord(
            user_id=user.id,
            amount=free_credits,
            balance_after=total_points,
            record_type="BONUS",
            reason=f"新用户免费体验（{FREE_POINT_HOURS}h后过期）",
        ))

    db.commit()
    db.refresh(user)

    if give_free_points:
        gift_note = (
            f"新用户注册奖励：赠送 {bonus_credits} 点"
            f" + {free_credits} 点免费体验（{FREE_POINT_HOURS}小时后过期）"
        )
    else:
        gift_note = "检测到设备异常，未赠送初始点数，请充值后使用"

    return user, True, gift_note


# ================================================================
# 匿名设备 Token 签发（仅接受 device_id，严禁 phone/wx_openid）
# ================================================================
@router.post("/token")
def get_token(
    device_id: str = Query("", description="设备指纹"),
    channel: str = Query("web", description="注册来源"),
    request: Request = None,
    db: Session = Depends(get_db),
):
    """仅用于匿名设备用户，不接受 phone 或 wx_openid。
    手机号登录请用 /auth/login，微信授权请用 /auth/wechat/official。"""
    if not device_id:
        raise HTTPException(status_code=400, detail="device_id 不能为空")
    client_ip = _get_client_ip(request) if request else ""
    user, is_new, gift_note = _find_or_create_user(
        db,
        device_id=device_id,
        channel=channel,
        client_ip=client_ip,
    )
    token = create_token(user.id, role="user")
    return {
        "token": token,
        "user": user.to_dict(),
        "is_new_user": is_new,
        "gift_note": gift_note,
    }


# ================================================================
# 手机号 + 密码 注册 / 登录
# ================================================================
class PhoneRegisterBody(BaseModel):
    phone: str
    password: str


class PhoneLoginBody(BaseModel):
    phone: str
    password: str


@router.post("/register")
def phone_register(
    body: PhoneRegisterBody,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """手机号 + 密码注册。phone 必填且唯一，密码哈希入库，返回 JWT。"""
    phone = body.phone.strip()
    password = body.password.strip()

    if not phone or len(phone) < 11:
        raise HTTPException(status_code=400, detail="请输入有效的手机号")
    if not password or len(password) < 6:
        raise HTTPException(status_code=400, detail="密码至少 6 位")

    # 检查手机号是否已注册（双字段 OR 查询）
    existing = find_user_by_phone(db, phone)
    if existing:
        raise HTTPException(status_code=409, detail="该手机号已注册，请直接登录")

    client_ip = _get_client_ip(request) if request else ""

    # 防刷检查
    cutoff = datetime.now() - timedelta(hours=FREE_POINT_HOURS)
    abuse_count = db.query(func.count(User.id)).filter(
        User.registration_ip == client_ip,
        User.created_at >= cutoff,
    ).scalar() or 0

    give_free_points = abuse_count < MAX_FREE_ACCOUNTS_PER_DEVICE

    if give_free_points:
        bonus_credits = _get_config_int(db, "register_bonus", _ENV_SIGNUP_BONUS)
        free_credits = _get_config_int(db, "register_free", _ENV_SIGNUP_FREE)
        total_points = bonus_credits + free_credits
        free_expire = datetime.now() + timedelta(hours=FREE_POINT_HOURS)
    else:
        total_points = 0
        free_expire = None

    try:
        user = User(
            balance_credits=total_points,
            membership_tier="free",
            free_point_expire_at=free_expire,
            registration_ip=client_ip,
            phone=phone,
            phone_number=phone,
            password_hash=_hash_password(password),
            channel="phone",
            is_new_user=True,
        )
        db.add(user)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该手机号已注册，请直接登录")

    if give_free_points:
        db.add(BillingRecord(
            user_id=user.id,
            amount=bonus_credits if give_free_points else 0,
            balance_after=total_points,
            record_type="BONUS",
            reason="新用户注册奖励",
        ))
        db.add(BillingRecord(
            user_id=user.id,
            amount=free_credits if give_free_points else 0,
            balance_after=total_points,
            record_type="BONUS",
            reason=f"新用户免费体验（{FREE_POINT_HOURS}h后过期）",
        ))

    db.commit()
    db.refresh(user)

    token = create_token(user.id, role="user")
    gift_note = (
        f"注册成功！赠送 {bonus_credits} 点 + {free_credits} 点免费体验"
        if give_free_points
        else "注册成功，请充值后使用"
    )

    return {
        "token": token,
        "user": user.to_dict(),
        "is_new_user": True,
        "gift_note": gift_note,
    }


@router.post("/login")
def phone_login(
    body: PhoneLoginBody,
    db: Session = Depends(get_db),
):
    """手机号 + 密码登录，校验成功返回 JWT。"""
    phone = body.phone.strip()
    password = body.password.strip()

    if not phone or not password:
        raise HTTPException(status_code=400, detail="请输入手机号和密码")

    user = find_user_by_phone(db, phone)
    if not user:
        raise HTTPException(status_code=401, detail="手机号未注册")

    if not user.password_hash or not _verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="密码错误")

    token = create_token(user.id, role="user")
    return {
        "token": token,
        "user": user.to_dict(),
        "is_new_user": False,
        "gift_note": "",
    }


# ================================================================
# 公众号网页授权登录
# ================================================================
class WechatOfficialBody(BaseModel):
    code: str
    state: str = ""


@router.post("/wechat/official")
def wechat_official_login(
    body: WechatOfficialBody,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """微信公众号网页授权登录。
    前端传入 wx.authorize() 返回的 code，后端换取 openid 后签发 JWT。
    流程：code → access_token → openid → find/create user → JWT。
    """
    if not WECHAT_MP_APPID or not WECHAT_MP_SECRET:
        raise HTTPException(
            status_code=503,
            detail="微信公众号未配置（WECHAT_MP_APPID / WECHAT_MP_SECRET 缺失）",
        )

    # 1. 调用微信接口换取 openid
    wx_url = (
        "https://api.weixin.qq.com/sns/oauth2/access_token"
        f"?appid={WECHAT_MP_APPID}"
        f"&secret={WECHAT_MP_SECRET}"
        f"&code={body.code}"
        "&grant_type=authorization_code"
    )

    import httpx
    try:
        wx_resp = httpx.get(wx_url, timeout=10)
        wx_data = wx_resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="微信接口请求失败，请重试")

    if "errcode" in wx_data and wx_data["errcode"] != 0:
        err_map = {
            40029: "code 无效，请重新授权",
            40163: "code 已被使用，请重新授权",
            41002: "appid 配置错误",
            -1: "微信接口限频，请稍后重试",
        }
        detail = err_map.get(wx_data["errcode"], "invalid_code")
        raise HTTPException(status_code=400, detail=detail)

    openid = wx_data.get("openid", "")
    if not openid:
        raise HTTPException(status_code=400, detail="invalid_code")

    # 2. 查找或创建用户
    client_ip = _get_client_ip(request) if request else ""
    user, is_new, gift_note = _find_or_create_user(
        db,
        wx_openid=openid,
        channel="official_account",
        client_ip=client_ip,
    )

    # 3. 签发 JWT
    token = create_token(user.id, role="user")
    return {
        "token": token,
        "user": user.to_dict(),
        "is_new_user": is_new,
        "gift_note": gift_note,
        "wx_openid": openid,
    }


# ═══════════════════════════════════════════════════════════
# Phase 16: 微信小程序登录
# ═══════════════════════════════════════════════════════════

class WechatMiniBody(BaseModel):
    code: str


@router.post("/wechat/mini")
def wechat_mini_login(
    body: WechatMiniBody,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """微信小程序登录。
    小程序端 wx.login() 返回 code，后端 jscode2session 换取 openid / unionid。
    流程：code → jscode2session → openid + unionid → find/create user → JWT。
    session_key 不返回前端，不持久化。
    """
    # ── 读取小程序凭证：优先从 DB SystemConfig，fallback 环境变量 ──
    mini_appid = _get_config_str(db, "wx_mini_appid",
                                 os.getenv("WECHAT_MINI_APPID", ""))
    mini_secret = _get_config_str(db, "wx_mini_secret",
                                  os.getenv("WECHAT_MINI_SECRET", ""))
    if not mini_appid or not mini_secret:
        raise HTTPException(
            status_code=503,
            detail="小程序未配置（请在管理后台 → 系统参数中填写 wx_mini_appid / wx_mini_secret）",
        )

    # 1. 调用 jscode2session 换取 openid + unionid
    wx_url = (
        "https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={mini_appid}"
        f"&secret={mini_secret}"
        f"&js_code={body.code}"
        "&grant_type=authorization_code"
    )

    import httpx
    try:
        wx_resp = httpx.get(wx_url, timeout=10)
        wx_data = wx_resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="微信接口请求失败，请重试")

    if "errcode" in wx_data and wx_data["errcode"] != 0:
        err_map = {
            40029: "code 无效，请重新调用 wx.login()",
            40163: "code 已被使用，请重新调用 wx.login()",
            41002: "appid 配置错误",
            -1: "微信接口限频，请稍后重试",
        }
        detail = err_map.get(wx_data["errcode"],
                             f"微信登录失败（{wx_data.get('errmsg', '')}）")
        raise HTTPException(status_code=400, detail=detail)

    openid = wx_data.get("openid", "")
    unionid = wx_data.get("unionid", "")
    if not openid:
        raise HTTPException(status_code=400, detail="invalid_code")

    # 2. 查找或创建用户
    client_ip = _get_client_ip(request) if request else ""
    user, is_new, gift_note = _find_or_create_user(
        db,
        wx_mini_openid=openid,
        wx_unionid=unionid,
        channel="mini_program",
        client_ip=client_ip,
    )

    # 3. 签发 JWT（session_key 不返回前端）
    token = create_token(user.id, role="user")
    resp = {
        "token": token,
        "user": user.to_dict(),
        "is_new_user": is_new,
        "gift_note": gift_note,
        "wx_mini_openid": openid,
    }
    if unionid:
        resp["wx_unionid"] = unionid
    return resp


# ═══════════════════════════════════════════════════════════
# Phase 23N: 微信小程序手机号绑定
# ═══════════════════════════════════════════════════════════

class BindPhoneBody(BaseModel):
    code: str


@router.post("/wechat/mini/bind-phone")
def wechat_mini_bind_phone(
    body: BindPhoneBody,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """微信小程序手机号快速验证。
    小程序端 button open-type="getPhoneNumber" 返回 code，
    后端调用 getPhoneNumber 接口换取手机号，写入 User.phone 字段。
    使用已有 wx_mini_appid / wx_mini_secret 配置。
    """
    mini_appid = _get_config_str(db, "wx_mini_appid",
                                 os.getenv("WECHAT_MINI_APPID", ""))
    mini_secret = _get_config_str(db, "wx_mini_secret",
                                  os.getenv("WECHAT_MINI_SECRET", ""))
    if not mini_appid or not mini_secret:
        raise HTTPException(
            status_code=503,
            detail="小程序未配置，无法绑定手机号",
        )

    # 1. 获取 access_token
    import httpx
    try:
        token_resp = httpx.get(
            "https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={mini_appid}&secret={mini_secret}",
            timeout=10,
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token", "")
        if not access_token:
            raise HTTPException(status_code=502, detail="微信服务 token 获取失败")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="微信服务不可达")

    # 2. 换取手机号
    try:
        phone_resp = httpx.post(
            f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}",
            json={"code": body.code},
            timeout=10,
        )
        phone_data = phone_resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="微信手机号接口不可达")

    if phone_data.get("errcode", 0) != 0:
        raise HTTPException(
            status_code=400,
            detail=phone_data.get("errmsg", "手机号获取失败"),
        )

    phone_info = phone_data.get("phone_info", {})
    phone_number = phone_info.get("purePhoneNumber", "")
    if not phone_number:
        raise HTTPException(status_code=400, detail="未获取到手机号")

    # 3. 检查手机号是否已被其他账号占用（双字段 OR 查询）
    existing = find_user_by_phone(db, phone_number)
    if existing and existing.id != user["user_id"]:
        raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")

    # 4. 写入 User 表（双字段 + IntegrityError 兜底）
    db_user = db.query(User).filter(User.id == user["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    try:
        db_user.phone_number = phone_number
        db_user.phone = phone_number
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")

    return {"ok": True, "phone": phone_number}


# ═══════════════════════════════════════════════════════════
# Phase 23N: 微信小程序手机号一键登录
# ═══════════════════════════════════════════════════════════

class WechatMiniPhoneLoginBody(BaseModel):
    login_code: str       # wx.login 返回的 code
    phone_code: str       # getPhoneNumber 返回的 code


@router.post("/wechat/mini/phone-login")
def wechat_mini_phone_login(
    body: WechatMiniPhoneLoginBody,
    request: Request = None,
    db: Session = Depends(get_db),
):
    """微信小程序手机号一键登录。
    合并 wx.login + getPhoneNumber 两步为单一接口：
    1. login_code → jscode2session → openid/unionid
    2. phone_code → 换取手机号
    3. find/create user → 绑定手机号 → 签发 JWT
    不要求用户先完成微信登录再绑定手机号。
    """
    mini_appid = _get_config_str(db, "wx_mini_appid",
                                 os.getenv("WECHAT_MINI_APPID", ""))
    mini_secret = _get_config_str(db, "wx_mini_secret",
                                  os.getenv("WECHAT_MINI_SECRET", ""))
    if not mini_appid or not mini_secret:
        raise HTTPException(
            status_code=503,
            detail="小程序未配置（请在管理后台 → 系统参数中填写 wx_mini_appid / wx_mini_secret）",
        )

    import httpx

    # Step 1: login_code → openid
    wx_url = (
        "https://api.weixin.qq.com/sns/jscode2session"
        f"?appid={mini_appid}"
        f"&secret={mini_secret}"
        f"&js_code={body.login_code}"
        "&grant_type=authorization_code"
    )
    try:
        wx_resp = httpx.get(wx_url, timeout=10)
        wx_data = wx_resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="微信服务不可达")

    wx_err = wx_data.get("errcode", 0)
    if wx_err:
        raise HTTPException(status_code=400, detail="invalid_code")
    openid = wx_data.get("openid", "")
    unionid = wx_data.get("unionid", "")
    if not openid:
        raise HTTPException(status_code=400, detail="invalid_code")

    # Step 2: 获取 access_token 后换取手机号
    try:
        token_resp = httpx.get(
            "https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={mini_appid}&secret={mini_secret}",
            timeout=10,
        )
        token_data = token_resp.json()
        access_token = token_data.get("access_token", "")
        if not access_token:
            raise HTTPException(status_code=502, detail="微信服务 token 获取失败")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=502, detail="微信服务不可达")

    try:
        phone_resp = httpx.post(
            f"https://api.weixin.qq.com/wxa/business/getuserphonenumber?access_token={access_token}",
            json={"code": body.phone_code},
            timeout=10,
        )
        phone_data = phone_resp.json()
    except Exception:
        raise HTTPException(status_code=502, detail="微信手机号接口不可达")

    if phone_data.get("errcode", 0) != 0:
        raise HTTPException(
            status_code=400,
            detail=phone_data.get("errmsg", "手机号获取失败"),
        )

    phone_info = phone_data.get("phone_info", {})
    phone_number = phone_info.get("purePhoneNumber", "")
    if not phone_number:
        raise HTTPException(status_code=400, detail="未获取到手机号")

    # Step 3: 查找或创建用户 → 绑定手机号
    client_ip = _get_client_ip(request) if request else ""
    user, is_new, gift_note = _find_or_create_user(
        db,
        wx_mini_openid=openid,
        wx_unionid=unionid,
        phone=phone_number,
        channel="mini_program",
        client_ip=client_ip,
    )

    # 始终回写手机号（已有用户可能之前未绑定）
    # 先检查手机号是否被其他用户占用
    existing = find_user_by_phone(db, phone_number)
    if existing and existing.id != user.id:
        raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")
    try:
        if not user.phone_number:
            user.phone_number = phone_number
        if not user.phone:
            user.phone = phone_number
        db.flush()
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="该手机号已绑定其他账号")

    # Step 4: 签发 JWT
    token = create_token(user.id, role="user")
    resp = {
        "token": token,
        "user": user.to_dict(),
        "is_new_user": is_new,
        "gift_note": gift_note,
        "wx_mini_openid": openid,
        "phone": phone_number,
    }
    if unionid:
        resp["wx_unionid"] = unionid
    return resp
