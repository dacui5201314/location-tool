"""轻量验证：擀面皮品牌感知 classification 不污染数据口径。"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from services.amap_service import classify_poi_rigor
from prompts.industry_config import get_rigor_for_config_key

RIGOR = get_rigor_for_config_key("刚需快餐小吃")
assert RIGOR, "刚需快餐小吃 rigor missing"

BRAND = "陕二丫擀面皮"
BTYPE = "小餐饮"
CAT = "fast_food"
TCODE = "050300"

cases = [
    # (name, expected_min, expected_max_or_same)
    ("陕二丫擀面皮", "direct"),
    ("老街热米皮", "direct"),
    ("老八米线", "substitute"),
    ("鼎香源砂锅店", "substitute"),
    ("东福水饺", "substitute"),
    ("马文老味砂锅", "substitute"),
    ("张记牛肉拉面", "substitute"),
    ("老孙家泡馍", "substitute"),
    ("魏家凉皮", "direct"),
    ("袁师傅擀面皮", "direct"),
    ("秦镇米皮老店", "direct"),
    ("汉中热米皮", "direct"),
    ("王家饺子馆", "substitute"),
    ("杨国福麻辣烫", "substitute"),
    ("柳州螺蛳粉", "substitute"),
    # non-面皮 brand: should fall back to master rules (米线/sandpot etc are direct)
    ("老八米线", "direct"),  # with empty brand
    ("鼎香源砂锅店", "direct"),  # with empty brand
    ("东福水饺", "direct"),  # with empty brand
]

failures = 0
for i, (name, expected) in enumerate(cases):
    if i >= 15:
        # Last 3 are non-brand tests
        actual = classify_poi_rigor(name, CAT, TCODE, RIGOR, BTYPE, brand_name="")
    else:
        actual = classify_poi_rigor(name, CAT, TCODE, RIGOR, BTYPE, brand_name=BRAND)

    status = "PASS" if actual == expected else "FAIL"
    if status == "FAIL":
        failures += 1
    print(f"[{status}] {name:16s} → {actual:12s} (expected={expected})")

print(f"\n{'='*50}")
print(f"TOTAL: {len(cases) - failures} PASS, {failures} FAIL")
if failures:
    sys.exit(1)
else:
    print("ALL PASSED")
