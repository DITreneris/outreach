FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml requirements.txt README.md ./
COPY src ./src
COPY templates ./templates

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY supabase ./supabase
COPY data ./data
COPY docs ./docs
COPY scripts/docker-entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
