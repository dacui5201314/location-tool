"""
统一首屏决策服务 — 确定性函数，不依赖 LLM。
所有报告（normal / retry / fallback）使用同一个 compute_decision_snapshot()。

# verdict 三档阈值（严格只按 score_n）：
#   score_n >= 60: 可优先现场核验
#   40 <= score_n <= 59: 谨慎考察
#   score_n < 40: 应列为低优先级候选点
# 阈值不得依赖 LLM 输出或前端展示文案。
# 竞品、客流、人口支撑等只影响 one_sentence / fit_condition / stop_condition，不影响 verdict 档位。
# P1: fit_condition / stop_condition 按生意模型族群差异化。
"""
import re as _re
from services.business_model_service import classify_business_model_family

_BANNED_REPLACEMENTS = [
    ("最终决策", "后续判断"),
    ("建议推进", "建议继续现场核验"),
    ("可以投资", "可作为候选点继续核验"),
    ("值得投资", "可作为候选点继续核验"),
    ("强烈建议", "需结合现场核验"),
    ("推荐入驻", "需结合现场核验"),
    ("推荐开店", "需结合现场核验"),
    ("可以放心", "需结合现场核验"),
    # P1: 0竞品过度乐观表达
    ("市场空白明显", "近场无同类门店"),
    ("先发优势明显", "近场供给较少"),
    ("先发优势", "近场供给较少"),
    ("品类切入空间较好", "品类空间需结合需求侧核验"),
    ("竞争环境宽松", "近场竞品较少但远场竞争不可忽视"),
]


def _sanitize(text: str) -> str:
    """清洗用户可见字段中的禁词，做保守替换不删整句。"""
    for banned, replacement in _BANNED_REPLACEMENTS:
        text = text.replace(banned, replacement)
    return text


def _int(v, default=0):
    try: return int(v)
    except: return default


def compute_decision_snapshot(score, real_data, business_type="", brand_name="",
                              advantages=None, disadvantages=None, action_plan=None,
                              is_fallback=False):
    """确定性生成 decision_snapshot。verdict 严格只由 score_n 决定。"""

    r = real_data or {}
    dc_200 = _int(r.get("direct_competitors_200m", 0))
    dc_500 = _int(r.get("direct_competitors_500m", 0))
    dc_1000 = _int(r.get("direct_competitors_1000m", 0))
    s5 = r.get("stats_500m", {}) or {}
    res_500 = _int(s5.get("residential", 0))
    office_500 = _int(s5.get("office", 0))
    school_500 = _int(s5.get("schools", 0))

    adv = advantages or []
    dis = disadvantages or []
    acts = action_plan or []

    score_n = max(0, min(100, _int(score)))

    # ── verdict（严格只按 score_n 三档）──
    if score_n >= 60:
        verdict = "可优先现场核验"
    elif score_n >= 40:
        verdict = "谨慎考察"
    else:
        verdict = "应列为低优先级候选点"

    # ── one_sentence（竞品/客流/人口影响描述但不改档位）──
    if verdict == "可优先现场核验":
        one_sentence = (
            f"当前点位综合评分较好（{score_n}分），200米直接竞品{dc_200}家，"
            f"500米内居住{res_500}个小区、办公{office_500}栋。"
            f"建议重点核验午晚高峰门前实际客流和租金条件，核验通过可作为优先候选点。"
        )
    elif verdict == "谨慎考察":
        reason = ""
        if dc_200 > 15:
            reason = f"200米直接竞品{dc_200}家较密集"
        elif dc_1000 > 10:
            reason = f"1000米同品类门店{dc_1000}家较多"
        elif res_500 < 5 and office_500 < 5:
            reason = "常住和办公人口偏少"
        else:
            reason = "部分指标存在不确定性"
        one_sentence = (
            f"当前点位表现中等（{score_n}分），{reason}。"
            f"建议重点核验租金和实际客流，核验通过且租金在预算内可作为候选点继续核验，"
            f"否则应先对比其他候选点。"
        )
    else:
        reason = ""
        if dc_200 > 15:
            reason = "200米直接竞品过于密集"
        elif dc_1000 > 15:
            reason = "1000米同品类竞争激烈"
        elif res_500 < 3 and office_500 < 3:
            reason = "周边人口和办公支撑严重不足"
        else:
            reason = "综合数据表现偏弱"
        one_sentence = (
            f"当前点位应列为低优先级候选点（{score_n}分），{reason}。"
            f"除非租金明显低于同商圈、目标客群实测达标，否则应先对比其他候选点。"
        )

    # ── top_strength / top_risk ──
    top_strength = adv[0] if adv else "基础商业条件可用，需现场核验补充判断"
    top_risk = dis[0] if dis else "数据依据有限，需实地核验后确认"

    # ── next_action ──
    if acts:
        if isinstance(acts[0], dict):
            next_action = acts[0].get("title", "安排现场客流实测")
        else:
            next_action = str(acts[0])
    else:
        next_action = "安排工作日午晚高峰时段现场实测门前客流"

    # ── P1: fit_condition / stop_condition（按生意模型族群差异化）──
    family = classify_business_model_family(business_type, brand_name)
    if family == "education_childcare":
        if verdict == "可优先现场核验":
            fit_condition = "周边小学步行5分钟内可达且动线安全，周边低年级家庭密度足够，合规资质可办理，租金可控"
            stop_condition = "周边小学距离偏远或动线不安全，已有多家成熟托管无差异化空间，或合规无法满足"
        elif verdict == "谨慎考察":
            fit_condition = "周边小学和家庭密度经核验成立，合规和空间条件基本满足，租金可控"
            stop_condition = "周边小学客源不足、动线不安全、或暗竞品已充分覆盖且无差异化空间"
        else:
            fit_condition = "租金显著低于同地段、附近有新建小学或大型社区带来增量需求"
            stop_condition = "周边小学弱且家庭密度不足、合规无法满足、或已有托管全覆盖"
    elif family == "snack_fast_food":
        if verdict == "可优先现场核验":
            fit_condition = "午市客流实测成立、租金低、1-2人可运营、外卖可覆盖晚餐缺口"
            stop_condition = "午市客流低于预期、或月租金远超同商圈平均水平"
        elif verdict == "谨慎考察":
            fit_condition = "租金低、午市学校/办公客流实测成立、外卖可补充晚餐"
            stop_condition = "租金高、晚餐和周末客流弱、外卖出单不足时不应优先推进"
        else:
            fit_condition = "租金显著低于同商圈、目标客群实测远超预期、或有强线上引流能力"
            stop_condition = "目标客群实测持续偏低、租金占比过高、且外卖条件不佳"
    else:
        # 通用逻辑
        if verdict == "可优先现场核验":
            fit_condition = "目标客群实测达标，且月租金在预算范围内"
            stop_condition = "门前实测客流明显低于预期，或月租金远超同商圈平均水平"
        elif verdict == "谨慎考察":
            fit_condition = "目标客群实际经过量达到预期，且租金可控"
            stop_condition = "目标客群实测明显不足，或租金占比超过营收20%且无议价空间"
        else:
            fit_condition = "租金显著低于同商圈、目标客群实测远超预期，或有强线上引流能力"
            stop_condition = "目标客群实测持续偏低，且经营条件难以改善"

    if is_fallback:
        fit_condition += "（本报告为初筛版参考）"

    # ── sanitize 所有用户可见字段 ──
    return {
        "verdict": _sanitize(verdict),
        "one_sentence": _sanitize(one_sentence),
        "score": score_n,
        "top_strength": _sanitize(top_strength),
        "top_risk": _sanitize(top_risk),
        "next_action": _sanitize(next_action),
        "fit_condition": _sanitize(fit_condition),
        "stop_condition": _sanitize(stop_condition),
    }
