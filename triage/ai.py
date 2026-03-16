import json
import logging
import re

import anthropic

from config import Config
from models import Email, TriageResult

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are an email triage assistant. For each email you receive, return a JSON object "
    "with three fields: `summary` (one sentence, max 15 words, describing what the email "
    "is about), `action` (one of: Reply, Archive, Delete, Spam), and `reason` (a short "
    "phrase explaining the suggestion). Be concise and opinionated."
)

VALID_ACTIONS = {"Reply", "Archive", "Delete", "Spam"}


def triage_with_ai(emails: list[Email], config: Config) -> list[TriageResult]:
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    results = []

    for email in emails:
        try:
            prompt = _build_prompt(email)
            data = _call_claude(client, prompt)
            results.append(
                TriageResult(
                    email=email,
                    summary=data["summary"],
                    action=data["action"],
                    reason=data["reason"],
                    source="ai",
                )
            )
        except Exception:
            logger.exception("AI triage failed for message %s", email.message_id)
            raise

    logger.info("AI triaged %d emails", len(results))
    return results


OVERVIEW_SYSTEM_PROMPT = (
    "You are an email triage assistant. You will receive a list of triaged emails with "
    "their summaries, actions, and senders. Write a brief, conversational overview "
    "(3-5 sentences) of what's in the inbox today. Highlight anything that needs "
    "immediate attention (Reply actions) first, then mention themes or patterns in the "
    "rest. Be concise and helpful. Do not use markdown — just plain text."
)


def generate_overview(results: list[TriageResult], config: Config) -> str:
    """Generate an AI overview summary of all triaged emails."""
    if not config.anthropic_api_key:
        return _fallback_overview(results)

    client = anthropic.Anthropic(api_key=config.anthropic_api_key)

    email_list = "\n".join(
        f"- From: {r.email.sender_name or r.email.sender_email} | "
        f"Subject: {r.email.subject} | Action: {r.action} | Summary: {r.summary}"
        for r in results
    )
    prompt = f"Here are today's {len(results)} triaged emails:\n\n{email_list}"

    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=OVERVIEW_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        overview = response.content[0].text.strip()
        logger.info("Generated AI overview")
        return overview
    except Exception:
        logger.warning("Failed to generate AI overview, using fallback")
        return _fallback_overview(results)


def _fallback_overview(results: list[TriageResult]) -> str:
    action_counts = {}
    for r in results:
        action_counts[r.action] = action_counts.get(r.action, 0) + 1
    parts = [f"{count} {action.lower()}" for action, count in sorted(action_counts.items())]
    return f"You have {len(results)} emails today: {', '.join(parts)}."


def _build_prompt(email: Email) -> str:
    return (
        f"From: {email.sender_name} <{email.sender_email}>\n"
        f"Subject: {email.subject}\n"
        f"Received: {email.timestamp.isoformat()}\n"
        f"\n{email.body}"
    )


def _call_claude(client: anthropic.Anthropic, user_prompt: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    text = response.content[0].text

    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
    text = re.sub(r"\n?```\s*$", "", text.strip())

    data = json.loads(text)

    for key in ("summary", "action", "reason"):
        if key not in data:
            raise ValueError(f"Missing key in Claude response: {key}")

    if data["action"] not in VALID_ACTIONS:
        raise ValueError(f"Invalid action from Claude: {data['action']}")

    return data
