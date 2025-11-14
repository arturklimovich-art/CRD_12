#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic models для Roadmap Module
Version: 2.0
Date: 2025-11-12
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


# =====================================================================
# ENUMS
# =====================================================================

class BlockStatus(str, Enum):
    """Статусы блоков"""
    planned = "planned"
    in_progress = "in_progress"
    done = "done"
    archived = "archived"


class BlockKind(str, Enum):
    """Типы блоков"""
    L = "L"  # Learning
    B = "B"  # Building
    TL = "TL"  # TradLab
    OTHER = "OTHER"


class TaskStatus(str, Enum):
    """Статусы задач"""
    planned = "planned"
    in_progress = "in_progress"
    done = "done"
    failed = "failed"
    blocked = "blocked"
    removed = "removed"


class TaskKind(str, Enum):
    """Типы задач"""
    task = "task"
    subtask = "subtask"
    epic = "epic"
    milestone = "milestone"


class EventType(str, Enum):
    """Типы событий"""
    created = "created"
    status_changed = "status_changed"
    updated = "updated"
    tz_generated = "tz_generated"
    impl_started = "impl_started"
    impl_done = "impl_done"
    archived = "archived"


# =====================================================================
# ROADMAP BLOCK MODELS
# =====================================================================

class RoadmapBlockBase(BaseModel):
    """Базовая модель блока"""
    code: str = Field(..., description="Уникальный код блока (E1-L1, E1-B13)")
    title: str = Field(..., description="Название блока")
    stage: str = Field(..., description="Этап (E1, E2, TL1)")
    kind: BlockKind = Field(..., description="Тип блока (L, B, TL)")
    status: BlockStatus = Field(BlockStatus.planned, description="Статус блока")
    priority: int = Field(100, ge=0, le=1000, description="Приоритет (0-1000)")
    description: Optional[str] = Field(None, description="Описание блока")
    meta: Optional[Dict[str, Any]] = Field(None, description="Дополнительные метаданные")
    
    @validator('code')
    def validate_code(cls, v):
        """Валидация формата кода блока"""
        import re
        if not re.match(r'^[A-Z0-9]+-[A-Z0-9]+$', v):
            raise ValueError('Code must match pattern: E1-L1, E1-B13, TL1-AGENT')
        return v


class RoadmapBlockCreate(RoadmapBlockBase):
    """Модель для создания блока"""
    pass


class RoadmapBlockUpdate(BaseModel):
    """Модель для обновления блока"""
    title: Optional[str] = None
    status: Optional[BlockStatus] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None


class RoadmapBlock(RoadmapBlockBase):
    """Полная модель блока (с ID)"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =====================================================================
# ROADMAP TASK MODELS
# =====================================================================

class RoadmapTaskBase(BaseModel):
    """Базовая модель задачи"""
    code: str = Field(..., description="Код задачи (E1-B13-IMPL)")
    title: str = Field(..., description="Название задачи")
    block_id: Optional[int] = Field(None, description="ID блока")
    status: TaskStatus = Field(TaskStatus.planned, description="Статус задачи")
    kind: TaskKind = Field(TaskKind.task, description="Тип задачи")
    priority: int = Field(100, ge=0, le=1000, description="Приоритет")
    description: Optional[str] = Field(None, description="Описание")
    tz_ref: Optional[str] = Field(None, description="Ссылка на ТЗ")
    steps: Optional[List[Dict[str, Any]]] = Field(None, description="Шаги задачи (JSONB)")
    mechanisms: Optional[List[Dict[str, Any]]] = Field(None, description="Механизмы реализации")
    artifacts: Optional[List[Dict[str, Any]]] = Field(None, description="Артефакты")
    meta: Optional[Dict[str, Any]] = Field(None, description="Метаданные")


class RoadmapTaskCreate(RoadmapTaskBase):
    """Модель для создания задачи"""
    id: int = Field(..., description="ID задачи (должен быть уникальным)")


class RoadmapTaskUpdate(BaseModel):
    """Модель для обновления задачи"""
    block_id: Optional[int] = None
    title: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    description: Optional[str] = None
    tz_ref: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    mechanisms: Optional[List[Dict[str, Any]]] = None
    artifacts: Optional[List[Dict[str, Any]]] = None
    meta: Optional[Dict[str, Any]] = None


class RoadmapTask(RoadmapTaskBase):
    """Полная модель задачи"""
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# =====================================================================
# ROADMAP EVENT MODELS
# =====================================================================

class RoadmapEventCreate(BaseModel):
    """Модель для создания события"""
    entity_type: str = Field(..., description="Тип сущности (block|task)")
    entity_id: int = Field(..., description="ID сущности")
    event_type: EventType = Field(..., description="Тип события")
    old_value: Optional[Dict[str, Any]] = Field(None, description="Старое значение")
    new_value: Optional[Dict[str, Any]] = Field(None, description="Новое значение")
    changed_by: str = Field("system", description="Кто изменил")
    meta: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст")


class RoadmapEvent(RoadmapEventCreate):
    """Полная модель события"""
    id: int
    ts: datetime
    
    class Config:
        from_attributes = True


# =====================================================================
# DASHBOARD MODELS
# =====================================================================

class DashboardBlock(BaseModel):
    """Блок для dashboard"""
    block_code: str
    block_title: str
    block_status: str
    total_tasks: int
    done_tasks: int
    in_progress_tasks: int
    planned_tasks: int
    completion_percentage: float
    
    class Config:
        from_attributes = True


class RoadmapDashboard(BaseModel):
    """Dashboard метрики"""
    blocks: List[DashboardBlock]
    total_blocks: int
    total_tasks: int
    total_done: int
    total_in_progress: int
    total_planned: int
    overall_completion: float


# =====================================================================
# QUERY MODELS
# =====================================================================

class RoadmapQuery(BaseModel):
    """Параметры запроса Roadmap"""
    stage: Optional[str] = Field(None, description="Фильтр по этапу (E1, TL1)")
    kind: Optional[str] = Field(None, description="Фильтр по типу (L, B, TL)")
    status: Optional[str] = Field(None, description="Фильтр по статусу")
    limit: int = Field(50, ge=1, le=1000, description="Лимит результатов")
    offset: int = Field(0, ge=0, description="Offset для пагинации")


# =====================================================================
# RESPONSE MODELS
# =====================================================================

class RoadmapResponse(BaseModel):
    """Стандартный ответ API"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RoadmapSyncResponse(BaseModel):
    """Ответ на запрос синхронизации"""
    success: bool
    yaml_generated: bool
    md_generated: bool
    blocks_count: int
    tasks_count: int
    file_paths: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
