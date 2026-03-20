from __future__ import annotations

from app.models.jira import IndexedTicket
from app.services.search_service import SearchService
from app.store.vector_store import LocalVectorStore


class SemanticFakeEmbedder:
    vocabulary = ["mobile", "login", "slow", "billing", "invoice", "webhook"]
    synonyms = {
        "phone": "mobile",
        "phones": "mobile",
        "sign": "login",
        "signin": "login",
        "sign-in": "login",
        "auth": "login",
        "sluggish": "slow",
        "latency": "slow",
    }

    def _normalize(self, text: str) -> list[str]:
        tokens = []
        for raw_token in text.lower().replace("-", " ").split():
            token = self.synonyms.get(raw_token, raw_token)
            tokens.append(token)
        return tokens

    def embed_text(self, text: str) -> list[float]:
        tokens = self._normalize(text)
        return [float(tokens.count(term)) for term in self.vocabulary]

    def embed_texts(self, texts) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def summarize_ticket(self, title: str, description: str, max_chars: int) -> str | None:
        return None


def test_search_returns_paraphrase_match(settings) -> None:
    store = LocalVectorStore(settings.vector_store_path)
    embedder = SemanticFakeEmbedder()
    records = [
        IndexedTicket(
            ticket_key="MIND-10",
            title="Fix slow mobile login",
            description="Users reported slow login on the mobile app.",
            status_name="Done",
            labels=["mobile"],
            url="https://example.atlassian.net/browse/MIND-10",
            searchable_text="Fix slow mobile login users reported slow login on the mobile app",
            embedding=embedder.embed_text(
                "Fix slow mobile login users reported slow login on the mobile app"
            ),
        ),
        IndexedTicket(
            ticket_key="MIND-11",
            title="Repair invoice export",
            description="CSV invoice export timed out for finance.",
            status_name="Done",
            labels=["finance"],
            url="https://example.atlassian.net/browse/MIND-11",
            searchable_text="Repair invoice export CSV invoice export timed out for finance",
            embedding=embedder.embed_text(
                "Repair invoice export CSV invoice export timed out for finance"
            ),
        ),
    ]
    store.upsert(records)
    service = SearchService(settings, embedder, store)

    response = service.search("Did we already fix sluggish phone sign in?")

    assert response.total_matches == 1
    assert response.matches[0].ticket_key == "MIND-10"
    assert response.matches[0].score >= settings.search_min_score


def test_search_filters_low_confidence_matches(settings) -> None:
    store = LocalVectorStore(settings.vector_store_path)
    embedder = SemanticFakeEmbedder()
    records = [
        IndexedTicket(
            ticket_key="MIND-12",
            title="Placeholder task",
            description="No description was provided in Jira.",
            status_name="Done",
            labels=[],
            url="https://example.atlassian.net/browse/MIND-12",
            searchable_text="Placeholder task No description was provided in Jira.",
            embedding=embedder.embed_text("Placeholder task No description was provided in Jira."),
        )
    ]
    store.upsert(records)
    service = SearchService(settings, embedder, store)

    response = service.search("quantum banana toaster outage")

    assert response.total_matches == 0
    assert response.matches == []
