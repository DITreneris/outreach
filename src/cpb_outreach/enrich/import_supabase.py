from pathlib import Path

import pandas as pd

from cpb_outreach.db import get_supabase
from cpb_outreach.enrich.scrape_contacts import scrape_school_contacts
from cpb_outreach.enrich.verify_email import verify_email


def import_schools_csv(csv_path: Path) -> int:
    df = pd.read_csv(csv_path, dtype=str)
    sb = get_supabase()
    count = 0
    for _, row in df.iterrows():
        payload = {
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
        if payload["nces_id"]:
            sb.table("schools").upsert(payload, on_conflict="nces_id").execute()
        else:
            sb.table("schools").insert(payload).execute()
        count += 1
    return count


def enrich_and_import_contacts(limit: int = 50, scrape: bool = True) -> dict:
    sb = get_supabase()
    schools = (
        sb.table("schools")
        .select("id, website_url, domain")
        .not_.is_("website_url", "null")
        .limit(limit)
        .execute()
    ).data

    added = 0
    verified = 0
    for school in schools:
        if not scrape or not school.get("website_url"):
            continue
        contacts = scrape_school_contacts(school["website_url"])
        for c in contacts:
            ok, confidence = verify_email(c["email"])
            if not ok:
                continue
            verified += 1
            row = {
                "school_id": school["id"],
                "email": c["email"],
                "role_target": c["role_target"],
                "email_source": c["email_source"],
                "verified_at": pd.Timestamp.utcnow().isoformat(),
                "verify_confidence": confidence,
                "outreach_status": "ready",
            }
            sb.table("contacts").upsert(row, on_conflict="email").execute()
            added += 1
    return {"schools_processed": len(schools), "contacts_upserted": added, "verified": verified}
