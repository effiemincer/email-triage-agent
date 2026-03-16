import asyncio
import logging
from datetime import datetime, timezone
from urllib.parse import quote

from azure.identity.aio import ClientSecretCredential
from bs4 import BeautifulSoup
from msgraph import GraphServiceClient
from msgraph.generated.users.item.messages.messages_request_builder import (
    MessagesRequestBuilder,
)

from config import Config
from models import Email

logger = logging.getLogger(__name__)

MAX_EMAILS = 50
MAX_BODY_WORDS = 500


def fetch_emails(config: Config) -> tuple[list[Email], int]:
    return asyncio.run(_fetch_emails_async(config))


async def _fetch_emails_async(config: Config) -> tuple[list[Email], int]:
    credential = ClientSecretCredential(
        tenant_id=config.outlook_tenant_id,
        client_id=config.outlook_client_id,
        client_secret=config.outlook_client_secret,
    )

    try:
        client = GraphServiceClient(
            credential, scopes=["https://graph.microsoft.com/.default"]
        )

        messages, total_unread = await _list_unread_messages(
            client, config.outlook_user_email
        )

        if not messages:
            return [], total_unread

        emails = [_parse_message(msg) for msg in messages]
        emails = _group_by_conversation(emails)

        logger.info("Fetched %d emails (%d total unread)", len(emails), total_unread)
        return emails, total_unread
    finally:
        await credential.close()


async def _list_unread_messages(client: GraphServiceClient, user_email: str):
    query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
        filter="isRead eq false",
        top=MAX_EMAILS,
        orderby=["receivedDateTime desc"],
        select=["id", "conversationId", "from", "subject", "receivedDateTime", "body"],
    )
    config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
        query_parameters=query_params,
    )

    result = await client.users.by_user_id(user_email).messages.get(
        request_configuration=config
    )

    messages = result.value if result and result.value else []

    # Get total unread count from inbox folder
    inbox = await client.users.by_user_id(user_email).mail_folders.by_mail_folder_id(
        "inbox"
    ).get()
    total_unread = inbox.unread_item_count if inbox and inbox.unread_item_count else len(messages)

    return messages, total_unread


def _parse_message(msg) -> Email:
    sender_name = ""
    sender_email = ""
    if msg.from_ and msg.from_.email_address:
        sender_name = msg.from_.email_address.name or ""
        sender_email = msg.from_.email_address.address or ""

    timestamp = msg.received_date_time or datetime.now(timezone.utc)

    body_text = ""
    if msg.body and msg.body.content:
        if msg.body.content_type and "html" in str(msg.body.content_type).lower():
            body_text = BeautifulSoup(msg.body.content, "html.parser").get_text(
                separator=" ", strip=True
            )
        else:
            body_text = msg.body.content
    body_text = _truncate_words(body_text, MAX_BODY_WORDS)

    message_id = msg.id or ""
    deep_link = f"https://outlook.office365.com/mail/inbox/id/{quote(message_id, safe='')}"

    return Email(
        message_id=message_id,
        thread_id=msg.conversation_id or message_id,
        sender_name=sender_name,
        sender_email=sender_email,
        subject=msg.subject or "(no subject)",
        timestamp=timestamp,
        body=body_text,
        headers={},
        deep_link=deep_link,
    )


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words])


def _group_by_conversation(emails: list[Email]) -> list[Email]:
    threads: dict[str, Email] = {}
    for email in emails:
        existing = threads.get(email.thread_id)
        if existing is None or email.timestamp > existing.timestamp:
            threads[email.thread_id] = email
    return list(threads.values())
