# Supabase — project `ncoxilxwjrjbtipfcngr`

**URL:** https://ncoxilxwjrjbtipfcngr.supabase.co

## Env vars

| Variable | Use |
|----------|-----|
| `SUPABASE_URL` | API base (same as `NEXT_PUBLIC_SUPABASE_URL`) |
| `SUPABASE_SERVICE_ROLE_KEY` | **Railway / CLI** — server-only, bypasses RLS |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Client-safe; OK for local dev with this repo’s RLS policies |

Copy [`.env.example`](../.env.example) to `.env` and fill keys from **Dashboard → Settings → API**.

## Apply schema (no CLI required)

In Supabase **SQL Editor**, run in order:

1. [`supabase/migrations/20260516000000_initial_schema.sql`](../supabase/migrations/20260516000000_initial_schema.sql)
2. [`supabase/seed/20260516000001_pilot_campaign.sql`](../supabase/seed/20260516000001_pilot_campaign.sql)

## CLI link (optional)

```bash
npx supabase@latest login
npx supabase@latest link --project-ref ncoxilxwjrjbtipfcngr
npx supabase@latest db push
```

## Import 500 contacts (local CLI only)

Use **service_role** in `.env`. Full steps: [`data/README.md`](../data/README.md).

```powershell
cpb-outreach merge-nces --nces-csv data\nces_raw\schools.csv --school-pool 750
cpb-outreach import-schools --csv data\schools_master.csv
cpb-outreach enrich-contacts --target 500 --school-batch 50
```

Campaign `pilot_50` stays `dry_run = true` until you explicitly go live.

## Railway deploy troubleshooting

1. **Settings → Deploy → Start Command** must be **empty** (use Dockerfile `ENTRYPOINT`).
2. Set `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (or publishable for smoke test).
3. After deploy, open `https://<app>.up.railway.app/` — expect `{"status":"up"}`.
4. If healthcheck fails: check **Deploy Logs** for `cpb-outreach: starting uvicorn on 0.0.0.0:...`

## Security

- Never commit `.env` or the **service_role** key.
- Use **service_role** on Railway, not the publishable key, for production sends.
