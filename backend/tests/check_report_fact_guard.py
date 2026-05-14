"""
P0 + P2 报告事实校验 — 自测套件
验证 check_poi_name_hallucination 与 check_poi_context_mismatch 行为
"""
import sys, os, importlib.util

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
print(f"\n{'='*50}")
print(f"TOTAL: {p} PASS, {f} FAIL")
if f == 0:
    print("ALL TESTS PASSED")
else:
    print(f"SOME TESTS FAILED ({f} failures)")
    sys.exit(1)
