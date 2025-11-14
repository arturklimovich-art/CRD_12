import os, sys, time, json, signal, socket, logging, subprocess, threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

UV_HOST = os.getenv("UVICORN_HOST", "0.0.0.0")
UV_PORT = int(os.getenv("UVICORN_PORT", "8000"))
SUP_PORT = int(os.getenv("SUPERVISOR_PORT", "8030"))
WORKDIR = Path("/app")
ENV = os.environ.copy()
ENV["PYTHONPATH"] = str(WORKDIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - supervisor - %(levelname)s - %(message)s")
log = logging.getLogger("supervisor")

state = {
    "status": "starting",
    "child_pid": None,
    "last_restart_epoch": time.time(),
}

def tcp_check(host: str, port: int, timeout: float = 0.3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except Exception:
        return False

def code_path_marker():
    try:
        out = subprocess.check_output(
            [sys.executable, "-c",
             "import sys; import importlib; sys.path=sys.path[:1]+['/app']+sys.path[1:]; import intelligent_agent as ia; import app as app_mod; print('CODE_PATH_MARKER:', ia.__file__, app_mod.__file__, sys.path[:4])"],
            cwd=str(WORKDIR), env=ENV, stderr=subprocess.STDOUT, timeout=5
        ).decode("utf-8", "ignore").strip()
        log.info(out)
    except Exception as e:
        log.warning(f"CODE_PATH_MARKER probe failed: {e}")

_child = None

def start_worker():
    global _child
    cmd = ["uvicorn", "app:app", "--host", UV_HOST, "--port", str(UV_PORT), "--no-access-log"]
    log.info(f"Starting worker: {' '.join(cmd)}")
    _child = subprocess.Popen(cmd, cwd=str(WORKDIR), env=ENV, stdout=sys.stdout, stderr=sys.stderr)
    state["child_pid"] = _child.pid
    state["status"] = "starting"
    state["last_restart_epoch"] = time.time()

    for _ in range(120):
        if _child.poll() is not None:
            state["status"] = "failed"
            log.error("Worker exited during start")
            return
        if tcp_check("127.0.0.1", UV_PORT, timeout=0.25):
            state["status"] = "healthy"
            log.info("Worker is healthy (socket up)")
            code_path_marker()
            return
        time.sleep(0.5)
    state["status"] = "failed"
    log.error("Worker start timeout")

def stop_worker(grace_timeout=15):
    global _child
    if not _child or _child.poll() is not None:
        return
    state["status"] = "draining"
    log.info("Stopping worker (SIGTERM)")
    _child.terminate()
    t0 = time.time()
    while time.time() - t0 < grace_timeout:
        if _child.poll() is not None:
            log.info("Worker stopped gracefully")
            return
        time.sleep(0.5)
    log.warning("Grace timeout, SIGKILL")
    _child.kill()
    _child.wait(timeout=5)

def restart_worker():
    stop_worker()
    start_worker()

class Handler(BaseHTTPRequestHandler):
    def _json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            healthy = (_child is not None and _child.poll() is None and tcp_check("127.0.0.1", UV_PORT))
            status = "healthy" if healthy else ("starting" if state["status"] == "starting" else "failed")
            self._json(200, {"status": status, "child_pid": state["child_pid"]})
            return
        elif self.path == "/state":
            self._json(200, state)
            return
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/restart":
            threading.Thread(target=restart_worker, daemon=True).start()
            self._json(202, {"ok": True, "action": "restart"})
            return
        self._json(404, {"error": "not found"})

def sigterm(_signo, _frame):
    log.info("SIGTERM-> stopping")
    stop_worker(grace_timeout=8)
    os._exit(0)

def main():
    signal.signal(signal.SIGTERM, sigterm)
    start_worker()
    srv = HTTPServer(("0.0.0.0", SUP_PORT), Handler)
    log.info(f"Supervisor listening on :{SUP_PORT}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_worker()

if __name__ == "__main__":
    main()
