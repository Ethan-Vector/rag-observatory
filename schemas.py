from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    route: str = "default"
    query: str
    top_k: int | None = None


class QueryResponse(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    confidence: float
    no_answer: bool
    trace_id: str
