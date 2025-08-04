# ──────────────────────────────────────────────────────────────
# 1. Build stage
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /app

ENV PIP_NO_CACHE_DIR=1
COPY requirements.txt .
RUN pip install --upgrade pip && pip wheel -r requirements.txt --wheel-dir /wheels

# ──────────────────────────────────────────────────────────────
# 2. Final runtime stage
# ──────────────────────────────────────────────────────────────
FROM python:3.11-slim
WORKDIR /app

# install wheels as root so console scripts land in /usr/local/bin
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/*

# now drop privileges
RUN groupadd -r app && useradd -m -g app app
USER app

# copy source after switching user (keeps file ownership clean)
COPY --chown=app:app . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
