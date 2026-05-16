import time
from datetime import datetime, timezone

import resend

from cpb_outreach.config import get_settings
from cpb_outreach.db import get_supabase, normalize_email
from cpb_outreach.email_render import render_template
from cpb_outreach.suppressions import can_send_to
from cpb_outreach.unsubscribe_tokens import unsubscribe_url


def _configure_resend() -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY is required")
    resend.api_key = settings.resend_api_key


def send_to_contact(contact_id: str, campaign_slug: str) -> dict:
    sb = get_supabase()
    settings = get_settings()

    campaign = (
        sb.table("campaigns").select("*").eq("slug", campaign_slug).single().execute()
    ).data
    contact = (
        sb.table("contacts")
        .select("*, schools(state, school_name)")
        .eq("id", contact_id)
        .single()
        .execute()
    ).data

    email = normalize_email(contact["email"])
    if not can_send_to(email):
        return {"skipped": True, "reason": "suppressed"}

    school = contact.get("schools") or {}
    state = school.get("state")
    subject_tpl = campaign["subject_template"]
    subject = subject_tpl.replace("{{state}}", state or "US")
    _, html = render_template(
        campaign["html_template_path"],
        contact_name=contact.get("contact_name"),
        state=state,
        utm_campaign=campaign["utm_campaign"],
        to_email=email,
    )

    dry_run = campaign.get("dry_run", settings.dry_run_default)
    if dry_run:
        sb.table("send_log").upsert(
            {
                "contact_id": contact_id,
                "campaign_id": campaign["id"],
                "status": "dry_run",
                "sent_at": None,
            },
            on_conflict="contact_id,campaign_id",
        ).execute()
        return {"dry_run": True, "to": email}

    _configure_resend()
    unsub = unsubscribe_url(email)
    payload = {
        "from": f"{settings.outreach_from_name} <{settings.outreach_from_email}>",
        "to": [email],
        "subject": subject,
        "html": html,
        "headers": {
            "List-Unsubscribe": f"<{unsub}>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click",
        },
    }
    response = resend.Emails.send(payload)
    message_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)

    sb.table("send_log").upsert(
        {
            "contact_id": contact_id,
            "campaign_id": campaign["id"],
            "resend_message_id": message_id,
            "status": "sent",
            "sent_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="contact_id,campaign_id",
    ).execute()
    sb.table("contacts").update({"outreach_status": "sent"}).eq("id", contact_id).execute()

    time.sleep(1.0 / max(settings.send_rate_per_second, 0.05))
    return {"sent": True, "message_id": message_id, "to": email}


def run_campaign_batch(campaign_slug: str, limit: int | None = None) -> dict:
    sb = get_supabase()
    settings = get_settings()
    campaign = (
        sb.table("campaigns").select("*").eq("slug", campaign_slug).single().execute()
    ).data
    cap = limit or campaign.get("daily_cap") or settings.warmup_week1_daily_cap

    contacts = (
        sb.table("contacts")
        .select("id")
        .eq("outreach_status", "ready")
        .limit(cap)
        .execute()
    ).data

    sent = 0
    skipped = 0
    dry = 0
    for row in contacts:
        result = send_to_contact(row["id"], campaign_slug)
        if result.get("skipped"):
            skipped += 1
        elif result.get("dry_run"):
            dry += 1
        elif result.get("sent"):
            sent += 1

    return {"campaign": campaign_slug, "sent": sent, "dry_run": dry, "skipped": skipped, "attempted": len(contacts)}
