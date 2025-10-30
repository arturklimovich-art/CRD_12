import json
import os
import urllib.request
import urllib.error
import pytest

def _json_get(url: str, timeout: float = 3.0):
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
        return json.loads(data)

def test_engineer_b_health_ok():
    data = _json_get("http://localhost:8000/health", timeout=3.0)
    assert isinstance(data, dict)
    assert data.get("status") == "ok"
    assert data.get("service") == "engineer_b_api"

def test_engineer_a_start_optional():
    # Если не настроен бот, пропускаем (зелёный статус)
    start_url = os.getenv("ENGINEER_A_BOT_START_URL", "").strip()
    if not start_url:
        pytest.skip("Engineer A bot not configured; skipping /start contract test.")
    # Иначе — проверяем, что эндпоинт отвечает 200 и не пустой
    try:
        req = urllib.request.Request(start_url, method="GET")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            body = resp.read().decode("utf-8")
            assert resp.status == 200
            assert body is not None and body != ""
    except urllib.error.URLError as e:
        pytest.fail(f"/start unreachable: {e}")
