from datetime import datetime, timezone
from html import escape

from models import TriageResult

ACTION_COLORS = {
    "Reply": "#2563eb",
    "Archive": "#6b7280",
    "Delete": "#dc2626",
    "Spam": "#ea580c",
}

ACTION_PRIORITY = {
    "Reply": 0,
    "Archive": 1,
    "Delete": 2,
    "Spam": 3,
}

INBOX_LINKS = {
    "gmail": "https://mail.google.com/mail/u/0/#inbox",
    "outlook": "https://outlook.office365.com/mail/inbox",
}


def compose_digest(
    results: list[TriageResult],
    total_unread: int,
    provider: str,
    overview: str = "",
) -> str:
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")

    if not results:
        return _render_zero_digest(today, provider)

    results_sorted = sorted(results, key=lambda r: ACTION_PRIORITY.get(r.action, 99))
    action_counts = {}
    for r in results_sorted:
        action_counts[r.action] = action_counts.get(r.action, 0) + 1

    header_html = _render_header(today, total_unread, action_counts)
    overview_html = _render_overview(overview)
    cards_html = "\n".join(_render_card(r) for r in results_sorted)
    overflow_html = _render_overflow(total_unread, len(results))
    footer_html = _render_footer(provider)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:20px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">
{header_html}
{overview_html}
<tr><td style="padding:0 24px 24px;">
{cards_html}
{overflow_html}
</td></tr>
{footer_html}
</table>
</td></tr>
</table>
</body>
</html>"""


def _render_header(date: str, total_unread: int, action_counts: dict) -> str:
    badges = " &nbsp; ".join(
        f'<span style="display:inline-block;padding:2px 8px;border-radius:4px;'
        f'background:{ACTION_COLORS.get(action, "#6b7280")};color:#fff;font-size:12px;">'
        f'{action}: {count}</span>'
        for action, count in sorted(action_counts.items(), key=lambda x: ACTION_PRIORITY.get(x[0], 99))
    )
    return f"""<tr><td style="padding:24px;background:#1f2937;">
  <h1 style="margin:0 0 8px;color:#ffffff;font-size:20px;">Email Triage Digest</h1>
  <p style="margin:0 0 4px;color:#d1d5db;font-size:14px;">{escape(date)}</p>
  <p style="margin:0 0 8px;color:#d1d5db;font-size:14px;">{total_unread} unread emails</p>
  <p style="margin:0;">{badges}</p>
</td></tr>"""


def _render_overview(overview: str) -> str:
    if not overview:
        return ""
    return f"""<tr><td style="padding:24px 24px 8px;">
  <h2 style="margin:0 0 12px;font-size:16px;color:#1f2937;">Today's Overview</h2>
  <p style="margin:0;font-size:14px;color:#374151;line-height:1.6;">{escape(overview)}</p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0 0;">
</td></tr>"""


def _render_card(result: TriageResult) -> str:
    e = result.email
    sender = escape(e.sender_name or e.sender_email)
    sender_email = escape(e.sender_email)
    time_str = e.timestamp.strftime("%H:%M")
    badge = _render_badge(result.action)

    return f"""<table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #e5e7eb;border-radius:8px;margin-bottom:12px;">
<tr><td style="padding:16px;">
  <table width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-size:14px;font-weight:bold;color:#1f2937;">
      <a href="{escape(e.deep_link)}" style="color:#1f2937;text-decoration:none;">{escape(e.subject)}</a>
    </td>
    <td width="80" align="right">{badge}</td>
  </tr>
  <tr>
    <td style="padding-top:6px;font-size:13px;color:#6b7280;">{sender} &lt;{sender_email}&gt; &middot; {time_str}</td>
  </tr>
  <tr>
    <td colspan="2" style="padding-top:8px;font-size:13px;color:#374151;line-height:1.5;">
      {escape(result.summary)}
    </td>
  </tr>
  <tr>
    <td colspan="2" style="padding-top:8px;">
      <a href="{escape(e.deep_link)}" style="font-size:12px;color:#2563eb;text-decoration:none;">View email &rarr;</a>
    </td>
  </tr>
  </table>
</td></tr>
</table>"""


def _render_badge(action: str) -> str:
    color = ACTION_COLORS.get(action, "#6b7280")
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:12px;'
        f'background:{color};color:#ffffff;font-size:12px;font-weight:bold;">'
        f'{escape(action)}</span>'
    )


def _render_overflow(total_unread: int, shown: int) -> str:
    if total_unread <= shown:
        return ""
    remaining = total_unread - shown
    return (
        f'<p style="margin:12px 0 0;font-size:13px;color:#6b7280;text-align:center;">'
        f'Showing {shown} most recent &mdash; {remaining} more unread emails in your inbox</p>'
    )


def _render_footer(provider: str) -> str:
    inbox_url = INBOX_LINKS.get(provider, INBOX_LINKS["gmail"])
    return f"""<tr><td style="padding:16px 24px;background:#f3f4f6;text-align:center;">
  <a href="{inbox_url}" style="color:#2563eb;font-size:13px;text-decoration:none;">Open Inbox</a>
  <p style="margin:8px 0 0;font-size:11px;color:#9ca3af;">Generated by AI Email Triage Agent</p>
</td></tr>"""


def _render_zero_digest(date: str, provider: str) -> str:
    inbox_url = INBOX_LINKS.get(provider, INBOX_LINKS["gmail"])
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#f9fafb;font-family:Arial,Helvetica,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f9fafb;padding:20px 0;">
<tr><td align="center">
<table width="640" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;">
<tr><td style="padding:24px;background:#1f2937;">
  <h1 style="margin:0;color:#ffffff;font-size:20px;">Email Triage Digest</h1>
  <p style="margin:8px 0 0;color:#d1d5db;font-size:14px;">{escape(date)}</p>
</td></tr>
<tr><td style="padding:48px 24px;text-align:center;">
  <p style="font-size:24px;margin:0 0 8px;">Inbox zero &mdash; you're amazing!</p>
  <p style="font-size:14px;color:#6b7280;margin:0;">No unread emails to triage today.</p>
</td></tr>
<tr><td style="padding:16px 24px;background:#f3f4f6;text-align:center;">
  <a href="{inbox_url}" style="color:#2563eb;font-size:13px;text-decoration:none;">Open Inbox</a>
  <p style="margin:8px 0 0;font-size:11px;color:#9ca3af;">Generated by AI Email Triage Agent</p>
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>"""
