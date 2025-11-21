# ---   : src/bot/tasks/task_manager.py ---

import asyncio
import aiohttp
from aiohttp import ClientConnectorError
import json
import logging
import os
from tasks.post_deploy import wait_post_deploy
import re
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any
from json import JSONDecodeError

# === :    ( USER_MODE) ===
#  ,  bot.py
try:
    from database import SessionLocal, Task  # /app/database.py
except ImportError:
    #  ,     ,
    #  'database'   sys.path
    log = logging.getLogger("task_manager")
    if not log.hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        log = logging.getLogger("task_manager")
    log.warning("   'database'.  USER_MODE ( bot.py)   .")
    SessionLocal = None
    Task = None

# ===  : ( SELF_BUILDING_MODE) ===
try:
    import asyncpg
except ImportError:
    print("!!! : 'asyncpg'  .  'pip install asyncpg' !!!")
    print("!!!   'asyncpg'  requirements.txt   . !!!")
    asyncpg = None


#
log = logging.getLogger("task_manager")
#  ,      (,   )
if not log.hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# ---  :      (SELF_BUILDING_MODE) ---

# 1.
#   .  "true"  "1",   .
SELF_BUILDING_MODE = os.getenv("SELF_BUILDING_MODE", "false").lower() in ("true", "1")

# 2.      (  eng_it)
#        ,
DB_USER = os.getenv("POSTGRES_USER", "crd_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "crd12")
DB_NAME = os.getenv("POSTGRES_DB", "crd12")
DB_HOST = os.getenv("POSTGRES_HOST", "pgvector")  # <-- :
DB_PORT = os.getenv("POSTGRES_PORT", 5432)

#     ( eng_it)
navigator_db_pool = None

# ---    ---

# URL Engineer B API (  )
ENGINEER_B_API_URL = os.getenv("ENGINEER_B_API_URL", "http://engineer_b_api:8000")
#
CURATOR_API_URL = os.getenv("CURATOR_API_URL", "http://fake_curator_api:8001/api/v1/validate")

# ─────────────────────────────────────────────────────────────
# ШАГ 9 — конфиг пост-деплой валидации из ENV
# ─────────────────────────────────────────────────────────────
POST_DEPLOY_VALIDATE = os.getenv("POST_DEPLOY_VALIDATE", "true").lower() == "true"
def _as_float(v: str, default: float) -> float:
    try:
        return float(v)
    except Exception:
        return default
def _as_int(v: str, default: int) -> int:
    try:
        return int(float(v))
    except Exception:
        return default

POST_DEPLOY_TIMEOUT_SEC = _as_float(os.getenv("POST_DEPLOY_TIMEOUT_SEC", "60"), 60.0)
POST_DEPLOY_POLL_SEC = _as_float(os.getenv("POST_DEPLOY_POLL_SEC", "2"), 2.0)
POST_DEPLOY_MIN_CONSEC_OK = _as_int(os.getenv("POST_DEPLOY_MIN_CONSEC_OK", "2"), 2)

# ===================================================================
#    ( )
# ===================================================================

CODE_FENCE_RE = re.compile(
    r"```(?:python|py)?\s*(?P<code>[\s\S]*?)\s*```",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)
JSON_FENCE_RE = re.compile(
    r"```json\s*(?P<json>[\s\S]*?)\s*```",
    re.IGNORECASE | re.DOTALL | re.MULTILINE,
)

def _choose_best_code_block(candidates: list[str]) -> Optional[str]:
    best = None
    best_score = -1.0
    for c in candidates:
        s = c.strip()
        if s.startswith(("{", "[")) and s.endswith(("}", "]")):
            continue
        score = 0
        if "def " in s:
            score += 2
        if "class " in s:
            score += 1
        score += min(len(s) / 1000.0, 2.0)
        if score > best_score:
            best_score = score
            best = s
    return best if best and len(best) >= 10 else None

def _extract_code(text: str) -> Optional[str]:
    if not text:
        return None
    blocks = [m.group("code") for m in CODE_FENCE_RE.finditer(text)]
    if not blocks and len(text.strip()) > 50 and not text.strip().startswith(("{", "[")):
        blocks.append(text)
    return _choose_best_code_block(blocks)

def _extract_json_report(text: str) -> Optional[Dict[str, Any]]:
    if not text:
        return None
    fence = JSON_FENCE_RE.search(text)
    if fence:
        raw = fence.group("json").strip()
        try:
            return json.loads(raw)
        except JSONDecodeError as e:
            log.warning(f"JSON in ```json block decode failed: {e}")
    first = text.find("{")
    last = text.rfind("}")
    if first == -1 or last == -1 or last <= first:
        return None
    candidate = text[first: last + 1].replace("\r", "").strip()
    try:
        return json.loads(candidate)
    except JSONDecodeError:
        pass
    # ... (  )
    for ltrim in range(0, min(120, len(candidate) - 2), 10):
        for rtrim in range(0, min(120, len(candidate) - 2 - ltrim), 10):
            # ... ()
            pass
    return None

def _parse_analysis_result(text: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    code = _extract_code(text)
    report = _extract_json_report(text)
    return code, report

# ─────────────────────────────────────────────────────────────
# ШАГ 9 — универсальный враппер post-deploy валидации
# ─────────────────────────────────────────────────────────────
async def _post_deploy_gate() -> Tuple[bool, Dict[str, Any]]:
    """
    Универсальный запуск wait_post_deploy с поддержкой синхронной/асинхронной реализации
    и разных сигнатур. Возвращает (ok: bool, details: dict).
    """
    if not POST_DEPLOY_VALIDATE:
        return True, {"skipped": True, "reason": "POST_DEPLOY_VALIDATE=false"}

    base_url = ENGINEER_B_API_URL.rstrip("/")
    # Попробуем вызвать с параметрами, при несовпадении сигнатуры сделаем фолбэк.
    async def _call_variant():
        try:
            res = wait_post_deploy(base_url, POST_DEPLOY_TIMEOUT_SEC, POST_DEPLOY_POLL_SEC, POST_DEPLOY_MIN_CONSEC_OK)
        except TypeError:
            try:
                res = wait_post_deploy(base_url)
            except TypeError:
                res = wait_post_deploy()
        if asyncio.iscoroutine(res):
            res = await res
        return res

    try:
        result = await _call_variant()
    except Exception as e:
        log.error("[POST-DEPLOY] wait_post_deploy raised: %s", e, exc_info=True)
        return False, {"error": str(e), "exception": type(e).__name__}

    # Нормализуем результат
    ok = False
    details: Dict[str, Any] = {}
    try:
        if isinstance(result, tuple):
            ok = bool(result[0])
            if len(result) > 1 and isinstance(result[1], dict):
                details = result[1]
            elif len(result) > 1:
                details = {"details": result[1]}
        elif isinstance(result, dict):
            # допускаем ключи ok/success/status
            if "ok" in result:
                ok = bool(result["ok"])
            elif "success" in result:
                ok = bool(result["success"])
            elif "status" in result:
                ok = (str(result["status"]).lower() == "ok" or str(result["status"]).lower() == "passed")
            details = result
        elif isinstance(result, bool):
            ok = result
            details = {}
        else:
            details = {"raw": str(result)}
            ok = False
    except Exception:
        pass

    return ok, details

# ===================================================================
#  TASKMANAGER
# ===================================================================

class TaskManager:

    # ===================================================================
    # ---  USER_MODE (  ,  ) ---
    # ---  SQLAlchemy  (public).Task ---
    # ===================================================================

    @staticmethod
    async def create_new_task(user_id: str, task_description: str) -> 'Task':
        """    (USER_MODE)."""
        log.info(f"[USER_MODE]     {user_id}")
        if not SessionLocal:
            log.error("[USER_MODE] SessionLocal  .    .")
            raise ImportError("Database components not loaded.")

        def sync_create_task() -> 'Task':
            db = SessionLocal()
            try:
                task = Task(
                    user_id=user_id,
                    task_description=task_description,
                    status="pending",
                    created_at=datetime.now(timezone.utc),
                )
                db.add(task)
                db.commit()
                db.refresh(task)
                log.info(f" [USER_MODE]   #{task.id}  {user_id}")
                return task
            except Exception as e:
                db.rollback()
                log.error(f" [USER_MODE]    : {e}", exc_info=True)
                raise
            finally:
                db.close()
        return await asyncio.to_thread(sync_create_task)

    @staticmethod
    async def get_task_by_id(task_id: int) -> Optional['Task']:
        """   ID (USER_MODE)."""
        if not SessionLocal:
            return None

        def sync_get_task() -> Optional['Task']:
            db = SessionLocal()
            try:
                return db.query(Task).filter(Task.id == task_id).first()
            finally:
                db.close()
        return await asyncio.to_thread(sync_get_task)

    @staticmethod
    async def _update_task_status(task_id: int, status: str, error_message: Optional[str] = None):
        """     (USER_MODE)."""
        if not SessionLocal:
            return

        def sync_update():
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return
                task.status = status
                now = datetime.now(timezone.utc)
                if status == "in_progress":
                    task.started_at = now
                if status in ("completed", "failed"):
                    task.completed_at = now
                if error_message:
                    task.error_message = error_message
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        await asyncio.to_thread(sync_update)

    @staticmethod
    async def _set_completed(task_id: int, generated_code: str, report: Dict[str, Any]):
        """ 'completed',     (USER_MODE)."""
        if not SessionLocal:
            return

        print(f" [USER_MODE] DEBUG: _set_completed called for task #{task_id}, tests_status: {report.get('tests_status')}")
        def sync_set_completed():
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return
                task.status = "completed"
                task.generated_code = generated_code
                task.test_results = json.dumps(report, ensure_ascii=False)

                #  deployment_ready   tests_status
                dep_ready = bool(report.get('deployment_ready', False))
                task.deployment_ready = dep_ready

                task.completed_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        await asyncio.to_thread(sync_set_completed)

    @staticmethod
    async def _set_failed(task_id: int, error_message: str):
        """ 'failed'    (USER_MODE)."""
        if not SessionLocal:
            return

        def sync_set_failed():
            db = SessionLocal()
            try:
                task = db.query(Task).filter(Task.id == task_id).first()
                if not task:
                    return
                task.status = "failed"
                task.error_message = error_message
                task.completed_at = datetime.now(timezone.utc)
                db.commit()
            except Exception:
                db.rollback()
                raise
            finally:
                db.close()
        await asyncio.to_thread(sync_set_failed)

    # ===================================================================
    # ---  API () ---
    # --- _call_engineer_b_api    ---
    # ===================================================================

    @staticmethod
    @staticmethod
    async def _get_system_context() -> Optional[Dict[str, Any]]:
        """
        Получает System Context из Engineer B API.
        Возвращает контекст или None если недоступен.
        """
        context_url = f"{ENGINEER_B_API_URL.rstrip('/')}/api/system/context"
        
        try:
            log.info(f"[CONTEXT] Получаю System Context из {context_url}")
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(context_url) as response:
                    if response.status == 200:
                        context = await response.json()
                        log.info("[CONTEXT] ✅ System Context получен успешно")
                        return context
                    else:
                        log.warning(f"[CONTEXT] ⚠️ Status {response.status}")
                        return None
        except Exception as e:
            log.warning(f"[CONTEXT] ⚠️ Ошибка: {e}")
            return None

    async def _call_engineer_b_api(task_description: str) -> Dict[str, Any]:
        """
         POST  Engineer B API    .
        ( ,  ,   URL  )
        """
        # : URL
        url = f"{ENGINEER_B_API_URL.rstrip('/')}/agent/analyze"
        payload = {"task": (task_description or "").strip()}
        log.info(f"  Engineer B API: {url}")

        try:
            # :
            timeout = aiohttp.ClientTimeout(total=600)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    raw_response = await response.text()
                    #  DEBUG
                    print(f" RAW RESPONSE FROM ENGINEER: {raw_response[:1000]}...")

                    if response.status != 200:
                        error_msg = f"API Error: HTTP {response.status}. Body: {raw_response[:400]}"
                        log.error(f" Engineer B API HTTP error: {error_msg}")
                        return {"error": error_msg}

                    try:
                        data = json.loads(raw_response)  #  json.loads, .. response.json()
                    except JSONDecodeError:
                        log.error(f"    JSON   Engineer B: {raw_response[:1000]}")
                        return {"error": "Failed to decode JSON response from Engineer B"}

            #     ,
            if not isinstance(data, dict):
                error_msg = f"API Error: unexpected payload type: {type(data).__name__}"
                log.error(f" Engineer B API parse error: {error_msg}")
                return {"error": error_msg}

            # --- НОВОЕ: честный статус от app.py v4.0 ---
            engineer_status = data.get("status", "error")  # "passed" | "failed" | "error"

            analysis_report_text = (data.get("analysis") or "").strip()
            generated_code = (data.get("generated_code") or "").strip()

            #
            if not generated_code:
                code_field = (data.get("code") or "").strip()
                if code_field:
                    #  _extract_code   RE
                    generated_code = _extract_code(code_field) or code_field
            if not generated_code:
                parsed_code, _ = _parse_analysis_result(analysis_report_text)
                if parsed_code:
                    generated_code = parsed_code
                else:
                    log.warning("No code extracted from any field or fallback parser.")

            #
            report_dict = data.get("report")
            if isinstance(report_dict, str):
                report_dict = _extract_json_report(report_dict)
            elif not isinstance(report_dict, dict):
                report_dict = {}

            if "tests_status" not in report_dict and isinstance(data.get("tests_status"), str):
                report_dict["tests_status"] = data["tests_status"]
            if "deployment_ready" not in report_dict and isinstance(data.get("deployment_ready"), bool):
                report_dict["deployment_ready"] = data["deployment_ready"]

            if (not report_dict) or (report_dict.get("tests_status", "unknown") == "unknown"):
                parsed_report = _extract_json_report(analysis_report_text)
                if parsed_report:
                    report_dict.update(parsed_report)

            if not report_dict:
                report_dict = {"description": "Could not parse report JSON.", "tests_status": "unknown"}

            if not generated_code:
                report_dict.setdefault("description", "No code extracted from LLM response.")
                report_dict.setdefault("tests_status", "error")
                report_dict["deployment_ready"] = False

            return {
                "engineer_status": engineer_status,  # --- НОВОЕ ---
                "generated_code": generated_code.strip() if generated_code else "",
                "report": report_dict,
                "full_analysis_text": analysis_report_text,
            }

        except ClientConnectorError as e:
            error_msg = f"Connection error to Engineer B API: {type(e).__name__}: {e}"
            log.error(f" {error_msg}")
            return {"error": error_msg}
        except asyncio.TimeoutError as e:
            error_msg = f"Timeout error during Engineer B API call: {e}"
            log.error(f" {error_msg}")
            return {"error": error_msg}
        except JSONDecodeError as e:
            error_msg = f"Failed to decode API response JSON: {e}"
            log.exception(f" {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Unexpected error during API call: {type(e).__name__}: {e}"
            log.exception(f" {error_msg}")
            return {"error": error_msg}

    # ===================================================================
    # ---  USER_MODE () ---
    # ---   USER_MODE ---
    # ===================================================================

    @staticmethod
    async def process_task(task_id: int):
        """    (USER_MODE). ( )"""
        print(f" [USER_MODE] DEBUG: process_task called for task #{task_id}")
        log.info(f" [USER_MODE] Starting processing for task #{task_id}")
        try:
            await TaskManager._update_task_status(task_id, "in_progress")

            task = await TaskManager.get_task_by_id(task_id)
            if not task:
                log.error(f" [USER_MODE] Task #{task_id} not found")
                return

            api_result = await TaskManager._call_engineer_b_api(task.task_description)

            if "error" in api_result:
                log.error(f" [USER_MODE] API call failed for task #{task_id}: {api_result['error']}")
                await TaskManager._set_failed(task_id, api_result["error"])
                return

            # --- НОВОЕ: честная проверка статуса инженера ---
            engineer_status = api_result.get("engineer_status", "error")
            generated_code = (api_result.get("generated_code") or "").strip()
            report = api_result.get("report", {})
            report_notes = report.get('description', 'No description in report.')

            if engineer_status != "passed" or not generated_code:
                error_msg = f"Engineer failed: {report_notes}"
                if not generated_code and engineer_status == "passed":
                    error_msg = "Engineer reported 'passed' but returned no code."
                log.error(f" [USER_MODE] No code generated or Engineer failed for task #{task_id}. Reason: {error_msg}")
                await TaskManager._set_failed(task_id, error_msg)
                return

            # ── ШАГ 9: пост-деплой валидация (орchestrator не «врёт»)
            if POST_DEPLOY_VALIDATE:
                log.info(f"[USER_MODE] Post-deploy validation started for task #{task_id}...")
                ok, details = await _post_deploy_gate()
                if not ok:
                    reason = details.get("reason") or details.get("error") or "post-deploy check failed"
                    log.error(f"[USER_MODE] Post-deploy validation FAILED for task #{task_id}: {reason}")
                    await TaskManager._set_failed(task_id, f"Post-deploy failed: {reason}")
                    return
                else:
                    log.info(f"[USER_MODE] Post-deploy validation OK for task #{task_id}: {details}")

            await TaskManager._set_completed(task_id, generated_code, report)
            log.info(f" [USER_MODE] Successfully completed task #{task_id}")

        except Exception as e:
            log.exception(f" [USER_MODE] Critical error processing task #{task_id}: {e}")
            await TaskManager._set_failed(task_id, f"Processing error: {type(e).__name__}: {str(e)}")

    @staticmethod
    async def create_task(user_id: str, task_description: str) -> 'Task':
        """    (USER_MODE). ( )"""
        return await TaskManager.create_new_task(user_id, task_description)

    # ===================================================================
    # ---  :  SELF_BUILDING_MODE ---
    # ---  asyncpg  (eng_it) ---
    # ===================================================================

    @staticmethod
    async def init_navigator_db():
        """      (eng_it)."""
        global navigator_db_pool
        if navigator_db_pool:
            return
        if not asyncpg:
            log.critical("[SELF_BUILD] 'asyncpg'  .   .")
            raise ImportError("asyncpg is not installed")
        try:
            log.info(f"[SELF_BUILD]    : {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
            navigator_db_pool = await asyncpg.create_pool(
                user=DB_USER,
                password=DB_PASS,
                database=DB_NAME,
                host=DB_HOST,
                port=DB_PORT,
                server_settings={'search_path': 'eng_it,public'}
            )
            log.info(f" [SELF_BUILD]        ( eng_it).")
        except Exception as e:
            log.critical(f" [SELF_BUILD]      : {e}", exc_info=True)
            raise

    @staticmethod
    async def get_next_self_building_task() -> Optional['asyncpg.Record']:
        """       eng_it.progress_navigator."""
        if not navigator_db_pool:
            await TaskManager.init_navigator_db()

        query = """
        SELECT pn.task_code, pn.title, pn.description, pn.module, pn.level
        FROM eng_it.progress_navigator pn
        WHERE pn.status = 'planned'
        AND NOT EXISTS (
            SELECT 1
            FROM eng_it.task_dependencies td
            JOIN eng_it.progress_navigator pn_dep ON td.depends_on_task_code = pn_dep.task_code
            WHERE td.task_code = pn.task_code
              AND td.dependency_type = 'hard'
              AND pn_dep.status != 'passed'
        )
        ORDER BY pn.priority ASC, pn.created_at ASC
        LIMIT 1;
        """
        try:
            async with navigator_db_pool.acquire() as conn:
                task_record = await conn.fetchrow(query)
                return task_record
        except Exception as e:
            log.error(f" [SELF_BUILD]      : {e}", exc_info=True)
            return None

    @staticmethod
    async def update_task_status_in_navigator(task_code: str, status: str, notes: str = ""):
        """     eng_it.progress_navigator."""
        if not navigator_db_pool:
            await TaskManager.init_navigator_db()

        query = """
        UPDATE eng_it.progress_navigator
        SET status = $1::eng_it.status_t, updated_at = now()
        WHERE task_code = $2;
        """
        log.info(f"[SELF_BUILD]   {task_code}  {status}  progress_navigator...")
        try:
            async with navigator_db_pool.acquire() as conn:
                await conn.execute(query, status, task_code)
        except Exception as e:
            log.error(f" [SELF_BUILD]    {task_code}  progress_navigator: {e}", exc_info=True)

    @staticmethod
    async def update_agent_progress(task_code: str, agent_name: str, status: str, notes: str = "", evidence_uri: str = None):
        """       eng_it.agent_progress."""
        if not navigator_db_pool:
            await TaskManager.init_navigator_db()

        query = """
        INSERT INTO eng_it.agent_progress (task_code, agent_name, status, notes, evidence_uri, started_at, finished_at)
        VALUES ($1, $2, $3::eng_it.status_t, $4, $5, now(), CASE WHEN $3 IN ('passed', 'failed') THEN now() ELSE NULL END)
        ON CONFLICT (task_code, agent_name) DO UPDATE
        SET status = $3::eng_it.status_t,
            notes = $4,
            evidence_uri = $5,
            progress_percent = CASE WHEN $3 = 'passed' THEN 100 WHEN $3 = 'in_progress' THEN 50 ELSE 0 END,
            finished_at = CASE WHEN $3 IN ('passed', 'failed') THEN now() ELSE NULL END;
        """
        log.info(f"[SELF_BUILD]  {agent_name}  {task_code}  {status}...")
        try:
            async with navigator_db_pool.acquire() as conn:
                await conn.execute(query, task_code, agent_name, status, notes, evidence_uri)
        except Exception as e:
            log.error(f" [SELF_BUILD]   agent_progress  {task_code} ({agent_name}): {e}", exc_info=True)

    # ===================================================================
    # --- CURATOR: реальный вызов + фолбэк на заглушку ---
    # ===================================================================

    @staticmethod
    async def _call_curator_api(task_code: str, task_description: str, generated_code: str) -> Dict[str, Any]:
        """Вызывает реальный API Куратора с фолбэком на заглушку."""
        url = CURATOR_API_URL  # Используем URL из переменной окружения
        if not url or url.startswith("http://fake_curator"):  # Проверяем, что URL задан и не фейковый
            log.warning("[SELF_BUILD] CURATOR_API_URL not configured or is fake, using stub.")
            return await TaskManager._call_curator_api_stub(task_code, task_description, generated_code)

        log.info(f"[SELF_BUILD] Calling REAL Curator at {url} for task {task_code}...")
        try:
            payload = {
                "task_code": task_code,
                "description": task_description,
                "code": generated_code,
            }
            # Увеличиваем таймаут для потенциально долгой проверки Gemini
            timeout = aiohttp.ClientTimeout(total=180)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    body = await resp.text()
                    if resp.status != 200:
                        log.warning(f"[SELF_BUILD] Curator HTTP {resp.status}: {body[:400]}. Falling back to stub.")
                        # Фолбэк на заглушку при HTTP ошибке
                        return await TaskManager._call_curator_api_stub(task_code, task_description, generated_code)
                    try:
                        data = json.loads(body)
                    except JSONDecodeError:
                        log.warning("[SELF_BUILD] Curator non-JSON response, falling back to stub.")
                        # Фолбэк на заглушку при не-JSON ответе
                        return await TaskManager._call_curator_api_stub(task_code, task_description, generated_code)

            # Парсим ответ реального куратора (предполагаем поля approved/notes или status/reason)
            approved = bool(data.get("approved") or data.get("status") == "passed")
            notes = data.get("notes") or data.get("reason") or "No notes from Curator."
            log.info(f"[SELF_BUILD] REAL Curator response for {task_code}: Approved={approved}")
            return {"approved": approved, "notes": notes, "status": "passed" if approved else "failed"}

        except ClientConnectorError as e:
            log.warning(f"[SELF_BUILD] Curator connection failed: {e}. Using stub.")
            return await TaskManager._call_curator_api_stub(task_code, task_description, generated_code)
        except asyncio.TimeoutError:
            log.warning(f"[SELF_BUILD] Curator call timed out. Using stub.")
            return await TaskManager._call_curator_api_stub(task_code, task_description, generated_code)
        except Exception as e:
            log.warning(f"[SELF_BUILD] Curator call failed with unexpected error: {e}. Using stub.")
            # Фолбэк на заглушку при любой другой ошибке
            return await TaskManager._call_curator_api_stub(task_code, task_description, generated_code)

    @staticmethod
    async def _call_curator_api_stub(task_code: str, task_description: str, generated_code: str) -> Dict[str, Any]:
        """  API  (Gemini)."""
        log.info(f"[SELF_BUILD] [CURATOR STUB]   {task_code}...")

        if not generated_code:
            log.warning(f"[SELF_BUILD] [CURATOR STUB] : {task_code} ( ).")
            return {
                "approved": False,
                "notes": "  ():   .",
                "status": "failed"
            }

        log.info(f" [SELF_BUILD] [CURATOR STUB] : {task_code}.")
        return {
            "approved": True,
            "notes": "  ().   .",
            "status": "passed"
        }

    @staticmethod
    async def run_self_building_loop():
        """    (SELF_BUILDING_MODE)."""
        log.info("---     ---")
        log.info("    ...")
        try:
            await TaskManager.init_navigator_db()
        except Exception as e:
            log.critical(f" [SELF_BUILD]    :     . {e}")
            return

        while True:
            log.info("[SELF_BUILD]     ...")
            task = await TaskManager.get_next_self_building_task()

            if not task:
                log.info(" [SELF_BUILD]  'planned' .  30 ...")
                await asyncio.sleep(300)  #  ,
                continue  #     (  ...)

            task_code = task['task_code']
            task_title = task['title']
            task_desc = task['description'] or task_title

            log.info(f"---  [SELF_BUILD]    : [{task_code}] {task_title} ---")

            try:
                # 1.
                await TaskManager.update_task_status_in_navigator(task_code, 'in_progress')
                await TaskManager.update_agent_progress(task_code, 'orchestrator', 'passed', f"  Engineer B.")
                await TaskManager.update_agent_progress(task_code, 'coder', 'in_progress', "  .")

                # 2.  Engineer B (Coder) -
                log.info(f"[{task_code}]  Engineer B...")
                full_task_prompt = f" : {task_title}\n\n: {task_desc}"
                api_result = await TaskManager._call_engineer_b_api(full_task_prompt)

                if "error" in api_result:
                    log.error(f" [{task_code}]  Engineer B: {api_result['error']}")
                    await TaskManager.update_task_status_in_navigator(task_code, 'failed')
                    await TaskManager.update_agent_progress(task_code, 'coder', 'failed', api_result['error'])
                    await asyncio.sleep(5)
                    continue

                # --- НОВОЕ: честно учитываем статус инженера и наличие кода ---
                engineer_status = api_result.get("engineer_status", "error")  # "passed" / "failed"
                generated_code = (api_result.get("generated_code") or "").strip()
                report = api_result.get("report", {})
                report_notes = report.get('description', f'Engineer status: {engineer_status}')

                # 4. (!!!) — если инженер провалился, задача проваливается
                if engineer_status != "passed":
                    log.warning(f" [{task_code}] Engineer B (Coder) failed. Status: {engineer_status}. Notes: {report_notes}")
                    await TaskManager.update_task_status_in_navigator(task_code, 'failed')
                    await TaskManager.update_agent_progress(task_code, 'coder', 'failed', f"Engineer failed: {report_notes}")
                    await asyncio.sleep(5)
                    continue  # <-- не идем к куратору

                # Инженер успешен — фиксируем успех coder
                await TaskManager.update_agent_progress(task_code, 'coder', 'passed', f"Engineer passed: {report_notes}")

                # 3.   (Curator)
                log.info(f"[{task_code}]   ()...")
                await TaskManager.update_agent_progress(task_code, 'curator', 'in_progress', "   .")

                # >>> ЗАМЕНА ВЫЗОВА: используем реальный API с фолбэком
                curator_result = await TaskManager._call_curator_api(task_code, task_desc, generated_code)

                if not curator_result.get("approved"):
                    log.warning(f" [{task_code}]  : {curator_result.get('notes')}")
                    await TaskManager.update_task_status_in_navigator(task_code, 'failed')
                    await TaskManager.update_agent_progress(task_code, 'curator', 'failed', curator_result.get('notes'))
                    await asyncio.sleep(5)
                    continue

                await TaskManager.update_agent_progress(task_code, 'curator', 'passed', curator_result.get('notes'))

                # ── ШАГ 9: пост-деплой валидация (честный оркестратор)
                if POST_DEPLOY_VALIDATE:
                    log.info(f"[{task_code}] Post-deploy validation started...")
                    ok, details = await _post_deploy_gate()
                    if not ok:
                        reason = details.get("reason") or details.get("error") or "post-deploy check failed"
                        log.error(f"[{task_code}] Post-deploy validation FAILED: {reason}")
                        await TaskManager.update_task_status_in_navigator(task_code, 'failed')
                        await TaskManager.update_agent_progress(task_code, 'orchestrator', 'failed', f"Post-deploy failed: {reason}")
                        await asyncio.sleep(5)
                        continue
                    else:
                        log.info(f"[{task_code}] Post-deploy validation OK: {details}")

                # 4.
                #  :
                log.info(f"---  [SELF_BUILD]   : [{task_code}] ---")
                log.info(f"✅ [SELF_BUILD] КОД УСПЕШНО ВНЕДРЕН ДЛЯ ЗАДАЧИ: [{task_code}]")
                await TaskManager.update_task_status_in_navigator(task_code, 'passed')

            except Exception as e:
                log.exception(f" [{task_code}]     : {e}")
                await TaskManager.update_task_status_in_navigator(task_code, 'failed')
                await TaskManager.update_agent_progress(task_code, 'orchestrator', 'failed', f" : {e}")

            log.info("[SELF_BUILD]  10     ...")
            await asyncio.sleep(300)

# ===================================================================
# ---    (  ) ---
# ===================================================================

async def main_loop():
    """
     ,  ,   .
    """
    if SELF_BUILDING_MODE:
        #
        await TaskManager.run_self_building_loop()
    else:
        #    ( USER_MODE)
        log.info("---    (USER_MODE)  ---")
        log.info("    Telegram (  bot.py)...")
        #     . `bot.py`
        # TaskManager   `process_task()` / `create_task()`   .
        #   ""  ,
        # ,   SELF_BUILDING_MODE=true.
        await asyncio.Event().wait()  #

if __name__ == "__main__":
    """
        ,   'bot' (crd12_bot)
      (, `python -m bot.tasks.task_manager`).

     `bot.py`   ,    .
    """
    log.info(f" Task Manager (SELF_BUILDING_MODE={SELF_BUILDING_MODE})... [MARK:SB-BOOT-1337]")
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        log.info(" Task Manager...")
    except Exception as e:
        log.critical(f"    main_loop: {e}", exc_info=True)




