from __future__ import annotations

import csv
from pathlib import Path


ENTRIES = [
    {
        "date": "2026-03-18",
        "task": "Assignment review, PDF alignment, architecture decisions",
        "hours": 1.8,
        "notes": "Validated deliverables and locked the lean FastAPI plus local vector store approach.",
    },
    {
        "date": "2026-03-19",
        "task": "Environment setup, credentials, delivery-path validation",
        "hours": 1.2,
        "notes": "Prepared Jira, OpenAI, SMTP, and confirmed Google Chat webhook restrictions.",
    },
    {
        "date": "2026-03-20",
        "task": "Implementation, tests, indexing flow, submission docs",
        "hours": 4.4,
        "notes": "Built the app, webhook flow, SMTP delivery, semantic search, fixtures, and docs.",
    },
]


def main() -> None:
    output_path = Path("artifacts/time-report/mindfriend-time-report.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="") as file_handle:
        writer = csv.DictWriter(file_handle, fieldnames=["date", "task", "hours", "notes"])
        writer.writeheader()
        writer.writerows(ENTRIES)

    total_hours = sum(entry["hours"] for entry in ENTRIES)
    print(f"Wrote {output_path} with {len(ENTRIES)} entries and {total_hours:.1f} total hours.")


if __name__ == "__main__":
    main()

