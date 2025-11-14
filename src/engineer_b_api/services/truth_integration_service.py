# -*- coding: utf-8 -*-
"""
Truth Integration Service
Version: 1.0
Date: 2025-11-12

Автоматическая интеграция Roadmap ↔ Truth System:
- Создание вердиктов при изменении статуса задачи
- Связывание артефактов с вердиктами
- Проверка расхождений между Navigator и Truth
"""

import asyncpg
import os
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from models.truth import (
    VerdictStatus,
    TaskVerdictCreate,
    TaskVerdict,
)
from models.roadmap import TaskStatus

logger = logging.getLogger(__name__)


class TruthIntegrationService:
    """Сервис интеграции Truth System с Roadmap"""
    
    def __init__(self):
        self.database_url = os.getenv(
            "DATABASE_URL", 
            "postgres://crd_user:crd12@crd12_pgvector:5432/crd12"
        )
    
    async def get_db_connection(self):
        """Получить подключение к БД"""
        return await asyncpg.connect(self.database_url)
    
    async def get_active_revision_id(self) -> Optional[uuid.UUID]:
        """
        Получить ID активной ревизии истины
        
        Returns:
            UUID активной ревизии или None если нет активной
        """
        conn = await self.get_db_connection()
        try:
            query = "SELECT rev_id FROM eng_it.truth_revisions WHERE is_active = true LIMIT 1"
            row = await conn.fetchrow(query)
            return row['rev_id'] if row else None
        finally:
            await conn.close()
    
    async def create_verdict_for_task(
        self,
        task_id: int,
        task_title: str,
        new_status: TaskStatus,
        evidence_id: Optional[int] = None
    ) -> Optional[TaskVerdict]:
        """
        Создать вердикт для задачи при изменении статуса
        
        Args:
            task_id: ID задачи
            task_title: Название задачи
            new_status: Новый статус задачи
            evidence_id: ID артефакта-доказательства (опционально)
        
        Returns:
            TaskVerdict если создан, None если ошибка
        """
        try:
            # Получить активную ревизию
            rev_id = await self.get_active_revision_id()
            if not rev_id:
                logger.warning("No active truth revision found, skipping verdict creation")
                return None
            
            # Маппинг статусов Roadmap → Truth
            status_mapping = {
                TaskStatus.planned: VerdictStatus.planned,
                TaskStatus.in_progress: VerdictStatus.in_progress,
                TaskStatus.done: VerdictStatus.done,
                TaskStatus.failed: VerdictStatus.done,  # Failed тоже считается завершенным
                TaskStatus.blocked: VerdictStatus.in_progress,
                TaskStatus.removed: VerdictStatus.planned,  # Removed возвращается в planned
            }
            
            verdict_status = status_mapping.get(new_status, VerdictStatus.planned)
            
            # Проверить существует ли уже вердикт для этой задачи
            conn = await self.get_db_connection()
            try:
                existing_query = """
                    SELECT id FROM eng_it.task_verdicts 
                    WHERE task_title = $1 
                    ORDER BY verdict_ts DESC 
                    LIMIT 1
                """
                existing = await conn.fetchrow(existing_query, task_title)
                
                if existing:
                    # Обновить существующий вердикт
                    update_query = """
                        UPDATE eng_it.task_verdicts
                        SET status = $1, evidence_id = $2, verdict_ts = NOW()
                        WHERE id = $3
                        RETURNING id, task_title, rev_id, status, evidence_id, verdict_ts
                    """
                    row = await conn.fetchrow(
                        update_query,
                        verdict_status.value,
                        evidence_id,
                        existing['id']
                    )
                    logger.info(f"Updated verdict #{existing['id']} for task '{task_title}' to status '{verdict_status}'")
                else:
                    # Создать новый вердикт
                    insert_query = """
                        INSERT INTO eng_it.task_verdicts 
                        (task_title, rev_id, status, evidence_id)
                        VALUES ($1, $2, $3, $4)
                        RETURNING id, task_title, rev_id, status, evidence_id, verdict_ts
                    """
                    row = await conn.fetchrow(
                        insert_query,
                        task_title,
                        rev_id,
                        verdict_status.value,
                        evidence_id
                    )
                    logger.info(f"Created new verdict #{row['id']} for task '{task_title}' with status '{verdict_status}'")
                
                return TaskVerdict(
                    id=row['id'],
                    task_title=row['task_title'],
                    rev_id=row['rev_id'],
                    status=VerdictStatus(row['status']),
                    evidence_id=row['evidence_id'],
                    verdict_ts=row['verdict_ts']
                )
            finally:
                await conn.close()
                
        except Exception as e:
            logger.error(f"Error creating verdict for task '{task_title}': {e}")
            return None
    
    async def auto_verify_task(
        self,
        task_id: int,
        task_title: str,
        old_status: Optional[TaskStatus],
        new_status: TaskStatus
    ) -> Dict[str, Any]:
        """
        Автоматическая верификация задачи при изменении статуса
        
        Вызывается из Roadmap API при обновлении задачи.
        Создает вердикт если статус изменился.
        
        Args:
            task_id: ID задачи
            task_title: Название задачи
            old_status: Старый статус (None если новая задача)
            new_status: Новый статус
        
        Returns:
            Dict с информацией о созданном вердикте
        """
        result = {
            "verdict_created": False,
            "verdict_updated": False,
            "verdict_id": None,
            "status_changed": old_status != new_status
        }
        
        # Создаем вердикт только если статус изменился
        if old_status != new_status:
            verdict = await self.create_verdict_for_task(
                task_id=task_id,
                task_title=task_title,
                new_status=new_status
            )
            
            if verdict:
                result["verdict_created"] = True
                result["verdict_id"] = verdict.id
                logger.info(f"Auto-verification: Task '{task_title}' status changed {old_status} → {new_status}, verdict #{verdict.id} created")
        
        return result
    
    async def check_task_evidence(self, task_title: str) -> Optional[int]:
        """
        Проверить наличие артефактов для задачи
        
        Ищет артефакты в evidence_artifacts по названию задачи.
        
        Args:
            task_title: Название задачи
        
        Returns:
            ID найденного артефакта или None
        """
        conn = await self.get_db_connection()
        try:
            # Ищем артефакты где path содержит ключевые слова из названия задачи
            # Это простая эвристика, можно улучшить
            query = """
                SELECT id FROM eng_it.evidence_artifacts
                WHERE path_or_query ILIKE $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            # Берем первое слово из названия задачи для поиска
            search_term = f"%{task_title.split()[0] if task_title else ''}%"
            row = await conn.fetchrow(query, search_term)
            
            return row['id'] if row else None
        finally:
            await conn.close()


# Singleton instance
_truth_integration_service = None


def get_truth_integration_service() -> TruthIntegrationService:
    """Получить singleton instance TruthIntegrationService"""
    global _truth_integration_service
    if _truth_integration_service is None:
        _truth_integration_service = TruthIntegrationService()
    return _truth_integration_service
