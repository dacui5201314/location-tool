"""数据库 ORM 模型"""
import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, func
from database import Base


def _new_uuid() -> str:
    return uuid.uuid4().hex


class SystemConfig(Base):
    """系统配置键值表 — 持久化所有系统级设置"""
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, index=True, nullable=False, comment="配置键")
    value = Column(Text, default="", comment="配置值")
    description = Column(String(200), default="", comment="配置项中文说明")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "key": self.key,
            "value": self.value,
            "description": self.description or "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(20), unique=True, index=True, nullable=True, comment="手机号")
    avatar_url = Column(String(500), default="", comment="头像URL")
    nickname = Column(String(80), default="", comment="用户昵称")
    balance_credits = Column(Integer, default=1, comment="剩余分析点数（即 points），新用户默认赠送 1 点")
    membership_tier = Column(String(20), default="free", comment="会员等级 free/monthly/quarterly/yearly")
    membership_expiry = Column(DateTime, nullable=True, comment="会员过期时间")
    free_point_expire_at = Column(DateTime, nullable=True, comment="免费赠送点数过期时间（注册+24h），过期后赠送点数失效")
    device_id = Column(String(100), default="", comment="注册设备指纹 UUID")
    registration_ip = Column(String(45), default="", comment="注册时客户端 IP")
    # 微信打通
    wx_unionid = Column(String(64), unique=True, nullable=True, comment="微信 UnionID（跨应用统一标识）")
    wx_mp_openid = Column(String(64), unique=True, nullable=True, comment="公众号 OpenID")
    wx_mini_openid = Column(String(64), unique=True, nullable=True, comment="小程序 OpenID")
    wx_session_key = Column(Text, nullable=True, comment="小程序 session_key（虚拟支付签名用，不返回前端）")
    wx_openid = Column(String(64), unique=True, index=True, nullable=True, comment="★ 统一微信 OpenID（当前接入端）")
    phone = Column(String(20), unique=True, index=True, nullable=True, comment="★ 手机号（未来核心主键）")
    channel = Column(String(30), default="web", comment="注册来源 official_account/mini_program/app/web")
    password_hash = Column(String(128), default="", comment="PBKDF2 密码哈希")
    is_new_user = Column(Boolean, default=True, comment="是否新用户（未完成过首次分析）")
    created_at = Column(DateTime, default=func.now())

    @property
    def points(self):
        return self.balance_credits

    @property
    def is_member(self):
        if not self.membership_expiry:
            return False
        return self.membership_expiry > datetime.now()

    @property
    def membership_days_left(self):
        if not self.membership_expiry:
            return 0
        delta = (self.membership_expiry - datetime.now()).days
        return max(0, delta)

    @property
    def free_point_active(self):
        """免费赠送点数是否在有效期内"""
        if not self.free_point_expire_at:
            return False
        return self.free_point_expire_at > datetime.now()

    @property
    def free_point_seconds_left(self):
        """免费点数剩余秒数，0 表示已过期或无免费点数"""
        if not self.free_point_expire_at:
            return 0
        delta = (self.free_point_expire_at - datetime.now()).total_seconds()
        return max(0, int(delta))

    def to_dict(self):
        return {
            "id": self.id,
            "phone_number": self.phone_number or "",
            "avatar_url": self.avatar_url or "",
            "nickname": self.nickname or "",
            "balance_credits": self.balance_credits,
            "points": self.balance_credits,
            "membership_tier": self.membership_tier,
            "membership_expiry": self.membership_expiry.isoformat() if self.membership_expiry else None,
            "is_member": self.is_member,
            "membership_days_left": self.membership_days_left,
            "free_point_active": self.free_point_active,
            "free_point_expire_at": self.free_point_expire_at.isoformat() if self.free_point_expire_at else None,
            "free_point_seconds_left": self.free_point_seconds_left,
            "phone": self.phone or "",
            "channel": self.channel or "web",
            "is_new_user": bool(self.is_new_user) if self.is_new_user is not None else True,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AnalysisRecord(Base):
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    report_uuid = Column(String(32), unique=True, index=True, default=_new_uuid, comment="公开唯一标识（防遍历）")
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    brand_desc = Column(String(200), default="", comment="品牌描述")
    address = Column(String(500), default="", comment="详细地址")
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    business_type = Column(String(50), default="", comment="选址业态")
    store_size = Column(Integer, default=0, comment="门店面积")
    overall_score = Column(Integer, default=0, comment="综合评分")
    report_json = Column(Text, default="", comment="完整分析报告JSON")
    report_file = Column(String(500), default="", comment="本地报告文件路径")
    report_url = Column(String(500), default="", comment="云端报告URL")
    is_pdf_unlocked = Column(Integer, default=0, comment="PDF导出已解锁 0=未解锁 1=已解锁")
    share_token = Column(String(64), unique=True, nullable=True, default=None, comment="分享令牌（随机生成，owner 可创建）")
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "report_uuid": self.report_uuid or "",
            "brand_desc": self.brand_desc,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "business_type": self.business_type,
            "store_size": self.store_size,
            "overall_score": self.overall_score,
            "report_file": self.report_file,
            "report_url": self.report_url,
            "is_pdf_unlocked": bool(self.is_pdf_unlocked),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SavedLocation(Base):
    __tablename__ = "saved_locations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    custom_name = Column(String(200), default="", comment="用户自定义名称")
    address = Column(String(500), default="", comment="详细地址")
    latitude = Column(Float, default=0.0)
    longitude = Column(Float, default=0.0)
    latest_report_uuid = Column(String(32), default="", comment="最近一次分析生成的 report_uuid")
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "custom_name": self.custom_name,
            "address": self.address,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class RedeemCode(Base):
    __tablename__ = "redeem_codes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), unique=True, index=True, nullable=False, comment="兑换码")
    credits = Column(Integer, default=1, comment="包含分析点数")
    is_used = Column(Integer, default=0, comment="0=未使用 1=已使用")
    used_by = Column(Integer, default=0, comment="使用者用户ID")
    used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    batch_id = Column(String(50), default="", comment="批次标识")
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "credits": self.credits,
            "is_used": self.is_used,
            "used_by": self.used_by,
            "used_at": self.used_at.isoformat() if self.used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "batch_id": self.batch_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class OperationLog(Base):
    """管理员操作审计日志 — 点数/套餐变更强制留痕"""
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, default=0, comment="操作者ID")
    user_id = Column(Integer, index=True, nullable=False, comment="目标用户ID")
    type = Column(String(30), default="", comment="变更类型")
    before_value = Column(String(200), default="")
    after_value = Column(String(200), default="")
    change_amount = Column(String(50), default="")
    reason = Column(String(300), default="")
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id, "admin_id": self.admin_id, "user_id": self.user_id,
            "type": self.type or "", "before_value": self.before_value or "",
            "after_value": self.after_value or "", "change_amount": self.change_amount or "",
            "reason": self.reason or "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BillingRecord(Base):
    """点数流水表 — 记录每一笔点数变动"""
    __tablename__ = "billing_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False, comment="用户ID")
    amount = Column(Integer, default=0, comment="点数变动（正=充值/奖励，负=消耗）")
    balance_after = Column(Integer, default=0, comment="变动后余额")
    record_type = Column(String(20), default="", comment="流水类型 BONUS/PURCHASE/CONSUME/REFUND")
    reason = Column(String(200), default="", comment="变动原因")
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "balance_after": self.balance_after,
            "record_type": self.record_type or "",
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class BusinessIndustry(Base):
    """业态专属规则 — 每个业态可绑定独立 AI 提示词/测算规则"""
    __tablename__ = "business_industries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(80), unique=True, default="", comment="业态名称")
    config_key = Column(String(40), default="", comment="对应 MASTER_TEMPLATES 的 key")
    exclusive_prompt = Column(Text, default="", comment="专属AI提示词/测算规则")
    is_active = Column(Integer, default=1, comment="启用状态 1=启用 0=停用")
    sort_order = Column(Integer, default=0, comment="排序权重")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name or "",
            "config_key": self.config_key or "",
            "exclusive_prompt": self.exclusive_prompt or "",
            "is_active": self.is_active if self.is_active is not None else 1,
            "sort_order": self.sort_order if self.sort_order is not None else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# ═══════════════════════════════════════════════════════════
# Phase 23O: 微信支付订单
# ═══════════════════════════════════════════════════════════
class PaymentOrder(Base):
    __tablename__ = "payment_orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    out_trade_no = Column(String(64), unique=True, index=True, nullable=False)
    transaction_id = Column(String(64), default="")
    user_id = Column(Integer, index=True, nullable=False)
    sku_id = Column(Integer, default=0)
    sku_snapshot = Column(Text, default="")
    amount_fen = Column(Integer, default=0)
    credits = Column(Integer, default=0)
    membership_days = Column(Integer, default=0)
    status = Column(String(20), default="CREATED")
    pay_channel = Column(String(20), default="WECHAT_JSAPI")
    paid_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "out_trade_no": self.out_trade_no,
            "transaction_id": self.transaction_id or "",
            "user_id": self.user_id,
            "sku_id": self.sku_id,
            "amount_fen": self.amount_fen,
            "credits": self.credits,
            "membership_days": self.membership_days,
            "status": self.status or "CREATED",
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Feedback(Base):
    """用户意见反馈"""
    __tablename__ = "feedbacks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    content = Column(Text, nullable=False)
    contact = Column(String(120), default="")
    image_urls = Column(Text, default="[]")
    credits_granted = Column(Integer, default=0)
    report_uuid = Column(String(64), default="")
    report_title = Column(String(200), default="")
    report_address = Column(Text, default="")
    source = Column(String(40), default="profile")
    status = Column(String(20), default="pending")
    admin_reply = Column(Text, default="")
    replied_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())


class AmapKey(Base):
    """高德 Web 服务 API Key 池"""
    __tablename__ = "amap_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(120), default="", comment="备注名")
    api_key = Column(String(128), nullable=False, default="", comment="高德 Web 服务 API Key")
    security_secret = Column(String(128), default="", comment="高德安全密钥（可选）")
    enabled = Column(Integer, default=1, comment="是否启用 1=启用 0=停用")
    priority = Column(Integer, default=0, comment="优先级，越小越优先")
    last_status = Column(String(60), default="", comment="最近状态码")
    last_info = Column(String(200), default="", comment="最近状态信息")
    last_infocode = Column(String(20), default="", comment="最近 infocode")
    last_checked_at = Column(DateTime, nullable=True, comment="最近检测时间")
    fail_count = Column(Integer, default=0, comment="连续失败次数")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict_admin(self):
        """管理后台返回：脱敏 key"""
        mk = ""
        if self.api_key:
            mk = self.api_key[:4] + "****" + self.api_key[-4:] if len(self.api_key) > 8 else "****"
        return {
            "id": self.id,
            "name": self.name,
            "masked_key": mk,
            "has_security_secret": bool(self.security_secret and self.security_secret.strip()),
            "enabled": bool(self.enabled),
            "priority": self.priority,
            "last_status": self.last_status or "",
            "last_info": self.last_info or "",
            "last_infocode": self.last_infocode or "",
            "last_checked_at": self.last_checked_at.isoformat() if self.last_checked_at else None,
            "fail_count": self.fail_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
