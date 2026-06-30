"""高德地图 Web API 服务 - 获取选址所需的真实 POI 数据。
使用单次大范围搜索 + 手动分类，确保数据准确性。
职责：HTTP 请求、Key 池管理、POI 采集流程、逆地理编码。
"""
import os
import re
import httpx

from services.runtime_config import get_config_value
from prompts.industry_config import get_rigor_for_config_key
from services.amap_models import LocationData, _city_has_subway
from services.amap_poi_rules import (
    classify_poi_type, classify_poi_rigor,
    is_real_hospital, is_real_school, is_real_convenience, is_real_pharmacy,
    is_real_training, is_real_laundry, is_real_clinic,
    is_real_fitness, is_real_fresh_retail, is_real_tobacco_liquor_retail,
    is_real_shopping, is_real_hotel, is_real_immersive_entertainment,
    is_real_office, is_real_low_freq_retail, is_real_residential,
    is_market_anchor, is_snack_competitor,
    _hospital_base, _is_hospital_main_name, _normalize_bus_stop_name,
    ALL_CATEGORY_KEYS, RESTAURANT_SUB_KEYS, KNOWN_BRANDS,
)

AMAP_WEB_KEY = os.getenv("AMAP_WEB_KEY", os.getenv("AMAP_KEY", ""))
AMAP_BASE = "https://restapi.amap.com/v3"


class AmapService:
    def __init__(self, api_key: str = ""):
        self.key = api_key or get_config_value("amap_key", "") or AMAP_WEB_KEY

    @staticmethod
    def _get_keys_from_pool():
        """从 DB Key 池取所有启用的 Key，按优先级排序"""
        try:
            from database import SessionLocal
            from routers.admin import _get_amap_key_selector as _selector
            db = SessionLocal()
            try:
                from models.db_models import AmapKey as _AK
                rows = db.query(_AK).filter(_AK.enabled == 1).order_by(_AK.priority, _AK.id).all()
                if rows:
                    return [(r.api_key, r.security_secret or "") for r in rows]
            finally:
                db.close()
        except Exception:
            pass
        return []

    @staticmethod
    def _report_key_failure(key_str: str, status: str, info: str = ""):
        """标记 Key 失败"""
        if not key_str:
            return
        try:
            from database import SessionLocal
            from models.db_models import AmapKey as _AK
            from datetime import datetime as _dt
            db = SessionLocal()
            try:
                row = db.query(_AK).filter(_AK.api_key == key_str, _AK.enabled == 1).first()
                if row:
                    row.last_status = status
                    row.last_info = (info or "")[:200]
                    row.last_checked_at = _dt.utcnow()
                    row.fail_count = (row.fail_count or 0) + 1
                    db.commit()
            finally:
                db.close()
        except Exception:
            pass

    async def _request(self, path: str, params: dict) -> dict:
        # ★ Key 池重试：DB 池 → env fallback
        pool_keys = self._get_keys_from_pool()
        all_keys = [(k, s) for k, s in pool_keys] if pool_keys else []
        # env fallback
        env_key = AMAP_WEB_KEY
        if env_key and not any(k == env_key for k, _ in all_keys):
            all_keys.append((env_key, ""))
        if self.key and not any(k == self.key for k, _ in all_keys):
            all_keys.append((self.key, ""))

        if not all_keys:
            raise Exception("AMAP_KEY_UNAVAILABLE: 无可用高德 Key")

        last_err = "unknown"
        for key, sec in all_keys:
            try:
                p = {**params, "key": key}
                async with httpx.AsyncClient(timeout=15) as client:
                    resp = await client.get(f"{AMAP_BASE}{path}", params=p)
                    resp.raise_for_status()
                    data = resp.json()
                    if data.get("status") == "1":
                        return data
                    info = str(data.get("info", "") or "")
                    ic = str(data.get("infocode", "") or "")
                    _iu = info.upper()
                    # 分类：可重试（额度/QPS用完）vs 不可重试（Key类型/签名错误）
                    is_retryable = (
                        "OVER_DAILY" in _iu or ic in ("10003", "10004") or
                        "CUQPS" in _iu or ic == "10007"
                    )
                    err_type = info[:80]
                    self._report_key_failure(key, err_type, info)
                    if is_retryable:
                        print(f"[AMAP] Key {key[:6]}*** {err_type} → 切换下一个 Key", flush=True)
                        last_err = f"高德API错误(已重试): {info[:120]}"
                        continue
                    else:
                        last_err = f"高德API错误: {info[:120]}"
                        break  # 不可重试（如 INVALID_KEY），停止尝试
            except Exception as e:
                err_str = str(e)[:120]
                self._report_key_failure(key, "NETWORK_ERROR", err_str)
                print(f"[AMAP] Key {key[:6]}*** NETWORK_ERROR → 切换下一个 Key", flush=True)
                last_err = f"高德API网络错误(已重试): {err_str}"
                continue

        raise Exception(last_err)

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
                                radius: int = 1000, max_results: int = 300,
                                keep_missing_distance: bool = False,
                                missing_distance_default: int = 999) -> list[dict]:
        """分页获取周边全部POI。keep_missing_distance 用于公交等专项，保留 distance 缺失的 POI。"""
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
                raw = p.get("distance")
                dist = None
                dist_missing = False
                if raw is None or raw == "" or (isinstance(raw, str) and not raw.strip().isdigit()):
                    dist_missing = True
                    dist = 0
                else:
                    try:
                        dist = int(raw)
                    except (ValueError, TypeError):
                        dist_missing = True
                        dist = 0
                if dist_missing and keep_missing_distance:
                    dist = missing_distance_default
                    p["distance"] = missing_distance_default
                elif dist < 10:
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
                                   radius: int = 1000, max_results: int = 100,
                                   keep_missing_distance: bool = False,
                                   missing_distance_default: int = 999) -> list[dict]:
        """分页获取周边关键词POI。keep_missing_distance 保留 distance 缺失的 POI。"""
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
                raw = p.get("distance")
                dist = None
                dist_missing = False
                if raw is None or raw == "" or (isinstance(raw, str) and not raw.strip().isdigit()):
                    dist_missing = True
                    dist = 0
                else:
                    try:
                        dist = int(raw)
                    except (ValueError, TypeError):
                        dist_missing = True
                        dist = 0
                if dist_missing and keep_missing_distance:
                    dist = missing_distance_default
                    p["distance"] = missing_distance_default
                elif dist < 10:
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
                          amap_type: str = "",
                          config_key: str = "",
                          business_type: str = "",
                          brand_name: str = "") -> LocationData:
        ld = LocationData()
        rigor = get_rigor_for_config_key(config_key) if config_key else {}

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

        # 公交站：类型码 + 多关键词搜索 + 去重
        bus_seen = {}  # normalized_name → best_entry
        _bus_dist_missing = 0
        _bus_type_count = 0
        _bus_kw_count = 0
        try:
            bus_type_pois = await self._fetch_all_pois(lng, lat, types="150200", radius=1000, max_results=100,
                                                       keep_missing_distance=True, missing_distance_default=999)
            _bus_type_count = len(bus_type_pois)
            for p in bus_type_pois:
                nname = _normalize_bus_stop_name(p.get("name", ""))
                key = nname or f"{p.get('name','')}|{p.get('distance','?')}"
                dist = p.get("distance", 0)
                if dist == 999:
                    _bus_dist_missing += 1
                if key not in bus_seen or dist < bus_seen[key].get("distance", 999):
                    bus_seen[key] = {**p, "distance": dist}
        except Exception:
            pass
        bus_keywords = ["公交站", "公交车站", "公交站牌", "公交枢纽", "公交首末站"]
        for kw in bus_keywords:
            try:
                kw_pois = await self._fetch_by_keyword(lng, lat, kw, radius=1000, max_results=80,
                                                        keep_missing_distance=True, missing_distance_default=999)
                _bus_kw_count += len(kw_pois)
                for p in kw_pois:
                    nname = _normalize_bus_stop_name(p.get("name", ""))
                    key = nname or f"{p.get('name','')}|{p.get('distance','?')}"
                    dist = p.get("distance", 0)
                    if dist == 999:
                        _bus_dist_missing += 1
                    if key not in bus_seen or dist < bus_seen[key].get("distance", 999):
                        bus_seen[key] = {**p, "distance": dist}
            except Exception:
                pass
        all_pois.extend(bus_seen.values())

        # P1: 购物商场 + 市场/专业市场关键词补采
        shopping_kw_seen = {}
        shopping_keywords = [
            "购物中心", "百货商场", "商业广场", "购物广场", "万象城", "龙湖天街",
            "大悦城", "印象城", "宝龙广场", "吾悦广场", "万达广场", "奥特莱斯",
        ]
        for kw in shopping_keywords:
            try:
                for p in await self._fetch_by_keyword(lng, lat, kw, radius=1000, max_results=60):
                    name = p.get("name", "")
                    key = f"{name}|{p.get('distance', 0)}"
                    if key not in shopping_kw_seen:
                        shopping_kw_seen[key] = p
            except Exception:
                pass
        all_pois.extend(shopping_kw_seen.values())

        # P1: 写字楼关键词补采（"写字楼"类型码可能漏采）
        office_kw_seen = {}
        office_keywords = ["写字楼", "办公楼", "商务楼", "商务中心", "企业中心", "产业园", "科技园"]
        for kw in office_keywords:
            try:
                for p in await self._fetch_by_keyword(lng, lat, kw, radius=1000, max_results=60):
                    name = p.get("name", "")
                    key = f"{name}|{p.get('distance', 0)}"
                    if key not in office_kw_seen:
                        office_kw_seen[key] = p
            except Exception:
                pass
        all_pois.extend(office_kw_seen.values())

        market_kw_seen = {}
        market_keywords = [
            "农贸市场", "菜市场", "批发市场", "建材市场", "五金市场",
            "家居市场", "汽配城", "商贸城",
        ]
        for kw in market_keywords:
            try:
                for p in await self._fetch_by_keyword(lng, lat, kw, radius=1000, max_results=60):
                    name = p.get("name", "")
                    key = f"{name}|{p.get('distance', 0)}"
                    if key not in market_kw_seen:
                        market_kw_seen[key] = p
            except Exception:
                pass
        all_pois.extend(market_kw_seen.values())

        # 合并后去重
        seen = set()
        deduped = []
        for p in all_pois:
            name = p.get("name", "")  # ★ 每轮循环第一时间设置
            key = f"{name}|{p['distance']}"
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
        # 旧字段兼容
        competitors_200m = 0
        competitors_500m = 0
        competitors_1000m = 0
        competitor_list = []
        # ★ 严谨度框架新字段
        direct_comp_200m = 0; direct_comp_500m = 0; direct_comp_1000m = 0
        direct_comp_list = []
        direct_comp_list_200m = []; direct_comp_list_500m = []; direct_comp_list_1000m = []
        sub_200m = 0; sub_500m = 0; sub_1000m = 0
        sub_list = []
        sub_list_200m = []; sub_list_500m = []; sub_list_1000m = []
        anchor_200m = 0; anchor_500m = 0; anchor_1000m = 0
        anchor_list = []
        anchor_list_200m = []; anchor_list_500m = []; anchor_list_1000m = []
        irrelevant_count = 0
        dewater_excluded = 0  # ★ 被名称脱水规则剔除的POI
        valid_kept = 0  # ★ 每个POI只计1次，避免子类/父类重复
        _hospital_groups = {}  # ★ 医院归并去重: base -> {main_name, main_poi, dept_names, min_dist}
        quality_notes = []

        for p in all_pois:
            dist = p["distance"]
            cat = classify_poi_type(p["type"])
            name = p.get("name", "")  # ★ 每轮循环第一时间设置，杜绝沿用上一条数据

            if cat:
                # === 原始计数（脱水前，先计入） ===
                raw_poi_counts[cat] += 1
                if dist <= 200: raw_stats_200m[cat] += 1
                if dist <= 500: raw_stats_500m[cat] += 1
                raw_stats_1000m[cat] += 1

                # ★ 业务感知改写：shopping 大类下的生鲜/烟酒 → 独立 category
                if cat == "shopping" and business_type:
                    if any(kw in business_type for kw in ("生鲜","水果","蔬菜","菜店","鲜果")):
                        if is_real_fresh_retail(name):
                            cat = "fresh_retail"
                    elif any(kw in business_type for kw in ("烟酒","名烟","名酒","酒行","酒类")):
                        if is_real_tobacco_liquor_retail(name):
                            cat = "tobacco_liquor"
                    elif any(kw in business_type for kw in ("零售店","服装店","数码店")):
                        if is_real_low_freq_retail(name):
                            cat = "low_freq_retail"
                    elif any(kw in business_type for kw in ("日用百货","百货")) and is_real_convenience(name):
                        cat = "convenience"

                # === 市场/专业市场识别 — 在购物商场脱水前先分离 ===
                if cat == "shopping" and is_market_anchor(name):
                    cat = "market_anchor"

                # === 四类数据脱水：写字楼/商场/住宅/酒店 ===
                if cat == "office" and not is_real_office(name):
                    dewater_excluded += 1; continue
                if cat == "shopping" and not is_real_shopping(name):
                    dewater_excluded += 1; continue
                if cat == "residential" and not is_real_residential(name):
                    dewater_excluded += 1; continue
                if cat == "hotels" and not is_real_hotel(name):
                    dewater_excluded += 1; continue
                # 医院：非真医院 → 降级为 pharmacy；真医院 → 全部收集到 _hospital_groups，循环结束后统一写入
                if cat == "hospitals" and not is_real_hospital(name):
                    cat = "pharmacy"
                if cat == "hospitals":
                    base = _hospital_base(name)
                    group = _hospital_groups.get(base)
                    if group is None:
                        group = {"main_name": "", "main_poi": None, "dept_names": [], "min_dist": dist}
                        _hospital_groups[base] = group
                    if dist < group["min_dist"]:
                        group["min_dist"] = dist
                    if _is_hospital_main_name(name):
                        if not group["main_name"] or len(name) < len(group["main_name"]):
                            group["main_name"] = name
                            group["main_poi"] = p
                    else:
                        short = name.replace(base, "").strip()
                        if short and short not in group["dept_names"]:
                            group["dept_names"].append(short)
                    continue  # ★ 医院POI暂不进入普通计数，循环结束后统一写入
                if cat == "schools" and not is_real_school(name):
                    dewater_excluded += 1; continue
                if cat == "convenience" and not is_real_convenience(name):
                    dewater_excluded += 1; continue
                if cat == "pharmacy" and not is_real_pharmacy(name):
                    dewater_excluded += 1; continue
                if cat == "education_training" and not is_real_training(name):
                    dewater_excluded += 1; continue
                if cat == "laundry" and not is_real_laundry(name):
                    dewater_excluded += 1; continue
                if cat == "clinics" and not is_real_clinic(name):
                    dewater_excluded += 1; continue
                if cat == "fitness" and not is_real_fitness(name):
                    dewater_excluded += 1; continue
                if cat == "fresh_retail" and not is_real_fresh_retail(name):
                    dewater_excluded += 1; continue
                if cat == "tobacco_liquor" and not is_real_tobacco_liquor_retail(name):
                    dewater_excluded += 1; continue
                if cat == "immersive_entertainment" and not is_real_immersive_entertainment(name):
                    dewater_excluded += 1; continue
                if cat == "low_freq_retail" and not is_real_low_freq_retail(name):
                    dewater_excluded += 1; continue

                poi_counts[cat] += 1
                valid_kept += 1  # ★ 每个通过脱水的POI只计1次
                if dist <= 200:
                    stats_200m[cat] += 1
                if dist <= 500:
                    stats_500m[cat] += 1
                stats_1000m[cat] += 1

                if len(poi_lists[cat]) < 15:
                    poi_lists[cat].append({
                        "name": name,
                        "distance": dist,
                        "address": p["address"],
                    })

                # ★ 严谨度框架：四级POI分类
                rigor_label = classify_poi_rigor(name, cat, p["type"], rigor, business_type, brand_name) if rigor else "pass"
                if rigor_label == "irrelevant":
                    irrelevant_count += 1
                elif rigor_label == "direct":
                    direct_comp_list.append({"name": name, "distance": dist})
                    if dist <= 200:
                        direct_comp_200m += 1
                        if len(direct_comp_list_200m) < 15:
                            direct_comp_list_200m.append({"name": name, "distance": dist})
                    if dist <= 500:
                        direct_comp_500m += 1
                        if len(direct_comp_list_500m) < 15:
                            direct_comp_list_500m.append({"name": name, "distance": dist})
                    direct_comp_1000m += 1
                    if len(direct_comp_list_1000m) < 15:
                        direct_comp_list_1000m.append({"name": name, "distance": dist})
                elif rigor_label == "substitute":
                    sub_list.append({"name": name, "distance": dist})
                    if dist <= 200:
                        sub_200m += 1
                        if len(sub_list_200m) < 10:
                            sub_list_200m.append({"name": name, "distance": dist})
                    if dist <= 500:
                        sub_500m += 1
                        if len(sub_list_500m) < 10:
                            sub_list_500m.append({"name": name, "distance": dist})
                    sub_1000m += 1
                    if len(sub_list_1000m) < 10:
                        sub_list_1000m.append({"name": name, "distance": dist})
                elif rigor_label == "anchor":
                    anchor_list.append({"name": name, "distance": dist})
                    if dist <= 200:
                        anchor_200m += 1
                        if len(anchor_list_200m) < 10:
                            anchor_list_200m.append({"name": name, "distance": dist})
                    if dist <= 500:
                        anchor_500m += 1
                        if len(anchor_list_500m) < 10:
                            anchor_list_500m.append({"name": name, "distance": dist})
                    anchor_1000m += 1
                    if len(anchor_list_1000m) < 10:
                        anchor_list_1000m.append({"name": name, "distance": dist})

            # 品牌识别
            for brand in KNOWN_BRANDS:
                if brand in name:
                    if brand not in brands:
                        brands[brand] = {"name": brand, "count": 0, "distances": []}
                    brands[brand]["count"] += 1
                    brands[brand]["distances"].append(dist)
                    break

            # 竞品判定——从已分类POI中精确筛选（同业态才算竞品）
            if amap_type and cat:
                is_competitor = False

                # ---- 小餐饮/快餐/小吃：仅匹配快餐+茶饮+关键词命中 ----
                if amap_type in ("050000", "050300"):
                    # 直接类型匹配：快餐厅、咖啡茶饮就是竞品
                    if cat in ("fast_food", "cafe_tea"):
                        is_competitor = True
                    # 关键词二次筛选：中餐厅、餐饮场所中命中快餐关键词的才算竞品
                    elif cat in ("chinese_restaurants", "restaurants", "foreign_restaurants", "bars"):
                        if is_snack_competitor(name):
                            is_competitor = True

                # ---- 大餐饮/中餐/火锅/烧烤：匹配中餐厅（同业态直接算竞品） ----
                elif amap_type == "050100":
                    is_competitor = cat == "chinese_restaurants"

                # ---- 茶饮咖啡：仅匹配茶饮 ----
                elif amap_type == "050500":
                    is_competitor = cat == "cafe_tea"

                # ---- 甜品烘焙 ----
                elif amap_type == "050600":
                    is_competitor = cat == "cafe_tea"

                # ---- 酒吧 ----
                elif amap_type == "050400":
                    is_competitor = cat == "bars"

                # ---- 酒店住宿 ----
                elif amap_type == "100000":
                    is_competitor = cat == "hotels"

                # ---- 零售/便利店/超市 ----
                elif amap_type in ("060200", "060300"):
                    is_competitor = cat in ("convenience", "shopping")
                elif amap_type in ("060100", "060400"):
                    is_competitor = cat == "shopping"
                elif amap_type.startswith("06"):
                    is_competitor = cat in ("shopping", "convenience")

                # ---- 药店 ----
                elif amap_type == "090400":
                    is_competitor = cat == "pharmacy"

                # ---- 生活服务 ----
                elif amap_type == "070000":
                    is_competitor = cat == "convenience"

                # ---- 休闲娱乐 ----
                elif amap_type == "080000":
                    is_competitor = cat == "bars"

                # ---- 教育培训 ----
                elif amap_type == "141200":
                    is_competitor = cat == "education_training"

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
            name = p.get("name", "")  # ★ 每轮循环第一时间设置
            cat = classify_poi_type(p["type"])
            if cat == "subway":
                # 提取站名：去除出口后缀（如"B2东北口"、"C西南口"）
                base_name = re.sub(r'[A-Z]\d*(东北|东南|西北|西南|[东西南北])?口?$', '', name)
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

        # ★ 城市地铁适用性：基于城市名判断
        city_lower = (ld.city or "").strip()
        subway_applicable_val = _city_has_subway(city_lower)
        if not subway_applicable_val and real_subway_count > 0:
            subway_applicable_val = True  # 1000米内已发现地铁→覆盖
        ld.city_has_subway = subway_applicable_val
        ld.subway_applicable = subway_applicable_val
        if not subway_applicable_val:
            quality_notes.append("该城市暂无地铁系统，地铁不纳入交通扣分项")

        # ★ 医院归并后处理：清零 stats + 按 group min_dist 重算三层半径 + 1条计数 + 1条明细
        if _hospital_groups:
            stats_200m["hospitals"] = 0
            stats_500m["hospitals"] = 0
            stats_1000m["hospitals"] = 0
            hosp_count = 0
            hosp_list = []
            for base, group in _hospital_groups.items():
                display_name = group["main_name"] or base
                dept_note = ""
                if group["dept_names"]:
                    unique_depts = list(dict.fromkeys(group["dept_names"]))[:6]
                    dept_note = "含" + "/".join(unique_depts) + "等院内POI，已归并计数"
                hosp_count += 1
                hosp_list.append({
                    "name": display_name,
                    "distance": group["min_dist"],
                    "address": group["main_poi"].get("address", "") if group["main_poi"] else "",
                    "note": dept_note,
                })
                # ★ 按归并后 min_dist 重算三层半径
                if group["min_dist"] <= 200:
                    stats_200m["hospitals"] += 1
                if group["min_dist"] <= 500:
                    stats_500m["hospitals"] += 1
                stats_1000m["hospitals"] += 1
            poi_counts["hospitals"] = hosp_count
            poi_lists["hospitals"] = hosp_list[:15]
            quality_notes.append(f"医院归并去重：原始 {raw_poi_counts.get('hospitals', 0)} 条POI合并为 {hosp_count} 家医院")

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
        ld.competitor_list = competitor_list[:15]

        # ★ 严谨度框架新字段
        ld.direct_competitors_200m = direct_comp_200m
        ld.direct_competitors_500m = direct_comp_500m
        ld.direct_competitors_1000m = direct_comp_1000m
        ld.direct_competitor_list = direct_comp_list[:15]
        ld.direct_competitor_list_200m = direct_comp_list_200m
        ld.direct_competitor_list_500m = direct_comp_list_500m
        ld.direct_competitor_list_1000m = direct_comp_list_1000m
        ld.substitute_competitors_200m = sub_200m
        ld.substitute_competitors_500m = sub_500m
        ld.substitute_competitors_1000m = sub_1000m
        ld.substitute_list = sub_list[:15]
        ld.substitute_list_200m = sub_list_200m
        ld.substitute_list_500m = sub_list_500m
        ld.substitute_list_1000m = sub_list_1000m
        ld.traffic_anchors_200m = anchor_200m
        ld.traffic_anchors_500m = anchor_500m
        ld.traffic_anchors_1000m = anchor_1000m
        ld.traffic_anchor_list = anchor_list[:20]
        ld.traffic_anchor_list_200m = anchor_list_200m
        ld.traffic_anchor_list_500m = anchor_list_500m
        ld.traffic_anchor_list_1000m = anchor_list_1000m
        ld.irrelevant_excluded = irrelevant_count
        # ★ 数据解释与边界 — 展示更有价值的分类统计
        market_200 = stats_200m.get("market_anchor", 0)
        market_500 = stats_500m.get("market_anchor", 0)
        market_1000 = stats_1000m.get("market_anchor", 0)
        market_list = poi_lists.get("market_anchor", [])
        shopping_500 = stats_500m.get("shopping", 0)
        shopping_1000 = stats_1000m.get("shopping", 0)
        low_freq_list = poi_lists.get("low_freq_retail", [])
        convenience_500 = stats_500m.get("convenience", 0)
        parking_500 = stats_500m.get("parking", 0)
        banks_500 = stats_500m.get("banks", 0)

        quality_notes.append(f"有效保留 {valid_kept} 个周边POI（原始采集 {len(all_pois)} 个）")
        if dewater_excluded > 0:
            quality_notes.append(f"名称脱水剔除 {dewater_excluded} 个（公司/厂房/培训/养生/中介等）")
        if irrelevant_count > 0:
            quality_notes.append(f"严谨度规则剔除 {irrelevant_count} 个（律所/广告/SPA等无关业态）")
        if shopping_1000 > 0:
            quality_notes.append(f"购物商场：500米{shopping_500}个 / 1000米{shopping_1000}个 — 代表逛街休闲类综合客流")
        if market_1000 > 0:
            market_samples = [p.get("name", "") for p in market_list[:5] if p.get("name")]
            mkt_note = f"市场/专业市场：500米{market_500}个 / 1000米{market_1000}个"
            if market_samples:
                mkt_note += f"（示例：{'、'.join(market_samples[:3])}）"
            mkt_note += " — 代表目的性采购客流，不等同于购物商场"
            quality_notes.append(mkt_note)
        if low_freq_list:
            lf_names = [p.get("name", "") for p in low_freq_list[:5] if p.get("name")]
            lf_note = f"低频目的零售：{len(low_freq_list)} 个（服装/数码/眼镜/品牌零售等）"
            if lf_names:
                lf_note += f"（示例：{'、'.join(lf_names[:3])}）"
            lf_note += " — 代表目的性消费，非高频日常客流"
            quality_notes.append(lf_note)
        if convenience_500 > 0:
            quality_notes.append(f"便利超市：500米{convenience_500}个 — 满足日常即时需求")
        if parking_500 > 0:
            quality_notes.append(f"停车场：500米{parking_500}个 — 驾车便利性参考")
        if banks_500 > 0:
            quality_notes.append(f"银行：500米{banks_500}个 — 周边成熟度和中高端客群参考")
        # 零计数诊断：严格口径为 0 但有原始候选时说明
        office_raw = raw_poi_counts.get("office", 0)
        hospital_raw = raw_poi_counts.get("hospitals", 0)
        office_500s = stats_500m.get("office", 0)
        hospital_500s = stats_500m.get("hospitals", 0)
        market_500s = stats_500m.get("market_anchor", 0)
        if office_500s == 0 and office_raw > 0:
            quality_notes.append("写字楼：严格口径下为 0（已排除公司/厂房/培训等名称脱水），不代表周边无办公人群")
        if hospital_500s == 0 and hospital_raw > 0:
            quality_notes.append("医院：严格口径下为 0（医院=大型医疗机构，不含诊所/药店/门诊）")
        if market_500s == 0:
            quality_notes.append("市场/专业市场：周边未识别到农贸/建材/五金等专业市场")
        # ★ P0.5: 公交采集诊断
        bus_s200 = stats_200m.get("bus", 0)
        bus_s500 = stats_500m.get("bus", 0)
        bus_s1000 = stats_1000m.get("bus", 0)
        bus_cls_count = poi_counts.get("bus", 0)
        bus_seen_count = len(bus_seen)
        print(f"[BUS_DIAG] type={_bus_type_count} kw={_bus_kw_count} seen={bus_seen_count} "
              f"cls={bus_cls_count} s200={bus_s200} s500={bus_s500} s1000={bus_s1000} "
              f"dist_missing={_bus_dist_missing}", flush=True)
        ld.data_quality_notes = quality_notes

        # 品牌排序
        brand_list = sorted(brands.values(), key=lambda x: -x["count"])
        ld.hot_brands = [{
            "name": b["name"],
            "count": b["count"],
            "min_distance": min(b["distances"]) if b["distances"] else 0,
        } for b in brand_list[:15]]

        return ld


async def collect_location_data(lng: float, lat: float,
                                 amap_type: str = "",
                                 config_key: str = "",
                                 business_type: str = "",
                                 brand_name: str = "") -> LocationData:
    """amap_type: 高德POI类型码 | config_key: 行业集群key | business_type: 业态名称 | brand_name: 品牌描述"""
    service = AmapService()
    return await service.collect_all(lng, lat, amap_type=amap_type, config_key=config_key, business_type=business_type, brand_name=brand_name)
