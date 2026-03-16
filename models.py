from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Email:
    message_id: str
    thread_id: str
    sender_name: str
    sender_email: str
    subject: str
    timestamp: datetime
    body: str
    headers: dict = field(default_factory=dict)
    deep_link: str = ""


@dataclass
class TriageResult:
    email: Email
    summary: str
    action: str  # Reply, Archive, Delete, Spam
    reason: str
    source: str  # "rule" or "ai"
