"""Phase 4J: 60个模型族群样本回归库 — 12族 x5样本"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.business_model_service import (
    classify_business_model_family, compute_business_model_snapshot,
    load_business_model,
)
from services.location_profile_service import compute_location_profile
from services.fallback_report_service import build_fallback_report
from services.report_enrichment_service import enrich_report_business_context
from services.storage_service import _build_report_html


def _make_rd(**overrides):
    base = {
        "stats_200m":{"residential":2,"office":1,"schools":1,"hospitals":0,"subway":0,"bus":1,"parking":1,"shopping":0,"hotels":0,"restaurants":3},
        "stats_500m":{"residential":8,"office":5,"schools":3,"hospitals":1,"subway":1,"bus":5,"parking":3,"shopping":1,"hotels":2,"restaurants":15},
        "stats_1000m":{"residential":20,"office":10,"schools":6,"hospitals":2,"subway":2,"bus":10,"parking":8,"shopping":3,"hotels":5,"restaurants":40},
        "direct_competitors_200m":2,"direct_competitors_500m":4,"direct_competitors_1000m":8,
        "substitute_competitors_200m":0,"substitute_competitors_500m":2,"substitute_competitors_1000m":5,
        "traffic_anchors_200m":1,"traffic_anchors_500m":4,"traffic_anchors_1000m":10,
        "direct_competitor_list":[],"direct_competitor_list_200m":[],"direct_competitor_list_500m":[],"direct_competitor_list_1000m":[],
        "substitute_list":[],"traffic_anchor_list":[],"poi_lists":{},"hot_brands":[],"nearby_roads":[],
        "rigor_enabled":True,"subway_applicable":True,"city_has_subway":True,
    }
    base.update(overrides)
    return base


# ═══════════════════════════════════════════════
# 18 个样本
# ═══════════════════════════════════════════════

SAMPLES = [
    # ── 基础 12 个 ──
    {
        "case_id": "snack_fast_food_01",
        "expected_model_id": "snack_fast_food", "model_id": "snack_fast_food",
        "business_type": "小吃快餐", "brand_name": "砂锅小吃", "store_size": 50,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=3, direct_competitors_1000m=12,
            stats_1000m={"residential":13,"office":0,"schools":9,"hospitals":1,"subway":0,"bus":8,"parking":26,"shopping":0,"hotels":7,"restaurants":56}),
        "expected_present": ["直接竞品","替代消费","客流锚点","现场核验清单"],
        "expected_absent": ["市场空白明显","先发优势","竞争环境宽松","推荐开店","值得投资"],
    },
    {
        "case_id": "food_service_01",
        "expected_model_id": "food_service", "model_id": "food_service","business_type": "中餐", "brand_name": "湘菜馆", "store_size": 200,
        "real_data": _make_rd(direct_competitors_200m=3, direct_competitors_500m=5, direct_competitors_1000m=8),
        "expected_present": ["直接竞品","现场核验清单"],
        "expected_absent": ["市场空白明显","先发优势","推荐开店","值得投资"],
    },
    {
        "case_id": "beverage_dessert_01",
        "expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type": "奶茶店", "brand_name": "茶百道", "store_size": 20,
        "real_data": _make_rd(direct_competitors_200m=1, direct_competitors_500m=3, direct_competitors_1000m=6),
        "expected_present": ["直接竞品","现场核验清单"],
        "expected_absent": ["市场空白明显","先发优势","推荐开店"],
    },
    {
        "case_id": "retail_convenience_01",
        "expected_model_id": "retail_convenience", "model_id": "retail_convenience","business_type": "便利店", "brand_name": "全家", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=1, direct_competitors_1000m=3),
        "expected_present": ["直接竞品"],
        "expected_absent": ["推荐开店","值得投资","出餐速度","外卖骑手"],
    },
    {
        "case_id": "pharmacy_01",
        "expected_model_id": "pharmacy", "model_id": "pharmacy","business_type": "药店", "brand_name": "", "store_size": 80,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_present": ["直接竞品","现场核验清单"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },
    {
        "case_id": "retail_shopping_01",
        "expected_model_id": "retail_shopping", "model_id": "retail_shopping","business_type": "服装店", "brand_name": "", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=2, direct_competitors_1000m=4),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","推荐开店"],
    },
    {
        "case_id": "education_childcare_01",
        "expected_model_id": "education_childcare", "model_id": "education_childcare","business_type": "教育培训", "brand_name": "小学生托管服务", "store_size": 100,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":4,"office":0,"schools":4,"subway":0,"bus":2,"parking":6,"shopping":0,"hotels":2,"restaurants":11}),
        "expected_present": ["直接竞品","托管","暗竞品","放学"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","外卖骑手","出餐速度","上座率","午晚高峰堂食","排队","推荐开店"],
    },
    {
        "case_id": "education_training_01",
        "expected_model_id": "education_training", "model_id": "education_training","business_type": "教育培训", "brand_name": "英语培训", "store_size": 80,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=1, direct_competitors_1000m=2),
        "expected_present": ["直接竞品"],
        "expected_absent": ["午托","小饭桌","餐食成本","市场空白明显","推荐开店"],
    },
    {
        "case_id": "service_basic_01",
        "expected_model_id": "service_basic", "model_id": "service_basic","business_type": "洗衣店", "brand_name": "", "store_size": 30,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","外卖骑手","出餐速度","推荐开店"],
    },
    {
        "case_id": "service_beauty_01",
        "expected_model_id": "service_beauty", "model_id": "service_beauty","business_type": "美容美发", "brand_name": "", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","品类切入空间较好","外卖骑手","出餐速度"],
    },
    {
        "case_id": "hotel_01",
        "expected_model_id": "hotel", "model_id": "hotel","business_type": "酒店", "brand_name": "汉庭", "store_size": 2000,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },
    {
        "case_id": "entertainment_01",
        "expected_model_id": "entertainment", "model_id": "entertainment","business_type": "酒吧", "brand_name": "", "store_size": 200,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },

    # ── 补齐 6 个第二样本 ──
    {
        "case_id": "food_service_02",
        "expected_model_id": "food_service", "model_id": "food_service","business_type": "火锅店", "brand_name": "重庆老火锅", "store_size": 250,
        "real_data": _make_rd(direct_competitors_200m=2, direct_competitors_500m=6, direct_competitors_1000m=10,
            stats_500m={"residential":10,"office":8,"schools":2,"hospitals":1,"subway":1,"bus":6,"parking":4,"shopping":2,"hotels":3,"restaurants":20}),
        "expected_present": ["直接竞品","停车","排烟","消防"],
        "expected_absent": ["市场空白明显","推荐开店"],
    },
    {
        "case_id": "beverage_dessert_02",
        "expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type": "咖啡店", "brand_name": "瑞幸", "store_size": 15,
        "real_data": _make_rd(direct_competitors_200m=1, direct_competitors_500m=4, direct_competitors_1000m=8,
            stats_500m={"residential":6,"office":10,"schools":2,"hospitals":0,"subway":2,"bus":8,"parking":3,"shopping":1,"hotels":1,"restaurants":15}),
        "expected_present": ["直接竞品","步行","动线","外卖"],
        "expected_absent": ["市场空白明显","先发优势","推荐开店"],
    },
    {
        "case_id": "retail_convenience_02",
        "expected_model_id": "retail_convenience", "model_id": "retail_convenience","business_type": "生鲜店", "brand_name": "社区生鲜", "store_size": 80,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=2, direct_competitors_1000m=4,
            stats_500m={"residential":15,"office":2,"schools":2,"hospitals":0,"subway":0,"bus":4,"parking":2,"shopping":0,"hotels":0,"restaurants":6}),
        "expected_present": ["直接竞品","住宅","动线","入住"],
        "expected_absent": ["推荐开店","出餐速度","外卖骑手"],
    },
    {
        "case_id": "retail_shopping_02",
        "expected_model_id": "retail_shopping", "model_id": "retail_shopping","business_type": "数码店", "brand_name": "", "store_size": 50,
        "real_data": _make_rd(direct_competitors_200m=1, direct_competitors_500m=3, direct_competitors_1000m=5,
            stats_500m={"residential":5,"office":6,"schools":1,"hospitals":0,"subway":1,"bus":7,"parking":3,"shopping":2,"hotels":1,"restaurants":12}),
        "expected_present": ["直接竞品","商圈","电商"],
        "expected_absent": ["市场空白明显","推荐开店"],
    },
    {
        "case_id": "service_basic_02",
        "expected_model_id": "service_basic", "model_id": "service_basic","business_type": "诊所", "brand_name": "", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=1, direct_competitors_1000m=2,
            stats_500m={"residential":12,"office":3,"schools":2,"hospitals":1,"subway":0,"bus":4,"parking":2,"shopping":0,"hotels":0,"restaurants":8}),
        "expected_present": ["直接竞品","住宅","资质"],
        "expected_absent": ["市场空白明显","外卖骑手","出餐速度","推荐开店"],
    },
    {
        "case_id": "service_beauty_02",
        "expected_model_id": "service_beauty", "model_id": "service_beauty","business_type": "健身房", "brand_name": "私教工作室", "store_size": 200,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=1,
            stats_500m={"residential":10,"office":5,"schools":2,"hospitals":0,"subway":1,"bus":6,"parking":3,"shopping":1,"hotels":1,"restaurants":10}),
        "expected_present": ["直接竞品","消费力","会员"],
        "expected_absent": ["市场空白明显","品类切入空间较好","外卖骑手","出餐速度"],
    },

    # ── 高风险 6 个 ──
    {
        "case_id": "snack_fast_food_02_highrisk",
        "expected_model_id": "snack_fast_food", "model_id": "snack_fast_food","business_type": "小吃快餐", "brand_name": "麻辣烫", "store_size": 40,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=2, direct_competitors_1000m=15,
            stats_500m={"residential":3,"office":0,"schools":4,"subway":0,"bus":1,"parking":2,"shopping":0,"hotels":1,"restaurants":8},
            stats_1000m={"residential":8,"office":1,"schools":8,"hospitals":0,"subway":0,"bus":3,"parking":5,"shopping":0,"hotels":2,"restaurants":50}),
        "expected_present": ["直接竞品","远场","低租金"],
        "expected_absent": ["市场空白明显","先发优势","竞争环境宽松","品类切入空间较好"],
    },
    {
        "case_id": "education_childcare_02_highrisk",
        "expected_model_id": "education_childcare", "model_id": "education_childcare","business_type": "教育培训", "brand_name": "午托晚托作业辅导", "store_size": 120,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":6,"office":0,"schools":5,"subway":0,"bus":2,"parking":4,"shopping":0,"hotels":1,"restaurants":8}),
        "expected_present": ["暗竞品","放学","合规","消防","空间"],
        "expected_absent": ["外卖骑手","出餐速度","上座率","午晚高峰堂食","排队","市场空白明显","品类切入空间较好"],
    },
    {
        "case_id": "education_training_02_highrisk",
        "expected_model_id": "education_training", "model_id": "education_training","business_type": "教育培训", "brand_name": "美术培训", "store_size": 80,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=1,
            stats_500m={"residential":12,"office":2,"schools":3,"subway":1,"bus":6,"parking":3,"shopping":1,"hotels":1,"restaurants":10}),
        "expected_present": ["直接竞品","办学","消防"],
        "expected_absent": ["午托","小饭桌","餐食成本","托管接送","外卖骑手","市场空白明显"],
    },
    {
        "case_id": "pharmacy_02_highrisk",
        "expected_model_id": "pharmacy", "model_id": "pharmacy","business_type": "药店", "brand_name": "", "store_size": 80,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":10,"office":3,"schools":2,"hospitals":2,"subway":1,"bus":6,"parking":3,"shopping":1,"hotels":1,"restaurants":12}),
        "expected_present": ["直接竞品","医院","锚点"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好"],
    },
    {
        "case_id": "hotel_02_highrisk",
        "expected_model_id": "hotel", "model_id": "hotel","business_type": "酒店", "brand_name": "", "store_size": 3000,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":5,"office":2,"schools":1,"hospitals":0,"subway":0,"bus":2,"parking":2,"shopping":0,"hotels":0,"restaurants":5},
            stats_1000m={"residential":10,"office":3,"schools":2,"hospitals":0,"subway":0,"bus":4,"parking":4,"shopping":0,"hotels":1,"restaurants":12}),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },
    {
        "case_id": "entertainment_02_highrisk",
        "expected_model_id": "entertainment", "model_id": "entertainment","business_type": "KTV", "brand_name": "", "store_size": 400,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":15,"office":1,"schools":1,"hospitals":0,"subway":0,"bus":2,"parking":2,"shopping":0,"hotels":0,"restaurants":5},
            stats_1000m={"residential":30,"office":2,"schools":2,"hospitals":0,"subway":0,"bus":4,"parking":4,"shopping":0,"hotels":1,"restaurants":15}),
        "expected_present": ["直接竞品","隔音","消防"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },

    # ── 第三样本：典型误判场景 ──
    # 排斥型 0竞品但需求弱
    {
        "case_id": "snack_fast_food_03_weakdemand",
        "expected_model_id": "snack_fast_food", "model_id": "snack_fast_food","business_type": "小餐饮", "brand_name": "煎饼摊", "store_size": 15,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=2,
            stats_500m={"residential":2,"office":0,"schools":1,"subway":0,"bus":1,"parking":1,"shopping":0,"hotels":0,"restaurants":3},
            stats_1000m={"residential":4,"office":0,"schools":2,"subway":0,"bus":2,"parking":2,"shopping":0,"hotels":0,"restaurants":8}),
        "expected_present": ["直接竞品","需求","核验"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","竞争环境宽松"],
    },
    # 半聚集型 有同类但不能直接推荐
    {
        "case_id": "food_service_03_semiagg",
        "expected_model_id": "food_service", "model_id": "food_service","business_type": "烧烤店", "brand_name": "", "store_size": 150,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=3, direct_competitors_1000m=7,
            stats_500m={"residential":8,"office":3,"schools":1,"subway":0,"bus":4,"parking":3,"shopping":1,"hotels":2,"restaurants":18}),
        "expected_present": ["直接竞品","晚市","停车"],
        "expected_absent": ["市场空白明显","推荐开店","值得投资"],
    },
    # 半聚集型茶饮 0竞品不写空白
    {
        "case_id": "beverage_dessert_03_semiagg",
        "expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type": "饮品店", "brand_name": "", "store_size": 20,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=1,
            stats_500m={"residential":6,"office":3,"schools":1,"subway":0,"bus":3,"parking":1,"shopping":0,"hotels":0,"restaurants":8}),
        "expected_present": ["直接竞品","步行","人流"],
        "expected_absent": ["市场空白明显","先发优势","推荐开店"],
    },
    # 排斥型便利 住宅弱时不写推荐
    {
        "case_id": "retail_convenience_03_weakresident",
        "expected_model_id": "retail_convenience", "model_id": "retail_convenience","business_type": "小超市", "brand_name": "", "store_size": 40,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=1,
            stats_500m={"residential":3,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
        "expected_present": ["直接竞品","住宅"],
        "expected_absent": ["推荐开店","值得投资"],
    },
    # 中性型药店 医院锚点弱 0竞品不写机会
    {
        "case_id": "pharmacy_03_neutral",
        "expected_model_id": "pharmacy", "model_id": "pharmacy","business_type": "药房", "brand_name": "", "store_size": 60,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":5,"office":2,"schools":1,"hospitals":0,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":5}),
        "expected_present": ["直接竞品","人口"],
        "expected_absent": ["市场空白明显","品类切入空间较好","推荐开店"],
    },
    # 中性型零售 孤立选址不写机会
    {
        "case_id": "retail_shopping_03_isolated",
        "expected_model_id": "retail_shopping", "model_id": "retail_shopping","business_type": "零售店", "brand_name": "", "store_size": 40,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":4,"office":1,"schools":1,"subway":0,"bus":1,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
        "expected_present": ["直接竞品","商圈","孤立"],
        "expected_absent": ["市场空白明显","推荐开店"],
    },
    # 暗竞品型托管 brand_name空+category托管(通过category识别)
    {
        "case_id": "education_childcare_03_categoryonly",
        "expected_model_id": "education_childcare", "model_id": "education_childcare","business_type": "教育培训", "brand_name": "", "category": "小学生课后托管服务", "store_size": 100,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":5,"office":0,"schools":4,"subway":0,"bus":2,"parking":4,"shopping":0,"hotels":1,"restaurants":7}),
        "expected_present": ["直接竞品","暗竞品","放学"],
        "expected_absent": ["外卖骑手","出餐速度","上座率","市场空白明显"],
    },
    # 聚集型培训 0竞品需看满班率
    {
        "case_id": "education_training_03_aggregation",
        "expected_model_id": "education_training", "model_id": "education_training","business_type": "教育培训", "brand_name": "舞蹈培训", "store_size": 100,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":10,"office":3,"schools":2,"subway":1,"bus":5,"parking":2,"shopping":1,"hotels":1,"restaurants":8}),
        "expected_present": ["直接竞品","满班率","生源"],
        "expected_absent": ["午托","外卖骑手","出餐速度","市场空白明显"],
    },
    # 暗竞品型洗衣 0POI需提示低收录
    {
        "case_id": "service_basic_03_hidden",
        "expected_model_id": "service_basic", "model_id": "service_basic","business_type": "洗衣店", "brand_name": "社区干洗", "store_size": 25,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":10,"office":1,"schools":2,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":0,"restaurants":6}),
        "expected_present": ["直接竞品","住宅"],
        "expected_absent": ["市场空白明显","外卖骑手","出餐速度"],
    },
    # 暗竞品型美业 0POI需提示工作室漏收录
    {
        "case_id": "service_beauty_03_hidden",
        "expected_model_id": "service_beauty", "model_id": "service_beauty","business_type": "宠物店", "brand_name": "", "store_size": 50,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":8,"office":2,"schools":1,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":0,"restaurants":5}),
        "expected_present": ["直接竞品","工作室","消费力"],
        "expected_absent": ["市场空白明显","品类切入空间较好","外卖骑手"],
    },
    # 聚集型酒店 0竞品+交通弱
    {
        "case_id": "hotel_03_notadvantage",
        "expected_model_id": "hotel", "model_id": "hotel","business_type": "民宿", "brand_name": "", "store_size": 500,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":6,"office":2,"schools":1,"hospitals":0,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4},
            stats_1000m={"residential":12,"office":3,"schools":2,"hospitals":0,"subway":0,"bus":3,"parking":3,"shopping":0,"hotels":1,"restaurants":10}),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },
    # 聚集型娱乐 0竞品+合规弱
    {
        "case_id": "entertainment_03_nightweak",
        "expected_model_id": "entertainment", "model_id": "entertainment","business_type": "台球厅", "brand_name": "", "store_size": 300,
        "real_data": _make_rd(direct_competitors_200m=0, direct_competitors_500m=0, direct_competitors_1000m=0,
            stats_500m={"residential":10,"office":1,"schools":1,"subway":0,"bus":2,"parking":2,"shopping":0,"hotels":0,"restaurants":5},
            stats_1000m={"residential":20,"office":2,"schools":2,"subway":0,"bus":3,"parking":3,"shopping":0,"hotels":1,"restaurants":10}),
        "expected_present": ["直接竞品"],
        "expected_absent": ["市场空白明显","先发优势","品类切入空间较好","推荐开店"],
    },

    # ── Phase 4J: 24个新增样本 (12族x2) ──
    # 01 snack: 近场0竞品远场多; 学校强寒暑假弱
    {"case_id":"snack_fast_food_04","expected_model_id": "snack_fast_food", "model_id": "snack_fast_food","business_type":"小吃快餐","brand_name":"麻辣烫","store_size":40,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=4,direct_competitors_1000m=14,stats_500m={"residential":3,"office":0,"schools":5,"subway":0,"bus":2,"parking":2,"shopping":0,"hotels":1,"restaurants":10},stats_1000m={"residential":8,"office":1,"schools":8,"subway":0,"bus":4,"parking":4,"shopping":0,"hotels":2,"restaurants":55}),
     "expected_present":["直接竞品","远场"],"expected_absent":["市场空白明显","先发优势","竞争环境宽松"]},
    {"case_id":"snack_fast_food_05","expected_model_id": "snack_fast_food", "model_id": "snack_fast_food","business_type":"小吃快餐","brand_name":"炸鸡","store_size":30,
     "real_data":_make_rd(direct_competitors_200m=1,direct_competitors_500m=3,direct_competitors_1000m=6,stats_500m={"residential":2,"office":0,"schools":6,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":5},stats_1000m={"residential":5,"office":0,"schools":10,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":0,"restaurants":12}),
     "expected_present":["直接竞品","学校","晚餐"],"expected_absent":["市场空白明显","竞争环境宽松"]},
    # 01.5 snack P2: schools=5 全大学/培训 → checklist 不得出现学校午休/放学动线
    {"case_id":"snack_fast_food_06_university","expected_model_id": "snack_fast_food", "model_id": "snack_fast_food","business_type":"小吃快餐","brand_name":"","store_size":40,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=2,direct_competitors_1000m=4,stats_500m={"residential":4,"office":0,"schools":5,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":1,"restaurants":8},poi_lists={"schools":[{"name":"宝鸡文理学院"},{"name":"宝鸡职业技术学院"},{"name":"某师范大学"},{"name":"某理工学校"},{"name":"新东方培训中心"}]}),
     "expected_present":["直接竞品","午高峰"],"expected_absent":["学校午休","放学动线","市场空白明显"]},
    # 01.5 snack G6: direct少+substitute高 → 替代消费分流核验
    {"case_id":"snack_fast_food_07_substitute","expected_model_id": "snack_fast_food", "model_id": "snack_fast_food","business_type":"小吃快餐","brand_name":"","store_size":40,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=2,substitute_competitors_200m=2,substitute_competitors_500m=5,substitute_competitors_1000m=8,stats_500m={"residential":6,"office":3,"schools":2,"subway":1,"bus":5,"parking":2,"shopping":1,"hotels":1,"restaurants":15}),
     "expected_present":["替代消费","分流","直接竞品"],"expected_absent":["市场空白明显"]},

    # 02 food_service: 停车排烟消防不足; 办公热闹晚市弱
    {"case_id":"food_service_04","expected_model_id": "food_service", "model_id": "food_service","business_type":"中餐","brand_name":"","store_size":150,
     "real_data":_make_rd(direct_competitors_200m=1,direct_competitors_500m=4,direct_competitors_1000m=8,stats_500m={"residential":4,"office":0,"schools":2,"subway":0,"bus":3,"parking":0,"shopping":1,"hotels":1,"restaurants":12}),
     "expected_present":["停车","排烟","消防"],"expected_absent":["市场空白明显","推荐开店"]},
    {"case_id":"food_service_05","expected_model_id": "food_service", "model_id": "food_service","business_type":"火锅店","brand_name":"","store_size":200,
     "real_data":_make_rd(direct_competitors_200m=2,direct_competitors_500m=5,direct_competitors_1000m=10,stats_500m={"residential":5,"office":12,"schools":1,"subway":1,"bus":6,"parking":3,"shopping":2,"hotels":2,"restaurants":20},stats_1000m={"residential":10,"office":20,"schools":2,"subway":2,"bus":10,"parking":5,"shopping":3,"hotels":4,"restaurants":40}),
     "expected_present":["晚市","停车"],"expected_absent":["推荐开店"]},
    # 02.5 food_service G1: 0竞品 → competitor_note 含半聚集型/停车/餐饮生态
    {"case_id":"food_service_06_zero_comp","expected_model_id": "food_service", "model_id": "food_service","business_type":"中餐","brand_name":"","store_size":150,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":4,"office":0,"schools":2,"subway":0,"bus":3,"parking":0,"shopping":1,"hotels":1,"restaurants":12},stats_1000m={"residential":10,"office":0,"schools":4,"subway":0,"bus":6,"parking":2,"shopping":1,"hotels":2,"restaurants":25}),
     "expected_present":["半聚集","停车","直接竞品"],"expected_absent":["市场空白","蓝海","直接竞争压力较小","推荐开店"]},

    # 03 beverage: 0竞品缺年轻客群; 平台强品牌覆盖
    {"case_id":"beverage_dessert_04","expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type":"奶茶店","brand_name":"","store_size":15,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=1,stats_500m={"residential":8,"office":0,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":6}),
     "expected_present":["直接竞品","步行","人流","客群"],"expected_absent":["市场空白明显","先发优势","推荐开店"]},
    {"case_id":"beverage_dessert_05","expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type":"咖啡店","brand_name":"","store_size":20,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=1,direct_competitors_1000m=3,stats_500m={"residential":6,"office":3,"schools":1,"subway":1,"bus":5,"parking":1,"shopping":1,"hotels":1,"restaurants":10}),
     "expected_present":["直接竞品", "品牌"],"expected_absent":["市场空白明显","推荐开店"]},
    # 03.5 beverage G2: school=6 res=2 office=1 → 必须含校门口步行动线核验，禁止年轻客群充足
    {"case_id":"beverage_dessert_06_schoolflow","expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type":"饮品店","brand_name":"","store_size":20,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=1,stats_500m={"residential":2,"office":1,"schools":6,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品", "步行动线", "放学时段"],"expected_absent":["年轻客群充足","市场空白明显","推荐开店"]},
    # 03.5 beverage_dessert G2: 0竞品 → competitor_note 含步行动线/外卖平台/半聚集
    {"case_id":"beverage_dessert_07_zero_comp","expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type":"咖啡店","brand_name":"","store_size":20,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":6,"office":3,"schools":1,"subway":1,"bus":5,"parking":1,"shopping":1,"hotels":1,"restaurants":10}),
     "expected_present":["步行动线","半聚集","直接竞品"],"expected_absent":["市场空白","蓝海","直接竞争压力较小","推荐开店"]},
    # 03.5 beverage G5: 0竞品+hot_brands 含强品牌 → 提示外卖平台/强品牌覆盖
    {"case_id":"beverage_dessert_08_strongbrand","expected_model_id": "beverage_dessert", "model_id": "beverage_dessert","business_type":"咖啡店","brand_name":"瑞幸","store_size":20,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":6,"office":5,"schools":1,"subway":1,"bus":5,"parking":1,"shopping":1,"hotels":1,"restaurants":10},hot_brands=[{"name":"瑞幸咖啡"},{"name":"星巴克"},{"name":"霸王茶姬"}]),
     "expected_present":["步行动线","外卖平台","直接竞品"],"expected_absent":["市场空白","直接竞争压力较小","推荐开店"]},

    # 04 retail_convenience: 住宅多动线不经过; 入住率不足
    {"case_id":"retail_convenience_04","expected_model_id": "retail_convenience", "model_id": "retail_convenience","business_type":"便利店","brand_name":"","store_size":50,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=1,direct_competitors_1000m=2,stats_500m={"residential":12,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":5}),
     "expected_present":["直接竞品","动线","入住"],"expected_absent":["推荐开店","值得投资"]},
    {"case_id":"retail_convenience_05","expected_model_id": "retail_convenience", "model_id": "retail_convenience","business_type":"小超市","brand_name":"","store_size":40,
     "real_data":_make_rd(direct_competitors_200m=1,direct_competitors_500m=2,direct_competitors_1000m=4,stats_500m={"residential":8,"office":2,"schools":1,"subway":0,"bus":3,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品","住宅","入住"],"expected_absent":["推荐开店"]},
    # 04.5 retail_convenience school-dominant: school=8+res=2，不应写学生客群稳定
    {"case_id":"retail_convenience_06_schooldominant","expected_model_id": "retail_convenience", "model_id": "retail_convenience","business_type":"便利店","brand_name":"","store_size":50,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":2,"office":1,"schools":8,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":3}),
     "expected_present":["直接竞品","住宅"],"expected_absent":["学生客群稳定","推荐开店"]},

    # 05 pharmacy: 医院社区支撑弱; 周边药店多不简单写机会劣势
    {"case_id":"pharmacy_04","expected_model_id": "pharmacy", "model_id": "pharmacy","business_type":"药店","brand_name":"","store_size":60,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":4,"office":1,"schools":0,"hospitals":0,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品", "医院"],"expected_absent":["市场空白明显","品类切入空间较好","推荐开店"]},
    {"case_id":"pharmacy_05","expected_model_id": "pharmacy", "model_id": "pharmacy","business_type":"药房","brand_name":"","store_size":80,
     "real_data":_make_rd(direct_competitors_200m=1,direct_competitors_500m=3,direct_competitors_1000m=5,stats_500m={"residential":10,"office":3,"schools":2,"hospitals":1,"subway":1,"bus":6,"parking":2,"shopping":1,"hotels":1,"restaurants":12}),
     "expected_present":["直接竞品", "动线"],"expected_absent":["推荐开店"]},

    # 06 retail_shopping: 弱商圈低频; 有商场但品类楼层动线不匹配
    {"case_id":"retail_shopping_04","expected_model_id": "retail_shopping", "model_id": "retail_shopping","business_type":"服装店","brand_name":"","store_size":50,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=1,stats_500m={"residential":5,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":5}),
     "expected_present":["直接竞品","商圈"],"expected_absent":["市场空白明显","推荐开店"]},
    {"case_id":"retail_shopping_05","expected_model_id": "retail_shopping", "model_id": "retail_shopping","business_type":"数码店","brand_name":"","store_size":40,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=1,direct_competitors_1000m=3,stats_500m={"residential":6,"office":4,"schools":1,"subway":1,"bus":5,"parking":2,"shopping":1,"hotels":1,"restaurants":8}),
     "expected_present":["直接竞品", "动线"],"expected_absent":["推荐开店"]},

    # 07 education_childcare: 学校多动线不安全; 0POI暗竞品漏收录
    {"case_id":"education_childcare_04","expected_model_id": "education_childcare", "model_id": "education_childcare","business_type":"教育培训","brand_name":"午托晚托","store_size":100,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":5,"office":0,"schools":6,"subway":0,"bus":1,"parking":2,"shopping":0,"hotels":0,"restaurants":6}),
     "expected_present":["直接竞品","暗竞品","动线"],"expected_absent":["外卖骑手","出餐速度","市场空白明显"]},
    {"case_id":"education_childcare_05","expected_model_id": "education_childcare", "model_id": "education_childcare","business_type":"教育培训","brand_name":"课后服务","store_size":80,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":3,"office":0,"schools":3,"subway":0,"bus":2,"parking":2,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品","暗竞品"],"expected_absent":["外卖骑手","出餐速度","上座率"]},

    # 08 education_training: 有学校消费力弱; 0竞品不写强优势
    {"case_id":"education_training_04","expected_model_id": "education_training", "model_id": "education_training","business_type":"教育培训","brand_name":"学科辅导","store_size":80,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":8,"office":1,"schools":4,"subway":0,"bus":3,"parking":1,"shopping":0,"hotels":0,"restaurants":5}),
     "expected_present":["直接竞品", "生源"],"expected_absent":["午托","市场空白明显"]},
    {"case_id":"education_training_05","expected_model_id": "education_training", "model_id": "education_training","business_type":"教育培训","brand_name":"","store_size":60,
     "real_data":_make_rd(direct_competitors_200m=1,direct_competitors_500m=2,direct_competitors_1000m=4,stats_500m={"residential":7,"office":6,"schools":3,"subway":1,"bus":6,"parking":3,"shopping":1,"hotels":1,"restaurants":12}),
     "expected_present":["直接竞品","停车"],"expected_absent":["午托","外卖骑手"]},
    # 08.5 education_training G3: school=5 res=2 → 禁止生源充足，必须含消费力核验
    {"case_id":"education_training_06_weakspend","expected_model_id": "education_training", "model_id": "education_training","business_type":"教育培训","brand_name":"美术培训","store_size":80,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":2,"office":1,"schools":5,"subway":1,"bus":3,"parking":2,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品", "消费力", "客单价", "满班率"],"expected_absent":["生源充足","午托","外卖骑手"]},

    # 09 service_basic: 暗竞品漏收录; 合规资质不足
    {"case_id":"service_basic_04","expected_model_id": "service_basic", "model_id": "service_basic","business_type":"洗衣店","brand_name":"","store_size":25,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":9,"office":1,"schools":2,"subway":0,"bus":3,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品","资质"],"expected_absent":["市场空白明显","外卖骑手","出餐速度"]},
    {"case_id":"service_basic_05","expected_model_id": "service_basic", "model_id": "service_basic","business_type":"诊所","brand_name":"","store_size":50,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=1,stats_500m={"residential":10,"office":2,"schools":2,"hospitals":0,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":0,"restaurants":5}),
     "expected_present":["资质","合规"],"expected_absent":["市场空白明显","推荐开店"]},

    # 10 service_beauty: 工作室暗竞品; 宠物噪音气味物业限制
    {"case_id":"service_beauty_04","expected_model_id": "service_beauty", "model_id": "service_beauty","business_type":"美容美发","brand_name":"","store_size":50,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=1,stats_500m={"residential":8,"office":2,"schools":1,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":0,"restaurants":5}),
     "expected_present":["工作室","暗竞品"],"expected_absent":["市场空白明显","品类切入空间较好","外卖骑手"]},
    {"case_id":"service_beauty_05","expected_model_id": "service_beauty", "model_id": "service_beauty","business_type":"宠物店","brand_name":"","store_size":60,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":7,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品", "暗竞品", "工作室", "物业", "噪音", "气味"],"expected_absent":["市场空白明显","外卖骑手"]},
    # 10.5 service_beauty category-only: business_type无宠物关键词，category="宠物店" 触发 pet 分支
    {"case_id":"service_beauty_06","expected_model_id": "service_beauty", "model_id": "service_beauty","business_type":"专业生活服务","brand_name":"","category":"宠物店","store_size":60,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":7,"office":1,"schools":1,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品", "工作室", "物业", "噪音", "气味"],"expected_absent":["市场空白明显","外卖骑手"]},

    # 11 hotel: 商业热闹缺过夜需求; 0竞品不写蓝海
    {"case_id":"hotel_04","expected_model_id": "hotel", "model_id": "hotel","business_type":"酒店","brand_name":"","store_size":2000,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":6,"office":3,"schools":1,"subway":0,"bus":3,"parking":2,"shopping":1,"hotels":0,"restaurants":20}),
     "expected_present":["直接竞品", "住宿"],"expected_absent":["市场空白明显","先发优势","品类切入空间较好","推荐开店"]},
    {"case_id":"hotel_05","expected_model_id": "hotel", "model_id": "hotel","business_type":"民宿","brand_name":"","store_size":500,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=1,direct_competitors_1000m=3,stats_500m={"residential":5,"office":1,"schools":1,"subway":0,"bus":3,"parking":2,"shopping":0,"hotels":1,"restaurants":8}),
     "expected_present":["直接竞品"],"expected_absent":["市场空白明显","推荐开店"]},
    # 11.5 hotel school-dominant: school=8+res=3，不应写学生客群稳定
    {"case_id":"hotel_06_no_school_bias","expected_model_id": "hotel", "model_id": "hotel","business_type":"酒店","brand_name":"","store_size":2000,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":3,"office":1,"schools":8,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":4}),
     "expected_present":["直接竞品"],"expected_absent":["学生客群稳定","市场空白明显","推荐开店"]},

    # 12 entertainment: 夜间交通弱; 居民区扰民合规风险
    {"case_id":"entertainment_04","expected_model_id": "entertainment", "model_id": "entertainment","business_type":"KTV","brand_name":"","store_size":400,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=0,stats_500m={"residential":18,"office":0,"schools":1,"subway":0,"bus":1,"parking":1,"shopping":0,"hotels":0,"restaurants":3}),
     "expected_present":["消防","隔音"],"expected_absent":["市场空白明显","先发优势","推荐开店"]},
    {"case_id":"entertainment_05","expected_model_id": "entertainment", "model_id": "entertainment","business_type":"酒吧","brand_name":"","store_size":200,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=0,direct_competitors_1000m=1,stats_500m={"residential":8,"office":1,"schools":0,"subway":0,"bus":2,"parking":1,"shopping":0,"hotels":0,"restaurants":8}),
     "expected_present":["直接竞品","居民"],"expected_absent":["市场空白明显","品类切入空间较好","推荐开店"]},

    # ── Phase 4N: 公交去重 ──
    # bus raw=8 但同名站上下行重复去重后~2-3站，住宅弱，不得写公交网络较密
    {"case_id":"snack_fast_food_08_busdedup","expected_model_id": "snack_fast_food", "model_id": "snack_fast_food","business_type":"小吃快餐","brand_name":"","store_size":40,
     "real_data":_make_rd(direct_competitors_200m=0,direct_competitors_500m=1,direct_competitors_1000m=3,stats_500m={"residential":3,"office":1,"schools":2,"subway":0,"bus":8,"parking":1,"shopping":0,"hotels":0,"restaurants":6},poi_lists={"bus_stops":[{"name":"宝鸡文理学院(上行)"},{"name":"宝鸡文理学院(下行)"},{"name":"宝鸡文理学院站牌东"},{"name":"宝鸡文理学院站牌西"},{"name":"宝鸡文理学院东侧"},{"name":"高新管委会"},{"name":"高新管委会(上行)"},{"name":"高新管委会(下行)"}]}),
     "expected_present":["直接竞品"],"expected_absent":["公交网络较密","交通优势明显","客流导入强"]},
]


def _check_sample(s):
    rd = s["real_data"]
    bt, bn, sz = s["business_type"], s["brand_name"], s["store_size"]
    cat = s.get("category", "")
    mid = s["expected_model_id"]

    family = classify_business_model_family(bt, bn, cat)
    assert family == mid, f"{s['case_id']}: classify={family}, expected={mid}"

    lp = compute_location_profile(rd)
    assert lp["primary_type"], f"{s['case_id']}: location_profile empty"

    snap = compute_business_model_snapshot(rd, bt, bn, sz, category=cat)
    assert snap["model_type"] == mid, f"{s['case_id']}: snapshot={snap['model_type']}"

    model_yaml = load_business_model(mid)
    assert model_yaml, f"{s['case_id']}: YAML not loaded for {mid}"

    fb = build_fallback_report(rd, address="test", business_type=bt, brand_name=bn, store_size=sz, category=cat)
    enriched = enrich_report_business_context(fb, rd, business_type=bt, brand_name=bn, category=cat, store_size=sz, is_fallback=True)

    required = ["location_profile","location_fundamentals","business_model_snapshot",
                "business_model_version","revenue_disclaimer","field_checklist",
                "caliber_explanation","evidence_summary","data_boundary"]
    for k in required:
        assert k in enriched and enriched[k], f"{s['case_id']}: enriched missing {k}"

    enriched["business_type"] = bt
    enriched["generated_at"] = "2026-06-15 10:00"
    html = _build_report_html(1, enriched, "addr", bn)
    for marker in ["选址决策参考","保守版数据摘要","地点基本面","现场核验清单"]:
        assert marker in html, f"{s['case_id']}: HTML missing {marker}"

    # ── 硬化扫描：JSON + HTML 双文本 ──
    report_text = json.dumps(enriched, ensure_ascii=False)
    both_texts = report_text + " " + html

    for phrase in s.get("expected_present", []):
        assert phrase in both_texts, f"{s['case_id']}: missing expected '{phrase}'"

    for phrase in s.get("expected_absent", []):
        assert phrase not in both_texts, f"{s['case_id']}: found banned '{phrase}'"

    return True


def test_all_samples():
    for s in SAMPLES:
        _check_sample(s)
    print(f"SAMPLE_REGRESSION: {len(SAMPLES)} samples ALL PASS")


EXPECTED_MODEL_IDS = {
    "snack_fast_food","food_service","beverage_dessert","retail_convenience",
    "pharmacy","retail_shopping","education_childcare","education_training",
    "service_basic","service_beauty","hotel","entertainment",
}


def test_meta():
    """元测试：防假绿。"""
    from collections import Counter

    for s in SAMPLES:
        assert "expected_model_id" in s, f"{s['case_id']}: missing expected_model_id"
        assert "model_id" in s, f"{s['case_id']}: missing model_id"
        assert s["expected_model_id"] == s["model_id"], f"{s['case_id']}: expected_model_id != model_id"
        ep = s.get("expected_present", [])
        ea = s.get("expected_absent", [])
        assert isinstance(ep, list) and len(ep) > 0, f"{s['case_id']}: expected_present empty"
        assert isinstance(ea, list) and len(ea) > 0, f"{s['case_id']}: expected_absent empty"

    counts = Counter(s["expected_model_id"] for s in SAMPLES)
    assert set(counts.keys()) == EXPECTED_MODEL_IDS, (
        f"model_ids mismatch: got {sorted(counts.keys())}, expected {sorted(EXPECTED_MODEL_IDS)}"
    )
    for mid in EXPECTED_MODEL_IDS:
        assert counts[mid] >= 5, f"model_id '{mid}' only has {counts[mid]} samples (need >=5)"

    ids = [s["case_id"] for s in SAMPLES]
    assert len(ids) == len(set(ids)), f"duplicate case_ids: {[i for i,n in Counter(ids).items() if n>1]}"

    print(f"META: {len(SAMPLES)} samples, 12 models x>=5, all case_ids unique PASS")


if __name__ == "__main__":
    test_all_samples()
    test_meta()
