"""Railway worker entry: send one campaign batch (cron or manual)."""

import os
import sys

from cpb_outreach.sender import run_campaign_batch


def main() -> None:
    slug = os.environ.get("CAMPAIGN_SLUG", "pilot_50")
    limit_raw = os.environ.get("SEND_LIMIT", "50")
    limit = int(limit_raw) if limit_raw.isdigit() else 50
    result = run_campaign_batch(slug, limit=limit)
    print(result, flush=True)
    if result.get("sent", 0) == 0 and result.get("dry_run", 0) == 0:
        sys.exit(0)


if __name__ == "__main__":
    main()
