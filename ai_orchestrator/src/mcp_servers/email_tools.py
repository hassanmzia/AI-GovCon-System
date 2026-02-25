"""MCP tool server: Email drafting and sending for BD communications."""
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("ai_orchestrator.mcp.email")

_DJANGO_URL = os.getenv("DJANGO_API_URL", "http://django-api:8001")
_SERVICE_TOKEN = os.getenv("DJANGO_SERVICE_TOKEN", "")

# Email provider config
_SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
_SMTP_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
_SMTP_PORT = int(os.getenv("EMAIL_PORT", "587"))
_SMTP_USER = os.getenv("EMAIL_HOST_USER", "")
_SMTP_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@dealmanager.local")


def _headers() -> dict:
    return {"Authorization": f"Bearer {_SERVICE_TOKEN}"} if _SERVICE_TOKEN else {}


async def draft_email(
    email_type: str,
    context: dict[str, Any],
    tone: str = "professional",
) -> dict[str, Any]:
    """Draft an email using AI based on type and context.

    Args:
        email_type: Type of email to draft:
            "intro_letter", "capability_statement", "rfp_clarification",
            "meeting_request", "teaming_inquiry", "proposal_submission",
            "follow_up", "win_notification", "loss_debrief_request".
        context: Context dict with relevant details (deal info, agency, contacts, etc.).
        tone: Tone preference ("professional", "formal", "casual", "concise").

    Returns:
        Dict with subject, body, to_addresses, cc_addresses, key_points.
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/communications/draft-email/",
                json={"email_type": email_type, "context": context, "tone": tone},
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("Email draft API failed, using template: %s", exc)
        return _email_template(email_type, context, tone)


async def send_email(
    to_addresses: list[str],
    subject: str,
    body: str,
    cc_addresses: list[str] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    reply_to: str | None = None,
) -> dict[str, Any]:
    """Send an email via configured email provider.

    Args:
        to_addresses: List of recipient email addresses.
        subject: Email subject.
        body: Email body (HTML or plain text).
        cc_addresses: Optional CC addresses.
        attachments: Optional list of attachment dicts with filename, content (base64), content_type.
        reply_to: Optional reply-to address.

    Returns:
        Dict with success (bool), message_id, provider.
    """
    if _SENDGRID_API_KEY:
        return await _send_via_sendgrid(
            to_addresses, subject, body, cc_addresses or [], attachments or [], reply_to
        )
    if _SMTP_HOST and _SMTP_USER:
        return await _send_via_smtp(
            to_addresses, subject, body, cc_addresses or [], attachments or [], reply_to
        )

    logger.warning("No email provider configured; email not sent")
    return {
        "success": False,
        "message_id": None,
        "provider": "none",
        "note": "Configure SENDGRID_API_KEY or SMTP credentials to enable sending",
        "draft": {"to": to_addresses, "subject": subject, "body": body[:500] + "..."},
    }


async def track_email(
    message_id: str,
    deal_id: str,
    email_type: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Track a sent email in the CRM.

    Args:
        message_id: Email provider message ID.
        deal_id: Associated deal UUID.
        email_type: Type of email sent.
        metadata: Additional metadata to store.

    Returns:
        Dict with tracking_id and status.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{_DJANGO_URL}/api/communications/track-email/",
                json={
                    "message_id": message_id,
                    "deal_id": deal_id,
                    "email_type": email_type,
                    "metadata": metadata or {},
                },
                headers=_headers(),
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.error("Email tracking failed: %s", exc)
        return {"success": False, "error": str(exc)}


async def get_email_templates(email_type: str | None = None) -> list[dict[str, Any]]:
    """Retrieve available email templates.

    Args:
        email_type: Optional filter by email type.

    Returns:
        List of template dicts with type, name, subject_template, body_template.
    """
    templates = [
        {
            "type": "intro_letter",
            "name": "Agency Introduction Letter",
            "subject_template": "Introduction: {company_name} Capabilities for {agency_name}",
        },
        {
            "type": "rfp_clarification",
            "name": "RFP Clarification Questions",
            "subject_template": "Clarification Questions – {solicitation_number}",
        },
        {
            "type": "teaming_inquiry",
            "name": "Teaming Partner Inquiry",
            "subject_template": "Teaming Opportunity: {opportunity_title}",
        },
        {
            "type": "meeting_request",
            "name": "Capability Briefing Request",
            "subject_template": "Request for Capability Briefing – {company_name}",
        },
        {
            "type": "proposal_submission",
            "name": "Proposal Submission Confirmation",
            "subject_template": "Proposal Submission – {solicitation_number}",
        },
        {
            "type": "loss_debrief_request",
            "name": "Debrief Request After Loss",
            "subject_template": "Debrief Request – {solicitation_number}",
        },
    ]
    if email_type:
        return [t for t in templates if t["type"] == email_type]
    return templates


# ── Provider implementations ──────────────────────────────────────────────────

async def _send_via_sendgrid(
    to_addresses, subject, body, cc_addresses, attachments, reply_to
) -> dict:
    try:
        payload: dict[str, Any] = {
            "personalizations": [{"to": [{"email": e} for e in to_addresses]}],
            "from": {"email": _FROM_EMAIL},
            "subject": subject,
            "content": [{"type": "text/html", "value": body}],
        }
        if cc_addresses:
            payload["personalizations"][0]["cc"] = [{"email": e} for e in cc_addresses]
        if reply_to:
            payload["reply_to"] = {"email": reply_to}
        if attachments:
            payload["attachments"] = [
                {
                    "content": a["content"],
                    "filename": a["filename"],
                    "type": a.get("content_type", "application/octet-stream"),
                }
                for a in attachments
            ]

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                json=payload,
                headers={"Authorization": f"Bearer {_SENDGRID_API_KEY}"},
            )
            resp.raise_for_status()
            return {"success": True, "message_id": resp.headers.get("X-Message-Id", ""), "provider": "sendgrid"}
    except Exception as exc:
        logger.error("SendGrid send failed: %s", exc)
        return {"success": False, "error": str(exc), "provider": "sendgrid"}


async def _send_via_smtp(
    to_addresses, subject, body, cc_addresses, attachments, reply_to
) -> dict:
    import asyncio
    import email as email_lib
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    def _blocking_send():
        msg = MIMEMultipart("alternative")
        msg["From"] = _FROM_EMAIL
        msg["To"] = ", ".join(to_addresses)
        msg["Subject"] = subject
        if cc_addresses:
            msg["Cc"] = ", ".join(cc_addresses)
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(body, "html"))

        recipients = to_addresses + (cc_addresses or [])
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.starttls()
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.sendmail(_FROM_EMAIL, recipients, msg.as_string())
        return "sent"

    try:
        await asyncio.get_event_loop().run_in_executor(None, _blocking_send)
        return {"success": True, "message_id": "", "provider": "smtp"}
    except Exception as exc:
        logger.error("SMTP send failed: %s", exc)
        return {"success": False, "error": str(exc), "provider": "smtp"}


def _email_template(email_type: str, context: dict, tone: str) -> dict:
    company = context.get("company_name", "[Company]")
    agency = context.get("agency_name", "[Agency]")
    contact = context.get("contact_name", "Contracting Officer")
    opp = context.get("opportunity_title", "[Opportunity]")

    templates = {
        "intro_letter": {
            "subject": f"Introduction: {company} Capabilities",
            "body": f"Dear {contact},\n\nI am writing to introduce {company} and our capabilities relevant to {agency}'s mission...\n\nBest regards,",
        },
        "rfp_clarification": {
            "subject": f"Clarification Questions – {context.get('solicitation_number', 'RFP')}",
            "body": f"Dear {contact},\n\nWe have the following questions regarding the above-referenced solicitation:\n\n[Questions to be inserted]\n\nThank you for your time.",
        },
        "teaming_inquiry": {
            "subject": f"Teaming Opportunity: {opp}",
            "body": f"Dear {contact},\n\nWe are pursuing {opp} and believe a teaming arrangement could be mutually beneficial...",
        },
        "meeting_request": {
            "subject": f"Capability Briefing Request – {company}",
            "body": f"Dear {contact},\n\nWe would welcome the opportunity to present {company}'s capabilities to {agency}...",
        },
    }
    default = templates.get(
        email_type,
        {"subject": f"[{email_type}] from {company}", "body": f"Dear {contact},\n\n[Email body]\n\nBest regards,"},
    )
    return {**default, "email_type": email_type, "tone": tone, "draft": True}
