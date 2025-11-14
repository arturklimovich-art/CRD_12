# -*- coding: utf-8 -*-
"""
PatchApplier - обёртка для интеграции PatchManager с существующим кодом
Версия: 1.1 (Fixed approve_token format)
Дата: 2025-11-11
"""

import os
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

PATCH_MANAGER_ENABLED = True

try:
    from patch_manager import PatchManager
except Exception as e:
    logger.warning(f"PatchManager not available: {e}")
    PATCH_MANAGER_ENABLED = False


def apply_code_via_patch_manager(
    target_file: str, 
    generated_code: str, 
    task_id: Optional[str] = None,
    author: str = "engineer_b_agent"
) -> Tuple[bool, str, str]:
    """
    Применяет код через PatchManager + main.py API
    
    Args:
        target_file: Путь к целевому файлу
        generated_code: Сгенерированный код
        task_id: ID задачи
        author: Автор патча
        
    Returns:
        (success, message, patch_id)
    """
    if not PATCH_MANAGER_ENABLED:
        return False, "PatchManager not available", ""
    
    try:
        # 1. Создание патча
        DB_DSN = os.getenv("DATABASE_URL", "postgres://crd_user:crd12@crd12_pgvector:5432/crd12")
        pm = PatchManager(db_dsn=DB_DSN)
        
        patch_id, approve_token = pm.create_patch_from_generated_code(
            target_file=target_file,
            generated_code=generated_code,
            task_id=task_id or "unknown_task",
            author=author
        )
        
        logger.info(f"✅ Patch created: {patch_id}")
        
        # 2. Применение через API (ИСПРАВЛЕНО: approve_token как строка в body)
        import requests
        
        response = requests.post(
            f"http://localhost:8000/api/patches/{patch_id}/apply",
            data=approve_token,  # ИСПРАВЛЕНО: передаём строку напрямую, не JSON
            headers={"Content-Type": "text/plain"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Patch applied successfully: {result}")
            return True, f"Patch {patch_id} applied successfully", patch_id
        else:
            logger.error(f"❌ Patch application failed: {response.status_code} - {response.text}")
            return False, f"Patch application failed: {response.text}", patch_id
    
    except Exception as e:
        logger.error(f"❌ apply_code_via_patch_manager failed: {e}")
        return False, str(e), ""


def apply_code_with_fallback(
    target_file: str,
    generated_code: str,
    task_id: Optional[str] = None,
    fallback_function = None
) -> Tuple[bool, str, str]:
    """
    Пытается применить через PatchManager, при неудаче - через fallback
    
    Returns:
        (success, message, backup_or_patch_id)
    """
    # Попытка через PatchManager
    if PATCH_MANAGER_ENABLED:
        success, msg, patch_id = apply_code_via_patch_manager(
            target_file, generated_code, task_id
        )
        
        if success:
            return True, msg, patch_id
        
        logger.warning(f"PatchManager failed: {msg}, trying fallback")
    
    # Fallback к старому методу
    if fallback_function:
        try:
            applied_ok, apply_msg, backup_path = fallback_function(target_file, generated_code)
            return applied_ok, apply_msg, backup_path
        except Exception as e:
            return False, f"Fallback failed: {e}", ""
    
    return False, "No fallback function provided", ""
