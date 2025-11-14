# -*- coding: utf-8 -*-
"""
PatchManager - управление патчами с версионированием и интеграцией
Версия: 1.2 (Fixed event logging with patch_id)
Дата: 2025-11-11
"""

from pathlib import Path
import hashlib
import uuid
import os
from datetime import datetime
from typing import Optional, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
import json

logger = logging.getLogger(__name__)


class PatchManager:
    """Управление патчами с интеграцией в существующую систему"""
    
    def __init__(self, db_dsn: str, base_path: str = "/app", patches_dir: str = "/app/workspace/patches_applied"):
        self.db_dsn = db_dsn
        self.base_path = Path(base_path)
        self.patches_dir = Path(patches_dir)
        self.patches_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"PatchManager initialized: base={base_path}, patches={patches_dir}")
    
    def create_patch_from_generated_code(
        self, 
        target_file: str, 
        generated_code: str, 
        task_id: str,
        author: str = "engineer_b_auto"
    ) -> Tuple[str, str]:
        """
        Создаёт патч из generated_code и регистрирует в БД
        
        Args:
            target_file: Путь к целевому файлу (относительно /app)
            generated_code: Сгенерированный код
            task_id: ID задачи из eng_it.tasks (TEXT)
            author: Автор патча
            
        Returns:
            (patch_id, approve_token): UUID патча и токен для применения
        """
        conn = psycopg2.connect(self.db_dsn, cursor_factory=RealDictCursor)
        
        try:
            patch_id = str(uuid.uuid4())
            
            # 1. Сохраняем текущую версию (если файл существует)
            full_path = self.base_path / target_file
            previous_version_id = None
            
            if full_path.exists():
                logger.info(f"File {target_file} exists, saving current version")
                with open(full_path, 'r', encoding='utf-8') as f:
                    old_content = f.read()
                
                previous_version_id = self._save_version(
                    conn=conn,
                    file_path=str(full_path),
                    content=old_content,
                    task_id=task_id,
                    is_stable=True
                )
                logger.info(f"Previous version saved: {previous_version_id}")
            else:
                logger.info(f"File {target_file} does not exist (new file)")
            
            # 2. Создаём файл патча
            patch_filename = f"{patch_id}.patch"
            patch_file_path = self.patches_dir / patch_filename
            
            with open(patch_file_path, 'w', encoding='utf-8') as f:
                f.write(generated_code)
            
            logger.info(f"Patch file created: {patch_file_path}")
            
            # 3. Вычисляем SHA256
            sha256_hash = hashlib.sha256(generated_code.encode()).hexdigest()
            
            # 4. Подготовка content (bytea)
            content_bytes = generated_code.encode('utf-8')
            
            # 5. Генерация токена
            approve_token = f"auto-{task_id[:8] if len(task_id) > 8 else task_id}-{int(datetime.utcnow().timestamp())}"
            
            # 6. Регистрируем в eng_it.patches
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO eng_it.patches 
                    (id, author, filename, content, sha256, status, approve_token, 
                     task_id, generated_by, previous_version_id, target_file)
                    VALUES (%s, %s, %s, %s, %s, 'validated', %s, %s, 'llm_auto', %s, %s)
                    RETURNING id
                """, (
                    patch_id, 
                    author, 
                    patch_filename,
                    psycopg2.Binary(content_bytes),
                    sha256_hash,
                    approve_token,
                    task_id,
                    previous_version_id,
                    target_file
                ))
                conn.commit()
            
            logger.info(f"Patch registered in DB: {patch_id}")
            
            # 7. Логируем событие создания (ИСПРАВЛЕНО: добавлен patch_id)
            self._log_event(conn, patch_id, "eng.patch.created", {
                "patch_id": patch_id,
                "task_id": task_id,
                "target_file": target_file,
                "by": "patch_manager",
                "previous_version_id": previous_version_id
            })
            
            return patch_id, approve_token
            
        except Exception as e:
            logger.error(f"Failed to create patch: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def _save_version(
        self, 
        conn, 
        file_path: str, 
        content: str, 
        task_id: str, 
        is_stable: bool = False
    ) -> str:
        """Сохраняет версию файла в eng_it.code_versions"""
        version_id = f"{task_id}_{int(datetime.utcnow().timestamp())}"
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO eng_it.code_versions
                (version_id, file_path, content, content_hash, task_id, is_stable, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, 'patch_manager')
            """, (version_id, file_path, content, content_hash, task_id, is_stable))
            conn.commit()
        
        return version_id
    
    def _log_event(self, conn, patch_id: str, event_type: str, payload: dict):
        """Логирует событие в eng_it.patch_events (ИСПРАВЛЕНО: добавлен patch_id)"""
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
                    VALUES (%s, %s, %s::jsonb)
                """, (patch_id, event_type, json.dumps(payload)))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log event {event_type}: {e}")


def get_patch_manager(db_dsn: str) -> PatchManager:
    """Factory function для создания PatchManager"""
    return PatchManager(db_dsn=db_dsn)
