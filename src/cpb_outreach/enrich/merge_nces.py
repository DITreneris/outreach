"""Merge NCES CCD school CSV with optional rankings CSV (e.g. us_news_rank)."""

from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from rapidfuzz import fuzz, process


def normalize_name(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum() or ch.isspace()).strip()


def extract_domain(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    if not raw.startswith("http"):
        raw = f"https://{raw}"
    try:
        host = urlparse(raw).netloc or urlparse(raw).path.split("/")[0]
    except Exception:
        return ""
    return host.lower().removeprefix("www.")


def load_nces_schools(nces_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(nces_csv, dtype=str, low_memory=False)
    if _is_lea_finance_format(list(df.columns)):
        return load_nces_lea_finance(df)

    rename = {}
    for col in df.columns:
        lower = col.upper()
        if lower in ("NCESSCH", "NCESSCHOOL"):
            rename[col] = "nces_id"
        elif lower == "SCH_NAME":
            rename[col] = "school_name"
        elif lower == "LEA_NAME":
            rename[col] = "district_name"
        elif lower == "LCITY":
            rename[col] = "city"
        elif lower in ("LSTATE", "STATE", "ST"):
            rename[col] = "state"
        elif lower == "LZIP":
            rename[col] = "zip"
        elif lower == "GSLO":
            rename[col] = "grades_low"
        elif lower == "GSHI":
            rename[col] = "grades_high"
        elif lower == "MEMBER":
            rename[col] = "enrollment"
        elif lower in ("WEBSITE", "SCH_WEBSITE"):
            rename[col] = "website_url"
        elif lower == "SY_STATUS":
            rename[col] = "sy_status"
        elif lower == "SY_STATUS_TEXT":
            rename[col] = "sy_status_text"
        elif lower == "LEVEL":
            rename[col] = "level"
        elif lower == "PHONE":
            rename[col] = "phone"
    df = df.rename(columns=rename)
    required = {"school_name", "state"}
    if not required.issubset(df.columns):
        raise ValueError(f"NCES CSV missing columns; have {list(df.columns)}")
    if "nces_id" not in df.columns and "NCESSCH" in df.columns:
        df["nces_id"] = df["NCESSCH"]
    df["grades"] = df.apply(
        lambda r: f"{r.get('grades_low', '')}-{r.get('grades_high', '')}".strip("-"),
        axis=1,
    )
    return df


def _is_lea_finance_format(columns: list[str]) -> bool:
    upper = {c.upper() for c in columns}
    return "LEAID" in upper and "STABBR" in upper and "NAME" in upper and "SCH_NAME" not in upper


def load_nces_lea_finance(df: pd.DataFrame) -> pd.DataFrame:
    rename = {
        "LEAID": "nces_id",
        "NAME": "school_name",
        "STABBR": "state",
        "MEMBERSCH": "enrollment",
        "GSLO": "grades_low",
        "GSHI": "grades_high",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    df["district_name"] = df["school_name"]
    df["nces_id"] = "lea_" + df["nces_id"].astype(str).str.strip()
    df["enrollment"] = pd.to_numeric(df["enrollment"], errors="coerce")
    df = df[df["enrollment"].fillna(0) > 0].copy()
    df["grades"] = df.apply(
        lambda r: f"{r.get('grades_low', '')}-{r.get('grades_high', '')}".strip("-"),
        axis=1,
    )
    df["website_url"] = ""
    df["domain"] = ""
    df["entity_type"] = "district"
    return df


def filter_school_directory(
    df: pd.DataFrame,
    *,
    level: str | None = "High",
    open_only: bool = True,
) -> pd.DataFrame:
    out = df.copy()
    if open_only:
        if "sy_status" in out.columns:
            out = out[out["sy_status"].astype(str).str.strip() == "1"]
        elif "sy_status_text" in out.columns:
            out = out[out["sy_status_text"].astype(str).str.strip().str.lower() == "open"]
    if level and "level" in out.columns:
        out = out[out["level"].astype(str).str.strip() == level]
    if "website_url" in out.columns:
        w = out["website_url"].fillna("").astype(str).str.strip()
        invalid = {"", "-", "n/a", "na", "none", "nan"}
        out = out[~w.str.lower().isin(invalid)]
    return out


def dedupe_by_domain(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["domain"] = out["website_url"].fillna("").apply(extract_domain)
    out = out[out["domain"] != ""].copy()
    out = out.sort_values("school_name", kind="stable")
    return out.drop_duplicates(subset=["domain"], keep="first")


def load_rankings(rankings_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(rankings_csv, dtype=str)
    if "us_news_rank" not in df.columns and "rank" in df.columns:
        df = df.rename(columns={"rank": "us_news_rank"})
    return df


def fuzzy_merge_rankings(nces: pd.DataFrame, rankings: pd.DataFrame) -> pd.DataFrame:
    keys = [
        normalize_name(f"{row.get('school_name','')} {row.get('city','')} {row.get('state','')}")
        for _, row in nces.iterrows()
    ]
    rank_keys = [
        normalize_name(f"{row.get('school_name','')} {row.get('city','')} {row.get('state','')}")
        for _, row in rankings.iterrows()
    ]
    rank_values = rankings.to_dict("records")

    merged_ranks: list[int | None] = []
    for key in keys:
        if not key.strip():
            merged_ranks.append(None)
            continue
        match = process.extractOne(key, rank_keys, scorer=fuzz.token_sort_ratio)
        if match and match[1] >= 88:
            idx = rank_keys.index(match[0])
            rank_raw = rank_values[idx].get("us_news_rank")
            merged_ranks.append(int(rank_raw) if rank_raw and str(rank_raw).isdigit() else None)
        else:
            merged_ranks.append(None)
    nces = nces.copy()
    nces["us_news_rank"] = merged_ranks
    return nces


def build_master(
    nces_csv: Path,
    rankings_csv: Path | None = None,
    *,
    school_pool: int = 750,
    level: str | None = "High",
    open_only: bool = True,
    dedupe_domain: bool = True,
) -> pd.DataFrame:
    nces = load_nces_schools(nces_csv)
    nces = filter_school_directory(nces, level=level, open_only=open_only)

    if rankings_csv and rankings_csv.exists():
        rankings = load_rankings(rankings_csv)
        nces = fuzzy_merge_rankings(nces, rankings)
        nces = nces[nces["us_news_rank"].notna()].copy()
        nces["us_news_rank"] = pd.to_numeric(nces["us_news_rank"], errors="coerce")
        nces = nces.sort_values("us_news_rank")
    elif "enrollment" in nces.columns:
        nces["enrollment"] = pd.to_numeric(nces["enrollment"], errors="coerce")
        nces = nces.sort_values("enrollment", ascending=False, na_position="last")

    if dedupe_domain and "website_url" in nces.columns:
        nces = dedupe_by_domain(nces)
    elif "website_url" in nces.columns:
        nces["domain"] = nces["website_url"].fillna("").apply(extract_domain)

    nces = nces.head(school_pool)
    return nces
