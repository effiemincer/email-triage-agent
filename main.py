import logging
import sys

from config import load_config
from connectors import fetch_emails
from triage import triage_emails
from triage.ai import generate_overview
from digest import compose_digest, send_digest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    try:
        logger.info("Starting email triage agent")

        config = load_config()
        logger.info("Config loaded (provider=%s)", config.email_provider)

        emails, total_unread = fetch_emails(config)
        logger.info("Fetched %d emails (%d total unread)", len(emails), total_unread)

        results = triage_emails(emails, config)
        logger.info("Triaged %d emails", len(results))

        overview = generate_overview(results, config) if results else ""
        logger.info("Overview generated")

        html = compose_digest(results, total_unread, config.email_provider, overview)
        logger.info("Digest composed")

        if config.resend_api_key:
            send_digest(html, config)
            logger.info("Digest sent")
        else:
            with open("digest.html", "w", encoding="utf-8") as f:
                f.write(html)
            logger.info("Digest written to digest.html (no RESEND_API_KEY)")

        logger.info("Done")

    except Exception:
        logger.exception("Email triage agent failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
