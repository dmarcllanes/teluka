"""
Gunicorn config — cost-efficient multi-worker setup.

Production start:
  gunicorn -c gunicorn.conf.py main:app

Rule of thumb: workers = (2 × CPU cores) + 1
Railway/Render free tier = 1 shared vCPU → 3 workers
Paid tier (2 vCPU) → 5 workers
"""
import multiprocessing
import os

# ── Worker count ──────────────────────────────────────────────────────────────
_cpus = multiprocessing.cpu_count()
workers = int(os.environ.get("WEB_CONCURRENCY", min(_cpus * 2 + 1, 9)))

# ── Worker class (async-native via uvicorn) ───────────────────────────────────
worker_class = "uvicorn.workers.UvicornWorker"

# ── Bind ──────────────────────────────────────────────────────────────────────
host = os.environ.get("HOST", "0.0.0.0")
port = os.environ.get("PORT", "8000")
bind = f"{host}:{port}"

# ── Timeouts ──────────────────────────────────────────────────────────────────
timeout          = 30    # kill worker if no response in 30s
keepalive        = 5     # keep connections alive 5s (good behind load balancers)
graceful_timeout = 10    # time to finish in-flight requests on restart

# ── Logging ───────────────────────────────────────────────────────────────────
accesslog  = "-"         # stdout
errorlog   = "-"         # stderr
loglevel   = os.environ.get("LOG_LEVEL", "info")
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'

# ── Process naming ────────────────────────────────────────────────────────────
proc_name = "teluka"

# ── Preload (loads app once, forks — saves memory, speeds up cold start) ─────
preload_app = True
