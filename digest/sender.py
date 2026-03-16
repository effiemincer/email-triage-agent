import logging
from datetime import datetime, timezone

import resend

from config import Config

logger = logging.getLogger(__name__)


def send_digest(html: str, config: Config) -> None:
    resend.api_key = config.resend_api_key

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    subject = f"Email Triage Digest — {today}"

    resend.Emails.send(
        {
            "from": config.digest_sender_email,
            "to": [config.digest_recipient_email],
            "subject": subject,
            "html": html,
        }
    )

    logger.info("Digest sent to %s", config.digest_recipient_email)
