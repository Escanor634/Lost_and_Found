"""Gunicorn production configuration for Render deployment."""
import os

# Render automatically provides $PORT (typically 10000). Fallback to 5000 for local testing.
port = os.getenv("PORT", "5000")
bind = f"0.0.0.0:{port}"

# Concurrency tuning for Render Free Tier (512MB RAM limit)
# 2 workers with 2 threads each provide concurrency while keeping memory < 300MB
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "2"))
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))

# Direct logs to standard output/error for Render log streaming
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
