from services.amap_poi_rules import *
async def collect_location_data(lng: float, lat: float,
                                 amap_type: str = "",
                                 config_key: str = "",
                                 business_type: str = "",
                                 brand_name: str = "") -> LocationData:
    """amap_type: 高德POI类型码 | config_key: 行业集群key | business_type: 业态名称 | brand_name: 品牌描述"""
    service = AmapService()
    return await service.collect_all(lng, lat, amap_type=amap_type, config_key=config_key, business_type=business_type, brand_name=brand_name)
