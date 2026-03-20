from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class JiraClient:
    def __init__(
        self,
        settings: Settings,
        client: httpx.Client | None = None,
        sleep_fn=time.sleep,
    ) -> None:
        self.settings = settings
        self.sleep_fn = sleep_fn
        if client is not None:
            self.client = client
        else:
            self.client = httpx.Client(
                base_url=settings.atlassian_url.rstrip("/"),
                auth=(settings.atlassian_email, settings.atlassian_api_token),
                timeout=settings.request_timeout_seconds,
                headers={"Accept": "application/json"},
            )

    def fetch_issue(self, issue_key: str) -> dict[str, Any]:
        response = self._request("GET", f"/rest/api/3/issue/{issue_key}")
        return response.json()

    def search_project_issues(self, max_results: int = 100) -> list[dict[str, Any]]:
        jql = f"project = {self.settings.atlassian_project_key} ORDER BY updated DESC"
        issues: list[dict[str, Any]] = []
        start_at = 0
        endpoint = "/rest/api/3/search"
        while True:
            try:
                response = self._request(
                    "GET",
                    endpoint,
                    params={
                        "jql": jql,
                        "maxResults": max_results,
                        "startAt": start_at,
                        "fields": "summary,description,status,labels",
                    },
                )
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 410 and endpoint == "/rest/api/3/search":
                    endpoint = "/rest/api/3/search/jql"
                    continue
                raise
            payload = response.json()
            batch = payload.get("issues", [])
            if not isinstance(batch, list):
                break
            issues.extend(batch)
            total = int(payload.get("total", len(issues)))
            start_at += len(batch)
            if not batch or start_at >= total:
                break
        return issues

    def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        delay = self.settings.retry_backoff_seconds
        for attempt in range(1, self.settings.retry_max_attempts + 1):
            response = self.client.request(method, url, **kwargs)
            if response.status_code == 429 and attempt < self.settings.retry_max_attempts:
                retry_after = response.headers.get("Retry-After")
                wait_seconds = float(retry_after) if retry_after else delay
                logger.warning("Jira rate limited, retrying attempt %s", attempt)
                self.sleep_fn(wait_seconds)
                delay *= 2
                continue
            response.raise_for_status()
            return response
        raise RuntimeError("Jira request failed after exhausting retries")
