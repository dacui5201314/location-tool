import json
import os
import re
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.schemas import AnalyzeRequest, AnalyzeResponse
from prompts.location_analysis import build_system_prompt, build_analysis_prompt
from prompts.industry_config import get_config
from services.amap_service import collect_location_data
from ai_providers.unified import generate_llm_response
from database import init_db, SessionLocal
from models.db_models import AnalysisRecord
from services.storage_service import save_report
from services.billing_service import check_billing_access, refund_credits
from services.runtime_config import get_config_value as get_runtime_config_value, get_llm_config, normalize_report_result
from models.db_models import User
from auth import get_current_user

# 注册业务路由
from routers.records import router as records_router
from routers.favorites import router as favorites_router
from routers.user import router as user_router
from routers.admin import router as admin_router
from routers.auth import router as auth_router

app = FastAPI(title="址得选 API", version="3.7.0", description="址得选 — AI 选址分析 SaaS 平台后端服务")
app.include_router(auth_router)
app.include_router(records_router)
app.include_router(favorites_router)
app.include_router(user_router)
app.include_router(admin_router)

# 挂载静态资源目录（上传的二维码等）— 按 /assets 对外暴露
import os as _os2
_static_root = _os2.path.join(_os2.path.dirname(_os2.path.abspath(__file__)), "storage", "assets")
_static_root = _os2.path.abspath(_static_root)
_os2.makedirs(_static_root, exist_ok=True)
# 放一个占位文件防止空目录报错
_placeholder = _os2.path.join(_static_root, ".gitkeep")
if not _os2.path.exists(_placeholder):
    with open(_placeholder, "w") as _f:
        _f.write("")
app.mount("/assets", StaticFiles(directory=_static_root), name="assets")


@app.on_event("startup")
def on_startup():
    init_db()


# CORS: 生产环境应通过 CORS_ORIGINS 环境变量限制来源（逗号分隔），开发环境默认允许所有
_cors_origins = os.getenv("CORS_ORIGINS", "*").split(",") if os.getenv("CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/providers")
async def list_providers():
    return {
        "providers": [
            {"id": "gemini", "name": "Google Gemini", "icon": "🤖"},
            {"id": "deepseek", "name": "DeepSeek", "icon": "🔍"},
            {"id": "kimi", "name": "Kimi (月之暗面)", "icon": "🌙"},
            {"id": "minimax", "name": "MiniMax", "icon": "✨"},
            {"id": "zhipu", "name": "智谱 GLM", "icon": "🧠"},
        ]
    }


# 业态到高德POI分类的映射
BUSINESS_TYPE_TO_AMAP = {
    # 餐饮类
    "小餐饮": "050000",    # 所有餐饮
    "大餐饮": "050100",    # 中餐厅为主
    "中餐": "050100",      # 中餐厅
    "日餐": "050200",      # 外国餐厅
    "西餐": "050200",      # 外国餐厅
    "火锅店": "050100",    # 中餐厅（火锅子类）
    "烧烤店": "050100",    # 中餐厅（烧烤子类）
    "小吃店": "050300",    # 快餐厅/小吃
    "烘焙店": "050600",    # 甜品/烘焙
    "快餐店": "050300",    # 快餐厅
    # 茶饮咖啡
    "奶茶店": "050500",    # 茶饮咖啡
    "咖啡店": "050500",    # 茶饮咖啡
    "甜品店": "050600",    # 甜品
    "饮品店": "050500",    # 茶饮咖啡
    # 酒店住宿
    "酒店": "100000",      # 酒店
    "民宿": "100000",      # 酒店/民宿
    "青年旅舍": "100000",  # 酒店
    # 零售商业
    "零售店": "060000",    # 零售
    "便利店": "060200",    # 便利店
    "超市": "060300",      # 超市
    "服装店": "060100",    # 购物/服装
    "数码店": "060400",    # 购物中心/数码
    "药店": "060400",      # 购物/药店
    # 生活服务
    "美容美发": "070000",  # 生活服务
    "健身房": "080000",    # 体育休闲
    "教育培训": "141200",  # 学校/培训
    "宠物店": "070000",    # 生活服务
    "洗衣店": "070000",    # 生活服务
    "诊所": "090100",      # 医疗
    # 休闲娱乐
    "酒吧": "050400",      # 酒吧
    "KTV": "080000",       # 娱乐
    "剧本杀": "080000",    # 娱乐
    "网吧": "080000",      # 娱乐/网吧
    "台球厅": "080000",    # 体育休闲
}


def _extract_json(text: str) -> str:
    """从 LLM 原始响应中强力提取 JSON — 处理 Markdown 代码块及前后废话"""
    text = text.strip()
    # 去掉 ```json ... ``` 或 ``` ... ``` 等 Markdown 代码块标记
    text = re.sub(r'```(?:json)?\s*\n?', '', text)
    text = re.sub(r'```\s*', '', text)
    # 定位最外层 JSON 对象
    first = text.find('{')
    last = text.rfind('}')
    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]
    return text.strip()


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_location(req: AnalyzeRequest, user: dict = Depends(get_current_user)):
    current_user_id = user["user_id"]

    # 1. 获取高德真实数据（后端 Web API 优先，前端 JS API 做备选）
    real_data = None
    try:
        # 优先使用 IndustryConfig 的竞品类型
        cfg = get_config(req.business_type)
        competitor_type = cfg.get("competitor_amap_types", "")
        if not competitor_type:
            competitor_type = BUSINESS_TYPE_TO_AMAP.get(req.business_type, "")
        ld = await collect_location_data(
            req.location.lng, req.location.lat, competitor_type
        )
        real_data = {
            "city": ld.city,
            "district": ld.district,
            "township": ld.township,
            "formatted_address": ld.address,
            "nearby_roads": ld.nearby_roads,
            "business_areas": ld.business_areas,
            "building_type": ld.building_type,
            "poi_counts": ld.poi_counts,
            "stats_200m": ld.stats_200m,
            "stats_500m": ld.stats_500m,
            "stats_1000m": ld.stats_1000m,
            "raw_poi_counts": ld.raw_poi_counts,
            "raw_stats_200m": ld.raw_stats_200m,
            "raw_stats_500m": ld.raw_stats_500m,
            "raw_stats_1000m": ld.raw_stats_1000m,
            "hot_brands": ld.hot_brands[:15],
            "competitors_200m": ld.competitors_200m,
            "competitors_500m": ld.competitors_500m,
            "competitors_1000m": ld.competitors_1000m,
            "competitor_list": ld.competitor_list[:10],
            "poi_lists": {k: v for k, v in ld.poi_lists.items()},
        }
    except Exception as e:
        import traceback
        print(f"[WARN] 后端AMap数据采集失败: {e}")
        traceback.print_exc()
        print("[INFO] 回退使用前端采集数据")
        real_data = req.real_data
    else:
        total = sum(real_data.get("poi_counts", {}).values())
        print(f"[INFO] 后端数据采集成功，共 {total} 个POI，"
              f"医院{real_data.get('poi_counts', {}).get('hospitals', 0)}个，"
              f"学校{real_data.get('poi_counts', {}).get('schools', 0)}个")

    # 2. 计费校验：会员优先 → 点数抵扣 → 拦截（强制后端鉴权，杜绝绕过）
    db_billing = SessionLocal()
    try:
        user = db_billing.query(User).filter(User.id == current_user_id).first()
        if not user:
            # 不存在用户 → 自动创建（0 点数），必须充值后才能使用
            user = User(id=current_user_id, balance_credits=0, membership_tier="free")
            db_billing.add(user)
            db_billing.commit()
            db_billing.refresh(user)

        billing = check_billing_access(user, cost=1, db_session=db_billing)
        if not billing.allowed:
            db_billing.close()
            raise HTTPException(status_code=402, detail=billing.reason)
        db_billing.commit()
        db_billing.close()
    except HTTPException:
        raise
    except Exception:
        db_billing.close()
        raise HTTPException(status_code=500, detail="计费系统异常")

    # 3. 构建提示词并调用大模型（provider 从后台核心配置热读取）
    runtime_llm = get_llm_config()
    custom_system_prompt = get_runtime_config_value("system_prompt", "").strip()
    system_prompt = custom_system_prompt or build_system_prompt(req.business_type)
    prompt = system_prompt + "\n\n" + build_analysis_prompt(
        req.address, req.location.lng, req.location.lat,
        req.business_type or "", real_data,
        brand_name=req.brand_name or "",
        store_size=req.store_size or 0,
    )

    try:
        raw_response = await generate_llm_response(prompt)
        raw_response = _extract_json(raw_response)
        result = json.loads(raw_response)
        result = normalize_report_result(result)
        result["provider"] = runtime_llm.get("provider", req.provider)
        result["error"] = None
        result["real_data"] = real_data

        # 保存分析记录到数据库
        try:
            db = SessionLocal()
            # 从 detail 中提取综合评分
            details = result.get("details", {})
            scores = []
            for key in ["population_density","traffic_accessibility","traffic_flow",
                        "consumer_profile","competition","complementary_businesses",
                        "category_advantage","cost_estimate"]:
                txt = str(details.get(key, ""))
                m = re.search(r'(\d{1,3})\s*分', txt)
                if m: scores.append(int(m.group(1)))
            overall = round(sum(scores) / len(scores)) if scores else 0

            record = AnalysisRecord(
                user_id=current_user_id,
                brand_desc=req.brand_name or "",
                address=req.address,
                latitude=req.location.lat,
                longitude=req.location.lng,
                business_type=req.business_type or "",
                store_size=req.store_size or 0,
                overall_score=overall,
                report_json=json.dumps(result, ensure_ascii=False),
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            # 保存报告为物理文件，记录路径/URL
            try:
                file_path = save_report(
                    record.id, result,
                    address=req.address, brand_name=req.brand_name or "",
                )
                if file_path.startswith("http"):
                    record.report_url = file_path
                else:
                    record.report_file = file_path
                db.commit()
            except Exception:
                pass

            db.close()
        except Exception:
            pass  # 记录保存失败不影响分析结果返回

        return result
    except json.JSONDecodeError:
        # 点数退还：LLM 返回格式异常，已扣点数必须回滚
        if billing and billing.source == "points":
            try:
                refund_credits(current_user_id, 1)
            except Exception:
                pass
        return AnalyzeResponse(
            score=0,
            advantages=[],
            disadvantages=[],
            summary="AI 引擎数据生成异常，已为您全额退还点数，请稍后重试",
            details={},
            provider=req.provider,
            error="AI JSON parse error, credits refunded",
            real_data=real_data,
        )
    except Exception as e:
        # 点数退还：任何 AI 调用异常都触发资损回滚
        if billing and billing.source == "points":
            try:
                refund_credits(current_user_id, 1)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"AI service error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
