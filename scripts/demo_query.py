from __future__ import annotations

import sys

from app.config import get_settings
from app.runtime import build_services


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: uv run python scripts/demo_query.py '<query>'")

    settings = get_settings()
    services = build_services(settings)
    search_service = services["search"]
    response = search_service.search(sys.argv[1])
    if not response.matches:
        print(
            "No indexed tickets cleared the semantic similarity threshold. "
            "This usually means the project data is too sparse or unrelated to the query."
        )
        return

    for match in response.matches:
        print(f"{match.ticket_key} | {match.title} | score={match.score}")
        print(f"  reason: {match.reason}")
        print(f"  link:   {match.url}")


if __name__ == "__main__":
    main()
