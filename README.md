# MindFriend Take-Home

For the fastest reviewer path, start with `docs/submission-walkthrough.md`.

Lean FastAPI implementation for the two required MindFriend flows:

1. Jira issue reaches `Done` and triggers a short notification.
2. A natural-language query retrieves semantically relevant Jira tickets.

## Runtime Shape

- FastAPI service for webhook intake and search
- Jira REST API for issue data
- OpenAI embeddings for semantic retrieval
- Local JSON vector store for an inspectable demo
- Email delivery via Gmail SMTP for the working MVP path
- Google Chat webhook kept as a supported adapter when available
- A minimum similarity threshold so search can return no match instead of misleading noise

## Python Support

The take-home targets Python 3.12+, but this repo is configured for `>=3.12,<3.15` because the current local environment is Python 3.14.

## Quick Start

1. Install dependencies:

```bash
uv sync --extra dev
```

2. Confirm `.env` is populated.
   The live Jira re-run commands below require Jira, OpenAI, and notification credentials.

3. Start the API:

```bash
uv run uvicorn app.main:app --reload
```

4. Build the first local semantic index:

```bash
uv run python scripts/bootstrap_index.py
```

5. Query the index:

```bash
uv run python scripts/demo_query.py "have we fixed slow mobile login before?"
```

If the Jira project only contains placeholder tickets or missing descriptions, the search flow now returns no matches instead of inventing a low-confidence result. The positive paraphrase case is covered in `tests/test_search.py`.

## Reviewer Path

- Zero-config review: read `docs/submission-walkthrough.md`, inspect `artifacts/demo/`, and run `uv run pytest` plus `uv run ruff check app tests scripts`.
- Credentialed live re-run: populate `.env`, rebuild the Jira index, run semantic queries, and trigger a Jira `Done` event.

## API Endpoints

- `GET /health`
- `POST /webhooks/jira`
- `POST /search`

## Jira Webhook Setup

Once the app is running locally, expose it with:

```bash
ngrok http 8000
```

Then set `PUBLIC_BASE_URL` and create a Jira webhook pointing to:

```text
https://<public-base-url>/webhooks/jira?secret=<JIRA_WEBHOOK_SECRET>
```

`JIRA_WEBHOOK_SECRET` is required. The webhook endpoint rejects requests until the shared secret is configured.

## Delivery Behavior

- If `GOOGLE_CHAT_WEBHOOK_URL` is present, the service tries Google Chat first.
- If Google Chat is unavailable or unset and `EMAIL_FALLBACK_ENABLED=true`, the service sends the notification via SMTP email.
- Notification copy uses an optional LLM summary step when enabled. Otherwise it falls back to a deterministic description snippet.

## Test Commands

```bash
uv run pytest
```
