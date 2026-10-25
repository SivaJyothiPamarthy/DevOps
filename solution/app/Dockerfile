# syntax=docker/dockerfile:1.7
# ---- build stage: compile wheels so the runtime image needs no compilers ----
FROM python:3.12-slim-bookworm AS build
WORKDIR /build
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---- runtime stage ----
FROM python:3.12-slim-bookworm
# In real pipelines pin by digest too: python:3.12-slim-bookworm@sha256:...
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8080

RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /srv
COPY --from=build /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && rm -rf /wheels

COPY --chown=app:app app/ ./app/
COPY --chown=app:app gunicorn.conf.py .

ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}
LABEL org.opencontainers.image.title="orders-service" \
      org.opencontainers.image.version="${APP_VERSION}"

USER 10001:10001
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8080/healthz', timeout=2)" || exit 1

# exec form => gunicorn is PID 1 and receives SIGTERM directly for graceful shutdown
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app.main:create_app()"]
