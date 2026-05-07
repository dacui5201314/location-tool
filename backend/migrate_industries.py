"""将 industry_config.py 中 14 个业态母版批量插入 business_industries 表，并填充 config_key"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal, init_db
from models.db_models import BusinessIndustry
from prompts.industry_config import MASTER_TEMPLATES

# 确保表存在（含新增的 config_key 列）
init_db()

# 从 MASTER_TEMPLATES 提取业态列表
templates = []
for key, cfg in MASTER_TEMPLATES.items():
    name = cfg.get("label", key)
    templates.append({"name": name, "config_key": key})

print(f"从 industry_config.py 读取到 {len(templates)} 个业态母版：")
for i, t in enumerate(templates, 1):
    print(f"  {i:2d}. {t['name']:<16s}  config_key={t['config_key']}")

db = SessionLocal()

# ── 先更新已有记录的 config_key ──
all_items = db.query(BusinessIndustry).all()
updated_keys = 0
for item in all_items:
    # 精确匹配 name
    for t in templates:
        if item.name == t["name"]:
            item.config_key = t["config_key"]
            updated_keys += 1
            print(f"  [FIX] {item.name} → config_key={t['config_key']}")
            break
    else:
        # 模糊匹配（手动创建的业态如 新茶饮、小吃快餐、火锅烧烤）
        for t in templates:
            name_parts = set(item.name.replace("/", " ").split())
            tpl_parts = set(t["name"].replace("/", " ").split())
            if name_parts & tpl_parts:
                item.config_key = t["config_key"]
                updated_keys += 1
                print(f"  [FIX] {item.name} → config_key={t['config_key']} (模糊匹配 {t['name']})")
                break
if updated_keys:
    db.commit()
    print(f"\n已修复 {updated_keys} 条已有记录的 config_key")

# ── 插入缺失的业态 ──
existing_names = {e.name for e in db.query(BusinessIndustry).all()}
inserted = 0
skipped = 0
for i, t in enumerate(templates, 1):
    if t["name"] in existing_names:
        print(f"  [SKIP] {t['name']} — 已存在")
        skipped += 1
        continue
    # 模糊匹配检查
    match = None
    for en in existing_names:
        n1_parts = set(t["name"].replace("/", " ").split())
        n2_parts = set(en.replace("/", " ").split())
        if n1_parts & n2_parts:
            match = en
            break
    if match:
        print(f"  [SKIP] {t['name']} — 疑似匹配已有「{match}」")
        skipped += 1
        continue

    item = BusinessIndustry(
        name=t["name"],
        config_key=t["config_key"],
        exclusive_prompt="",
        is_active=1,
        sort_order=i,
    )
    db.add(item)
    print(f"  [OK]   {t['name']} → 已插入 (config_key={t['config_key']})")
    inserted += 1

db.commit()

# ── 最终汇总 ──
final = db.query(BusinessIndustry).order_by(BusinessIndustry.sort_order).all()
print(f"\n{'='*60}")
print(f"迁移完成：新增 {inserted} 条，跳过 {skipped} 条")
print(f"\n最终业态列表（共 {len(final)} 条）：")
for item in final:
    has_prompt = "✓" if item.exclusive_prompt and item.exclusive_prompt.strip() else "—"
    print(f"  {item.sort_order:2d}. {item.name:<18s}  config_key={item.config_key:<16s}  规则:{has_prompt}  状态:{'启用' if item.is_active else '停用'}")
db.close()
