import logging

from config import Config
from models import Email, TriageResult
from triage.rules import apply_rules

logger = logging.getLogger(__name__)


def triage_emails(emails: list[Email], config: Config) -> list[TriageResult]:
    """Triage emails: rules first, then AI for unmatched."""
    matched, unmatched = apply_rules(emails)

    if unmatched:
        if config.anthropic_api_key:
            try:
                from triage.ai import triage_with_ai

                ai_results = triage_with_ai(unmatched, config)
                matched.extend(ai_results)
                return matched
            except Exception:
                logger.warning(
                    "AI triage failed, falling back to default for %d emails",
                    len(unmatched),
                )

        if not config.anthropic_api_key:
            logger.warning(
                "Skipping AI triage for %d emails (no API key)", len(unmatched)
            )

        for email in unmatched:
            matched.append(
                TriageResult(
                    email=email,
                    summary="Not triaged (AI unavailable)",
                    action="Archive",
                    reason="no API key configured",
                    source="rule",
                )
            )

    return matched
