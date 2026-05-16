from cpb_outreach.db import get_supabase, normalize_email


def is_suppressed(email: str) -> bool:
    normalized = normalize_email(email)
    sb = get_supabase()
    result = (
        sb.table("suppressions")
        .select("id")
        .eq("email", normalized)
        .limit(1)
        .execute()
    )
    return bool(result.data)


def suppress_email(email: str, reason: str, source_email_id: str | None = None) -> None:
    normalized = normalize_email(email)
    sb = get_supabase()
    row = {"email": normalized, "reason": reason}
    if source_email_id:
        row["source_email_id"] = source_email_id
    sb.table("suppressions").upsert(row, on_conflict="email").execute()


def can_send_to(email: str) -> bool:
    return not is_suppressed(email)
