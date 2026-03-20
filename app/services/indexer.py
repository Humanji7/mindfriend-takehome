from __future__ import annotations

import json
from typing import Any, Iterable, Mapping

from app.config import Settings
from app.models.jira import IndexedTicket
from app.services.jira_events import FALLBACK_DESCRIPTION, adf_to_text
from app.services.jira_client import JiraClient
from app.services.llm_client import EmbeddingClient
from app.store.vector_store import LocalVectorStore


class JiraIndexer:
    def __init__(
        self,
        settings: Settings,
        jira_client: JiraClient,
        llm_client: EmbeddingClient,
        vector_store: LocalVectorStore,
    ) -> None:
        self.settings = settings
        self.jira_client = jira_client
        self.llm_client = llm_client
        self.vector_store = vector_store

    def normalize_issue(self, issue: Mapping[str, Any]) -> IndexedTicket:
        fields = issue.get("fields", {})
        summary = str(fields.get("summary", "")).strip() or str(issue.get("key", "")).strip()
        description = adf_to_text(fields.get("description")) or FALLBACK_DESCRIPTION
        status = fields.get("status", {}) if isinstance(fields.get("status"), Mapping) else {}
        labels = fields.get("labels", [])
        ticket_key = str(issue.get("key", "")).strip()
        searchable_text = "\n".join(
            [
                f"Ticket: {ticket_key}",
                f"Title: {summary}",
                f"Description: {description}",
                f"Status: {status.get('name', '')}",
                f"Labels: {', '.join(labels) if isinstance(labels, list) else ''}",
            ]
        )
        return IndexedTicket(
            ticket_key=ticket_key,
            title=summary,
            description=description,
            status_name=str(status.get("name", "")).strip(),
            labels=list(labels) if isinstance(labels, list) else [],
            url=f"{self.settings.atlassian_url.rstrip('/')}/browse/{ticket_key}",
            searchable_text=searchable_text,
        )

    def build_index(self, issues: Iterable[Mapping[str, Any]]) -> list[IndexedTicket]:
        records = [self.normalize_issue(issue) for issue in issues]
        if not records:
            return []
        embeddings = self.llm_client.embed_texts([record.searchable_text for record in records])
        return [
            record.model_copy(update={"embedding": embedding})
            for record, embedding in zip(records, embeddings, strict=True)
        ]

    def sync_project_issues(self) -> list[IndexedTicket]:
        issues = self.jira_client.search_project_issues()
        records = self.build_index(issues)
        self.vector_store.upsert(records)
        self._write_snapshot(records)
        return records

    def _write_snapshot(self, records: list[IndexedTicket]) -> None:
        payload = [
            {
                "ticket_key": record.ticket_key,
                "title": record.title,
                "description": record.description,
                "status_name": record.status_name,
                "labels": record.labels,
                "url": record.url,
            }
            for record in records
        ]
        self.settings.index_data_path.write_text(json.dumps(payload, indent=2))
