# -*- coding: utf-8 -*-
"""
Pydantic models для Truth System (Система Истины)
Version: 1.0
Date: 2025-11-12
Author: arturklimovich-art

Truth System - модуль верификации выполнения задач через артефакты.
Связь: roadmap_tasks → task_verdicts → evidence_artifacts → truth_revisions
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


# =====================================================================
# ENUMS
# =====================================================================

class VerdictStatus(str, Enum):
    """Статусы вердиктов (должны совпадать с БД)"""
    planned = "planned"
    in_progress = "in_progress"
    done = "done"


class EvidenceKind(str, Enum):
    """Типы артефактов-доказательств"""
    fs = "fs"          # File System (файлы)
    sql = "sql"        # SQL миграции/queries
    http = "http"      # HTTP responses
    event = "event"    # Event logs
    git = "git"        # Git commits


# =====================================================================
# TRUTH REVISION MODELS
# =====================================================================

class TruthRevisionBase(BaseModel):
    """Базовая модель ревизии (версии) истины"""
    file_path: str = Field(..., description="Путь к файлу источника истины")
    sha256: str = Field(..., description="SHA256 хэш файла")
    commit_sha: Optional[str] = Field(None, description="SHA commit в Git")
    actor: Optional[str] = Field(None, description="Кто создал ревизию")
    is_active: bool = Field(False, description="Является ли активной ревизией")

    @validator('sha256')
    def validate_sha256(cls, v):
        """Валидация SHA256 формата"""
        import re
        if not re.match(r'^[a-f0-9]{64}$', v.lower()):
            raise ValueError('sha256 must be 64 hex characters')
        return v.lower()


class TruthRevisionCreate(TruthRevisionBase):
    """Модель для создания ревизии"""
    pass


class TruthRevision(TruthRevisionBase):
    """Полная модель ревизии (с ID)"""
    rev_id: uuid.UUID
    committed_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# EVIDENCE ARTIFACT MODELS
# =====================================================================

class EvidenceArtifactBase(BaseModel):
    """Базовая модель артефакта-доказательства"""
    kind: EvidenceKind = Field(..., description="Тип артефакта (fs|sql|http|event|git)")
    path_or_query: str = Field(..., description="Путь к файлу или текст запроса")
    result_hash: Optional[str] = Field(None, description="Хэш результата проверки")


class EvidenceArtifactCreate(EvidenceArtifactBase):
    """Модель для создания артефакта"""
    pass


class EvidenceArtifact(EvidenceArtifactBase):
    """Полная модель артефакта"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================================
# TASK VERDICT MODELS
# =====================================================================

class TaskVerdictBase(BaseModel):
    """Базовая модель вердикта по задаче"""
    task_title: str = Field(..., description="Название задачи (должно совпадать с roadmap_tasks.title)")
    rev_id: uuid.UUID = Field(..., description="ID ревизии истины")
    status: VerdictStatus = Field(..., description="Статус вердикта (planned|in_progress|done)")
    evidence_id: Optional[int] = Field(None, description="ID артефакта-доказательства")


class TaskVerdictCreate(TaskVerdictBase):
    """Модель для создания вердикта"""
    pass


class TaskVerdictUpdate(BaseModel):
    """Модель для обновления вердикта"""
    status: Optional[VerdictStatus] = None
    evidence_id: Optional[int] = None


class TaskVerdict(TaskVerdictBase):
    """Полная модель вердикта"""
    id: int
    verdict_ts: datetime

    class Config:
        from_attributes = True


# =====================================================================
# TRUTH MATRIX MODELS (для view eng_it.v_truth_matrix)
# =====================================================================

class TruthMatrixRow(BaseModel):
    """Строка Truth Matrix - сравнение Navigator vs Verified статусов"""
    title: str = Field(..., description="Название задачи")
    navigator_status: Optional[str] = Field(None, description="Статус из Navigator (eng_it.tasks)")
    verified_status: Optional[str] = Field(None, description="Верифицированный статус (task_verdicts)")
    has_evidence: bool = Field(False, description="Есть ли артефакт-доказательство")
    verdict_ts: Optional[datetime] = Field(None, description="Время вердикта")
    sha256: Optional[str] = Field(None, description="SHA256 ревизии")
    file_path: Optional[str] = Field(None, description="Путь к файлу ревизии")

    class Config:
        from_attributes = True


class TruthMatrix(BaseModel):
    """Truth Matrix - полная картина верификации"""
    rows: List[TruthMatrixRow]
    total_tasks: int
    verified_tasks: int
    with_evidence: int
    mismatch_count: int  # Количество расхождений между navigator_status и verified_status
    last_revision: Optional[TruthRevision] = None


# =====================================================================
# DASHBOARD MODELS
# =====================================================================

class TruthDashboard(BaseModel):
    """Dashboard метрики Truth System"""
    total_revisions: int
    active_revision: Optional[TruthRevision] = None
    total_verdicts: int
    verdicts_with_evidence: int
    total_artifacts: int
    artifacts_by_kind: Dict[str, int]  # {'fs': 5, 'sql': 3, ...}
    verification_coverage: float  # % задач с вердиктами
    evidence_coverage: float  # % вердиктов с артефактами


# =====================================================================
# VERIFICATION REQUEST MODELS
# =====================================================================

class VerifyTaskRequest(BaseModel):
    """Запрос на верификацию задачи"""
    task_title: str = Field(..., description="Название задачи для верификации")
    expected_status: VerdictStatus = Field(..., description="Ожидаемый статус")
    evidence_kind: Optional[EvidenceKind] = Field(None, description="Тип артефакта")
    evidence_path: Optional[str] = Field(None, description="Путь к артефакту")


class VerifyTaskResponse(BaseModel):
    """Результат верификации задачи"""
    success: bool
    task_title: str
    verdict_status: VerdictStatus
    has_evidence: bool
    evidence_id: Optional[int] = None
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =====================================================================
# QUERY MODELS
# =====================================================================

class TruthQuery(BaseModel):
    """Параметры запроса Truth данных"""
    status: Optional[VerdictStatus] = Field(None, description="Фильтр по статусу вердиктов")
    has_evidence: Optional[bool] = Field(None, description="Только с/без артефактов")
    evidence_kind: Optional[EvidenceKind] = Field(None, description="Фильтр по типу артефакта")
    limit: int = Field(50, ge=1, le=1000, description="Лимит результатов")
    offset: int = Field(0, ge=0, description="Offset для пагинации")


# =====================================================================
# RESPONSE MODELS
# =====================================================================

class TruthResponse(BaseModel):
    """Стандартный ответ Truth API"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
