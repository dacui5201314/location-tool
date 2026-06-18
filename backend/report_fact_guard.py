"""
报告事实一致性校验（纯函数，仅依赖标准库 json / re）。
可被 main.py 和 check_report_fact_guard.py 分别导入，无需 FastAPI / AMap / LLM 依赖。
"""
import json as _json
import re


# ═══════════════════════════════════════════════════════════════
# 统一用户可见文本构造
# ═══════════════════════════════════════════════════════════════

_USER_VISIBLE_FIELDS = [
    "details", "advantages", "disadvantages", "executive_summary",
    "action_plan", "summary", "location_profile", "location_fundamentals",
    "business_model_snapshot", "decision_snapshot", "field_checklist", "evidence_summary",
    "risk_notes", "demand_contradiction_note",
]


def build_user_visible_report_text(result: dict) -> str:
    """统一构造用户可见报告字段的文本，供所有 guard 扫描使用。
    不包含 real_data 等内部原始数据。
    """
    parts = []
    for field in _USER_VISIBLE_FIELDS:
        val = result.get(field)
        if val is None:
            continue
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, (list, dict)):
            parts.append(_json.dumps(val, ensure_ascii=False))
        else:
            parts.append(str(val))
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════
# 主校验入口
# ═══════════════════════════════════════════════════════════════

def validate_report_fact_consistency(result: dict, real_data: dict) -> list[str]:
    """校验 LLM 报告中的数字与 real_data 是否一致。返回 fact_errors 列表。"""
    fact_errors = []

    # 1. dimension_scores 结构
    dims = result.get("dimension_scores", [])
    if not isinstance(dims, list) or len(dims) < 8:
        fact_errors.append(f"dimension_scores 不足8维(仅{len(dims) if isinstance(dims, list) else 0}维)")

    # 2. 统一构造用户可见文本
    full_text = build_user_visible_report_text(result)

    sentences = re.split(r'[。，；;、\n]+', full_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    # 3. 半径识别
    R200 = re.compile(r'200米|200m|贴身')
    R500 = re.compile(r'500米|500m|步行圈')
    R1K  = re.compile(r'1km|1000米|1000m')
    GENERIC = re.compile(r'附近|周边|区域内|范围内|周围')

    def _get_radius(sentence):
        if R200.search(sentence): return "200m"
        if R500.search(sentence): return "500m"
        if R1K.search(sentence): return "1000m"
        if GENERIC.search(sentence): return "1000m"
        return None

    def _check_sentence(sentence, field_path, expected, radius, subject_kw, units):
        sent_radius = _get_radius(sentence)
        if sent_radius != radius:
            return []
        if not any(kw in sentence for kw in subject_kw):
            return []
        unit_pat = "|".join(units)
        for m in re.finditer(rf'(\d+)\s*({unit_pat})', sentence, re.IGNORECASE):
            reported = int(m.group(1))
            if expected == 0 and reported > 0:
                return [f"{field_path}={expected} but report says {reported}{m.group(2)} in '{sentence[:40]}'"]
            elif expected > 0:
                limit = max(expected + 3, expected * 2)
                if reported > limit:
                    return [f"{field_path}={expected} but report says {reported}{m.group(2)} (>{limit}) in '{sentence[:40]}'"]
        return []

    s2 = real_data.get("stats_200m", {}) or {}
    s5 = real_data.get("stats_500m", {}) or {}
    s10 = real_data.get("stats_1000m", {}) or {}

    # 4. 逐句扫描：direct / substitute / anchor / stats
    for sent in sentences:
        # 直接竞品
        for radius, dc_field in [("200m","direct_competitors_200m"),("500m","direct_competitors_500m"),("1000m","direct_competitors_1000m")]:
            expected = real_data.get(dc_field)
            if expected is not None:
                fact_errors += _check_sentence(sent, dc_field, int(expected), radius,
                    ("直接竞品","同类竞品","同品类竞品","竞争品牌","同品类门店","同业竞品"), ("家",))
        # 替代竞品
        for radius, sc_field in [("200m","substitute_competitors_200m"),("500m","substitute_competitors_500m"),("1000m","substitute_competitors_1000m")]:
            expected = real_data.get(sc_field)
            if expected is not None:
                fact_errors += _check_sentence(sent, sc_field, int(expected), radius,
                    ("替代消费","替代业态","替代压力","替代竞争","分流压力","非同业态竞争"), ("家",))
        # 客流锚点
        for radius, ta_field in [("200m","traffic_anchors_200m"),("500m","traffic_anchors_500m"),("1000m","traffic_anchors_1000m")]:
            expected = real_data.get(ta_field)
            if expected is not None:
                fact_errors += _check_sentence(sent, ta_field, int(expected), radius,
                    ("客流锚点","客流来源","人流导入","导流","流量锚点"), ("个",))
        # 基础设施 POI
        for radius, stats_dict in [("200m",s2),("500m",s5),("1000m",s10)]:
            for cat, keywords, units in [
                ("subway",("地铁站","地铁","轨道交通"),("个","座","条")),
                ("bus",("公交站","公交线路","公交车"),("个","条")),
                ("schools",("学校","中小学","大学","学院","高校","校区"),("所","个")),
                ("hospitals",("医院","医疗机构","三甲","综合医院"),("家","所","个")),
                ("residential",("住宅小区","小区","社区","居民区"),("个","座")),
                ("office",("写字楼","办公楼","商务楼","办公区"),("栋","座","幢")),
            ]:
                expected = stats_dict.get(cat)
                if expected is not None:
                    fact_errors += _check_sentence(sent, f"stats_{radius}.{cat}", int(expected), radius, keywords, units)

    # 5. 异常大数字
    details = result.get("details", {}) or {}
    for key in ("competition","population_density","traffic_accessibility","traffic_flow"):
        txt = str(details.get(key, ""))
        big_nums = re.findall(r'(\d{4,})\s*(家|个|所|栋|条|辆)', txt)
        if big_nums:
            fact_errors.append(f"{key}中出现异常大数字: {big_nums[:3]}")

    # 6. 旧口径 competitors_* 检测
    rigor_enabled = real_data.get("rigor_enabled", False)
    if rigor_enabled:
        for old_field in ("competitors_200m","competitors_500m","competitors_1000m"):
            if old_field in full_text:
                fact_errors.append(f"has_rigor=True but report references old field {old_field}")

    # 7. Phase 12: 禁止推荐/不推荐决策语言
    fact_errors.extend(_check_prohibited_decision_language(full_text))

    # 8. Phase 12: 财务单点精确数字检测
    fact_errors.extend(_check_single_point_financial(full_text))

    # 9. Phase 4N: 半径错配检测 + 小数字严格校验
    fact_errors.extend(check_radius_mismatch(full_text, real_data))
    fact_errors.extend(_validate_small_counts(full_text, real_data))

    return fact_errors


# ═══════════════════════════════════════════════════════════════
# Phase 12: 禁止推荐/不推荐决策语言
# ═══════════════════════════════════════════════════════════════
_PROHIBITED_DECISION_PATTERNS = [
    "推荐开店","不推荐开店","建议推进","强烈推荐","可以投资","值得投资","最终决策",
    "建议在此开店","建议立即入驻","强烈建议","推荐入驻","可以放心",
]
_ALLOWED_SAFE_PATTERNS = [
    "选址初筛参考","需线下核验","需线下实地核验","风险点","候选点","待验证",
]


def _check_prohibited_decision_language(full_text: str) -> list[str]:
    errors = []
    for pat in _PROHIBITED_DECISION_PATTERNS:
        if pat in full_text:
            errors.append(f"[DECISION] 报告出现禁止的决策语言: '{pat}'")
    return errors


def check_prohibited_decision_language(report_text: str) -> list[str]:
    return _check_prohibited_decision_language(report_text)


# ═══════════════════════════════════════════════════════════════
# Phase 12: 财务单点精确数字检测
# ═══════════════════════════════════════════════════════════════
def _check_single_point_financial(full_text: str) -> list[str]:
    errors = []
    financial_kw = ["月净利","月营收","月流水","月利润","年利润","日净利","回本周期","回本",
                    "月毛利","月纯利","净利润","净利","净赚","月固定成本","月总成本"]
    for kw in financial_kw:
        for m in re.finditer(rf'{kw}\s*[约大约]?\s*([\d.]+)\s*(万|元|天|月|%)', full_text):
            num_str = m.group(1)
            unit = m.group(2) or ""
            start, end = m.start(), m.end()
            context = full_text[max(0, start - 40):min(len(full_text), end + 40)]
            if re.search(r'(\d+[-~至]\d+|[-至]+\d+)', context):
                continue
            safe_kw = ("模型假设","需核验","置信度","不代表承诺")
            if any(k in context for k in safe_kw):
                continue
            # 百分比阈值是红线/参考值（如"月营收20%"），非财务结算数字 → 允许
            if unit == "%" and re.search(r'(租金|营收)\s*占比|超过.*%|红线|不超过|参考', context):
                continue
            errors.append(f"[FINANCE] 单点精确财务数字: '{m.group(0)}' in '{context[:60]}'")
            if len(errors) >= 3:
                break
        if len(errors) >= 3:
            break
    return errors


def check_single_point_financial(report_text: str) -> list[str]:
    return _check_single_point_financial(report_text)


# ═══════════════════════════════════════════════════════════════
# Phase 4N: 半径错配检测 — 类别感知版本
# ═══════════════════════════════════════════════════════════════

_RADIUS_KEYWORDS = {
    "500m": ["500m", "500米", "五百米", "500 米"],
    "200m": ["200m", "200米", "二百米", "200 米"],
    "1000m": ["1000m", "1000米", "一千米", "1km", "1000 米"],
}

_RADIUS_STATS_MAP = {
    "200m": "stats_200m",
    "500m": "stats_500m",
    "1000m": "stats_1000m",
}

# 类别关键词 → stats 字段映射（与 validate_report_fact_consistency 的 mapping 一致）
_CATEGORY_MAP = [
    ("bus", ("公交站","公交线路","公交车"), ("个","条")),
    ("subway", ("地铁站","地铁","轨道交通"), ("个","座","条")),
    ("schools", ("学校","中小学","大学","学院","高校","校区"), ("所","个")),
    ("hospitals", ("医院","医疗机构","三甲","综合医院"), ("家","所","个")),
    ("residential", ("住宅小区","小区","社区","居民区"), ("个","座")),
    ("office", ("写字楼","办公楼","商务楼","办公区"), ("栋","座","幢")),
    ("shopping", ("商业体","商场","购物中心","商圈"), ("个","座")),
    ("parking", ("停车场","停车位","停车设施"), ("个","处")),
    ("hotels", ("酒店","宾馆","旅馆","住宿"), ("家","个")),
    ("restaurants", ("餐饮","餐厅","饭店","餐馆"), ("家","个")),
]

# 纯数字关键词（忽略）
_RADIUS_NUMBER_KEYWORDS = {"200", "500", "1000", "1km", "1KM"}


def _find_radius_in_sentence(sentence: str):
    """返回句子中出现的第一个半径关键词和对应的半径key。"""
    for radius_key, labels in _RADIUS_KEYWORDS.items():
        for label in labels:
            idx = sentence.find(label)
            if idx >= 0:
                return radius_key, label, idx
    return None, None, -1


def _find_category_in_sentence(sentence: str):
    """返回句子中命中的类别关键词和对应的 stats 字段名。"""
    for cat, keywords, units in _CATEGORY_MAP:
        for kw in keywords:
            if kw in sentence:
                return cat, keywords, units
    return None, None, None


def _split_into_radius_segments(sentence: str):
    """将含多个半径关键词的句子拆成逐半径的短片段。
    例如 '500米内2个公交站，1000米内5个公交站' →
         [('500m','500米内2个公交站'), ('1000m','1000米内5个公交站')]
    """
    # 找到所有半径关键词的位置
    matches = []
    for radius_key, labels in _RADIUS_KEYWORDS.items():
        for label in labels:
            idx = sentence.find(label)
            if idx >= 0:
                matches.append((idx, label, radius_key))
    if not matches:
        return [(None, sentence)]

    matches.sort(key=lambda x: x[0])
    segments = []
    for i, (pos, label, rk) in enumerate(matches):
        end = matches[i+1][0] if i+1 < len(matches) else len(sentence)
        seg = sentence[pos:end].strip().rstrip("，,;； ")
        segments.append((rk, seg))
    return segments


def check_radius_mismatch(report_text: str, real_data: dict) -> list[str]:
    """检测半径错配：文案写500m但数值来自1000m（类别感知，必须同时命中半径+类别+数字单位）。"""
    errors = []
    reported_text = str(report_text)
    sentences = re.split(r'[。\n]+', reported_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    for sent in sentences:
        # 拆分为逐半径片段
        segments = _split_into_radius_segments(sent)
        for radius_key, seg in segments:
            if not radius_key:
                continue
            cat, _, units = _find_category_in_sentence(seg)
            if not cat:
                continue

            unit_pat = "|".join(units)
            for m in re.finditer(rf'(\d+)\s*({unit_pat})', seg):
                claimed = int(m.group(1))
                if claimed <= 0:
                    continue
                if str(claimed) in _RADIUS_NUMBER_KEYWORDS:
                    continue

                current_stats_key = _RADIUS_STATS_MAP.get(radius_key)
                current_stats = (real_data.get(current_stats_key, {}) or {})
                current_val = int(current_stats.get(cat, -1))

                for other_radius, other_stats_key in _RADIUS_STATS_MAP.items():
                    if other_radius == radius_key:
                        continue
                    other_stats = (real_data.get(other_stats_key, {}) or {})
                    other_val = int(other_stats.get(cat, -1))
                    if other_val == claimed and current_val != claimed:
                        errors.append(
                            f"[RADIUS-MISMATCH] 文案写{_RADIUS_KEYWORDS[radius_key][0]}但{cat}={claimed}实际来自{other_radius}"
                            f"（{radius_key}内{cat}={current_val}，{other_radius}内{cat}={claimed}）"
                            f" in '{seg[:60]}'"
                        )
    return errors[:10]


def _validate_small_counts(report_text: str, real_data: dict) -> list[str]:
    """小数字（0-3）严格校验：要求数字+单位与类别关键词相邻出现。"""
    errors = []
    reported_text = str(report_text)
    sentences = re.split(r'[。\n]+', reported_text)
    sentences = [s.strip() for s in sentences if s.strip()]

    for sent in sentences:
        segments = _split_into_radius_segments(sent)
        for radius_key, seg in segments:
            if not radius_key:
                continue
            for cat, keywords, units in _CATEGORY_MAP:
                current_stats_key = _RADIUS_STATS_MAP.get(radius_key)
                current_stats = (real_data.get(current_stats_key, {}) or {})
                actual = int(current_stats.get(cat, -1))
                if actual < 0 or actual > 3:
                    continue
                unit_pat = "|".join(units)
                kw_pat = "|".join(re.escape(k) for k in keywords)
                # 数字+单位 与 类别关键词 必须在 10 字内相邻
                for m in re.finditer(
                    rf'(\d+)\s*({unit_pat})\s*({kw_pat})|({kw_pat})\s*(\d+)\s*({unit_pat})',
                    seg
                ):
                    claimed_str = m.group(1) or m.group(5)
                    claimed = int(claimed_str)
                    if claimed <= actual:
                        continue
                    if claimed_str in _RADIUS_NUMBER_KEYWORDS:
                        continue
                    ctx = seg[max(0, m.start()-10):m.end()+10]
                    errors.append(
                        f"[SMALL-COUNT] {radius_key}内{cat}={actual} but report says {claimed}"
                        f" in '{ctx[:60]}'"
                    )
    return errors[:10]


# ═══════════════════════════════════════════════════════════════
# Final guard 分类：硬阻断 vs 仅告警
# ═══════════════════════════════════════════════════════════════

_HARD_BLOCK_PREFIXES = [
    "[RADIUS-MISMATCH]",
    "[SMALL-COUNT]",
    "[DECISION]",
    "[FINANCE]",
]

_HARD_BLOCK_PATTERNS = [
    "but report says",
    "has_rigor=True but report",
]


def split_final_guard_issues(issues: list[str]):
    """将最终 guard 问题分为 hard_errors（必须阻断）和 warnings（仅记录）。
    Returns (hard_errors: list[str], warnings: list[str])
    """
    hard = []
    warn = []
    for issue in issues:
        is_hard = False
        for prefix in _HARD_BLOCK_PREFIXES:
            if issue.startswith(prefix):
                is_hard = True
                break
        if not is_hard:
            for pat in _HARD_BLOCK_PATTERNS:
                if pat in issue:
                    is_hard = True
                    break
        if is_hard:
            hard.append(issue)
        else:
            warn.append(issue)
    return hard, warn
