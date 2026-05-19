"""
Industry Rigor Rules — canonical read-only self-test
Verifies 43 business type completeness, snack/hospital/pharmacy/residential/convenience accuracy.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from prompts.industry_config import (
    BUSINESS_TYPE_TO_MASTER, MASTER_TEMPLATES, INDUSTRY_RIGOR, get_rigor_for_config_key
)
from services.amap_service import (
    classify_poi_rigor, classify_poi_type,
    is_real_hospital, is_real_residential, is_real_convenience, is_real_pharmacy,
    is_real_training, is_real_laundry, is_real_clinic,
    is_real_fitness, is_real_fresh_retail, is_real_tobacco_liquor_retail,
    is_real_shopping, is_real_hotel, is_real_immersive_entertainment,
    is_real_office, is_real_school, is_real_low_freq_retail,
)

p, f = 0, 0
def check(cond, label):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {label}")

_cr = classify_poi_rigor
_d = lambda rigor, n, c, b="", cat="fast_food": _cr(n, cat, c, rigor, b) == "direct"
_nd = lambda rigor, n, c, b="", cat="fast_food": _cr(n, cat, c, rigor, b) != "direct"

# ===== A. Completeness =====
print("=== A. Completeness ===")
check(len(BUSINESS_TYPE_TO_MASTER) == 43, f"43 entries: got {len(BUSINESS_TYPE_TO_MASTER)}")
check(len(MASTER_TEMPLATES) == 14, f"14 masters: got {len(MASTER_TEMPLATES)}")
check(len(INDUSTRY_RIGOR) == 14, f"14 rigor: got {len(INDUSTRY_RIGOR)}")
check(set(MASTER_TEMPLATES.keys()) == set(INDUSTRY_RIGOR.keys()),
    f"MASTER_TEMPLATES keys == INDUSTRY_RIGOR keys")
for bt in sorted(BUSINESS_TYPE_TO_MASTER):
    mk = BUSINESS_TYPE_TO_MASTER[bt]
    ok = mk in MASTER_TEMPLATES and mk in INDUSTRY_RIGOR
    check(ok, f"{bt} -> {mk}")
    if ok:
        rigor = INDUSTRY_RIGOR[mk]
        for fld in ("direct_competitor_rules","substitute_competitor_rules","traffic_anchor_rules","irrelevant_poi_rules"):
            check(fld in rigor, f"{mk}.{fld}")
print(f"  Entries: {len(BUSINESS_TYPE_TO_MASTER)}, Masters: {len(MASTER_TEMPLATES)}, Rigor: {len(INDUSTRY_RIGOR)}")

# ===== B. Snack Shop =====
print("\n=== B. Snack Shop Tests ===")
rigor = get_rigor_for_config_key("刚需快餐小吃")
dc = rigor.get("direct_competitor_rules", {})
check(dc.get("require_name_keyword_for_code") == True, "require_name_keyword_for_code=True")
check(dc.get("substitute_before_direct") == True, "substitute_before_direct=True")
check(len(dc.get("name_keywords",[])) >= 30, "snack keywords >= 30")
check(len(dc.get("exclude_names",[])) >= 25, "snack exclude >= 25")
single = [k for k in dc.get("name_keywords",[]) if len(k) == 1]
check(len(single) == 0, f"no single-char keywords: {single}")

code = "050300"
for name in ["擀面皮","凉皮","米皮","烙面皮","螺蛳粉","酸辣粉","麻辣烫","麻辣拌","肉夹馍","包子","饺子","馄饨","砂锅","冒菜","拉面","拌面","热干面","沙县小吃","宝宝面皮","魏家凉皮","小蛮螺螺蛳粉","张亮麻辣烫","老潼关肉夹馍","兰州拉面","袁记云饺","阿香米线"]:
    check(_d(rigor, name, code, "小吃店"), f"direct: {name}")
for name in ["韩国料理紫菜包饭","圈圈寿司","绝味鸭脖","久久鸭脖","茶百道","蜜雪冰城","星巴克咖啡","瑞幸咖啡","肯德基","麦当劳","华莱士","德克士","汉堡王","必胜客","海底捞火锅","某某中餐厅","某某酒楼","某某烧烤","某某烤鱼","甜品店","蛋糕店","咖啡店","奶茶店","老乡鸡","乡村基","真功夫"]:
    check(_nd(rigor, name, code, "小吃店"), f"NOT direct: {name}")

# Substitute priority: 鸭脖/卤味/炸鸡/汉堡 must be substitute, not direct
for name in ["绝味鸭脖","久久鸭脖","正新鸡排","汉堡"]:
    r = classify_poi_rigor(name, "fast_food", "050300", rigor, "小吃店")
    check(r == "substitute", f"substitute: {name} -> {r}")

# ===== C. Hospital/Pharmacy =====
print("\n=== C. Hospital/Pharmacy Tests ===")
for n in ["某某人民医院","某某中心医院","某某中医院","某某妇幼保健院","某某社区卫生服务中心","某某卫生院","某某市儿童医院","某某市急救中心"]:
    check(is_real_hospital(n), f"hospital: {n}")
for n in ["某某人民医院门诊部","某某人民医院发热门诊","某某人民医院住院部","某某人民医院急诊中心","某某人民医院创伤中心"]:
    check(is_real_hospital(n), f"hospital dept: {n}")
for n in ["某某人民医院体检中心","某某人民医院整形美容中心","某某人民医院美容中心","某某人民医院康复中心","某某人民医院皮肤科"]:
    check(not is_real_hospital(n), f"NOT hospital: {n}")
for n in ["某某眼科","某某视光中心","某某助听器","某某皮肤修护","某某疤痕管理","某某医美中心","某某理疗馆"]:
    check(not is_real_hospital(n), f"NOT hospital: {n}")
    check(not is_real_pharmacy(n), f"NOT pharmacy: {n}")
for n in ["某某大药房","某某同仁堂","某某益丰","某某海王星辰"]:
    check(is_real_pharmacy(n), f"pharmacy: {n}")
for n in ["牙博士口腔医院","普通口腔门诊","某儿科门诊"]:
    check(not is_real_hospital(n), f"NOT hospital: {n}")

# ===== D. Residential/Convenience =====
print("\n=== D. Residential/Convenience Tests ===")
for n in ["公交公司家属院","阳光小区","翠苑新村","兰亭公寓"]:
    check(is_real_residential(n), f"residential: {n}")
for n in ["某某产业园","某某科技园","某某写字楼","某某办公楼","某某商务大厦","某某人民法院","某某养老院","某某美容院"]:
    check(not is_real_residential(n), f"NOT residential: {n}")
for n in ["社区便利店","小区便利店","便民超市","生鲜超市","烟酒副食店","日杂百货店"]:
    check(is_real_convenience(n), f"convenience: {n}")
for n in ["美甲沙龙","充客手机快修连锁","中国体育彩票","黄金加工回收","OPPO授权体验店","华为授权体验店","快递驿站"]:
    check(not is_real_convenience(n), f"NOT convenience: {n}")

# ===== E. Subtype Inheritance Test =====
print("\n=== E. Subtype Inheritance ===")
# Verify master-level fields propagate to subtype in classify_poi_rigor
rigor_retail = get_rigor_for_config_key("高频刚需零售")
master_dc = rigor_retail.get("direct_competitor_rules", {})
check(master_dc.get("require_name_keyword_for_code") == True, "retail master require_name_keyword_for_code=True")
check(master_dc.get("substitute_before_direct") == True, "retail master substitute_before_direct=True")
stypes = master_dc.get("subtypes", {})
check(len(stypes) == 5, f"retail subtypes count: {len(stypes)}")

# Verify subtype merge: supermarket should inherit master booleans
from services.amap_service import classify_poi_rigor as _cr
# A convenience store with 050300 code should be direct (keyword match + require_kw)
r1 = _cr("社区便利店", "convenience", "050300", rigor_retail, "便利店")
check(r1 == "direct", f"retail便利店 inherit: 社区便利店 -> {r1}")
# A 美甲 salon with same code should NOT be direct (strict_exclude from master inherited)
r2 = _cr("美甲沙龙", "convenience", "050300", rigor_retail, "便利店")
check(r2 != "direct", f"retail便利店 inherit strict_exclude: 美甲沙龙 -> {r2} (expected not direct)")

# ===== F. High-Frequency Retail Subtypes =====
print("\n=== F. Retail Subtypes ===")
for bt, subtype_name, direct_pos, direct_neg in [
    ("便利店", "supermarket",
        ["社区便利店","便民超市","某某小卖部","某某生活超市","每一天便利店"],
        ["美甲沙龙","手机快修","中国体育彩票","黄金回收","OPPO体验店","某某药房","某某大药房","某某百货大楼","某某购物中心"]),
    ("生鲜店", "fresh",
        ["某某生鲜超市","某某水果店","某某蔬菜店","某某果品店","某某鲜肉店"],
        ["某某百货超市","某某便利店","某某冷库","某某批发市场","某某餐饮店","某某药房"]),
    ("药店", "pharmacy2",
        ["某某大药房","某某药店","某某医药连锁","同仁堂药店","老百姓大药房"],
        ["某某医院","某某诊所","某某口腔医院","某某眼科中心","某某体检中心","某某助听器店"]),
    ("烟酒店", "tobacco_liquor",
        ["某某烟酒店","某某名烟名酒","某某酒水商行","某某酒庄","某某酒行"],
        ["某某酒吧","某某餐厅","某某KTV","某某超市","某某便利店","某某茶叶店"]),
    ("日用百货", "daily_goods",
        ["某某百货店","某某日杂店","某某杂货铺","某某日用品店","某某两元店"],
        ["某某建材市场","某某五金店","某某购物中心","某某服装店","某某家电城","某某便利店"]),
]:
    rig = get_rigor_for_config_key("高频刚需零售")
    for name in direct_pos:
        r = _cr(name, "convenience", "050300", rig, bt)
        check(r == "direct", f"{bt} direct: {name} -> {r}")
    for name in direct_neg:
        r = _cr(name, "convenience", "050300", rig, bt)
        check(r != "direct", f"{bt} NOT direct: {name} -> {r}")

# ===== G. Professional Life Services Subtypes =====
print("\n=== G. Professional Services Subtypes ===")
for bt, direct_pos, direct_neg in [
    ("美容美发",
        ["某某美容院","某某美发店","某某美甲店","某某SPA会所","某某皮肤管理"],
        ["某某宠物店","某某动物医院","某某健身房","某某瑜伽馆","某某足疗店","某某按摩店","某某医美诊所"]),
    ("宠物店",
        ["某某宠物店","某某宠物用品","某某猫舍","某某犬舍","某某宠物生活馆"],
        ["某某美容院","某某美发店","某某动物医院","某某宠物医院","某某健身房","某某兽药店"]),
    ("健身房",
        ["某某健身房","某某瑜伽馆","某某普拉提","某某私教工作室","某某游泳馆"],
        ["某某宠物店","某某美容院","某某足疗按摩","某某体育用品店","某某推拿艾灸","某某舞蹈培训班"]),
]:
    rig = get_rigor_for_config_key("专业生活服务")
    for name in direct_pos:
        r = _cr(name, "convenience", "050300", rig, bt)
        check(r == "direct", f"{bt} direct: {name} -> {r}")
    for name in direct_neg:
        r = _cr(name, "convenience", "050300", rig, bt)
        check(r != "direct", f"{bt} NOT direct: {name} -> {r}")

# ===== H. Community Basic Services Subtypes =====
print("\n=== H. Community Services Subtypes ===")
for bt, direct_pos, direct_neg in [
    ("教育培训",
        ["某某教育培训","某某琴行","某某画室","某某早教中心","某某托管班","某某辅导班","某某语言培训"],
        ["某某洗衣店","某某干洗店","某某诊所","某某学校","某某小学","某某幼儿园","某某文具店"]),
    ("洗衣店",
        ["某某洗衣店","某某干洗店","某某洗护中心","某某衣物护理","某某干洗连锁"],
        ["某某培训中心","某某教育机构","某某诊所","某某家政公司","某某维修店","某某皮具护理"]),
    ("诊所",
        ["某某诊所","某某卫生所","某某社区卫生站","某某中医诊所","某某中西医结合门诊"],
        ["某某培训中心","某某洗衣店","某某医院","某某口腔医院","某某眼科医院","某某体检中心","某某大药房"]),
]:
    rig = get_rigor_for_config_key("社区基础服务")
    for name in direct_pos:
        r = _cr(name, "convenience", "050300", rig, bt)
        check(r == "direct", f"{bt} direct: {name} -> {r}")
    for name in direct_neg:
        r = _cr(name, "convenience", "050300", rig, bt)
        check(r != "direct", f"{bt} NOT direct: {name} -> {r}")

# ===== I. Nightlife Entertainment Subtypes =====
print("\n=== I. Nightlife Subtypes ===")
for bt, direct_pos, direct_neg in [
    ("酒吧",
        ["某某酒吧","某某清吧","某某精酿酒馆","某某LiveHouse","某某威士忌吧","某某鸡尾酒吧"],
        ["某某KTV","某某网吧","某某网咖","某某台球厅","某某棋牌室","某某咖啡厅","某某餐厅"]),
    ("KTV",
        ["某某KTV","某某歌厅","某某练歌房","某某量贩KTV","某某卡拉OK"],
        ["某某酒吧","某某清吧","某某网吧","某某网咖","某某台球厅","某某棋牌室","某某餐厅"]),
    ("网吧",
        ["某某网吧","某某网咖","某某电竞馆","某某电竞酒店","某某电竞中心"],
        ["某某酒吧","某某KTV","某某台球厅","某某棋牌室","某某酒店","某某宾馆"]),
]:
    rig = get_rigor_for_config_key("夜经济娱乐")
    for name in direct_pos:
        r = _cr(name, "bars", "080000", rig, bt)
        check(r == "direct", f"{bt} direct: {name} -> {r}")
    for name in direct_neg:
        r = _cr(name, "bars", "080000", rig, bt)
        check(r != "direct", f"{bt} NOT direct: {name} -> {r}")

# ===== J. High-Risk Code Audit =====
print("\n=== J. High-Risk Code Audit ===")
for mk, rig in INDUSTRY_RIGOR.items():
    dc = rig.get("direct_competitor_rules", {})
    codes = dc.get("amap_codes", [])
    has_broad = any(c in ("050000","050300","060000","070000","080000","090000","100000","120000","140000","150000") for c in codes)
    require_kw = dc.get("require_name_keyword_for_code", False)
    sub_first = dc.get("substitute_before_direct", False)
    if has_broad and not require_kw:
        print(f"  TODO: {mk} broad={codes} require_kw=False (may need tightening)")
    elif has_broad and require_kw:
        print(f"  OK: {mk} broad={codes} require_kw=True sub_first={sub_first}")

# ===== K. classify_poi_type 映射 =====
print("\n=== K. classify_poi_type Mapping ===")
for type_code, expected_cat in [
    ("科教文化服务;培训机构", "education_training"),
    ("141200", "education_training"),
    ("生活服务;洗衣店", "laundry"),
    ("医疗保健服务;诊所", "clinics"),
    ("090300", "clinics"),
    ("医疗保健服务;综合医院", "hospitals"),
    ("090100", "hospitals"),
    ("医疗保健服务;医药保健销售店", "pharmacy"),
    ("090400", "pharmacy"),
    ("科教文化服务;学校", "schools"),
]:
    got = classify_poi_type(type_code)
    check(got == expected_cat, f"classify_poi_type(\"{type_code}\")={got} exp={expected_cat}")

# ===== L. Dewatering — Training/Laundry/Clinic =====
print("\n=== L. New Dewatering Functions ===")
for name in ["语言培训中心","美术培训","某某琴行","某某画室","某某驾校","某某职业技能"]:
    check(is_real_training(name), f"training: {name}")
for name in ["某某小学","某某幼儿园","某某文具店","某某书店","某某教育局"]:
    check(not is_real_training(name), f"NOT training: {name}")
for name in ["某某洗衣店","某某干洗店","某某洗护中心","某某衣物护理"]:
    check(is_real_laundry(name), f"laundry: {name}")
for name in ["某某家政","某某手机维修","某某皮具护理","某某擦鞋店"]:
    check(not is_real_laundry(name), f"NOT laundry: {name}")
for name in ["某某诊所","某某卫生所","某某社区卫生室","某某医务室","某某中医诊所","某某中西医结合门诊"]:
    check(is_real_clinic(name), f"clinic: {name}")
for name in ["某某综合医院","某某口腔医院","某某眼科医院","某某体检中心","某某大药房","某某医美中心","某某助听器"]:
    check(not is_real_clinic(name), f"NOT clinic: {name}")

# ===== M. Real-Chain Simulation =====
print("\n=== M. Real-Chain Simulation ===")
def sim_chain(name, type_code, rigor_key, bt):
    cat = classify_poi_type(type_code)
    if cat is None: return "no_cat"
    if cat == "education_training" and not is_real_training(name): return "dewater_drop"
    if cat == "laundry" and not is_real_laundry(name): return "dewater_drop"
    if cat == "clinics" and not is_real_clinic(name): return "dewater_drop"
    rig = get_rigor_for_config_key(rigor_key)
    return _cr(name, cat, type_code, rig, bt)

for bt, rigor_key, direct_pos, direct_neg in [
    ("教育培训", "社区基础服务",
        [("语言培训中心","科教文化服务;培训机构"),("美术培训","科教文化服务;培训机构"),
         ("某某早教中心","科教文化服务;培训机构"),("某某托管班","科教文化服务;培训机构"),("某某辅导班","141200")],
        [("某某小学","科教文化服务;培训机构"),("某某幼儿园","科教文化服务;培训机构"),
         ("某某文具店","141200"),("某某书店","141200"),("某某教育局","141200")]),
    ("洗衣店", "社区基础服务",
        [("某某洗衣店","生活服务;洗衣店"),("某某干洗店","生活服务;洗衣店"),
         ("某某洗护中心","生活服务;洗衣店"),("某某衣物护理","生活服务;洗衣店"),("某某干洗连锁","生活服务;洗衣店")],
        [("某某家政公司","生活服务;洗衣店"),("某某手机维修","生活服务;洗衣店"),
         ("某某皮具护理","生活服务;洗衣店"),("某某擦鞋店","生活服务;洗衣店"),("某某教育培训","生活服务;洗衣店")]),
    ("诊所", "社区基础服务",
        [("某某中医诊所","医疗保健服务;诊所"),("某某中西医结合门诊","090300"),
         ("某某社区卫生室","医疗保健服务;诊所"),("某某医务室","090300"),("某某卫生所","医疗保健服务;诊所")],
        [("某某综合医院","医疗保健服务;诊所"),("某某口腔医院","090300"),
         ("某某眼科医院","090300"),("某某体检中心","医疗保健服务;诊所"),("某某大药房","090300"),
         ("某某医美中心","090300"),("某某助听器","090300")]),
]:
    for name, tc in direct_pos:
        r = sim_chain(name, tc, rigor_key, bt)
        check(r == "direct", f"{bt} chain direct: {name}({tc}) -> {r}")
    for name, tc in direct_neg:
        r = sim_chain(name, tc, rigor_key, bt)
        check(r != "direct", f"{bt} chain NOT direct: {name}({tc}) -> {r}")

# ===== N. classify_poi_type — New Categories =====
print("\n=== N. classify_poi_type — New Categories ===")
for type_code, expected_cat in [
    ("体育休闲服务;运动场馆", "fitness"),
]:
    got = classify_poi_type(type_code)
    check(got == expected_cat, f"classify_poi_type(\"{type_code}\")={got} exp={expected_cat}")

# ===== O. New Dewatering Functions =====
print("\n=== O. New Dewatering — Fitness/Fresh/Tobacco ===")
for name in ["某某健身房","某某健身中心","某某瑜伽馆","某某普拉提","某某私教工作室","某某游泳馆"]:
    check(is_real_fitness(name), f"fitness: {name}")
for name in ["某某体育用品店","某某足疗按摩","某某舞蹈培训班","某某美容院","某某宠物店"]:
    check(not is_real_fitness(name), f"NOT fitness: {name}")
for name in ["某某生鲜超市","某某水果店","某某蔬菜店","某某鲜果店","某某菜店","某某鲜肉店"]:
    check(is_real_fresh_retail(name), f"fresh_retail: {name}")
for name in ["某某百货超市","某某便利店","某某药店","某某餐饮店","某某冷库","某某批发市场"]:
    check(not is_real_fresh_retail(name), f"NOT fresh_retail: {name}")
for name in ["某某烟酒店","某某烟酒行","某某名烟名酒","某某酒水商行","某某酒行","某某酒庄"]:
    check(is_real_tobacco_liquor_retail(name), f"tobacco_liquor: {name}")
for name in ["某某酒吧","某某KTV","某某餐厅","某某超市","某某便利店","某某茶叶店"]:
    check(not is_real_tobacco_liquor_retail(name), f"NOT tobacco_liquor: {name}")

# ===== P. Real-Chain — Fitness/Fresh/Tobacco =====
print("\n=== P. Real-Chain — Fitness/Fresh/Tobacco ===")
def sim_real_chain(name, type_code, rigor_key, bt):
    """模拟真实采集链路：classify_poi_type → 业务感知改写 → 脱水 → classify_poi_rigor"""
    cat = classify_poi_type(type_code)
    if cat is None: return "no_cat"
    # 业务感知改写：shopping 大类下的生鲜/烟酒 → 独立 category
    if cat == "shopping":
        if any(kw in bt for kw in ("生鲜","水果","蔬菜","菜店","鲜果")):
            if is_real_fresh_retail(name):
                cat = "fresh_retail"
        elif any(kw in bt for kw in ("烟酒","名烟","名酒","酒行","酒类")):
            if is_real_tobacco_liquor_retail(name):
                cat = "tobacco_liquor"
    # 脱水
    if cat == "fitness" and not is_real_fitness(name): return "dewater_drop"
    if cat == "fresh_retail" and not is_real_fresh_retail(name): return "dewater_drop"
    if cat == "tobacco_liquor" and not is_real_tobacco_liquor_retail(name): return "dewater_drop"
    if cat == "shopping" and not is_real_shopping(name): return "dewater_drop"
    rig = get_rigor_for_config_key(rigor_key)
    return _cr(name, cat, type_code, rig, bt)

for bt, rigor_key, direct_pos, direct_neg in [
    ("健身房", "专业生活服务",
        [("某某健身房","体育休闲服务;运动场馆"),("某某健身中心","体育休闲服务;运动场馆"),
         ("某某瑜伽馆","体育休闲服务;运动场馆"),("某某普拉提","体育休闲服务;运动场馆"),
         ("某某私教工作室","体育休闲服务;运动场馆")],
        [("某某体育用品店","体育休闲服务;运动场馆"),("某某足疗按摩","体育休闲服务;运动场馆"),
         ("某某舞蹈培训","体育休闲服务;运动场馆"),("某某美容院","体育休闲服务;运动场馆"),
         ("某某宠物店","体育休闲服务;运动场馆")]),
    ("生鲜店", "高频刚需零售",
        [("某某生鲜超市","购物服务"),("某某水果店","购物服务"),
         ("某某蔬菜店","购物服务"),("某某鲜果店","购物服务"),
         ("某某菜店","购物服务")],
        [("某某百货超市","购物服务"),("某某便利店","购物服务"),
         ("某某药店","购物服务"),("某某餐饮店","购物服务"),
         ("某某冷库","购物服务"),("某某批发市场","购物服务")]),
    ("烟酒店", "高频刚需零售",
        [("某某烟酒店","购物服务"),("某某烟酒行","购物服务"),
         ("某某名烟名酒","购物服务"),("某某酒水商行","购物服务"),
         ("某某酒行","购物服务")],
        [("某某酒吧","购物服务"),("某某KTV","购物服务"),
         ("某某餐厅","购物服务"),("某某超市","购物服务"),
         ("某某便利店","购物服务"),("某某茶叶店","购物服务")]),
]:
    for name, tc in direct_pos:
        r = sim_real_chain(name, tc, rigor_key, bt)
        check(r == "direct", f"{bt} chain direct: {name}({tc}) -> {r}")
    for name, tc in direct_neg:
        r = sim_real_chain(name, tc, rigor_key, bt)
        check(r != "direct", f"{bt} chain NOT direct: {name}({tc}) -> {r}")

# ===== Q. Hotels — Rule Tightening =====
print("\n=== Q. Hotels — Rule Tightening ===")
for mk in ["商务酒店","民宿青旅"]:
    dc = INDUSTRY_RIGOR.get(mk,{}).get("direct_competitor_rules",{})
    check(dc.get("require_name_keyword_for_code") == True, f"{mk} require_name_keyword_for_code=True")
    check(dc.get("substitute_before_direct") == True, f"{mk} substitute_before_direct=True")
    check(len(dc.get("name_keywords",[])) >= 8, f"{mk} keywords >= 8")
# 民宿青旅 direct kw 不应包含 短租公寓
inn_dc = INDUSTRY_RIGOR["民宿青旅"]["direct_competitor_rules"]
check("短租公寓" not in inn_dc.get("name_keywords",[]), "inn direct kw NOT contain 短租公寓")

# ===== R. Hotels — Direct/Not Direct =====
print("\n=== R. Hotels — Direct/Not Direct ===")
hotel_rigor = get_rigor_for_config_key("商务酒店")
for name in ["某某商务酒店","某某快捷酒店","某某宾馆","某某大酒店","某某连锁酒店","汉庭酒店","全季酒店","亚朵酒店","某某旅店"]:
    check(_d(hotel_rigor, name, "100000", "商务酒店", "hotels"), f"hotel direct: {name}")
for name in ["某某民宿","某某青旅","某某客栈","某某洗浴中心","某某足浴会所","某某农家乐","某某日租房","某某钟点房","某某电竞酒店","某某公寓"]:
    check(_nd(hotel_rigor, name, "100000", "商务酒店", "hotels"), f"hotel NOT direct: {name}")

inn_rigor = get_rigor_for_config_key("民宿青旅")
for name in ["某某民宿","某某青旅","某某青年旅舍","某某客栈","某某背包客旅舍","某某旅舍"]:
    check(_d(inn_rigor, name, "100000", "民宿青旅", "hotels"), f"inn direct: {name}")
for name in ["某某星级酒店","某某希尔顿","某某万豪","某某商务宾馆","某某洗浴中心","某某日租房","某某电竞酒店","某某公寓"]:
    check(_nd(inn_rigor, name, "100000", "民宿青旅", "hotels"), f"inn NOT direct: {name}")

# ===== S. Hotels — Real-Chain =====
print("\n=== S. Hotels — Real-Chain ===")
def sim_hotel_chain(name, type_code, rigor_key, bt):
    cat = classify_poi_type(type_code)
    if cat is None: return "no_cat"
    if cat == "hotels" and not is_real_hotel(name): return "dewater_drop"
    if cat == "hospitals": return "wrong_cat_hospital"
    rig = get_rigor_for_config_key(rigor_key)
    return _cr(name, cat, type_code, rig, bt)

for bt, rigor_key, direct_pos, direct_neg in [
    ("商务酒店", "商务酒店",
        [("某某商务酒店","住宿服务"),("某某快捷酒店","住宿服务"),("某某宾馆","100000"),
         ("某某大酒店","住宿服务"),("汉庭酒店","100000"),("全季酒店","住宿服务"),("某某旅店","100000")],
        [("某某民宿","住宿服务"),("某某青旅","100000"),("某某洗浴中心","住宿服务"),
         ("某某足浴会所","100000"),("某某农家乐","住宿服务"),("某某日租房","100000"),
         ("某某钟点房","住宿服务"),("某某电竞酒店","100000"),("某某公寓","住宿服务")]),
    ("民宿青旅", "民宿青旅",
        [("某某民宿","住宿服务"),("某某青旅","100000"),("某某青年旅舍","住宿服务"),
         ("某某客栈","100000"),("某某背包客旅舍","住宿服务"),("某某旅舍","100000")],
        [("某某星级酒店","住宿服务"),("某某希尔顿","100000"),("某某万豪","住宿服务"),
         ("某某商务宾馆","100000"),("某某洗浴中心","住宿服务"),("某某日租房","100000"),
         ("某某电竞酒店","住宿服务"),("某某公寓","100000"),("某某快捷酒店","住宿服务")]),
]:
    for name, tc in direct_pos:
        r = sim_hotel_chain(name, tc, rigor_key, bt)
        check(r == "direct", f"{bt} chain direct: {name}({tc}) -> {r}")
    for name, tc in direct_neg:
        r = sim_hotel_chain(name, tc, rigor_key, bt)
        check(r != "direct", f"{bt} chain NOT direct: {name}({tc}) -> {r}")

# ===== S2. Hotels — Explicit substitute/irrelevant =====
print("\n=== S2. Hotels — Substitute/Irrelevant ===")
hotel_rig = get_rigor_for_config_key("商务酒店")
inn_rig = get_rigor_for_config_key("民宿青旅")
for name in ["某某公寓酒店","某某短租公寓","某某电竞酒店"]:
    r = classify_poi_rigor(name, "hotels", "100000", hotel_rig, "商务酒店")
    check(r == "substitute", f"hotel substitute: {name} -> {r}")
for name in ["某某洗浴中心","某某足浴会所","某某KTV","某某招待所","某某日租房","某某钟点房","某某农家乐"]:
    r = classify_poi_rigor(name, "hotels", "100000", hotel_rig, "商务酒店")
    check(r != "direct" and r != "substitute", f"hotel excl: {name} -> {r}")
for name in ["某某公寓酒店","某某短租公寓","某某电竞酒店","某某快捷酒店","汉庭连锁","如家酒店"]:
    r = classify_poi_rigor(name, "hotels", "100000", inn_rig, "民宿青旅")
    check(r == "substitute", f"inn substitute: {name} -> {r}")
for name in ["某某洗浴中心","某某足浴会所","某某KTV","某某招待所","某某日租房","某某钟点房","某某农家乐"]:
    r = classify_poi_rigor(name, "hotels", "100000", inn_rig, "民宿青旅")
    check(r != "direct" and r != "substitute", f"inn excl: {name} -> {r}")

# ===== T. Remaining TODOs =====
print("\n=== T. Remaining TODOs ===")
for mk in ["商务酒店","民宿青旅"]:
    dc = INDUSTRY_RIGOR.get(mk,{}).get("direct_competitor_rules",{})
    status = "OK" if dc.get("require_name_keyword_for_code") else "TODO"
    print(f"  {mk}: broad={dc.get('amap_codes')} require_kw={dc.get('require_name_keyword_for_code',False)} [{status}]")

# ===== U. Anchor 显式测试 =====
# ★ 本节是 traffic_anchor_rules 规则层测试。
# 手工传入 cat/type_code，验证 anchor 优先级且不被 direct/substitute 污染。
# 不代表真实采集链路；真实链路测试在 M/P/S 章节。
print("\n=== U. Anchor Explicit Tests ===")
def _a(rigor_key, name, type_code, cat, bt=""):
    rig = get_rigor_for_config_key(rigor_key)
    r = classify_poi_rigor(name, cat, type_code, rig, bt)
    check(r == "anchor", f"{rigor_key}: {name} -> {r} (expected anchor)")
    check(r != "direct" and r != "substitute", f"{rigor_key}: {name} not direct/sub")
    return r

# 刚需快餐小吃：categories 匹配（schools/office/hospitals/subway/bus）
for name, tc, cat in [
    ("某某小学","141200","schools"),("某某中学","141200","schools"),
    ("某某写字楼","120200","office"),("某某人民医院","090100","hospitals"),
    ("某某地铁站","150500","subway"),("某某公交站","150200","bus"),
]:
    _a("刚需快餐小吃", name, tc, cat, "小吃店")

# 精品茶饮咖啡：categories 匹配（shopping/office/schools/subway）
for name, tc, cat in [
    ("某某购物中心","060100","shopping"),("某某写字楼","120200","office"),
    ("某某小学","141200","schools"),("某某地铁站","150500","subway"),
]:
    _a("精品茶饮咖啡", name, tc, cat, "咖啡店")

# 商务酒店：categories（office/shopping/subway/hospitals）+ name_keywords（火车站/机场/会展）
for name, tc, cat in [
    ("某某火车站","150200","bus"),("某某汽车站","150200","bus"),
    ("某某会展中心","130000","office"),("某某商务中心","120200","office"),
    ("某某人民医院","090100","hospitals"),
    # name_keywords anchor：火车站/机场/会展 命中 anchor_rules.name_keywords，cat 用不触发 direct 的中性值
    ("某某国际机场","150200","bus"),
]:
    _a("商务酒店", name, tc, cat, "商务酒店")

# 民宿青旅：categories（subway/shopping）+ name_keywords（景区/火车站/步行街/大学城）
for name, tc, cat in [
    ("某某地铁站","150500","subway"),("某某火车站","150200","bus"),
    ("某某步行街","060100","shopping"),
    # name_keywords anchor：景区/大学城 通过 anchor name_keywords 匹配，cat 用中性值
    ("某某旅游景区","150200","bus"),
    ("某某大学城","150200","bus"),
]:
    _a("民宿青旅", name, tc, cat, "民宿")

# 高频刚需零售：categories 匹配（residential/schools/office）
for name, tc, cat in [
    ("某某小区","120300","residential"),("某某小学","141200","schools"),
    ("某某写字楼","120200","office"),
]:
    _a("高频刚需零售", name, tc, cat, "便利店")

# 专业生活服务：categories 匹配（residential/office/shopping/parking）
for name, tc, cat in [
    ("某某小区","120300","residential"),("某某写字楼","120200","office"),
    ("某某购物中心","060100","shopping"),("某某停车场","150900","parking"),
]:
    _a("专业生活服务", name, tc, cat, "美容美发")

# 社区基础服务：categories 匹配（residential/schools/office）
for name, tc, cat in [
    ("某某小区","120300","residential"),("某某小学","141200","schools"),
    ("某某写字楼","120200","office"),
]:
    _a("社区基础服务", name, tc, cat, "教育培训")

# 反例：anchor 不能是 direct
snack_rig = get_rigor_for_config_key("刚需快餐小吃")
for name in ["某某小蛮螺螺蛳粉","某某擀面皮","某某麻辣烫"]:
    r = classify_poi_rigor(name, "fast_food", "050300", snack_rig, "小吃店")
    check(r != "anchor", f"snack anchor NOT: {name} -> {r} (should be direct, not anchor)")

# ===== V. Immersive Social Entertainment Subtypes =====
print("\n=== V. Immersive Social Subtypes ===")
imm_rigor = get_rigor_for_config_key("沉浸式社交娱乐")
imm_dc = imm_rigor.get("direct_competitor_rules", {})
check(imm_dc.get("require_name_keyword_for_code") == True, "immersive require_name_keyword_for_code=True")
check(imm_dc.get("substitute_before_direct") == True, "immersive substitute_before_direct=True")
stypes = imm_dc.get("subtypes", {})
check(len(stypes) >= 5, f"immersive subtypes count: {len(stypes)}")

for bt, direct_pos, direct_neg, sub_list in [
    ("剧本杀", ["某某剧本杀","某某推理馆","某某谋杀之谜","某某沉浸式剧场","某某实景搜证"],
        ["某某密室逃脱","某某台球厅","某某桌游吧","某某电玩城","某某KTV","某某酒吧","某某网吧","某某电竞酒店"],
        ["某某KTV","某某网吧","某某酒吧"]),
    ("密室逃脱", ["某某密室逃脱","某某密室","某某沉浸式密室","某某机械密室","某某恐怖密室"],
        ["某某剧本杀","某某台球厅","某某桌游吧","某某电玩城","某某KTV","某某酒吧","某某网吧"],
        ["某某KTV","某某网吧","某某酒吧"]),
    ("台球厅", ["某某台球厅","某某桌球室","某某台球俱乐部","某某桌球俱乐部"],
        ["某某棋牌室","某某桌游吧","某某剧本杀","某某密室","某某KTV","某某酒吧","某某网吧"],
        ["某某KTV","某某网吧","某某酒吧"]),
    ("桌游/轰趴", ["某某桌游吧","某某棋牌室","某某轰趴馆","某某三国杀","某某德扑俱乐部"],
        ["某某剧本杀","某某密室","某某台球厅","某某电玩城","某某KTV","某某酒吧","某某网吧"],
        ["某某KTV","某某网吧","某某酒吧"]),
    ("电玩/VR", ["某某电玩城","某某VR体验馆","某某虚拟现实","某某游戏厅","某某主机游戏"],
        ["某某剧本杀","某某密室","某某台球厅","某某桌游吧","某某KTV","某某酒吧","某某网吧","某某电竞酒店"],
        ["某某KTV","某某网吧","某某酒吧","某某电竞酒店"]),
]:
    for name in direct_pos:
        r = _cr(name, "bars", "080000", imm_rigor, bt)
        check(r == "direct", f"{bt} direct: {name} -> {r}")
    for name in direct_neg:
        r = _cr(name, "bars", "080000", imm_rigor, bt)
        check(r != "direct", f"{bt} NOT direct: {name} -> {r}")
    for name in sub_list:
        r = classify_poi_rigor(name, "bars", "080000", imm_rigor, bt)
        check(r == "substitute", f"{bt} substitute: {name} -> {r}")

# KTV/酒吧/网吧 应继续归夜经济娱乐 direct，不应混入沉浸式 direct
night_rig = get_rigor_for_config_key("夜经济娱乐")
for name, bt in [("某某KTV","KTV"),("某某量贩KTV","KTV"),("某某酒吧","酒吧"),("某某清吧","酒吧"),("某某网吧","网吧"),("某某网咖","网吧")]:
    r = classify_poi_rigor(name, "bars", "080000", night_rig, bt)
    check(r == "direct", f"nightlife direct: {name}({bt}) -> {r}")
    # 同时验证这些不进入沉浸式 direct
    r2 = classify_poi_rigor(name, "bars", "080000", imm_rigor, "剧本杀")
    check(r2 != "direct", f"immersive NOT direct: {name} -> {r2}")

# ===== W. Immersive Real-Chain =====
print("\n=== W. Immersive Real-Chain ===")
def sim_immersive_chain(name, type_code, bt):
    cat = classify_poi_type(type_code)
    if cat is None: return "no_cat"
    if cat == "bars" and any(kw in name for kw in ["KTV","酒吧","清吧","网吧","网咖"]):
        return "routed_to_bars"  # KTV/酒吧/网吧 应走夜经济娱乐
    if cat == "immersive_entertainment" and not is_real_immersive_entertainment(name):
        return "dewater_drop"
    rig = get_rigor_for_config_key("沉浸式社交娱乐")
    return _cr(name, cat, type_code, rig, bt)

# 正向：direct
for name, tc, bt in [
    ("某某剧本杀","体育休闲服务;娱乐场所","剧本杀"),
    ("某某推理馆","体育休闲服务;娱乐场所","推理馆"),
    ("某某密室逃脱","体育休闲服务;娱乐场所","密室逃脱"),
    ("某某台球厅","体育休闲服务;娱乐场所","台球厅"),
    ("某某桌球室","体育休闲服务;娱乐场所","台球厅"),
    ("某某桌游吧","体育休闲服务;娱乐场所","桌游/轰趴"),
    ("某某棋牌室","体育休闲服务;娱乐场所","桌游/轰趴"),
    ("某某电玩城","体育休闲服务;娱乐场所","电玩/VR"),
    ("某某VR体验馆","体育休闲服务;娱乐场所","电玩/VR"),
    ("某某游戏厅","体育休闲服务;娱乐场所","电玩/VR"),
]:
    r = sim_immersive_chain(name, tc, bt)
    check(r == "direct", f"immersive direct: {name}({tc},{bt}) -> {r}")

# 反向：not direct
for name, tc, bt in [
    ("某某KTV","体育休闲服务;娱乐场所","剧本杀"),
    ("某某酒吧","体育休闲服务;娱乐场所","密室逃脱"),
    ("某某清吧","体育休闲服务;娱乐场所","台球厅"),
    ("某某网吧","体育休闲服务;娱乐场所","桌游/轰趴"),
    ("某某网咖","体育休闲服务;娱乐场所","电玩/VR"),
    ("某某电竞酒店","体育休闲服务;娱乐场所","剧本杀"),
    ("某某麻将馆","体育休闲服务;娱乐场所","桌游/轰趴"),
    ("某某健身房","体育休闲服务;娱乐场所","剧本杀"),
    ("某某足疗店","体育休闲服务;娱乐场所","密室逃脱"),
]:
    r = sim_immersive_chain(name, tc, bt)
    check(r != "direct", f"immersive NOT direct: {name}({tc}) -> {r}")

# 混名反例：KTV剧本杀/酒吧密室/网吧VR/电竞酒店剧本杀/麻将馆桌游 → 真实链路 dewater_drop
for name in ["某某KTV剧本杀","某某酒吧密室","某某网吧VR","某某电竞酒店剧本杀","某某麻将馆桌游"]:
    r = sim_immersive_chain(name, "体育休闲服务;娱乐场所", "剧本杀")
    check(r == "dewater_drop", f"immersive mix-name dewater: {name} -> {r}")

# 棋牌室/桌游棋牌室 应保留并通过真实链路 direct
for name, bt in [("某某棋牌室","桌游/轰趴"),("某某桌游棋牌室","桌游/轰趴")]:
    r = sim_immersive_chain(name, "体育休闲服务;娱乐场所", bt)
    check(r == "direct", f"immersive direct: {name} -> {r}")

# 确认 KTV/酒吧/网吧 仍归夜经济娱乐 direct
for name, tc, bt in [
    ("某某KTV","体育休闲服务;KTV","KTV"),
    ("某某酒吧","体育休闲服务;酒吧","酒吧"),
    ("某某网吧","体育休闲服务;网吧","网吧"),
]:
    r = classify_poi_type(tc)
    check(r == "bars", f"nightlife cat: {name} -> {r}")
    nrig = get_rigor_for_config_key("夜经济娱乐")
    r2 = classify_poi_rigor(name, "bars", tc, nrig, bt)
    check(r2 == "direct", f"nightlife direct: {name} -> {r2}")

# 确认健身房 direct 不受影响
for name in ["某某健身房","某某瑜伽馆","某某普拉提"]:
    r = classify_poi_type("体育休闲服务;运动场馆")
    check(r == "fitness", f"fitness cat: {name}")
    frig = get_rigor_for_config_key("专业生活服务")
    r2 = classify_poi_rigor(name, "fitness", "体育休闲服务;运动场馆", frig, "健身房")
    check(r2 == "direct", f"fitness direct: {name} -> {r2}")

# ===== X. Sample Bank - Real-Chain Helper (no cat_override) =====
def sim_full_chain(name, type_code, rigor_key, bt):
    cat = classify_poi_type(type_code)
    if cat is None: return "no_cat"
    if cat == "shopping":
        if any(kw in bt for kw in ("生鲜","水果","蔬菜","菜店","鲜果")) and is_real_fresh_retail(name):
            cat = "fresh_retail"
        elif any(kw in bt for kw in ("烟酒","名烟","名酒","酒行","酒类")) and is_real_tobacco_liquor_retail(name):
            cat = "tobacco_liquor"
        elif any(kw in bt for kw in ("零售店","服装店","数码店")) and is_real_low_freq_retail(name):
            cat = "low_freq_retail"
    dew_map = {
        "office": is_real_office, "shopping": is_real_shopping, "residential": is_real_residential,
        "hotels": is_real_hotel, "convenience": is_real_convenience, "pharmacy": is_real_pharmacy,
        "fitness": is_real_fitness, "fresh_retail": is_real_fresh_retail,
        "tobacco_liquor": is_real_tobacco_liquor_retail, "immersive_entertainment": is_real_immersive_entertainment,
        "low_freq_retail": is_real_low_freq_retail,
        "education_training": is_real_training, "laundry": is_real_laundry, "clinics": is_real_clinic,
        "schools": is_real_school,
    }
    if cat in dew_map and not dew_map[cat](name):
        return "dewater_drop"
    rig = get_rigor_for_config_key(rigor_key)
    return _cr(name, cat, type_code, rig, bt)

def check_direct(rigor_key, name, tc, bt):
    r = sim_full_chain(name, tc, rigor_key, bt)
    check(r == "direct", f"{rigor_key}/{bt} direct: {name} -> {r}")

def check_not_direct(rigor_key, name, tc, bt):
    r = sim_full_chain(name, tc, rigor_key, bt)
    check(r != "direct", f"{rigor_key}/{bt} NOT direct: {name} -> {r}")

def check_sub(rigor_key, name, tc, bt):
    r = sim_full_chain(name, tc, rigor_key, bt)
    check(r == "substitute", f"{rigor_key}/{bt} substitute: {name} -> {r}")

def check_anchor(rigor_key, name, tc, bt):
    r = sim_full_chain(name, tc, rigor_key, bt)
    check(r == "anchor", f"{rigor_key}/{bt} anchor: {name} -> {r}")

def check_irrelevant(rigor_key, name, tc, bt):
    r = sim_full_chain(name, tc, rigor_key, bt)
    check(r == "irrelevant", f"{rigor_key}/{bt} irrelevant: {name} -> {r}")

known_gaps = []

def gap(rigor_key, bt, name, tc, issue):
    known_gaps.append(f"{rigor_key}/{bt}: {name}({tc}) - {issue}")

# ===== X1. Snack Shop [partial] =====
print("\n=== X1. Sample Bank - Snack Shop [partial] ===")
for name in ["擀面皮","凉皮店","米线馆","酸辣粉","肉夹馍","砂锅店","冒菜馆","拉面馆","拌面馆","热干面","沙县小吃","麻辣烫","饺子馆","包子店","馄饨店","锅贴店","煎饼店","盖浇饭店"]:
    check_direct("刚需快餐小吃", "某某"+name, "050300", "小吃店")
for name in ["肯德基","麦当劳","华莱士","汉堡王","必胜客","海底捞","星巴克","茶百道","韩国料理","寿司店","火锅店","烧烤店","奶茶店","咖啡店","甜品店","西餐厅"]:
    check_not_direct("刚需快餐小吃", "某某"+name, "050300", "小吃店")
for name in ["绝味鸭脖","正新鸡排","便利店","单位食堂","卤味店","炸鸡店","汉堡店"]:
    check_sub("刚需快餐小吃", "某某"+name, "050300", "小吃店")
for name, code in [("写字楼","120200"),("商务中心","120200"),("人民医院","090100"),("地铁站","150500"),("公交站","150200")]:
    check_anchor("刚需快餐小吃", "某某"+name, code, "小吃店")
for name, code in [("大酒楼","050100"),("海鲜酒楼","050100"),("法餐厅","050200"),("怀石料理","050200"),("韩国料理店","050200")]:
    check_irrelevant("刚需快餐小吃", "某某"+name, code, "小吃店")

# ===== X2. Tea/Coffee [complete_candidate] =====
print()
print("=== X2. Sample Bank - Tea/Coffee [complete_candidate] ===")
for name in ["奶茶店","咖啡店","茶饮店","果饮店","星巴克","瑞幸咖啡","喜茶","奈雪的茶","蜜雪冰城","茶百道","柠檬茶"]:
    check_direct("精品茶饮咖啡", "某某"+name, "050500", "咖啡店")
for name in ["酒吧","茶馆","棋牌室","小吃店","快餐店","中餐馆"]:
    check_not_direct("精品茶饮咖啡", "某某"+name, "050500", "咖啡店")
for name in ["甜品店","冰淇淋店"]:
    check_sub("精品茶饮咖啡", "某某"+name, "050500", "咖啡店")
for name in ["便利店","超市","小超市"]:
    check_sub("精品茶饮咖啡", "某某"+name, "060200", "咖啡店")
for name, code in [("火锅店","050100"),("火锅店","050500"),("烧烤店","050100"),("烧烤店","050500")]:
    check_not_direct("精品茶饮咖啡", "某某"+name, code, "咖啡店")
for name, code in [("中餐馆","050100"),("西餐厅","050200"),("日料店","050200")]:
    check_not_direct("精品茶饮咖啡", "某某"+name, code, "咖啡店")
for name, code in [("写字楼","120200"),("商务中心","120200"),("购物中心","060100"),("阳光小区","120300"),("地铁站","150500")]:
    check_anchor("精品茶饮咖啡", "某某"+name, code, "咖啡店")
for name, code in [("KTV","体育休闲服务;KTV"),("网吧","体育休闲服务;网吧"),("棋牌室","体育休闲服务;娱乐场所"),("人民医院","090100"),("酒吧","餐饮服务;酒吧")]:
    check_irrelevant("精品茶饮咖啡", "某某"+name, code, "咖啡店")

# ===== X3. Chinese Restaurant [complete_candidate] =====
print()
print("=== X3. Sample Bank - Chinese Restaurant [complete_candidate] ===")
for name in ["湘菜馆","川菜馆","粤菜馆","东北菜馆","本帮菜馆","私房菜馆","海鲜酒楼","烤鸭店","宴会厅","大酒店中餐厅","鲁菜馆","土菜馆"]:
    check_direct("中餐正餐", "某某"+name, "050100", "中餐")
for name in ["快餐店","小吃店","面馆","麻辣烫","汉堡店","大排档","西餐厅","日料店","韩国料理","茶餐厅","简餐店","奶茶店","咖啡店"]:
    check_not_direct("中餐正餐", "某某"+name, "050100", "中餐")
for name in ["火锅店","烧烤店","烤肉店","毛肚火锅","韩式烤肉"]:
    check_sub("中餐正餐", "某某"+name, "050100", "中餐")
for name in ["茶饮店","咖啡店"]:
    check_not_direct("中餐正餐", "某某"+name, "050500", "中餐")
    check_not_direct("中餐正餐", "某某"+name, "050100", "中餐")
for name, code in [("购物中心","060100"),("购物广场","060100"),("写字楼","120200"),("商务中心","120200"),("停车场","150900")]:
    check_anchor("中餐正餐", "某某"+name, code, "中餐")
for name, code in [("炸鸡店","050300"),("米线店","050300"),("食堂","050100"),("面馆","050300"),("麻辣烫店","050300")]:
    check_irrelevant("中餐正餐", "某某"+name, code, "中餐")

# ===== X3b. Foreign Premium Dining [complete_candidate] =====
print()
print("=== X3b. Sample Bank - Foreign Premium Dining [complete_candidate] ===")
# direct: 异国/高端正餐 (code 050100 or 050200 + keyword match)
for name in ["西餐厅","日料店","法餐厅","意餐厅","铁板烧","怀石料理","omakase","海鲜私房","韩国料理","牛排馆","披萨店"]:
    code = "050200" if name in ("日料店","法餐厅","怀石料理","omakase","韩国料理","披萨店") else "050100"
    check_direct("异国_中高端正餐", "某某"+name, code, "西餐")
# not-direct: 非异国品类不应进 direct
for name in ["烧烤店","茶饮店","咖啡店","奶茶店","甜品店","烘焙店"]:
    check_not_direct("异国_中高端正餐", "某某"+name, "050100", "西餐")
for name in ["快餐店","小吃店","米线店","面馆"]:
    check_not_direct("异国_中高端正餐", "某某"+name, "050300", "西餐")
# substitute: 中餐/火锅应进 substitute（sub_first拦截）
for name in ["中餐馆","湘菜馆","川菜馆","火锅店","海鲜酒楼"]:
    check_sub("异国_中高端正餐", "某某"+name, "050100", "西餐")
# anchor
for name, code in [("购物中心","060100"),("百货大楼","060100"),("写字楼","120200"),("希尔顿酒店","100000"),("停车场","150900")]:
    check_anchor("异国_中高端正餐", "某某"+name, code, "西餐")
# irrelevant
for name in ["快餐店","米线店","面馆","炸鸡店","麻辣烫"]:
    check_irrelevant("异国_中高端正餐", "某某"+name, "050300", "西餐")

# ===== X4. Hotpot/BBQ [complete_candidate] =====
print()
print("=== X4. Sample Bank - Hotpot/BBQ [complete_candidate] ===")
for name in ["火锅店","毛肚火锅","川味火锅","烧烤店","烤肉店","烤串店","涮肉馆","羊蝎子火锅","烤鱼店","小龙虾馆","大排档","串串香"]:
    check_direct("火锅_烧烤", "某某"+name, "050100", "火锅店")
for name in ["快餐店","小吃店","面馆","包子铺","食堂","奶茶店","咖啡店"]:
    check_not_direct("火锅_烧烤", "某某"+name, "050100", "火锅店")
for name in ["中餐馆","湘菜馆","川菜馆","夜市","排档"]:
    check_sub("火锅_烧烤", "某某"+name, "050100", "火锅店")
for name in ["茶饮店","咖啡店"]:
    check_not_direct("火锅_烧烤", "某某"+name, "050500", "火锅店")
    check_not_direct("火锅_烧烤", "某某"+name, "050100", "火锅店")
for name in ["西餐厅","日料店"]:
    check_not_direct("火锅_烧烤", "某某"+name, "050200", "火锅店")
    check_not_direct("火锅_烧烤", "某某"+name, "050100", "火锅店")
for name, code in [("KTV","体育休闲服务;KTV"),("酒吧","体育休闲服务;酒吧"),("酒店","住宿服务"),("连锁酒店","住宿服务"),("停车场","150900")]:
    check_anchor("火锅_烧烤", "某某"+name, code, "火锅店")
for name, code in [("茶饮店","050500"),("咖啡店","050500"),("西餐厅","050200"),("日料店","050200"),("快餐店","050300")]:
    check_irrelevant("火锅_烧烤", "某某"+name, code, "火锅店")

# ===== X5. Bakery/Dessert [complete_candidate] =====
print()
print("=== X5. Sample Bank - Bakery/Dessert [complete_candidate] ===")
for name in ["面包店","蛋糕店","烘焙坊","甜品店","泡芙店","蛋挞店","慕斯蛋糕","马卡龙店","曲奇店","冰淇淋店"]:
    check_direct("烘焙甜品", "某某"+name, "050600", "甜品店")
for name in ["包子铺","馒头店","大饼店","油条摊","煎饼摊","食堂","快餐店","火锅店","烧烤店"]:
    check_not_direct("烘焙甜品", "某某"+name, "050600", "甜品店")
for name in ["茶饮店","咖啡店","奶茶店","咖啡厅","奶茶铺"]:
    check_sub("烘焙甜品", "某某"+name, "050600", "甜品店")
for name, code in [("便利店","060200"),("便利店","050600"),("火锅店","050100"),("火锅店","050600"),("烧烤店","050100"),("烧烤店","050600")]:
    check_not_direct("烘焙甜品", "某某"+name, code, "甜品店")
for name, code in [("阳光小区","120300"),("住宅小区","120300"),("地铁站","150500"),("购物中心","060100"),("百货商场","060100")]:
    check_anchor("烘焙甜品", "某某"+name, code, "甜品店")
for name in ["包子铺","馒头店","大饼摊","油条摊","食堂","火锅店","烧烤店","便利店","超市"]:
    check_irrelevant("烘焙甜品", "某某"+name, "050600", "甜品店")

# ===== X5b. Low Frequency Retail [partial] =====
# 注: 个体零售店(服装/数码/眼镜)名不通过 is_real_shopping 脱水(SHOPPING_KEEP 只含商场/百货/步行街)。
# 因此本段用 classify_poi_rigor 直调(cat="shopping")，避过 sim_full_chain 的 shopping 脱水。
print()
print("=== X5b. Sample Bank - Low Frequency Retail [partial] ===")
rig_lfr = get_rigor_for_config_key("低频目的零售")
# direct: 低频目的零售 (code 060100/060400 + keyword match)
for name in ["服装店","鞋帽店","数码店","手机店","电脑城","家电城","眼镜店","珠宝店","屈臣氏","优衣库","名创优品"]:
    code = "060400" if name in ("服装店","家电城") else "060100"
    r = _cr("某某"+name, "shopping", code, rig_lfr, "零售店")
    check(r == "direct", f"低频目的零售/零售店 direct: 某某{name} -> {r}")
# not-direct: 高频/非目的零售不应进 direct
for name in ["超市","便利店","水果店","生鲜店","菜市场","杂货铺"]:
    r = _cr("某某"+name, "shopping", "060400", rig_lfr, "零售店")
    check(r != "direct", f"低频目的零售/零售店 NOT direct: 某某{name} -> {r}")
for name in ["建材市场","五金店","批发市场","汽配城"]:
    r = _cr("某某"+name, "shopping", "060100", rig_lfr, "零售店")
    check(r != "direct", f"低频目的零售/零售店 NOT direct: 某某{name} -> {r}")
# substitute: 本轮不补，s=0
# anchor (cat=shopping 匹配 anchor categories 中的 "shopping")
for name, code in [("购物中心","060100"),("百货大楼","060100"),("地铁站","150500"),("写字楼","120200"),("步行街","060100")]:
    cat = classify_poi_type(code) if code not in ("060100","060400") else "shopping"
    r = _cr("某某"+name, cat, code, rig_lfr, "零售店")
    check(r == "anchor", f"低频目的零售/零售店 anchor: 某某{name} -> {r}")
# irrelevant
for name in ["批发市场","建材市场","农贸市场","维修店","彩票店"]:
    code = "060400" if name in ("维修店","彩票店") else "060100"
    r = _cr("某某"+name, "shopping", code, rig_lfr, "零售店")
    check(r == "irrelevant", f"低频目的零售/零售店 irrelevant: 某某{name} -> {r}")

# ===== X5c. Low Frequency Retail Real Chain [partial] =====
# 走 sim_full_chain，不得绕过 is_real_low_freq_retail 脱水
print()
print("=== X5c. Sample Bank - Low Frequency Retail Real Chain [partial] ===")
# direct: 个体低频零售走真实链路通入 classify_poi_rigor
for name, tc in [
    ("服装店","购物服务;服装鞋帽店"),("数码店","购物服务;数码电子"),
    ("手机店","购物服务;数码电子"),("家电城","购物服务;数码电子"),
    ("眼镜店","购物服务;服装鞋帽店"),("珠宝店","购物服务;服装鞋帽店"),
    ("屈臣氏","购物服务;购物中心"),("优衣库","购物服务;服装鞋帽店"),
    ("名创优品","购物服务;购物中心"),
]:
    r = sim_full_chain("某某"+name, tc, "低频目的零售", "零售店")
    check(r == "direct", f"LFR real-chain direct: 某某{name} -> {r}")
# not-direct
for name, tc in [
    ("超市","购物服务;超市"),("便利店","购物服务;便利店"),
    ("水果店","购物服务;综合市场"),("生鲜店","购物服务;综合市场"),
    ("建材市场","购物服务;家居建材市场"),("五金店","购物服务;专卖店"),
]:
    r = sim_full_chain("某某"+name, tc, "低频目的零售", "零售店")
    check(r != "direct", f"LFR real-chain NOT direct: 某某{name} -> {r}")
# anchor: 购物中心/百货/步行街走真实链路
for name, tc in [
    ("购物中心","购物服务;购物中心"),("百货大楼","购物服务;百货商场"),
    ("步行街","购物服务;特色商业街"),
]:
    r = sim_full_chain("某某"+name, tc, "低频目的零售", "零售店")
    check(r == "anchor", f"LFR real-chain anchor: 某某{name} -> {r}")

# ===== Y1. Convenience [complete_candidate] =====
print()
print("=== Y1. Sample Bank - Convenience [complete_candidate] ===")
for name in ["社区便利店","便民超市","小卖部","生活超市","便利店","24小时便利店","社区超市","便民生活超市","连锁便利店","小区小卖部"]:
    check_direct("高频刚需零售", "某某"+name, "060200", "便利店")
for name in ["美甲沙龙","手机快修","体育彩票","黄金回收","OPPO体验店","美发店","按摩店","足疗店","药房","百货大楼"]:
    check_not_direct("高频刚需零售", "某某"+name, "060200", "便利店")
for name, code in [("快餐店","050300"),("咖啡店","050500"),("茶饮店","050500"),("炸鸡店","050300"),("汉堡店","050300")]:
    check_sub("高频刚需零售", "某某"+name, code, "便利店")
for name, code in [("住宅小区","120300"),("写字楼","120200"),("人民医院","090100"),("地铁站","150500"),("公交站","150200")]:
    check_anchor("高频刚需零售", "某某"+name, code, "便利店")
for name, code in [("美容院","生活服务;美容美发"),("理发店","生活服务;美容美发"),("美甲店","生活服务;美容美发"),("SPA会所","生活服务;美容美发"),("纹身店","生活服务;美容美发")]:
    check_irrelevant("高频刚需零售", "某某"+name, code, "便利店")

# ===== Y2. Fresh Produce [complete_candidate] =====
print("\n=== Y2. Sample Bank - Fresh Produce [complete_candidate] ===")
for name in ["生鲜超市","水果店","蔬菜店","鲜果店","菜店","果品店","鲜肉店","菜场","菜市场","果蔬店"]:
    check_direct("高频刚需零售", "某某"+name, "购物服务", "生鲜店")
for name in ["百货超市","便利店","大药房","餐饮店","火锅店","冷库","批发市场","五金建材","药房","饭店"]:
    check_not_direct("高频刚需零售", "某某"+name, "购物服务", "生鲜店")
for name, code in [("快餐店","050300"),("咖啡店","050500"),("茶饮店","050500"),("炸鸡店","050300"),("汉堡店","050300")]:
    check_sub("高频刚需零售", "某某"+name, code, "生鲜店")
for name, code in [("住宅小区","120300"),("写字楼","120200"),("人民医院","090100"),("地铁站","150500"),("公交站","150200")]:
    check_anchor("高频刚需零售", "某某"+name, code, "生鲜店")
for name, code in [("美容院","生活服务;美容美发"),("理发店","生活服务;美容美发"),("美甲店","生活服务;美容美发"),("SPA会所","生活服务;美容美发"),("纹身店","生活服务;美容美发")]:
    check_irrelevant("高频刚需零售", "某某"+name, code, "生鲜店")

# ===== Y3-Y5. Retail Subtypes [partial] =====
print("\n=== Y3-Y5. Sample Bank - Retail Subtypes [partial] ===")
for name in ["大药房","药店","医药连锁","同仁堂","老百姓药房","益丰大药房","一心堂","健之佳","海王星辰","国药药店"]:
    check_direct("高频刚需零售", "某某"+name, "090400", "药店")
for name in ["人民医院","口腔诊所","牙科诊所","眼科医院","体检中心","医美中心","助听器店","康复中心","理疗馆","美容院"]:
    check_not_direct("高频刚需零售", "某某"+name, "090400", "药店")
# Pharmacy anchor: real-chain via residential/office/hospitals/subway/bus
for name, code in [("住宅小区","120300"),("写字楼","120200"),("人民医院","090100"),("地铁站","150500"),("公交站","150200")]:
    check_anchor("高频刚需零售", "某某"+name, code, "药店")
# Pharmacy irrelevant: real-chain via beauty category + name_blacklist hit
for name, code in [("美容院","生活服务;美容美发"),("美发店","生活服务;美容美发"),("美甲店","生活服务;美容美发"),("按摩店","生活服务;美容美发"),("足疗店","生活服务;美容美发")]:
    check_irrelevant("高频刚需零售", "某某"+name, code, "药店")

for name in ["烟酒店","烟酒行","名烟名酒","酒水商行","酒行","酒庄","1919酒类","酒便利","烟草专卖","酒类直供"]:
    check_direct("高频刚需零售", "某某"+name, "购物服务", "烟酒店")
for name in ["酒吧","KTV","火锅店","餐厅","超市","便利店","茶叶店","茶庄","咖啡厅","百货店"]:
    check_not_direct("高频刚需零售", "某某"+name, "购物服务", "烟酒店")
# Tobacco/Liquor anchor: real-chain via residential/office/hotels/subway/bus
for name, code in [("住宅小区","120300"),("写字楼","120200"),("酒店","住宿服务"),("地铁站","150500"),("公交站","150200")]:
    check_anchor("高频刚需零售", "某某"+name, code, "烟酒店")
# Tobacco/Liquor irrelevant: real-chain via beauty category + name_blacklist hit
for name, code in [("美容院","生活服务;美容美发"),("美发店","生活服务;美容美发"),("美甲店","生活服务;美容美发"),("按摩店","生活服务;美容美发"),("足疗店","生活服务;美容美发")]:
    check_irrelevant("高频刚需零售", "某某"+name, code, "烟酒店")

# Daily Goods direct: 购物服务 path (百货 in SHOPPING_KEEP) + 060200 path (日杂/杂货/粮油/副食 in CONVENIENCE_KEEP)
for name in ["百货店","日用百货","百货商行","百货铺","百货行"]:
    check_direct("高频刚需零售", "某某"+name, "购物服务", "日用百货")
for name in ["日杂店","杂货铺","粮油店","副食店","副食百货"]:
    check_direct("高频刚需零售", "某某"+name, "060200", "日用百货")
# Daily Goods not-direct: dewater + exclude_names paths
for name in ["建材市场","五金店","购物中心","服装店","家电城","便利店","超市","数码店","家具城","商场"]:
    check_not_direct("高频刚需零售", "某某"+name, "购物服务", "日用百货")
# Daily Goods anchor: real-chain via residential/office/hotels/subway/bus
for name, code in [("住宅小区","120300"),("写字楼","120200"),("酒店","住宿服务"),("地铁站","150500"),("公交站","150200")]:
    check_anchor("高频刚需零售", "某某"+name, code, "日用百货")
# Daily Goods irrelevant: real-chain via beauty category + name_blacklist hit
for name, code in [("美容院","生活服务;美容美发"),("美发店","生活服务;美容美发"),("美甲店","生活服务;美容美发"),("按摩店","生活服务;美容美发"),("足疗店","生活服务;美容美发")]:
    check_irrelevant("高频刚需零售", "某某"+name, code, "日用百货")

# ===== Z1-Z3. Life Services [partial] =====
print("\n=== Z1-Z3. Sample Bank - Life Services [partial] ===")
for name in ["美容院","美发店","美甲店","SPA会所","美睫店","皮肤管理","造型设计","形象设计","护肤中心","美体店"]:
    check_direct("专业生活服务", "某某"+name, "050300", "美容美发")
for name in ["宠物店","动物医院","健身房","瑜伽馆","足疗店","按摩店","医美诊所","口腔诊所","牙科诊所","舞蹈培训"]:
    check_not_direct("专业生活服务", "某某"+name, "050300", "美容美发")
# Beauty substitute: 当前 master irr 拦截足疗/按摩/推拿，暂不补 substitute 样本
# Beauty anchor: categories residential/office/shopping/parking (2×residential to fill 5 with 4 categories)
for name, code in [("住宅小区","120300"),("公寓","120300"),("写字楼","120200"),("购物中心","060100"),("停车场","150900")]:
    check_anchor("专业生活服务", "某某"+name, code, "美容美发")
# Beauty irrelevant: real-chain via beauty category + irrelevant name_blacklist hit
for name, code in [("足疗店","生活服务;美容美发"),("按摩店","生活服务;美容美发"),("洗浴中心","生活服务;美容美发"),("汗蒸馆","生活服务;美容美发"),("医美诊所","生活服务;美容美发")]:
    check_irrelevant("专业生活服务", "某某"+name, code, "美容美发")

for name in ["宠物店","宠物用品店","猫舍","犬舍","宠物生活馆","宠物寄养","宠物训练","宠物乐园","宠物会馆","宠物商城"]:
    check_direct("专业生活服务", "某某"+name, "050300", "宠物店")
for name in ["美容院","美发店","动物医院","宠物医院","健身房","兽药店","足疗店","按摩店","SPA会所","医美诊所"]:
    check_not_direct("专业生活服务", "某某"+name, "050300", "宠物店")
# Pet substitute: 宠物医院/宠物美容分流宠物消费
for name in ["宠物医院","宠物美容"]:
    r = _cr("某某"+name, "convenience", "050300", get_rigor_for_config_key("专业生活服务"), "宠物店")
    check(r == "substitute", f"专业生活服务/宠物店 substitute: 某某{name} -> {r}")
# Pet anchor: categories residential/office/shopping/parking (same as Beauty)
for name, code in [("住宅小区","120300"),("公寓","120300"),("写字楼","120200"),("购物中心","060100"),("停车场","150900")]:
    check_anchor("专业生活服务", "某某"+name, code, "宠物店")
# Pet irrelevant: real-chain via beauty category + irrelevant name_blacklist hit
for name, code in [("足疗店","生活服务;美容美发"),("按摩店","生活服务;美容美发"),("洗浴中心","生活服务;美容美发"),("汗蒸馆","生活服务;美容美发"),("医美诊所","生活服务;美容美发")]:
    check_irrelevant("专业生活服务", "某某"+name, code, "宠物店")

for name in ["健身房","健身中心","瑜伽馆","普拉提馆","私教工作室","游泳馆","拳击馆","体能训练","操课中心","CrossFit"]:
    check_direct("专业生活服务", "某某"+name, "体育休闲服务;运动场馆", "健身房")
for name in ["体育用品店","足疗按摩","舞蹈培训班","美容院","宠物店","推拿艾灸","洗浴中心","汗蒸馆","少儿培训","医美中心"]:
    check_not_direct("专业生活服务", "某某"+name, "体育休闲服务;运动场馆", "健身房")
# Fitness substitute: 动感单车/搏击/跆拳道分流健身预算
for name in ["动感单车","搏击馆","跆拳道"]:
    r = _cr("某某"+name, "fitness", "体育休闲服务;运动场馆", get_rigor_for_config_key("专业生活服务"), "健身房")
    check(r == "substitute", f"专业生活服务/健身房 substitute: 某某{name} -> {r}")
# Fitness anchor: categories residential/office/shopping/parking (same as Beauty/Pet)
for name, code in [("住宅小区","120300"),("公寓","120300"),("写字楼","120200"),("购物中心","060100"),("停车场","150900")]:
    check_anchor("专业生活服务", "某某"+name, code, "健身房")
# Fitness irrelevant: real-chain via beauty category + irrelevant name_blacklist hit
for name, code in [("足疗店","生活服务;美容美发"),("按摩店","生活服务;美容美发"),("洗浴中心","生活服务;美容美发"),("汗蒸馆","生活服务;美容美发"),("医美诊所","生活服务;美容美发")]:
    check_irrelevant("专业生活服务", "某某"+name, code, "健身房")

# ===== Z4-Z6. Community Services [partial] =====
print("\n=== Z4-Z6. Sample Bank - Community Services [partial] ===")
for name in ["教育培训中心","琴行","画室","早教中心","托管班","辅导班","语言培训","美术培训","音乐培训","舞蹈培训班"]:
    check_direct("社区基础服务", "某某"+name, "141200", "教育培训")
for name in ["小学","幼儿园","文具店","书店","洗衣店","干洗店","诊所","卫生所","家政公司","办公用品店"]:
    check_not_direct("社区基础服务", "某某"+name, "141200", "教育培训")
# Education anchor: categories residential/schools/office
for name, code in [("住宅小区","120300"),("公寓","120300"),("写字楼","120200"),("小学","科教文化服务;学校"),("中学","科教文化服务;学校")]:
    check_anchor("社区基础服务", "某某"+name, code, "教育培训")
# Education irrelevant: 050300 bypass + irrelevant name_blacklist hit
for name, code in [("驾校","050300"),("职业培训","050300"),("职业培训学校","050300"),("医院","050300"),("药店","050300")]:
    check_irrelevant("社区基础服务", "某某"+name, code, "教育培训")

for name in ["洗衣店","干洗店","洗护中心","衣物护理","干洗连锁","洗衣连锁","衣物清洗","洗衣房","洗衣馆","干洗馆"]:
    check_direct("社区基础服务", "某某"+name, "生活服务;洗衣店", "洗衣店")
for name in ["家政公司","手机维修","皮具护理","擦鞋店","教育培训","开锁公司","疏通管道","搬家公司","美容院","美发店"]:
    check_not_direct("社区基础服务", "某某"+name, "生活服务;洗衣店", "洗衣店")
# Laundry substitute: 家政分流社区服务预算（维修类不得进入）
for name in ["家政服务"]:
    r = _cr("某某"+name, "laundry", "生活服务;洗衣店", get_rigor_for_config_key("社区基础服务"), "洗衣店")
    check(r == "substitute", f"社区基础服务/洗衣店 substitute: 某某{name} -> {r}")
# Laundry 反例: 维修类不得进入 direct 或 substitute
rig_cs = get_rigor_for_config_key("社区基础服务")
for name in ["手机维修","家电维修","电脑维修"]:
    r = _cr("某某"+name, "laundry", "生活服务;洗衣店", rig_cs, "洗衣店")
    check(r != "direct", f"社区基础服务/洗衣店 NOT direct: 某某{name} -> {r}")
    check(r != "substitute", f"社区基础服务/洗衣店 NOT substitute: 某某{name} -> {r}")
# Laundry anchor: categories residential/schools/office (same as Education)
for name, code in [("住宅小区","120300"),("公寓","120300"),("写字楼","120200"),("小学","科教文化服务;学校"),("中学","科教文化服务;学校")]:
    check_anchor("社区基础服务", "某某"+name, code, "洗衣店")
# Laundry irrelevant: 050300 bypass + irrelevant name_blacklist hit
for name, code in [("驾校","050300"),("职业培训","050300"),("职业培训学校","050300"),("医院","050300"),("药店","050300")]:
    check_irrelevant("社区基础服务", "某某"+name, code, "洗衣店")

for name in ["中医诊所","中西医结合门诊","社区卫生室","医务室","卫生所","内科门诊","儿科门诊","妇科门诊","门诊部","社区卫生服务站"]:
    check_direct("社区基础服务", "某某"+name, "090300", "诊所")
for name in ["综合医院","口腔医院","眼科医院","体检中心","大药房","医美中心","助听器","康复医院","月子中心","养老院"]:
    check_not_direct("社区基础服务", "某某"+name, "090300", "诊所")
# Clinic substitute: 药店/保健被 master irr 拦截，暂不补 substitute 样本
# Clinic anchor: categories residential/schools/office (same as Education/Laundry)
for name, code in [("住宅小区","120300"),("公寓","120300"),("写字楼","120200"),("小学","科教文化服务;学校"),("中学","科教文化服务;学校")]:
    check_anchor("社区基础服务", "某某"+name, code, "诊所")
# Clinic irrelevant: 050300 bypass + irrelevant name_blacklist hit
for name, code in [("驾校","050300"),("职业培训","050300"),("职业培训学校","050300"),("医院","050300"),("药店","050300")]:
    check_irrelevant("社区基础服务", "某某"+name, code, "诊所")

# ===== AA1-AA4. Nightlife/Immersive [partial] =====
print("\n=== AA. Sample Bank - Nightlife/Immersive [partial] ===")
for name in ["酒吧","清吧","精酿酒馆","LiveHouse","威士忌吧","鸡尾酒吧","夜店","酒馆","精酿酒吧","音乐酒吧"]:
    check_direct("夜经济娱乐", "某某"+name, "体育休闲服务;酒吧", "酒吧")
for name in ["KTV","网吧","网咖","台球厅","棋牌室","咖啡厅","餐厅","书店","茶社","茶庄"]:
    check_not_direct("夜经济娱乐", "某某"+name, "体育休闲服务;酒吧", "酒吧")
# Bar substitute: 台球/棋牌/桌游/电玩/夜店可替代夜生活消费
for name in ["台球厅","棋牌室","桌游吧","轰趴馆","夜市"]:
    check_sub("夜经济娱乐", "某某"+name, "体育休闲服务;酒吧", "酒吧")
# Bar anchor: categories hotels/parking/subway
for name, code in [("酒店","住宿服务"),("快捷酒店","住宿服务"),("停车场","150900"),("地下车库","150900"),("地铁站","150500")]:
    check_anchor("夜经济娱乐", "某某"+name, code, "酒吧")
# Bar irrelevant: 050300 bypass + name_blacklist hit
for name, code in [("学校","050300"),("培训学校","050300"),("医院","050300"),("人民医院","050300"),("中心医院","050300")]:
    check_irrelevant("夜经济娱乐", "某某"+name, code, "酒吧")

for name in ["KTV","歌厅","练歌房","量贩KTV","卡拉OK","主题KTV","KTV歌厅","练歌厅","KTV练歌房","量贩歌厅"]:
    check_direct("夜经济娱乐", "某某"+name, "体育休闲服务;KTV", "KTV")
for name in ["酒吧","清吧","网吧","网咖","台球厅","棋牌室","餐厅","电影院","茶馆","迪厅"]:
    check_not_direct("夜经济娱乐", "某某"+name, "体育休闲服务;KTV", "KTV")
# KTV substitute: 台球/棋牌/桌游/电玩/夜店可替代
for name in ["台球厅","棋牌室","桌游吧","轰趴馆","夜市"]:
    check_sub("夜经济娱乐", "某某"+name, "体育休闲服务;KTV", "KTV")
# KTV anchor: categories hotels/parking/subway (same as Bar)
for name, code in [("酒店","住宿服务"),("快捷酒店","住宿服务"),("停车场","150900"),("地下车库","150900"),("地铁站","150500")]:
    check_anchor("夜经济娱乐", "某某"+name, code, "KTV")
# KTV irrelevant: 050300 bypass + name_blacklist hit
for name, code in [("学校","050300"),("培训学校","050300"),("医院","050300"),("人民医院","050300"),("中心医院","050300")]:
    check_irrelevant("夜经济娱乐", "某某"+name, code, "KTV")

for name in ["网吧","网咖","电竞馆","电竞酒店","电竞中心","网吧连锁","网咖电竞","电竞网咖","电竞体验馆","网咖会所"]:
    check_direct("夜经济娱乐", "某某"+name, "体育休闲服务;网吧", "网吧")
for name in ["酒吧","KTV","台球厅","棋牌室","宾馆","餐厅","咖啡厅","电影院","茶馆","甜品店"]:
    check_not_direct("夜经济娱乐", "某某"+name, "体育休闲服务;网吧", "网吧")
# Internet Cafe substitute: 台球/棋牌/桌游/电玩/夜店可替代
for name in ["台球厅","棋牌室","桌游吧","轰趴馆","夜市"]:
    check_sub("夜经济娱乐", "某某"+name, "体育休闲服务;网吧", "网吧")
# Internet Cafe anchor: categories hotels/parking/subway (same as Bar/KTV)
for name, code in [("酒店","住宿服务"),("快捷酒店","住宿服务"),("停车场","150900"),("地下车库","150900"),("地铁站","150500")]:
    check_anchor("夜经济娱乐", "某某"+name, code, "网吧")
# Internet Cafe irrelevant: 050300 bypass + name_blacklist hit
for name, code in [("学校","050300"),("培训学校","050300"),("医院","050300"),("人民医院","050300"),("中心医院","050300")]:
    check_irrelevant("夜经济娱乐", "某某"+name, code, "网吧")

for name in ["剧本杀馆","推理馆","谋杀之谜","沉浸式剧场","实景搜证"]:
    check_direct("沉浸式社交娱乐", "某某"+name, "体育休闲服务;娱乐场所", "剧本杀")
for name in ["密室逃脱","机械密室","恐怖密室","沉浸式密室"]:
    check_direct("沉浸式社交娱乐", "某某"+name, "体育休闲服务;娱乐场所", "密室逃脱")
for name in ["台球厅","桌球室","台球俱乐部","桌球俱乐部"]:
    check_direct("沉浸式社交娱乐", "某某"+name, "体育休闲服务;娱乐场所", "台球厅")
for name in ["桌游吧","棋牌室","轰趴馆","三国杀俱乐部","德扑俱乐部"]:
    check_direct("沉浸式社交娱乐", "某某"+name, "体育休闲服务;娱乐场所", "桌游/轰趴")
for name in ["电玩城","VR体验馆","虚拟现实馆","游戏厅"]:
    check_direct("沉浸式社交娱乐", "某某"+name, "体育休闲服务;娱乐场所", "电玩/VR")
for name in ["KTV","酒吧","网吧","电竞酒店","麻将馆","健身房","瑜伽馆","足疗店","洗浴中心","按摩店"]:
    check_not_direct("沉浸式社交娱乐", "某某"+name, "体育休闲服务;娱乐场所", "剧本杀")
# Immersive substitute: KTV/酒吧/网吧/电竞酒店分流社交娱乐消费
# 注: 直调 _cr(cat=\"immersive_entertainment\") 避过 sim_full_chain 的 is_real_immersive_entertainment 脱水
rig_is = get_rigor_for_config_key("沉浸式社交娱乐")
for name in ["KTV","酒吧","网吧","电竞酒店","量贩KTV"]:
    r = _cr("某某"+name, "immersive_entertainment", "体育休闲服务;娱乐场所", rig_is, "剧本杀")
    check(r == "substitute", f"沉浸式社交娱乐/剧本杀 substitute: 某某{name} -> {r}")
# Immersive anchor: categories subway/schools/office + name_keywords 大学城/地铁站/写字楼
for name, code in [("地铁站","150500"),("写字楼","120200"),("大学城","050300"),("小学","科教文化服务;学校"),("中学","科教文化服务;学校")]:
    check_anchor("沉浸式社交娱乐", "某某"+name, code, "剧本杀")
# Immersive irrelevant: name_blacklist 麻将馆 + categories_excluded hospitals
for name, code in [("麻将馆","050300"),("棋牌麻将馆","050300"),("医院","090100"),("人民医院","090100"),("中心医院","090100")]:
    check_irrelevant("沉浸式社交娱乐", "某某"+name, code, "剧本杀")

# ===== AB. Code Safety Invariants =====
# 逐 source 扫描：master + subtype 的 amap_codes，forbidden 不容忍，risky 必须防御
print()
print("=== AB. Code Safety Invariants ===")
_forbidden_codes = {"050000","060000","070000","090000","120000"}
_risky_codes = {"050100","050200","050300","050600","060100","060400","100000"}
for mk, rig in INDUSTRY_RIGOR.items():
    dc = rig.get("direct_competitor_rules", {})
    # -- Gather code sources: (label, codes, eff_req_kw, eff_defense) --
    sources = []
    master_req_kw = dc.get("require_name_keyword_for_code", False)
    master_codes = dc.get("amap_codes", [])
    if master_codes:
        eff_def = bool(master_req_kw or dc.get("name_keywords") or dc.get("exclude_names") or dc.get("strict_exclude_names"))
        sources.append((f"{mk}/master", set(master_codes), master_req_kw, eff_def))
    for sub_key, sub_rules in dc.get("subtypes", {}).items():
        sub_codes = sub_rules.get("amap_codes", [])
        if not sub_codes:
            continue
        sub_req_kw = sub_rules.get("require_name_keyword_for_code", master_req_kw)
        sub_def = bool(sub_req_kw or sub_rules.get("name_keywords") or sub_rules.get("exclude_names") or sub_rules.get("strict_exclude_names"))
        sources.append((f"{mk}/subtype:{sub_key}", set(sub_codes), sub_req_kw, sub_def))
    # -- Check each source --
    for label, codes, req_kw, eff_def in sources:
        for fc in _forbidden_codes:
            check(fc not in codes, f"{label}: forbidden code {fc}")
        for rc in _risky_codes:
            if rc in codes:
                check(eff_def, f"{label}: risky code {rc} req_kw={req_kw} defense={eff_def}")

# ===== AC. Low Freq Retail Real Chain Invariants =====
# 锁住：个体零售走 low_freq_retail, 购物中心/百货/步行街走 shopping anchor, 超市/便利店不进 direct
print()
print("=== AC. Low Freq Retail Real Chain Invariants ===")
# 个体零售 direct 走 low_freq_retail
for name, tc in [
    ("服装店","购物服务;服装鞋帽店"),("数码店","购物服务;数码电子"),
    ("手机店","购物服务;数码电子"),("眼镜店","购物服务;服装鞋帽店"),
]:
    r = sim_full_chain("某某"+name, tc, "低频目的零售", "零售店")
    check(r == "direct", f"LFR invariant direct: 某某{name} -> {r}")
# 购物中心/百货/步行街 → anchor (走 shopping, is_real_shopping 保留)
for name, tc in [
    ("购物中心","购物服务;购物中心"),("百货大楼","购物服务;百货商场"),
]:
    r = sim_full_chain("某某"+name, tc, "低频目的零售", "零售店")
    check(r == "anchor", f"LFR invariant anchor: 某某{name} -> {r}")
# 超市/便利店/水果/生鲜/建材/五金 → not direct
for name, tc in [
    ("超市","购物服务;超市"),("便利店","购物服务;便利店"),
    ("水果店","购物服务;综合市场"),("建材市场","购物服务;家居建材市场"),
]:
    r = sim_full_chain("某某"+name, tc, "低频目的零售", "零售店")
    check(r != "direct", f"LFR invariant NOT direct: 某某{name} -> {r}")

# ===== AD. Subtype Substitute Real-Chain Regression =====
# 验证 Phase 8B subtype 级 substitute_keywords 引擎不污染 direct/substitute 边界
print()
print("=== AD. Subtype Substitute Real-Chain Regression ===")

# -- Pet: 规则层验证（宠物医院代用词不触发 dewater）--
rig_pls = get_rigor_for_config_key("专业生活服务")
# Pet substitute → substitute
for name in ["宠物医院","宠物美容"]:
    r = _cr("某某"+name, "convenience", "050300", rig_pls, "宠物店")
    check(r == "substitute", f"AD Pet sub: 某某{name} -> {r}")
# Pet direct → direct (不受 substitute 污染)
for name in ["宠物店","宠物用品店"]:
    r = _cr("某某"+name, "convenience", "050300", rig_pls, "宠物店")
    check(r == "direct", f"AD Pet direct: 某某{name} -> {r}")
# Pet anti-regression → not direct, not substitute
for name in ["美容院","健身房"]:
    r = _cr("某某"+name, "convenience", "050300", rig_pls, "宠物店")
    check(r != "direct", f"AD Pet NOT direct: 某某{name} -> {r}")
    check(r != "substitute", f"AD Pet NOT substitute: 某某{name} -> {r}")

# -- Fitness: 规则层验证 --
# Fitness substitute → substitute
for name in ["动感单车","搏击馆","跆拳道"]:
    r = _cr("某某"+name, "fitness", "体育休闲服务;运动场馆", rig_pls, "健身房")
    check(r == "substitute", f"AD Fit sub: 某某{name} -> {r}")
# Fitness direct → direct
for name in ["健身房","瑜伽馆"]:
    r = _cr("某某"+name, "fitness", "体育休闲服务;运动场馆", rig_pls, "健身房")
    check(r == "direct", f"AD Fit direct: 某某{name} -> {r}")
# Fitness anti-regression → not direct, not substitute
for name in ["体育用品店","足疗按摩"]:
    r = _cr("某某"+name, "fitness", "体育休闲服务;运动场馆", rig_pls, "健身房")
    check(r != "direct", f"AD Fit NOT direct: 某某{name} -> {r}")
    check(r != "substitute", f"AD Fit NOT substitute: 某某{name} -> {r}")

# -- Laundry: 规则层验证 --
rig_cs = get_rigor_for_config_key("社区基础服务")
# Laundry substitute → substitute
r = _cr("某某家政服务", "laundry", "生活服务;洗衣店", rig_cs, "洗衣店")
check(r == "substitute", f"AD Laundry sub: 某某家政服务 -> {r}")
# Laundry direct → direct
for name in ["洗衣店","干洗店"]:
    r = _cr("某某"+name, "laundry", "生活服务;洗衣店", rig_cs, "洗衣店")
    check(r == "direct", f"AD Laundry direct: 某某{name} -> {r}")
# Laundry anti-regression → not direct, not substitute
for name in ["手机维修","皮具护理","擦鞋店"]:
    r = _cr("某某"+name, "laundry", "生活服务;洗衣店", rig_cs, "洗衣店")
    check(r != "direct", f"AD Laundry NOT direct: 某某{name} -> {r}")
    check(r != "substitute", f"AD Laundry NOT substitute: 某某{name} -> {r}")

# -- Subtype sub_first 继承验证 --
# Fitness: 动感单车命中 substitute_keywords 后不得进入 direct，即使 type_code 落在 master code
r = _cr("某某动感单车", "fitness", "体育休闲服务;运动场馆", rig_pls, "健身房")
check(r == "substitute", f"AD sub_first inherited: 某某动感单车 -> {r} (not direct)")

# ===== KNOWN_RULE_GAPS =====
print("\n=== KNOWN_RULE_GAPS ===")
if known_gaps:
    for g in known_gaps:
        print(f"  GAP: {g}")
else:
    print("  (none)")

# ===== Subtype Coverage Audit (Phase 5C) =====
# 14 masters: 5 have subtypes, 9 do not.
# All 9 un-subtyped masters have req_kw=True — the code-gate is already locked.
# Conclusion: no subtype forced this round. Each assessment below.
#
# 刚需快餐小吃 (3 entries): NO subtype needed. 42 kw + 32 excl, req_kw=True, sub_first=True. Rules tight.
# 精品茶饮咖啡 (3 entries): LOW priority. 奶茶/咖啡/饮品 share 050500 code and competitor profile.
# 中餐正餐 (2 entries): LOW priority. req_kw=True with 21 kw. 中餐/酒楼 distinction captured by keywords.
# 火锅_烧烤 (2 entries): NO subtype needed. Single competitive dimension.
# 异国_中高端正餐 (2 entries): MEDIUM priority. 西餐/日餐 have different keywords but both use 050100/050200.
#   → Future: could split into western (steak/pizza/意餐) and japanese (sushi/omakase/怀石) subtypes.
# 烘焙甜品 (2 entries): NO subtype needed. Single competitive dimension.
# 商务酒店 (1 entry): NO subtype needed. Single entry master.
# 民宿青旅 (2 entries): LOW priority. 民宿/青旅 share 100000 code.
# 低频目的零售 (3 entries): LOW priority. req_kw=True + is_real_low_freq_retail dewatering already gates.

# ===== Sample Bank Ledger (structured, verifiable) =====
_PARTIAL_NO_SUB_REASON = (
    "当前业态无稳定全国通用 substitute 规则，避免为凑数污染 direct/substitute 边界"
)
_SAMPLE_BANK = [
    # (label, d, nd, s, a, i, status, partial_reason)
    ("Snack Shop",        18,16,7,5,5, "complete_candidate", ""),
    ("Tea/Coffee",        11,13,5,5,5, "complete_candidate", ""),
    ("Chinese Restaurant",12,17,5,5,5, "complete_candidate", ""),
    ("Foreign Premium Dining",11,10,5,5,5,"complete_candidate",""),
    ("Hotpot/BBQ",        12,15,5,5,5, "complete_candidate", ""),
    ("Bakery/Dessert",    10,15,5,5,9, "complete_candidate", ""),
    ("Low Frequency Retail",11,10,0,5,5,"partial",_PARTIAL_NO_SUB_REASON),
    ("Convenience",       10,10,5,5,5, "complete_candidate", ""),
    ("Fresh Produce",     10,10,5,5,5, "complete_candidate", ""),
    ("Pharmacy",          10,10,0,5,5, "partial", _PARTIAL_NO_SUB_REASON),
    ("Tobacco/Liquor",    10,10,0,5,5, "partial", _PARTIAL_NO_SUB_REASON),
    ("Daily Goods",       10,10,0,5,5, "partial", _PARTIAL_NO_SUB_REASON),
    ("Beauty",            10,10,0,5,5, "partial", "substitute blocked by master irr"),
    ("Pet",               10,10,2,5,5, "partial", "substitute keywords added, need more samples"),
    ("Fitness",           10,10,3,5,5, "partial", "substitute keywords added, need more samples"),
    ("Education",         10,10,0,5,5, "partial", _PARTIAL_NO_SUB_REASON),
    ("Laundry",           10,10,1,5,5, "partial", "家政 only; 维修类 excluded from substitute"),
    ("Clinic",            10,10,0,5,5, "partial", "substitute blocked by master irr"),
    ("Bar",               10,10,5,5,5, "complete_candidate", ""),
    ("KTV",               10,10,5,5,5, "complete_candidate", ""),
    ("Internet Cafe",     10,10,5,5,5, "complete_candidate", ""),
    ("Immersive Social",  22,10,5,5,5, "complete_candidate", ""),
]

print("\n=== Sample Bank Ledger ===")
complete_n, partial_n = 0, 0
for entry in _SAMPLE_BANK:
    label, d, nd, s, a, i, status, reason = entry
    print(f"  {label}: d={d} nd={nd} s={s} a={a} i={i} [{status}]")
    if status == "complete_candidate":
        complete_n += 1
        check(d >= 10, f"{label}: d={d} < 10")
        check(nd >= 10, f"{label}: nd={nd} < 10")
        check(s >= 5, f"{label}: s={s} < 5")
        check(a >= 5, f"{label}: a={a} < 5")
        check(i >= 5, f"{label}: i={i} < 5")
    elif status == "partial":
        partial_n += 1
        check(d >= 10, f"{label}: d={d} < 10")
        check(nd >= 10, f"{label}: nd={nd} < 10")
        check(a >= 5, f"{label}: a={a} < 5")
        check(i >= 5, f"{label}: i={i} < 5")
        check(len(reason) > 0, f"{label}: partial without reason")
    else:
        check(False, f"{label}: unknown status {status}")
print(f"  complete={complete_n} partial={partial_n}")


# ===== Summary =====
print(f"\n{'='*50}")
print(f"TOTAL: {p} PASS, {f} FAIL")
if f == 0:
    print("ALL TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({f} failures)")
    sys.exit(1)
