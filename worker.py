"""
arq worker process — run alongside the web server.

  python worker.py

Or with gunicorn for the web server:
  gunicorn -c gunicorn.conf.py main:app &
  python worker.py
"""
import logging
import os

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from lib.jobs import WorkerSettings   # noqa: E402  (after dotenv)

if __name__ == "__main__":
    import asyncio
    from arq import run_worker
    run_worker(WorkerSettings, watch="lib")
