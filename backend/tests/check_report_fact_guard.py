"""
P0 + P2 报告事实校验 — 自测套件
验证 check_poi_name_hallucination 与 check_poi_context_mismatch 行为
"""
import sys, os, importlib.util, inspect
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# 按文件路径直接加载，不触发 services/__init__.py / amap_service / FastAPI
_guard_path = os.path.join(os.path.dirname(__file__), "..", "services", "poi_name_guard.py")
_guard_path = os.path.abspath(_guard_path)
_spec = importlib.util.spec_from_file_location("poi_name_guard", _guard_path)
_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_guard)
check_poi_name_hallucination = _guard.check_poi_name_hallucination
check_poi_context_mismatch = _guard.check_poi_context_mismatch
check_direct_competitor_count_mismatch = _guard.check_direct_competitor_count_mismatch

p, f = 0, 0

def check(cond, label):
    global p, f
    if cond: p += 1
    else: f += 1; print(f"  FAIL: {label}")

# ═══════════════════════════════════════════════════════════════
# T1: 合法 direct 名称 — 通过
# ═══════════════════════════════════════════════════════════════
print("=== T1: 合法 direct 名称 ===")
rd = {
    "direct_competitor_list": [{"name":"同仁堂大药房","distance":150}],
}
report = "贴身200米内，同仁堂大药房构成直接竞争压力。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"T1 PASS: {issues}")

# ═══════════════════════════════════════════════════════════════
# T2: 合法 anchor 名称 — 通过
# ═══════════════════════════════════════════════════════════════
print("=== T2: 合法 anchor 名称 ===")
rd = {
    "traffic_anchor_list": [{"name":"阳光小区","distance":300}],
}
report = "阳光小区提供稳定社区客流来源，商业配套齐全。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"T2 PASS: {issues}")

# ═══════════════════════════════════════════════════════════════
# T3: 不存在的竞品名称 — 触发 warning
# ═══════════════════════════════════════════════════════════════
print("=== T3: 伪造竞品名称 ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [],
    "traffic_anchor_list": [],
}
report = "500米内聚集了益丰大药房、老百姓大药房两家竞品。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) >= 2, f"T3 至少2条: {issues}")
check(any("益丰大药房" in i for i in issues), f"T3 包含益丰大药房")
check(any("老百姓大药房" in i for i in issues), f"T3 包含老百姓大药房")

# ═══════════════════════════════════════════════════════════════
# T4: 泛称 — 不触发 (周边学校/附近社区/医疗配套)
# ═══════════════════════════════════════════════════════════════
print("=== T4: 泛称不误杀 ===")
rd = {
    "direct_competitor_list": [],
}
report = "周边学校密集，附近社区客群稳定，医疗配套齐全。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"T4 不误杀: {issues}")

# ═══════════════════════════════════════════════════════════════
# T5: 普通报告短语 — 不触发
# ═══════════════════════════════════════════════════════════════
print("=== T5: 报告短语不误杀 ===")
rd = {
    "direct_competitor_list": [],
}
report = "稳定社区客流支撑，直接竞争压力可控，商业活跃度一般。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"T5 不误杀: {issues}")

# ═══════════════════════════════════════════════════════════════
# T6: 前缀/去括号匹配 — 通过
# ═══════════════════════════════════════════════════════════════
print("=== T6: 前缀/去括号匹配 ===")
rd = {
    "direct_competitor_list": [{"name":"瑞幸咖啡(XX路店)","distance":200}],
}
report = "周边有瑞幸咖啡两家门店，品牌势能强。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"T6 去括号后通过: {issues}")

# ═══════════════════════════════════════════════════════════════
# T7: hot_brands 名称 — 前缀匹配通过
# ═══════════════════════════════════════════════════════════════
print("=== T7: hot_brands 前缀匹配 ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [],
    "traffic_anchor_list": [],
    "hot_brands": [{"name":"星巴克","count":3}],
}
# "星巴克门店" 被提取为候选（店=POI后缀），与 allowlist "星巴克" 前缀匹配
report = "周边星巴克门店密集，品牌势能突出。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"T7 前缀匹配通过: {issues}")

# ═══════════════════════════════════════════════════════════════
# T7b: hot_brands allowlist 生效 — 不在 allowlist 的品牌触发 warning
# ═══════════════════════════════════════════════════════════════
print("=== T7b: hot_brands 不存在触发 ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [],
    "traffic_anchor_list": [],
    "hot_brands": [{"name":"星巴克","count":3}],
}
# "瑞幸咖啡门店" 被提取，但 "瑞幸咖啡" 不在 allowlist → 触发
report = "周边瑞幸咖啡门店密集，分流压力大。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) >= 1, f"T7b 至少1条: {issues}")
check(any("瑞幸" in i for i in issues), f"T7b 包含瑞幸咖啡相关: {issues}")

# ═══════════════════════════════════════════════════════════════
# T8: poi_lists 中设施名 — 通过
# ═══════════════════════════════════════════════════════════════
print("=== T8: poi_lists 设施名 ===")
rd = {
    "direct_competitor_list": [],
    "poi_lists": {
        "hospitals": [{"name":"某某人民医院","distance":400}],
        "schools": [{"name":"阳光小学","distance":300}],
        "residential": [{"name":"翠苑新村","distance":200}],
    },
}
report = "500米内有某某人民医院，阳光小学提供学区客流，翠苑新村住户稳定。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"T8 PASS: {issues}")

# ═══════════════════════════════════════════════════════════════
# T9: poi_lists 不存在的设施名 — 触发 warning
# ═══════════════════════════════════════════════════════════════
print("=== T9: 伪造设施名 ===")
rd = {
    "direct_competitor_list": [],
    "poi_lists": {
        "hospitals": [{"name":"某某人民医院","distance":400}],
    },
}
report = "500米内有协和医院提供优质医疗配套，周边医疗资源丰富。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) >= 1, f"T9 至少1条: {issues}")
check(any("协和医院" in i for i in issues), f"T9 包含协和医院")

# ═══════════════════════════════════════════════════════════════
# T10: 无 real_data — 不崩溃
# ═══════════════════════════════════════════════════════════════
print("=== T10: 空数据不崩溃 ===")
issues = check_poi_name_hallucination("任意报告文本", None)
check(len(issues) == 0, f"T10 None data: {issues}")
issues = check_poi_name_hallucination("任意报告文本", {})
check(len(issues) == 0, f"T10 empty data: {issues}")
issues = check_poi_name_hallucination("", {"direct_competitor_list":[{"name":"XX"}]})
check(len(issues) == 0, f"T10 empty text: {issues}")

# ═══════════════════════════════════════════════════════════════
# P2: 竞品语境误用检测
# ═══════════════════════════════════════════════════════════════

# T-P2-1: direct 名称在竞品句中 → 通过
print("=== T-P2-1: direct 在竞品语境 → 通过 ===")
rd = {
    "direct_competitor_list": [{"name":"同仁堂大药房","distance":150}],
    "substitute_list": [],
    "traffic_anchor_list": [],
}
report = "贴身200米内，同仁堂大药房构成直接竞争压力。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-1 PASS: {issues}")

# T-P2-2: substitute 名称在替代语境中 → 通过
print("=== T-P2-2: substitute 在替代语境 → 通过 ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [{"name":"某某便利店","distance":200}],
    "traffic_anchor_list": [],
}
report = "替代消费压力主要来自某某便利店。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-2 PASS: {issues}")

# T-P2-3: substitute 名称在直接竞品语境中 → warning
print("=== T-P2-3: substitute 在竞品语境 → warning ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [{"name":"某某便利店","distance":200}],
    "traffic_anchor_list": [],
}
report = "贴身200米内，某某便利店构成直接竞争压力。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) >= 1, f"P2-3 至少1条: {issues}")
check(any("某某便利店" in i for i in issues), f"P2-3 包含某某便利店")

# T-P2-4: anchor 名称在客流锚点语境中 → 通过
print("=== T-P2-4: anchor 在锚点语境 → 通过 ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [],
    "traffic_anchor_list": [{"name":"阳光小区","distance":300}],
}
report = "阳光小区是周边重要的客流锚点，提供稳定客流来源。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-4 PASS: {issues}")

# T-P2-5: anchor 名称在竞争对手语境中 → warning
print("=== T-P2-5: anchor 在竞品语境 → warning ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [],
    "traffic_anchor_list": [{"name":"阳光小区","distance":300}],
}
report = "周边竞争对手包括阳光小区等商业设施，同类竞品密集。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) >= 1, f"P2-5 至少1条: {issues}")
check(any("阳光小区" in i for i in issues), f"P2-5 包含阳光小区")

# T-P2-6: 泛称不误杀
print("=== T-P2-6: 泛称不误杀 ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [],
    "traffic_anchor_list": [],
}
report = "周边学校和附近社区是重要的客流锚点，直接竞争压力可控。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-6 不误杀: {issues}")

# T-P2-7: substitute 无后缀名称在竞品语境 → warning
print("=== T-P2-7: substitute 无后缀名在竞品语境 → warning ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [{"name":"肯德基","distance":200}],
    "traffic_anchor_list": [],
}
report = "贴身200米内，肯德基构成直接竞争压力。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) >= 1, f"P2-7 至少1条: {issues}")
check(any("肯德基" in i for i in issues), f"P2-7 包含肯德基")

# T-P2-8: direct 优先级覆盖 substitute 同名 → 不 warning
print("=== T-P2-8: direct 覆盖 substitute 同名 → 通过 ===")
rd = {
    "direct_competitor_list": [{"name":"肯德基","distance":150}],
    "substitute_list": [{"name":"肯德基","distance":200}],
    "traffic_anchor_list": [],
}
report = "贴身200米内，肯德基构成直接竞争压力。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-8 direct覆盖: {issues}")

# T-P2-9: substitute 无后缀名称在替代语境 → 不 warning
print("=== T-P2-9: substitute 无后缀名在替代语境 → 通过 ===")
rd = {
    "direct_competitor_list": [],
    "substitute_list": [{"name":"星巴克","distance":300}],
    "traffic_anchor_list": [],
}
report = "星巴克属于替代消费压力来源，分流部分饮品需求。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-9 PASS: {issues}")

# T-P2-10: direct 等价前缀覆盖 substitute → 不 warning
print("=== T-P2-10: direct 前缀覆盖 substitute → 通过 ===")
rd = {
    "direct_competitor_list": [{"name":"肯德基店","distance":150}],
    "substitute_list": [{"name":"肯德基","distance":200}],
    "traffic_anchor_list": [],
}
report = "肯德基构成直接竞争压力。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-10 direct前缀覆盖: {issues}")

# T-P2-11: direct 长名覆盖 substitute 短名 → 不 warning
print("=== T-P2-11: direct 长名覆盖 substitute 短名 → 通过 ===")
rd = {
    "direct_competitor_list": [{"name":"星巴克门店","distance":150}],
    "substitute_list": [{"name":"星巴克","distance":300}],
    "traffic_anchor_list": [],
}
report = "星巴克构成直接竞争压力。"
issues = check_poi_context_mismatch(report, rd)
check(len(issues) == 0, f"P2-11 direct长名覆盖: {issues}")

# ═══════════════════════════════════════════════════════════════
# P3: 直接竞品数量膨胀检测
# ═══════════════════════════════════════════════════════════════

# T-P3-1: 精确一致 → 通过
print("=== T-P3-1: 精确一致 → 通过 ===")
rd = {"direct_competitors_200m": 5}
report = "贴身200米内5家同类竞品构成竞争。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) == 0, f"P3-1 PASS: {issues}")

# T-P3-2: 报告数膨胀 → warning
print("=== T-P3-2: 数量膨胀 → warning ===")
rd = {"direct_competitors_200m": 3}
report = "200米内聚集了8家同类竞品，竞争激烈。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) >= 1, f"P3-2 至少1条: {issues}")
check(any("3" in i and "8" in i for i in issues), f"P3-2 3→8: {issues}")

# T-P3-3: 报告数小于真实数 → 通过（只列重点竞品）
print("=== T-P3-3: 少于真实数 → 通过 ===")
rd = {"direct_competitors_200m": 5}
report = "200米内3家同类竞品值得关注。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) == 0, f"P3-3 PASS: {issues}")

# T-P3-4: 模糊表述跳过
print("=== T-P3-4: 模糊表述 → 跳过 ===")
rd = {"direct_competitors_200m": 5}
report = "200米内约有8家同类竞品，竞争压力较大。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) == 0, f"P3-4 模糊跳过: {issues}")

# T-P3-5: 无半径标记 → 跳过
print("=== T-P3-5: 无半径 → 跳过 ===")
rd = {"direct_competitors_200m": 5}
report = "周边竞品共8家门店，分布密集。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) == 0, f"P3-5 无半径跳过: {issues}")

# T-P3-6: 无竞品语境 → 跳过
print("=== T-P3-6: 无竞品语境 → 跳过 ===")
rd = {"direct_competitors_200m": 3}
report = "200米内8家餐饮门店。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) == 0, f"P3-6 无语境跳过: {issues}")

# T-P3-7: 零竞品报告非零 → warning
print("=== T-P3-7: 零竞品报非零 → warning ===")
rd = {"direct_competitors_200m": 0}
report = "200米内2家同类竞品需要关注。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) >= 1, f"P3-7 至少1条: {issues}")

# ═══════════════════════════════════════════════════════════════
# P0-FIX: 泛称 POI 后缀过滤 (id=21 假阳性修补)
# ═══════════════════════════════════════════════════════════════

# T-P0F-1: "周边酒店" 泛称 → 不 warning
print("=== T-P0F-1: 周边酒店泛称 → 通过 ===")
rd = {"direct_competitor_list": []}
report = "周边酒店住宿配套丰富，带来流动客群。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-1 泛称通过: {issues}")

# T-P0F-2: "周边写字楼" 泛称 → 不 warning
print("=== T-P0F-2: 周边写字楼泛称 → 通过 ===")
rd = {"direct_competitor_list": []}
report = "周边写字楼分布较少，白领客群不足。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-2 泛称通过: {issues}")

# T-P0F-3: "周边便利店/超市" 泛称 → 不 warning
print("=== T-P0F-3: 周边便利店超市泛称 → 通过 ===")
rd = {"direct_competitor_list": []}
report = "周边便利店和超市较少，缺少日常消费场景的协同。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-3 泛称通过: {issues}")

# T-P0F-4: "大学校" artifact → 不 warning
print("=== T-P0F-4: 大学校 artifact → 通过 ===")
rd = {"direct_competitor_list": []}
report = "周边分布有6所学校，包括小学、大学校区等。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-4 artifact通过: {issues}")

# T-P0F-5: 真实伪造名称仍 warning — allowlist 为空，报告写具体品牌名
print("=== T-P0F-5: 真实伪造名仍触发 ===")
rd = {"direct_competitor_list": []}
report = "200米内聚集了瑞幸咖啡门店，品牌势能突出。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) >= 1, f"P0F-5 仍触发: {issues}")
check(any("瑞幸咖啡" in i for i in issues), f"P0F-5 包含瑞幸咖啡: {issues}")

# T-P0F-6: 描述性前缀+周边+泛称POI → 不 warning ("晚间客流依赖周边酒店")
print("=== T-P0F-6: 描述性前缀+周边酒店 → 通过 ===")
rd = {"direct_competitor_list": []}
report = "晚间客流依赖周边酒店住宿和夜间配套，具备全天候消费潜力。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-6 描述性前缀通过: {issues}")

# T-P0F-7: 描述性前缀+附近+泛称POI → 不 warning
print("=== T-P0F-7: 描述性前缀+附近学校 → 通过 ===")
rd = {"direct_competitor_list": []}
report = "午间客流依赖附近学校，学生群体消费频次高。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-7 描述性前缀通过: {issues}")

# T-P0F-8: 距离+否定+同类+业态后缀 → 不 warning ("米内无任何同类药店")
print("=== T-P0F-8: 距离否定同类artifact → 通过 ===")
rd = {"direct_competitor_list": []}
report = "500米内无任何同类药店，竞争压力极低。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-8 距离artifact通过: {issues}")

# T-P0F-9: 距离+商圈内+同类+业态后缀 → 不 warning
print("=== T-P0F-9: 商圈内同类artifact → 通过 ===")
rd = {"direct_competitor_list": []}
report = "1公里商圈内同类药店较少，市场空间充足。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-9 商圈artifact通过: {issues}")

# T-P0F-10: 否定+大型+商圈/商场泛称 → 不 warning
print("=== T-P0F-10: 否定大型商圈泛称 → 通过 ===")
rd = {"direct_competitor_list": []}
report = "无大型商圈或购物商场，商业配套薄弱。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-10 否定泛称通过: {issues}")

# T-P0F-11: 具体分店名仍 warning — 避免数字+米内边界截断
print("=== T-P0F-11: 具体分店名仍触发 ===")
rd = {"direct_competitor_list": []}
report = "周边分布有解放路店，同类竞品密集。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) >= 1, f"P0F-11 仍触发: {issues}")
check(any("解放路店" in i for i in issues), f"P0F-11 包含解放路店: {issues}")

# T-P0F-12: 回归锁 — "米内无" 不得误杀 "米内+具名品牌"
print("=== T-P0F-12: 米内有具名品牌仍触发 ===")
rd = {"direct_competitor_list": []}
report = "500米内聚集了益丰大药房，竞争压力大。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) >= 1, f"P0F-12 仍触发: {issues}")
check(any("益丰大药房" in i for i in issues), f"P0F-12 包含益丰大药房: {issues}")

# T-P0F-13: "周边客群以高校" 假阳性 → 不 warning（真实句式含"写字楼"）
print("=== T-P0F-13: 客群描述artifact → 通过 ===")
rd = {"direct_competitor_list": []}
report = "周边客群以高校学生和写字楼白领为主。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-13 客群artifact通过: {issues}")

# T-P0F-14: 具体伪造名仍触发（回归锁）
print("=== T-P0F-14: 具体伪造名仍触发 ===")
rd = {"direct_competitor_list": []}
report = "周边聚集了瑞幸小吃店，竞争压力较强。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) >= 1, f"P0F-14 仍触发: {issues}")
check(any("瑞幸" in i for i in issues), f"P0F-14 包含瑞幸: {issues}")

# T-P0F-15: 裸泛称回归 — "周边写字楼" → 不 warning
print("=== T-P0F-15: 裸泛称通过 ===")
rd = {"direct_competitor_list": []}
report = "周边写字楼白领客群稳定，带来稳定午市客流。"
issues = check_poi_name_hallucination(report, rd)
check(len(issues) == 0, f"P0F-15 裸泛称通过: {issues}")

# T-P3-8: 500m/1000m 半径独立校验
print("=== T-P3-8: 多半径独立 ===")
rd = {"direct_competitors_500m": 4, "direct_competitors_1000m": 10}
report = "500米内6家直接竞品，1000米内8家直接竞品。"
issues = check_direct_competitor_count_mismatch(report, rd)
check(len(issues) >= 1, f"P3-8 至少1条: {issues}")
# 500m: 6>4 → warning; 1000m: 8<10 → no warning
check(any("500m" in i for i in issues), f"P3-8 含500m: {issues}")
check(not any("1000m" in i for i in issues), f"P3-8 不含1000m: {issues}")

# ═══════════════════════════════════════════════════════════════
# P4: 报告事实一致性校验（validate_report_fact_consistency 纯函数）
# ═══════════════════════════════════════════════════════════════

# 通过 importlib 从文件路径加载 report_fact_guard，避免触发 main.py 的 FastAPI/AMap 依赖
_rfg_path = os.path.join(os.path.dirname(__file__), "..", "report_fact_guard.py")
_rfg_path = os.path.abspath(_rfg_path)
_rfg_spec = importlib.util.spec_from_file_location("report_fact_guard", _rfg_path)
_rfg = importlib.util.module_from_spec(_rfg_spec)
_rfg_spec.loader.exec_module(_rfg)
validate_report_fact_consistency = _rfg.validate_report_fact_consistency

def _result_with_text(text, dims=None):
    """构造最小 result dict，把 text 分布在 advantages/disadvantages/summary 中"""
    return {
        "dimension_scores": dims or [{"key":f"d{i}"} for i in range(8)],
        "details": {},
        "advantages": [text],
        "disadvantages": [],
        "executive_summary": {},
        "action_plan": [],
        "summary": "",
    }

# T-P4-1: direct expected=0, report says 3 -> fact_error
print("=== T-P4-1: direct 数量膨胀=0→3 -> error ===")
rd = {"direct_competitors_200m": 0, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("200米内3家直接竞品，竞争压力大。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-1 error: {issues}")
check(any("direct_competitors_200m=0" in i for i in issues), f"P4-1 内容: {issues}")

# T-P4-2: direct expected=5, report says 2 -> 不触发
print("=== T-P4-2: direct 少报=5→2 -> 不触发 ===")
rd = {"direct_competitors_200m": 5, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("200米内仅2家直接竞品，竞争压力可控。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P4-2 不触发: {issues}")

# T-P4-3: substitute expected=1, report says 5 "替代竞争" -> fact_error
print("=== T-P4-3: substitute 数量膨胀=1→5 -> error ===")
rd = {"substitute_competitors_200m": 1, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("200米内5家替代竞争分流，压力较大。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-3 error: {issues}")
check(any("substitute_competitors_200m=1" in i for i in issues), f"P4-3 内容: {issues}")

# T-P4-4: anchor expected=1, report says 5 "客流来源" -> fact_error
print("=== T-P4-4: anchor 数量膨胀=1→5 -> error ===")
rd = {"traffic_anchors_200m": 1, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("200米内5个客流来源，导流能力较强。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-4 error: {issues}")
check(any("traffic_anchors_200m=1" in i for i in issues), f"P4-4 内容: {issues}")

# T-P4-5: rigor=True, report text 含 competitors_200m -> fact_error
print("=== T-P4-5: 旧口径 competitors_200m -> error ===")
rd = {"rigor_enabled": True, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("周边 competitors_200m 为 8 家，竞争激烈。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-5 error: {issues}")
check(any("competitors_200m" in i for i in issues), f"P4-5 内容: {issues}")

# T-P4-6: rigor=False, report text 含 competitors_200m -> 不触发旧口径 error
print("=== T-P4-6: rigor=False 旧口径 -> 不触发 ===")
rd = {"rigor_enabled": False, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("周边 competitors_200m 为 8 家。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P4-6 不触发: {issues}")

# T-P4-7: schools expected=0, report says 4 "高校校区" -> fact_error
print("=== T-P4-7: schools 数字幻觉 -> error ===")
rd = {"stats_200m": {"schools": 0}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("200米内4所高校校区，学生客流充沛。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-7 error: {issues}")
check(any("schools=0" in i for i in issues), f"P4-7 内容: {issues}")

# T-P4-8: 模糊表述 -> 不触发
print("=== T-P4-8: 模糊表述 -> 不触发 ===")
rd = {"direct_competitors_200m": 2, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("周边约有七八家便利店，日常消费便捷。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P4-8 不触发: {issues}")

# T-P4-9: 多半径独立 — 全部精确一致或略少 -> 不触发
print("=== T-P4-9: 多半径精确一致 -> 不触发 ===")
rd = {
    "direct_competitors_200m": 3, "direct_competitors_500m": 8,
    "substitute_competitors_1000m": 2, "traffic_anchors_500m": 5,
    "stats_200m": {"schools": 1}, "stats_500m": {}, "stats_1000m": {},
}
result = _result_with_text(
    "200米内3家直接竞品，分布密集。500米内8家同品类门店，选择丰富。"
    "1000米内周边约有2家替代竞争，分流有限。500米范围内5个客流来源，导流能力强。"
    "200米内1所高校校区，午间客流可观。"
)
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P4-9 不触发: {issues}")

# T-P4-10: real_data 中有 competitors_* 旧字段，但 report text 不含 -> 不触发旧口径 error
print("=== T-P4-10: real_data旧字段不触发 -> 通过 ===")
rd = {
    "rigor_enabled": True,
    "competitors_200m": 9,  # 旧字段在 real_data 中，但不在 report text 中
    "stats_200m": {}, "stats_500m": {}, "stats_1000m": {},
}
result = _result_with_text("200米内5家直接竞品，竞争激烈。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P4-10 不触发: {issues}")

# T-P4-11: direct=0, 500m半径, "同业竞品"关键词 -> error
print("=== T-P4-11: 500m direct=0 同业竞品 -> error ===")
rd = {"direct_competitors_500m": 0, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("500米内有2家同业竞品，竞争压力较大。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-11 error: {issues}")
check(any("direct_competitors_500m=0" in i for i in issues), f"P4-11 内容: {issues}")

# T-P4-12: direct=1, 1000m半径, >3x膨胀 -> error
print("=== T-P4-12: 1000m direct 膨胀1->5 -> error ===")
rd = {"direct_competitors_1000m": 1, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("1000米内5家竞争品牌，竞争态势严峻。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-12 error: {issues}")
check(any("direct_competitors_1000m=1" in i for i in issues), f"P4-12 内容: {issues}")

# T-P4-13: 模糊表达"不少于4家" expected=2 -> 不触发（4不超3x2=6）
print("=== T-P4-13: 不少于模糊表达 -> 不触发 ===")
rd = {"direct_competitors_500m": 2, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("500米内不少于4家直接竞品，需要差异化。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P4-13 不触发: {issues}")

# T-P4-14: rigor=True, 报告含 competitors_500m -> error
print("=== T-P4-14: 旧口径 competitors_500m -> error ===")
rd = {"rigor_enabled": True, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("周边 competitors_500m 为 5 家，竞争激烈。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-14 error: {issues}")
check(any("competitors_500m" in i for i in issues), f"P4-14 内容: {issues}")

# T-P4-15: rigor=True, 报告含 competitors_1000m -> error
print("=== T-P4-15: 旧口径 competitors_1000m -> error ===")
rd = {"rigor_enabled": True, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("周边 competitors_1000m 为 10 家。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P4-15 error: {issues}")
check(any("competitors_1000m" in i for i in issues), f"P4-15 内容: {issues}")

# T-P4-16: real_data 含 competitors_500m/1000m 旧字段，但 report text 不含 -> 不触发
print("=== T-P4-16: real_data旧字段500m/1000m不触发 -> 通过 ===")
rd = {
    "rigor_enabled": True,
    "competitors_500m": 3, "competitors_1000m": 7,
    "stats_200m": {}, "stats_500m": {}, "stats_1000m": {},
}
result = _result_with_text("500米内3家直接竞品，1000米内8家同品类门店。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P4-16 不触发: {issues}")

# ═══════════════════════════════════════════════════════════════
# P5: fact_errors 重试 fallback 纯函数测试
# 注: 真实 LLM 重试链路在 main.py SSE 中，需集成测试。本段验证校验函数稳定性。
# ═══════════════════════════════════════════════════════════════

# T-P5-1: fact_errors detected -> retry correction hint 包含真实值
print("=== T-P5-1: fact_errors 可生成修正提示 ===")
rd = {"direct_competitors_200m": 0, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("200米内3家直接竞品，竞争激烈。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P5-1 应触发: {issues}")
# 修正提示应包含字段名和真实值
hint = "; ".join(issues)
check("direct_competitors_200m=0" in hint, f"P5-1 hint包含字段: {hint}")
check("3" in hint, f"P5-1 hint包含声称值: {hint}")

# T-P5-2: 修正后报告通过 -> 不触发 fact_errors
print("=== T-P5-2: 修正后报告通过 ===")
rd = {"direct_competitors_200m": 2, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("200米内仅2家直接竞品，竞争压力可控。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) == 0, f"P5-2 不触发: {issues}")

# T-P5-3: 旧口径 competitors_* retry 提示覆盖
print("=== T-P5-3: 旧口径 error 可生成修正提示 ===")
rd = {"rigor_enabled": True, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {}}
result = _result_with_text("周边 competitors_200m 为 8 家。")
issues = validate_report_fact_consistency(result, rd)
check(len(issues) >= 1, f"P5-3 应触发: {issues}")
check(any("competitors_200m" in i for i in issues), f"P5-3 包含旧口径: {issues}")

# ═══════════════════════════════════════════════════════════════
# Phase 12: 收窄容忍 + 禁止决策语言 + 财务单点检测
# ═══════════════════════════════════════════════════════════════

# T-P12-1: 收窄 3x 容忍 — expected=8, reported=23 必须 fail
print("=== T-P12-1: 收窄容忍 (max(e+3, e*2)) ===")
rd_p12 = {"rigor_enabled": False, "stats_200m": {}, "stats_500m": {"schools": 8}, "stats_1000m": {}}
result_p12 = _result_with_text("500米内23所学校，学区属性突出。")
issues_p12 = validate_report_fact_consistency(result_p12, rd_p12)
check(len(issues_p12) >= 1, f"P12-1 expected=8 reported=23 > max(11,16)=16 应触发: {issues_p12}")

# T-P12-1b: expected=8, reported=15 should pass (15 <= max(11,16))
rd_p12b = {"rigor_enabled": False, "stats_200m": {}, "stats_500m": {"schools": 8}, "stats_1000m": {}}
result_p12b = _result_with_text("500米内15所学校，学区属性突出。")
issues_p12b = validate_report_fact_consistency(result_p12b, rd_p12b)
# 15 > max(8+3, 8*2) = max(11, 16) = 16? No, 15 <= 16. So should pass.
# Wait, max(8+3, 8*2) = max(11, 16) = 16. 15 <= 16 → should NOT trigger
check(len(issues_p12b) == 0, f"P12-1b expected=8 reported=15 <= max(11,16)=16 不应触发: {issues_p12b}")

# T-P12-2: 禁止推荐语言
print("=== T-P12-2: 禁止推荐/不推荐决策语言 ===")
check_prohibited_decision_language = _rfg.check_prohibited_decision_language
check_single_point_financial = _rfg.check_single_point_financial
check(len(check_prohibited_decision_language("建议推荐开店，此处适合投资。")) >= 1, "P12-2 推荐开店应触发")
check(len(check_prohibited_decision_language("强烈建议在此开店。")) >= 1, "P12-2 强烈建议应触发")
check(len(check_prohibited_decision_language("本报告为选址初筛参考，需线下实地核验。")) == 0, "P12-2 安全措辞不应触发")
check(len(check_prohibited_decision_language("适合作为候选点继续核验，风险点包括...")) == 0, "P12-2 候选点+风险点不应触发")

# T-P12-3: 财务单点精确数字
print("=== T-P12-3: 财务单点精确数字检测 ===")
check(len(check_single_point_financial("月净利 4.7 万元，回本 124 天。")) >= 1, "P12-3 单点财务应触发")
check(len(check_single_point_financial("月净利 3-5 万元，回本周期约 6-9 个月。")) == 0, "P12-3 区间财务不应触发")
check(len(check_single_point_financial("月净利约 5 万（模型假设，需核验）。")) == 0, "P12-3 模型假设标注不应触发")

# ═══════════════════════════════════════════════════════════════
# Phase 13: 资金安全 / 保存链路最小测试
# ═══════════════════════════════════════════════════════════════

# T-P13-1: refund_credits 函数存在且可导入（确保退款收口可用）
print("=== T-P13-1: refund_credits 可导入 ===")
from services.billing_service import refund_credits, check_billing_access, BillingResult
check(callable(refund_credits), "P13-1 refund_credits 必须是可调用函数")
check(callable(check_billing_access), "P13-1 check_billing_access 必须是可调用函数")

# T-P13-2: refund_credits 参数签名正确
print("=== T-P13-2: refund 参数签名 ===")
sig = inspect.signature(refund_credits)
params = list(sig.parameters.keys())
check("user_id" in params, "P13-2 refund_credits 必须接受 user_id")
check("amount" in params, "P13-2 refund_credits 必须接受 amount")
check("reason" in params, "P13-2 refund_credits 必须接受 reason")

# T-P13-3: BillingResult 结构完整
print("=== T-P13-3: BillingResult 结构 ===")
br = BillingResult(allowed=True, reason="test", source="points", points_before=5, points_after=4)
check(br.allowed == True, "P13-3 allowed")
check(br.source == "points", "P13-3 source")
check(br.points_before == 5, "P13-3 points_before")
check(br.points_after == 4, "P13-3 points_after")

# T-P13-4: main.py _db_save_error flag 存在（源码级校验）
print("=== T-P13-4: _db_save_error flag 存在 ===")
import main as _main
src = inspect.getsource(_main.analyze_location)
check("_db_save_error" in src, "P13-4 _db_save_error 在 analyze_location 中定义")
check("_db_save_ok" in src, "P13-4 _db_save_ok 在 analyze_location 中使用")
check("DB_SAVE_FAILED" in src, "P13-4 DB_SAVE_FAILED RuntimeError 存在")
check("DB保存失败" in src or "DB save" in src.lower(), "P13-4 DB保存失败在退款条件中")

# T-P13-5: PDF unlock 并发安全（逻辑级校验）
print("=== T-P13-5: PDF unlock 逻辑安全 ===")
# 验证 check_billing_access 不自行 commit（依赖调用方 commit/rollback）
ba_src = inspect.getsource(check_billing_access)
# 去除注释行后检查：check_billing_access 不应自行 commit
ba_code = '\n'.join(l for l in ba_src.split('\n')
    if not l.strip().startswith('#') and not l.strip().startswith('"""') and '调用方' not in l)
has_commit = 'db_session.commit()' in ba_code or 'db.commit()' in ba_code
check(not has_commit,
      "P13-5 check_billing_access 不自行 commit（调用方控制事务边界）")

# ═══════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print(f"TOTAL: {p} PASS, {f} FAIL")
if f == 0:
    print("ALL TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({f} failures)")
    sys.exit(1)
