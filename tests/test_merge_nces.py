from pathlib import Path

from cpb_outreach.enrich.merge_nces import build_master

DATA = Path(__file__).resolve().parents[1] / "data"


def test_build_master_with_rankings():
    df = build_master(
        DATA / "sample_nces.csv",
        DATA / "sample_rankings.csv",
        school_pool=10,
        level=None,
        open_only=False,
        dedupe_domain=False,
    )
    assert len(df) == 2
    assert "us_news_rank" in df.columns
    assert df.iloc[0]["school_name"]
