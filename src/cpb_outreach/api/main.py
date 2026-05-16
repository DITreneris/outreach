import json

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse

from cpb_outreach.config import get_settings
from cpb_outreach.db import get_supabase, normalize_email
from cpb_outreach.suppressions import suppress_email
from cpb_outreach.unsubscribe_tokens import verify_unsubscribe_token

app = FastAPI(title="CPB School Outreach", version="0.1.0")


@app.get("/health")
def health() -> dict:
    settings = get_settings()
    ok = bool(settings.supabase_url and settings.supabase_api_key())
    return {"ok": ok, "service": "cpb-school-outreach"}


def _verify_internal_key(x_api_key: str | None) -> None:
    expected = get_settings().internal_api_key
    if not expected or x_api_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/internal/campaigns/{slug}/send-batch")
def send_batch(slug: str, limit: int | None = None, x_api_key: str | None = Header(default=None)):
    _verify_internal_key(x_api_key)
    from cpb_outreach.sender import run_campaign_batch

    return run_campaign_batch(slug, limit=limit)


@app.post("/webhooks/resend")
async def resend_webhook(request: Request):
    settings = get_settings()
    payload = await request.body()
    payload_str = payload.decode("utf-8")

    svix_id = request.headers.get("svix-id")
    svix_timestamp = request.headers.get("svix-timestamp")
    svix_signature = request.headers.get("svix-signature")
    secret = settings.resend_webhook_secret

    if secret and svix_id and svix_timestamp and svix_signature:
        import resend

        resend.api_key = settings.resend_api_key or "re_placeholder"
        resend.Webhooks.verify(
            {
                "payload": payload_str,
                "headers": {
                    "id": svix_id,
                    "timestamp": svix_timestamp,
                    "signature": svix_signature,
                },
                "webhook_secret": secret,
            }
        )
    elif secret:
        raise HTTPException(status_code=400, detail="Missing Svix headers")

    event = json.loads(payload_str)
    event_type = event.get("type", "")
    data = event.get("data", {}) or {}
    to_list = data.get("to") or []
    email = to_list[0] if to_list else data.get("email")
    message_id = data.get("email_id") or data.get("id")

    if not email:
        return {"received": True, "type": event_type, "skipped": "no_email"}

    normalized = normalize_email(email)
    sb = get_supabase()

    if event_type == "email.bounced":
        suppress_email(normalized, "hard_bounce", str(message_id) if message_id else None)
        sb.table("contacts").update({"outreach_status": "bounced"}).eq("email", normalized).execute()
    elif event_type == "email.complained":
        suppress_email(normalized, "complaint", str(message_id) if message_id else None)
        sb.table("contacts").update({"outreach_status": "complained"}).eq("email", normalized).execute()

    return {"received": True, "type": event_type}


@app.api_route("/unsubscribe", methods=["GET", "POST"])
async def unsubscribe(request: Request):
    if request.method == "POST":
        form = await request.form()
        email = form.get("email") or request.query_params.get("email")
        token = form.get("token") or request.query_params.get("token")
        list_unsubscribe = request.headers.get("List-Unsubscribe") == "One-Click"
        if list_unsubscribe and not token:
            token = request.query_params.get("token")
    else:
        email = request.query_params.get("email")
        token = request.query_params.get("token")

    if not email or not token:
        return HTMLResponse("<p>Invalid unsubscribe link.</p>", status_code=400)

    normalized = normalize_email(str(email))
    if not verify_unsubscribe_token(normalized, str(token)):
        return HTMLResponse("<p>Invalid or expired unsubscribe link.</p>", status_code=400)

    suppress_email(normalized, "unsubscribe")
    get_supabase().table("contacts").update({"outreach_status": "opted_out"}).eq(
        "email", normalized
    ).execute()

    if request.method == "POST":
        return PlainTextResponse("", status_code=200)

    return HTMLResponse(
        "<p>You have been unsubscribed from Prompt Anatomy school outreach emails.</p>",
        status_code=200,
    )
