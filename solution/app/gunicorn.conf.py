"""Gunicorn settings tuned for Kubernetes."""

import os

bind = f"0.0.0.0:{os.getenv('PORT', '8080')}"
workers = int(os.getenv("WEB_CONCURRENCY", "1"))  # metrics are per-process; scale with pods
threads = int(os.getenv("GUNICORN_THREADS", "4"))
timeout = 30
graceful_timeout = 25  # < terminationGracePeriodSeconds (30)
keepalive = 75  # > typical cloud LB idle timeout (60s) to avoid 502s
accesslog = None  # the app emits structured access logs itself
worker_tmp_dir = "/dev/shm"  # noqa: S108 - avoid heartbeat stalls on slow/readonly disks
