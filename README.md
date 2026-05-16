# outreach

**GitHub:** [github.com/DITreneris/outreach](https://github.com/DITreneris/outreach)

School outreach for [Classroom Prompt Builder](https://promptanatomy.online/) — **isolated** from Vercel PDF fulfillment.

| | Fulfillment (main repo) | This repo |
|--|-------------------------|-----------|
| Host | Vercel | Railway |
| DB | Upstash Redis | Supabase Postgres |
| Resend | Transactional receipts | Marketing (`news.promptanatomy.online`) |

Operator memo in main repo: [`memo_outreach.md`](../06_DI_Operacine_sistema_mokytojui/memo_outreach.md).

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -e ".[dev]"

cp .env.example .env
# Fill Supabase + Resend + secrets

# Apply SQL in Supabase dashboard or CLI:
#   supabase/migrations/20260516000000_initial_schema.sql
#   supabase/seed/20260516000001_pilot_campaign.sql

uvicorn cpb_outreach.api.main:app --reload
```

## CLI

```bash
cpb-outreach merge-nces --nces-csv data/sample_nces.csv --rankings-csv data/sample_rankings.csv --top-n 2
cpb-outreach import-schools --csv data/schools_master.csv
cpb-outreach enrich-contacts --limit 50
cpb-outreach send-pilot --slug pilot_50 --limit 50
```

Pilot campaign starts with `dry_run = true` in seed SQL. Set `dry_run = false` only after Resend domain warmup and main-repo P0 test-mode E2E.

## Railway

Deploy uses **Dockerfile** (avoids Nixpacks `$NIXPACKS_PATH` build issues).

1. New project → deploy from this repo.
2. **API service** start (set in `railway.toml`): `uvicorn cpb_outreach.api.main:app --host 0.0.0.0 --port $PORT`
3. **Worker service** (optional cron): `python -m cpb_outreach.worker.run_send`
4. Set all vars from [`.env.example`](.env.example).
5. Resend webhook: `POST https://<railway>/webhooks/resend` — see [docs/RESEND_MARKETING_SETUP.md](docs/RESEND_MARKETING_SETUP.md).

## Internal send (protected)

```http
POST /internal/campaigns/pilot_50/send-batch?limit=50
X-Api-Key: <INTERNAL_API_KEY>
```

## Tests

```bash
pytest
```
