"""
报告事实一致性校验（纯函数，仅依赖标准库 json / re）。
可被 main.py 和 check_report_fact_guard.py 分别导入，无需 FastAPI / AMap / LLM 依赖。
"""
import json as _json
import re


def validate_report_fact_consistency(result: dict, real_data: dict) -> list[str]:
    """校验 LLM 报告中的数字与 real_data 是否一致。返回 fact_errors 列表。"""
    fact_errors = []

    # 1. dimension_scores 结构
    dims = result.get("dimension_scores", [])
    if not isinstance(dims, list) or len(dims) < 8:
        fact_errors.append(f"dimension_scores 不足8维(仅{len(dims) if isinstance(dims, list) else 0}维)")

    # 2. 拼 full_text
    details = result.get("details", {}) or {}
    exec_summary = result.get("executive_summary", {}) or {}
    full_text = (
        _json.dumps(details, ensure_ascii=False) + " " +
        _json.dumps(result.get("advantages", []), ensure_ascii=False) + " " +
        _json.dumps(result.get("disadvantages", []), ensure_ascii=False) + " " +
        _json.dumps(exec_summary, ensure_ascii=False) + " " +
        _json.dumps(result.get("action_plan", []), ensure_ascii=False) + " " +
        str(result.get("summary", ""))
    )
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
            elif expected > 0 and reported > expected * 3:
                return [f"{field_path}={expected} but report says {reported}{m.group(2)} (>3x) in '{sentence[:40]}'"]
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

    return fact_errors
