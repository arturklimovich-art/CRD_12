#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roadmap API Endpoints
Version: 2.0
Date: 2025-11-12
"""

from fastapi import APIRouter, HTTPException, Query, Path, Body
from typing import List, Optional
from datetime import datetime

from models.roadmap import (
    RoadmapBlock, RoadmapBlockCreate, RoadmapBlockUpdate,
    RoadmapTask, RoadmapTaskCreate, RoadmapTaskUpdate,
    RoadmapResponse, RoadmapDashboard, RoadmapSyncResponse,
    BlockStatus, TaskStatus
)
from services.roadmap_service import RoadmapService
from services.truth_integration_service import get_truth_integration_service

# =====================================================================
# ROUTER
# =====================================================================

router = APIRouter(
    prefix="/api/v1/roadmap",
    tags=["roadmap"],
    responses={404: {"description": "Not found"}}
)

service = RoadmapService()


# =====================================================================
# BLOCKS ENDPOINTS
# =====================================================================

@router.get("/blocks", response_model=List[RoadmapBlock])
async def get_blocks(
    stage: Optional[str] = Query(None, description="Фильтр по этапу (E1, TL1)"),
    kind: Optional[str] = Query(None, description="Фильтр по типу (L, B, TL)"),
    status: Optional[BlockStatus] = Query(None, description="Фильтр по статусу"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Получить список блоков Roadmap
    
    - **stage**: Этап (E1, E2, TL1)
    - **kind**: Тип блока (L=Learning, B=Building, TL=TradLab)
    - **status**: Статус (planned, in_progress, done, archived)
    """
    try:
        status_value = status.value if status else None
        blocks = service.get_blocks(
            stage=stage,
            kind=kind,
            status=status_value,
            limit=limit,
            offset=offset
        )
        return blocks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/blocks/{code}", response_model=RoadmapBlock)
async def get_block(
    code: str = Path(..., description="Код блока (E1-L1, E1-B13)")
):
    """Получить блок по коду"""
    block = service.get_block_by_code(code)
    if not block:
        raise HTTPException(status_code=404, detail=f"Block {code} not found")
    return block


@router.post("/blocks", response_model=RoadmapResponse)
async def create_block(block: RoadmapBlockCreate):
    """
    Создать новый блок Roadmap
    
    Пример:
    `json
    {
        "code": "E1-L9",
        "title": "New Learning Block",
        "stage": "E1",
        "kind": "L",
        "status": "planned",
        "priority": 90,
        "description": "Description here"
    }
    `
    """
    try:
        # Проверка существования
        existing = service.get_block_by_code(block.code)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Block {block.code} already exists"
            )
        
        result = service.create_block(block.dict())
        return RoadmapResponse(
            success=True,
            message=f"Block {block.code} created successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/blocks/{code}", response_model=RoadmapResponse)
async def update_block(
    code: str = Path(..., description="Код блока"),
    update: RoadmapBlockUpdate = Body(...)
):
    """
    Обновить блок
    
    Можно обновить: title, status, priority, description, meta
    """
    try:
        result = service.update_block(code, update.dict(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail=f"Block {code} not found")
        
        return RoadmapResponse(
            success=True,
            message=f"Block {code} updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# TASKS ENDPOINTS
# =====================================================================

@router.get("/tasks", response_model=List[RoadmapTask])
async def get_tasks(
    block_code: Optional[str] = Query(None, description="Фильтр по блоку"),
    status: Optional[TaskStatus] = Query(None, description="Фильтр по статусу"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """Получить список задач"""
    try:
        status_value = status.value if status else None
        tasks = service.get_tasks(
            block_code=block_code,
            status=status_value,
            limit=limit,
            offset=offset
        )
        return tasks
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=RoadmapTask)
async def get_task(
    task_id: int = Path(..., description="ID задачи")
):
    """Получить задачу по ID"""
    task = service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("/tasks", response_model=RoadmapResponse)
async def create_task(task: RoadmapTaskCreate):
    """
    Создать новую задачу
    
    Пример:
    `json
    {
        "id": 2000,
        "block_id": 1,
        "code": "E1-L9-TASK1",
        "title": "New task",
        "status": "planned",
        "priority": 100
    }
    `
    """
    try:
        # Проверка существования
        existing = service.get_task_by_id(task.id)
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Task {task.id} already exists"
            )
        
        result = service.create_task(task.dict())
        return RoadmapResponse(
            success=True,
            message=f"Task {task.id} created successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/tasks/{task_id}", response_model=RoadmapResponse)
async def update_task(
    task_id: int = Path(..., description="ID задачи"),
    update: RoadmapTaskUpdate = Body(...)
):
    """
    Обновить задачу
    
    Можно обновить: block_id, title, status, priority, description, 
                    tz_ref, steps, mechanisms, artifacts, meta
    """
    try:
        result = service.update_task(task_id, update.dict(exclude_unset=True))

        # === TRUTH INTEGRATION: Auto-verify task status change ===
        try:
            truth_service = get_truth_integration_service()
            
            # Получить старый статус из result (до обновления в БД нужно было бы запросить)
            # Для упрощения: если статус изменился, создаем вердикт
            if 'status' in update.dict(exclude_unset=True):
                verification_result = await truth_service.auto_verify_task(
                    task_id=task_id,
                    task_title=result.get('title', 'Unknown'),
                    old_status=None,  # TODO: получить из БД перед обновлением
                    new_status=update.status
                )
                
                # Добавляем информацию о верификации в response data
                if result:
                    result['_truth_verification'] = verification_result
        except Exception as e_truth:
            # Не падаем если Truth integration не работает
            import logging
            logging.warning(f'Truth integration failed for task {task_id}: {e_truth}')

        if not result:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        return RoadmapResponse(
            success=True,
            message=f"Task {task_id} updated successfully",
            data=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# DASHBOARD ENDPOINT
# =====================================================================

@router.get("/dashboard", response_model=RoadmapDashboard)
async def get_dashboard():
    """
    Получить dashboard метрики
    
    Возвращает:
    - Список блоков с метриками выполнения
    - Общую статистику по всем задачам
    """
    try:
        return service.get_dashboard()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# SYNC ENDPOINT
# =====================================================================

@router.post("/sync", response_model=RoadmapSyncResponse)
async def sync_roadmap():
    """
    Синхронизация: генерация YAML из БД
    
    Создаёт ROADMAP_SYNC_AUTO.yaml из текущего состояния БД
    """
    try:
        success, result = service.sync_to_yaml()
        
        if not success:
            raise HTTPException(status_code=500, detail=result.get('error'))
        
        dashboard = service.get_dashboard()
        
        return RoadmapSyncResponse(
            success=True,
            yaml_generated=True,
            md_generated=False,
            blocks_count=dashboard['total_blocks'],
            tasks_count=dashboard['total_tasks'],
            file_paths=result
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
