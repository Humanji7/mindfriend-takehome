# Submission Walkthrough

This is the primary reviewer-facing walkthrough for the MindFriend take-home.

## What Is Implemented

- Jira `Done` transition intake through a FastAPI webhook endpoint
- Notification delivery with a short description and a ticket link
- Semantic Jira ticket search using OpenAI embeddings and a local JSON vector store
- Explicit handling for missing descriptions, terminal-state filtering, and Jira rate limits

## What Was Live-Verified

- Live Jira indexing against a real project
- Live semantic retrieval against real Jira tickets with meaningful descriptions
- Live `Done -> notification` delivery through the email path

Google Chat remains in the architecture because it is the intended channel from the assignment, but the active workspace blocks that path. The verified runtime delivery path is SMTP email.

## Evidence Artifacts

- Search evidence: `artifacts/demo/search-demo.txt` (public redaction applied to live tenant and ticket text)
- Notification evidence: `artifacts/demo/notification-demo.md` (public redaction applied to live tenant and ticket text)
- Architecture and tool rationale: `docs/architecture.md`
- Time report summary: `docs/time-report.md`
- Toggl Track CSV time report artifact: `artifacts/time-report/mindfriend-time-report.csv`

## 5-Minute Reviewer Path

1. Install dependencies:

```bash
uv sync --extra dev
```

2. Run tests:

```bash
uv run pytest
uv run ruff check app tests scripts
```

Expected result:

- all tests pass
- Ruff returns `All checks passed!`

3. Inspect the captured live evidence:

- `artifacts/demo/search-demo.txt`
- `artifacts/demo/notification-demo.md`
- `docs/architecture.md`

Expected result:

- search evidence shows live retrieval scores and match ordering with the tenant and ticket text redacted for public sharing
- notification evidence shows a live `Done -> email` result with the tenant and ticket text redacted for public sharing
- architecture doc explains where the LLM API, vector store, Jira webhook, and delivery adapter fit

4. Optional: start the API and verify the health endpoint:

```bash
uv run uvicorn app.main:app --reload
curl http://127.0.0.1:8000/health
```

Expected result:

- `{"status":"ok","environment":"development"}`
- `POST /search` returns an empty result until a local index exists
- `POST /webhooks/jira` returns `503` until `JIRA_WEBHOOK_SECRET` is configured

## Credentialed Live Re-Run

Use this only if `.env` is populated with working Jira, OpenAI, and notification credentials.

1. Rebuild the Jira index:

```bash
uv run python scripts/bootstrap_index.py
```

Expected result:

- the script reports the number of indexed Jira tickets

2. Verify semantic retrieval:

```bash
uv run python scripts/demo_query.py "Did we ever fix that weird login lag on mobile?"
uv run python scripts/demo_query.py "Have we dealt with webhook calls failing and needing retries?"
uv run python scripts/demo_query.py "Did we already solve slow invoice exports for big customers?"
```

Expected top-1 matches:

- a mobile-login-related ticket for the mobile login query
- a webhook-retries-related ticket for the webhook retries query
- an invoice-export-related ticket for the invoice export query

3. Verify the notification flow:

- Move a Jira ticket into `Done`
- The webhook should hit `/webhooks/jira`
- The verified runtime path sends an email notification containing:
  - ticket key
  - title
  - brief description
  - ticket link

## Reviewer Notes

- The semantic search is intentionally simple and inspectable: embeddings plus cosine similarity over a local JSON store.
- The notification formatter uses a minimal optional LLM summary step, but the runtime remains reliable via deterministic fallback.
- Use this file, `README.md`, and `docs/architecture.md` as the reviewer-facing source of truth.
