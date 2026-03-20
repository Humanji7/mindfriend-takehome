from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.search import SearchRequest, SearchResponse
from app.services.llm_client import SemanticSearchUnavailableError

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search_tickets(payload: SearchRequest, request: Request) -> SearchResponse:
    service = request.app.state.services["search"]
    try:
        return service.search(payload.query, payload.top_k)
    except SemanticSearchUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
