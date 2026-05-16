"""Merge NCES CCD school CSV with optional rankings CSV (e.g. us_news_rank)."""

from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process


def normalize_name(value: str) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum() or ch.isspace()).strip()


def load_nces_schools(nces_csv: Path) -> pd.DataFrame:
    df = pd.read_csv(nces_csv, dtype=str, low_memory=False)
    # CCD column names vary by year; map common aliases
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
        elif lower in ("LSTATE", "STATE"):
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
    df = df.rename(columns=rename)
    required = {"school_name", "state"}
    if not required.issubset(df.columns):
        raise ValueError(f"NCES CSV missing columns; have {list(df.columns)}")
    if "nces_id" not in df.columns and "NCESSCH" in df.columns:
        df["nces_id"] = df["NCESSCH"]
    return df


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


def build_master(nces_csv: Path, rankings_csv: Path | None = None, top_n: int = 500) -> pd.DataFrame:
    nces = load_nces_schools(nces_csv)
    if rankings_csv and rankings_csv.exists():
        rankings = load_rankings(rankings_csv)
        nces = fuzzy_merge_rankings(nces, rankings)
        nces = nces[nces["us_news_rank"].notna()].copy()
        nces["us_news_rank"] = pd.to_numeric(nces["us_news_rank"], errors="coerce")
        nces = nces.sort_values("us_news_rank").head(top_n)
    else:
        if "enrollment" in nces.columns:
            nces["enrollment"] = pd.to_numeric(nces["enrollment"], errors="coerce")
            nces = nces.sort_values("enrollment", ascending=False).head(top_n)
        else:
            nces = nces.head(top_n)
    if "website_url" in nces.columns:
        nces["domain"] = nces["website_url"].fillna("").apply(
            lambda u: u.replace("https://", "").replace("http://", "").split("/")[0] if u else ""
        )
    return nces
