from pydantic import BaseModel
from typing import List, Optional


class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5


class SearchResponse(BaseModel):
    query: str
    answer: str
    sources: List[str]
    elapsed_ms: float
