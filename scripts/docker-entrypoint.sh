#!/bin/sh
set -e
PORT="${PORT:-8000}"
echo "cpb-outreach: starting uvicorn on 0.0.0.0:${PORT}"
exec uvicorn cpb_outreach.api.main:app --host 0.0.0.0 --port "${PORT}"
