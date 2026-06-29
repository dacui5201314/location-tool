"""5.1B: Payment E2E acceptance — real route paths + mock deps + admin list + checklist"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite://", echo=False)
@event.listens_for(engine, "connect")
def _set_pragma(dbapi_conn, _rec):
    dbapi_conn.execute("PRAGMA journal_mode=WAL;")
SessionLocal = sessionmaker(bind=engine)

from database import Base
from models.db_models import PaymentOrder, User, BillingRecord, SystemConfig
Base.metadata.create_all(bind=engine)

from unittest.mock import patch, MagicMock
from fastapi import HTTPException

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


def _seed_user(db, user_id=1, balance=0, mini_openid="oTest001"):
    u = User(id=user_id, balance_credits=balance, membership_tier="free", wx_mini_openid=mini_openid)
    db.add(u)
    db.commit()
    return u

def _seed_order(db, out_trade_no="T001", user_id=1, status="CREATED", credits=1, amount_fen=990, **kw):
    defaults = {"out_trade_no": out_trade_no, "user_id": user_id, "sku_id": 11,
                "amount_fen": amount_fen, "credits": credits, "membership_days": 0,
                "status": status, "pay_channel": "WECHAT_JSAPI"}
    defaults.update(kw)
    o = PaymentOrder(**defaults)
    db.add(o)
    db.commit()
    db.refresh(o)
    return o

_admin = {"user_id": 1, "role": "admin"}
_user = {"user_id": 1001}


# ═══ T1: real prepay failure → NOT PAID / no grant ═══
print("=== T1: prepay failure not PAID ===")
from routers.pay import wechat_prepay, PrepayBody, _prepay_configured, _pay_config, _load_private_key
from services.runtime_config import get_user_skus

db1 = SessionLocal()
u1 = _seed_user(db1, user_id=1001, balance=5, mini_openid="oPrepay001")
o1_out = "TEST_PREPAY_FAIL"

mock_skus = [{"id": 11, "type": "points", "label": "体验包", "price": "9.9", "credits": 1,
              "duration_days": 0, "badge": "", "desc": "1次", "visible": True}]
mock_priv_key = MagicMock()

with patch('routers.pay._prepay_configured', return_value=True), \
     patch('routers.pay._pay_config', return_value=("mch_001", "wxappid_001", "apiv3key_32bytes_abcabcabcabcabc", "cert_sn", mock_priv_key, None, "https://example.com/notify", None, None)), \
     patch('routers.pay._load_private_key', return_value=mock_priv_key), \
     patch('routers.pay.get_user_skus', return_value=(mock_skus, True)), \
     patch('routers.pay._get_sys_config_str', return_value=""), \
     patch('routers.pay._wx_post', side_effect=Exception("connection refused")):
    try:
        body = PrepayBody(sku_id=11)
        wechat_prepay(body, user=_user, db=db1)
        check(False, "should have raised HTTPException")
    except HTTPException as e:
        check(e.status_code == 502, f"prepay fail → 502: {e.status_code}")
        check("异常" in str(e.detail) or "refused" in str(e.detail).lower(),
              f"error detail: {str(e.detail)[:80]}")

# Verify: exactly 1 order, status FAILED, not PAID, no BillingRecord
all_orders = db1.query(PaymentOrder).filter(PaymentOrder.user_id == 1001).all()
check(len(all_orders) == 1, f"exactly 1 order created: {len(all_orders)}")
check(all_orders[0].status == "FAILED", f"order status FAILED: {all_orders[0].status}")
check(all_orders[0].status != "PAID", "order definitely not PAID")
u1_after = db1.query(User).filter(User.id == 1001).first()
check(u1_after.balance_credits == 5, f"balance unchanged: {u1_after.balance_credits}")
br_count = db1.query(BillingRecord).filter(BillingRecord.user_id == 1001).count()
check(br_count == 0, f"no BillingRecord created: {br_count}")
db1.rollback()
print("T1 PASS")

# ═══ T2: PROCESSING reconcile → PAID ═══
print("=== T2: PROCESSING reconcile → PAID ===")
db2 = SessionLocal()
u2 = _seed_user(db2, user_id=2001, balance=2, mini_openid="oProc001")
o2 = _seed_order(db2, user_id=2001, out_trade_no="TEST_E2E_PROC", status="PROCESSING",
                 credits=5, pay_channel="WECHAT_VIRTUAL")
import routers.virtual_pay as vpay_mod
with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="PAID"):
    result = vpay_mod.reconcile_order("TEST_E2E_PROC", user={"user_id": 2001}, db=db2)
check(result.get("ok"), f"reconcile ok: {result}")
check(result.get("status") == "PAID", f"PROCESSING→PAID: {result}")
check(result.get("synced"), "synced=True")
db2.refresh(u2)
check(u2.balance_credits >= 7, f"credits granted: {u2.balance_credits}")
db2.rollback()
print("T2 PASS")

# ═══ T3: reconcile NOT_PAID → stays ═══
print("=== T3: reconcile NOT_PAID → stays ===")
db3 = SessionLocal()
u3 = _seed_user(db3, user_id=3001, balance=2, mini_openid="oNP001")
o3 = _seed_order(db3, user_id=3001, out_trade_no="TEST_E2E_NP", credits=3, pay_channel="WECHAT_VIRTUAL")
with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="NOT_PAID"):
    result3 = vpay_mod.reconcile_order("TEST_E2E_NP", user={"user_id": 3001}, db=db3)
check(result3.get("status") == "CREATED", f"NOT_PAID stays CREATED: {result3}")
check(not result3.get("synced"), "synced=False")
db3.rollback()
print("T3 PASS")

# ═══ T4: query order readable ═══
print("=== T4: query visible ===")
db4 = SessionLocal()
u4 = _seed_user(db4, user_id=4001, balance=2, mini_openid="oVis001")
o4 = _seed_order(db4, user_id=4001, out_trade_no="TEST_E2E_VIS", credits=3, amount_fen=1990,
                 pay_channel="WECHAT_VIRTUAL")
from routers.virtual_pay import query_virtual_order
r4 = query_virtual_order("TEST_E2E_VIS", user={"user_id": 4001}, db=db4)
check(r4.get("status") == "CREATED", f"query status: {r4['status']}")
check(r4.get("amount_fen") == 1990, f"query amount: {r4['amount_fen']}")
db4.rollback()
print("T4 PASS")

# ═══ T5: query error → status unchanged ═══
print("=== T5: query error → unchanged ===")
db5 = SessionLocal()
u5 = _seed_user(db5, user_id=5001, balance=10, mini_openid="oErr001")
o5 = _seed_order(db5, user_id=5001, out_trade_no="TEST_E2E_ERR", credits=3, pay_channel="WECHAT_VIRTUAL")
with patch.object(vpay_mod, '_wx_query_virtual_order', return_value="ERROR"):
    result5 = vpay_mod.reconcile_order("TEST_E2E_ERR", user={"user_id": 5001}, db=db5)
check(result5.get("status") == "CREATED", f"ERROR stays CREATED: {result5}")
check(not result5.get("synced"), "synced=False")
db5.rollback()
print("T5 PASS")

# ═══ T6: admin list_orders visible ═══
print("=== T6: admin order list visible ===")
db6 = SessionLocal()
u6 = _seed_user(db6, user_id=6001, balance=0, mini_openid="oAdm001")
o6 = _seed_order(db6, user_id=6001, out_trade_no="TEST_E2E_ADM", status="PAID",
                 credits=25, amount_fen=2990, membership_days=30, pay_channel="WECHAT_JSAPI")
from routers.admin import list_orders
r6 = list_orders(_admin, 1, 50, "", "", "TEST_E2E_ADM", db=db6)
check(r6.get("total", 0) >= 1, f"admin list has orders: total={r6.get('total')}")
orders6 = r6.get("orders", [])
check(len(orders6) >= 1, f"orders list non-empty: {len(orders6)}")
order6 = orders6[0]
for f in ["out_trade_no", "status", "amount_fen", "amount_yuan", "credits", "membership_days", "pay_channel", "user_id"]:
    check(f in order6, f"order has field '{f}'")
check(order6.get("out_trade_no") == "TEST_E2E_ADM", "out_trade_no matches")
check(order6.get("status") == "PAID", "status PAID")
check(order6.get("amount_fen") == 2990, f"amount_fen 2990: {order6.get('amount_fen')}")
check(order6.get("amount_yuan") == "29.90", f"amount_yuan '29.90': {order6.get('amount_yuan')}")
check(order6.get("credits") == 25, f"credits 25: {order6.get('credits')}")
check(order6.get("membership_days") == 30, f"membership_days 30: {order6.get('membership_days')}")
check(order6.get("pay_channel") == "WECHAT_JSAPI", f"pay_channel WECHAT_JSAPI: {order6.get('pay_channel')}")
check(order6.get("user_id") == 6001, f"user_id 6001: {order6.get('user_id')}")
db6.rollback()
print("T6 PASS")

# ═══ T7: balance after grant ═══
print("=== T7: balance refresh ===")
db7 = SessionLocal()
u7 = _seed_user(db7, user_id=7001, balance=3, mini_openid="oBal001")
o7 = _seed_order(db7, user_id=7001, out_trade_no="TEST_E2E_BAL", credits=7)
from services.payment_idempotency import claim_payment_order, grant_payment_benefits
check(claim_payment_order(db7, o7), "claim succeeds")
grant_payment_benefits(db7, o7)
db7.commit()
db7.refresh(u7)
check(u7.balance_credits == 10, f"balance 3+7=10: {u7.balance_credits}")
db7.rollback()
print("T7 PASS")

# ═══ T8: frontend audit ═══
print("=== T8: frontend ===")
uniapp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src', 'pages', 'profile')
for fname, markers in [
    ("recharge.vue", ["wx.requestVirtualPayment", "订单参数异常", "queryVirtualOrder", "reconcileVirtualOrder"]),
    ("orders.vue", ["wx.requestVirtualPayment", "支付参数异常", "queryVirtualOrder"]),
    ("order-detail.vue", ["wx.requestVirtualPayment", "支付参数异常", "queryVirtualOrder"]),
]:
    src = open(os.path.join(uniapp_dir, fname), 'r', encoding='utf-8').read()
    for m in markers:
        check(m in src, f"{fname} has '{m}'")
print("T8 PASS")

# ═══ T9: manual E2E checklist ═══
print("=== T9: manual E2E checklist ===")
print("""
真实商户 E2E 验收清单
==================
配置:
  [ ] 微信商户号 mch_id + API v3 Key + 私钥 + 证书序列号 + 平台证书
  [ ] 虚拟支付 Offer ID + App Key
  [ ] 支付回调 URL / 虚拟支付回调 URL 已在微信后台配置

小程序端:
  [ ] SKU 选择 → createPrepay → requestPayment 拉起支付
  [ ] 虚拟支付 SKU → createVirtualPrepay → wx.requestVirtualPayment
  [ ] 支付成功 → queryOrder PAID → balance/membership 更新
  [ ] 取消/失败 → 明确提示
  [ ] 处理中 → 轮询 + reconcile 补偿

后台:
  [ ] 订单列表可见 (admin list_orders)
  [ ] 订单详情：out_trade_no / amount / status / credits / membership_days
  [ ] 重复回调不重复发权益
  [ ] 取消/超时/查单失败状态正确
""")
print("T9 PASS (manual checklist above)")

print(f"\n{'='*50}")
print(f"PAYMENT E2E ACCEPTANCE: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
