# -*- coding: utf-8 -*-
from fastapi import FastAPI, HTTPException
from datetime import datetime
import logging
from typing import Any, Dict, Optional, Tuple
import os
import json
import asyncio
import httpx
import re

# === S1-FIX-SELF-DEPLOY: Step 3 (imports) START ===
import subprocess
import sys
import tempfile
import textwrap
import shutil
import signal
import hashlib
# === S1-FIX-SELF-DEPLOY: Step 3 (imports) END ===

# === Шаг 7: события/артефакты — безопасные заглушки при недоступности core.event_bus ===
try:
    from core.event_bus import put_event, upload_artifact, sha256_str, ensure_events_table
except Exception:
    def put_event(*args, **kwargs):  # type: ignore
        return None
    def upload_artifact(*args, **kwargs):  # type: ignore
        return None
    def sha256_str(s: str) -> str:  # type: ignore
        return hashlib.sha256((s or "").encode("utf-8", "replace")).hexdigest()
    def ensure_events_table():  # type: ignore
        return None

# === [IDEMPOTENCY/LOCKS] Импорты с безопасным fallback ===
# Ожидаемые реальные модули: locks.py и idempotency.py рядом с приложением.
try:
    from locks import LockManager  # type: ignore
except Exception:  # безопасная in-memory заглушка
    class _LockToken:
        def __init__(self, key: str) -> None:
            self.key = key
    class _FallbackLockManager:
        def __init__(self) -> None:
            # простая in-memory блокировка на процесс
            self._locks: Dict[str, int] = {}
            self._loop = asyncio.get_event_loop()
        class _Ctx:
            def __init__(self, mgr: "_FallbackLockManager", key: str) -> None:
                self.mgr = mgr
                self.key = key
            async def __aenter__(self):
                # наивная reentrant-семафора на ключ
                while self.mgr._locks.get(self.key, 0) > 0:
                    await asyncio.sleep(0.01)
                self.mgr._locks[self.key] = 1
                return _LockToken(self.key)
            async def __aexit__(self, exc_type, exc, tb):
                try:
                    self.mgr._locks.pop(self.key, None)
                except Exception:
                    pass
        def acquire_lock(self, key: Optional[str]):
            return self._Ctx(self, key or "/app/.global")
    LockManager = _FallbackLockManager  # type: ignore

try:
    from idempotency import IdempotencyManager  # type: ignore
except Exception:
    class _FallbackIdempotencyManager:
        """Простая in-memory идемпотентность. В бою заменяется на версию с PostgreSQL (core.patches)."""
        def __init__(self) -> None:
            self._store: Dict[str, Dict[str, Any]] = {}
        async def get_existing_result(self, key: str) -> Optional[Dict[str, Any]]:
            return self._store.get(key)
        async def update_patch_status(self, key: str, status: str, result: Dict[str, Any]) -> None:
            self._store[key] = {"status": status, "result": result, "updated_at": datetime.utcnow().isoformat()}
    IdempotencyManager = _FallbackIdempotencyManager  # type: ignore

# Важное замечание: LLMRouter может отличаться по сигнатуре __init__
from llm_router import LLMRouter
from intelligent_agent import IntelligentAgent, DeepSeekExecutor
from curator import Curator

# =============================================================================
# Конфигурация логирования
# =============================================================================
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)-8s - %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Конфиг
DEEPSEEK_URL = os.getenv("DEEPSEEK_PROXY_URL", "http://deepseek_proxy:8010/llm/complete").rstrip("/")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")

# Единый корень кода рантайма
APP_ROOT_PATH = "/app"

# Детектор целевого файла из текста задачи
_FILEPATH_RE = re.compile(r"(?:Modify|Patch|Edit|Fix)\s+([\w\./\-_]+\.py)", re.IGNORECASE)

app = FastAPI(title="Engineer B API", version="4.0 - Self-Healing")

# === CODE_PATH_MARKER START ===
import sys as _sys
log = logging.getLogger(__name__)
try:
    import intelligent_agent as ia
    log.info("CODE_PATH_MARKER app=%s ia=%s SYSPATH_HEAD=%s", __file__, getattr(ia, "__file__", None), _sys.path[:4])
except Exception as e:
    log.warning("CODE_PATH_MARKER failed: %s", e)
# === CODE_PATH_MARKER END ===

agent: Optional[IntelligentAgent] = None
llm_router: Optional[LLMRouter] = None
deepseek_executor: Optional[DeepSeekExecutor] = None

# =============================================================================
# Утилиты
# =============================================================================
_CODE_FENCE = re.compile(r"```(?:python|py)?\s*(?P<code>[\s\S]*?)\s*```", re.IGNORECASE | re.DOTALL)
_JSON_FENCE = re.compile(r"```json\s*(?P<json>[\s\S]*?)\s*```", re.IGNORECASE | re.DOTALL)
_AUTO_REPORT = re.compile(r"===\s*Analysis Report\s*===.*?```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE | re.DOTALL)

def _extract_code(text: str) -> str:
    m = _CODE_FENCE.search(text or "")
    if not m:
        return ""
    s = (m.group("code") or "").strip()
    if s.startswith("{") and s.endswith("}"):
        return ""
    return s

def _extract_report_json(text: str) -> Dict[str, Any]:
    m = _AUTO_REPORT.search(text or "")
    raw = None
    if m:
        raw = m.group(1).strip()
    else:
        j = _JSON_FENCE.search(text or "")
        raw = j.group("json").strip() if j else None
    if not raw:
        return {"deployment_ready": False, "description": "Could not find final report block in LLM response.", "tests_status": "error"}
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse report JSON: %s", e)
        return {"deployment_ready": False, "description": "Could not parse report JSON from LLM response.", "tests_status": "error"}

# --- Проверка что путь в пределах /app ---
def _under_app_root(path: str) -> bool:
    try:
        if not path:
            return False
        rp = os.path.realpath(path)
        rr = os.path.realpath(APP_ROOT_PATH)
        return rp == rr or rp.startswith(rr + os.sep)
    except Exception:
        return False

# === [IDEMPOTENCY/LOCKS] Генерация ключа идемпотентности ===
def generate_idempotency_key(target_path: Optional[str], code: str, task_text: str) -> str:
    """Детерминированный ключ по целевому пути, коду и тексту задачи."""
    norm_path = (target_path or "").strip()
    h_code = hashlib.sha256((code or "").encode("utf-8", "replace")).hexdigest()
    h_task = hashlib.sha256((task_text or "").encode("utf-8", "replace")).hexdigest()
    base = f"{norm_path}|{h_code}|{h_task}"
    return hashlib.sha256(base.encode("utf-8", "replace")).hexdigest()

# =============================================================================
# Step 3 — Runtime-Smoke
# =============================================================================
def _run_runtime_smoke_test(code_str: str, target_filepath: Optional[str], job_id: Optional[str] = None) -> Tuple[bool, str]:
    if not code_str:
        return False, "Runtime Smoke: Code is empty."
    logger.info("[Runtime Smoke] Starting test in subprocess...")
    tmp_filepath = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as tmp_file:
            dedented_code = textwrap.dedent(code_str).lstrip("\ufeff")
            tmp_file.write(dedented_code)
            tmp_filepath = tmp_file.name
        cmd = [_sys.executable, tmp_filepath]
        logger.debug("[Runtime Smoke] Executing command: %s", " ".join(cmd))
        process = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15, check=False)
        stdout = (process.stdout or "").strip()
        stderr = (process.stderr or "").strip()
        exit_code = process.returncode
        logger.debug("[Runtime Smoke] Subprocess finished. Exit code: %d", exit_code)
        if stdout:
            logger.debug("[Runtime Smoke] Subprocess stdout:\n%s", stdout[:500])
        if stderr:
            logger.debug("[Runtime Smoke] Subprocess stderr:\n%s", stderr[:500])
        try:
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            prefix = f"engineer_b_api/{job_id}/{ts}" if job_id else f"engineer_b_api/{ts}"
            stdout_key = f"{prefix}/smoke/stdout.log"
            stderr_key = f"{prefix}/smoke/stderr.log"
            stdout_b = stdout.encode("utf-8", "replace") if stdout else b""
            stderr_b = stderr.encode("utf-8", "replace") if stderr else b""
            stdout_uri = upload_artifact(stdout_key, stdout_b, "text/plain") or stdout_key
            stderr_uri = upload_artifact(stderr_key, stderr_b, "text/plain") or stderr_key
        except Exception:
            stdout_uri, stderr_uri = "stdout", "stderr"
        if exit_code != 0:
            error_msg = f"Runtime Smoke Failed: Subprocess exited with code {exit_code}."
            if stderr:
                error_msg += f" Stderr: {stderr[:300]}"
            logger.warning(error_msg)
            try:
                put_event(stage="smoke", event_type="runtime_smoke_failed", context={"exit_code": exit_code, "stderr_key": stderr_uri, "stdout_key": stdout_uri})
            except Exception:
                pass
            return False, error_msg
        else:
            is_app_py = bool(target_filepath) and (os.path.basename(target_filepath) == "app.py")
            if is_app_py:
                logger.debug("[Runtime Smoke] Target is app.py, checking syntax only...")
                try:
                    with open(tmp_filepath, "r", encoding="utf-8") as f:
                        compile(f.read(), tmp_filepath, "exec")
                except SyntaxError as syn_err:
                    return False, f"Runtime Smoke Failed: Syntax error in app.py - {syn_err}"
                except Exception as e:
                    logger.info("[Runtime Smoke] app.py dependencies check skipped: %s", e)
            logger.info("[Runtime Smoke] Test passed.")
            try:
                put_event(stage="smoke", event_type="runtime_smoke_ok", context={"stderr_key": stderr_uri, "stdout_key": stdout_uri})
            except Exception:
                pass
            return True, "Runtime Smoke OK"
    except subprocess.TimeoutExpired:
        logger.warning("[Runtime Smoke] Test timed out after 15s.")
        try:
            put_event(stage="smoke", event_type="runtime_smoke_failed", context={"reason": "timeout"})
        except Exception:
            pass
        return False, "Runtime Smoke Failed: Test execution timed out."
    except Exception as e:
        logger.exception("[Runtime Smoke] Unexpected error during test.")
        try:
            put_event(stage="smoke", event_type="runtime_smoke_failed", context={"reason": f"unexpected_error:{type(e).__name__}"})
        except Exception:
            pass
        return False, f"Runtime Smoke Failed: Unexpected error - {type(e).__name__}: {e}"
    finally:
        if tmp_filepath and os.path.exists(tmp_filepath):
            try:
                os.remove(tmp_filepath)
                logger.debug("[Runtime Smoke] Cleaned up temp file: %s", tmp_filepath)
            except Exception as e_clean:
                logger.warning("Failed to clean up temp file %s: %s", tmp_filepath, e_clean)

# =============================================================================
# Поиск целевого файла
# =============================================================================
def _get_target_filepath(task_text: str) -> Optional[str]:
    match = _FILEPATH_RE.search(task_text or "")
    if not match:
        logger.info("Auto-applying code regardless of path detection")
        return None
    relative_path = match.group(1).replace("\\", "/")
    logger.info("Found relative path in prompt: %s", relative_path)
    if relative_path.startswith("src/app/engineer_b_api/"):
        file_name = relative_path.replace("src/app/engineer_b_api/", "", 1)
        container_path = os.path.join(APP_ROOT_PATH, file_name)
        safe_path = os.path.normpath(container_path)
        logger.info("Mapped to container path: %s", safe_path)
        return safe_path
    if relative_path in {"app.py", "intelligent_agent.py", "llm_router.py", "tools.py"}:
        safe_path = os.path.normpath(os.path.join(APP_ROOT_PATH, relative_path))
        logger.info("Mapped known filename to container path: %s", safe_path)
        return safe_path
    if relative_path.startswith("/app/"):
        safe_path = os.path.normpath(relative_path)
        if safe_path == APP_ROOT_PATH or safe_path.startswith(APP_ROOT_PATH + os.sep):
            logger.info("Using absolute container path: %s", safe_path)
            return safe_path
    logger.warning("Path %s is not recognized for this agent. Expected 'src/app/engineer_b_api/...', '/app/...', or a known filename.", relative_path)
    return None

# === S1-FIX-SELF-DEPLOY: Step 4 START ===
def _apply_code_changes(filepath: str, code: str) -> Tuple[bool, str]:
    safe_path = os.path.normpath(filepath)
    if not (safe_path == APP_ROOT_PATH or safe_path.startswith(APP_ROOT_PATH + os.sep)):
        logger.error("SECURITY ERROR: Attempted to write outside of %s: %s", APP_ROOT_PATH, safe_path)
        return False, f"SECURITY ERROR: Path {safe_path} is outside the {APP_ROOT_PATH} directory."
    backup_path = f"{safe_path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    temp_filepath = ""
    file_dir = os.path.dirname(safe_path) or "."
    try:
        old_hash = ""
        if os.path.exists(safe_path):
            with open(safe_path, "rb") as f:
                old_hash = hashlib.sha256(f.read()).hexdigest()
        new_hash = sha256_str(code)
        put_event(stage="patch", event_type="patch_write_started", context={"target_file": safe_path, "new_sha256": new_hash, "old_sha256": old_hash})
    except Exception:
        pass
    try:
        if os.path.exists(safe_path):
            shutil.move(safe_path, backup_path)
            logger.info("Created unique backup: %s", backup_path)
        else:
            logger.info("Target file %s does not exist, creating new.", safe_path)
            os.makedirs(file_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tmp", dir=file_dir, delete=False, encoding="utf-8") as tmp_file:
            temp_filepath = tmp_file.name
            logger.debug("Writing code to temporary file: %s", temp_filepath)
            tmp_file.write(code)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        logger.debug("Atomically replacing %s with %s", safe_path, temp_filepath)
        os.replace(temp_filepath, safe_path)
        try:
            dir_fd = os.open(file_dir, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
        except OSError as fsync_err:
            logger.warning("Could not fsync directory %s: %s", file_dir, fsync_err)
        logger.info("Successfully applied ATOMIC code changes to %s", safe_path)
        try:
            put_event(stage="patch", event_type="patch_written", context={"target_file": safe_path, "backup_path": backup_path, "new_sha256": sha256_str(code)})
        except Exception:
            pass
        return True, f"Atomically applied patch to {safe_path}"
    except Exception as e:
        logger.exception("FAILED to apply ATOMIC code changes to %s: %s", safe_path, e)
        try:
            put_event(stage="patch", event_type="incident", context={"severity": "error", "message": f"apply failed: {e}", "target_file": safe_path})
        except Exception:
            pass
        try:
            if os.path.exists(backup_path):
                if os.path.exists(safe_path):
                    try:
                        os.remove(safe_path)
                    except Exception as rm_err:
                        logger.warning("Could not remove %s before rollback: %s", safe_path, rm_err)
                os.rename(backup_path, safe_path)
                logger.warning("Restored %s from unique backup %s.", safe_path, backup_path)
            elif os.path.exists(safe_path):
                try:
                    os.remove(safe_path)
                    logger.warning("Removed partially created file %s during rollback.", safe_path)
                except Exception as rm2_err:
                    logger.error("Failed to remove partially created file %s: %s", safe_path, rm2_err)
        except Exception as e_restore:
            logger.error("CRITICAL: Failed to restore from backup %s: %s", backup_path, e_restore)
        return False, f"Failed to write file atomically: {e}"
    finally:
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
                logger.debug("Cleaned up temp file: %s", temp_filepath)
            except Exception as e_clean:
                logger.warning("Failed to clean up temp file %s: %s", temp_filepath, e_clean)
# === S1-FIX-SELF-DEPLOY: Step 4 END ===

# =============================================================================
# STARTUP & SHUTDOWN
# =============================================================================
@app.on_event("startup")
async def startup_event():
    global llm_router, agent, deepseek_executor

    # === Step 1: CODE_PATH_MARKER ===
    try:
        import importlib
        from importlib.util import find_spec
        import intelligent_agent as _ia
        agent_path = os.path.realpath(getattr(_ia, "__file__", "") or "")
        app_path = os.path.realpath(__file__)
        logger.info("CODE_PATH_MARKER: app.py = %s", app_path)
        logger.info("CODE_PATH_MARKER: intelligent_agent.py = %s", agent_path)
        spec = find_spec("intelligent_agent")
        if spec and getattr(spec, "origin", None):
            logger.debug("CODE_PATH_MARKER: intelligent_agent.spec.origin = %s", os.path.realpath(spec.origin))
        if not _under_app_root(agent_path):
            logger.error("CRITICAL ERROR: intelligent_agent loaded outside %s ? %s", APP_ROOT_PATH, agent_path)
        if not _under_app_root(app_path):
            logger.error("CRITICAL ERROR: app.py loaded outside %s ? %s", APP_ROOT_PATH, app_path)
    except Exception as e:
        logger.error("CRITICAL ERROR during CODE_PATH_MARKER check: %s", e)

    # Runtime state
    app.state.start_time = datetime.now()
    app.state.analysis_history = []
    app.state.ready = False

    # [IDEMPOTENCY/LOCKS] Инициализация менеджеров
    try:
        app.state.lock_mgr = LockManager()
        logger.info("[LOCKS] LockManager initialized: %s", type(app.state.lock_mgr).__name__)
    except Exception as e:
        logger.warning("[LOCKS] LockManager init failed: %s", e)
        app.state.lock_mgr = None
    try:
        app.state.idempotency_mgr = IdempotencyManager()
        logger.info("[IDEMP] IdempotencyManager initialized: %s", type(app.state.idempotency_mgr).__name__)
    except Exception as e:
        logger.warning("[IDEMP] IdempotencyManager init failed: %s", e)
        app.state.idempotency_mgr = None

    # 1) LLMRouter (Gemini)
    try:
        llm_router = None
        try:
            llm_router = LLMRouter(gemini_api_key=GEMINI_API_KEY, gemini_model_name=GEMINI_MODEL)  # type: ignore[call-arg]
            logger.info("LLMRouter (Gemini) initialized with gemini_api_key/model.")
        except TypeError as te:
            logger.warning("LLMRouter(gemini_api_key=...) unsupported: %s. Try default ctor.", te)
            try:
                llm_router = LLMRouter()  # type: ignore[call-arg]
                logger.info("LLMRouter (Gemini) initialized with default ctor.")
            except Exception as e2:
                logger.warning("LLMRouter default ctor failed: %s. Running without Gemini.", e2)
                llm_router = None
    except Exception as e:
        logger.warning("LLMRouter initialization failed: %s. Running without Gemini.", e)
        llm_router = None

    # 2) DeepSeekExecutor
    deepseek_executor = DeepSeekExecutor(api_url=DEEPSEEK_URL, api_key="")
    logger.info("DeepSeekExecutor initialized (url=%s)", DEEPSEEK_URL)

    # 3) IntelligentAgent
    try:
        agent = IntelligentAgent(llm_router=llm_router, deepseek_executor=deepseek_executor)
        logger.info("IntelligentAgent initialized successfully")
        app.state.ready = True
    except Exception as e:
        agent = None
        app.state.ready = False
        logger.error("IntelligentAgent initialization failed: %s", e)

    # 4) Events table
    try:
        ensure_events_table()
    except Exception:
        pass

    # 5) CURATOR INIT (S1)
    try:
        app.state.curator = Curator(put_event=put_event, upload_artifact=upload_artifact)
        logger.info("Curator initialized")
    except Exception as e:
        logger.warning("Curator init failed: %s", e)
        app.state.curator = None

    logger.info("Engineer B API fully initialized")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Engineer B API...")
    if deepseek_executor and getattr(deepseek_executor, "client", None):
        try:
            await deepseek_executor.client.aclose()
            logger.info("DeepSeekExecutor client closed.")
        except Exception as e:
            logger.warning("Error on DeepSeekExecutor client close: %s", e)
    logger.info("Engineer B API shutdown complete")

# =============================================================================
# Основной эндпоинт анализа — патч/деплой
# =============================================================================
@app.post("/agent/analyze")
async def analyze_task(task_data: Dict[str, Any]):
    if not app.state.ready or agent is None:
        raise HTTPException(status_code=503, detail="Agent not ready")

    user_prompt = (task_data or {}).get("task", "").strip()
    job_id = (task_data or {}).get("job_id") or None
    if not user_prompt:
        result = {
            "status": "failed",
            "analysis": "Task prompt was empty, no action taken.",
            "is_complete": False,
            "generated_code": "",
            "report": {"deployment_ready": False, "description": "Empty task", "tests_status": "skipped"},
        }
        # [IDEMP] пустые задачи не кэшируем
        return result

    logger.info("Received task: %s", user_prompt[:160])

    # локальный помощник для безопасного обновления идемпотентности
    async def _try_update_idemp(idemp_key: Optional[str], status: str, result_obj: Dict[str, Any]) -> None:
        mgr = getattr(app.state, "idempotency_mgr", None)
        if not (mgr and idemp_key):
            return
        try:
            await mgr.update_patch_status(idemp_key, status, result_obj)
        except Exception:
            pass

    try:
        analysis_result = await agent.run_cycle(user_prompt)
        logger.debug("Received analysis_result from agent.run_cycle (type %s): %s", type(analysis_result).__name__, analysis_result)

        generated_code: str = ""
        report_data: Dict[str, Any] = {"deployment_ready": False, "description": "No report", "tests_status": "error"}
        analysis_text_for_debug: str = ""

        if isinstance(analysis_result, dict):
            analysis_text_for_debug = analysis_result.get("raw") or ""
        else:
            analysis_text_for_debug = str(analysis_result)

        if isinstance(analysis_result, dict):
            code_field = analysis_result.get("code") or ""
            if code_field:
                generated_code = code_field.strip()
            else:
                generated_code = _extract_code(analysis_text_for_debug)
        else:
            generated_code = _extract_code(analysis_text_for_debug)

        rep = None
        if isinstance(analysis_result, dict):
            rep = analysis_result.get("report")
        if isinstance(rep, dict):
            report_data = rep
        elif isinstance(rep, str):
            report_data = _extract_report_json(rep)
        else:
            report_data = _extract_report_json(analysis_text_for_debug or "")

        logger.debug("Extracted generated_code (first 200 chars): %s", (generated_code[:200] if generated_code else "None"))
        logger.debug("Extracted report_data: %s", report_data)

        agent_status = (analysis_result.get("status") if isinstance(analysis_result, dict) else None) or "error"
        smoke_test_ok = (agent_status in ("ok", "passed", "success"))

        final_status_for_orchestrator = "failed"

        # === PATCH: Step 3 - Call Runtime Smoke Test ===
        target_file = _get_target_filepath(user_prompt)
        runtime_smoke_ok, runtime_smoke_msg = False, "Skipped (no code or agent failed)"
        if smoke_test_ok and generated_code:
            runtime_smoke_ok, runtime_smoke_msg = _run_runtime_smoke_test(generated_code, target_file, job_id=job_id)

        # [IDEMPOTENCY/LOCKS] — сформируем/проверим ключ после извлечения target_file и кода
        idempotency_key: Optional[str] = (task_data or {}).get("idempotency_key")
        if not idempotency_key:
            idempotency_key = generate_idempotency_key(target_file, generated_code or "", user_prompt)

        mgr = getattr(app.state, "idempotency_mgr", None)
        if mgr and idempotency_key:
            try:
                existing = await mgr.get_existing_result(idempotency_key)
            except Exception:
                existing = None
            if existing and isinstance(existing, dict) and "result" in existing:
                logger.info("[IDEMP] Returning cached result for key=%s", idempotency_key[:16])
                return existing["result"]  # ранний возврат из кэша

        if smoke_test_ok and runtime_smoke_ok and generated_code:
            if target_file:
                logger.info("Both smoke tests passed. Attempting to apply changes to: %s", target_file)

                # === Gate: Проверка политики Куратора (Белые пути/Уровень критичности) ===
                cur = getattr(app.state, "curator", None)
                if cur is None:
                    logger.warning("Curator unavailable; rejecting by policy.")
                    final_status_for_orchestrator = "failed"
                    report_data["description"] = "Curator unavailable."
                    report_data["tests_status"] = "error"
                    report_data["deployment_ready"] = False
                    result = {
                        "status": final_status_for_orchestrator,
                        "analysis": analysis_text_for_debug,
                        "is_complete": False,
                        "generated_code": generated_code,
                        "report": report_data,
                    }
                    await _try_update_idemp(idempotency_key, "failed", result)
                    return result

                review = cur.review(
                    task_text=user_prompt,
                    code=generated_code,
                    target_path=target_file,
                    job_id=job_id,
                    idempotency_key=idempotency_key,
                )
                try:
                    put_event(stage="curator", event_type="curator_review_done",
                              context={"decision": review.get("decision"), "score": review.get("score"), "metrics": review.get("metrics")})
                except Exception:
                    pass
                if review.get("decision") != "approve":
                    reasons = "; ".join(review.get("reasons") or [])
                    logger.warning("Curator rejected patch: %s", reasons)
                    final_status_for_orchestrator = "failed"
                    report_data["description"] = f"Curator rejected: {reasons}"
                    report_data["tests_status"] = "error"
                    report_data["deployment_ready"] = False
                    result = {
                        "status": final_status_for_orchestrator,
                        "analysis": analysis_text_for_debug,
                        "is_complete": False,
                        "generated_code": generated_code,
                        "report": report_data,
                    }
                    await _try_update_idemp(idempotency_key, "failed", result)
                    return result
                # === /Gate ===

                # === [LOCKS] Критическая секция применения патча под блокировкой ===
                applied_ok: bool
                apply_msg: str
                lock_mgr = getattr(app.state, "lock_mgr", None)
                if lock_mgr:
                    async with lock_mgr.acquire_lock(target_file):
                        applied_ok, apply_msg = _apply_code_changes(target_file, generated_code)
                else:
                    applied_ok, apply_msg = _apply_code_changes(target_file, generated_code)

                if applied_ok:
                    final_status_for_orchestrator = "passed"
                    # === PATCH: Step 5 - Send SIGHUP ===
                    try:
                        supervisor_pid = 1
                        logger.info("Patch applied. Sending SIGHUP to Supervisor PID %s for worker restart...", supervisor_pid)
                        os.kill(supervisor_pid, signal.SIGHUP)
                        logger.info("SIGHUP signal sent.")
                        try:
                            put_event(stage="deploy", event_type="restart_requested", context={"signal": "SIGHUP", "supervisor_pid": supervisor_pid})
                        except Exception:
                            pass
                    except AttributeError:
                        logger.warning("SIGHUP signal not available on this platform (Windows?). Cannot trigger worker restart.")
                    except ProcessLookupError:
                        logger.error("Supervisor process with PID %s not found!", supervisor_pid)
                    except Exception as sig_err:
                        logger.error("Failed to send SIGHUP signal: %s", sig_err, exc_info=True)
                    # === /SIGHUP ===
                    report_data["description"] = f"Patch successfully applied to {target_file}. {apply_msg}. Restart triggered."
                    report_data["tests_status"] = "passed"
                    report_data["deployment_ready"] = True
                    report_data["smoke_test_result"] = runtime_smoke_msg
                else:
                    final_status_for_orchestrator = "failed"
                    report_data["description"] = f"Smoke tests passed, but FAILED to apply patch: {apply_msg}"
                    report_data["tests_status"] = "error"
                    report_data["deployment_ready"] = False
                    report_data["smoke_test_result"] = runtime_smoke_msg
            else:
                logger.info("Both smoke tests passed, but no target file specified. Returning code.")
                final_status_for_orchestrator = "passed"
                report_data.setdefault("description", "Code generated and passed both smoke tests. No file modification requested.")
                report_data["deployment_ready"] = True
                report_data.setdefault("tests_status", "passed")
                report_data["smoke_test_result"] = runtime_smoke_msg

        elif not generated_code:
            logger.warning("No code extracted from agent response.")
            report_data.setdefault("description", "No code extracted from LLM response.")
            final_status_for_orchestrator = "failed"
            report_data["deployment_ready"] = False
            report_data["smoke_test_result"] = "No code extracted"
            try:
                put_event(stage="deploy", event_type="post_deploy_failed", context={"reason": "no_code_extracted"})
            except Exception:
                pass
        else:
            fail_reason = runtime_smoke_msg if not runtime_smoke_ok else report_data.get("smoke_message", "Syntax check failed")
            logger.warning("Smoke test failed. Code not applied. Reason: %s", fail_reason)
            final_status_for_orchestrator = "failed"
            report_data.setdefault("description", f"Smoke test failed: {fail_reason}")
            report_data["deployment_ready"] = False
            report_data["smoke_test_result"] = fail_reason
            try:
                put_event(stage="deploy", event_type="post_deploy_failed", context={"reason": fail_reason})
            except Exception:
                pass

        # Единая точка возврата + [IDEMP] запись результата
        result = {
            "status": final_status_for_orchestrator,
            "analysis": analysis_text_for_debug or (analysis_result if isinstance(analysis_result, str) else json.dumps(analysis_result, ensure_ascii=False)),
            "is_complete": (final_status_for_orchestrator == "passed") and bool(report_data.get("deployment_ready", False)),
            "generated_code": generated_code,
            "report": report_data,
        }
        await _try_update_idemp(
            idempotency_key,
            "applied" if result["status"] == "passed" and result["report"].get("deployment_ready") else "failed",
            result,
        )
        return result

    except Exception as e:
        logger.exception("Critical error during agent analysis: %s", e)
        error_report = {
            "deployment_ready": False,
            "description": f"Internal error in analyze_task: {type(e).__name__}: {str(e)}",
            "tests_status": "error",
            "smoke_test_result": f"Internal Error: {type(e).__name__}",
        }
        try:
            put_event(stage="deploy", event_type="incident", context={"severity": "error", "message": str(e)})
        except Exception:
            pass
        result = {
            "status": "error",
            "analysis": f"=== Analysis Report ===\n```json\n{json.dumps(error_report, ensure_ascii=False, indent=2)}\n```",
            "is_complete": False,
            "error": str(e),
            "generated_code": "",
            "report": error_report,
        }
        # [IDEMP] фиксируем аварийный результат
        await _try_update_idemp((task_data or {}).get("idempotency_key"), "failed", result)
        return result

# =============================================================================
# Service endpoints
# =============================================================================
@app.get("/")
async def root():
    return {"message": "Engineer B API is running", "version": "4.0", "status": "operational",
            "endpoints": {"health": "/system/health", "ready": "/ready", "memory": "/agent/memory", "analyze": "/agent/analyze (POST)"}}

@app.get("/system/health")
async def health_check():
    return {"status": "ok", "uptime": str(datetime.now() - app.state.start_time), "llm_router_active": llm_router is not None}

@app.get("/ready")
async def ready():
    if app.state.ready and agent is not None:
        return {"status": "ok"}
    raise HTTPException(status_code=503, detail="Agent not ready")

@app.get("/agent/memory")
async def get_agent_memory():
    if agent and hasattr(agent, "get_memory"):
        return agent.get_memory()
    raise HTTPException(status_code=503, detail="Agent is not initialized")

# === AutoDev startup marker (safe to keep) ===
try:
    from fastapi import FastAPI as _FastAPI
    _app_obj = globals().get("app", None)
    if isinstance(_app_obj, _FastAPI):
        @_app_obj.on_event("startup")
        async def _autodev_start_marker():
            import logging as _logging
            _logging.getLogger("uvicorn.error").info("EngineerB START [MARK:ENGB-BOOT-1337]")
except Exception:
    pass
# === /marker ===

# === ENGINEER_B_MARKER ===
try:
    import logging as _lg
    _lg.getLogger("uvicorn.error").info("EngineerB app loaded [MARK:ENGB-BOOT-1337]")
except Exception:
    pass
# === /ENGINEER_B_MARKER ===
print("EngineerB app loaded [MARK:ENGB-BOOT-PRINT]")




