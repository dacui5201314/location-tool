import json
import os
import re
import asyncio
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from models.schemas import AnalyzeRequest, AnalyzeResponse
from prompts.location_analysis import build_system_prompt, build_analysis_prompt
from prompts.industry_config import get_config
from services.amap_service import collect_location_data
from ai_providers.unified import generate_llm_response
from database import init_db, SessionLocal
from models.db_models import AnalysisRecord, User, BusinessIndustry
from services.storage_service import save_report
from services.billing_service import check_billing_access, refund_credits
from services.runtime_config import get_config_value as get_runtime_config_value, get_llm_config, normalize_report_result
from auth import get_current_user

# 注册业务路由
from routers.records import router as records_router
from routers.favorites import router as favorites_router
from routers.user import router as user_router
from routers.admin import router as admin_router
from routers.auth import router as auth_router
from routers.industries import router as industries_router, public_router as industries_public_router

app = FastAPI(title="址得选 API", version="3.7.0", description="址得选 — AI 选址分析 SaaS 平台后端服务")
app.include_router(auth_router)
app.include_router(records_router)
app.include_router(favorites_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(industries_router)
app.include_router(industries_public_router)

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
    """从 LLM 原始响应中强力提取 JSON — Markdown 清洗 + 截断修复 + 尾逗号清理"""
    text = text.strip()
    # 1. 去掉 Markdown 代码块标记
    text = re.sub(r'```(?:json)?\s*\n?', '', text)
    text = re.sub(r'```\s*', '', text)
    # 2. 定位最外层 JSON 对象
    first = text.find('{')
    last = text.rfind('}')
    if first != -1 and last != -1 and last > first:
        text = text[first:last + 1]
    # 3. 清洗 JSON 中常见非法内容
    text = re.sub(r',\s*}', '}', text)   # 尾逗号 → }（对象）
    text = re.sub(r',\s*]', ']', text)   # 尾逗号 → ]（数组）
    # 4. 截断修复：补全缺失的括号
    if text and text[0] == '{':
        open_braces = text.count('{') - text.count('}')
        open_brackets = text.count('[') - text.count(']')
        if open_braces > 0 or open_brackets > 0:
            # 截断在字符串中 → 先闭合引号
            in_string = False
            prev = ''
            for ch in text:
                if ch == '"' and prev != '\\':
                    in_string = not in_string
                prev = ch
            if in_string:
                text += '"'
            text += ']' * max(0, open_brackets) + '}' * max(0, open_braces)
    return text.strip()


def _sse(step, msg, result=None):
    """构建 SSE 事件字符串"""
    payload = {"step": step, "msg": msg}
    if result is not None:
        payload["result"] = result
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


@app.post("/api/analyze")
async def analyze_location(req: AnalyzeRequest, user: dict = Depends(get_current_user)):
    """SSE 流式选址分析 — 四步进度推送 + 最终报告 JSON"""
    current_user_id = user["user_id"]

    # ── 前置计费校验（流开始前必须通过，失败直接返回 402）──
    billing = None
    db_billing = SessionLocal()
    try:
        db_user = db_billing.query(User).filter(User.id == current_user_id).first()
        if not db_user:
            db_user = User(id=current_user_id, balance_credits=0, membership_tier="free")
            db_billing.add(db_user)
            db_billing.commit()
            db_billing.refresh(db_user)

        billing = check_billing_access(db_user, cost=1, db_session=db_billing)
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

    async def event_stream():
        """SSE 事件生成器"""
        nonlocal billing
        _stream_ok = False  # ★ 流完整结束时置 True，防止 finally 误退款
        try:
            # ═══════════════════════════════════════════
            # Step 1 — POI 数据采集
            # ═══════════════════════════════════════════
            yield _sse(1, "📍 正在锁定坐标，拉取周边核心商圈 POI...")
            await asyncio.sleep(0)  # ★ 强制刷新 ASGI 缓冲区，立刻推送到前端

            real_data = None
            try:
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
            except Exception:
                import traceback
                print("[WARN] 后端AMap数据采集失败，回退前端数据", flush=True)
                traceback.print_exc()
                real_data = req.real_data

            # ═══════════════════════════════════════════
            # Step 2 — 数据脱水与竞品交叉比对
            # ═══════════════════════════════════════════
            yield _sse(2, "🧮 高德数据脱水完成，正在交叉比对竞品与客流...")
            await asyncio.sleep(0)

            # ═══════════════════════════════════════════
            # Step 3 — AI 大模型分析
            # ═══════════════════════════════════════════
            yield _sse(3, "🧠 AI 消费水平测算中，正在构建商业评估模型...")
            await asyncio.sleep(0)

            runtime_llm = get_llm_config()
            custom_system_prompt = get_runtime_config_value("system_prompt", "").strip()
            system_prompt = custom_system_prompt or build_system_prompt(req.business_type)
            # ★ 业态专属规则注入：叠加 industry 专属 Prompt 到 system_prompt 尾部
            if req.industry_id:
                try:
                    db_local = SessionLocal()
                    industry = db_local.query(BusinessIndustry).filter(
                        BusinessIndustry.id == req.industry_id,
                        BusinessIndustry.is_active == 1
                    ).first()
                    db_local.close()
                    if industry and industry.exclusive_prompt and industry.exclusive_prompt.strip():
                        system_prompt += "\n\n## 业态专属测算规则（优先于通用规则执行）\n" + industry.exclusive_prompt.strip()
                        print(f"[SSE Prompt] 已注入业态专属规则: {industry.name} ({len(industry.exclusive_prompt)}字符)", flush=True)
                except Exception as e:
                    print(f"[SSE Prompt] 业态专属规则注入失败: {e}", flush=True)
            prompt = system_prompt + "\n\n" + build_analysis_prompt(
                req.address, req.location.lng, req.location.lat,
                req.business_type or "", real_data,
                brand_name=req.brand_name or "",
                store_size=req.store_size or 0,
            )

            raw_response = await generate_llm_response(prompt)
            raw_response = _extract_json(raw_response)
            result = json.loads(raw_response)
            result = normalize_report_result(result)
            result["provider"] = runtime_llm.get("provider", req.provider)
            result["error"] = None
            result["real_data"] = real_data

            # 保存到数据库
            try:
                db = SessionLocal()
                # ★ 直接复用 normalize_report_result 已算好的分数，不与 detail 文本重复解析
                overall = result.get("score", 0)

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
                    import traceback
                    print("[CRITICAL] 报告物理文件保存失败", flush=True)
                    traceback.print_exc()
                db.close()
            except Exception:
                import traceback
                print("[CRITICAL] 分析记录数据库保存失败", flush=True)
                traceback.print_exc()

            # ═══════════════════════════════════════════
            # Step 4 — 流输出前最终拦截：强制重算总分
            # ═══════════════════════════════════════════
            dims = result.get("dimension_scores", [])
            final_scores = [int(d.get("score") or 0) for d in dims if isinstance(d, dict) and int(d.get("score") or 0) > 0]
            if final_scores:
                locked_score = round(sum(final_scores) / len(final_scores))
                result["score"] = locked_score
                result["overall_score"] = locked_score
                result["total_score"] = locked_score
                print(f"[SSE Intercept] Step4 前最终锁定: 维度分={final_scores}, 总分={locked_score}", flush=True)
            _stream_ok = True  # ★ 标记流完整成功，finally 块不退款
            yield _sse(4, "✅ 报告生成完毕！", result=result)
            await asyncio.sleep(0)

        except json.JSONDecodeError:
            if billing and billing.source == "points":
                try: refund_credits(current_user_id, 1)
                except Exception:
                    import traceback
                    print("[CRITICAL] JSON解析失败后点数退还失败！", flush=True)
                    traceback.print_exc()
            yield _sse("error", "AI 引擎数据生成异常，已为您全额退还点数，请稍后重试")
            await asyncio.sleep(0)
        except Exception:
            if billing and billing.source == "points":
                try: refund_credits(current_user_id, 1)
                except Exception:
                    import traceback
                    print("[CRITICAL] AI调用异常后点数退还失败！", flush=True)
                    traceback.print_exc()
            yield _sse("error", "分析服务异常，已为您退还点数，请稍后重试")
            await asyncio.sleep(0)
        finally:
            # ★ 流异常中断兜底：客户端断连 / GeneratorExit / 任何未被上层捕获的退出
            if not _stream_ok and billing and billing.source == "points":
                try:
                    refund_credits(current_user_id, 1)
                    print("[SSE Guard] 流异常中断，已执行点数退款", flush=True)
                except Exception:
                    import traceback
                    print("[CRITICAL] 流中断后点数退还失败！", flush=True)
                    traceback.print_exc()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
