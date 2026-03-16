from config import Config
from models import Email


def fetch_emails(config: Config) -> tuple[list[Email], int]:
    """Fetch unread emails from the configured provider.

    Returns (emails, total_unread_count).
    """
    if config.email_provider == "gmail":
        from connectors.gmail import fetch_emails as gmail_fetch

        return gmail_fetch(config)
    elif config.email_provider == "outlook":
        from connectors.outlook import fetch_emails as outlook_fetch

        return outlook_fetch(config)
    else:
        raise ValueError(f"Unknown email provider: {config.email_provider}")
