"""POI 名称识别与分类规则纯函数模块。"""
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
HOSPITAL_DENY = [
    "诊所", "牙科", "牙医", "牙博士", "口腔", "齿科", "牙科医院", "口腔医院",
    "药店", "药房", "医务室",
    "视光", "眼科", "眼科医院", "助听器", "医美", "皮肤", "疤痕", "理疗",
    "康复医院", "养老", "护理院", "月子", "产后",
]
# ★ 强排除：即使名称含"人民医院/中医院"也直接拒绝的非医疗机构
HOSPITAL_STRONG_DENY = [
    "体检中心", "体检科", "体检",
    "整形美容", "整形", "美容中心", "美容", "美容医院",
    "康复中心", "视光", "眼科", "助听器", "皮肤", "疤痕", "理疗",
]
# 院内部门/楼栋后缀→归并到主院，不单独计为一家医院
HOSPITAL_DEPT_SUFFIX = [
    "住院部","创伤中心","卒中中心","胸痛中心","急诊急救","急诊科","急救站",
    "内儿","医技","综合楼","门诊部","发热门诊","感染科",
    "检验科","放射科","超声科","病理科",
    "行政楼","后勤楼","教学楼","科研楼","学术报告厅",
]

def _hospital_base(name: str) -> str:
    """提取医院主名：去除院内部门/楼栋后缀，同一医院归并为一个主体"""
    for suffix in HOSPITAL_DEPT_SUFFIX:
        name = name.replace(suffix, "")
    # 去除末尾的"号楼/楼/栋"等
    name = re.sub(r'[（(][^)）]*[)）]$', '', name)
    name = re.sub(r'\d+号楼?$', '', name)
    name = re.sub(r'[东西南北]院区?$', '', name)
    return name.strip()

def _is_hospital_main_name(name: str) -> bool:
    """判断是否为医院主名称（而非院内部门）"""
    MAIN_MARKERS = ["人民医院", "中医院", "妇幼保健院", "社区卫生服务中心", "卫生院", "急救中心"]
    DEPT_MARKERS = ["住院部", "创伤中心", "卒中中心", "胸痛中心", "急诊急救", "急诊科", "急救站", "综合楼", "门诊部", "发热门诊"]
    # 急救中心是独立机构，优先识别为主
    if "急救中心" in name:
        return True
    if any(m in name for m in DEPT_MARKERS):
        return False
    if any(m in name for m in MAIN_MARKERS):
        return True
    return not any(s in name for s in HOSPITAL_DEPT_SUFFIX)

def is_real_hospital(name: str) -> bool:
    """名称正向筛选：仅真正的医院通过。
    1. HOSPITAL_STRONG_DENY 优先——体检/整形/美容等即使含"人民医院"也拒绝
    2. 主医院标记（人民医院/中医院等）放行，部门名（门诊部/发热门诊等）允许进入归并
    3. HOSPITAL_DENY 排除普通门诊/口腔/牙科等
    4. HOSPITAL_ALLOW 放行医院关键词"""
    MAIN_MARKERS = ["人民医院", "中医院", "妇幼保健院", "社区卫生服务中心", "卫生院", "急救中心"]
    # 强排除优先级最高：体检中心/整形美容等不属于医院主体
    for kw in HOSPITAL_STRONG_DENY:
        if kw in name:
            return False
    # 主医院标记放行（包括含门诊部/发热门诊等院内部门）
    if any(m in name for m in MAIN_MARKERS):
        return True
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

# 便利店脱水：仅保留真正的便利店/超市/社区刚需
CONVENIENCE_KEEP = ["便利店", "超市", "小卖部", "生鲜", "蔬果", "水果", "烟酒", "百货店", "百货商店", "日用百货", "百货商行", "百货铺", "百货行", "杂货", "便利", "副食", "日杂", "蔬菜", "肉", "粮油"]
CONVENIENCE_DROP = [
    "废品", "回收", "养生", "足疗", "足道", "彩票", "中介", "广告", "装饰", "装修",
    "房产", "地产", "充电站", "充电桩", "售票", "旅行社", "劳务", "人力", "家政",
    "搬家", "开锁", "疏通", "驾校", "文印", "照相", "刻章", "缝纫", "修理", "修鞋",
    "配钥匙", "干洗", "皮具护理", "擦鞋", "美发", "理发", "美容", "美甲", "纹身",
    "按摩", "采耳", "洗浴", "汗蒸", "推拿", "艾灸", "拔罐", "眼镜",
    # ★ 新增排除
    "手机维修", "手机快修", "黄金加工", "黄金回收", "体验店", "体验中心",
    "沙龙", "美睫", "美瞳", "美肤", "美体", "减肥", "瘦身",
    "彩票", "福彩", "体彩", "体育彩票",
    "OPPO", "vivo", "华为", "小米", "Apple", "苹果", "三星",
]

def is_real_convenience(name: str) -> bool:
    for kw in CONVENIENCE_DROP:
        if kw in name:
            return False
    for kw in CONVENIENCE_KEEP:
        if kw in name:
            return True
    return False

# 药店脱水：仅保留真正的药店
PHARMACY_KEEP = ["药店", "药房", "医药", "大药房", "药行", "国药", "同仁堂", "老百姓", "益丰", "一心堂", "健之佳", "海王星辰", "大参林"]
PHARMACY_DROP = [
    "器械", "体验中心", "门诊", "诊所", "医院", "卫生院", "体检", "整形", "美容",
    "保健体验", "理疗", "养生馆", "养生堂", "生活馆",
    # ★ 新增排除
    "眼科", "视光", "助听器", "飞利浦", "听力",
    "皮肤", "疤痕", "修护", "医美", "轻医美", "植发",
    "康复", "产后", "月子", "心理咨询", "心理诊所",
    "牙科", "口腔", "齿科", "镶牙",
]

def is_real_pharmacy(name: str) -> bool:
    for kw in PHARMACY_DROP:
        if kw in name:
            return False
    for kw in PHARMACY_KEEP:
        if kw in name:
            return True
    return False

# 教育培训脱水：仅保留培训机构，排除学校/幼儿园/文具/书店
TRAINING_KEEP = ["培训", "教育", "琴行", "画室", "早教", "托管", "辅导", "补习", "驾校", "职业技能", "美术", "音乐", "舞蹈"]
TRAINING_DROP = ["小学", "中学", "高中", "大学", "学院", "幼儿园", "学校", "文具", "书店", "办公用品", "教育局", "政府"]

def is_real_training(name: str) -> bool:
    for kw in TRAINING_DROP:
        if kw in name:
            return False
    for kw in TRAINING_KEEP:
        if kw in name:
            return True
    return False

# 洗衣店脱水
LAUNDRY_KEEP = ["洗衣", "干洗", "洗护", "清洗", "护理"]
LAUNDRY_DROP = ["家政", "维修", "皮具", "擦鞋", "开锁", "疏通", "搬家", "培训", "教育", "宠物"]

def is_real_laundry(name: str) -> bool:
    for kw in LAUNDRY_DROP:
        if kw in name:
            return False
    for kw in LAUNDRY_KEEP:
        if kw in name:
            return True
    return False

# 诊所脱水：仅保留真正诊所，排除医院/牙科/眼科/体检/药店
CLINIC_KEEP = ["诊所", "卫生所", "卫生室", "医务室", "社区卫生", "门诊部", "门诊", "中医", "中西医"]
CLINIC_DROP = ["医院", "口腔", "牙科", "眼科", "视光", "体检", "医美", "整形", "助听器", "药店", "大药房", "康复", "月子"]

def is_real_clinic(name: str) -> bool:
    for kw in CLINIC_DROP:
        if kw in name:
            return False
    for kw in CLINIC_KEEP:
        if kw in name:
            return True
    return False

# 健身房脱水
FITNESS_KEEP = ["健身", "瑜伽", "普拉提", "私教", "游泳", "拳击", "体能", "CrossFit", "操课", "力量"]
FITNESS_DROP = ["体育用品", "体育器材", "足疗", "按摩", "推拿", "舞蹈培训", "少儿", "儿童", "宠物", "美容", "美发"]

def is_real_fitness(name: str) -> bool:
    for kw in FITNESS_DROP:
        if kw in name:
            return False
    for kw in FITNESS_KEEP:
        if kw in name:
            return True
    return False

# 生鲜零售脱水
FRESH_RETAIL_KEEP = ["生鲜", "水果", "蔬菜", "果蔬", "鲜果", "菜店", "菜场", "菜市场", "鲜肉", "果品"]
FRESH_RETAIL_DROP = ["百货", "便利店", "药店", "药房", "餐饮", "饭店", "冷库", "物流", "批发", "五金", "建材", "超市"]

def is_real_fresh_retail(name: str) -> bool:
    # KEEP 优先：生鲜超市/水果超市 等含"生鲜/水果"的复合名不应被"超市"误杀
    has_keep = any(kw in name for kw in FRESH_RETAIL_KEEP)
    if has_keep:
        return True
    for kw in FRESH_RETAIL_DROP:
        if kw in name:
            return False
    return False

# 烟酒零售脱水
TOBACCO_LIQUOR_KEEP = ["烟酒", "名烟", "名酒", "酒水", "酒行", "酒庄", "酒类", "烟草", "1919", "酒便利"]
TOBACCO_LIQUOR_DROP = ["酒吧", "KTV", "餐厅", "饭店", "超市", "便利店", "茶叶", "茶庄", "百货"]

def is_real_tobacco_liquor_retail(name: str) -> bool:
    for kw in TOBACCO_LIQUOR_DROP:
        if kw in name:
            return False
    for kw in TOBACCO_LIQUOR_KEEP:
        if kw in name:
            return True
    return False

# 沉浸式娱乐脱水：剧本杀/密室/台球/桌游/电玩，排除 KTV/酒吧/网吧/麻将馆/健身
IMMERSIVE_KEEP = ["剧本杀","推理馆","谋杀之谜","密室逃脱","密室","沉浸式","台球","桌球","桌游","棋牌室","轰趴","电玩","VR","虚拟现实","游戏厅","娱乐体验","主机游戏","实景搜证","狼人杀","三国杀","德扑","机械密室","恐怖密室","台球厅","桌球室"]
# 强排除：混名 POI（如 KTV剧本杀/酒吧密室/电竞酒店剧本杀）必须先被拒绝
IMMERSIVE_STRONG_DENY = ["KTV","酒吧","清吧","网吧","网咖","电竞酒店","健身","瑜伽","足疗","洗浴","按摩","麻将馆","麻将","茶楼","茶社","咖啡","餐厅","火锅","烧烤"]

def is_real_immersive_entertainment(name: str) -> bool:
    # 强排除优先：混名 POI（KTV剧本杀/酒吧密室等）直接拒绝
    for kw in IMMERSIVE_STRONG_DENY:
        if kw in name:
            return False
    for kw in IMMERSIVE_KEEP:
        if kw in name:
            return True
    return False

# 写字楼脱水
OFFICE_KEEP = [
    "办公楼", "写字楼", "大厦", "商务中心", "国际中心", "企业中心",
    "科创中心", "科技园", "产业园", "创业园", "总部基地", "商务楼", "商办楼",
]
OFFICE_DROP = [
    "公司", "厂房", "工业园", "制造", "仓库", "物流", "公寓",
    "有限公司", "有限责任公司", "事务所", "工作室", "培训",
]

def is_real_office(name: str) -> bool:
    for kw in OFFICE_DROP:
        if kw in name:
            return False
    for kw in OFFICE_KEEP:
        if kw in name:
            return True
    return False

# 购物商场脱水
SHOPPING_KEEP = [
    "购物中心", "百货商场", "百货大楼", "商场", "商城", "商业广场",
    "购物广场", "万达广场", "吾悦广场", "银泰城", "奥特莱斯", "奥莱",
    "商业街", "步行街", "购物公园", "MALL",
    # 新增品牌购物中心
    "万象城", "万象汇", "龙湖天街", "大悦城", "印象城", "宝龙广场",
    "生活广场", "商业中心", "商贸中心",
]
SHOPPING_DROP = [
    "建材", "批发", "农贸", "汽配", "五金", "家具", "灯饰", "石材", "印刷", "旧货", "二手",
    "便利店", "超市", "专卖店", "服装店", "鞋店", "数码店", "药店", "烟酒店",
    "水果店", "生鲜店", "母婴店", "维修店", "文具店", "眼镜店",
    "小卖部", "服务中心", "单体零售",
]

# 市场/专业市场参考层 — 不计入购物商场，但在数据解释中体现
MARKET_ANCHOR_KEYWORDS = [
    "农贸市场", "菜市场", "批发市场", "建材市场", "五金市场",
    "家居市场", "汽配城", "商贸城", "水产市场", "花卉市场",
    "果蔬市场", "粮油市场", "茶叶市场", "布料市场", "皮革市场",
    "电子市场", "数码广场", "电脑城",
]

def is_real_shopping(name: str) -> bool:
    for kw in SHOPPING_DROP:
        if kw in name:
            return False
    for kw in SHOPPING_KEEP:
        if kw in name:
            return True
    return False

def is_market_anchor(name: str) -> bool:
    """判断 POI 是否为市场/专业市场类型"""
    for kw in MARKET_ANCHOR_KEYWORDS:
        if kw in name:
            return True
    return False

# 公交站名称去重：去除方向尾缀
def _normalize_bus_stop_name(name: str) -> str:
    """标准化公交站名：去除上行/下行/方向尾缀，合并同一站点的多方向"""
    name = re.sub(r'[（(][^)）]*[)）]$', '', name)
    # 去除方向/方位尾缀
    name = re.sub(r'[-\s]*(上行|下行|内环|外环|东行|西行|南行|北行|东南|东北|西南|西北|往东|往西|往南|往北|[东西南北]站牌|站牌[东西南北]?|东侧|南侧|西侧|北侧|主站|辅站|[东西南北](?:侧|区|口|方向|行)?|内|外)$', '', name)
    name = name.strip()
    return name

# 低频目的零售脱水（服装/数码/眼镜/品牌零售，不污染 shopping 大类）
LOW_FREQ_RETAIL_KEEP = [
    "服装", "鞋帽", "数码", "手机", "电脑", "家电", "眼镜", "珠宝",
    "屈臣氏", "优衣库", "名创优品",
]
LOW_FREQ_RETAIL_DROP = [
    "维修", "彩票", "快递", "手机维修", "黄金回收",
    "批发", "建材", "五金", "农贸", "汽配",
    "超市", "便利店", "水果", "生鲜", "菜市场", "杂货",
]

def is_real_low_freq_retail(name: str) -> bool:
    for kw in LOW_FREQ_RETAIL_DROP:
        if kw in name:
            return False
    for kw in LOW_FREQ_RETAIL_KEEP:
        if kw in name:
            return True
    return False

# 住宅小区脱水
RESIDENTIAL_KEEP = ["小区", "社区", "家属院", "家属楼", "住宅", "居民楼", "公寓", "新村", "花园", "家园", "苑", "庭", "邸"]
RESIDENTIAL_DROP = [
    "售楼", "中介", "销售中心", "营销中心", "展厅",
    "产业园", "工业园", "科技园", "创业园", "物流园",
    "大厦", "银座", "办公楼", "商业楼", "商务楼", "写字楼",
    "医药", "电商", "数码", "电子", "科技",
    "厂房", "仓库", "酒店", "宾馆", "医院", "学校",
    # ★ 新增
    "法院", "检察院", "研究院", "设计院", "养老院", "福利院",
    "美容院", "学院", "书院", "科学院", "画院",
]

def is_real_residential(name: str) -> bool:
    for kw in RESIDENTIAL_DROP:
        if kw in name:
            return False
    for kw in RESIDENTIAL_KEEP:
        if kw in name:
            return True
    return False

# 酒店住宿脱水
HOTEL_DROP = ["招待所", "农家乐", "农庄", "洗浴", "日租房", "钟点房"]

def is_real_hotel(name: str) -> bool:
    for kw in HOTEL_DROP:
        if kw in name:
            return False
    return True

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
    ("购物服务;药店", "pharmacy"),
    ("购物服务", "shopping"),
    # === 生活服务 → 拆分：美容美体/便利店/删除无关 ===
    ("生活服务;美容美发", "beauty"),
    ("生活服务;宠物服务", "pets"),
    ("生活服务;洗衣店", "laundry"),
    # 售票处/旅行社/裸生活服务 太泛 → 不展示
    # === 商务住宅 ===
    ("商务住宅;住宅区", "residential"),
    ("商务住宅;商务写字楼", "office"),
    ("商务住宅;商住两用", "office"),
    ("商务住宅", "residential"),
    # === 医疗保健服务 → 医院/药店分离 ===
    ("医疗保健服务;综合医院", "hospitals"),
    ("医疗保健服务;专科医院", "hospitals"),
    ("医疗保健服务;诊所", "clinics"),
    ("医疗保健服务;医药保健销售店", "pharmacy"),
    ("医疗保健服务;药房", "pharmacy"),
    # 动物医疗/裸医疗保健 太泛 → 不展示
    # === 住宿服务 ===
    ("住宿服务", "hotels"),
    # === 交通设施服务 ===
    ("交通设施服务;地铁站", "subway"),
    ("交通设施服务;公交站", "bus"),
    ("交通设施服务;停车场", "parking"),
    ("交通设施服务;长途客运站", "bus"),
    # 裸交通设施 太泛(含机场/火车站) → 不展示
    # === 科教文化服务 → 仅保留学校 ===
    ("科教文化服务;学校", "schools"),
    ("科教文化服务;培训机构", "education_training"),
    # 裸科教文化 太泛 → 不展示
    # === 金融保险服务 ===
    ("金融保险服务", "banks"),
    # === 体育休闲服务 → 仅保留夜经济 ===
    ("体育休闲服务;KTV", "bars"),
    ("体育休闲服务;酒吧", "bars"),
    ("体育休闲服务;网吧", "bars"),
    ("体育休闲服务;运动场馆", "fitness"),
    ("体育休闲服务;娱乐场所", "immersive_entertainment"),
    # 裸体育休闲 太泛 → 不展示
    # === 公司企业 ===
    ("公司企业", "office"),
    # 风景名胜/政府机构 不展示
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
    # 070000 生活服务大类 → 不展示
    # 080000 体育休闲大类 → 不展示
    ("090100", "hospitals"),
    ("090200", "hospitals"),
    ("090300", "clinics"),
    ("090400", "pharmacy"),
    ("090500", "hospitals"),
    ("090000", "hospitals"),
    ("100000", "hotels"),
    ("110000", "residential"),
    ("120300", "residential"),
    ("120200", "office"),
    ("120000", "residential"),
    ("130000", "office"),
    ("141200", "education_training"),
    # 140000 科教大类 → 不展示
    ("150500", "subway"),
    ("150200", "bus"),
    ("150900", "parking"),
    # 150000 交通大类 → 不展示
    ("160100", "banks"),
    ("160000", "banks"),
    # 170000 政府机构 → 不展示
]

# 用于前端/后端统一key名
ALL_CATEGORY_KEYS = [
    "restaurants", "chinese_restaurants", "foreign_restaurants",
    "fast_food", "cafe_tea", "bars",
    "shopping", "market_anchor", "convenience",
    "residential", "office", "schools", "hotels",
    "subway", "bus", "parking", "hospitals", "pharmacy", "banks",
    "beauty", "pets",
    "education_training", "laundry", "clinics",
    "fitness", "fresh_retail", "tobacco_liquor",
    "low_freq_retail",
    "immersive_entertainment",
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
    "pharmacy": "药店",
    "banks": "银行",
    "beauty": "美容美体",
    "pets": "宠物服务",
    "education_training": "教育培训",
    "laundry": "洗衣店",
    "clinics": "诊所",
    "fitness": "健身房",
    "fresh_retail": "生鲜零售",
    "tobacco_liquor": "烟酒零售",
    "low_freq_retail": "低频目的零售",
    "immersive_entertainment": "沉浸式娱乐",
    "market_anchor": "市场/专业市场",
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


def _match_name(name: str, keywords: list) -> bool:
    """名称关键词匹配"""
    if not name or not keywords:
        return False
    for kw in keywords:
        if kw in name:
            return True
    return False

def classify_poi_rigor(name: str, cat: str, type_code: str, rigor: dict, business_type: str = "", brand_name: str = "") -> str:
    """
    根据业态严谨度规则，将已分类POI进一步标记为：
    'direct' / 'substitute' / 'anchor' / 'irrelevant' / 'pass'
    支持 name_keywords、categories、amap_codes 三维匹配
    支持 subtypes 子业态独立规则（复合集群内不同业态互相不污染）
    支持 brand_name 品牌感知：当品牌含特定关键词时，收紧 direct 口径
    """
    if not rigor or not name:
        return "pass"
    rules = rigor

    def _match_code(code_list, tc):
        if not code_list or not tc:
            return False
        for code in code_list:
            if tc.startswith(code):
                return True
        return False

    # ★ 品牌感知：擀面皮/面皮类品牌 → 收紧 direct 只匹配同类面皮，米线/砂锅/水饺等降为 substitute
    _brand_is_noodle_skin = False
    if brand_name:
        for kw in ["擀面皮", "面皮", "凉皮", "米皮", "烙面皮"]:
            if kw in brand_name:
                _brand_is_noodle_skin = True
                break

    # ★ 子业态精准规则：命中第一个 subtype 后稳定锁定。
    # ★ 继承 master 级字段（bool/排除词），subtype 显式覆盖优先
    master_dc = rules.get("direct_competitor_rules", {})
    dc = master_dc  # 默认使用 master
    subtypes = master_dc.get("subtypes", {})
    selected_subtype = None
    if subtypes and business_type:
        for sub_key, sub_rules in subtypes.items():
            matched = False
            for kw in sub_rules.get("match_keywords", []):
                if kw in business_type:
                    selected_subtype = sub_key
                    # 合并：master 级 bool + 排除词继承，subtype name_keywords/amap_codes 优先
                    dc = {
                        "require_name_keyword_for_code": sub_rules.get("require_name_keyword_for_code", master_dc.get("require_name_keyword_for_code", False)),
                        "substitute_before_direct": sub_rules.get("substitute_before_direct", master_dc.get("substitute_before_direct", False)),
                        "strict_exclude_names": list(set(master_dc.get("strict_exclude_names", []) + sub_rules.get("strict_exclude_names", []))),
                        "exclude_names": list(set(master_dc.get("exclude_names", []) + sub_rules.get("exclude_names", []))),
                        "name_keywords": sub_rules.get("name_keywords", []),
                        "amap_codes": sub_rules.get("amap_codes", master_dc.get("amap_codes", [])),
                        "substitute_keywords": sub_rules.get("substitute_keywords", []),
                    }
                    matched = True
                    break
            if matched:
                break

    # ★ 品牌感知：擀面皮品牌 → 收紧 direct 关键词 只留面皮同类
    if _brand_is_noodle_skin:
        # 面皮同类：擀面皮/面皮/凉皮/米皮/烙面皮/热米皮
        _skin_kw = ["擀面皮", "面皮", "凉皮", "米皮", "烙面皮", "热米皮"]
        dc = dict(dc)  # 不污染 master
        dc["name_keywords"] = _skin_kw
        dc["substitute_keywords"] = [
            "米线", "砂锅", "水饺", "饺子", "馄饨", "拉面", "拌面", "刀削面",
            "泡馍", "水盆", "麻辣烫", "麻辣拌", "冒菜", "酸辣粉", "螺蛳粉",
            "热干面", "煎饼", "肉夹馍", "锅贴", "生煎", "小笼", "汤面",
            "干拌", "臊子面", "油泼面", "蘸水面", "饸饹", "biangbiang",
            "快餐", "便当", "盖浇",
        ]

    # 1. 检查 irrelevant —— 明确无关项
    irr = rules.get("irrelevant_poi_rules", {})
    if _match_name(name, irr.get("name_blacklist", [])):
        return "irrelevant"
    if cat in irr.get("categories_excluded", []):
        return "irrelevant"

    # 2. 检查 substitute（如果配置了 substitute_before_direct，优先于 direct code）
    sub = rules.get("substitute_competitor_rules", {})
    sub_first = dc.get("substitute_before_direct", False)
    if sub_first:
        # brand-aware substitute_keywords（优先于 master 级），再 master 级
        sub_kw = dc.get("substitute_keywords", [])
        if sub_kw and _match_name(name, sub_kw):
            return "substitute"
        if _match_name(name, sub.get("name_keywords", [])):
            return "substitute"
        if _match_code(sub.get("amap_codes", []), type_code):
            return "substitute"
        if cat in sub.get("categories", []):
            return "substitute"

    # 3. 检查 direct_competitor
    dc_kw = dc.get("name_keywords", [])
    dc_ex = dc.get("exclude_names", [])
    dc_strict_ex = dc.get("strict_exclude_names", [])
    dc_codes = dc.get("amap_codes", [])
    dc_require_kw = dc.get("require_name_keyword_for_code", False)
    if _match_name(name, dc_strict_ex):
        return "irrelevant"
    if _match_code(dc_codes, type_code):
        # 命中 AMap type_code
        if dc_require_kw:
            # ★ 配置要求：code 命中后必须同时命中关键词，且不能命中排除词
            if _match_name(name, dc_kw) and not _match_name(name, dc_ex):
                return "direct"
            # 否则 fall through
        else:
            # 默认：code 命中即可 direct（仅需不命中排除词）
            if not _match_name(name, dc_ex):
                return "direct"
    if _match_name(name, dc_ex):
        pass
    elif _match_name(name, dc_kw):
        return "direct"

    # 4. 检查 substitute（如已通过 sub_first 检查则跳过）
    if not sub_first:
        sub_kw2 = dc.get("substitute_keywords", [])
        if sub_kw2 and _match_name(name, sub_kw2):
            return "substitute"
        if _match_name(name, sub.get("name_keywords", [])):
            return "substitute"
        if _match_code(sub.get("amap_codes", []), type_code):
            return "substitute"
        if cat in sub.get("categories", []):
            return "substitute"

    # 4. 检查 traffic_anchor
    anc = rules.get("traffic_anchor_rules", {})
    if _match_name(name, anc.get("name_keywords", [])):
        return "anchor"
    if _match_code(anc.get("amap_codes", []), type_code):
        return "anchor"
    if cat in anc.get("categories", []):
        return "anchor"

    return "pass"

def classify_poi_type(type_code: str) -> str | None:
    """根据高德POI type字段分类到我们的类别（支持中文名和数字码）。
    注意：高德返回的 type 字段格式可能是 '交通设施服务;公交车站' 或 '交通设施服务;公交车站;公交车站相关'，
    而 TYPE_CLASSIFIERS 仅收录了 '交通设施服务;公交站'，因此额外用关键词兜底。
    """
    if not type_code:
        return None
    # 处理 | 分隔的多分类（如：餐饮|购物）
    parts = type_code.split("|") if "|" in type_code else [type_code]
    for part in parts:
        part = part.strip()
        for prefix, category in TYPE_CLASSIFIERS:
            if part.startswith(prefix):
                return category
        # ★ 公交关键词兜底：高德可能返回 "公交车站" 而非 "公交站"
        if "公交" in part and "站" in part and "地铁" not in part and "火车站" not in part and "停车场" not in part and "机场" not in part and "长途" not in part:
            return "bus"
    return None
