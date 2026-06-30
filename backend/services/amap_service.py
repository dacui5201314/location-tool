"""amap_service 兼容入口 —— 保持原外部导入路径不变。
实际实现拆分至：
  - amap_models.py（LocationData / 城市拓扑数据）
  - amap_poi_rules.py（POI 分类规则纯函数）
  - amap_collect_service.py（AmapService / HTTP 请求 / 采集流程）
"""
from services.amap_models import *
from services.amap_poi_rules import *
from services.amap_collect_service import *
