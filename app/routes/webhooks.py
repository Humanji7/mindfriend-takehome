from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, Request

from app.services.jira_events import parse_done_ticket

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/jira")
def receive_jira_webhook(
    payload: dict[str, Any],
    request: Request,
    secret: str | None = Query(default=None),
    header_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    settings = request.app.state.settings
    expected_secret = settings.jira_webhook_secret
    if not expected_secret:
        raise HTTPException(status_code=503, detail="Webhook secret is not configured")
    if expected_secret not in {secret, header_secret}:
        raise HTTPException(status_code=403, detail="Invalid webhook secret")

    try:
        ticket = parse_done_ticket(payload, settings.atlassian_url, settings.done_status_overrides)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if ticket is None:
        return {"status": "ignored", "reason": "not_done_transition"}

    formatter = request.app.state.services["formatter"]
    notifier = request.app.state.services["notifier"]
    message = formatter.format_ticket_notification(ticket)
    delivery = notifier.send(message)
    delivered = delivery.delivered if hasattr(delivery, "delivered") else bool(delivery.get("delivered"))
    return {
        "status": "processed" if delivered else "failed",
        "ticket_key": ticket.key,
        "channel": delivery.get("channel"),
        "brief_description": message.brief_description,
        "detail": delivery.get("detail"),
    }
