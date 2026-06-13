"""
小餐饮/小吃快餐等业态的替代消费中药店/医疗 POI 过滤。
仅对餐饮相关业态启用保守过滤，不影响非餐饮业态。
"""
import re as _re

_PHARMACY_MEDICAL_KW = [
    "药店", "药房", "医药", "医药超市", "药业", "药品", "药械",
    "医院", "诊所", "门诊", "医疗", "卫生室",
]

_PHARMACY_MEDICAL_CATS = {"pharmacy", "hospitals", "clinics", "medical"}

_FOOD_BIZ_KW = ["小餐饮", "快餐", "小吃", "面馆", "粉店", "麻辣烫", "炸鸡",
                "米线", "凉皮", "肉夹馍", "饺子", "馄饨", "煎饼", "便当",
                "盖浇", "砂锅", "冒菜", "卤味", "鸭脖", "鸡排", "汉堡",
                "中餐", "火锅", "烧烤", "烘焙", "茶饮", "咖啡", "甜品", "餐饮"]


def _is_food_business(business_type: str) -> bool:
    bt = business_type or ""
    for kw in _FOOD_BIZ_KW:
        if kw in bt:
            return True
    return False


def _is_pharmacy_medical(name: str, cat: str = "") -> bool:
    """判定 POI 名称或类别是否属于药店/医疗类。"""
    if cat and cat in _PHARMACY_MEDICAL_CATS:
        return True
    if not name:
        return False
    for kw in _PHARMACY_MEDICAL_KW:
        if kw in name:
            return True
    return False


def filter_substitute_pharmacy(real_data: dict, business_type: str) -> dict:
    """对小餐饮/小吃快餐等业态，从替代消费数据中过滤药店/医疗 POI。

    过滤后重新计算三层半径计数，保证列表长度与计数一致。
    非餐饮业态不做过滤，直接返回原 real_data。
    """
    if not _is_food_business(business_type):
        return real_data

    rd = dict(real_data)

    # ── 过滤 substitute_list ──
    sub_list = list(rd.get("substitute_list", []) or [])
    filtered_list = [x for x in sub_list if not _is_pharmacy_medical(x.get("name", ""), x.get("category", ""))]
    rd["substitute_list"] = filtered_list

    # ── 按半径过滤 + 重算计数 ──
    for radius_key in ("200m", "500m", "1000m"):
        list_key = f"substitute_list_{radius_key}"
        count_key = f"substitute_competitors_{radius_key}"

        if list_key in rd:
            existing = list(rd.get(list_key, []) or [])
            filtered = [x for x in existing if not _is_pharmacy_medical(x.get("name", ""), x.get("category", ""))]
            rd[list_key] = filtered
            rd[count_key] = len(filtered)
        else:
            # 分半径字段不存在，从 filtered_list 按 distance 拆分
            dist_limit = {"200m": 200, "500m": 500, "1000m": 1000}[radius_key]
            radius_list = []
            for x in filtered_list:
                d = x.get("distance")
                try:
                    d_int = int(d)
                except (TypeError, ValueError):
                    continue  # 缺失 distance 不进入计数
                if d_int <= dist_limit:
                    radius_list.append(x)
            rd[list_key] = radius_list
            rd[count_key] = len(radius_list)

    return rd
