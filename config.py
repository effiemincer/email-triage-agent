import logging
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    email_provider: str
    gmail_credentials_json: str
    gmail_token_json: str
    outlook_client_id: str
    outlook_client_secret: str
    outlook_tenant_id: str
    outlook_user_email: str
    anthropic_api_key: str
    resend_api_key: str
    digest_recipient_email: str
    digest_sender_email: str


def load_config() -> Config:
    load_dotenv()

    provider = os.environ.get("EMAIL_PROVIDER", "").lower()
    if provider not in ("gmail", "outlook"):
        raise ValueError("EMAIL_PROVIDER must be 'gmail' or 'outlook'")

    config = Config(
        email_provider=provider,
        gmail_credentials_json=os.environ.get("GMAIL_CREDENTIALS_JSON", ""),
        gmail_token_json=os.environ.get("GMAIL_TOKEN_JSON", ""),
        outlook_client_id=os.environ.get("OUTLOOK_CLIENT_ID", ""),
        outlook_client_secret=os.environ.get("OUTLOOK_CLIENT_SECRET", ""),
        outlook_tenant_id=os.environ.get("OUTLOOK_TENANT_ID", ""),
        outlook_user_email=os.environ.get("OUTLOOK_USER_EMAIL", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        resend_api_key=os.environ.get("RESEND_API_KEY", ""),
        digest_recipient_email=os.environ.get("DIGEST_RECIPIENT_EMAIL", ""),
        digest_sender_email=os.environ.get("DIGEST_SENDER_EMAIL", ""),
    )

    if provider == "gmail":
        if not config.gmail_credentials_json or not config.gmail_token_json:
            raise ValueError("Gmail requires GMAIL_CREDENTIALS_JSON and GMAIL_TOKEN_JSON")
    elif provider == "outlook":
        missing = [
            name
            for name, val in [
                ("OUTLOOK_CLIENT_ID", config.outlook_client_id),
                ("OUTLOOK_CLIENT_SECRET", config.outlook_client_secret),
                ("OUTLOOK_TENANT_ID", config.outlook_tenant_id),
                ("OUTLOOK_USER_EMAIL", config.outlook_user_email),
            ]
            if not val
        ]
        if missing:
            raise ValueError(f"Outlook requires: {', '.join(missing)}")

    if not config.anthropic_api_key:
        logging.getLogger(__name__).warning(
            "ANTHROPIC_API_KEY not set — AI triage will be skipped"
        )
    if not config.resend_api_key:
        logging.getLogger(__name__).warning(
            "RESEND_API_KEY not set — digest will be written to digest.html instead"
        )

    return config
