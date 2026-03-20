from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    public_base_url: str = "http://localhost:8000"

    atlassian_url: str = ""
    atlassian_email: str = ""
    atlassian_api_token: str = ""
    atlassian_project_key: str = ""
    jira_webhook_secret: str | None = None
    jira_done_status_names: str = ""

    google_chat_webhook_url: str | None = None
    email_fallback_enabled: bool = True
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    gmail_sender: str = ""
    gmail_recipient: str = ""

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"
    openai_summary_model: str = "gpt-4.1-mini"
    notification_use_llm_summary: bool = False
    notification_max_summary_chars: int = 180

    search_top_k: int = 3
    search_min_score: float = 0.2
    vector_store_path: Path = Field(default_factory=lambda: Path("data/vector_store.json"))
    index_data_path: Path = Field(default_factory=lambda: Path("data/index_snapshot.json"))

    request_timeout_seconds: float = 20.0
    retry_max_attempts: int = 3
    retry_backoff_seconds: float = 1.0

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @property
    def done_status_overrides(self) -> set[str]:
        names = [item.strip().lower() for item in self.jira_done_status_names.split(",")]
        return {item for item in names if item}

    def ensure_runtime_paths(self) -> None:
        self.vector_store_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_data_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
