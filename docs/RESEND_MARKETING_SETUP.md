# Resend marketing domain setup

Separate from Vercel fulfillment (`FULFILLMENT_FROM_EMAIL` on `promptanatomy.app` / receipts).

## 1. Subdomain

Use **`news.promptanatomy.online`** (or your chosen subdomain). Do not send cold outreach from the receipt sender domain.

## 2. Resend dashboard

1. **Domains** → Add `news.promptanatomy.online`.
2. Add DNS records at your registrar (SPF, DKIM, optional DMARC).
3. Wait until domain status is **Verified**.

## 4. Sender

Set Railway env:

```env
OUTREACH_FROM_EMAIL=hello@news.promptanatomy.online
OUTREACH_FROM_NAME=Prompt Anatomy
```

## 5. Webhook

1. **Webhooks** → endpoint `https://<your-railway-app>/webhooks/resend`
2. Events: `email.bounced`, `email.complained`
3. Copy signing secret → `RESEND_WEBHOOK_SECRET`

## 6. API key

Prefer a **dedicated** Resend API key for Railway only (not the Vercel fulfillment key).

## 7. Warmup (week 1)

- `campaigns.daily_cap` = 50 for `pilot_50`
- Keep `dry_run = true` until test sends to your own inboxes succeed
- Monitor bounce rate &lt; 2%, complaint rate &lt; 0.05%

## 8. Go live

```sql
update campaigns set dry_run = false, status = 'active' where slug = 'pilot_50';
```

Only after [main repo todo.md P0 §2](https://github.com/DITreneris/teacher/blob/main/todo.md) test-mode E2E is complete.
