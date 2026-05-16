import pandas as pd

from cpb_outreach.enrich.merge_nces import (
    dedupe_by_domain,
    extract_domain,
    filter_school_directory,
)


def test_extract_domain():
    assert extract_domain("http://www.albertk12.org/path") == "albertk12.org"


def test_filter_school_directory_high_open_website():
    df = pd.DataFrame(
        [
            {
                "school_name": "A High",
                "state": "AL",
                "sy_status": "1",
                "level": "High",
                "website_url": "http://a.example.org",
            },
            {
                "school_name": "B Elem",
                "state": "AL",
                "sy_status": "1",
                "level": "Elementary",
                "website_url": "http://b.example.org",
            },
            {
                "school_name": "C Closed",
                "state": "AL",
                "sy_status": "2",
                "level": "High",
                "website_url": "http://c.example.org",
            },
            {
                "school_name": "D No Web",
                "state": "AL",
                "sy_status": "1",
                "level": "High",
                "website_url": "",
            },
        ]
    )
    out = filter_school_directory(df, level="High", open_only=True)
    assert len(out) == 1
    assert out.iloc[0]["school_name"] == "A High"


def test_dedupe_by_domain():
    df = pd.DataFrame(
        [
            {"school_name": "B School", "website_url": "http://shared.k12.al.us"},
            {"school_name": "A School", "website_url": "http://www.shared.k12.al.us"},
        ]
    )
    out = dedupe_by_domain(df)
    assert len(out) == 1
    assert out.iloc[0]["school_name"] == "A School"
