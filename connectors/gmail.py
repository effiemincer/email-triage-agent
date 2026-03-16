import base64
import json
import logging
from email.utils import parseaddr, parsedate_to_datetime

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import Config
from models import Email

logger = logging.getLogger(__name__)

MAX_EMAILS = 50
MAX_BODY_WORDS = 500


def fetch_emails(config: Config) -> tuple[list[Email], int]:
    service = _build_gmail_service(config)
    message_ids, total_unread = _list_unread_message_ids(service)

    if not message_ids:
        return [], total_unread

    emails = []
    for msg_ref in message_ids:
        raw = _get_message_detail(service, msg_ref["id"])
        email = _parse_message(raw)
        emails.append(email)

    emails = _group_by_thread(emails)
    logger.info("Fetched %d emails (%d total unread)", len(emails), total_unread)
    return emails, total_unread


def _build_gmail_service(config: Config):
    creds_info = json.loads(config.gmail_credentials_json)
    token_info = json.loads(config.gmail_token_json)

    creds = Credentials.from_authorized_user_info(token_info)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("gmail", "v1", credentials=creds)


def _list_unread_message_ids(service) -> tuple[list[dict], int]:
    response = service.users().messages().list(
        userId="me", q="is:unread", maxResults=MAX_EMAILS
    ).execute()

    messages = response.get("messages", [])

    label_info = service.users().labels().get(userId="me", id="INBOX").execute()
    total_unread = label_info.get("messagesUnread", len(messages))

    return messages, total_unread


def _get_message_detail(service, msg_id: str) -> dict:
    return service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()


def _parse_message(raw: dict) -> Email:
    headers = {}
    for h in raw.get("payload", {}).get("headers", []):
        headers[h["name"].lower()] = h["value"]

    sender_name, sender_email = parseaddr(headers.get("from", ""))

    try:
        timestamp = parsedate_to_datetime(headers.get("date", ""))
    except Exception:
        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc)

    subject = headers.get("subject", "(no subject)")
    message_id = raw.get("id", "")
    thread_id = raw.get("threadId", "")

    payload = raw.get("payload", {})
    body = _find_body_part(payload, "text/plain")
    if not body:
        html_body = _find_body_part(payload, "text/html")
        if html_body:
            body = BeautifulSoup(html_body, "html.parser").get_text(separator=" ", strip=True)
    body = body or ""
    body = _truncate_words(body, MAX_BODY_WORDS)

    deep_link = f"https://mail.google.com/mail/u/0/#all/{message_id}"

    return Email(
        message_id=message_id,
        thread_id=thread_id,
        sender_name=sender_name,
        sender_email=sender_email,
        subject=subject,
        timestamp=timestamp,
        body=body,
        headers=headers,
        deep_link=deep_link,
    )


def _find_body_part(payload: dict, mime_type: str) -> str:
    if payload.get("mimeType") == mime_type:
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        result = _find_body_part(part, mime_type)
        if result:
            return result

    return ""


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _group_by_thread(emails: list[Email]) -> list[Email]:
    threads: dict[str, Email] = {}
    for email in emails:
        existing = threads.get(email.thread_id)
        if existing is None or email.timestamp > existing.timestamp:
            threads[email.thread_id] = email
    return list(threads.values())
