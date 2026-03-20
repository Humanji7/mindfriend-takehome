from __future__ import annotations

from app.config import Settings
from app.models.search import SearchMatch, SearchResponse
from app.services.llm_client import EmbeddingClient
from app.store.vector_store import LocalVectorStore


class SearchService:
    def __init__(
        self,
        settings: Settings,
        llm_client: EmbeddingClient,
        vector_store: LocalVectorStore,
    ) -> None:
        self.settings = settings
        self.llm_client = llm_client
        self.vector_store = vector_store

    def search(self, query: str, top_k: int | None = None) -> SearchResponse:
        limit = top_k or self.settings.search_top_k
        records = self.vector_store.load()
        if not records:
            return SearchResponse(query=query, total_matches=0, matches=[])

        query_embedding = self.llm_client.embed_text(query)
        raw_matches = self.vector_store.search(query_embedding, limit)
        matches = [
            (record, score)
            for record, score in raw_matches
            if score >= self.settings.search_min_score
        ]
        response_matches = [
            SearchMatch(
                ticket_key=record.ticket_key,
                title=record.title,
                description=record.description,
                url=record.url,
                score=round(score, 4),
                reason="Matched by embedding similarity across indexed Jira ticket text.",
            )
            for record, score in matches
        ]
        return SearchResponse(
            query=query,
            total_matches=len(response_matches),
            matches=response_matches,
        )
