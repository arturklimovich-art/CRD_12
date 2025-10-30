import requests

def test_health():
    r = requests.get("http://localhost:8000/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_tasks():
    r = requests.get("http://localhost:8000/tasks?limit=1")
    assert r.status_code == 200
    assert "items" in r.json()

def test_snapshot():
    r = requests.post("http://localhost:8000/system/snapshot", params={"description": "smoke"})
    assert r.status_code == 200
    assert "snapshot_id" in r.json()
