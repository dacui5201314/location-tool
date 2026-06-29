"""5.2: Frontend payment guard audit — param checks, no fallbacks, polling, reconcile"""
import sys, os, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

p = 0
fails = 0
def check(cond, msg):
    global p, fails
    if cond: p += 1
    else: fails += 1; print(f"  FAIL: {msg}")


uniapp_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'uniapp', 'src', 'pages', 'profile')
files = ["recharge.vue", "orders.vue", "order-detail.vue"]

# ═══ T1: no || '' or || 'short_series_goods' in wx.requestVirtualPayment params ═══
print("=== T1: no fallback in wx call ===")
for fname in files:
    src = open(os.path.join(uniapp_dir, fname), 'r', encoding='utf-8').read()
    # Find the wx.requestVirtualPayment block
    idx = src.find('wx.requestVirtualPayment')
    if idx < 0:
        continue
    block = src[idx:idx+300]
    check("|| ''" not in block, f"{fname}: no || '' in wx call")
    check("|| 'short_series_goods'" not in block, f"{fname}: no || 'short_series_goods' in wx call")
print("T1 PASS")

# ═══ T2: param validation before wx call ═══
print("=== T2: param validation ===")
for fname, expect in [
    ("recharge.vue", ["订单参数异常，请重新下单", "pp.mode", "pp.signData", "pp.paySig", "pp.signature", "pp.order_no"]),
    ("orders.vue", ["支付参数异常，请重新发起支付", "pp.mode", "pp.signData", "pp.paySig", "pp.signature", "pp.order_no", "o.out_trade_no"]),
    ("order-detail.vue", ["支付参数异常，请重新发起支付", "pp.mode", "pp.signData", "pp.paySig", "pp.signature", "pp.order_no", "this.orderNo"]),
]:
    src = open(os.path.join(uniapp_dir, fname), 'r', encoding='utf-8').read()
    for e in expect:
        check(e in src, f"{fname}: has '{e}'")
print("T2 PASS")

# ═══ T3: polling 20 iterations + reconcile ═══
print("=== T3: polling + reconcile ===")
src_r = open(os.path.join(uniapp_dir, "recharge.vue"), 'r', encoding='utf-8').read()
check("i < 20" in src_r, "recharge: 20 polling iterations")
check("reconcileVirtualOrder" in src_r, "recharge: reconcile compensation")
check("支付确认中" in src_r, "recharge: shows '支付确认中'")
check("支付处理中" in src_r, "recharge: shows '支付处理中'")

for fname in ["orders.vue", "order-detail.vue"]:
    src = open(os.path.join(uniapp_dir, fname), 'r', encoding='utf-8').read()
    check("i < 20" in src, f"{fname}: 20 polling iterations")
print("T3 PASS")

# ═══ T4: cancel shows toast, not silent return ═══
print("=== T4: cancel messages ===")
src_r = open(os.path.join(uniapp_dir, "recharge.vue"), 'r', encoding='utf-8').read()
check("已取消支付" in src_r, "recharge: cancel message")
check("支付失败" in src_r or "支付服务异常" in src_r or "payErr" in src_r, "recharge: handles failure")

for fname in ["orders.vue", "order-detail.vue"]:
    src = open(os.path.join(uniapp_dir, fname), 'r', encoding='utf-8').read()
    check("errMsg.includes('cancel')" in src or "errMsg.includes(\"cancel\")" in src,
          f"{fname}: cancel branch exists")
    # Find cancel line context
    cancel_idx = src.find("cancel")
    ctx = src[max(0,cancel_idx-40):cancel_idx+80] if cancel_idx >= 0 else ""
    check("showToast" in ctx, f"{fname}: cancel branch has showToast")
    check("已取消支付" in src, f"{fname}: has '已取消支付'")
    check("return" in ctx, f"{fname}: cancel branch still returns after toast")
print("T4 PASS")

# ═══ T5: queryVirtualOrder in all 3 files ═══
print("=== T5: queryVirtualOrder ===")
for fname in files:
    src = open(os.path.join(uniapp_dir, fname), 'r', encoding='utf-8').read()
    check("queryVirtualOrder" in src, f"{fname}: calls queryVirtualOrder")
print("T5 PASS")

print(f"\n{'='*50}")
print(f"FRONTEND PAYMENT GUARD: {p} PASS, {fails} FAIL (total {p+fails})")
if fails: sys.exit(1)
