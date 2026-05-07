"""将 industry_config.py 中 14 个业态母版批量插入 business_industries 表"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import SessionLocal, init_db
from models.db_models import BusinessIndustry
from prompts.industry_config import MASTER_TEMPLATES

# 确保表存在
init_db()

# 从 MASTER_TEMPLATES 提取业态列表（label 作为 name，exclusive_prompt 初始为空）
templates = []
for key, cfg in MASTER_TEMPLATES.items():
    name = cfg.get("label", key)
    templates.append({"name": name, "source_key": key})

print(f"从 industry_config.py 读取到 {len(templates)} 个业态母版：")
for i, t in enumerate(templates, 1):
    print(f"  {i:2d}. {t['name']}  (key: {t['source_key']})")

db = SessionLocal()

# 查询已有业态
existing = db.query(BusinessIndustry).all()
existing_names = {e.name for e in existing}
print(f"\n数据库中已有 {len(existing)} 条记录：{existing_names}")

# 跳过已存在的
inserted = 0
skipped = 0
for i, t in enumerate(templates, 1):
    if t["name"] in existing_names:
        print(f"  [SKIP] {t['name']} — 已存在")
        skipped += 1
        continue
    # 模糊匹配：已有名称包含新名称 或 新名称包含已有名称
    match = None
    for en in existing_names:
        if en in t["name"] or t["name"] in en or any(p in en for p in t["name"].split("/")) or any(p in t["name"] for p in en.split("/")):
            match = en
            break
    if match:
        print(f"  [SKIP] {t['name']} — 疑似匹配已有「{match}」")
        skipped += 1
        continue

    item = BusinessIndustry(
        name=t["name"],
        exclusive_prompt="",
        is_active=1,
        sort_order=i,
    )
    db.add(item)
    print(f"  [OK]   {t['name']} → 已插入 (sort_order={i})")
    inserted += 1

db.commit()
db.close()

print(f"\n迁移完成：新增 {inserted} 条，跳过 {skipped} 条，总计 {len(existing_names) + inserted} 条")
