from __future__ import annotations

import json

from app.services.indexer import JiraIndexer
from app.store.vector_store import LocalVectorStore


class FakeJiraClient:
    def __init__(self, issues) -> None:
        self.issues = issues

    def search_project_issues(self):
        return self.issues


class FakeEmbedder:
    def embed_text(self, text: str) -> list[float]:
        return [float(len(text)), 1.0]

    def embed_texts(self, texts) -> list[list[float]]:
        return [self.embed_text(text) for text in texts]

    def summarize_ticket(self, title: str, description: str, max_chars: int) -> str | None:
        return None


def test_indexer_handles_missing_description(settings) -> None:
    issues = [
        {
            "key": "MIND-7",
            "fields": {
                "summary": "Handle missing Jira descriptions",
                "description": None,
                "status": {"name": "Done"},
                "labels": ["ops"],
            },
        }
    ]
    store = LocalVectorStore(settings.vector_store_path)
    indexer = JiraIndexer(settings, FakeJiraClient(issues), FakeEmbedder(), store)

    records = indexer.sync_project_issues()

    assert len(records) == 1
    assert records[0].description == "No description was provided in Jira."
    saved = json.loads(settings.index_data_path.read_text())
    assert saved[0]["ticket_key"] == "MIND-7"
    assert store.load()[0].embedding


def test_indexer_handles_empty_issue_batches(settings) -> None:
    store = LocalVectorStore(settings.vector_store_path)
    indexer = JiraIndexer(settings, FakeJiraClient([]), FakeEmbedder(), store)

    records = indexer.sync_project_issues()

    assert records == []
    assert store.load() == []
    assert json.loads(settings.index_data_path.read_text()) == []
