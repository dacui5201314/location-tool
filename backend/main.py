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

from models.schemas import AnalyzeRequest
from prompts.location_analysis import build_system_prompt, build_analysis_prompt
from prompts.industry_config import get_config, get_config_by_key, BUSINESS_TYPE_TO_MASTER, get_rigor_for_config_key
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


# CORS: 生产环境必须显式设置 CORS_ORIGINS（逗号分隔），不允许 "*" 或空列表
_cors_raw = os.getenv("CORS_ORIGINS", "").strip()
_env = os.getenv("ENVIRONMENT", "development").strip().lower()
if _env == "production":
    if not _cors_raw:
        raise RuntimeError(
            "生产环境必须设置 CORS_ORIGINS 为具体域名（如 https://example.com），"
            "不允许空值。如需本地开发，请设置 ENVIRONMENT=development。"
        )
    _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()]
    if not _cors_origins:
        raise RuntimeError(
            "生产环境 CORS_ORIGINS 解析为空列表，必须包含至少一个具体域名。"
        )
    if any(o == "*" for o in _cors_origins):
        raise RuntimeError(
            "生产环境 CORS_ORIGINS 不允许包含 '*' 通配符，必须使用具体域名。"
        )
    _allow_creds = True  # 全部为具体域名时可开启
else:
    _cors_origins = [o.strip() for o in _cors_raw.split(",") if o.strip()] if _cors_raw else ["*"]
    _allow_creds = True
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器 — 捕获所有未经路由级处理的异常，返回优雅 500 而非进程崩溃
from fastapi.responses import JSONResponse as _JSONResponse
from fastapi.requests import Request as _Request

@app.exception_handler(Exception)
async def _global_exception_handler(_req: _Request, exc: Exception):
    import traceback as _traceback
    _traceback.print_exc()
    return _JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/providers")
async def list_providers(user: dict = Depends(get_current_user)):
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


from report_fact_guard import validate_report_fact_consistency


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
        _stream_ok = False  # ★ 流完整成功时置 True
        _refund_processed = False  # ★ 防双重退款
        _client_disconnect = False  # ★ 客户端主动断开不退款
        _llm_server_error = False  # ★ LLM 500 级错误
        _llm_parse_error = False   # ★ JSON 解析失败 / 空响应 / 报告结构缺失
        _amap_failed = False       # ★ AMap 采集失败（非调试模式）
        try:
            # ═══════════════════════════════════════════
            # Step 1 — POI 数据采集
            # ═══════════════════════════════════════════
            yield _sse(1, "📍 正在锁定坐标，拉取周边核心商圈 POI...")
            await asyncio.sleep(0)  # ★ 强制刷新 ASGI 缓冲区，立刻推送到前端

            real_data = None
            try:
                # ★ 统一解析 cfg 和 config_key：优先 industry_id → 数据库 → get_config_by_key
                config_key = ""
                cfg = None
                if req.industry_id:
                    db_cfg = SessionLocal()
                    try:
                        row = db_cfg.query(BusinessIndustry).filter(
                            BusinessIndustry.id == req.industry_id
                        ).first()
                        if row and row.config_key:
                            config_key = row.config_key
                            cfg = get_config_by_key(config_key)
                    except Exception:
                        pass
                    finally:
                        db_cfg.close()
                if not cfg:
                    cfg = get_config(req.business_type)
                if not config_key:
                    config_key = BUSINESS_TYPE_TO_MASTER.get(req.business_type, "")
                # competitor_type 也来自同一份 cfg
                competitor_type = cfg.get("competitor_amap_types", "") or BUSINESS_TYPE_TO_AMAP.get(req.business_type, "")
                ld = await collect_location_data(
                    req.location.lng, req.location.lat,
                    amap_type=competitor_type,
                    config_key=config_key,
                    business_type=req.business_type,
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
                    # ★ 严谨度框架
                    "direct_competitors_200m": ld.direct_competitors_200m,
                    "direct_competitors_500m": ld.direct_competitors_500m,
                    "direct_competitors_1000m": ld.direct_competitors_1000m,
                    "direct_competitor_list": ld.direct_competitor_list,
                    "substitute_competitors_200m": ld.substitute_competitors_200m,
                    "substitute_competitors_500m": ld.substitute_competitors_500m,
                    "substitute_competitors_1000m": ld.substitute_competitors_1000m,
                    "substitute_list": ld.substitute_list,
                    "traffic_anchors_200m": ld.traffic_anchors_200m,
                    "traffic_anchors_500m": ld.traffic_anchors_500m,
                    "traffic_anchors_1000m": ld.traffic_anchors_1000m,
                    "traffic_anchor_list": ld.traffic_anchor_list,
                    "irrelevant_excluded": ld.irrelevant_excluded,
                    "data_quality_notes": ld.data_quality_notes,
                    "rigor_enabled": bool(get_rigor_for_config_key(config_key)),
                }
            except Exception:
                import traceback
                print("[CRITICAL] 后端AMap数据采集失败", flush=True)
                traceback.print_exc()
                # ★ 生产环境禁止使用客户端 real_data 参与评分
                allow_fallback = os.getenv("ALLOW_CLIENT_REALDATA_FALLBACK", "").strip().lower() in ("1", "true", "yes")
                if allow_fallback:
                    fallback = req.real_data or {}
                    print(f"[WARN] ALLOW_CLIENT_REALDATA_FALLBACK=true，回退前端数据: poi_lists={len(fallback.get('poi_lists', {}))}类", flush=True)
                    real_data = fallback
                else:
                    _amap_failed = True
                    real_data = {
                        "city": "", "district": "", "township": "",
                        "poi_counts": {}, "stats_200m": {}, "stats_500m": {}, "stats_1000m": {},
                        "competitors_200m": 0, "competitors_500m": 0, "competitors_1000m": 0,
                        "competitor_list": [], "poi_lists": {},
                        "direct_competitors_200m": 0, "direct_competitors_500m": 0, "direct_competitors_1000m": 0,
                        "direct_competitor_list": [],
                        "data_quality_notes": ["数据采集失败：后端AMap服务不可用，报告数据不完整"],
                        "rigor_enabled": False,
                    }

            # ═══════════════════════════════════════════
            # Step 2 — 数据脱水与竞品交叉比对
            # ═══════════════════════════════════════════
            yield _sse(2, "🧮 高德数据脱水完成，正在交叉比对竞品与客流...")
            await asyncio.sleep(0)

            # ═══════════════════════════════════════════
            # Step 3 — AI 大模型分析
            # ═══════════════════════════════════════════
            if _amap_failed and not os.getenv("ALLOW_CLIENT_REALDATA_FALLBACK", "").strip().lower() in ("1", "true", "yes"):
                raise RuntimeError("AMAP_DATA_COLLECTION_FAILED: 后端高德数据采集失败，无法生成有效分析报告。请检查 AMAP_WEB_KEY 配置。")
            yield _sse(3, "🧠 AI 消费水平测算中，正在构建商业评估模型...")
            await asyncio.sleep(0)

            runtime_llm = get_llm_config()
            custom_system_prompt = get_runtime_config_value("system_prompt", "").strip()
            # ★ 复用前面已解析的 cfg 和 config_key，避免重复查库
            industry_config = cfg  # cfg 已在 POI 采集阶段统一解析
            industry_name = req.business_type or ""
            # 专属 Prompt 注入（如有 industry_id）
            if req.industry_id:
                db_local = SessionLocal()
                try:
                    industry = db_local.query(BusinessIndustry).filter(
                        BusinessIndustry.id == req.industry_id,
                        BusinessIndustry.is_active == 1
                    ).first()
                    if industry:
                        industry_name = industry.name
                        if industry.exclusive_prompt and industry.exclusive_prompt.strip():
                            print(f"[SSE Prompt] 已注入业态专属规则: {industry.name} ({len(industry.exclusive_prompt)}字符)", flush=True)
                except Exception as e:
                    print(f"[SSE Prompt] 业态查询失败: {e}", flush=True)
                finally:
                    db_local.close()
            system_prompt = custom_system_prompt or build_system_prompt(industry_name, config=industry_config)
            # 叠加专属规则
            if req.industry_id and industry_config:
                db_local = SessionLocal()
                try:
                    industry = db_local.query(BusinessIndustry).filter(
                        BusinessIndustry.id == req.industry_id
                    ).first()
                    if industry and industry.exclusive_prompt and industry.exclusive_prompt.strip():
                        system_prompt += "\n\n## 业态专属测算规则（优先于通用规则执行）\n" + industry.exclusive_prompt.strip()
                except Exception:
                    pass
                finally:
                    db_local.close()
            prompt = system_prompt + "\n\n" + build_analysis_prompt(
                req.address, req.location.lng, req.location.lat,
                industry_name, real_data,
                brand_name=req.brand_name or "",
                store_size=req.store_size or 0,
                config=industry_config,
            )

            try:
                raw_response = await generate_llm_response(prompt)
            except Exception as e:
                # ★ 判定是否为 LLM 服务端 5xx 错误（唯一允许退款的场景）
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    if e.response.status_code >= 500:
                        _llm_server_error = True
                        print(f"[SSE Guard] LLM 服务端 {e.response.status_code} 错误，标记可退款", flush=True)
                raise  # 继续上抛，由外层 except 统一处理
            raw_response = _extract_json(raw_response)
            result = json.loads(raw_response)

            # ★ 报告结构校验：空/非dict/缺失关键字段 → 标记解析失败走退款
            def _validate_report_payload(r):
                if not isinstance(r, dict) or not r:
                    return False, "LLM返回空或非dict"
                details = r.get("details")
                if not isinstance(details, dict) or not details:
                    return False, "缺少details或details不是有效dict"
                # 至少需要 advantages/disadvantages/summary/dimension_scores 中有2个
                has_fields = sum(1 for k in ("advantages","disadvantages","summary","dimension_scores") if r.get(k))
                if has_fields < 2:
                    return False, f"关键报告字段严重缺失(仅{has_fields}/4)"
                return True, ""
            valid, fail_reason = _validate_report_payload(result)
            if not valid:
                print(f"[SSE Guard] 报告结构校验失败: {fail_reason}", flush=True)
                _llm_parse_error = True
                raise ValueError(f"报告结构不可用: {fail_reason}")

            result = normalize_report_result(result, weights=industry_config.get("radar_weights") if industry_config else None)
            result["provider"] = runtime_llm.get("provider", req.provider)
            result["error"] = None
            result["real_data"] = real_data

            # ★ 报告事实校验：分句校验，杜绝半径交叉误伤
            if real_data and isinstance(real_data, dict):
                # ── 事实一致性校验（纯函数，可单测）──
                fact_errors = validate_report_fact_consistency(result, real_data)
                full_text = (
                    json.dumps(result.get("details", {}) or {}, ensure_ascii=False) + " " +
                    json.dumps(result.get("advantages", []), ensure_ascii=False) + " " +
                    json.dumps(result.get("disadvantages", []), ensure_ascii=False) + " " +
                    json.dumps(result.get("executive_summary", {}) or {}, ensure_ascii=False) + " " +
                    json.dumps(result.get("action_plan", []), ensure_ascii=False) + " " +
                    str(result.get("summary", ""))
                )

                # ★ P0: POI 名称引用校验 (warning-only)
                from services.poi_name_guard import check_poi_name_hallucination, check_poi_context_mismatch, check_direct_competitor_count_mismatch
                poi_name_issues = check_poi_name_hallucination(full_text, real_data, strict=False)
                if poi_name_issues:
                    print(f"[SSE Guard] POI名称引用告警 ({len(poi_name_issues)}条): {'; '.join(poi_name_issues[:5])}", flush=True)
                    result["_poi_name_warnings"] = poi_name_issues

                # ★ P2: 竞品语境中 substitute/anchor 误用检测 (warning-only)
                poi_ctx_issues = check_poi_context_mismatch(full_text, real_data)
                if poi_ctx_issues:
                    print(f"[SSE Guard] POI语境告警 ({len(poi_ctx_issues)}条): {'; '.join(poi_ctx_issues[:5])}", flush=True)
                    result["_poi_context_warnings"] = poi_ctx_issues

                # ★ P3: 直接竞品数量膨胀检测 (warning-only)
                count_issues = check_direct_competitor_count_mismatch(full_text, real_data)
                if count_issues:
                    print(f"[SSE Guard] 竞品数量告警 ({len(count_issues)}条): {'; '.join(count_issues[:5])}", flush=True)
                    result["_direct_competitor_count_warnings"] = count_issues

                if fact_errors:
                    print(f"[SSE Guard] 事实校验失败: {'; '.join(fact_errors)}", flush=True)
                    # ★ 内部免费重试一次：用同一份 real_data + fact_errors 摘要，要求 LLM 修正数字
                    print(f"[SSE Guard] 启动内部重试，修正数字幻觉...", flush=True)
                    result["_fact_retry"] = True
                    result["_fact_errors_before_retry"] = fact_errors.copy()

                    # 构建修正提示
                    correction_lines = []
                    for fe in fact_errors[:8]:  # 最多带 8 条错误提示
                        correction_lines.append(f"  - {fe}")
                    correction_hint = "\n".join(correction_lines)

                    retry_prompt = prompt + f"""

⚠️ 上一版报告存在以下数据错误，请根据错误提示严格对照上方 POI 数据表格和竞品字段修正数字：

{correction_hint}

修正要求：
- 报告中所有 POI 数量必须与上方数据表格中的数字完全一致
- 不得自行估算、放大或缩小任何数字
- 不确定的数字改用"需线下核验"替代
- 其他内容保持不变"""

                    try:
                        retry_raw = await generate_llm_response(retry_prompt)
                        retry_raw = _extract_json(retry_raw)
                        retry_result = json.loads(retry_raw)
                        valid2, fail_reason2 = _validate_report_payload(retry_result)
                        if not valid2:
                            print(f"[SSE Guard] 重试后报告结构仍无效: {fail_reason2}", flush=True)
                        else:
                            retry_result = normalize_report_result(retry_result, weights=industry_config.get("radar_weights") if industry_config else None)
                            retry_result["provider"] = runtime_llm.get("provider", req.provider)
                            retry_result["error"] = None
                            retry_result["real_data"] = real_data
                            retry_fe = validate_report_fact_consistency(retry_result, real_data)
                            if not retry_fe:
                                print(f"[SSE Guard] 重试通过，fact_errors 已修正", flush=True)
                                _saved_retry_meta = {
                                    "_fact_retry": True,
                                    "_fact_retry_passed": True,
                                    "_fact_errors_before_retry": fact_errors.copy(),
                                }
                                result = retry_result
                                result.update(_saved_retry_meta)
                                fact_errors = []
                                # ★ 基于最终报告重算 P0/P2/P3 warning
                                retry_full_text = (
                                    json.dumps(retry_result.get("details", {}) or {}, ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("advantages", []), ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("disadvantages", []), ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("executive_summary", {}) or {}, ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("action_plan", []), ensure_ascii=False) + " " +
                                    str(retry_result.get("summary", ""))
                                )
                                result["_poi_name_warnings"] = check_poi_name_hallucination(retry_full_text, real_data, strict=False)
                                result["_poi_context_warnings"] = check_poi_context_mismatch(retry_full_text, real_data)
                                result["_direct_competitor_count_warnings"] = check_direct_competitor_count_mismatch(retry_full_text, real_data)
                            else:
                                print(f"[SSE Guard] 重试仍失败: {'; '.join(retry_fe[:3])}", flush=True)
                                result["_fact_retry_failed"] = True
                                result["_fact_errors_after_retry"] = retry_fe
                                fact_errors = retry_fe  # ★ 最终 raise 使用 retry 后的错误
                    except Exception:
                        print(f"[SSE Guard] 重试异常，回退至原始错误", flush=True)

                    if fact_errors:  # 重试未通过或异常 → 原路径
                        _llm_parse_error = True
                        raise ValueError(f"报告事实校验失败(含重试): {'; '.join(fact_errors[:3])}")

            # 保存到数据库
            db = SessionLocal()
            try:
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
            except Exception:
                import traceback
                print("[CRITICAL] 分析记录数据库保存失败", flush=True)
                traceback.print_exc()
            finally:
                db.close()

            # ★ normalize_report_result 已完成加权总分计算，此处不再覆盖
            _stream_ok = True  # ★ 标记流完整成功，finally 块不退款
            yield _sse(4, "✅ 报告生成完毕！", result=result)
            await asyncio.sleep(0)

        except GeneratorExit:
            # 客户端主动断开 — 不退款
            _client_disconnect = True
            print("[SSE Guard] 客户端主动断开，不执行退款", flush=True)
        except json.JSONDecodeError:
            _llm_parse_error = True
            print("[SSE Error] JSON 解析失败，标记可退款", flush=True)
            yield _sse("error", "AI 引擎数据生成异常，请稍后重试")
            await asyncio.sleep(0)
        except RuntimeError as e:
            msg = str(e)
            if msg.startswith("AMAP_DATA_COLLECTION_FAILED"):
                print(f"[SSE Error] {msg}", flush=True)
                yield _sse("error", "数据采集失败，请稍后重试")
            else:
                print(f"[SSE Error] RuntimeError: {msg}", flush=True)
                yield _sse("error", "分析服务异常，请稍后重试")
            await asyncio.sleep(0)
        except ValueError as e:
            _llm_parse_error = True
            print(f"[SSE Error] 报告结构校验失败: {e}", flush=True)
            yield _sse("error", f"报告生成异常，请稍后重试")
            await asyncio.sleep(0)
        except Exception as e:
            print(f"[SSE Error] 分析异常: {type(e).__name__}: {e}", flush=True)
            yield _sse("error", "分析服务异常，请稍后重试")
            await asyncio.sleep(0)
        finally:
            # ★ 退款收口：LLM 错误 / JSON解析失败 / 报告结构无效 / AMap采集失败 → 点数模式退款
            should_refund = (_llm_server_error or _llm_parse_error or _amap_failed) and not _refund_processed
            if should_refund and billing and billing.source == "points":
                _refund_processed = True
                try:
                    if _amap_failed:
                        refund_reason = "AMap数据采集失败"
                    elif _llm_server_error:
                        refund_reason = "LLM服务端异常"
                    else:
                        refund_reason = "LLM响应解析失败"
                    refund_credits(current_user_id, 1, reason=refund_reason)
                    print(f"[SSE Guard] {refund_reason}，已执行点数退款", flush=True)
                except Exception:
                    import traceback
                    print("[CRITICAL] 点数退还失败！", flush=True)
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
