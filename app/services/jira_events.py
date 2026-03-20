from __future__ import annotations

from typing import Any, Mapping

from app.models.jira import JiraTicket

FALLBACK_DESCRIPTION = "No description was provided in Jira."


def adf_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [adf_to_text(item) for item in value]
        return " ".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        parts: list[str] = []
        text = value.get("text")
        if isinstance(text, str):
            parts.append(text.strip())
        content = value.get("content")
        if isinstance(content, list):
            nested = adf_to_text(content)
            if nested:
                parts.append(nested)
        return " ".join(part for part in parts if part).strip()
    return str(value).strip()


def get_issue(payload: Mapping[str, Any]) -> Mapping[str, Any] | None:
    issue = payload.get("issue")
    if isinstance(issue, Mapping):
        return issue
    return None


def has_status_transition(payload: Mapping[str, Any]) -> bool:
    changelog = payload.get("changelog")
    if not isinstance(changelog, Mapping):
        return False
    items = changelog.get("items")
    if not isinstance(items, list):
        return False
    for item in items:
        if isinstance(item, Mapping) and str(item.get("field", "")).lower() == "status":
            return True
    return False


def is_terminal_status(payload: Mapping[str, Any], done_status_overrides: set[str]) -> bool:
    issue = get_issue(payload)
    if issue is None:
        return False
    fields = issue.get("fields")
    if not isinstance(fields, Mapping):
        return False
    status = fields.get("status")
    if not isinstance(status, Mapping):
        return False

    status_category = status.get("statusCategory")
    if isinstance(status_category, Mapping):
        category_key = str(status_category.get("key", "")).lower()
        if category_key == "done":
            return True

    status_name = str(status.get("name", "")).strip().lower()
    return bool(status_name and status_name in done_status_overrides)


def parse_done_ticket(
    payload: Mapping[str, Any],
    atlassian_url: str,
    done_status_overrides: set[str],
) -> JiraTicket | None:
    issue = get_issue(payload)
    if issue is None:
        raise ValueError("Webhook payload does not contain an issue")
    if not has_status_transition(payload):
        return None
    if not is_terminal_status(payload, done_status_overrides):
        return None

    fields = issue.get("fields")
    if not isinstance(fields, Mapping):
        raise ValueError("Webhook payload contains an invalid issue.fields object")
    status = fields.get("status") if isinstance(fields.get("status"), Mapping) else {}
    description = adf_to_text(fields.get("description")) or FALLBACK_DESCRIPTION
    issue_key = str(issue.get("key", "")).strip()
    if not issue_key:
        raise ValueError("Webhook payload does not contain issue.key")

    return JiraTicket(
        key=issue_key,
        summary=str(fields.get("summary", "")).strip() or issue_key,
        description=description,
        status_name=str(status.get("name", "")).strip() or None,
        status_category=(
            str(status.get("statusCategory", {}).get("key", "")).strip() or None
            if isinstance(status, Mapping)
            else None
        ),
        labels=list(fields.get("labels", [])) if isinstance(fields.get("labels"), list) else [],
        url=f"{atlassian_url.rstrip('/')}/browse/{issue_key}",
    )

