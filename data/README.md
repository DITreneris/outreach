# Data files

Large NCES extracts stay in `data/nces_raw/` (gitignored). Never commit `schools.csv` or `schools_master.csv`.

## Source: NCES Public School Directory

Use **`schools.csv`** (columns `SCH_NAME`, `NCESSCH`, `WEBSITE`, `LEVEL`, `SY_STATUS`, `ST`).

Save as: `data/nces_raw/schools.csv` **or** pass the file path directly (no copy needed):

```text
--nces-csv "..\..\06_DI_Operacine_sistema_mokytojui\schools.csv"
```

Do **not** use LEA finance files (`LEAID`, `NAME`, `STABBR` only) for contact scraping — no per-school websites.

## Pipeline: 500 contacts into Supabase

Prerequisites: `.env` with `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.

```powershell
cd cpb-school-outreach
.\.venv\Scripts\activate
pip install -e .

# 1) 750 High + Open + WEBSITE, one row per domain
cpb-outreach merge-nces --nces-csv data\nces_raw\schools.csv --school-pool 750 --output data\schools_master.csv

# 2) Upsert schools (batches of 100)
cpb-outreach import-schools --csv data\schools_master.csv

# 3) Scrape until 500 contacts with outreach_status=ready (30–90 min)
cpb-outreach enrich-contacts --target 500 --school-batch 50
```

Re-run step 3 if `contacts_ready_total` is below 500 (idempotent).

## QA in Supabase SQL Editor

```sql
select count(*) from schools;
select count(*) from contacts where outreach_status = 'ready';
select email_source, count(*) from contacts group by 1 order by 2 desc;
```

## Optional rankings

`data/rankings.csv`: `school_name`, `city`, `state`, `us_news_rank` — use `--rankings-csv` on merge-nces.
