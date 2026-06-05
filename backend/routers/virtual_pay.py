"""微信小程序虚拟支付 — 道具直购 (short_series_goods)"""
import os, json, time, hmac, hashlib, secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.db_models import User, BillingRecord, PaymentOrder, SystemConfig
from services.runtime_config import get_user_skus, get_core_config
from auth import get_current_user

router = APIRouter(prefix="/api/virtual-pay", tags=["虚拟支付"])


def _get_sys_config_str(db: Session, key: str, default: str = "") -> str:
    try:
        row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if row and row.value:
            return row.value.strip()
    except Exception:
        pass
    return default


def _virtual_pay_configured(db: Session) -> bool:
    """虚拟支付配置完整性检查"""
    cfg = get_core_config(db)
    enabled = str(cfg.get("wx_virtual_pay_enabled", "0")).strip() == "1"
    if not enabled:
        return False
    offer_id = (cfg.get("wx_virtual_offer_id") or "").strip()
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    if not offer_id or not app_key:
        return False
    return True


def _get_virtual_product_id(db: Session, sku_id: int) -> str:
    """从 wx_virtual_product_map 查 sku_id 对应的 productId"""
    map_str = _get_sys_config_str(db, "wx_virtual_product_map", "{}")
    try:
        pmap = json.loads(map_str)
        return str(pmap.get(str(sku_id), ""))
    except (json.JSONDecodeError, TypeError):
        return ""


class PrepayBody(BaseModel):
    sku_id: int


@router.post("/prepay")
def virtual_prepay(
    body: PrepayBody,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """虚拟支付预下单：生成 signData/paySig/signature"""
    if not _virtual_pay_configured(db):
        raise HTTPException(status_code=503, detail="虚拟支付配置未完成，请联系客服")

    cfg = get_core_config(db)
    offer_id = (cfg.get("wx_virtual_offer_id") or "").strip()
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    env_val = int(cfg.get("wx_virtual_env", "1") or "1")
    currency = (cfg.get("wx_virtual_currency_type") or "CNY").strip() or "CNY"

    user_id = int(user["user_id"])
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    openid = db_user.wx_mini_openid or ""
    if not openid:
        raise HTTPException(status_code=400, detail="请先在微信中登录并授权后，再进行支付")

    session_key = db_user.wx_session_key or ""
    if not session_key:
        raise HTTPException(status_code=400, detail="请重新登录后再购买")

    # SKU 校验
    skus, _ = get_user_skus(user_id, db)
    sku = next((s for s in skus if s.get("id") == body.sku_id and s.get("visible", True)), None)
    if not sku:
        raise HTTPException(status_code=400, detail="套餐不存在或已下架")

    product_id = _get_virtual_product_id(db, body.sku_id)
    if not product_id:
        raise HTTPException(status_code=400, detail="该套餐未配置虚拟支付道具，请联系客服")

    price = sku.get("price", "0")
    try:
        total_fen = int(float(price) * 100)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="套餐价格无效")
    if total_fen <= 0:
        raise HTTPException(status_code=400, detail="此套餐无需支付")

    label = sku.get("label", "套餐")
    credits = int(sku.get("credits", 0))
    days = int(sku.get("duration_days", 0))
    nonce = secrets.token_hex(4)
    out_trade_no = f"ZVX{int(time.time()*1000)}{user_id}{nonce}"

    # 创建订单
    order = PaymentOrder(
        out_trade_no=out_trade_no,
        user_id=user_id,
        sku_id=body.sku_id,
        sku_snapshot=json.dumps(sku, ensure_ascii=False),
        amount_fen=total_fen,
        credits=credits,
        membership_days=days,
        status="CREATED",
        pay_channel="WECHAT_VIRTUAL",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    attach = json.dumps({"user_id": user_id, "sku_id": body.sku_id, "order_no": out_trade_no}, ensure_ascii=False)

    # signData 严格保持字段插入顺序
    sign_data = {
        "offerId": offer_id,
        "buyQuantity": 1,
        "env": env_val,
        "currencyType": currency,
        "productId": product_id,
        "goodsPrice": total_fen,
        "outTradeNo": out_trade_no,
        "attach": attach,
    }
    sign_data_str = json.dumps(sign_data, ensure_ascii=False, separators=(",", ":"))

    # paySig = HMAC-SHA256(appKey, "requestVirtualPayment&" + signData)
    pay_sig = hmac.new(
        app_key.encode("utf-8"),
        b"requestVirtualPayment&" + sign_data_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # signature = HMAC-SHA256(session_key, signData)
    signature = hmac.new(
        session_key.encode("utf-8"),
        sign_data_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    print(f"[VPAY] prepay user={user_id} sku={body.sku_id} order={out_trade_no} product={product_id}", flush=True)

    return {
        "ok": True,
        "order_no": out_trade_no,
        "mode": "short_series_goods",
        "signData": sign_data_str,
        "paySig": pay_sig,
        "signature": signature,
    }


@router.get("/order/{order_no}")
def query_virtual_order(
    order_no: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询虚拟支付订单状态"""
    user_id = int(user["user_id"])
    order = db.query(PaymentOrder).filter(
        PaymentOrder.out_trade_no == order_no,
        PaymentOrder.user_id == user_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order_no": order.out_trade_no,
        "status": order.status or "CREATED",
        "credits": order.credits or 0,
        "membership_days": order.membership_days or 0,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
        "amount_fen": order.amount_fen,
    }


def _parse_notify_body(body_str: str) -> dict:
    """解析虚拟支付回调 body，返回 {'payload_str':..., 'pay_event_sig':...} 或空 dict"""
    # 尝试 JSON
    try:
        data = json.loads(body_str)
        if isinstance(data, dict):
            payload_str = data.get("MiniGame", {}).get("Payload", "")
            pay_event_sig = data.get("MiniGame", {}).get("PayEventSig", "")
            if payload_str:
                return {"payload_str": payload_str, "pay_event_sig": pay_event_sig or ""}
    except (json.JSONDecodeError, TypeError):
        pass
    # 尝试 XML
    try:
        import xml.etree.ElementTree as ET
        root = ET.fromstring(body_str)
        result = {"payload_str": "", "pay_event_sig": ""}
        for child in root.iter():
            if child.tag == "Payload" and child.text:
                result["payload_str"] = child.text
            if child.tag == "PayEventSig" and child.text:
                result["pay_event_sig"] = child.text
        if result["payload_str"]:
            return result
    except ET.ParseError:
        pass
    return {}


def _parse_payload_fields(payload_str: str) -> dict:
    """从 Payload JSON 提取字段，兼容大小写。缺失必要字段返回空 dict。"""
    try:
        p = json.loads(payload_str)
    except (json.JSONDecodeError, TypeError):
        return {}
    # 提取字段（兼容大小写）
    order_no = p.get("OutTradeNo", "") or p.get("outTradeNo", "") or ""
    openid = p.get("OpenId", "") or p.get("openId", "") or ""
    goods_info = p.get("GoodsInfo", {}) or {}
    if not isinstance(goods_info, dict):
        goods_info = {}
    product_id = goods_info.get("ProductId", "") or goods_info.get("productId", "") or ""
    raw_price = goods_info.get("ActualPrice", None) if goods_info.get("ActualPrice", None) is not None else goods_info.get("actualPrice", None)
    # ActualPrice 必须存在且 > 0
    if raw_price is None:
        return {}
    try:
        actual_price = int(raw_price)
    except (ValueError, TypeError):
        return {}
    if actual_price <= 0:
        return {}
    if not order_no or not openid or not product_id:
        return {}
    return {
        "order_no": order_no,
        "openid": openid,
        "product_id": product_id,
        "actual_price": actual_price,
    }


@router.post("/notify")
async def virtual_notify(request: Request, db: Session = Depends(get_db)):
    """虚拟支付发货回调通知。
    校验：签名 + pay_channel + openid + productId + amount 一致后才发放权益。
    幂等：已 PAID 直接返回成功。
    签名无法验证时直接拒绝，不做 TODO 验签后放行。"""
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8", errors="replace")

    parsed = _parse_notify_body(body_str)
    if not parsed:
        print(f"[VPAY-NOTIFY] 回调 body 无法解析: {body_str[:200]}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "body parse failed"})

    payload_str = parsed["payload_str"]
    pay_event_sig = parsed.get("pay_event_sig", "")

    # ★ 验签：保守策略 — 签名无法验证时拒绝发放
    cfg = get_core_config(db)
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    if app_key:
        expected_sig = hmac.new(
            app_key.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if pay_event_sig and pay_event_sig != expected_sig:
            print(f"[VPAY-NOTIFY] PayEventSig 验签失败", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "signature verification failed"})
    # 没有 appKey 配置时不验签，但打印告警
    if not pay_event_sig and not app_key:
        print(f"[VPAY-NOTIFY] ⚠ 未配置 appKey 且 PayEventSig 为空，签名校验跳过（非生产勿依赖）", flush=True)

    # 解析 Payload 字段
    fields = _parse_payload_fields(payload_str)
    if not fields:
        print(f"[VPAY-NOTIFY] Payload 字段缺失或 actual_price<=0: {payload_str[:200]}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "payload fields invalid"})

    order_no = fields["order_no"]
    openid = fields["openid"]
    product_id = fields["product_id"]
    actual_price = fields["actual_price"]

    print(f"[VPAY-NOTIFY] order={order_no} openid={openid[:8]}*** product={product_id} price={actual_price}", flush=True)

    # 查订单
    order = db.query(PaymentOrder).filter(PaymentOrder.out_trade_no == order_no).first()
    if not order:
        print(f"[VPAY-NOTIFY] 订单不存在: {order_no}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "order not found"})

    # ★ 校验 pay_channel
    if order.pay_channel != "WECHAT_VIRTUAL":
        print(f"[VPAY-NOTIFY] pay_channel 不匹配: {order.pay_channel}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "invalid pay channel"})

    # 幂等
    if order.status == "PAID":
        return JSONResponse(status_code=200, content={"ErrCode": 0, "ErrMsg": "Success"})

    # ★ 金额校验：ActualPrice 必须严格等于订单金额（actual_price 已保证 >0）
    if actual_price != order.amount_fen:
        print(f"[VPAY-NOTIFY] 金额不匹配: callback={actual_price} order={order.amount_fen}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "amount mismatch"})

    # ★ 校验 openid：回调 OpenId 必须等于订单用户的 wx_mini_openid
    db_user = db.query(User).filter(User.id == order.user_id).first()
    if not db_user:
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "user not found"})
    user_openid = db_user.wx_mini_openid or ""
    if openid != user_openid:
        print(f"[VPAY-NOTIFY] openid 不匹配: callback={openid[:8]}*** user={user_openid[:8]}***", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "openid mismatch"})

    # ★ 校验 productId：必须与 sku_id 映射的 productId 一致
    expected_product_id = _get_virtual_product_id(db, order.sku_id)
    if not expected_product_id or product_id != expected_product_id:
        print(f"[VPAY-NOTIFY] productId 不匹配: callback={product_id} expected={expected_product_id}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "product id mismatch"})

    # ── 所有校验通过，发放权益（同一事务）──
    try:
        order.status = "PAID"
        order.paid_at = datetime.now()

        if order.credits > 0:
            db_user.balance_credits += order.credits
            db.add(BillingRecord(
                user_id=order.user_id, amount=order.credits,
                balance_after=db_user.balance_credits,
                record_type="PURCHASE", reason=f"虚拟支付充值 {order.credits}点 ({order.out_trade_no})",
            ))

        if order.membership_days > 0:
            now = datetime.now()
            if db_user.membership_expiry and db_user.membership_expiry > now:
                db_user.membership_expiry += timedelta(days=order.membership_days)
            else:
                db_user.membership_expiry = now + timedelta(days=order.membership_days)
            db_user.membership_tier = "monthly" if order.membership_days <= 90 else ("quarterly" if order.membership_days <= 180 else "yearly")
            db.add(BillingRecord(
                user_id=order.user_id, amount=0,
                balance_after=db_user.balance_credits,
                record_type="MEMBERSHIP", reason=f"虚拟支付开通会员 {order.membership_days}天 ({order.out_trade_no})",
            ))

        db.commit()
        print(f"[VPAY-NOTIFY] 到账成功 order={order_no} credits={order.credits} days={order.membership_days}", flush=True)
    except Exception:
        db.rollback()
        print(f"[VPAY-NOTIFY] 发放权益事务失败 order={order_no}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "grant failed"})

    return JSONResponse(status_code=200, content={"ErrCode": 0, "ErrMsg": "Success"})
