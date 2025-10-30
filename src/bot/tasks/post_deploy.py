# src/bot/tasks/post_deploy.py
# Минимальная post-health валидация деплоя без внешних зависимостей (urllib)

from __future__ import annotations
import time
import urllib.request
import urllib.error
from typing import Tuple, Dict

def _get(url: str, timeout: float) -> Tuple[int, str]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            body = (resp.read() or b"").decode("utf-8", "replace")
            return code, body
    except urllib.error.HTTPError as e:
        try:
            body = (e.read() or b"").decode("utf-8", "replace")
        except Exception:
            body = ""
        return e.code, body
    except Exception:
        return -1, ""

def wait_post_deploy(
    base_url: str,
    timeout_sec: float = 60.0,
    poll_interval_sec: float = 2.0,
    min_consecutive_ok: int = 2,
    ready_path: str = "/ready"
) -> Tuple[bool, Dict]:
    """
    Ждём подтверждения пост-деплоя от сервиса Engineer B:
      - Успех: min_consecutive_ok подряд ответов 200 на /ready
      - Неуспех: любой устойчивый статус (404/500/503) либо истечение таймаута
    Возвращает (ok, details)
    """
    deadline = time.monotonic() + timeout_sec
    ok_streak = 0
    last_status = None

    url = base_url.rstrip("/") + ready_path
    while time.monotonic() < deadline:
        code, _ = _get(url, timeout=poll_interval_sec)
        last_status = code

        if code == 200:
            ok_streak += 1
            if ok_streak >= min_consecutive_ok:
                return True, {"last_status": code, "ok_streak": ok_streak}
        else:
            ok_streak = 0  # сбрасываем полосу успехов на любой не-200

        time.sleep(poll_interval_sec)

    return False, {"last_status": last_status, "ok_streak": ok_streak}
