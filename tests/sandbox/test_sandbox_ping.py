import time
import pytest

# Жёстко запрещаем сеть/файловую систему внутри sandbox-теста
class _NoFS:
    def __call__(self, *a, **k):
        raise RuntimeError("FS access is not allowed in sandbox")

class _NoSocket:
    def __init__(self, *a, **k):
        raise RuntimeError("Network is not allowed in sandbox")

def test_ping_sandbox_no_io(monkeypatch):
    # Запрет open()
    monkeypatch.setattr("builtins.open", _NoFS(), raising=True)
    # Запрет socket.socket
    import socket
    monkeypatch.setattr(socket, "socket", _NoSocket, raising=True)

    t0 = time.perf_counter()

    from agents.trader.core.ping import ping
    assert ping() == "pong"

    elapsed = time.perf_counter() - t0
    assert elapsed < 15.0, f"sandbox timeout exceeded: {elapsed:.3f}s"
