from __future__ import annotations

from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import Settings  # noqa: E402


def build_settings(tmp_path: Path, **overrides) -> Settings:
    values = {
        "app_env": "test",
        "log_level": "INFO",
        "public_base_url": "http://localhost:8000",
        "atlassian_url": "https://example.atlassian.net",
        "atlassian_email": "test@example.com",
        "atlassian_api_token": "token",
        "atlassian_project_key": "MIND",
        "jira_webhook_secret": "secret123",
        "email_fallback_enabled": True,
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_username": "bot@example.com",
        "smtp_password": "password",
        "smtp_use_tls": True,
        "gmail_sender": "bot@example.com",
        "gmail_recipient": "ops@example.com",
        "notification_use_llm_summary": False,
        "notification_max_summary_chars": 120,
        "search_top_k": 3,
        "search_min_score": 0.2,
        "vector_store_path": tmp_path / "vector_store.json",
        "index_data_path": tmp_path / "index_snapshot.json",
        "retry_backoff_seconds": 0.0,
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return build_settings(tmp_path)
