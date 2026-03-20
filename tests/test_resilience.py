from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from app.main import create_app
from app.models.jira import IndexedTicket
from app.services.jira_client import JiraClient
from app.store.vector_store import LocalVectorStore


def test_jira_client_retries_rate_limit(settings) -> None:
    requests_seen = {"count": 0}
    sleeps: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests_seen["count"] += 1
        if requests_seen["count"] == 1:
            return httpx.Response(status_code=429, headers={"Retry-After": "0"})
        return httpx.Response(status_code=200, json={"issues": [], "total": 0})

    client = httpx.Client(
        base_url=settings.atlassian_url,
        transport=httpx.MockTransport(handler),
    )
    jira_client = JiraClient(settings, client=client, sleep_fn=sleeps.append)

    issues = jira_client.search_project_issues()

    assert issues == []
    assert requests_seen["count"] == 2
    assert sleeps == [0.0]


def test_invalid_webhook_payload_is_rejected(settings) -> None:
    app = create_app(settings=settings)
    client = TestClient(app)

    response = client.post("/webhooks/jira?secret=secret123", json={})

    assert response.status_code == 400
    assert "issue" in response.json()["detail"].lower()


def test_webhook_requires_configured_secret(settings) -> None:
    settings.jira_webhook_secret = None
    app = create_app(settings=settings)
    client = TestClient(app)

    response = client.post("/webhooks/jira", json={})

    assert response.status_code == 503
    assert "secret" in response.json()["detail"].lower()


def test_jira_client_falls_back_to_search_jql_after_410(settings) -> None:
    requested_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested_paths.append(request.url.path)
        if request.url.path.endswith("/search"):
            return httpx.Response(status_code=410)
        return httpx.Response(status_code=200, json={"issues": [], "total": 0})

    client = httpx.Client(
        base_url=settings.atlassian_url,
        transport=httpx.MockTransport(handler),
    )
    jira_client = JiraClient(settings, client=client, sleep_fn=lambda _: None)

    issues = jira_client.search_project_issues()

    assert issues == []
    assert requested_paths == ["/rest/api/3/search", "/rest/api/3/search/jql"]


def test_search_returns_503_when_embeddings_are_not_configured(settings) -> None:
    store = LocalVectorStore(settings.vector_store_path)
    store.save(
        [
            IndexedTicket(
                ticket_key="MIND-99",
                title="Fix mobile login lag",
                description="Users reported slow login on mobile.",
                status_name="Done",
                labels=["mobile"],
                url="https://example.atlassian.net/browse/MIND-99",
                searchable_text="Fix mobile login lag users reported slow login on mobile",
                embedding=[1.0, 0.0],
            )
        ]
    )

    app = create_app(settings=settings)
    client = TestClient(app)

    response = client.post("/search", json={"query": "slow mobile login"})

    assert response.status_code == 503
    assert "openai_api_key" in response.json()["detail"].lower()
