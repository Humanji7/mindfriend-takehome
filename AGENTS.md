# MindFriend Take-Home Instructions

## Mission

Build a small but credible AI-driven operations agent for the MindFriend take-home.

The assignment has two required flows:

1. Jira ticket reaches `Done` -> send short notification to Google Chat or email alias.
2. User asks for a past task/problem in natural language -> return semantically relevant Jira ticket(s).

This repository is for execution, not brainstorming-only output. Favor a lean, reliable implementation over broad platform complexity.

## Primary Deliverables

- working codebase;
- architecture diagram or text flow;
- tool rationale;
- edge case handling notes;
- time tracking report artifact.

## Recommended Implementation Shape

Prefer a compact Python-first solution:

- Python 3.12
- FastAPI for webhook endpoint and lightweight query endpoint
- Jira REST API for issue events and ticket retrieval
- Google Chat API as the primary notification target for the MVP demo
- Email alias delivery as an optional fallback or follow-up extension
- embeddings API plus a local vector store for semantic search
- a minimal LLM summarization step for notification copy, with deterministic fallback to snippet formatting
- CLI and/or minimal web form for search interface

## Decision Rules

- Prefer fewer moving parts over platform sprawl.
- Prefer direct APIs over no-code tools unless a no-code step is clearly better for reliability or speed.
- Prefer a local, inspectable vector store over external infra for a take-home.
- Prefer explicit retries, logging, and graceful fallbacks over clever abstractions.
- Keep the semantic search pipeline simple and explainable.
- Treat Google Chat as the only required delivery channel for the first passing version.
- Make the `LLM API` explicit in the architecture: embeddings are mandatory, generative summarization is minimal and optional at runtime.

## Suggested Repository Layout

- `app/main.py` - FastAPI entrypoint
- `app/config.py` - environment/config loading
- `app/routes/webhooks.py` - Jira webhook receiver
- `app/routes/search.py` - semantic search endpoint
- `app/services/jira_client.py` - Jira access
- `app/services/notifier.py` - Google Chat / Gmail notification logic
- `app/services/indexer.py` - ticket ingestion and embedding/index refresh
- `app/services/search_service.py` - semantic retrieval
- `app/models/` - request/response schemas
- `app/store/` - vector store adapter and metadata store
- `scripts/bootstrap_index.py` - initial Jira sync/index build
- `scripts/demo_query.py` - local semantic query demo
- `tests/` - focused unit/integration tests
- `docs/architecture.md` - final architecture + tool rationale + edge cases
- `docs/time-report.md` - human-readable summary of a tool-generated time report
- `artifacts/time-report/` - exported report or screenshots from Clockify or another time tracking tool

## Hard Requirements

- Notification must include a brief ticket description and a link.
- Search must be semantic, not plain keyword matching.
- Must handle missing description and rate limit scenarios explicitly.
- Must show the `LLM API` in the architecture and explain where prompt-based summarization fits or why a deterministic fallback is used.
- Output should be understandable by a non-specialist reviewer.

## Non-Goals

- No enterprise auth system.
- No heavy frontend.
- No multi-tenant design unless needed for explanation.
- No overbuilt agent framework if a direct pipeline is enough.

## Testing Standard

- Test webhook payload parsing.
- Test done-event filtering logic.
- Test notification formatting.
- Test terminal-state detection using Jira `statusCategory=done` and config override behavior.
- Test indexing when description is missing.
- Test retrieval ranking on at least one paraphrase example.
- Test rate-limit retry or fallback path.

## Definition of Done

The repo is ready only when:

- the done-notification flow can be demonstrated end-to-end;
- semantic search returns sensible results for paraphrased queries;
- the architecture clearly shows Jira Webhooks, an LLM API, a vector store, and Google Chat interaction;
- docs explain architecture in plain English;
- edge cases are written down, not just implied;
- a tool-generated time report artifact is attached;
- the submission can be walked through in under 5 minutes.

## Subagent Policy

Use subagents only with disjoint write scopes.

Preferred execution split:

- Agent A: scaffold + config + shared schemas
- Agent B: Jira webhook + notification flow
- Agent C: indexing + semantic retrieval
- Agent D: docs + architecture + verification artifacts

Do not let multiple agents edit the same service module at the same time.
