from __future__ import annotations

from app.models.jira import NotificationMessage
from app.services.notifier import NotifierService


def build_message() -> NotificationMessage:
    return NotificationMessage(
        subject="[MindFriend] KAN-10 reached Done",
        body="Ticket KAN-10 reached Done.",
        ticket_key="KAN-10",
        ticket_url="https://example.atlassian.net/browse/KAN-10",
        brief_description="A short deterministic summary.",
    )


def test_notifier_falls_back_to_email_after_google_chat_failure(settings) -> None:
    settings.google_chat_webhook_url = "https://chat.googleapis.com/example"
    settings.email_fallback_enabled = True
    notifier = NotifierService(settings)
    delivered_messages: list[NotificationMessage] = []

    def fail_google_chat(message: NotificationMessage) -> None:
        raise RuntimeError("blocked")

    def send_email(message: NotificationMessage) -> None:
        delivered_messages.append(message)

    notifier._send_google_chat = fail_google_chat  # type: ignore[method-assign]
    notifier._send_email = send_email  # type: ignore[method-assign]

    result = notifier.send(build_message())

    assert result["delivered"] is True
    assert result["channel"] == "email"
    assert result["fallback_used"] is True
    assert delivered_messages[0].ticket_key == "KAN-10"


def test_notifier_reports_failure_when_no_channel_succeeds(settings) -> None:
    settings.google_chat_webhook_url = None
    settings.email_fallback_enabled = False
    notifier = NotifierService(settings)

    result = notifier.send(build_message())

    assert result["delivered"] is False
    assert result["channel"] == "none"
    assert result["detail"] == "No notification channel configured"
