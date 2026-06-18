from pydantic import BaseModel
from typing import List


class SourceInfo(BaseModel):
    source: str
    page: int


class MetricsInfo(BaseModel):
    retrieval_time: float
    rerank_time: float
    llm_time: float
    total_time: float


class QuestionResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    metrics: MetricsInfo