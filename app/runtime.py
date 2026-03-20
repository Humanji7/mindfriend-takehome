from __future__ import annotations

from typing import Any

from app.config import Settings
from app.services.indexer import JiraIndexer
from app.services.jira_client import JiraClient
from app.services.llm_client import NullLLMClient, OpenAILLMClient
from app.services.notifier import NotificationFormatter, NotifierService
from app.services.search_service import SearchService
from app.store.vector_store import LocalVectorStore


def build_services(settings: Settings, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    settings.ensure_runtime_paths()

    llm_client = OpenAILLMClient(settings) if settings.openai_api_key else NullLLMClient()
    vector_store = LocalVectorStore(settings.vector_store_path)
    jira_client = JiraClient(settings)
    formatter = NotificationFormatter(settings, llm_client)
    notifier = NotifierService(settings)
    search_service = SearchService(settings, llm_client, vector_store)
    indexer = JiraIndexer(settings, jira_client, llm_client, vector_store)

    services = {
        "jira_client": jira_client,
        "llm_client": llm_client,
        "vector_store": vector_store,
        "formatter": formatter,
        "notifier": notifier,
        "search": search_service,
        "indexer": indexer,
    }
    if overrides:
        services.update(overrides)
    return services

