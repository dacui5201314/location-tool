"""微信小程序虚拟支付 — 道具直购 (short_series_goods)"""
import os, json, time, hmac, hashlib, secrets, httpx
from datetime import datetime, timedelta
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.db_models import User, BillingRecord, PaymentOrder, SystemConfig
from services.runtime_config import get_user_skus, get_core_config
from auth import get_current_user, get_current_admin

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


def _get_virtual_env(cfg) -> int:
    """读取虚拟支付环境配置，仅允许 0 或 1，非法值抛异常"""
    raw = (cfg.get("wx_virtual_env") or "").strip()
    if raw in ("0", "1"):
        return int(raw)
    raise HTTPException(status_code=503, detail="虚拟支付环境未正确配置，请联系客服")


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
    env_val = _get_virtual_env(cfg)
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

    print(f"[VPAY-PREPAY] user={user_id} sku={body.sku_id} order={out_trade_no} env={env_val} offer_id={offer_id} product_id={product_id} goods_price={total_fen} has_session_key={bool(session_key)} mode=short_series_goods", flush=True)

    return {
        "ok": True,
        "order_no": out_trade_no,
        "mode": "short_series_goods",
        "signData": sign_data_str,
        "paySig": pay_sig,
        "signature": signature,
    }


@router.post("/pay-existing/{order_no}")
def pay_existing_order(
    order_no: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """继续支付未完成的 CREATED 订单，返回 prepay 参数。不创建新订单。"""
    user_id = int(user["user_id"])
    order = db.query(PaymentOrder).filter(
        PaymentOrder.out_trade_no == order_no,
        PaymentOrder.user_id == user_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.pay_channel != "WECHAT_VIRTUAL":
        raise HTTPException(status_code=400, detail="仅支持虚拟支付订单")
    if order.status == "PAID":
        raise HTTPException(status_code=400, detail="订单已完成，无需重复支付")
    if order.status != "CREATED":
        if order.status in ("TIMEOUT", "CANCELLED", "FAILED"):
            raise HTTPException(status_code=400, detail="订单已关闭，请重新购买")
        raise HTTPException(status_code=400, detail=f"订单状态 {order.status} 不可支付")
    # auto-timeout orders older than 30 minutes
    if order.created_at and order.created_at < datetime.now() - timedelta(minutes=30):
        order.status = "TIMEOUT"
        db.commit()
        raise HTTPException(status_code=400, detail="订单已关闭，请重新购买")

    cfg = get_core_config(db)
    offer_id = (cfg.get("wx_virtual_offer_id") or "").strip()
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    env_val = _get_virtual_env(cfg)
    currency = (cfg.get("wx_virtual_currency_type") or "CNY").strip() or "CNY"

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    openid = db_user.wx_mini_openid or ""
    session_key = db_user.wx_session_key or ""
    if not openid or not session_key:
        raise HTTPException(status_code=400, detail="请重新登录后再支付")

    product_id = _get_virtual_product_id(db, order.sku_id)
    if not product_id:
        raise HTTPException(status_code=400, detail="该套餐未配置虚拟支付道具")

    sign_data = {
        "offerId": offer_id, "buyQuantity": 1, "env": env_val,
        "currencyType": currency, "productId": product_id,
        "goodsPrice": order.amount_fen or 0, "outTradeNo": order.out_trade_no,
        "attach": json.dumps({"user_id": user_id, "sku_id": order.sku_id, "order_no": order.out_trade_no}, ensure_ascii=False),
    }
    sign_data_str = json.dumps(sign_data, ensure_ascii=False, separators=(",", ":"))
    pay_sig = hmac.new(app_key.encode("utf-8"), b"requestVirtualPayment&" + sign_data_str.encode("utf-8"), hashlib.sha256).hexdigest()
    signature = hmac.new(session_key.encode("utf-8"), sign_data_str.encode("utf-8"), hashlib.sha256).hexdigest()

    print(f"[VPAY-PREPAY] pay-existing user={user_id} order={order_no} env={env_val} offer_id={offer_id} product_id={product_id} goods_price={order.amount_fen} has_session_key={bool(session_key)} mode=short_series_goods", flush=True)
    return {"ok": True, "order_no": order.out_trade_no, "mode": "short_series_goods", "signData": sign_data_str, "paySig": pay_sig, "signature": signature}


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

    label = ""
    try:
        snap = json.loads(order.sku_snapshot or "{}")
        label = snap.get("label", "")
    except Exception:
        pass

    return {
        "order_no": order.out_trade_no,
        "out_trade_no": order.out_trade_no,
        "sku_label": label,
        "amount_yuan": f"{order.amount_fen / 100:.2f}",
        "amount_fen": order.amount_fen,
        "credits": order.credits or 0,
        "membership_days": order.membership_days or 0,
        "pay_channel": order.pay_channel or "",
        "status": order.status or "CREATED",
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    }


def _grant_order(db: Session, order, user_id: int, db_user=None) -> bool:
    """发放订单权益（原子抢占 + 同事务发权益）。
    返回 True 表示发放成功或已 PAID（幂等）。
    返回 False 表示订单是终态，不应发放。
    """
    from services.payment_idempotency import claim_payment_order, grant_payment_benefits

    # ── 幂等快速返回 ──
    if order.status == "PAID":
        return True

    # ── 拒绝终态 ──
    if order.status in ("REFUNDED", "CANCELLED", "CLOSED", "FAILED"):
        print(f"[VPAY] _grant_order 拒绝终态 {order.out_trade_no} status={order.status}", flush=True)
        return False

    # ── 原子抢占 ──
    claimed = claim_payment_order(db, order)
    if not claimed:
        db.refresh(order)
        if order.status == "PAID":
            return True
        print(f"[VPAY] claim 失败 order={order.out_trade_no} status={order.status}", flush=True)
        return False

    # ── 发权益（同事务）──
    try:
        if db_user is None:
            db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            db.rollback()
            print(f"[VPAY] 用户不存在 order={order.out_trade_no}", flush=True)
            return False
        grant_payment_benefits(db, order)
        db.commit()
        print(f"[VPAY] 到账成功 order={order.out_trade_no} credits={order.credits} days={order.membership_days}", flush=True)
        return True
    except Exception:
        db.rollback()
        print(f"[VPAY] 发放权益事务失败 order={order.out_trade_no}", flush=True)
        return False


def _revoke_order(db: Session, order, db_user):
    """Deduct points and mark REFUNDED. Idempotent: skip if negative REFUND or REFUND_SHORTFALL already recorded."""
    if order.status in ("REFUNDED", "CLOSED"):
        existing = db.query(BillingRecord).filter(
            BillingRecord.user_id == order.user_id,
            BillingRecord.record_type.in_(["REFUND", "REFUND_SHORTFALL"]),
            BillingRecord.reason.contains(order.out_trade_no),
        ).first()
        if existing and (existing.amount < 0 or existing.record_type == "REFUND_SHORTFALL"):
            return
        print(f"[VPAY-REVOKE] status is {order.status} but no negative refund record, will fix", flush=True)

    prev_balance = db_user.balance_credits
    try:
        print(f"[VPAY-REVOKE] start order={order.out_trade_no} status={order.status} credits={order.credits} balance={prev_balance}", flush=True)

        existing_refund = db.query(BillingRecord).filter(
            BillingRecord.user_id == order.user_id,
            BillingRecord.record_type.in_(["REFUND", "REFUND_SHORTFALL"]),
            BillingRecord.reason.contains(order.out_trade_no),
        ).first()
        if existing_refund:
            if existing_refund.amount < 0 or existing_refund.record_type == "REFUND_SHORTFALL":
                print(f"[VPAY-REVOKE] existing refund record type={existing_refund.record_type} amount={existing_refund.amount}, skip", flush=True)
                order.status = "REFUNDED"
                db.commit()
                return
            else:
                print(f"[VPAY-REVOKE] CRITICAL existing refund amount={existing_refund.amount} is NOT negative, will fix", flush=True)

        deduct = order.credits or 0
        shortfall = 0
        if deduct > 0 and db_user.balance_credits >= deduct:
            db_user.balance_credits -= deduct
        elif deduct > 0:
            shortfall = deduct - db_user.balance_credits
            if db_user.balance_credits > 0:
                db_user.balance_credits = 0
                print(f"[VPAY-REVOKE] partial deducted before={prev_balance} deduct={deduct} shortfall={shortfall}", flush=True)
            else:
                print(f"[VPAY-REVOKE] no balance to deduct before=0 deduct={deduct} shortfall={shortfall}", flush=True)

        actual_deduct = deduct - shortfall
        # actual_deduct > 0: normal/partial deduction
        # actual_deduct == 0: no balance at all
        if actual_deduct > 0:
            reason = f"虚拟支付退款，扣回 {deduct}点 ({order.out_trade_no})"
            if shortfall > 0:
                reason += f" 余额不足欠扣{shortfall}点 需人工处理"
            db.add(BillingRecord(
                user_id=order.user_id, amount=-actual_deduct,
                balance_after=db_user.balance_credits,
                record_type="REFUND",
                reason=reason,
            ))
        else:
            # deduct > 0 but balance was 0: record as shortfall only, amount=0
            reason = f"虚拟支付退款 欠扣{deduct}点 余额为0 需人工处理 ({order.out_trade_no})"
            db.add(BillingRecord(
                user_id=order.user_id, amount=0,
                balance_after=db_user.balance_credits,
                record_type="REFUND_SHORTFALL",
                reason=reason,
            ))

        order.status = "REFUNDED"

        if order.membership_days > 0:
            now = datetime.now()
            if db_user.membership_expiry and db_user.membership_expiry > now:
                db_user.membership_expiry -= timedelta(days=order.membership_days)
                if db_user.membership_expiry <= now:
                    db_user.membership_expiry = now
                    db_user.membership_tier = "free"

        db.commit()
        print(f"[VPAY-REVOKE] completed status=REFUNDED order={order.out_trade_no} before={prev_balance} deduct={deduct} actual_deduct={actual_deduct} shortfall={shortfall} after={db_user.balance_credits}", flush=True)
    except Exception:
        db.rollback()
        raise


def _order_has_granted_benefits(db: Session, order) -> bool:
    """判断本订单是否已实际发放过权益（点数/会员）。
    条件：order.status == 'PAID'，或存在 BillingRecord
    类型为 PURCHASE/MEMBERSHIP 且 reason 包含本订单 out_trade_no。
    只匹配本订单，不按用户历史 PURCHASE/MEMBERSHIP 判断，避免误命中其他订单。"""
    if order.status == "PAID":
        return True
    record = db.query(BillingRecord).filter(
        BillingRecord.user_id == order.user_id,
        BillingRecord.record_type.in_(["PURCHASE", "MEMBERSHIP"]),
        BillingRecord.reason.contains(order.out_trade_no),
    ).first()
    return record is not None


def _mark_order_refunded_no_revoke(db: Session, order):
    """退款通知到达但权益从未发放 → 只同步 REFUNDED，不扣点/不扣会员/不写负向账本。"""
    order.status = "REFUNDED"
    db.commit()
    print(f"[VPAY] refund without revoke (benefits never granted) order={order.out_trade_no}", flush=True)


def _handle_refund_cancel_notify(db: Session, order, db_user,
                                  is_refund: bool, is_cancel: bool,
                                  order_no: str = "") -> dict:
    """处理退款/取消通知分支（从 virtual_notify 抽取，便于测试）。
    返回 {'ErrCode': int, 'ErrMsg': str}，由调用方包装为 JSONResponse。
    P1-A: 已发放权益才允许扣回；未发放权益只同步状态不扣余额。"""
    if order.status in ("REFUNDED", "CANCELLED", "CLOSED"):
        return {"ErrCode": 0, "ErrMsg": "Success"}

    has_benefits = _order_has_granted_benefits(db, order)

    if is_refund:
        if has_benefits:
            try:
                _revoke_order(db, order, db_user)
                return {"ErrCode": 0, "ErrMsg": "Success"}
            except Exception:
                db.rollback()
                print(f"[VPAY-NOTIFY] 退款处理失败 order={order_no or order.out_trade_no}", flush=True)
                return {"ErrCode": 1, "ErrMsg": "refund failed"}
        else:
            _mark_order_refunded_no_revoke(db, order)
            return {"ErrCode": 0, "ErrMsg": "Success"}

    if is_cancel:
        if has_benefits:
            oid = order_no or order.out_trade_no
            print(f"[VPAY] cancel refused: order={oid} has granted benefits (status={order.status}), "
                  f"must use refund path instead", flush=True)
            return {"ErrCode": 1,
                    "ErrMsg": "order has granted benefits, use refund instead"}
        else:
            order.status = "CANCELLED"
            db.commit()
            print(f"[VPAY] 订单取消 order={order_no or order.out_trade_no}", flush=True)
            return {"ErrCode": 0, "ErrMsg": "Success"}

    return {"ErrCode": 0, "ErrMsg": "Success"}


def _parse_notify_body(body_str: str) -> dict:
    """解析虚拟支付回调 body，兼容两种格式：
    A. {"MiniGame":{"Payload":"...","PayEventSig":"..."}}  → auth_mode="pay_event_sig"
    B. {"Event":"xpay_goods_deliver_notify","OutTradeNo":"...","OpenId":"..."} → auth_mode="message_signature"
    """
    try:
        data = json.loads(body_str)
    except (json.JSONDecodeError, TypeError):
        return {}

    if not isinstance(data, dict):
        return {}

    # 格式 A：MiniGame 嵌套
    mini = data.get("MiniGame", {})
    if isinstance(mini, dict) and mini.get("Payload"):
        return {
            "payload_str": mini["Payload"],
            "pay_event_sig": (mini.get("PayEventSig") or "").strip(),
            "auth_mode": "pay_event_sig",
        }

    # 格式 B：扁平 JSON event（发货/退款/取消/失败均支持）
    event = data.get("Event", "") or ""
    _supported = (
        "xpay_goods_deliver_notify", "xpay_goods_refund_notify",
        "xpay_goods_cancel_notify", "xpay_goods_deliver_fail_notify",
    )
    if event in _supported:
        payload_str = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
        return {
            "payload_str": payload_str,
            "pay_event_sig": "",
            "auth_mode": "message_signature",
        }

    return {}


def _parse_payload_fields(payload_str: str) -> dict:
    """从 Payload JSON 提取字段，兼容新旧格式。
    返回 dict 含 is_refund，缺失 order_no 返回空 dict。"""
    try:
        p = json.loads(payload_str)
    except (json.JSONDecodeError, TypeError):
        return {}

    # ── 判断退款 / 取消 / 关闭 ──
    event_val = p.get("Event", "") or p.get("EventType", "") or p.get("eventType", "") or ""
    event_upper = event_val.upper()
    is_refund = event_upper in ("REFUND", "CHARGE_BACK", "XPAY_GOODS_REFUND_NOTIFY")
    is_cancel = event_upper in (
        "XPAY_GOODS_CANCEL_NOTIFY", "XPAY_GOODS_DELIVER_FAIL_NOTIFY",
        "CANCEL", "CLOSE", "FAIL",
    )

    # ── order_no ──
    order_no = (p.get("OutTradeNo") or p.get("outTradeNo") or p.get("out_trade_no") or "").strip()

    # ── openid ──
    openid = (p.get("OpenId") or p.get("openId") or p.get("openid") or p.get("FromUserName") or "").strip()

    # ── product_id ──
    goods_info = p.get("GoodsInfo", {}) or {}
    if not isinstance(goods_info, dict):
        goods_info = {}
    product_id = (goods_info.get("ProductId") or goods_info.get("productId") or
                  p.get("ProductId") or p.get("productId") or p.get("product_id") or
                  p.get("GoodsId") or p.get("goodsId") or "").strip()

    # ── actual_price ──
    raw_price = None
    if goods_info.get("ActualPrice") is not None:
        raw_price = goods_info["ActualPrice"]
    elif goods_info.get("actualPrice") is not None:
        raw_price = goods_info["actualPrice"]
    elif p.get("ActualPrice") is not None:
        raw_price = p["ActualPrice"]
    elif p.get("actualPrice") is not None:
        raw_price = p["actualPrice"]
    elif p.get("GoodsPrice") is not None:
        raw_price = p["goodsPrice"]
    elif p.get("goodsPrice") is not None:
        raw_price = p["goodsPrice"]
    elif p.get("Price") is not None:
        raw_price = p["Price"]
    elif p.get("price") is not None:
        raw_price = p["price"]
    elif p.get("Amount") is not None:
        raw_price = p["Amount"]
    elif p.get("amount") is not None:
        raw_price = p["amount"]

    actual_price = 0
    if raw_price is not None:
        try:
            actual_price = int(raw_price)
        except (ValueError, TypeError):
            actual_price = 0

    if not order_no or not openid:
        return {}

    return {
        "order_no": order_no,
        "openid": openid,
        "product_id": product_id,
        "actual_price": actual_price,
        "is_refund": is_refund,
        "is_cancel": is_cancel,
        "event": event_val,
    }


@router.get("/notify")
def virtual_notify_verify(
    signature: str = Query(""),
    timestamp: str = Query(""),
    nonce: str = Query(""),
    echostr: str = Query(""),
    db: Session = Depends(get_db),
):
    """微信服务器 URL 有效性验证（Token 校验）。
    微信虚拟支付后台在配置回调URL时会发起GET请求验证。"""
    if not signature or not timestamp or not nonce or not echostr:
        raise HTTPException(status_code=400, detail="missing params")

    row = db.query(SystemConfig).filter(SystemConfig.key == "wx_virtual_notify_token").first()
    token = (row.value or "").strip() if row and row.value else ""
    if not token:
        raise HTTPException(status_code=503, detail="token not configured")

    sorted_arr = sorted([token, timestamp, nonce])
    expected_sig = hashlib.sha1("".join(sorted_arr).encode("utf-8")).hexdigest()

    if not hmac.compare_digest(expected_sig, signature):
        raise HTTPException(status_code=403, detail="signature invalid")

    return PlainTextResponse(echostr)


@router.post("/notify")
async def virtual_notify(request: Request, db: Session = Depends(get_db)):
    """虚拟支付发货回调通知。兼容两种格式：
    A. MiniGame.Payload + PayEventSig 验签（旧格式）
    B. 扁平 JSON Event + URL query signature 验签（新格式）
    安全校验：pay_channel + openid + order_no，productId/amount 存在则必须匹配。"""
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8", errors="replace")

    parsed = _parse_notify_body(body_str)
    if not parsed:
        print(f"[VPAY-NOTIFY] 回调 body 无法解析: {body_str[:200]}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "body parse failed"})

    payload_str = parsed["payload_str"]
    pay_event_sig = parsed.get("pay_event_sig", "").strip()
    auth_mode = parsed.get("auth_mode", "pay_event_sig")

    cfg = get_core_config(db)

    # ═══ 验签：按 auth_mode 选择策略 ═══
    if auth_mode == "message_signature":
        # B 格式：微信消息推送签名校验
        qp = request.query_params
        r_sig = qp.get("signature", "").strip()
        r_ts = qp.get("timestamp", "").strip()
        r_nonce = qp.get("nonce", "").strip()
        if not r_sig or not r_ts or not r_nonce:
            print(f"[VPAY-NOTIFY] 消息签名参数缺失 sig={bool(r_sig)} ts={bool(r_ts)} nonce={bool(r_nonce)}", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "signature missing"})

        row = db.query(SystemConfig).filter(SystemConfig.key == "wx_virtual_notify_token").first()
        msg_token = (row.value or "").strip() if row and row.value else ""
        if not msg_token:
            print(f"[VPAY-NOTIFY] 消息签名 token 未配置", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "token not configured"})

        expected = hashlib.sha1("".join(sorted([msg_token, r_ts, r_nonce])).encode("utf-8")).hexdigest()
        if not hmac.compare_digest(expected, r_sig):
            print(f"[VPAY-NOTIFY] 消息签名校验失败", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "signature invalid"})

    else:
        # A 格式：PayEventSig 验签
        app_key = (cfg.get("wx_virtual_app_key") or "").strip()
        if not app_key:
            print(f"[VPAY-NOTIFY] app_key 未配置，拒绝回调", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "app key missing"})
        if not pay_event_sig:
            print(f"[VPAY-NOTIFY] PayEventSig 为空，拒绝回调", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "signature missing"})
        expected = hmac.new(app_key.encode("utf-8"), payload_str.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(pay_event_sig, expected):
            print(f"[VPAY-NOTIFY] PayEventSig 验签失败", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "signature verification failed"})

    # ═══ 解析字段 ═══
    fields = _parse_payload_fields(payload_str)
    if not fields:
        print(f"[VPAY-NOTIFY] Payload 字段缺失 (order_no/openid): keys={list(json.loads(payload_str).keys())[:10]}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "payload fields invalid"})

    order_no = fields["order_no"]
    openid = fields["openid"]
    product_id = fields.get("product_id", "")
    actual_price = fields.get("actual_price", 0)

    print(f"[VPAY-NOTIFY] order={order_no} openid={openid[:8]}*** product={product_id or '(无)'} price={actual_price or '(无)'} mode={auth_mode}", flush=True)

    # ═══ 查订单 ═══
    order = db.query(PaymentOrder).filter(PaymentOrder.out_trade_no == order_no).first()
    if not order:
        print(f"[VPAY-NOTIFY] 订单不存在: {order_no}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "order not found"})

    if order.pay_channel != "WECHAT_VIRTUAL":
        print(f"[VPAY-NOTIFY] pay_channel 不匹配: {order.pay_channel}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "invalid pay channel"})

    # ═══ openid 校验 ═══
    db_user = db.query(User).filter(User.id == order.user_id).first()
    if not db_user:
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "user not found"})
    user_openid = db_user.wx_mini_openid or ""
    if openid != user_openid:
        print(f"[VPAY-NOTIFY] openid 不匹配: callback={openid[:8]}*** user={user_openid[:8]}***", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "openid mismatch"})

    # ═══ ★ 退款 / 取消 优先处理（不受 PAID 幂等拦截）═══
    # P1-A: 通过 _handle_refund_cancel_notify 统一处理（可独立测试）。
    is_refund = fields.get("is_refund", False)
    is_cancel = fields.get("is_cancel", False)
    if is_refund or is_cancel:
        result = _handle_refund_cancel_notify(db, order, db_user, is_refund, is_cancel, order_no)
        return JSONResponse(status_code=200, content=result)

    # ═══ 支付到账幂等 ═══
    if order.status == "PAID":
        return JSONResponse(status_code=200, content={"ErrCode": 0, "ErrMsg": "Success"})

    # ═══ productId 校验（存在则必须匹配）═══
    if product_id:
        expected_product_id = _get_virtual_product_id(db, order.sku_id)
        if expected_product_id and product_id != expected_product_id:
            print(f"[VPAY-NOTIFY] productId 不匹配: callback={product_id} expected={expected_product_id}", flush=True)
            return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "product id mismatch"})

    # ═══ 金额校验（存在则必须匹配）═══
    if actual_price > 0 and actual_price != order.amount_fen:
        print(f"[VPAY-NOTIFY] 金额不匹配: callback={actual_price} order={order.amount_fen}", flush=True)
        return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "amount mismatch"})

    # ═══ 支付到账，发放权益 ═══
    if _grant_order(db, order, order.user_id):
        return JSONResponse(status_code=200, content={"ErrCode": 0, "ErrMsg": "Success"})
    return JSONResponse(status_code=200, content={"ErrCode": 1, "ErrMsg": "grant failed"})


# ═══════════════════════════════════════════════════════════
# 服务端补偿查询：调用微信虚拟支付查单接口确认支付状态
# ═══════════════════════════════════════════════════════════

def _get_wx_access_token(db: Session) -> str:
    """获取微信小程序 access_token（带缓存）"""
    mini_appid = ""
    mini_secret = ""
    for k in ["wx_mini_appid", "wx_mini_secret"]:
        row = db.query(SystemConfig).filter(SystemConfig.key == k).first()
        if k == "wx_mini_appid" and row and row.value:
            mini_appid = row.value.strip()
        if k == "wx_mini_secret" and row and row.value:
            mini_secret = row.value.strip()
    if not mini_appid or not mini_secret:
        return ""
    try:
        from services.wechat_http import wechat_get_sync
        r = wechat_get_sync(
            "https://api.weixin.qq.com/cgi-bin/token"
            f"?grant_type=client_credential&appid={mini_appid}&secret={mini_secret}"
        )
        data = r.json()
        return data.get("access_token", "")
    except Exception:
        return ""


def _wx_query_virtual_order(db: Session, order) -> str:
    """调用微信虚拟支付查单接口，返回 'PAID' | 'NOT_PAID' | 'ERROR'"""
    cfg = get_core_config(db)
    offer_id = (cfg.get("wx_virtual_offer_id") or "").strip()
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    if not offer_id or not app_key:
        return "ERROR"

    db_user = db.query(User).filter(User.id == order.user_id).first()
    openid = db_user.wx_mini_openid if db_user else ""

    access_token = _get_wx_access_token(db)
    if not access_token:
        return "ERROR"

    cfg2 = get_core_config(db)
    env_val = _get_virtual_env(cfg2)
    endpoint = "/xpay/query_order"
    payload = {
        "openid": openid,
        "order_id": order.out_trade_no,
        "env": env_val,
    }
    body_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    pay_sig = _xpay_sig(endpoint, body_str, app_key)
    url = f"https://api.weixin.qq.com{endpoint}?access_token={access_token}&pay_sig={pay_sig}"
    try:
        from services.wechat_http import wechat_post_sync
        r = wechat_post_sync(url, content=body_str.encode("utf-8"), headers={"Content-Type": "application/json"})
        result = r.json()
        _qs = f"ec={result.get('errcode')} msg={(result.get('errmsg') or '')[:40]}"
        print(f"[VPAY-QUERY] endpoint={endpoint} env={env_val} order={order.out_trade_no} http={r.status_code} {_qs}", flush=True)
        if result.get("errcode") == 0:
            pay_info = result.get("pay_info", {}) or {}
            status = str(pay_info.get("trade_state", "") or result.get("trade_state", ""))
            if status.upper() in ("SUCCESS", "PAID", "1", "2"):
                return "PAID"
            if status.upper() in ("CREATED", "NOTPAY", "0"):
                return "NOT_PAID"
        if result.get("ret") == 0:
            trade_state = str(result.get("trade_state", ""))
            if trade_state.upper() in ("SUCCESS", "PAID", "1", "2"):
                return "PAID"
    except Exception as e:
        print(f"[VPAY-QUERY] 异常 order={order.out_trade_no}: {e}", flush=True)
    return "ERROR"


@router.post("/reconcile/{order_no}")
def reconcile_order(
    order_no: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """服务端主动查询微信确认支付状态，安全补发权益。
    只允许查询自己的订单，仅 CREATED + WECHAT_VIRTUAL 可触发同步。"""
    user_id = int(user["user_id"])
    order = db.query(PaymentOrder).filter(
        PaymentOrder.out_trade_no == order_no,
        PaymentOrder.user_id == user_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    # 幂等：已支付直接返回
    if order.status == "PAID":
        return {"ok": True, "status": "PAID", "credits": order.credits, "membership_days": order.membership_days}

    # 只允许虚拟支付 + CREATED/PROCESSING
    if order.pay_channel != "WECHAT_VIRTUAL":
        raise HTTPException(status_code=400, detail="非虚拟支付订单")
    if order.status not in ("CREATED", "PROCESSING"):
        raise HTTPException(status_code=400, detail=f"订单状态 {order.status} 不可同步")

    # 调用微信查单
    confirm = _wx_query_virtual_order(db, order)
    if confirm == "PAID":
        ok = _grant_order(db, order, user_id)
        return {"ok": True, "status": "PAID" if ok else order.status,
                "credits": order.credits, "membership_days": order.membership_days,
                "synced": ok}
    elif confirm == "NOT_PAID":
        return {"ok": True, "status": "CREATED", "message": "微信未确认支付"}
    else:
        return {"ok": True, "status": "CREATED", "message": "查单失败请稍后重试"}


@router.post("/admin/reconcile/{order_no}")
def admin_reconcile_order(
    order_no: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理后台手动同步虚拟支付订单"""
    order = db.query(PaymentOrder).filter(PaymentOrder.out_trade_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.status == "PAID":
        return {"ok": True, "status": "PAID", "message": "已完成"}
    if order.pay_channel != "WECHAT_VIRTUAL":
        raise HTTPException(status_code=400, detail="非虚拟支付订单")

    confirm = _wx_query_virtual_order(db, order)
    if confirm == "PAID":
        ok = _grant_order(db, order, order.user_id)
        return {"ok": True, "status": "PAID" if ok else order.status, "credits": order.credits, "synced": ok}
    elif confirm == "NOT_PAID":
        return {"ok": True, "status": "CREATED", "message": "微信未确认支付"}
    else:
        return {"ok": True, "status": "CREATED", "message": "查单失败"}


# ═══════════════════════════════════════════════════════════
# 退款闭环：用户申请 + 管理后台审核 + notify 同步
# ═══════════════════════════════════════════════════════════

class AdminRefundBody(BaseModel):
    force: bool = False


def _extract_left_fee(query_result):
    """从 query_order 返回计算真实可退金额：order_fee - refunded_fee"""
    order = query_result.get("order") or {}
    order_fee = 0
    for k in ("order_fee", "OrderFee"):
        v = order.get(k)
        if v is not None:
            try:
                order_fee = int(v)
                break
            except (ValueError, TypeError):
                pass
    if order_fee <= 0:
        # fallback to explicit left_fee
        for src in (order, query_result):
            for k in ("left_fee", "LeftFee"):
                v = src.get(k)
                if v is not None:
                    try:
                        return int(v)
                    except (ValueError, TypeError):
                        pass
        # query_result is missing reliable fields: unknown, not zero
        return None
    # sum of already-refunded amounts
    refunded = 0
    for k in ("refund_fee", "refunded_fee", "total_refund_fee", "RefundFee", "RefundedFee"):
        v = order.get(k)
        if v is not None:
            try:
                refunded = max(refunded, int(v))
            except (ValueError, TypeError):
                pass
    return max(order_fee - refunded, 0)


def _is_wechat_order_refunded_or_closed(query_result):
    """判断微信侧是否已退款/已关闭"""
    order = query_result.get("order") or {}
    order_fee = int(order.get("order_fee") or order.get("OrderFee") or 0)
    refunded = 0
    for k in ("refund_fee", "refunded_fee", "total_refund_fee", "RefundFee", "RefundedFee"):
        v = order.get(k)
        if v is not None:
            try:
                refunded = max(refunded, int(v))
            except (ValueError, TypeError):
                pass
    if order_fee > 0 and refunded >= order_fee:
        return True
    status = order.get("status")
    if status is not None and str(status) in ("5", "6", "8", "9"):
        # status 5/6/8/9: refunded/closed by WeChat
        return True
    return False


def _xpay_sig(endpoint, body_str, app_key):
    """XPay 签名: HMAC-SHA256(app_key, endpoint + "&" + body_str)"""
    return hmac.new(app_key.encode("utf-8"), f"{endpoint}&{body_str}".encode("utf-8"), hashlib.sha256).hexdigest()


def _rid_query(access_token, rid):
    """查询微信 rid 详细信息，返回安全摘要（不含 request_body/response_body 原文）。"""
    try:
        from services.wechat_http import wechat_post_sync
        r = wechat_post_sync(
            f"https://api.weixin.qq.com/cgi-bin/openapi/rid/get?access_token={access_token}",
            json_data={"rid": rid},
        )
        data = r.json()
        req_path = ""
        req_url = str(data.get("request_url", "") or "")
        if req_url:
            try:
                from urllib.parse import urlparse
                req_path = urlparse(req_url).path or req_url[:80]
            except Exception:
                req_path = req_url[:80]
        req_keys = list((data.get("request_body") or {}).keys()) if isinstance(data.get("request_body"), dict) else []
        resp_keys = list((data.get("response_body") or {}).keys()) if isinstance(data.get("response_body"), dict) else []
        summary = f"path={req_path} req_keys={req_keys[:5]} resp_keys={resp_keys[:5]}"
        print(f"[VPAY-RID] rid={rid} {summary}", flush=True)
        return f"rid_diag:{summary}"
    except Exception as e:
        print(f"[VPAY-RID] 查询失败 rid={rid}: {type(e).__name__}", flush=True)
        return f"rid_query_failed:{type(e).__name__}"


def _wx_query_order_status(db, order, app_key, offer_id, openid, access_token):
    """查询虚拟支付订单状态，返回 dict 含 left_fee / trade_state 等"""
    cfg = get_core_config(db)
    env_val = _get_virtual_env(cfg)
    endpoint = "/xpay/query_order"
    payload = {
        "openid": openid,
        "order_id": order.out_trade_no,
        "env": env_val,
    }
    body_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    pay_sig = _xpay_sig(endpoint, body_str, app_key)
    url = f"https://api.weixin.qq.com{endpoint}?access_token={access_token}&pay_sig={pay_sig}"
    try:
        from services.wechat_http import wechat_post_sync
        r = wechat_post_sync(url, content=body_str.encode("utf-8"), headers={"Content-Type": "application/json"})
        result = r.json()
        _qs = f"ec={result.get('errcode')} msg={(result.get('errmsg') or '')[:40]}"
        print(f"[VPAY-QUERY] endpoint={endpoint} env={env_val} order={order.out_trade_no} http={r.status_code} {_qs}", flush=True)
        return result
    except Exception as e:
        print(f"[VPAY-QUERY] 异常 order={order.out_trade_no}: {e}", flush=True)
        return {}


def _wx_refund_virtual_order(db: Session, order) -> tuple:
    """调用微信官方虚拟支付退款接口 POST /xpay/refund_order"""
    cfg = get_core_config(db)
    offer_id = (cfg.get("wx_virtual_offer_id") or "").strip()
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    env_val = _get_virtual_env(cfg)
    if not offer_id or not app_key:
        return False, "虚拟支付配置缺失"

    db_user = db.query(User).filter(User.id == order.user_id).first()
    if not db_user or not db_user.wx_mini_openid:
        return False, "用户 openid 缺失"
    openid = db_user.wx_mini_openid

    # 获取 access_token
    import httpx
    mini_appid = ""
    mini_secret = ""
    for k in ["wx_mini_appid", "wx_mini_secret"]:
        row = db.query(SystemConfig).filter(SystemConfig.key == k).first()
        if k == "wx_mini_appid" and row and row.value:
            mini_appid = row.value.strip()
        if k == "wx_mini_secret" and row and row.value:
            mini_secret = row.value.strip()
    if not mini_appid or not mini_secret:
        return False, "小程序凭证未配置"

    try:
        from services.wechat_http import wechat_get_sync
        tr = wechat_get_sync(
            f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={mini_appid}&secret={mini_secret}"
        )
        access_token = tr.json().get("access_token", "")
    except Exception:
        return False, "获取 access_token 失败"
    if not access_token:
        return False, "获取 access_token 失败"

    amount_fen = order.amount_fen or 0
    # 先用 query_order 获取 left_fee
    query_result = _wx_query_order_status(db, order, app_key, offer_id, openid, access_token)
    left_fee = _extract_left_fee(query_result)

    if _is_wechat_order_refunded_or_closed(query_result):
        od = query_result.get("order") or {}
        diag = f"order_fee={od.get('order_fee')} left_fee={left_fee} status={od.get('status')}"
        print(f"[VPAY-REFUND] WeChat already refunded order={order.out_trade_no} {diag}", flush=True)
        return "ALREADY_REFUNDED", diag
    if left_fee is None:
        return False, "微信查单失败，无法确认可退金额，请稍后重试"
    if left_fee <= 0:
        return "ALREADY_REFUNDED", f"left_fee={left_fee}"

    refund_fee = min(amount_fen, left_fee)
    if refund_fee <= 0:
        return False, f"退款金额无效 amount_fen={amount_fen} left_fee={left_fee}"

    refund_order_id = f"RF{order.out_trade_no}"[:32]
    endpoint = "/xpay/refund_order"
    payload = {
        "openid": openid,
        "order_id": order.out_trade_no,
        "refund_order_id": refund_order_id,
        "left_fee": left_fee,
        "refund_fee": refund_fee,
        "refund_reason": "3",
        "req_from": "1",
        "env": env_val,
    }
    body_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    pay_sig = _xpay_sig(endpoint, body_str, app_key)
    url = f"https://api.weixin.qq.com{endpoint}?access_token={access_token}&pay_sig={pay_sig}"
    safe_info = f"openid={openid[:8]}*** order_id={order.out_trade_no} refund_fee={refund_fee} left_fee={left_fee} env={env_val} body_keys={list(payload.keys())}"
    print(f"[VPAY-REFUND] endpoint={endpoint} env={env_val} order={order.out_trade_no} {safe_info}", flush=True)

    try:
        from services.wechat_http import wechat_post_sync
        r = wechat_post_sync(url, content=body_str.encode("utf-8"), headers={"Content-Type": "application/json"})
        status = r.status_code
        result = r.json()
        _rs = f"ec={result.get('errcode')} msg={(result.get('errmsg') or '')[:60]}"
        print(f"[VPAY-REFUND] http={status} order={order.out_trade_no} {_rs}", flush=True)

        errcode = result.get("errcode", -1)
        errmsg = (result.get("errmsg") or result.get("msg") or "").strip()
        if errcode == 0:
            return True, "退款已提交"

        # rid 诊断
        rid = ""
        if not errmsg:
            errmsg = f"退款失败 errcode={errcode}"
        import re
        rid_match = re.search(r'rid[:\s]*([a-f0-9\-]+)', errmsg, re.I)
        if rid_match:
            rid = rid_match.group(1)
        if rid:
            rid_info = _rid_query(access_token, rid)
            errmsg = f"{errmsg[:200]} | rid_diag:{rid_info[:200]}"
        return False, errmsg[:400]
    except Exception as e:
        print(f"[VPAY-REFUND] 异常 order={order.out_trade_no}: {e}", flush=True)
        return False, f"退款请求异常: {str(e)[:200]}"


def _try_sync_refund_after_submit(db, order, db_user, attempts=5, interval=1):
    """Poll WeChat query_order after refund submission, auto-deduct on confirmed refund."""
    cfg = get_core_config(db)
    offer_id = (cfg.get("wx_virtual_offer_id") or "").strip()
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    openid = db_user.wx_mini_openid or ""
    if not offer_id or not app_key or not openid:
        return False
    access_token = _get_wx_access_token(db)
    if not access_token:
        return False
    for i in range(attempts):
        time.sleep(interval)
        query_result = _wx_query_order_status(db, order, app_key, offer_id, openid, access_token)
        if _is_wechat_order_refunded_or_closed(query_result):
            _revoke_order(db, order, db_user)
            return True
        lf = _extract_left_fee(query_result)
        if lf is not None and lf <= 0:
            _revoke_order(db, order, db_user)
            return True
        # lf is None: continue polling
    return False


@router.post("/refund-request/{order_no}")
def refund_request(
    order_no: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """User refund request: balance check -> WeChat refund -> poll -> deduct -> REFUNDED"""
    user_id = int(user["user_id"])
    order = db.query(PaymentOrder).filter(
        PaymentOrder.out_trade_no == order_no,
        PaymentOrder.user_id == user_id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.pay_channel != "WECHAT_VIRTUAL":
        raise HTTPException(status_code=400, detail="仅支持虚拟支付订单")
    if order.status not in ("PAID", "REFUND_REQUESTED"):
        raise HTTPException(status_code=400, detail=f"订单状态 {order.status} 不可申请退款")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if db_user.balance_credits < (order.credits or 0):
        raise HTTPException(status_code=400, detail="点数已使用，当前余额不足，无法退款，请联系客服处理")

    prev_status = order.status
    order.status = "REFUNDING"
    db.commit()

    success, msg = _wx_refund_virtual_order(db, order)
    if success == "ALREADY_REFUNDED":
        _revoke_order(db, order, db_user)
        return {"ok": True, "status": "REFUNDED", "message": "退款成功，点数已扣回"}
    if not success:
        order.status = prev_status
        db.commit()
        raise HTTPException(status_code=502, detail=msg)

    if _try_sync_refund_after_submit(db, order, db_user):
        return {"ok": True, "status": "REFUNDED", "message": "退款成功，点数已扣回"}
    return {"ok": True, "status": "REFUNDING", "message": "退款已提交，等待系统同步"}


@router.post("/admin/refund/{order_no}")
def admin_refund(
    order_no: str,
    body: AdminRefundBody,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """Admin refund: balance check -> WeChat refund -> poll -> deduct -> REFUNDED"""
    order = db.query(PaymentOrder).filter(PaymentOrder.out_trade_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.pay_channel != "WECHAT_VIRTUAL":
        raise HTTPException(status_code=400, detail="仅支持虚拟支付订单")
    if order.status not in ("PAID", "REFUND_REQUESTED"):
        raise HTTPException(status_code=400, detail=f"订单状态 {order.status} 不可退款")

    db_user = db.query(User).filter(User.id == order.user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if db_user.balance_credits < (order.credits or 0):
        raise HTTPException(status_code=400, detail="点数已使用，当前余额不足，无法退款，请联系客服处理")

    prev_status = order.status
    order.status = "REFUNDING"
    db.commit()

    success, msg = _wx_refund_virtual_order(db, order)
    if success == "ALREADY_REFUNDED":
        _revoke_order(db, order, db_user)
        return {"ok": True, "status": "REFUNDED", "message": "微信侧已退款，本地已同步"}
    if not success:
        order.status = prev_status
        db.commit()
        raise HTTPException(status_code=502, detail=msg)

    if _try_sync_refund_after_submit(db, order, db_user):
        return {"ok": True, "status": "REFUNDED", "message": "退款成功，点数已扣回"}
    print(f"[VPAY] admin退款已提交 order={order_no}", flush=True)
    return {"ok": True, "status": "REFUNDING"}


@router.post("/admin/refund-sync/{order_no}")
def admin_refund_sync(
    order_no: str,
    admin: dict = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """管理后台同步退款状态：查询微信侧确认退款后，本地扣点改 REFUNDED"""
    order = db.query(PaymentOrder).filter(PaymentOrder.out_trade_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    if order.pay_channel != "WECHAT_VIRTUAL":
        raise HTTPException(status_code=400, detail="仅支持虚拟支付订单")
    if order.status not in ("REFUNDING", "REFUND_REQUESTED", "PAID", "REFUNDED"):
        raise HTTPException(status_code=400, detail=f"订单状态 {order.status} 不可同步")

    cfg = get_core_config(db)
    offer_id = (cfg.get("wx_virtual_offer_id") or "").strip()
    app_key = (cfg.get("wx_virtual_app_key") or "").strip()
    if not offer_id or not app_key:
        raise HTTPException(status_code=503, detail="虚拟支付配置缺失")

    db_user = db.query(User).filter(User.id == order.user_id).first()
    if not db_user or not db_user.wx_mini_openid:
        raise HTTPException(status_code=404, detail="用户 openid 缺失")

    openid = db_user.wx_mini_openid
    mini_appid = _get_sys_config_str(db, "wx_mini_appid", "")
    mini_secret = _get_sys_config_str(db, "wx_mini_secret", "")
    if not mini_appid or not mini_secret:
        raise HTTPException(status_code=503, detail="小程序凭证未配置")

    try:
        from services.wechat_http import wechat_get_sync
        tr = wechat_get_sync(
            f"https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={mini_appid}&secret={mini_secret}"
        )
        access_token = tr.json().get("access_token", "")
    except Exception:
        raise HTTPException(status_code=502, detail="获取 access_token 失败")
    if not access_token:
        raise HTTPException(status_code=502, detail="获取 access_token 失败")

    query_result = _wx_query_order_status(db, order, app_key, offer_id, openid, access_token)
    if _is_wechat_order_refunded_or_closed(query_result):
        _revoke_order(db, order, db_user)
        print(f"[VPAY] refund-sync REFUNDED order={order_no}", flush=True)
        return {"ok": True, "status": "REFUNDED", "message": "微信侧已退款，本地已同步"}
    lf = _extract_left_fee(query_result)
    if lf is None:
        return {"ok": True, "status": order.status, "message": "微信查单字段缺失，无法确认退款状态，请稍后重试"}
    if lf <= 0:
        _revoke_order(db, order, db_user)
        print(f"[VPAY] refund-sync REFUNDED order={order_no}", flush=True)
        return {"ok": True, "status": "REFUNDED", "message": "微信侧已退款，本地已同步"}

    od = query_result.get("order") or {}
    return {"ok": True, "status": order.status, "message": f"微信侧未退款 order_fee={od.get('order_fee')} left_fee={lf}"}
