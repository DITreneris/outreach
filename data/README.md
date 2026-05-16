# Data files

## NCES CCD (required for merge)

1. Download the latest **Public School** directory CSV from [NCES CCD](https://nces.ed.gov/ccd/files.asp).
2. Save as `data/nces_raw/ccd_schools.csv` (gitignored).

## Rankings (optional, for top-500)

Provide `data/rankings.csv` with columns:

- `school_name`, `city`, `state`, `us_news_rank`

See `data/sample_rankings.csv` for format. Source rankings yourself (U.S. News does not ship a public API).

## Pipeline

```bash
cpb-outreach merge-nces --nces-csv data/nces_raw/ccd_schools.csv --rankings-csv data/rankings.csv
cpb-outreach import-schools --csv data/schools_master.csv
cpb-outreach enrich-contacts --limit 50
```
