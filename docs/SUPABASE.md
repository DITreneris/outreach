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

## Security

- Never commit `.env` or the **service_role** key.
- Use **service_role** on Railway, not the publishable key, for production sends.
