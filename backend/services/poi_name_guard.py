"""
P0 POI 名称引用校验（warning-only）
检查 LLM 报告是否引用了 real_data 中不存在的具体 POI 名称。
不做通用 NER，只在 POI 引用语境中提取后缀命中的候选名，大幅降低误杀。
"""
import re

# POI 名称后缀 — 长后缀在前，避免"中心"误匹配"购物中心"内部
_POI_SUFFIXES = [
    "国际中心","商务中心","购物中心",
    "地铁站","公交站","火车站","汽车站",
    "写字楼","家属院",
    "广场","商场","超市","药房","酒店","宾馆","旅店","民宿","公寓",
    "医院","诊所","卫生院",
    "小学","中学","高中","大学","学院","幼儿园","学校",
    "小区","社区","新村","花园","家园",
    "大厦","中心",
    "店","馆","院","校","园","楼","厦","场","站",
]

# Build regex — boundary + 2-8 CJK chars (non-greedy) + suffix.
# Boundary: start-of-string, non-CJK char, function/preposition word, or position word.
# Non-greedy {2,8}? ensures shortest valid match from each boundary position.
_suffix_alt = '|'.join(_POI_SUFFIXES)
_POI_NAME_BOUNDARY = r'(?:^|[^一-鿿]|[的了在有是将和与及为被把向对从到边近内处旁聚集])'
_POI_NAME_RE = re.compile(
    _POI_NAME_BOUNDARY +
    r'([一-鿿]{2,8}?'
    r'(?:' + _suffix_alt + r'))'
)

# 语境关键词 — 句子必须包含至少一个才扫描。
# 如果不命中任何关键词，说明句子不在 POI 引用语境中，跳过扫描。
_CONTEXT_KEYWORDS = [
    "竞品","同类","同品类","直接竞争","分流",
    "锚点","客流来源","配套",
    "品牌","连锁","门店","旗下",
    "周边","附近",
    "聚集","汇集","分布","设有","开设有","坐落",
]

# 候选名必须不以此开头 — 动词/形容词/数词/量词前缀，排除描述性短语
_NON_NAME_STARTS = re.compile(
    r'^[0-9零一二三四五六七八九十百千万亿几数多少量]'
    r'|^(?:提供|构成|存在|形成|拥有|配套|临近|靠近'
    r'|面向|服务|覆盖|辐射|缺乏|缺少|不足|严重'
    r'|稳定|密集|优质|成熟|新建|老旧|高档|繁华'
    r'|便利|充足|完善|齐全|丰富|良好|优秀|突出'
    r'|作为|属于|具备|带来|产生|包含|包括'
    r'|整个|全部|所有|部分|多数|少数'
    r'|本地|当地|此处|该区域'
    r'|提供|支撑|保障|满足|确保|强化'
    r'|有|了|的|在|是|将|与|和|及|为|被|把|向|对|从|到|含'
    r')'
)

# 泛称黑名单 — 命中 POI 后缀但属于报告术语，不是具体 POI
_GENERIC_BLACKLIST = {
    "周边学校","附近社区","周边医院","附近小区","周边写字楼",
    "商业配套","客流锚点","直接竞品","替代业态","同类门店","同类竞品",
    "周边设施","社区客群","医院客群","学校客群","写字楼客群",
    "主力客群","周边商圈","新建社区","高档小区","老旧小区",
    "周边社区","大型社区","成熟社区",
    "家门店","家店面","家店铺","个门店",
    # 数量词 + POI 后缀 artifact ("6所学校"→"所学校")
    "所学校","家酒店","个小区","个商场","个写字楼",
    "家竞品","个竞品","个锚点",
    # 周边/附近 + POI 后缀泛称
    "周边酒店","附近酒店",
    "周边便利店","附近便利店",
    "周边超市","附近超市",
    "周边商场","附近商场",
    "附近写字楼","附近学校",
    "周边小区","附近医院",
    # 字符串切分 artifact — 非自然 POI 名称
    "大学校","中学校","小学校",
    "大酒店","大医院","大型商场","大型社区",
    # 数据描述 artifact
    "米内写字楼","内写字楼","内酒店","内商场",
    "米内便利店","米内超市","米内商场","米内酒店","米内学校",
    "米内医院","米内小区",
    "内便利店","内超市","内学校","内小区","内医院",
    # "X米内" 距离描述 artifact（含否定/数量干扰字）
    "米内无写字楼","米内无便利店","米内无超市","米内无商场",
    "米内无酒店","米内无学校","米内无医院","米内无小区",
}


# 周边/附近 后的泛称 POI 指代 — 用于识别 "描述性前缀+周边/附近+POI后缀" 假阳性
_GENERIC_REFERENTS = {
    "酒店","写字楼","便利店","超市","商场","学校","医院","小区",
    "社区","地铁站","公交站","宾馆","旅店","民宿","公寓","药房",
    "卫生院","幼儿园","学院","大学","中学","小学","新村","花园",
    "家园","大厦","广场","餐饮","商业","住宿","购物",
    "酒店住宿","写字楼办公","商业配套","医疗配套","教育配套",
    "便利店和超市","酒店和民宿",
}


def _is_generic_candidate(candidate: str) -> bool:
    """检测候选名是否为泛称/描述性短语而非具体 POI 名称。

    规则:
    1. 命中 exact blacklist
    2. 包含 "周边" 或 "附近" 且其后为泛称 POI 指代（描述性前缀未被边界切断时）
    """
    if candidate in _GENERIC_BLACKLIST:
        return True

    for marker in ("周边", "附近"):
        idx = candidate.find(marker)
        if idx < 0:
            continue
        referent = candidate[idx + len(marker):]
        if not referent:
            return True
        if referent in _GENERIC_REFERENTS:
            return True
        # 前缀匹配: "酒店住宿" starts with "酒店" (generic)
        for gr in sorted(_GENERIC_REFERENTS, key=len, reverse=True):
            if referent.startswith(gr):
                rest = referent[len(gr):]
                if not rest or len(rest) <= 3:
                    return True
                break

    return False


def _build_name_allowlist(real_data: dict) -> set:
    """从 real_data 提取所有合法 POI 名称。

    一级: direct_competitor_list / substitute_list / traffic_anchor_list
    二级: hot_brands / nearby_roads
    三级: poi_lists 全部 category
    """
    allowlist = set()

    # 一级
    for key in ("direct_competitor_list","substitute_list","traffic_anchor_list"):
        for entry in real_data.get(key, []) or []:
            name = (entry.get("name") or "").strip()
            if name:
                allowlist.add(name)

    # 二级
    for entry in real_data.get("hot_brands", []) or []:
        name = (entry.get("name") or "").strip()
        if name:
            allowlist.add(name)
    for name in real_data.get("nearby_roads", []) or []:
        name = name.strip()
        if name:
            allowlist.add(name)

    # 三级
    for entries in real_data.get("poi_lists", {}).values():
        for entry in entries or []:
            name = (entry.get("name") or "").strip()
            if name:
                allowlist.add(name)

    return allowlist


def _extract_candidates(sentence: str) -> list:
    """从句子中提取所有命中 POI 后缀的候选名称，排除黑名单和非名称前缀。"""
    candidates = []
    for m in _POI_NAME_RE.finditer(sentence):
        candidate = m.group(1).strip()
        if len(candidate) < 2:
            continue
        if _is_generic_candidate(candidate):
            continue
        if _NON_NAME_STARTS.match(candidate):
            continue
        candidates.append(candidate)
    return candidates


def _deparen_clean(name: str) -> str:
    """去除括号及其内容: 瑞幸咖啡(XX路店) → 瑞幸咖啡"""
    return re.sub(r'[（(][^)）]*[)）]', '', name).strip()


def _matches_allowlist(candidate: str, allowlist: set) -> bool:
    """检查候选名是否匹配 allowlist。

    匹配层级:
    1. 精确匹配
    2. 双方去括号后精确匹配
    3. 去括号后前缀匹配 (>=3字)
    """
    if candidate in allowlist:
        return True

    cand_clean = _deparen_clean(candidate)
    if not cand_clean:
        return False

    for name in allowlist:
        name_clean = _deparen_clean(name)
        if not name_clean:
            continue
        if cand_clean == name_clean:
            return True
        # 长度不足 3 字跳过模糊匹配
        if len(cand_clean) < 3 or len(name_clean) < 3:
            continue
        # 前缀匹配: 任一方是另一方的前缀
        if cand_clean.startswith(name_clean) or name_clean.startswith(cand_clean):
            return True
        # 子串包含: 候选包含 allowlist 名 或 反之 (应对"周边星巴克门店"含"星巴克")
        if name_clean in cand_clean or cand_clean in name_clean:
            return True

    return False


def check_poi_name_hallucination(
    report_text: str,
    real_data: dict,
    strict: bool = False,
) -> list:
    """P0 校验: 检查 LLM 报告是否引用了 real_data 中不存在的具体 POI 名称。

    Args:
        report_text: 报告全文（JSON序列化后的字符串）
        real_data: main.py 中的 real_data dict
        strict: True=返回的列表应被当作 fact_errors 处理; False=仅 warning

    Returns:
        warning/error 字符串列表，空列表=通过
    """
    if not report_text or not real_data:
        return []

    allowlist = _build_name_allowlist(real_data)
    # 仅当 real_data 完全为空时跳过（None / {}）, 空 allowlist 也要校验

    issues = []
    sentences = re.split(r'[。，；;、\n]+', report_text)

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        # 仅扫描包含 POI 引用语境的句子
        if not any(kw in sent for kw in _CONTEXT_KEYWORDS):
            continue

        for candidate in _extract_candidates(sent):
            if _matches_allowlist(candidate, allowlist):
                continue
            issues.append(f"POI名称不在数据源中: {candidate}")

    # 去重保持顺序
    seen = set()
    unique = []
    for issue in issues:
        if issue not in seen:
            seen.add(issue)
            unique.append(issue)
    return unique


# ═══════════════════════════════════════════════════════════════
# P2: 竞品语境误用检测 (warning-only)
# ═══════════════════════════════════════════════════════════════

# 竞品语境关键词
_COMPETITOR_CTX = ["竞品","竞争对手","同类竞品","直接竞争","分流压力"]

# 合法语境 — 替代名称允许出现在替代语境中
_SUBSTITUTE_CTX = ["替代消费","替代压力","替代业态"]

# 合法语境 — 锚点名称允许出现在锚点语境中
_ANCHOR_CTX = ["客流锚点","客流来源"]


def _resolve_category(candidate: str, name_map: dict) -> str | None:
    """将候选名通过 P0 匹配逻辑解析到 name_map 中的真实名称，返回其类别。
    匹配优先级: direct > substitute > anchor (后建覆盖).
    复用 P0 的 _deparen_clean 和模糊匹配逻辑。
    """
    cand_clean = _deparen_clean(candidate)
    if not cand_clean:
        return None

    # 按优先级: 先查 direct, 再 substitute, 最后 anchor
    for category in ("direct", "substitute", "anchor"):
        for name, cat in name_map.items():
            if cat != category:
                continue
            name_clean = _deparen_clean(name)
            if not name_clean:
                continue
            if cand_clean == name_clean:
                return category
            if len(cand_clean) >= 3 and len(name_clean) >= 3:
                if cand_clean.startswith(name_clean) or name_clean.startswith(cand_clean):
                    return category
                if name_clean in cand_clean or cand_clean in name_clean:
                    return category
    return None


def check_poi_context_mismatch(
    report_text: str,
    real_data: dict,
) -> list:
    """P2 校验: 检查 substitute / anchor 名称是否被误写成直接竞品。

    仅在「竞品语境」句子中检测: 提取 POI 候选名, 如果匹配到
    substitute_list 或 traffic_anchor_list 中的名称 → warning.

    Args:
        report_text: 报告全文
        real_data: main.py 中的 real_data dict

    Returns:
        warning 字符串列表, 空列表=通过
    """
    if not report_text or not real_data:
        return []

    # 构建 name → category 映射 (anchor 先建, substitute 覆盖, direct 最后覆盖)
    name_map = {}
    for entry in real_data.get("traffic_anchor_list", []) or []:
        n = (entry.get("name") or "").strip()
        if n:
            name_map[n] = "anchor"
    for entry in real_data.get("substitute_list", []) or []:
        n = (entry.get("name") or "").strip()
        if n:
            name_map[n] = "substitute"
    for entry in real_data.get("direct_competitor_list", []) or []:
        n = (entry.get("name") or "").strip()
        if n:
            name_map[n] = "direct"

    if not name_map:
        return []

    issues = []
    sentences = re.split(r'[。，；;、\n]+', report_text)
    seen = set()

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # 仅检查竞品语境的句子
        is_competitor_ctx = any(kw in sent for kw in _COMPETITOR_CTX)
        if not is_competitor_ctx:
            continue

        # 但排除那些同时也是合法语境的句子（双重语境时以更精确的为准）
        has_sub_ctx = any(kw in sent for kw in _SUBSTITUTE_CTX)
        has_anchor_ctx = any(kw in sent for kw in _ANCHOR_CTX)

        # 路径1: 后缀提取 — 覆盖店/馆/院/校/小区等有后缀名称
        for candidate in _extract_candidates(sent):
            category = _resolve_category(candidate, name_map)
            if category is None:
                continue
            if category == "direct":
                continue
            if category == "substitute" and has_sub_ctx:
                continue
            if category == "anchor" and has_anchor_ctx:
                continue

            issue = f"{category}名称出现在竞品语境中: {candidate}"
            if issue not in seen:
                seen.add(issue)
                issues.append(issue)

        # 路径2: 真实 list 名称直接命中 — 覆盖肯德基/麦当劳/星巴克等无后缀名称
        for name in list(name_map.keys()):
            name_clean = _deparen_clean(name)
            if not name_clean or len(name_clean) < 2:
                continue
            # 检查名称是否出现在句子中（模糊匹配）
            if name_clean not in sent:
                # 尝试前缀匹配: "星巴克门店" 中的 "星巴克"
                found = False
                if len(name_clean) >= 3:
                    for m in re.finditer(r'([一-鿿A-Za-z]{3,})', sent):
                        if m.group(1).startswith(name_clean) or name_clean.startswith(m.group(1)):
                            found = True
                            break
                if not found:
                    continue

            # ★ 通过 _resolve_category 重新解析，确保 direct 优先级覆盖
            category = _resolve_category(name_clean, name_map)
            if category is None:
                continue
            if category == "direct":
                continue
            # 合法语境豁免
            if category == "substitute" and has_sub_ctx:
                continue
            if category == "anchor" and has_anchor_ctx:
                continue

            issue = f"{category}名称出现在竞品语境中: {name}"
            if issue not in seen:
                seen.add(issue)
                issues.append(issue)

    return issues


# ═══════════════════════════════════════════════════════════════
# P3: 直接竞品数量膨胀检测 (warning-only)
# ═══════════════════════════════════════════════════════════════

# 竞品语境关键词（与 P2 对齐）
_P3_COMPETITOR_CTX = ["直接竞品","同类竞品","同品类竞品","竞争对手","直接竞争"]

# 半径标记 → 字段后缀
_P3_RADIUS_MAP = {
    "200m":  ("200m", "200米"),
    "500m":  ("500m", "500米"),
    "1000m": ("1000m", "1000米", "1km", "1公里"),
}

# 模糊修饰前缀 — 如果数字紧跟在以下词之后，跳过（模糊表述）
_VAGUE_PREFIXES = [
    "约", "大约", "近", "左右", "余", "多",
    "几", "数个", "不足", "不到", "超过", "以上",
    "将近", "大概", "大致",
]

# 提取 "X家" 模式，X 为阿拉伯数字
_COUNT_RE = re.compile(r'(\d+)\s*家')


def _has_vague_prefix(sentence: str, match_start: int) -> bool:
    """检查 match_start 之前的字符是否紧邻模糊修饰词。
    允许修饰词与数字之间有 0-1 个中间字符（如 "约有8" 中 "约" 隔了 "有" 仍算模糊）。
    """
    chunk = sentence[max(0, match_start - 4):match_start]
    for vp in _VAGUE_PREFIXES:
        idx = chunk.find(vp)
        if idx < 0:
            continue
        # vp 紧贴数字 或 隔1个字符
        if idx + len(vp) >= len(chunk) or idx + len(vp) + 1 == len(chunk):
            return True
    return False


def _get_p3_radius(sentence: str) -> str | None:
    """从句子中识别半径标记 → "200m"/"500m"/"1000m"。"""
    for radius_key, markers in _P3_RADIUS_MAP.items():
        for mk in markers:
            if mk in sentence:
                return radius_key
    return None


def check_direct_competitor_count_mismatch(
    report_text: str,
    real_data: dict,
) -> list:
    """P3 校验: 检测报告中直接竞品数量是否超过 real_data (warning-only)。

    仅检查「竞品语境 + 精确数字 + 明确半径」的句子。
    仅当 reported > expected 时 warning。
    """
    if not report_text or not real_data:
        return []

    # 预提取期望值
    expected_map = {}
    for radius in ("200m", "500m", "1000m"):
        val = real_data.get(f"direct_competitors_{radius}")
        if val is not None:
            expected_map[radius] = int(val)

    if not expected_map:
        return []

    issues = []
    sentences = re.split(r'[。，；;、\n]+', report_text)
    seen = set()

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # 必须有竞品语境
        if not any(kw in sent for kw in _P3_COMPETITOR_CTX):
            continue

        # 必须有明确半径
        radius = _get_p3_radius(sent)
        if radius is None:
            continue

        expected = expected_map.get(radius)
        if expected is None:
            continue

        # 提取数字
        for m in _COUNT_RE.finditer(sent):
            if _has_vague_prefix(sent, m.start()):
                continue
            reported = int(m.group(1))
            if reported > expected:
                issue = (
                    f"direct_competitors_{radius}={expected} "
                    f"but report says {reported}家 in '{sent[:50]}'"
                )
                if issue not in seen:
                    seen.add(issue)
                    issues.append(issue)

    return issues
