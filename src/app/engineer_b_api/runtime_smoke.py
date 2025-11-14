import os
import tempfile
import subprocess
import logging
from typing import Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def run_runtime_smoke_test(code_str: str, target_filepath: Optional[str] = None, job_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Выполняет пред-валидацию патча через запуск кода в отдельном процессе.

    Args:
        code_str: строка с Python-кодом для проверки.
        target_filepath: путь к файлу, в который будет применён патч (для логирования).
        job_id: идентификатор задачи (для логирования/артефактов).

    Returns:
        (успех: bool, сообщение: str)
    """
    prefix = f"job_{job_id}" if job_id else f"smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Временный файл для проверки
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
        temp_file.write(code_str)
        temp_path = temp_file.name

    try:
        # Запуск кода в subprocess
        result = subprocess.run(
            ['python', temp_path],
            capture_output=True,
            text=True,
            timeout=30  # Таймаут 30 секунд
        )

        if result.returncode != 0:
            stderr_uri = f"{prefix}/smoke/stderr.log"
            stdout_uri = f"{prefix}/smoke/stdout.log"
            # Сохраняем артефакты (условно, в папку отчётов)
            save_artifact(stderr_uri, result.stderr)
            save_artifact(stdout_uri, result.stdout)
            return False, f"Runtime smoke failed with exit code {result.returncode}. Stderr: {result.stderr}"

        # Успешно
        stdout_uri = f"{prefix}/smoke/stdout.log"
        save_artifact(stdout_uri, result.stdout)
        return True, "Runtime smoke test passed."

    except subprocess.TimeoutExpired:
        return False, "Runtime smoke test timed out."

    except Exception as e:
        return False, f"Runtime smoke test failed with unexpected error: {type(e).__name__}: {str(e)}"

    finally:
        # Удаляем временный файл
        try:
            os.unlink(temp_path)
        except OSError:
            pass

def save_artifact(key: str, content: str):
    """
    Условное сохранение артефакта (в реальности — в папку отчётов).
    """
    import os
    from pathlib import Path

    report_dir = Path("workspace/reports/S1_FIX_SELF_DEPLOY/smoke-logs")
    report_dir.mkdir(parents=True, exist_ok=True)
    artifact_path = report_dir / key.replace('/', '_')
    artifact_path.write_text(content, encoding='utf-8')