# AI Email Triage Agent

An AI-powered email assistant that reads your unread emails each morning, triages them using hardcoded rules + Claude AI, and sends you a clean HTML digest with an overview and per-email action recommendations.

Built with Python, the Anthropic Claude API, and GitHub Actions for fully automated daily runs.

![Python](https://img.shields.io/badge/Python-3.11+-3776ab?logo=python&logoColor=white)
![Claude API](https://img.shields.io/badge/Claude_API-Sonnet_4-d97706?logo=anthropic&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## How It Works

```
Fetch unread emails  -->  Triage (rules + AI)  -->  Generate overview  -->  Send HTML digest
```

1. **Fetch** — Connects to Gmail (OAuth 2.0) or Outlook (Microsoft Graph) and pulls up to 50 unread emails. Threads are grouped so you get one entry per conversation.

2. **Triage** — Two-stage classification:
   - **Rules engine** runs first — catches newsletters, noreply senders, spam signals, invoices, and urgent keywords. This reduces API calls and cost.
   - **Claude AI** handles the rest — returns a one-line summary, a recommended action (Reply / Archive / Delete / Spam), and a reason.

3. **Overview** — Claude generates a 3-5 sentence natural language summary of your entire inbox: what needs attention, recurring themes, and what can wait.

4. **Digest** — An HTML email is composed with the AI overview up top, followed by individual email cards sorted by priority. Each card has a colour-coded action badge and a deep link back to the original email. Delivered via Resend.

## Digest Preview

The digest email you receive contains:

- **Header** — Date, total unread count, action breakdown badges
- **AI Overview** — A conversational summary of your inbox today
- **Email Cards** — One per email, sorted by action priority (Reply first), each with:
  - Subject (linked to original email)
  - Sender and timestamp
  - AI-generated summary
  - Colour-coded action badge (Reply = blue, Archive = grey, Delete = red, Spam = orange)
  - "View email" deep link for a quick deep dive
- **Footer** — Direct link to your inbox

## Project Structure

```
email-triage-agent/
├── main.py                  # Entry point — orchestrates the full pipeline
├── config.py                # Environment variable loading and validation
├── models.py                # Email and TriageResult dataclasses
├── connectors/
│   ├── __init__.py          # Provider router (Gmail or Outlook)
│   ├── gmail.py             # Gmail API connector (OAuth 2.0)
│   └── outlook.py           # Microsoft Graph connector (client credentials)
├── triage/
│   ├── __init__.py          # Triage orchestrator (rules then AI)
│   ├── rules.py             # Hardcoded rules engine
│   └── ai.py                # Claude API integration + overview generation
├── digest/
│   ├── __init__.py
│   ├── composer.py          # HTML digest builder
│   └── sender.py            # Resend email delivery
├── .github/workflows/
│   └── triage.yml           # GitHub Actions cron (weekdays at 7 AM UTC)
├── requirements.txt
└── .env.example
```

## Setup

### Prerequisites

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/)
- A [Resend API key](https://resend.com/) + verified sender domain
- Gmail OAuth credentials **or** an Azure AD app registration for Outlook

### Installation

```bash
git clone https://github.com/effiemincer/email-triage-agent.git
cd email-triage-agent
pip install -r requirements.txt
```

### Configuration

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `EMAIL_PROVIDER` | `gmail` or `outlook` |
| `GMAIL_CREDENTIALS_JSON` | Gmail OAuth credentials JSON string |
| `GMAIL_TOKEN_JSON` | Gmail OAuth token JSON string |
| `OUTLOOK_CLIENT_ID` | Azure AD application (client) ID |
| `OUTLOOK_CLIENT_SECRET` | Azure AD client secret |
| `OUTLOOK_TENANT_ID` | Azure AD tenant ID |
| `OUTLOOK_USER_EMAIL` | Outlook mailbox email address |
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `RESEND_API_KEY` | Resend API key |
| `DIGEST_RECIPIENT_EMAIL` | Where to send the digest |
| `DIGEST_SENDER_EMAIL` | Verified Resend sender address |

### Run locally

```bash
python main.py
```

If `ANTHROPIC_API_KEY` is missing, AI triage is skipped and emails are assigned a default "Archive" action. If `RESEND_API_KEY` is missing, the digest is written to `digest.html` locally instead of being emailed.

## Deploy with GitHub Actions

The included workflow runs the agent every weekday at 7:00 AM UTC.

1. Push the repo to GitHub
2. Go to **Settings > Secrets and variables > Actions**
3. Add each variable from `.env.example` as a repository secret
4. The agent will run on schedule, or trigger it manually via **Actions > Email Triage Agent > Run workflow**

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Read-only inbox** | No emails are modified, marked as read, or deleted. The provider's own unread flag drives everything. |
| **Rules before AI** | Hardcoded rules catch obvious categories (newsletters, noreply, spam) to minimize API calls and cost. |
| **All-or-nothing** | If any pipeline step fails, the entire run aborts. No partial digest is sent. The next run picks up the same unread emails. |
| **No persistent state** | Email data lives in memory only for the run duration. No database, no cache, no files. |
| **Body truncation** | Email bodies are stripped to plain text and truncated to 500 words before being sent to Claude. |

## Tech Stack

- **Python 3.11+**
- **[Anthropic Claude API](https://docs.anthropic.com/)** — Email triage + digest overview generation
- **[Google API Client](https://github.com/googleapis/google-api-python-client)** — Gmail access
- **[Microsoft Graph SDK](https://github.com/microsoftgraph/msgraph-sdk-python)** — Outlook access
- **[Resend](https://resend.com/)** — Digest email delivery
- **[BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)** — HTML-to-text stripping
- **GitHub Actions** — Scheduled daily runs

## License

MIT
