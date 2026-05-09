"""
高德地图 Web API 服务 - 获取选址所需的真实 POI 数据
使用单次大范围搜索 + 手动分类，确保数据准确性
"""
import httpx
import re

# 快餐/小吃关键词——高德分类粗放，需按店名强制归入竞品
SNACK_KEYWORDS = [
    "面", "皮", "粉", "饭", "包", "粥", "小吃", "麻辣烫", "炸鸡",
    "米线", "凉皮", "肉夹馍", "饺子", "馄饨", "馒头", "大饼", "煎饼",
    "快餐", "便当", "盖浇", "砂锅", "冒菜", "串串", "卤味", "鸭脖",
    "鸡排", "汉堡", "披萨", "拉面", "刀削面", "拌面", "汤面", "干拌",
    "酸辣粉", "螺蛳粉", "热干面", "小面", "燃面", "臊子面", "油泼面",
    "泡馍", "水盆", "葫芦头", "biangbiang", "擀面皮", "烙面皮", "米皮",
    "蘸水面", "浆水面", "饸饹", "搅团", "鱼鱼", "锅贴", "生煎", "小笼",
    "汤包", "蒸饺", "烧麦", "油条", "豆浆", "豆腐脑", "胡辣汤",
    "麻辣拌", "麻辣香锅", "烤冷面", "手抓饼", "鸡蛋灌饼", "肉灌饼",
    "杂粮煎饼", "掉渣饼", "酱香饼", "葱油饼", "韭菜盒子", "糖糕",
]

def is_snack_competitor(name: str) -> bool:
    """判断POI名称是否属于快餐/小吃竞品"""
    for kw in SNACK_KEYWORDS:
        if kw in name:
            return True
    return False

# 医院名校正：仅保留真正的医疗机构
HOSPITAL_ALLOW = ["医院", "中医院", "妇幼保健院", "社区卫生服务中心", "卫生院", "急救中心"]
HOSPITAL_DENY = ["诊所", "牙科", "门诊", "药店", "药房", "医务室", "体检", "整形", "美容医院", "康复中心"]

def is_real_hospital(name: str) -> bool:
    """名称正向筛选：仅真正的医院通过"""
    for kw in HOSPITAL_DENY:
        if kw in name:
            return False
    for kw in HOSPITAL_ALLOW:
        if kw in name:
            return True
    return False

# 学校名校正：仅保留正规教育机构
SCHOOL_ALLOW = ["小学", "中学", "高中", "大学", "学院", "幼儿园", "学校"]
SCHOOL_DENY = ["培训", "教育中心", "画室", "托管", "驾校", "辅导", "补习", "早教中心", "兴趣班"]

def is_real_school(name: str) -> bool:
    """名称正向筛选：仅正规学校通过"""
    for kw in SCHOOL_DENY:
        if kw in name:
            return False
    for kw in SCHOOL_ALLOW:
        if kw in name:
            return True
    return False

# 写字楼脱水
OFFICE_KEEP = ["大厦", "写字楼", "国际中心", "商务中心", "科创中心", "总部"]
OFFICE_DROP = ["公司", "厂房", "工业园", "制造", "产业园", "仓库", "物流", "公寓"]

def is_real_office(name: str) -> bool:
    for kw in OFFICE_DROP:
        if kw in name:
            return False
    for kw in OFFICE_KEEP:
        if kw in name:
            return True
    return False

# 购物商场脱水
SHOPPING_KEEP = ["购物中心", "百货", "商业街", "步行街", "茂", "商场", "奥特莱斯", "购物广场"]
SHOPPING_DROP = ["建材", "批发", "农贸", "汽配", "五金", "家具", "灯饰", "石材", "印刷", "旧货", "二手"]

def is_real_shopping(name: str) -> bool:
    for kw in SHOPPING_DROP:
        if kw in name:
            return False
    for kw in SHOPPING_KEEP:
        if kw in name:
            return True
    return False

# 住宅小区脱水
RESIDENTIAL_DROP = ["售楼", "中介", "销售中心", "营销中心", "展厅"]

def is_real_residential(name: str) -> bool:
    for kw in RESIDENTIAL_DROP:
        if kw in name:
            return False
    return True

# 酒店住宿脱水
HOTEL_DROP = ["招待所", "农家乐", "农庄", "洗浴", "客栈", "日租房", "钟点房"]

def is_real_hotel(name: str) -> bool:
    for kw in HOTEL_DROP:
        if kw in name:
            return False
    return True
import os
from dataclasses import dataclass, field
from services.runtime_config import get_config_value

AMAP_WEB_KEY = os.getenv("AMAP_WEB_KEY", os.getenv("AMAP_KEY", ""))
AMAP_BASE = "https://restapi.amap.com/v3"

# 大类→子类映射（匹配高德API返回的中文type字段，分号分隔：大类;中类;小类）
TYPE_CLASSIFIERS = [
    # === 餐饮服务 ===
    ("餐饮服务;中餐厅", "chinese_restaurants"),
    ("餐饮服务;清真菜馆", "chinese_restaurants"),
    ("餐饮服务;综合酒楼", "chinese_restaurants"),
    ("餐饮服务;外国餐厅", "foreign_restaurants"),
    ("餐饮服务;快餐厅", "fast_food"),
    ("餐饮服务;小吃店", "fast_food"),
    ("餐饮服务;冷饮店", "cafe_tea"),
    ("餐饮服务;甜品店", "cafe_tea"),
    ("餐饮服务;糕饼店", "cafe_tea"),
    ("餐饮服务;咖啡厅", "cafe_tea"),
    ("餐饮服务;茶艺馆", "cafe_tea"),
    ("餐饮服务;酒吧", "bars"),
    ("餐饮服务", "restaurants"),  # 餐饮兜底
    # === 购物服务 ===
    ("购物服务;购物中心", "shopping"),
    ("购物服务;百货商场", "shopping"),
    ("购物服务;便利店", "convenience"),
    ("购物服务;超市", "convenience"),
    ("购物服务;服装鞋帽店", "shopping"),
    ("购物服务;数码电子", "shopping"),
    ("购物服务;药店", "hospitals"),  # 药店归入医疗
    ("购物服务", "shopping"),
    # === 生活服务 ===
    ("生活服务;售票处", "convenience"),
    ("生活服务;旅行社", "convenience"),
    ("生活服务;美容美发", "convenience"),
    ("生活服务;洗衣店", "convenience"),
    ("生活服务;宠物服务", "convenience"),
    ("生活服务", "convenience"),
    # === 商务住宅 ===
    ("商务住宅;住宅区", "residential"),
    ("商务住宅;商务写字楼", "office"),
    ("商务住宅;商住两用", "office"),
    ("商务住宅", "residential"),
    # === 医疗保健服务 ===
    ("医疗保健服务;综合医院", "hospitals"),
    ("医疗保健服务;专科医院", "hospitals"),
    ("医疗保健服务;诊所", "pharmacy"),
    ("医疗保健服务;医药保健销售店", "pharmacy"),
    ("医疗保健服务;药房", "pharmacy"),
    ("医疗保健服务;动物医疗", "pharmacy"),
    ("医疗保健服务", "pharmacy"),
    # === 住宿服务 ===
    ("住宿服务", "hotels"),
    # === 交通设施服务 ===
    ("交通设施服务;地铁站", "subway"),
    ("交通设施服务;公交站", "bus"),
    ("交通设施服务;停车场", "parking"),
    ("交通设施服务;长途客运站", "bus"),
    ("交通设施服务", "bus"),
    # === 科教文化服务 ===
    ("科教文化服务;学校", "schools"),
    ("科教文化服务;培训机构", "schools"),
    ("科教文化服务", "schools"),
    # === 金融保险服务 ===
    ("金融保险服务", "banks"),
    # === 体育休闲服务 ===
    ("体育休闲服务;运动场馆", "bars"),
    ("体育休闲服务;KTV", "bars"),
    ("体育休闲服务;酒吧", "bars"),
    ("体育休闲服务;网吧", "bars"),
    ("体育休闲服务", "bars"),
    # === 风景名胜 ===
    ("风景名胜;公园", "residential"),
    ("风景名胜;风景名胜", "residential"),
    ("风景名胜", "residential"),
    # === 政府机构 ===
    ("政府机构及社会团体", "office"),
    # === 公司企业 ===
    ("公司企业", "office"),
    # === 数字代码兜底（兼容旧版API） ===
    ("050100", "chinese_restaurants"),
    ("050200", "foreign_restaurants"),
    ("050300", "fast_food"),
    ("050400", "bars"),
    ("050500", "cafe_tea"),
    ("050600", "cafe_tea"),
    ("050000", "restaurants"),
    ("060100", "shopping"),
    ("060400", "shopping"),
    ("060200", "convenience"),
    ("060300", "convenience"),
    ("060000", "shopping"),
    ("070000", "convenience"),
    ("080000", "bars"),
    ("090100", "hospitals"),
    ("090200", "hospitals"),
    ("090300", "hospitals"),
    ("090400", "hospitals"),
    ("090500", "hospitals"),
    ("090000", "hospitals"),
    ("100000", "hotels"),
    ("110000", "residential"),
    ("120300", "residential"),
    ("120200", "office"),
    ("120000", "residential"),
    ("130000", "office"),
    ("141200", "schools"),
    ("140000", "schools"),
    ("150500", "subway"),
    ("150200", "bus"),
    ("150900", "parking"),
    ("150000", "bus"),
    ("160100", "banks"),
    ("160000", "banks"),
    ("170000", "office"),
]

# 用于前端/后端统一key名
ALL_CATEGORY_KEYS = [
    "restaurants", "chinese_restaurants", "foreign_restaurants",
    "fast_food", "cafe_tea", "bars",
    "shopping", "convenience",
    "residential", "office", "schools", "hotels",
    "subway", "bus", "parking", "hospitals", "pharmacy", "banks",
]

# 餐饮子类合集（用于计算正确的"所有餐饮"总数）
RESTAURANT_SUB_KEYS = ["chinese_restaurants", "foreign_restaurants", "fast_food", "cafe_tea", "bars", "restaurants"]

CATEGORY_LABELS = {
    "restaurants": "餐饮门店",
    "chinese_restaurants": "中餐厅",
    "foreign_restaurants": "外国餐厅",
    "fast_food": "快餐厅",
    "cafe_tea": "咖啡茶饮",
    "bars": "酒吧",
    "shopping": "购物商场",
    "convenience": "便利店超市",
    "residential": "住宅小区",
    "office": "写字楼",
    "schools": "学校",
    "hotels": "酒店住宿",
    "subway": "地铁站",
    "bus": "公交站",
    "parking": "停车场",
    "hospitals": "医院",
    "banks": "银行",
}

KNOWN_BRANDS = [
    "肯德基", "麦当劳", "汉堡王", "必胜客", "海底捞", "西贝", "外婆家",
    "呷哺呷哺", "太二", "喜茶", "奈雪", "瑞幸", "星巴克", "蜜雪冰城",
    "茶百道", "古茗", "霸王茶姬", "Manner", "Costa",
    "达美乐", "赛百味", "沙县小吃", "兰州拉面",
    "黄焖鸡", "杨国福", "张亮麻辣烫", "袁记云饺", "巴比馒头",
    "乡村基", "大米先生", "老娘舅", "和府捞面", "味千拉面",
    "711", "罗森", "全家", "便利蜂", "美宜佳", "红旗连锁",
    "沃尔玛", "永辉", "盒马", "大润发", "华润万家", "物美",
    "优衣库", "名创优品", "屈臣氏",
    "汉庭", "如家", "全季", "亚朵", "丽枫", "维也纳",
    "链家", "贝壳", "我爱我家", "中原地产",
    "魏家凉皮",
]


def classify_poi_type(type_code: str) -> str | None:
    """根据高德POI type字段分类到我们的类别（支持中文名和数字码）"""
    if not type_code:
        return None
    # 处理 | 分隔的多分类（如：餐饮|购物）
    parts = type_code.split("|") if "|" in type_code else [type_code]
    for part in parts:
        part = part.strip()
        for prefix, category in TYPE_CLASSIFIERS:
            if part.startswith(prefix):
                return category
    return None


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
    competitors_200m: int = 0
    competitors_500m: int = 0
    competitors_1000m: int = 0
    competitor_list: list = field(default_factory=list)
    # 双轨制：原始计数（脱水前）
    raw_poi_counts: dict = field(default_factory=dict)
    raw_stats_200m: dict = field(default_factory=dict)
    raw_stats_500m: dict = field(default_factory=dict)
    raw_stats_1000m: dict = field(default_factory=dict)


class AmapService:
    def __init__(self, api_key: str = ""):
        self.key = api_key or get_config_value("amap_key", "") or AMAP_WEB_KEY
        if not self.key:
            raise ValueError("高德 Web API Key 未配置，请在后台核心配置或 .env 中设置")

    async def _request(self, path: str, params: dict) -> dict:
        params["key"] = self.key
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(f"{AMAP_BASE}{path}", params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != "1":
                raise Exception(f"高德API错误: {data.get('info', 'unknown')}")
            return data

    async def reverse_geocode(self, lng: float, lat: float) -> dict:
        data = await self._request("/geocode/regeo", {
            "location": f"{lng},{lat}",
            "extensions": "all",
            "radius": 1000,
        })
        regeo = data.get("regeocode", {})
        addr = regeo.get("addressComponent", {})
        roads = []
        for r in (regeo.get("roadinters") or [])[:5]:
            road_name = r.get("name") or r.get("first_name") or r.get("second_name") or ""
            if road_name:
                roads.append(road_name)
        return {
            "formatted_address": regeo.get("formatted_address", ""),
            "city": addr.get("city", "") or addr.get("province", ""),
            "district": addr.get("district", ""),
            "township": addr.get("township", ""),
            "neighborhood": addr.get("neighborhood", {}).get("name", ""),
            "building_type": addr.get("building", {}).get("type", ""),
            "business_areas": [b.get("name", "") for b in (regeo.get("businessAreas") or [])],
            "nearby_roads": roads,
        }

    async def _fetch_all_pois(self, lng: float, lat: float, types: str = "",
                                radius: int = 1000, max_results: int = 300) -> list[dict]:
        """分页获取周边全部POI，返回POI dict列表"""
        all_pois = []
        seen = set()
        for page in range(1, 20):
            params = {
                "location": f"{lng},{lat}",
                "radius": radius,
                "offset": 25,
                "page": page,
                "extensions": "all",
            }
            if types:
                params["types"] = types
            data = await self._request("/place/around", params)
            pois = data.get("pois", [])
            if not pois:
                break
            for p in pois:
                try:
                    dist = int(p.get("distance", 0) or 0)
                except (ValueError, TypeError):
                    dist = 0
                if dist < 10:
                    continue
                name = p.get("name", "")
                key = f"{name}|{dist}"
                if key in seen:
                    continue
                seen.add(key)
                loc_str = p.get("location", "0,0") or "0,0"
                parts = loc_str.split(",")
                try:
                    lng_val = float(parts[0]) if len(parts) > 0 else 0.0
                except (ValueError, TypeError):
                    lng_val = 0.0
                try:
                    lat_val = float(parts[1]) if len(parts) > 1 else 0.0
                except (ValueError, TypeError):
                    lat_val = 0.0
                all_pois.append({
                    "name": name,
                    "type": p.get("type", ""),
                    "distance": dist,
                    "address": p.get("address", ""),
                    "lng": lng_val,
                    "lat": lat_val,
                })
            if len(all_pois) >= max_results:
                break
        return all_pois

    async def _fetch_by_keyword(self, lng: float, lat: float, keyword: str,
                                   radius: int = 1000, max_results: int = 100) -> list[dict]:
        """分页获取周边关键词POI"""
        all_pois = []
        seen = set()
        for page in range(1, 10):
            data = await self._request("/place/around", {
                "location": f"{lng},{lat}",
                "keywords": keyword,
                "radius": radius,
                "offset": 25,
                "page": page,
                "extensions": "all",
            })
            pois = data.get("pois", [])
            if not pois:
                break
            for p in pois:
                try:
                    dist = int(p.get("distance", 0) or 0)
                except (ValueError, TypeError):
                    dist = 0
                if dist < 10:
                    continue
                name = p.get("name", "")
                key = f"{name}|{dist}"
                if key in seen:
                    continue
                seen.add(key)
                loc_str = p.get("location", "0,0") or "0,0"
                parts = loc_str.split(",")
                try:
                    lng_val = float(parts[0]) if len(parts) > 0 else 0.0
                except (ValueError, TypeError):
                    lng_val = 0.0
                try:
                    lat_val = float(parts[1]) if len(parts) > 1 else 0.0
                except (ValueError, TypeError):
                    lat_val = 0.0
                all_pois.append({
                    "name": name,
                    "type": p.get("type", ""),
                    "distance": dist,
                    "address": p.get("address", ""),
                    "lng": lng_val,
                    "lat": lat_val,
                })
            if len(all_pois) >= max_results:
                break
        return all_pois

    async def collect_all(self, lng: float, lat: float,
                          competitor_type: str = "") -> LocationData:
        ld = LocationData()

        # 1. 逆地理编码
        geo = await self.reverse_geocode(lng, lat)
        ld.address = geo["formatted_address"]
        ld.city = geo["city"]
        ld.district = geo["district"]
        ld.township = geo["township"]
        ld.nearby_roads = geo.get("nearby_roads", [])
        ld.business_areas = geo.get("business_areas", [])
        ld.building_type = geo.get("building_type", "")

        # 2. 大范围POI搜索（1000m翻页拉满，确保 200m ≤ 500m ≤ 1000m）
        all_pois = await self._fetch_all_pois(lng, lat, radius=1000, max_results=600)

        # 对容易被挤出的大类别做专项补充
        essential_types = {
            "090000": "医疗保健",
            "100000": "住宿",
            "141200": "学校",
            "150500": "地铁",
            "150900": "停车场",
            "160100": "银行",
        }
        for type_code in essential_types:
            try:
                extra = await self._fetch_all_pois(lng, lat, types=type_code, radius=1000, max_results=60)
                all_pois.extend(extra)
            except Exception:
                pass

        # 公交站用关键词搜索（类型码搜索不到）
        try:
            bus_pois = await self._fetch_by_keyword(lng, lat, "公交站", radius=1000, max_results=100)
            all_pois.extend(bus_pois)
        except Exception:
            pass

        # 合并后去重
        seen = set()
        deduped = []
        for p in all_pois:
            key = f"{p['name']}|{p['distance']}"
            if key not in seen:
                seen.add(key)
                deduped.append(p)
        all_pois = deduped

        # 初始化计数器（valid = 脱水后，raw = 脱水前）
        poi_counts = {k: 0 for k in ALL_CATEGORY_KEYS}
        poi_lists = {k: [] for k in ALL_CATEGORY_KEYS}
        stats_200m = {k: 0 for k in ALL_CATEGORY_KEYS}
        stats_500m = {k: 0 for k in ALL_CATEGORY_KEYS}
        stats_1000m = {k: 0 for k in ALL_CATEGORY_KEYS}
        raw_poi_counts = {k: 0 for k in ALL_CATEGORY_KEYS}
        raw_stats_200m = {k: 0 for k in ALL_CATEGORY_KEYS}
        raw_stats_500m = {k: 0 for k in ALL_CATEGORY_KEYS}
        raw_stats_1000m = {k: 0 for k in ALL_CATEGORY_KEYS}
        brands = {}
        competitors_200m = 0
        competitors_500m = 0
        competitors_1000m = 0
        competitor_list = []

        for p in all_pois:
            dist = p["distance"]
            cat = classify_poi_type(p["type"])

            if cat:
                # === 原始计数（脱水前，先计入） ===
                raw_poi_counts[cat] += 1
                if dist <= 200: raw_stats_200m[cat] += 1
                if dist <= 500: raw_stats_500m[cat] += 1
                raw_stats_1000m[cat] += 1

                # === 四类数据脱水：写字楼/商场/住宅/酒店 ===
                if cat == "office" and not is_real_office(p["name"]):
                    continue  # 厂房/工业园/公司 → 丢弃
                elif cat == "shopping" and not is_real_shopping(p["name"]):
                    continue  # 建材/汽配/批发 → 丢弃
                elif cat == "residential" and not is_real_residential(p["name"]):
                    continue  # 售楼处/中介 → 丢弃
                elif cat == "hotels" and not is_real_hotel(p["name"]):
                    continue  # 招待所/洗浴/农家乐 → 丢弃
                # 医院/学校名称脱水
                elif cat == "hospitals" and not is_real_hospital(p["name"]):
                    cat = "pharmacy"  # 诊所/牙科/药店 → 降级到 pharmacy
                elif cat == "schools" and not is_real_school(p["name"]):
                    continue  # 培训/托管/驾校 → 丢弃

                poi_counts[cat] += 1
                if dist <= 200:
                    stats_200m[cat] += 1
                if dist <= 500:
                    stats_500m[cat] += 1
                stats_1000m[cat] += 1

                if len(poi_lists[cat]) < 15:
                    poi_lists[cat].append({
                        "name": p["name"],
                        "distance": dist,
                        "address": p["address"],
                    })

            # 品牌识别
            name = p["name"]
            for brand in KNOWN_BRANDS:
                if brand in name:
                    if brand not in brands:
                        brands[brand] = {"name": brand, "count": 0, "distances": []}
                    brands[brand]["count"] += 1
                    brands[brand]["distances"].append(dist)
                    break

            # 竞品判定——从已分类POI中精确筛选（同业态才算竞品）
            if competitor_type and cat:
                is_competitor = False

                # ---- 小餐饮/快餐/小吃：仅匹配快餐+茶饮+关键词命中 ----
                if competitor_type in ("050000", "050300"):
                    # 直接类型匹配：快餐厅、咖啡茶饮就是竞品
                    if cat in ("fast_food", "cafe_tea"):
                        is_competitor = True
                    # 关键词二次筛选：中餐厅、餐饮场所中命中快餐关键词的才算竞品
                    elif cat in ("chinese_restaurants", "restaurants", "foreign_restaurants", "bars"):
                        if is_snack_competitor(name):
                            is_competitor = True

                # ---- 大餐饮/中餐/火锅/烧烤：匹配中餐厅（同业态直接算竞品） ----
                elif competitor_type == "050100":
                    is_competitor = cat == "chinese_restaurants"

                # ---- 茶饮咖啡：仅匹配茶饮 ----
                elif competitor_type == "050500":
                    is_competitor = cat == "cafe_tea"

                # ---- 甜品烘焙 ----
                elif competitor_type == "050600":
                    is_competitor = cat == "cafe_tea"

                # ---- 酒吧 ----
                elif competitor_type == "050400":
                    is_competitor = cat == "bars"

                # ---- 酒店住宿 ----
                elif competitor_type == "100000":
                    is_competitor = cat == "hotels"

                # ---- 零售/便利店/超市 ----
                elif competitor_type in ("060200", "060300"):
                    is_competitor = cat in ("convenience", "shopping")
                elif competitor_type in ("060100", "060400"):
                    is_competitor = cat == "shopping"
                elif competitor_type.startswith("06"):
                    is_competitor = cat in ("shopping", "convenience")

                # ---- 药店 ----
                elif competitor_type == "090400":
                    is_competitor = cat == "pharmacy"

                # ---- 生活服务 ----
                elif competitor_type == "070000":
                    is_competitor = cat == "convenience"

                # ---- 休闲娱乐 ----
                elif competitor_type == "080000":
                    is_competitor = cat == "bars"

                # ---- 教育培训 ----
                elif competitor_type == "141200":
                    is_competitor = cat == "schools"

                if is_competitor:
                    if dist <= 200:
                        competitors_200m += 1
                    if dist <= 500:
                        competitors_500m += 1
                    competitors_1000m += 1
                    if len(competitor_list) < 30:
                        competitor_list.append({
                            "name": name,
                            "distance": dist,
                        })

        # 地铁出口去重：同一站多个出口合并为1个站
        subway_stations = {}  # key=站名基, value={min_dist, count}
        for p in all_pois:
            cat = classify_poi_type(p["type"])
            if cat == "subway":
                # 提取站名：去除出口后缀（如"B2东北口"、"C西南口"）
                base_name = re.sub(r'[A-Z]\d*(东北|东南|西北|西南|[东西南北])?口?$', '', p["name"])
                base_name = re.sub(r'[（(][^)）]*[)）]$', '', base_name)
                base_name = base_name.strip()
                if base_name not in subway_stations:
                    subway_stations[base_name] = {"min_dist": p["distance"], "count": 0}
                subway_stations[base_name]["count"] += 1
                subway_stations[base_name]["min_dist"] = min(subway_stations[base_name]["min_dist"], p["distance"])

        # 用地铁站数（去重后）替换出口数
        real_subway_count = len(subway_stations)
        # 重新计算各半径的地铁站数
        real_subway_200 = 0
        real_subway_500 = 0
        real_subway_1000 = 0
        for base_name, info in subway_stations.items():
            if info["min_dist"] <= 200:
                real_subway_200 += 1
            if info["min_dist"] <= 500:
                real_subway_500 += 1
            real_subway_1000 += 1

        poi_counts["subway"] = real_subway_count
        stats_200m["subway"] = real_subway_200
        stats_500m["subway"] = real_subway_500
        stats_1000m["subway"] = real_subway_1000

        # 修正餐饮总数：父类(restaurants) = 所有餐饮子类之和，解决子类>父类的逻辑矛盾
        total_rest = sum(poi_counts.get(k, 0) for k in RESTAURANT_SUB_KEYS)
        poi_counts["restaurants"] = total_rest
        stats_200m["restaurants"] = sum(stats_200m.get(k, 0) for k in RESTAURANT_SUB_KEYS)
        stats_500m["restaurants"] = sum(stats_500m.get(k, 0) for k in RESTAURANT_SUB_KEYS)
        stats_1000m["restaurants"] = sum(stats_1000m.get(k, 0) for k in RESTAURANT_SUB_KEYS)

        ld.poi_counts = poi_counts
        ld.poi_lists = poi_lists
        ld.stats_200m = stats_200m
        ld.stats_500m = stats_500m
        ld.stats_1000m = stats_1000m
        ld.raw_poi_counts = raw_poi_counts
        ld.raw_stats_200m = raw_stats_200m
        ld.raw_stats_500m = raw_stats_500m
        ld.raw_stats_1000m = raw_stats_1000m
        # 强制交集校验：竞品必须是餐饮门店的严格子集（杜绝子类>父类）
        ld.competitors_200m = min(competitors_200m, stats_200m.get("restaurants", competitors_200m))
        ld.competitors_500m = min(competitors_500m, stats_500m.get("restaurants", competitors_500m))
        ld.competitors_1000m = min(competitors_1000m, stats_1000m.get("restaurants", competitors_1000m))
        ld.competitor_list = competitor_list

        # 品牌排序
        brand_list = sorted(brands.values(), key=lambda x: -x["count"])
        ld.hot_brands = [{
            "name": b["name"],
            "count": b["count"],
            "min_distance": min(b["distances"]) if b["distances"] else 0,
        } for b in brand_list[:15]]

        return ld


async def collect_location_data(lng: float, lat: float,
                                 business_type: str = "") -> LocationData:
    service = AmapService()
    return await service.collect_all(lng, lat, business_type)
