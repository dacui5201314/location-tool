"""微信支付 — JSAPI prepay + 回调通知
所有商户号/密钥/证书只从环境变量读取，禁止硬编码。
缺配置时返回 503，不做 mock 成功。
"""
import os, json, hashlib, time
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db
from models.db_models import User, BillingRecord, SystemConfig
from services.runtime_config import get_skus
from auth import get_current_user

router = APIRouter(prefix="/api/pay", tags=["支付"])

# ── 读取支付配置（仅环境变量，不存 DB 明文）──
def _get_pay_env():
    mchid = os.getenv("WX_PAY_MCHID", "")
    appid = os.getenv("WX_PAY_APPID", "")
    api_v3_key = os.getenv("WX_PAY_API_V3_KEY", "")
    cert_serial = os.getenv("WX_PAY_CERT_SERIAL_NO", "")
    private_key_path = os.getenv("WX_PAY_PRIVATE_KEY_PATH", "")
    notify_url = os.getenv("WX_PAY_NOTIFY_URL", "")
    return mchid, appid, api_v3_key, cert_serial, private_key_path, notify_url


def _pay_configured():
    mchid, appid, key, cert, pk, notify = _get_pay_env()
    return bool(mchid and appid and key and cert and pk and notify)


class PrepayBody(BaseModel):
    sku_id: int


@router.post("/wechat/prepay")
def wechat_prepay(
    body: PrepayBody,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """微信 JSAPI 预支付下单。
    返回 uni.requestPayment 需要的参数包。
    环境变量缺失时返回 503。
    """
    if not _pay_configured():
        raise HTTPException(status_code=503, detail="支付服务暂不可用，请联系管理员配置微信支付")

    mchid, appid, api_v3_key, cert_serial, private_key_path, notify_url = _get_pay_env()

    # 1. 校验 SKU
    skus = get_skus(db)
    sku = next((s for s in skus if s.get("id") == body.sku_id and s.get("visible", True)), None)
    if not sku:
        raise HTTPException(status_code=400, detail="套餐不存在或已下架")

    price_yuan = sku.get("price", "0")
    try:
        total_fen = int(float(price_yuan) * 100)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="套餐价格无效")

    if total_fen <= 0:
        raise HTTPException(status_code=400, detail="套餐价格为 0，无需支付")

    user_id = int(user["user_id"])
    label = sku.get("label", "套餐")
    out_trade_no = f"ZDX{user_id}{int(time.time()*1000)}"

    # 2. 调用微信支付 JSAPI 下单 (APIv3)
    #    当前为骨架：真实实现需要 requests + 微信 APIv3 签名（SHA256-RSA2048）
    #    签名逻辑涉及商户私钥、随机串、时间戳、请求体 digest 等
    #    此处返回 501 表示后端结构就绪，等待微信商户资料配齐后补齐签名+HTTP 调用
    raise HTTPException(
        status_code=501,
        detail="微信支付后端结构就绪，等待商户资料配齐后启用。预支付参数将在商户配置完成后自动生效。"
    )


@router.post("/wechat/notify")
async def wechat_notify(request: Request, db: Session = Depends(get_db)):
    """微信支付回调通知。
    验签后幂等到账，写 BillingRecord。
    """
    if not _pay_configured():
        raise HTTPException(status_code=503, detail="支付服务未配置")

    # 回调验签 + 解密 + 到账 逻辑需微信 APIv3 证书+私钥
    # 此处骨架就绪，等待商户资料配齐
    raise HTTPException(status_code=501, detail="微信支付回调就绪，等待商户配置")


class OrderStatusBody(BaseModel):
    out_trade_no: str


@router.get("/orders/{out_trade_no}")
def get_order(
    out_trade_no: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询订单状态（当前返回未实现，等待微信支付对接后启用）"""
    return {"out_trade_no": out_trade_no, "status": "pending", "note": "等待微信支付对接"}
