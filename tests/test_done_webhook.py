from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app
from app.models.jira import NotificationMessage
from app.services.llm_client import NullLLMClient
from app.services.notifier import NotificationFormatter
from tests.conftest import build_settings

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "jira"


class StubNotifier:
    def __init__(self) -> None:
        self.messages: list[NotificationMessage] = []

    def send(self, message: NotificationMessage):
        self.messages.append(message)
        return {"channel": "email", "delivered": True}


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text())


def test_ignore_non_done_transition(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    notifier = StubNotifier()
    app = create_app(
        settings=settings,
        service_overrides={
            "formatter": NotificationFormatter(settings, NullLLMClient()),
            "notifier": notifier,
        },
    )
    client = TestClient(app)

    response = client.post(
        "/webhooks/jira?secret=secret123",
        json=load_fixture("non-done-event.json"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
    assert notifier.messages == []


def test_done_webhook_formats_description_and_link(tmp_path: Path) -> None:
    settings = build_settings(tmp_path)
    notifier = StubNotifier()
    app = create_app(
        settings=settings,
        service_overrides={
            "formatter": NotificationFormatter(settings, NullLLMClient()),
            "notifier": notifier,
        },
    )
    client = TestClient(app)

    response = client.post(
        "/webhooks/jira?secret=secret123",
        json=load_fixture("done-event.json"),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    message = notifier.messages[0]
    assert "Brief:" in message.body
    assert "Link: https://example.atlassian.net/browse/MIND-42" in message.body
    assert "mobile login flow" in message.brief_description.lower()


def test_done_status_override_works_without_status_category_done(tmp_path: Path) -> None:
    payload = load_fixture("done-event.json")
    payload["issue"]["fields"]["status"]["statusCategory"]["key"] = "indeterminate"
    payload["issue"]["fields"]["status"]["name"] = "Closed"
    settings = build_settings(tmp_path, jira_done_status_names="Closed")
    notifier = StubNotifier()
    app = create_app(
        settings=settings,
        service_overrides={
            "formatter": NotificationFormatter(settings, NullLLMClient()),
            "notifier": notifier,
        },
    )
    client = TestClient(app)

    response = client.post("/webhooks/jira?secret=secret123", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert notifier.messages[0].ticket_key == "MIND-42"

