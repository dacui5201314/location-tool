/**
 * 高德地图 JS API 2.0 POI 数据采集服务
 * 使用已加载的 AMap JS API 进行一次搜索 + 前端分类，速度快
 */

// 高德API返回中文type字段（大类;中类;小类），按前缀匹配分类
// 同时也兼容数字代码（旧版API）
const TYPE_CLASSIFIERS = [
  // === 餐饮服务 ===
  ['餐饮服务;中餐厅', 'chinese_restaurants'],
  ['餐饮服务;清真菜馆', 'chinese_restaurants'],
  ['餐饮服务;综合酒楼', 'chinese_restaurants'],
  ['餐饮服务;外国餐厅', 'foreign_restaurants'],
  ['餐饮服务;快餐厅', 'fast_food'],
  ['餐饮服务;小吃店', 'fast_food'],
  ['餐饮服务;冷饮店', 'cafe_tea'],
  ['餐饮服务;甜品店', 'cafe_tea'],
  ['餐饮服务;糕饼店', 'cafe_tea'],
  ['餐饮服务;咖啡厅', 'cafe_tea'],
  ['餐饮服务;茶艺馆', 'cafe_tea'],
  ['餐饮服务;酒吧', 'bars'],
  ['餐饮服务', 'restaurants'],
  // === 购物服务 ===
  ['购物服务;购物中心', 'shopping'],
  ['购物服务;百货商场', 'shopping'],
  ['购物服务;便利店', 'convenience'],
  ['购物服务;超市', 'convenience'],
  ['购物服务;服装鞋帽店', 'shopping'],
  ['购物服务;数码电子', 'shopping'],
  ['购物服务;药店', 'pharmacy'],
  ['购物服务', 'shopping'],
  // === 生活服务 ===
  ['生活服务;售票处', 'convenience'],
  ['生活服务;旅行社', 'convenience'],
  ['生活服务;美容美发', 'convenience'],
  ['生活服务;洗衣店', 'convenience'],
  ['生活服务;宠物服务', 'convenience'],
  ['生活服务', 'convenience'],
  // === 商务住宅 ===
  ['商务住宅;住宅区', 'residential'],
  ['商务住宅;商务写字楼', 'office'],
  ['商务住宅;商住两用', 'office'],
  ['商务住宅', 'residential'],
  // === 医疗保健服务 ===
  ['医疗保健服务;综合医院', 'hospitals'],
  ['医疗保健服务;专科医院', 'hospitals'],
  ['医疗保健服务;诊所', 'pharmacy'],
  ['医疗保健服务;医药保健销售店', 'pharmacy'],
  ['医疗保健服务;药房', 'pharmacy'],
  ['医疗保健服务;动物医疗', 'pharmacy'],
  ['医疗保健服务', 'pharmacy'],
  // === 住宿服务 ===
  ['住宿服务', 'hotels'],
  // === 交通设施服务 ===
  ['交通设施服务;地铁站', 'subway'],
  ['交通设施服务;公交站', 'bus'],
  ['交通设施服务;停车场', 'parking'],
  ['交通设施服务;长途客运站', 'bus'],
  ['交通设施服务', 'bus'],
  // === 科教文化服务 ===
  ['科教文化服务;学校', 'schools'],
  ['科教文化服务;培训机构', 'schools'],
  ['科教文化服务', 'schools'],
  // === 金融保险服务 ===
  ['金融保险服务', 'banks'],
  // === 体育休闲服务 ===
  ['体育休闲服务;运动场馆', 'bars'],
  ['体育休闲服务;KTV', 'bars'],
  ['体育休闲服务;酒吧', 'bars'],
  ['体育休闲服务;网吧', 'bars'],
  ['体育休闲服务', 'bars'],
  // === 风景名胜 ===
  ['风景名胜;公园', 'residential'],
  ['风景名胜;风景名胜', 'residential'],
  ['风景名胜', 'residential'],
  // === 政府机构 ===
  ['政府机构及社会团体', 'office'],
  // === 公司企业 ===
  ['公司企业', 'office'],
  // === 数字代码兜底 ===
  ['050100', 'chinese_restaurants'],
  ['050200', 'chinese_restaurants'],
  ['050300', 'fast_food'],
  ['050400', 'bars'],
  ['050500', 'cafe_tea'],
  ['050600', 'cafe_tea'],
  ['050000', 'restaurants'],
  ['060100', 'shopping'],
  ['060200', 'convenience'],
  ['060300', 'convenience'],
  ['060400', 'shopping'],
  ['060000', 'shopping'],
  ['070000', 'convenience'],
  ['080000', 'bars'],
  ['090100', 'hospitals'],
  ['090200', 'hospitals'],
  ['090300', 'hospitals'],
  ['090400', 'hospitals'],
  ['090500', 'hospitals'],
  ['090000', 'hospitals'],
  ['100000', 'hotels'],
  ['110000', 'residential'],
  ['120300', 'residential'],
  ['120200', 'office'],
  ['120000', 'residential'],
  ['130000', 'office'],
  ['141200', 'schools'],
  ['140000', 'schools'],
  ['150500', 'subway'],
  ['150200', 'bus'],
  ['150900', 'parking'],
  ['150000', 'bus'],
  ['160100', 'banks'],
  ['160000', 'banks'],
  ['170000', 'office'],
]

// 聚合类别（用于初始化计数器）
const AGGREGATED_CATEGORIES = {
  restaurants: 1, chinese_restaurants: 1, foreign_restaurants: 1,
  fast_food: 1, cafe_tea: 1, bars: 1,
  shopping: 1, convenience: 1,
  residential: 1, office: 1, schools: 1, hotels: 1,
  subway: 1, bus: 1, parking: 1, hospitals: 1, pharmacy: 1, banks: 1,
}

const CATEGORY_LABELS = {
  restaurants: '餐饮门店',
  chinese_restaurants: '中餐厅',
  fast_food: '快餐厅',
  cafe_tea: '咖啡茶饮',
  shopping: '购物商场',
  convenience: '便利店超市',
  residential: '住宅小区',
  office: '写字楼',
  schools: '学校',
  hotels: '酒店住宿',
  subway: '地铁站',
  bus: '公交站',
  parking: '停车场',
  hospitals: '医院',
  banks: '银行',
}

const KNOWN_BRANDS = [
  '肯德基', '麦当劳', '汉堡王', '必胜客', '海底捞', '西贝',
  '呷哺呷哺', '太二', '喜茶', '奈雪', '瑞幸', '星巴克', '蜜雪冰城',
  '茶百道', '古茗', '霸王茶姬', 'Manner', 'Costa', '达美乐',
  '赛百味', '沙县小吃', '兰州拉面', '黄焖鸡', '杨国福', '张亮麻辣烫',
  '袁记云饺', '巴比馒头', '乡村基', '大米先生', '和府捞面',
  '711', '罗森', '全家', '便利蜂', '美宜佳',
  '沃尔玛', '永辉', '盒马', '大润发', '华润万家', '物美',
  '优衣库', '名创优品', '屈臣氏',
  '汉庭', '如家', '全季', '亚朵', '丽枫', '维也纳',
  '链家', '贝壳', '我爱我家',
]

const COMPETITOR_TYPE_MAP = {
  // 餐饮
  '050000': ['050100', '050200', '050300', '050600', '050400'], // 所有餐饮（含酒吧）
  '050100': ['050100'], // 中餐/火锅/烧烤
  '050200': ['050200'], // 外国餐厅
  '050300': ['050300'], // 快餐/小吃
  '050600': ['050600'], // 甜品/烘焙
  // 茶饮咖啡
  '050500': ['050500'], // 茶饮咖啡/饮品
  // 酒店住宿
  '100000': ['100000'], // 酒店/民宿
  // 零售
  '060000': ['060100', '060200', '060300', '060400'], // 所有零售
  '060200': ['060200'], // 便利店
  '060300': ['060300'], // 超市
  '060100': ['060100'], // 服装
  '060400': ['060400'], // 购物中心/数码/药店
  // 生活服务
  '070000': ['070000'], // 生活服务（美容美发/宠物/洗衣）
  '080000': ['080000', '050400'], // 体育娱乐（含酒吧）
  '141200': ['141200'], // 学校/培训
  '090100': ['090100'], // 医疗/诊所
  // 休闲娱乐
  '050400': ['050400'], // 酒吧
}

function classifyType(typeCode) {
  if (!typeCode) return null
  // 处理 | 分隔的多分类
  const parts = typeCode.includes('|') ? typeCode.split('|') : [typeCode]
  for (const part of parts) {
    const p = part.trim()
    for (const [prefix, category] of TYPE_CLASSIFIERS) {
      if (p.startsWith(prefix)) return category
    }
  }
  return null
}

/**
 * 一次搜索采集所有周边数据（最大450条，覆盖1000米）
 */
function fetchAllNearbyPOIs(lng, lat, radius = 1000) {
  if (!window.AMap || !window.AMap.PlaceSearch) {
    console.error('[amapData] AMap.PlaceSearch 未加载，POI数据采集不可用')
    return Promise.resolve([])
  }

  // 分页获取，最多450条（18页x25）
  const allPois = []
  const fetchPage = (page) => {
    return new Promise((resolve) => {
      const ps = new window.AMap.PlaceSearch({
        pageSize: 25,
        pageIndex: page,
        extensions: 'all',
      })
      ps.searchNearBy('', [lng, lat], radius, (status, result) => {
        if (status === 'complete' && result.info === 'OK') {
          const pois = (result.poiList?.pois || []).filter((p) => {
            return (parseInt(p.distance) || 0) >= 10
          })
          allPois.push(...pois)
          const total = Math.min(result.poiList?.count || 0, 450)
          if (page * 25 < total && page < 18) {
            resolve(fetchPage(page + 1))
          } else {
            resolve(allPois)
          }
        } else {
          resolve(allPois)
        }
      })
    })
  }
  return fetchPage(1)
}

export async function collectLocationData(lng, lat, businessType = '') {
  if (!window.AMap) return null

  // 1. 逆地理编码
  let geoData = {}
  try {
    geoData = await new Promise((resolve) => {
      const geocoder = new window.AMap.Geocoder()
      geocoder.getAddress([lng, lat], (status, result) => {
        if (status === 'complete' && result.info === 'OK') {
          const ac = result.regeocode.addressComponent
          resolve({
            formatted_address: result.regeocode.formattedAddress || '',
            city: ac.city || ac.province || '',
            district: ac.district || '',
            township: ac.township || '',
            neighborhood: (ac.neighborhood && ac.neighborhood.name) || '',
            building_type: (ac.building && ac.building.type) || '',
            business_areas: (result.regeocode.businessAreas || []).map((b) => b.name || ''),
            nearby_roads: (result.regeocode.roadinters || []).slice(0, 5).map((r) => r.name || ''),
          })
        } else {
          resolve({})
        }
      })
    })
  } catch (e) {
    geoData = {}
  }

  // 2. 一次搜索获取所有周边POI
  const allPois = await fetchAllNearbyPOIs(lng, lat, 1000)

  // 3. 归类统计
  const poiCounts = {}
  const poiLists = {}
  const stats200m = {}
  const stats500m = {}
  const stats1000m = {}
  const brands = {}
  let competitors200m = 0
  let competitors500m = 0
  let competitors1000m = 0
  let competitorList = []

  // 初始化统计计数器
  for (const key of Object.keys(AGGREGATED_CATEGORIES)) {
    poiCounts[key] = 0
    poiLists[key] = []
    stats200m[key] = 0
    stats500m[key] = 0
    stats1000m[key] = 0
  }

  // 竞品子类型
  const competitorTypes = businessType ? (COMPETITOR_TYPE_MAP[businessType] || [businessType]) : []

  for (const p of allPois) {
    const dist = parseInt(p.distance) || 0
    const typeCode = p.type || ''
    const cat = classifyType(typeCode)

    if (cat && AGGREGATED_CATEGORIES[cat]) {
      poiCounts[cat] += 1
      if (poiLists[cat].length < 10) {
        poiLists[cat].push({ name: p.name || '', distance: dist, address: p.address || '' })
      }
      if (dist <= 200) stats200m[cat] += 1
      if (dist <= 500) stats500m[cat] += 1
      stats1000m[cat] += 1
    }

    // 品牌识别
    const name = p.name || ''
    for (const brand of KNOWN_BRANDS) {
      if (name.includes(brand)) {
        if (!brands[brand]) brands[brand] = { name: brand, count: 0, distances: [] }
        brands[brand].count += 1
        brands[brand].distances.push(dist)
        break
      }
    }

    // 竞品统计（分类匹配 + 快餐关键词扩展）
    if (competitorTypes.length > 0 && cat) {
      let isCompetitor = competitorTypes.some((ct) => {
        if (ct === '050000' || ct === '050100' || ct === '050200' || ct === '050300' || ct === '050400' || ct === '050600')
          return cat === 'restaurants' || cat === 'chinese_restaurants' || cat === 'foreign_restaurants' || cat === 'fast_food' || cat === 'bars' || cat === 'cafe_tea'
        if (ct === '050500') return cat === 'cafe_tea'
        if (ct === '100000') return cat === 'hotels'
        if (ct === '060000' || ct === '060100' || ct === '060200' || ct === '060300' || ct === '060400')
          return cat === 'shopping' || cat === 'convenience'
        if (ct === '070000') return cat === 'convenience'
        if (ct === '080000') return cat === 'bars'
        if (ct === '141200') return cat === 'schools'
        if (ct === '090100') return cat === 'hospitals'
        return false
      })

      // 快餐/小吃业态：中餐厅按店名关键词强制划入竞品（防止高德分类粗放漏判）
      if (!isCompetitor && (businessType === '050000' || businessType === '050300')) {
        if (cat === 'chinese_restaurants' || cat === 'restaurants') {
          const SNACK_KW = ['面','皮','粉','饭','包','粥','小吃','麻辣烫','炸鸡','米线','凉皮','肉夹馍','饺子','馄饨','馒头','大饼','煎饼','快餐','便当','盖浇','砂锅','冒菜','串串','卤味','鸭脖','鸡排','汉堡','披萨','拉面','拌面','酸辣粉','螺蛳粉','热干面','小面','泡馍','擀面皮','米皮','锅贴','生煎','小笼','汤包','蒸饺','油条','豆浆','豆腐脑','胡辣汤','麻辣拌','烤冷面','手抓饼','鸡蛋灌饼']
          isCompetitor = SNACK_KW.some(kw => name.includes(kw))
        }
      }

      if (isCompetitor) {
        if (dist <= 200) competitors200m += 1
        if (dist <= 500) competitors500m += 1
        competitors1000m += 1
        if (competitorList.length < 15) {
          competitorList.push({ name, distance: dist })
        }
      }
    }
  }

  const hotBrands = Object.values(brands)
    .sort((a, b) => b.count - a.count)
    .slice(0, 15)
    .map((b) => ({
      name: b.name,
      count: b.count,
      min_distance: Math.min(...b.distances),
    }))

  // 修正餐饮总数：父类 = 子类之和
  const RESTAURANT_SUB_KEYS = ['chinese_restaurants', 'foreign_restaurants', 'fast_food', 'cafe_tea', 'bars', 'restaurants']
  const totalRest = RESTAURANT_SUB_KEYS.reduce((s, k) => s + (poiCounts[k] || 0), 0)
  poiCounts['restaurants'] = totalRest
  stats200m['restaurants'] = RESTAURANT_SUB_KEYS.reduce((s, k) => s + (stats200m[k] || 0), 0)
  stats500m['restaurants'] = RESTAURANT_SUB_KEYS.reduce((s, k) => s + (stats500m[k] || 0), 0)
  stats1000m['restaurants'] = RESTAURANT_SUB_KEYS.reduce((s, k) => s + (stats1000m[k] || 0), 0)

  return {
    ...geoData,
    poi_counts: poiCounts,
    poi_lists: poiLists,
    stats_200m: stats200m,
    stats_500m: stats500m,
    stats_1000m: stats1000m,
    hot_brands: hotBrands,
    competitors_200m: competitors200m,
    competitors_500m: competitors500m,
    competitors_1000m: competitors1000m,
    competitor_list: competitorList,
  }
}
