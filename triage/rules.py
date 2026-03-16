import logging
import re

from models import Email, TriageResult

logger = logging.getLogger(__name__)

NEWSLETTER_DOMAINS: set[str] = {
    "substack.com",
    "mail.beehiiv.com",
    "mailchimp.com",
    "campaign-archive.com",
    "convertkit.com",
    "buttondown.email",
    "revue.email",
    "ghost.io",
    "medium.com",
    "news.ycombinator.com",
    "email.mg.substack.com",
}

SPAM_TRIGGER_WORDS: list[str] = [
    "congratulations you've won",
    "act now",
    "limited time offer",
    "click here immediately",
    "free gift",
    "no obligation",
    "risk-free",
    "winner selected",
    "claim your prize",
    "double your income",
]

INVOICE_KEYWORDS: list[str] = ["invoice", "payment", "receipt", "billing"]

URGENT_KEYWORDS: list[str] = ["urgent", "asap", "action required", "deadline"]


def apply_rules(emails: list[Email]) -> tuple[list[TriageResult], list[Email]]:
    """Apply hardcoded rules to emails.

    Returns (matched_results, unmatched_emails).
    """
    matched: list[TriageResult] = []
    unmatched: list[Email] = []

    for email in emails:
        result = _match(email)
        if result:
            matched.append(result)
        else:
            unmatched.append(email)

    logger.info("Rules matched %d/%d emails", len(matched), len(emails))
    return matched, unmatched


def _match(email: Email) -> TriageResult | None:
    # Newsletter detection
    domain = _extract_domain(email.sender_email)
    if domain in NEWSLETTER_DOMAINS or email.headers.get("list-unsubscribe"):
        return TriageResult(
            email=email,
            summary="Newsletter or mailing list",
            action="Archive",
            reason="newsletter detected",
            source="rule",
        )

    # Automated/noreply sender
    local_part = email.sender_email.split("@")[0].lower() if "@" in email.sender_email else ""
    if local_part in ("noreply", "no-reply"):
        return TriageResult(
            email=email,
            summary="Automated notification",
            action="Archive",
            reason="automated sender (noreply)",
            source="rule",
        )

    # Spam signals
    subject_lower = email.subject.lower()
    body_lower = email.body.lower()
    for trigger in SPAM_TRIGGER_WORDS:
        if trigger in subject_lower or trigger in body_lower:
            return TriageResult(
                email=email,
                summary="Possible spam",
                action="Spam",
                reason=f"spam trigger: {trigger}",
                source="rule",
            )

    # Invoice/billing
    for keyword in INVOICE_KEYWORDS:
        if keyword in subject_lower:
            return TriageResult(
                email=email,
                summary=f"Billing: {keyword} detected in subject",
                action="Reply",
                reason=f"subject contains '{keyword}'",
                source="rule",
            )

    # Urgent flag
    for keyword in URGENT_KEYWORDS:
        if keyword in subject_lower:
            return TriageResult(
                email=email,
                summary="Flagged as urgent",
                action="Reply",
                reason=f"subject contains '{keyword}'",
                source="rule",
            )

    return None


def _extract_domain(email_address: str) -> str:
    if "@" in email_address:
        return email_address.split("@")[1].lower()
    return ""
