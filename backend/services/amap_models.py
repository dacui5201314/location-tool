"""数据结构：LocationData 与城市拓扑参考数据。"""
from dataclasses import dataclass, field

# ★ 中国已开通地铁城市集合（2026年基准）
_SUBWAY_CITIES = {
    "北京", "上海", "广州", "深圳", "成都", "重庆", "杭州", "武汉", "西安",
    "郑州", "南京", "天津", "苏州", "长沙", "沈阳", "青岛", "宁波", "合肥",
    "南宁", "昆明", "无锡", "福州", "厦门", "大连", "长春", "南昌", "贵阳",
    "济南", "兰州", "徐州", "石家庄", "太原", "洛阳", "呼和浩特", "温州",
    "绍兴", "芜湖", "南通", "佛山", "东莞", "乌鲁木齐", "哈尔滨",
    "常州", "金华", "嘉兴", "台州", "咸阳", "珠海",
    "香港", "澳门", "台北", "新北", "桃园", "台中", "高雄",
}


def _city_has_subway(city_name: str) -> bool:
    """判断城市是否属于已开通地铁城市。city_name 为空或无法匹配时默认 True（不惩罚）。"""
    if not city_name:
        return True
    for sc in _SUBWAY_CITIES:
        if sc in city_name:
            return True
    return False


@dataclass
class LocationData:
    address: str = ""
    city: str = ""
    district: str = ""
    township: str = ""
    nearby_roads: list = field(default_factory=list)
    business_areas: list = field(default_factory=list)
    building_type: str = ""
    poi_counts: dict = field(default_factory=dict)
    poi_lists: dict = field(default_factory=dict)
    hot_brands: list = field(default_factory=list)
    stats_200m: dict = field(default_factory=dict)
    stats_500m: dict = field(default_factory=dict)
    stats_1000m: dict = field(default_factory=dict)
    # 严谨度框架 → 四级POI分类
    direct_competitors_200m: int = 0
    direct_competitors_500m: int = 0
    direct_competitors_1000m: int = 0
    direct_competitor_list: list = field(default_factory=list)
    direct_competitor_list_200m: list = field(default_factory=list)
    direct_competitor_list_500m: list = field(default_factory=list)
    direct_competitor_list_1000m: list = field(default_factory=list)
    substitute_competitors_200m: int = 0
    substitute_competitors_500m: int = 0
    substitute_competitors_1000m: int = 0
    substitute_list: list = field(default_factory=list)
    substitute_list_200m: list = field(default_factory=list)
    substitute_list_500m: list = field(default_factory=list)
    substitute_list_1000m: list = field(default_factory=list)
    traffic_anchors_200m: int = 0
    traffic_anchors_500m: int = 0
    traffic_anchors_1000m: int = 0
    traffic_anchor_list: list = field(default_factory=list)
    traffic_anchor_list_200m: list = field(default_factory=list)
    traffic_anchor_list_500m: list = field(default_factory=list)
    traffic_anchor_list_1000m: list = field(default_factory=list)
    irrelevant_excluded: int = 0
    data_quality_notes: list = field(default_factory=list)
    # 旧字段保留兼容
    competitors_200m: int = 0
    competitors_500m: int = 0
    competitors_1000m: int = 0
    competitor_list: list = field(default_factory=list)
    # 双轨制：原始计数（脱水前）
    raw_poi_counts: dict = field(default_factory=dict)
    raw_stats_200m: dict = field(default_factory=dict)
    raw_stats_500m: dict = field(default_factory=dict)
    raw_stats_1000m: dict = field(default_factory=dict)
    # 城市地铁适用性
    city_has_subway: bool = True   # 默认 True，发现无地铁时改为 False
    subway_applicable: bool = True # 默认 True，city_has_subway=False 时改为 False
