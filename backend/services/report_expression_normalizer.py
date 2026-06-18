"""
表达归位 + 数据生态矛盾解释 — 确定性函数，不依赖 LLM。
只做文本归位，不改评分、不改 prompt、不删风险。
"""
import re as _re

_RISK_TRIGGER_WORDS = {"但", "不过", "同时需", "需核验", "风险", "低客流", "只有"}

_RISK_PATTERN = _re.compile(
    r'^(.*?)(但|不过|同时需|需核验|风险|低客流|只有|除非)(.+)$'
)


def _has_risk_phrasing(sentence: str) -> bool:
    """句子是否含风险/转折语气。"""
    return any(kw in sentence for kw in _RISK_TRIGGER_WORDS)


def _split_advantage_risk(sentence: str):
    """拆分优势句：转折前纯正向 → advantages，转折后 → risk/pending。
    Returns (keep_in_advantage: bool, cleaned_advantage: str, moved_to_risk: str or None)
    """
    m = _RISK_PATTERN.match(sentence)
    if not m:
        return True, sentence, None

    prefix = m.group(1).strip().rstrip("，,;； ")
    connector = m.group(2)
    suffix = m.group(3).strip().lstrip("，,;； ")

    # 转折前是否独立正向事实（至少 5 字，不含风险语气词）
    if len(prefix) >= 5 and not _has_risk_phrasing(prefix):
        return True, prefix, suffix
    # prefix 太短或本身就含风险语气 → 整句移出
    return False, "", sentence


def normalize_advantage_risk_phrasing(report: dict) -> dict:
    """将 advantages 中含风险语气的句子拆分归位。不删除任何信息。"""
    advantages = report.get("advantages") or []
    disadvantages = report.get("disadvantages") or []
    # 收集被拆出的风险片段
    risk_notes = list(report.get("risk_notes") or [])

    new_adv = []
    for sent in advantages:
        if not isinstance(sent, str) or not sent.strip():
            new_adv.append(sent)
            continue
        keep, cleaned, moved = _split_advantage_risk(sent)
        if cleaned:
            new_adv.append(cleaned)
        if moved:
            risk_notes.append(moved)

    # 去重风险片段
    seen = set()
    unique_risks = []
    for r in risk_notes:
        if r not in seen:
            seen.add(r)
            unique_risks.append(r)

    report["advantages"] = new_adv
    # 把移出的风险合并到 disadvantages 后面（不覆盖已有）
    existing_dis = set(str(d) for d in disadvantages)
    for r in unique_risks:
        if r not in existing_dis:
            disadvantages.append(r)
    report["disadvantages"] = disadvantages
    report["risk_notes"] = unique_risks

    # decision_snapshot.top_strength 不得选含风险语气的句子
    ds = report.get("decision_snapshot") or {}
    ts = ds.get("top_strength", "")
    if ts and _has_risk_phrasing(str(ts)):
        # 用第一个 pure advantage 替换
        for adv in (report.get("advantages") or []):
            if isinstance(adv, str) and not _has_risk_phrasing(adv):
                ds["top_strength"] = adv
                break
        else:
            ds["top_strength"] = "基础商业条件可用，需现场核验补充判断"
    report["decision_snapshot"] = ds

    return report


# ═══════════════════════════════════════════════════════════════
# 数据生态矛盾解释
# ═══════════════════════════════════════════════════════════════

def add_demand_contradiction_note(report: dict, real_data: dict) -> dict:
    """外圈商业活跃但近场客源弱时，追加客源解释。"""
    r = real_data or {}
    s5 = r.get("stats_500m", {}) or {}
    s10 = r.get("stats_1000m", {}) or {}

    res_500 = int(s5.get("residential", 0) or 0)
    office_500 = int(s5.get("office", 0) or 0)
    restaurants_1k = int(s10.get("restaurants", 0) or 0)
    hotels_1k = int(s10.get("hotels", 0) or 0)
    schools_1k = int(s10.get("schools", 0) or 0)
    bus_1k = int(s10.get("bus", 0) or 0)

    # 触发条件：外圈活跃但近场弱
    outer_active = (restaurants_1k >= 50 or hotels_1k >= 8 or schools_1k >= 5 or bus_1k >= 10)
    inner_weak = (res_500 < 5 and office_500 < 3)

    if not (outer_active and inner_weak):
        return report

    # 跨业态客源解释
    bt = str(report.get("business_type") or report.get("industry") or "")

    # 餐饮类
    if any(kw in bt for kw in ["小吃","快餐","餐饮","正餐","火锅","烧烤","中餐","茶饮","咖啡","烘焙","甜品"]):
        explanation = (
            f"1000m内餐饮{restaurants_1k}家、酒店{hotels_1k}家、学校{schools_1k}所，"
            f"但500m住宅仅{res_500}个、办公{office_500}栋，近场常住客源弱。"
            f"可能客源：学校时段流、外卖半径补量、酒店短停客、过路自然流量。"
            f"须现场核验午晚高峰实际到店客流，不可仅凭外圈数据判断。"
        )
    # 零售类
    elif any(kw in bt for kw in ["便利","超市","生鲜","零售","服装","数码","眼镜","百货"]):
        explanation = (
            f"外圈商业活跃但500m住宅仅{res_500}个、办公{office_500}栋，"
            f"近场人口支撑不足。可能客源：通勤过路流、目的性消费、社区补给、临街可见性。"
            f"须核验主出入口动线是否经过门前及周边入住率。"
        )
    # 服务类
    elif any(kw in bt for kw in ["美","发","宠","健身","洗衣","诊所","家政","维修","SPA"]):
        explanation = (
            f"外圈节点活跃但近场常住人口偏弱（住宅{res_500}、办公{office_500}）。"
            f"可能客源：3km会员储值半径、社区/办公稳定需求、复购到店便利性。"
            f"须核验周边小区消费力和同类门店会员活跃度。"
        )
    # 休闲娱乐
    elif any(kw in bt for kw in ["酒","KTV","网吧","剧本","密室","台球","桌游","电玩","轰趴","VR","夜"]):
        explanation = (
            f"外圈商业节点密集但近场居住/办公弱（住宅{res_500}、办公{office_500}）。"
            f"可能客源：目的性到访、商圈停留、夜间流量。"
            f"须核验深夜可达性、周边居民投诉风险及合规条件。"
        )
    else:
        explanation = (
            f"1000m内商业节点活跃（餐饮{restaurants_1k}、酒店{hotels_1k}），"
            f"但500m住宅仅{res_500}个、办公{office_500}栋，近场承接力弱。"
            f"须现场验证目标客群实际存在量。"
        )

    report["demand_contradiction_note"] = explanation
    return report
