from __future__ import annotations

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=10)


class SearchMatch(BaseModel):
    ticket_key: str
    title: str
    description: str
    url: str
    score: float
    reason: str


class SearchResponse(BaseModel):
    query: str
    total_matches: int
    matches: list[SearchMatch]

