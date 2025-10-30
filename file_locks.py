import os
import time
import hashlib
import json
import fcntl
from pathlib import Path
from typing import Optional, Dict, Any

class FileLockManager:
    def __init__(self, locks_dir: str = "/app/.locks", idempotency_dir: str = "/app/.idempotency"):
        self.locks_dir = Path(locks_dir)
        self.idempotency_dir = Path(idempotency_dir)
        self.locks_dir.mkdir(exist_ok=True)
        self.idempotency_dir.mkdir(exist_ok=True)
    
    def _get_lock_path(self, target_path: str) -> Path:
        """Получить путь к файлу блокировки"""
        lock_name = hashlib.sha256(target_path.encode()).hexdigest()[:16] + ".lock"
        return self.locks_dir / lock_name
    
    def _get_idempotency_path(self, idempotency_key: str) -> Path:
        """Получить путь к файлу идемпотентности"""
        return self.idempotency_dir / f"{idempotency_key}.json"
    
    def acquire_lock(self, target_path: str, timeout_s: int = 30) -> bool:
        """Захватить файловую блокировку"""
        lock_path = self._get_lock_path(target_path)
        start_time = time.time()
        
        while time.time() - start_time < timeout_s:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_RDWR)
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                # Записываем PID для отладки
                os.write(fd, str(os.getpid()).encode())
                return True
            except (IOError, BlockingIOError):
                time.sleep(0.1)
            except Exception as e:
                print(f"Ошибка при захвате блокировки: {e}")
                break
        
        return False
    
    def release_lock(self, target_path: str):
        """Освободить файловую блокировку"""
        lock_path = self._get_lock_path(target_path)
        try:
            if lock_path.exists():
                lock_path.unlink()
        except Exception as e:
            print(f"Ошибка при освобождении блокировки: {e}")
    
    def check_idempotency(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Проверить идемпотентность"""
        idemp_path = self._get_idempotency_path(idempotency_key)
        if idemp_path.exists():
            try:
                with open(idemp_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка чтения файла идемпотентности: {e}")
        return None
    
    def save_idempotency(self, idempotency_key: str, result: Dict[str, Any]):
        """Сохранить результат для идемпотентности"""
        idemp_path = self._get_idempotency_path(idempotency_key)
        try:
            with open(idemp_path, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            print(f"Ошибка сохранения идемпотентности: {e}")

def generate_idempotency_key(target_file: str, code: str, task_text: str) -> str:
    """Генерация ключа идемпотентности"""
    normalized_task = task_text.strip().lower()
    content = f"{target_file}|{code}|{normalized_task}"
    return hashlib.sha256(content.encode()).hexdigest()
