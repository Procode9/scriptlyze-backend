"""
Gunicorn configuration for production
"""

import os

# Bind
bind = f"0.0.0.0:{os.getenv('PORT', 8000)}"

# Workers
workers = int(os.getenv('WEB_CONCURRENCY', 4))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100

# Timeouts
timeout = 120
keepalive = 5
graceful_timeout = 30

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "scriptlyze-api"

# Preload
preload_app = True


# Server hooks
def on_starting(server):
    print("🚀 Starting ScriptLyze API")


def when_ready(server):
    print(f"✅ Server ready. Workers: {workers}")


def worker_int(worker):
    print(f"⚠️  Worker {worker.pid} interrupted")


def post_fork(server, worker):
    print(f"✅ Worker {worker.pid} spawned")
