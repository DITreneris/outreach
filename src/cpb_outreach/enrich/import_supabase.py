import time
from pathlib import Path

import pandas as pd

from cpb_outreach.db import get_supabase
from cpb_outreach.enrich.scrape_contacts import scrape_school_contacts
from cpb_outreach.enrich.verify_email import verify_email

BATCH_SIZE = 100
ROLE_PRIORITY = ("principal", "instructional_coach", "media_specialist", "generic_office", "other")
SCRAPE_DELAY_SECONDS = 1.0


def _row_to_school_payload(row: pd.Series) -> dict:
    return {
        "nces_id": row.get("nces_id") or None,
        "us_news_rank": int(row["us_news_rank"]) if pd.notna(row.get("us_news_rank")) else None,
        "school_name": row["school_name"],
        "district_name": row.get("district_name"),
        "city": row.get("city"),
        "state": row.get("state"),
        "zip": row.get("zip"),
        "grades": row.get("grades"),
        "enrollment": int(row["enrollment"]) if pd.notna(row.get("enrollment")) else None,
        "website_url": row.get("website_url"),
        "domain": row.get("domain"),
    }


def import_schools_csv(csv_path: Path, batch_size: int = BATCH_SIZE) -> int:
    df = pd.read_csv(csv_path, dtype=str)
    sb = get_supabase()
    total = len(df)
    count = 0

    for start in range(0, total, batch_size):
        chunk = df.iloc[start : start + batch_size]
        with_nces: list[dict] = []
        without_nces: list[dict] = []

        for _, row in chunk.iterrows():
            payload = _row_to_school_payload(row)
            if payload["nces_id"]:
                with_nces.append(payload)
            else:
                without_nces.append(payload)

        if with_nces:
            sb.table("schools").upsert(with_nces, on_conflict="nces_id").execute()
            count += len(with_nces)
        for payload in without_nces:
            sb.table("schools").insert(payload).execute()
            count += 1

        print(f"Imported {min(start + batch_size, total)}/{total} schools", flush=True)

    return count


def _role_rank(role: str) -> int:
    try:
        return ROLE_PRIORITY.index(role)
    except ValueError:
        return len(ROLE_PRIORITY)


def pick_best_contact(scraped: list[dict]) -> dict | None:
    verified: list[dict] = []
    for c in scraped:
        ok, confidence = verify_email(c["email"])
        if not ok:
            continue
        verified.append({**c, "verify_confidence": confidence})
    if not verified:
        return None
    verified.sort(key=lambda c: _role_rank(c.get("role_target", "other")))
    return verified[0]


def _count_ready_contacts(sb) -> int:
    result = (
        sb.table("contacts")
        .select("id", count="exact")
        .eq("outreach_status", "ready")
        .limit(1)
        .execute()
    )
    if getattr(result, "count", None) is not None:
        return int(result.count)
    return len(result.data or [])


def _schools_without_contacts(sb, limit: int) -> list[dict]:
    schools = (
        sb.table("schools")
        .select("id, website_url, domain")
        .not_.is_("website_url", "null")
        .neq("website_url", "")
        .execute()
    ).data or []
    existing = (sb.table("contacts").select("school_id").execute()).data or []
    have_contact = {row["school_id"] for row in existing if row.get("school_id")}
    pending = [s for s in schools if s["id"] not in have_contact]
    return pending[:limit]


def enrich_and_import_contacts(
    *,
    target_contacts: int = 500,
    school_batch: int = 50,
    scrape: bool = True,
) -> dict:
    sb = get_supabase()
    ready_before = _count_ready_contacts(sb)
    contacts_added = 0
    schools_scraped = 0

    if ready_before >= target_contacts:
        return {
            "schools_scraped": 0,
            "contacts_added": 0,
            "contacts_ready_total": ready_before,
            "stopped_reason": "target_already_met",
        }

    while _count_ready_contacts(sb) < target_contacts:
        schools = _schools_without_contacts(sb, school_batch)
        if not schools:
            break

        for school in schools:
            if _count_ready_contacts(sb) >= target_contacts:
                break
            if not scrape or not school.get("website_url"):
                continue

            scraped = scrape_school_contacts(school["website_url"])
            schools_scraped += 1
            best = pick_best_contact(scraped)
            if not best:
                time.sleep(SCRAPE_DELAY_SECONDS)
                continue

            row = {
                "school_id": school["id"],
                "email": best["email"],
                "role_target": best["role_target"],
                "email_source": best["email_source"],
                "verified_at": pd.Timestamp.utcnow().isoformat(),
                "verify_confidence": best["verify_confidence"],
                "outreach_status": "ready",
            }
            sb.table("contacts").upsert(row, on_conflict="email").execute()
            contacts_added += 1
            time.sleep(SCRAPE_DELAY_SECONDS)

    ready_total = _count_ready_contacts(sb)
    stopped_reason = "target_met" if ready_total >= target_contacts else "no_more_schools"

    return {
        "schools_scraped": schools_scraped,
        "contacts_added": contacts_added,
        "contacts_ready_total": ready_total,
        "stopped_reason": stopped_reason,
    }
