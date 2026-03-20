from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.routes.search import router as search_router
from app.routes.webhooks import router as webhooks_router
from app.runtime import build_services


def create_app(
    settings: Settings | None = None,
    service_overrides: dict[str, Any] | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    logging.basicConfig(level=resolved_settings.log_level.upper())

    application = FastAPI(title="MindFriend Agent", version="0.1.0")
    application.state.settings = resolved_settings
    application.state.services = build_services(resolved_settings, service_overrides)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "environment": resolved_settings.app_env}

    application.include_router(webhooks_router)
    application.include_router(search_router)
    return application


app = create_app()
