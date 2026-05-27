import json
import os
import re
import asyncio
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse

from models.schemas import AnalyzeRequest
from prompts.location_analysis import build_system_prompt, build_analysis_prompt
from prompts.industry_config import get_config, get_config_by_key, BUSINESS_TYPE_TO_MASTER, get_rigor_for_config_key
from services.amap_service import collect_location_data
from ai_providers.unified import generate_llm_response
from database import init_db, SessionLocal, get_db
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
from routers.pay import router as pay_router
from routers.location import router as location_router

app = FastAPI(title="址得选 API", version="3.7.0", description="址得选 — AI 选址分析 SaaS 平台后端服务")
app.include_router(auth_router)
app.include_router(records_router)
app.include_router(favorites_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(industries_router)
app.include_router(industries_public_router)
app.include_router(pay_router)
app.include_router(location_router)


# ═══════════════════════════════════════════
# 公开只读分享接口 — 替代 PDF 分享
# ═══════════════════════════════════════════
@app.get("/api/reports/share/{share_token}")
def get_shared_report(
    share_token: str,
    db: Session = Depends(get_db),
):
    """公开只读分享接口。
    通过 share_token 查找报告，仅返回展示所需字段。
    不返回手机号、token、openid、billing、admin 等隐私数据。
    """
    from models.db_models import AnalysisRecord

    if not share_token or len(share_token) < 10:
        raise HTTPException(status_code=404, detail="报告不存在或已失效")

    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.share_token == share_token
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="报告不存在或已失效")

    return {
        "report_uuid": record.report_uuid,
        "address": record.address or "",
        "business_type": record.business_type or "",
        "brand_desc": record.brand_desc or "",
        "overall_score": record.overall_score,
        "created_at": str(record.created_at) if record.created_at else "",
        "report_json": record.report_json or "{}",
    }


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
    # ═══════════ master 业态名 fallback（Phase 9E）═══════════
    # 优先走 get_config() competitor_amap_types；此处为安全网兜底
    "低频目的零售": "060100|060400",   # 服装/数码/专卖（config: 060100|060400）
    "民宿青旅": "100000",              # 酒店/民宿（config: 100000）
    "夜经济娱乐": "050400|080000",     # 酒吧/娱乐（config: 050400|080000）
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


def _filter_json_artifact_errors(fact_errors: list) -> list:
    """过滤因 JSON 序列化标点/数字泄露到分句产生的假阳性 fact_errors。
    JSON keys/values 在 json.dumps 后混入中文逗号分句中，导致
    "学校"匹配到 JSON 中 score=74 的 "74" 数字而产生误报。
    仅保留不包含 JSON artifact 或 reported 数值合理的错误。
    """
    if not fact_errors:
        return fact_errors
    _json_artifact_pat = re.compile(r'[\[\]{}"]')
    filtered = []
    for err in fact_errors:
        if " in '" not in err:
            filtered.append(err)
            continue
        prefix, fragment = err.split(" in '", 1)
        fragment = fragment.rstrip("'")
        n_artifacts = len(_json_artifact_pat.findall(fragment))
        if n_artifacts < 2:
            filtered.append(err)
            continue
        # 2+ JSON 标点 → 分句已被 JSON 语法污染，数字归属不可靠
        if n_artifacts >= 2:
            continue
        filtered.append(err)
    return filtered


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
        _db_save_error = False     # ★ Phase 13: DB 主记录保存失败（硬阻断，触发退款）
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
                if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                    if e.response.status_code >= 500:
                        _llm_server_error = True
                        print(f"[SSE Guard] LLM 服务端 {e.response.status_code} 错误，标记可退款", flush=True)
                raise
            # ── 安全诊断：记录响应形态，不输出内容 ──
            _raw_len = len(raw_response) if raw_response else 0
            _has_json_fence = '```json' in (raw_response or '')
            _first_brace = raw_response.find('{') if raw_response else -1
            _last_brace = raw_response.rfind('}') if raw_response else -1
            _likely_truncated = _last_brace < max(0, _raw_len - 20) if _raw_len > 0 else False
            print(f"[SSE Diag] LLM response len={_raw_len} json_fence={_has_json_fence} firstBrace={_first_brace} lastBrace={_last_brace} likelyTruncated={_likely_truncated}", flush=True)
            raw_response = _extract_json(raw_response)
            _extracted_len = len(raw_response) if raw_response else 0
            print(f"[SSE Diag] after extract_json len={_extracted_len}", flush=True)
            try:
                result = json.loads(raw_response)
            except json.JSONDecodeError as _je:
                print(f"[SSE Diag] JSON parse FAIL at pos {_je.pos}: {str(_je)[:120]}", flush=True)
                raise

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
                # ★ 过滤 JSON 序列化数字泄露到分句中的假阳性
                fact_errors = _filter_json_artifact_errors(fact_errors)
                full_text = (
                    json.dumps(result.get("details", {}) or {}, ensure_ascii=False) + " " +
                    json.dumps(result.get("advantages", []), ensure_ascii=False) + " " +
                    json.dumps(result.get("disadvantages", []), ensure_ascii=False) + " " +
                    json.dumps(result.get("executive_summary", {}) or {}, ensure_ascii=False) + " " +
                    json.dumps(result.get("action_plan", []), ensure_ascii=False) + " " +
                    str(result.get("summary", ""))
                )

                # ★ P0: POI 名称引用校验 → hard-error (Phase 11)
                from services.poi_name_guard import check_poi_name_hallucination, check_poi_context_mismatch, check_direct_competitor_count_mismatch
                poi_name_issues = check_poi_name_hallucination(full_text, real_data, strict=True)
                if poi_name_issues:
                    print(f"[SSE Guard] POI名称引用告警 ({len(poi_name_issues)}条): {'; '.join(poi_name_issues[:5])}", flush=True)
                    result["_poi_name_warnings"] = poi_name_issues
                    for issue in poi_name_issues[:5]:
                        fact_errors.append(f"[P0-NAME] {issue}")

                # ★ P2: 竞品语境中 substitute/anchor 误用检测 → hard-error (Phase 11)
                poi_ctx_issues = check_poi_context_mismatch(full_text, real_data)
                if poi_ctx_issues:
                    print(f"[SSE Guard] POI语境告警 ({len(poi_ctx_issues)}条): {'; '.join(poi_ctx_issues[:5])}", flush=True)
                    result["_poi_context_warnings"] = poi_ctx_issues
                    for issue in poi_ctx_issues[:5]:
                        fact_errors.append(f"[P2-CTX] {issue}")

                # ★ P3: 直接竞品数量膨胀检测 → hard-error (Phase 11)
                count_issues = check_direct_competitor_count_mismatch(full_text, real_data)
                if count_issues:
                    print(f"[SSE Guard] 竞品数量告警 ({len(count_issues)}条): {'; '.join(count_issues[:5])}", flush=True)
                    result["_direct_competitor_count_warnings"] = count_issues
                    for issue in count_issues[:5]:
                        fact_errors.append(f"[P3-COUNT] {issue}")

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

⚠️ 上一版报告存在以下数据错误，请根据错误提示严格对照上方 POI 数据表格和竞品字段修正：

{correction_hint}

修正要求：
- [P0-NAME] 报告中引用的POI名称必须在数据源中真实存在，不得凭知识编造。如果数据源中没有对应的POI，请写"暂无数据"，绝对不要凭空编造。不要使用"某X"、"周边有X"等模糊描述代替具体名称
- [P2-CTX] 替代性竞品和客流锚点不得在竞品语境中被写成直接竞品，必须标注其真实分类
- [P3-COUNT] 所有数值必须来自上方数据表格，不要夸大或编造。直接对照 stats_* 字段的数字填写
- 特别是交通设施数量（地铁站、公交站、停车场），必须严格使用 real_data 中各半径 stats 字段的值
- **每句只提一种类型数量**：住宅小区数量和学校数量要写在不同的句子中，例如"500米内有6所学校。同时有16个住宅小区"
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
                            retry_fe = _filter_json_artifact_errors(retry_fe)
                            if not retry_fe:
                                # ★ Phase 11: retry 后重新检查 P0/P2/P3，有残留则 retry 失败
                                retry_full_text = (
                                    json.dumps(retry_result.get("details", {}) or {}, ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("advantages", []), ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("disadvantages", []), ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("executive_summary", {}) or {}, ensure_ascii=False) + " " +
                                    json.dumps(retry_result.get("action_plan", []), ensure_ascii=False) + " " +
                                    str(retry_result.get("summary", ""))
                                )
                                retry_p0 = check_poi_name_hallucination(retry_full_text, real_data, strict=True)
                                retry_p2 = check_poi_context_mismatch(retry_full_text, real_data)
                                retry_p3 = check_direct_competitor_count_mismatch(retry_full_text, real_data)
                                # ★ P0/P2/P3 残留 → 合并进 retry_fe 触发失败
                                if retry_p0:
                                    for issue in retry_p0[:3]:
                                        retry_fe.append(f"[P0-NAME] {issue}")
                                if retry_p2:
                                    for issue in retry_p2[:3]:
                                        retry_fe.append(f"[P2-CTX] {issue}")
                                if retry_p3:
                                    for issue in retry_p3[:3]:
                                        retry_fe.append(f"[P3-COUNT] {issue}")

                            if not retry_fe:
                                print(f"[SSE Guard] 重试通过，所有 fact_errors/P0/P2/P3 已修正", flush=True)
                                _saved_retry_meta = {
                                    "_fact_retry": True,
                                    "_fact_retry_passed": True,
                                    "_fact_errors_before_retry": fact_errors.copy(),
                                }
                                result = retry_result
                                result.update(_saved_retry_meta)
                                result["_poi_name_warnings"] = retry_p0
                                result["_poi_context_warnings"] = retry_p2
                                result["_direct_competitor_count_warnings"] = retry_p3
                                fact_errors = []
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
            _db_save_ok = False
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
                # ★ expire_on_commit 可能使 record 脱管；直接取 id/uuid 不依赖 refresh
                _saved_id = record.id
                _saved_uuid = str(record.report_uuid) if hasattr(record, 'report_uuid') else ""
                _db_save_ok = True  # ★ DB 主记录保存成功

                try:
                    file_path = save_report(
                        _saved_id, result,
                        address=req.address, brand_name=req.brand_name or "",
                    )
                    # ★ record 可能已脱管，重新查询后更新 report_url/file
                    _r = db.query(AnalysisRecord).filter(AnalysisRecord.id == _saved_id).first()
                    if _r:
                        if file_path.startswith("http"):
                            _r.report_url = file_path
                        else:
                            _r.report_file = file_path
                        db.commit()
                except Exception:
                    import traceback
                    print("[CRITICAL] 报告物理文件保存失败（可用 report_json 动态重建）", flush=True)
                    traceback.print_exc()
            except Exception:
                import traceback
                print("[CRITICAL] 分析记录数据库保存失败，报告未落库！", flush=True)
                traceback.print_exc()
                _db_save_error = True  # ★ Phase 13: DB 主记录失败 → 触发退款
            finally:
                if not _db_save_ok:
                    try:
                        db.rollback()
                    except Exception:
                        pass
                db.close()

            if not _db_save_ok:
                # ★ Phase 13: DB 保存失败硬阻断，不返回成功
                print("[SSE Guard] DB 保存失败，终止成功流程，标记可退款", flush=True)
                raise RuntimeError("DB_SAVE_FAILED: 分析记录保存失败，报告未落库")

            # ★ normalize_report_result 已完成加权总分计算，此处不再覆盖
            result["record_id"] = _saved_uuid  # ★ uni-app 前端需要 UUID 跳转报告页
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
            elif msg.startswith("DB_SAVE_FAILED"):
                print(f"[SSE Error] {msg}", flush=True)
                yield _sse("error", "报告保存失败，点数已自动退还")
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
            ename = type(e).__name__
            emsg = str(e)[:200]
            # 安全错误分类：不泄露 key/请求内容
            if ename == "HTTPStatusError" and hasattr(e, 'response'):
                sc = e.response.status_code if hasattr(e.response, 'status_code') else 0
                if 400 <= sc < 500:
                    _llm_parse_error = True
                    print(f"[SSE Error] LLM HTTP {sc}", flush=True)
                    yield _sse("error", "AI 服务配置异常，请联系管理员")
                elif sc >= 500:
                    _llm_server_error = True
                    print(f"[SSE Error] LLM 服务端 {sc}", flush=True)
                    yield _sse("error", "AI 服务暂不可用，请稍后重试")
                else:
                    print(f"[SSE Error] LLM HTTP {sc}", flush=True)
                    yield _sse("error", "分析服务异常，请稍后重试")
            elif "timeout" in emsg.lower() or ename == "TimeoutException":
                print(f"[SSE Error] LLM timeout", flush=True)
                yield _sse("error", "AI 服务响应超时，请稍后重试")
            elif "connect" in emsg.lower() or ename == "ConnectError":
                print(f"[SSE Error] LLM connect failed", flush=True)
                yield _sse("error", "AI 服务连接失败，请检查网络或配置")
            else:
                print(f"[SSE Error] {ename}: {emsg}", flush=True)
                yield _sse("error", "分析服务异常，请稍后重试")
            await asyncio.sleep(0)
        finally:
            # ★ 退款收口：LLM/JSON/AMap/DB 失败 → 点数模式退款 (Phase 13: +_db_save_error)
            should_refund = (_llm_server_error or _llm_parse_error or _amap_failed or _db_save_error) and not _refund_processed
            if should_refund and billing and billing.source == "points":
                _refund_processed = True
                try:
                    if _db_save_error:
                        refund_reason = "DB保存失败"
                    elif _amap_failed:
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
