#!/usr/bin/env python3
"""
Supervisor для Engineer_B_API
Запускает uvicorn на порту 8030 и предоставляет health-check
"""

import http.server
import json
import logging
import os
import subprocess
import sys
import time
from pathlib import Path

UV_HOST = os.getenv("UVICORN_HOST", "0.0.0.0")
UV_PORT = int(os.getenv("UVICORN_PORT", "8030"))  # ИЗМЕНЕНО: 8030 вместо 8000
SUP_PORT = int(os.getenv("SUPERVISOR_PORT", "8030"))
WORKDIR = Path("/app")
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(WORKDIR)

log = logging.getLogger("supervisor")
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

_child = None

def start_worker():
    global _child
    cmd = ["uvicorn", "app:app", "--host", UV_HOST, "--port", str(UV_PORT), "--no-access-log"]
    log.info(f"Starting worker: {' '.join(cmd)}")
    _child = subprocess.Popen(cmd, cwd=str(WORKDIR), env=ENV, stdout=sys.stdout, stderr=sys.stderr)

def stop_worker():
    global _child
    if _child:
        log.info("Stopping worker")
        _child.terminate()
        _child.wait()
        _child = None

def worker_health():
    if not _child:
        return False
    return _child.poll() is None

class SupervisorHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_json(200 if worker_health() else 503, {"status": "healthy" if worker_health() else "unhealthy"})
        else:
            self.send_error(404)

    def send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        log.info(format % args)

def main():
    log.info(f"Supervisor starting on port {SUP_PORT}")
    start_worker()
    
    server = http.server.HTTPServer(("0.0.0.0", SUP_PORT), SupervisorHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Supervisor stopping")
    finally:
        stop_worker()
        server.shutdown()

if __name__ == "__main__":
    main()
