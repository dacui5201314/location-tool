"""精细化 business_industries 表：删除斜杠拼凑名，插入 34 个清爽专业业态名"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal, init_db
from models.db_models import BusinessIndustry

init_db()

# ── 34 个清爽业态：{name: (config_key, category, sort_order)} ──
CLEAN_INDUSTRIES = [
    # 餐饮（sort 1-11）
    ("中餐厅",     "中餐正餐",           "餐饮"),
    ("西餐厅",     "异国_中高端正餐",    "餐饮"),
    ("日料店",     "异国_中高端正餐",    "餐饮"),
    ("火锅店",     "火锅_烧烤",          "餐饮"),
    ("烧烤店",     "火锅_烧烤",          "餐饮"),
    ("小吃店",     "刚需快餐小吃",       "餐饮"),
    ("快餐店",     "刚需快餐小吃",       "餐饮"),
    ("小餐饮",     "刚需快餐小吃",       "餐饮"),
    ("大餐饮",     "中餐正餐",           "餐饮"),
    ("烘焙店",     "烘焙甜品",           "餐饮"),
    ("甜品店",     "烘焙甜品",           "餐饮"),
    # 茶饮咖啡（sort 12-14）
    ("奶茶店",     "精品茶饮咖啡",       "茶饮咖啡"),
    ("咖啡馆",     "精品茶饮咖啡",       "茶饮咖啡"),
    ("饮品店",     "精品茶饮咖啡",       "茶饮咖啡"),
    # 零售商业（sort 15-20）
    ("便利店",     "高频刚需零售",       "零售商业"),
    ("超市",       "高频刚需零售",       "零售商业"),
    ("药店",       "高频刚需零售",       "零售商业"),
    ("服装店",     "低频目的零售",       "零售商业"),
    ("数码店",     "低频目的零售",       "零售商业"),
    ("零售店",     "低频目的零售",       "零售商业"),
    # 酒店住宿（sort 21-23）
    ("酒店",       "商务酒店",           "酒店住宿"),
    ("民宿",       "民宿青旅",           "酒店住宿"),
    ("青年旅舍",   "民宿青旅",           "酒店住宿"),
    # 生活服务（sort 24-29）
    ("美容美发",   "专业生活服务",       "生活服务"),
    ("健身房",     "专业生活服务",       "生活服务"),
    ("宠物店",     "专业生活服务",       "生活服务"),
    ("洗衣店",     "社区基础服务",       "生活服务"),
    ("教育培训",   "社区基础服务",       "生活服务"),
    ("诊所",       "社区基础服务",       "生活服务"),
    # 休闲娱乐（sort 30-34）
    ("酒吧",       "夜经济娱乐",         "休闲娱乐"),
    ("KTV",        "夜经济娱乐",         "休闲娱乐"),
    ("网吧",       "夜经济娱乐",         "休闲娱乐"),
    ("剧本杀",     "沉浸式社交娱乐",     "休闲娱乐"),
    ("台球厅",     "沉浸式社交娱乐",     "休闲娱乐"),
]

db = SessionLocal()

# ── Step 1: 删除所有含 "/" 的拼凑名 ──
all_items = db.query(BusinessIndustry).all()
slash_names = [i for i in all_items if "/" in (i.name or "")]
deleted_count = 0
for item in slash_names:
    print(f"  [DEL] {item.name}  (id={item.id})")
    db.delete(item)
    deleted_count += 1
if deleted_count:
    db.commit()
    print(f"已删除 {deleted_count} 条含斜杠的拼凑名\n")

# ── Step 2: 保留的干净记录（人工创建的 新茶饮/小吃快餐/火锅烧烤）─
existing_names = {item.name for item in db.query(BusinessIndustry).all()}
print(f"保留的现有记录: {existing_names}\n")

# ── Step 3: 插入清爽业态 ──
inserted = 0
skipped = 0
for idx, (name, config_key, category) in enumerate(CLEAN_INDUSTRIES, 1):
    if name in existing_names:
        # 已存在 → 只更新 config_key 和 sort_order
        item = db.query(BusinessIndustry).filter(BusinessIndustry.name == name).first()
        if item:
            item.config_key = config_key
            item.sort_order = idx
            print(f"  [UPD] {name:<10s} → config_key={config_key:<18s} sort={idx}")
        skipped += 1
        continue

    item = BusinessIndustry(
        name=name,
        config_key=config_key,
        exclusive_prompt="",
        is_active=1,
        sort_order=idx,
    )
    db.add(item)
    print(f"  [ADD] {name:<10s} → config_key={config_key:<18s} sort={idx}  cat={category}")
    inserted += 1

db.commit()

# ── Step 4: 停用仍残留的混合名（如“新茶饮”、“小吃快餐”、“火锅烧烤”─ 它们与细分业态重复）──
# 这些是人工创建的总称，现在被细分业态覆盖，停用即可
overlap_names = {"新茶饮", "小吃快餐", "火锅烧烤"}
for item in db.query(BusinessIndustry).filter(BusinessIndustry.name.in_(overlap_names)).all():
    item.is_active = 0
    print(f"  [OFF] {item.name} → 已停用（细分业态已覆盖）")
db.commit()

# ── 最终汇总 ──
final = db.query(BusinessIndustry).filter(BusinessIndustry.is_active == 1).order_by(BusinessIndustry.sort_order).all()
print(f"\n{'='*55}")
print(f"迁移完成：新增 {inserted} 条，更新 {skipped} 条，删除 {deleted_count} 条")
print(f"当前启用业态 {len(final)} 条：")
for item in final:
    name_display = item.name or ""
    print(f"  {item.sort_order:2d}. {name_display:<10s}  config_key={item.config_key:<18s}  active={item.is_active}")

total = db.query(BusinessIndustry).count()
active = db.query(BusinessIndustry).filter(BusinessIndustry.is_active == 1).count()
print(f"\n总计 {total} 条（{active} 启用, {total - active} 停用）")
db.close()
