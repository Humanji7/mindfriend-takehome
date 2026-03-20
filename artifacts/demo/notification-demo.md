# Notification Demo

This artifact records the live-verified notification result for the MindFriend take-home.

## Verification Context

- Date: 2026-03-20
- Jira ticket moved to `Done`: `[redacted live ticket key]`
- Verified delivery path: SMTP email
- Google Chat was not the live delivery path because the active workspace blocks the incoming webhook flow

Tenant hostname, live ticket title, and live ticket description are redacted in the public repo copy of this artifact.

## Observed Email

Subject:

```text
[MindFriend] [redacted live ticket key] reached Done
```

Body:

```text
Ticket [redacted live ticket key] reached Done.
Title: [redacted live Jira title]
Brief: [redacted live Jira summary]
Link: https://<redacted-jira-host>/browse/[redacted-live-ticket-key]
```

## Assignment Requirement Check

The delivered notification includes:

- a brief ticket description
- a direct link to the Jira issue
- a compact format suitable for an operations update
