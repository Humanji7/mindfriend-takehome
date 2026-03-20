from __future__ import annotations

import json
import math
from pathlib import Path

from app.models.jira import IndexedTicket


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    numerator = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


class LocalVectorStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> list[IndexedTicket]:
        if not self.path.exists():
            return []
        data = json.loads(self.path.read_text() or "[]")
        return [IndexedTicket.model_validate(item) for item in data]

    def save(self, records: list[IndexedTicket]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = [record.model_dump(mode="json") for record in records]
        self.path.write_text(json.dumps(payload, indent=2))

    def upsert(self, records: list[IndexedTicket]) -> None:
        existing = {record.ticket_key: record for record in self.load()}
        for record in records:
            existing[record.ticket_key] = record
        ordered = sorted(existing.values(), key=lambda item: item.ticket_key)
        self.save(ordered)

    def search(self, query_embedding: list[float], limit: int) -> list[tuple[IndexedTicket, float]]:
        scored = [
            (record, cosine_similarity(query_embedding, record.embedding))
            for record in self.load()
        ]
        ranked = sorted(scored, key=lambda item: item[1], reverse=True)
        return ranked[:limit]

