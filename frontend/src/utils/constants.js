// 高德地图 JS API Key (免费申请: https://console.amap.com/)
// 通过 Vite 环境变量注入：在 frontend/.env.local 中设置 VITE_AMAP_KEY
export const AMAP_KEY = import.meta.env.VITE_AMAP_KEY || ''

// 高德地图安全密钥
// 通过 Vite 环境变量注入：在 frontend/.env.local 中设置 VITE_AMAP_SECURITY_CODE
export const AMAP_SECURITY_CODE = import.meta.env.VITE_AMAP_SECURITY_CODE || ''

export const AMAP_VERSION = '2.0'

export const PROVIDERS = [
  { id: 'deepseek', name: 'DeepSeek', icon: '🔍', color: 'bg-blue-500' },
  { id: 'gemini', name: 'Gemini', icon: '🤖', color: 'bg-green-500' },
  { id: 'kimi', name: 'Kimi 月之暗面', icon: '🌙', color: 'bg-purple-500' },
  { id: 'minimax', name: 'MiniMax', icon: '✨', color: 'bg-orange-500' },
  { id: 'zhipu', name: '智谱 GLM', icon: '🧠', color: 'bg-red-500' },
]

export const DEFAULT_PROVIDER = 'deepseek'

// 业态到高德POI分类映射（用于竞品搜索）
export const BUSINESS_TYPE_TO_AMAP = {
  // 餐饮类
  '小餐饮': '050000',    // 所有餐饮
  '大餐饮': '050100',    // 中餐厅为主
  '中餐': '050100',      // 中餐厅
  '日餐': '050200',      // 外国餐厅
  '西餐': '050200',      // 外国餐厅
  '火锅店': '050100',    // 中餐厅（火锅子类）
  '烧烤店': '050100',    // 中餐厅（烧烤子类）
  '小吃店': '050300',    // 快餐厅/小吃
  '烘焙店': '050600',    // 甜品/烘焙
  '快餐店': '050300',    // 快餐厅
  // 茶饮咖啡
  '奶茶店': '050500',    // 茶饮咖啡
  '咖啡店': '050500',    // 茶饮咖啡
  '甜品店': '050600',    // 甜品
  '饮品店': '050500',    // 茶饮咖啡
  // 酒店住宿
  '酒店': '100000',      // 酒店
  '民宿': '100000',      // 酒店/民宿
  '青年旅舍': '100000',  // 酒店
  // 零售商业
  '零售店': '060000',    // 零售
  '便利店': '060200',    // 便利店
  '超市': '060300',      // 超市
  '服装店': '060100',    // 购物/服装
  '数码店': '060400',    // 购物中心/数码
  '药店': '060400',      // 购物/药店
  // 生活服务
  '美容美发': '070000',  // 生活服务
  '健身房': '080000',    // 体育休闲
  '教育培训': '141200',  // 学校/培训
  '宠物店': '070000',    // 生活服务
  '洗衣店': '070000',    // 生活服务
  '诊所': '090100',      // 医疗
  // 休闲娱乐
  '酒吧': '050400',      // 酒吧
  'KTV': '080000',       // 娱乐
  '剧本杀': '080000',    // 娱乐
  '网吧': '080000',      // 娱乐/网吧
  '台球厅': '080000',    // 体育休闲
}
