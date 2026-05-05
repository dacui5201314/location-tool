from pydantic import BaseModel
from typing import Optional


class Location(BaseModel):
    lng: float
    lat: float


class AnalyzeRequest(BaseModel):
    address: str
    location: Location
    provider: str  # gemini, deepseek, kimi, minimax, zhipu
    business_type: str = ""  # 选址业态类型
    brand_name: str = ""  # 品牌名称或主营特色描述
    store_size: int = 0  # 门店预估面积（平方米）
    real_data: Optional[dict] = None  # 前端采集的高德数据
    user_id: int = 1  # 用户ID（接入鉴权后从 token 解析）


class AnalyzeResponse(BaseModel):
    score: Optional[int] = None
    advantages: list[str] = []
    disadvantages: list[str] = []
    warning: Optional[str] = None
    summary: str = ""
    details: dict[str, object] = {}
    provider: str = ""
    error: Optional[str] = None
    real_data: Optional[dict] = None
