web: sh -c 'exec uvicorn cpb_outreach.api.main:app --host 0.0.0.0 --port ${PORT:-8000}'
worker: python -m cpb_outreach.worker.run_send
