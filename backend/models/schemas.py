from pydantic import BaseModel, ConfigDict
from typing import Optional


class Location(BaseModel):
    lng: float
    lat: float


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    address: str
    location: Location
    provider: str  # gemini, deepseek, kimi, minimax, zhipu
    business_type: str = ""  # 选址业态类型
    brand_name: str = ""  # 品牌名称或主营特色描述
    store_size: int = 0  # 门店预估面积（平方米）
    real_data: Optional[dict] = None  # 前端采集的高德数据
    industry_id: Optional[int] = None  # 业态专属规则ID（business_industries表）
    favorite_id: Optional[int] = None  # 收藏ID（从收藏页发起分析时传入）


class AnalyzeResponse(BaseModel):
    score: Optional[int] = None
    advantages: list[str] = []
    disadvantages: list[str] = []
    warning: Optional[str] = None
    summary: str = ""
    details: dict[str, object] = {}
    executive_summary: dict[str, object] = {}
    dimension_scores: list[dict[str, object]] = []
    action_plan: list[str] = []
    provider: str = ""
    error: Optional[str] = None
    real_data: Optional[dict] = None
