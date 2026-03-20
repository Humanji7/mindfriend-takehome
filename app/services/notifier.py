from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

import httpx

from app.config import Settings
from app.models.jira import JiraTicket, NotificationMessage
from app.services.jira_events import FALLBACK_DESCRIPTION
from app.services.llm_client import EmbeddingClient

logger = logging.getLogger(__name__)


class DeliveryResult(dict):
    @property
    def delivered(self) -> bool:
        return bool(self.get("delivered"))


class NotificationFormatter:
    def __init__(self, settings: Settings, llm_client: EmbeddingClient) -> None:
        self.settings = settings
        self.llm_client = llm_client

    def format_ticket_notification(self, ticket: JiraTicket) -> NotificationMessage:
        brief = self.llm_client.summarize_ticket(
            ticket.summary,
            ticket.description,
            self.settings.notification_max_summary_chars,
        )
        if not brief:
            brief = self._snippet(ticket.description)

        body = "\n".join(
            [
                f"Ticket {ticket.key} reached Done.",
                f"Title: {ticket.summary}",
                f"Brief: {brief}",
                f"Link: {ticket.url}",
            ]
        )
        subject = f"[MindFriend] {ticket.key} reached Done"
        return NotificationMessage(
            subject=subject,
            body=body,
            ticket_key=ticket.key,
            ticket_url=ticket.url,
            brief_description=brief,
        )

    def _snippet(self, description: str) -> str:
        text = (description or FALLBACK_DESCRIPTION).strip()
        clipped = text[: self.settings.notification_max_summary_chars].strip()
        if len(text) > len(clipped):
            clipped = f"{clipped.rstrip('.')}..."
        return clipped or FALLBACK_DESCRIPTION


class NotifierService:
    def __init__(self, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.request_timeout_seconds)

    def send(self, message: NotificationMessage) -> DeliveryResult:
        errors: list[str] = []
        if self.settings.google_chat_webhook_url:
            try:
                self._send_google_chat(message)
                return DeliveryResult(channel="google_chat", delivered=True)
            except Exception as exc:  # pragma: no cover - depends on external network path
                logger.exception("Google Chat delivery failed")
                errors.append(str(exc))

        if self.settings.email_fallback_enabled:
            try:
                self._send_email(message)
                return DeliveryResult(
                    channel="email",
                    delivered=True,
                    fallback_used=bool(self.settings.google_chat_webhook_url),
                )
            except Exception as exc:
                logger.exception("Email delivery failed")
                errors.append(str(exc))

        detail = " | ".join(errors) if errors else "No notification channel configured"
        return DeliveryResult(channel="none", delivered=False, detail=detail)

    def _send_google_chat(self, message: NotificationMessage) -> None:
        response = self.client.post(
            self.settings.google_chat_webhook_url,
            json={"text": message.body},
        )
        response.raise_for_status()

    def _send_email(self, message: NotificationMessage) -> None:
        email_message = EmailMessage()
        email_message["Subject"] = message.subject
        email_message["From"] = self.settings.gmail_sender or self.settings.smtp_username
        email_message["To"] = self.settings.gmail_recipient
        email_message.set_content(message.body)

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username and self.settings.smtp_password:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(email_message)

