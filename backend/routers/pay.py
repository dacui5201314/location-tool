"""微信支付 — JSAPI v3 prepay + notify + order query
DB 优先（管理后台 SystemConfig），环境变量 fallback。
私钥/平台证书路径仅从环境变量读取。
API_V3_KEY 必须是 32 字节（AES-256-GCM 要求）。
"""
import os, json, time, base64, secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.db_models import User, BillingRecord, PaymentOrder
from services.runtime_config import get_user_skus, get_core_config
from auth import get_current_user

try:
    import cryptography  # noqa: F401
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _CRYPTO_OK = True
except ImportError:
    _CRYPTO_OK = False

router = APIRouter(prefix="/api/pay", tags=["支付"])


# ── 安全随机 nonce ──
def _rand_nonce():
    return secrets.token_urlsafe(12)[:16]


# ── 支付配置：DB 优先，env fallback ──
def _pay_config(db=None):
    cfg = get_core_config(db) if db else {}
    env = os.getenv
    return (
        cfg.get("wx_mch_id") or env("WX_PAY_MCHID", ""),
        cfg.get("wx_app_id") or env("WX_PAY_APPID", ""),
        cfg.get("wx_api_key") or env("WX_PAY_API_V3_KEY", ""),
        cfg.get("wx_cert_sn") or env("WX_PAY_CERT_SERIAL_NO", ""),
        env("WX_PAY_PRIVATE_KEY_PATH", ""),
        cfg.get("wx_notify_url") or env("WX_PAY_NOTIFY_URL", ""),
        env("WX_PAY_PLATFORM_CERT_PATH", ""),
    )


def _prepay_configured(db=None):
    """prepay 只需要商户配置 + 私钥，不需要平台证书"""
    mchid, appid, key, cert, pk, notify, _ = _pay_config(db)
    return all([mchid, appid, key, cert, pk, notify]) and len(key) == 32


def _notify_configured(db=None):
    """notify 额外需要平台证书"""
    vals = _pay_config(db)
    return all(vals) and len(vals[2]) == 32


# ── APIv3 SHA256-RSA2048 签名 ──
def _sign(method, url_path, body_str, mchid, cert_serial, pk_path):
    if not _CRYPTO_OK:
        raise HTTPException(status_code=500, detail="cryptography 依赖未安装")
    ts = str(int(time.time()))
    nonce = _rand_nonce()
    sign_raw = f"{method}\n{url_path}\n{ts}\n{nonce}\n{body_str}\n"
    with open(pk_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)
    sig = priv.sign(sign_raw.encode(), padding.PKCS1v15(), hashes.SHA256())
    sig_b64 = base64.b64encode(sig).decode()
    token = f'WECHATPAY2-SHA256-RSA2048 mchid="{mchid}",nonce_str="{nonce}",timestamp="{ts}",serial_no="{cert_serial}",signature="{sig_b64}"'
    return token


# ── APIv3 HTTP ──
def _wx_post(url_path, body, mchid, appid, key, cert_serial, pk_path):
    import urllib.request, ssl
    body_str = json.dumps(body, ensure_ascii=False)
    token = _sign("POST", url_path, body_str, mchid, cert_serial, pk_path)
    url = f"https://api.mch.weixin.qq.com{url_path}"
    req = urllib.request.Request(url, data=body_str.encode(), headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": token,
        "User-Agent": "Zhidexuan/1.0",
    })
    ctx = ssl.create_default_context()
    resp = urllib.request.urlopen(req, context=ctx, timeout=15)
    return json.loads(resp.read().decode())


class PrepayBody(BaseModel):
    sku_id: int


@router.post("/wechat/prepay")
def wechat_prepay(
    body: PrepayBody,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """真实微信 JSAPI v3 预支付下单"""
    if not _prepay_configured(db):
        raise HTTPException(status_code=503, detail="支付服务暂不可用，请在管理后台完善微信支付商户配置（商户号/AppID/APIv3密钥32位/证书序列号/私钥路径/回调地址）")
    mchid, appid, api_v3_key, cert_serial, pk_path, notify_url, _ = _pay_config(db)

    user_id = int(user["user_id"])
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # openid 检查：JSAPI 支付必须有小程序 openid
    openid = db_user.wx_mini_openid or ""
    if not openid:
        raise HTTPException(
            status_code=400,
            detail="请先在微信中登录并授权后，再进行支付"
        )

    # SKU 校验（用户可见套餐）
    skus, _ = get_user_skus(user_id, db)
    sku = next((s for s in skus if s.get("id") == body.sku_id and s.get("visible", True)), None)
    if not sku:
        raise HTTPException(status_code=400, detail="套餐不存在或已下架")

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
    out_trade_no = f"ZDX{user_id}{int(time.time()*1000)}"

    # 创建本地订单
    order = PaymentOrder(
        out_trade_no=out_trade_no,
        user_id=user_id,
        sku_id=body.sku_id,
        sku_snapshot=json.dumps(sku, ensure_ascii=False),
        amount_fen=total_fen,
        credits=credits,
        membership_days=days,
        status="CREATED",
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # 调用微信 JSAPI 下单
    wx_body = {
        "appid": appid,
        "mchid": mchid,
        "description": label,
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "amount": {"total": total_fen, "currency": "CNY"},
        "payer": {"openid": openid},
    }
    try:
        wx_resp = _wx_post("/v3/pay/transactions/jsapi", wx_body, mchid, appid, api_v3_key, cert_serial, pk_path)
    except Exception as e:
        order.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=502, detail=f"微信支付接口异常: {str(e)[:120]}")

    prepay_id = wx_resp.get("prepay_id", "")
    if not prepay_id:
        order.status = "FAILED"
        db.commit()
        raise HTTPException(status_code=502, detail=f"微信支付下单失败: {json.dumps(wx_resp, ensure_ascii=False)[:200]}")

    # 生成小程序调起支付参数（安全随机 nonce）
    ts = str(int(time.time()))
    nonce = _rand_nonce()
    package = f"prepay_id={prepay_id}"
    sign_raw = f"{appid}\n{ts}\n{nonce}\n{package}\n"
    with open(pk_path, "rb") as f:
        priv = serialization.load_pem_private_key(f.read(), password=None)
    sig = priv.sign(sign_raw.encode(), padding.PKCS1v15(), hashes.SHA256())
    pay_sign = base64.b64encode(sig).decode()

    return {
        "timeStamp": ts,
        "nonceStr": nonce,
        "package": package,
        "signType": "RSA",
        "paySign": pay_sign,
        "out_trade_no": out_trade_no,
    }


@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: Session = Depends(get_db)):
    """微信支付回调 — 平台证书验签 + serial 校验 + AES-GCM 解密 + 安全校验 + 幂等到账"""
    if not _notify_configured(db):
        return JSONResponse(status_code=500, content={"code": "FAIL", "message": "notify not fully configured"})

    mchid, appid, api_v3_key, cert_serial, pk_path, notify_url, plat_cert_path = _pay_config(db)

    # 0. Wechatpay-Serial 校验
    wx_serial = request.headers.get("Wechatpay-Serial", "")
    if not wx_serial:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "missing Wechatpay-Serial header"})

    # 1. 使用微信平台证书验签
    ts = request.headers.get("Wechatpay-Timestamp", "")
    nonce = request.headers.get("Wechatpay-Nonce", "")
    sig_header = request.headers.get("Wechatpay-Signature", "")
    body_bytes = await request.body()
    body_str = body_bytes.decode()
    sign_raw = f"{ts}\n{nonce}\n{body_str}\n"

    try:
        if not plat_cert_path:
            raise FileNotFoundError("WX_PAY_PLATFORM_CERT_PATH not configured")
        with open(plat_cert_path, "rb") as f:
            cert_raw = f.read()
        # 微信平台证书是 x509 PEM
        try:
            from cryptography import x509 as x509_mod
            cert = x509_mod.load_pem_x509_certificate(cert_raw)
            plat_key = cert.public_key()
        except Exception:
            plat_key = serialization.load_pem_public_key(cert_raw)
        sig_bytes = base64.b64decode(sig_header)
        plat_key.verify(sig_bytes, sign_raw.encode(), padding.PKCS1v15(), hashes.SHA256())
    except Exception:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "signature verification failed"})

    # 1b. serial 一致性检查
    if wx_serial != cert_serial:
        print(f"[Pay Notify] serial mismatch: header={wx_serial[:20]}... config={cert_serial[:20]}...", flush=True)

    # 2. AES-GCM 解密
    try:
        notify_data = json.loads(body_str)
        resource = notify_data.get("resource", {})
        cipher = resource.get("ciphertext", "")
        r_nonce = resource.get("nonce", "")
        associated_data = resource.get("associated_data", "")
        aesgcm = AESGCM(api_v3_key.encode())
        decrypted = aesgcm.decrypt(r_nonce.encode(), base64.b64decode(cipher), associated_data.encode())
        trade_data = json.loads(decrypted)
    except Exception as e:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": f"decrypt failed: {str(e)[:100]}"})

    # 3. 安全校验
    out_trade_no = trade_data.get("out_trade_no", "")
    transaction_id = trade_data.get("transaction_id", "")
    if trade_data.get("mchid", "") != mchid:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "mchid mismatch"})
    if trade_data.get("appid", "") != appid:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "appid mismatch"})
    if trade_data.get("trade_state", "") != "SUCCESS":
        return JSONResponse(status_code=200, content={"code": "SUCCESS", "message": "not success state"})
    if not transaction_id:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "missing transaction_id"})

    # 4. 幂等到账
    order = db.query(PaymentOrder).filter(PaymentOrder.out_trade_no == out_trade_no).first()
    if not order:
        return JSONResponse(status_code=404, content={"code": "FAIL", "message": "order not found"})
    if order.status == "PAID":
        return JSONResponse(status_code=200, content={"code": "SUCCESS", "message": "already paid"})

    wx_amount = trade_data.get("amount", {}).get("total", 0)
    if wx_amount != order.amount_fen:
        return JSONResponse(status_code=400, content={"code": "FAIL", "message": "amount mismatch"})

    # 到账
    order.transaction_id = transaction_id
    order.status = "PAID"
    order.paid_at = datetime.now()

    db_user = db.query(User).filter(User.id == order.user_id).first()
    if not db_user:
        return JSONResponse(status_code=404, content={"code": "FAIL", "message": "user not found"})
    balance_before = db_user.balance_credits

    if order.credits > 0:
        db_user.balance_credits += order.credits
        db.add(BillingRecord(
            user_id=order.user_id, amount=order.credits,
            balance_after=db_user.balance_credits,
            record_type="PURCHASE", reason=f"微信支付充值 {order.credits}点 ({order.out_trade_no})",
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
            record_type="MEMBERSHIP", reason=f"微信支付开通会员 {order.membership_days}天 ({order.out_trade_no})",
        ))

    db.commit()
    print(f"[Pay] 到账成功 out_trade_no={out_trade_no} credits={order.credits} days={order.membership_days} balance:{balance_before}->{db_user.balance_credits}", flush=True)
    return {"code": "SUCCESS", "message": "OK"}


@router.get("/orders/{out_trade_no}")
def get_order(
    out_trade_no: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询订单状态"""
    order = db.query(PaymentOrder).filter(
        PaymentOrder.out_trade_no == out_trade_no,
        PaymentOrder.user_id == int(user["user_id"]),
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return order.to_dict()
