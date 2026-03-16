# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI Email Triage Agent — a scheduled Python tool that reads unread emails from Gmail or Outlook each morning, triages them via hardcoded rules + Claude API, and sends an HTML digest email via Resend. Read-only inbox access; no write actions. Runs daily via GitHub Actions cron.

## Commands

```bash
pip install -r requirements.txt   # Install dependencies
python main.py                    # Run the agent locally (requires .env)
```

No test framework is specified yet. No linter/formatter is configured yet.

## Architecture

The pipeline runs as a single all-or-nothing pass: fetch → triage → compose → send.

**Entry point:** `main.py` orchestrates the full run.

**Pipeline stages:**

1. **Email Connectors** (`connectors/gmail.py`, `connectors/outlook.py`) — Fetch unread emails (max 50) from the configured provider. Gmail uses OAuth 2.0 delegated access; Outlook uses client credentials flow via Microsoft Graph. Thread grouping happens here (single digest row per conversation, using most recent message).

2. **Triage Engine** (`triage/rules.py`, `triage/ai.py`) — Two sequential stages. Stage 1 applies hardcoded rules (newsletter detection, noreply senders, spam signals, invoice/billing keywords, urgency flags). Stage 2 sends unmatched emails to Claude API (`claude-sonnet-4-6`) requesting JSON with `summary`, `action`, and `reason` fields.

3. **Digest Composer** (`digest/composer.py`) — Builds HTML email with action-sorted rows, colour-coded badges (Reply=blue, Archive=grey, Delete=red, Spam=orange), and deep links to original emails.

4. **Digest Sender** (`digest/sender.py`) — Delivers via Resend API.

## Key Design Decisions

- **No persistent state.** Email content lives in memory only for the run duration. Unread status comes from the provider's own flag — no separate tracking.
- **Rules before AI.** Hardcoded rules run first to reduce Claude API calls and cost.
- **Body truncation.** Email bodies are truncated to 500 words. HTML-only emails are stripped to plain text via BeautifulSoup before truncation.
- **All-or-nothing error handling.** Any step failure aborts the entire run; no partial digest is sent. Next run picks up the same unread emails since the inbox is never modified.
- **Zero digest.** If no unread emails, a congratulatory message is sent instead of an empty table.

## Tech Stack

- Python 3.11+
- `google-api-python-client` + `google-auth-oauthlib` (Gmail)
- `msgraph-sdk-python` (Outlook)
- `anthropic` (Claude API)
- `resend` (digest delivery)
- `beautifulsoup4` (HTML stripping)
- `python-dotenv` (local env loading)
- GitHub Actions for scheduling (`0 7 * * 1-5`)

## Environment Variables

Set in `.env` locally or GitHub Actions Secrets in CI. See `.env.example` for the full list. Key vars: `EMAIL_PROVIDER` (gmail|outlook), `ANTHROPIC_API_KEY`, `RESEND_API_KEY`, `DIGEST_RECIPIENT_EMAIL`, `DIGEST_SENDER_EMAIL`, plus provider-specific OAuth/credentials vars.
