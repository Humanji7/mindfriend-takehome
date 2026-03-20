from __future__ import annotations

from app.config import get_settings
from app.runtime import build_services


def main() -> None:
    settings = get_settings()
    services = build_services(settings)
    indexer = services["indexer"]
    records = indexer.sync_project_issues()
    print(f"Indexed {len(records)} Jira tickets into {settings.vector_store_path}")


if __name__ == "__main__":
    main()

