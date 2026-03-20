from __future__ import annotations

import logging
import time
from collections.abc import Sequence
from typing import Protocol

from app.config import Settings

logger = logging.getLogger(__name__)


class EmbeddingClient(Protocol):
    def embed_text(self, text: str) -> list[float]:
        ...

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        ...

    def summarize_ticket(self, title: str, description: str, max_chars: int) -> str | None:
        ...


class NullLLMClient:
    def embed_text(self, text: str) -> list[float]:
        raise RuntimeError("OPENAI_API_KEY is required for semantic search")

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        raise RuntimeError("OPENAI_API_KEY is required for semantic search")

    def summarize_ticket(self, title: str, description: str, max_chars: int) -> str | None:
        return None


class OpenAILLMClient:
    def __init__(self, settings: Settings) -> None:
        from openai import OpenAI

        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def embed_text(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        response = self._with_retry(
            lambda: self.client.embeddings.create(
                model=self.settings.openai_embedding_model,
                input=list(texts),
            )
        )
        return [list(item.embedding) for item in response.data]

    def summarize_ticket(self, title: str, description: str, max_chars: int) -> str | None:
        if not self.settings.notification_use_llm_summary:
            return None
        prompt = (
            "Write one plain-English sentence for an operations update. "
            f"Keep it under {max_chars} characters. "
            "Mention what changed, avoid hype, and do not invent details.\n\n"
            f"Title: {title}\nDescription: {description}"
        )
        try:
            response = self._with_retry(
                lambda: self.client.responses.create(
                    model=self.settings.openai_summary_model,
                    input=prompt,
                )
            )
        except Exception:  # pragma: no cover - fallback is the primary behavior in tests
            logger.exception("LLM summary generation failed; using deterministic fallback")
            return None

        output = getattr(response, "output_text", "") or ""
        summary = output.strip()
        if not summary:
            return None
        return summary[:max_chars].rstrip()

    def _with_retry(self, operation):
        attempt = 0
        delay = self.settings.retry_backoff_seconds
        while True:
            attempt += 1
            try:
                return operation()
            except Exception as exc:  # pragma: no cover - exercised via client behavior, not SDK internals
                status_code = getattr(exc, "status_code", None)
                if status_code != 429 or attempt >= self.settings.retry_max_attempts:
                    raise
                logger.warning("OpenAI rate limited, retrying attempt %s", attempt)
                time.sleep(delay)
                delay *= 2

