# -*- coding: utf-8 -*-
"""
Truth System API Routes
Version: 1.0
Date: 2025-11-12

Endpoints для работы с Truth System:
- Verdicts (вердикты по задачам)
- Evidence (артефакты-доказательства)
- Truth Matrix (сравнение статусов)
- Dashboard (метрики системы)
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
import asyncpg
import os
from datetime import datetime
import uuid

from models.truth import (
    # Models
    TruthRevision,
    EvidenceArtifact,
    TaskVerdict,
    TruthMatrixRow,
    TruthMatrix,
    TruthDashboard,
    # Create models
    TruthRevisionCreate,
    EvidenceArtifactCreate,
    TaskVerdictCreate,
    TaskVerdictUpdate,
    # Enums
    VerdictStatus,
    EvidenceKind,
    # Request/Response
    VerifyTaskRequest,
    VerifyTaskResponse,
    TruthQuery,
    TruthResponse,
)


# Router setup
router = APIRouter(
    prefix="/api/v1/truth",
    tags=["truth"],
    responses={404: {"description": "Not found"}},
)


# Database connection helper
async def get_db_connection():
    """Получить подключение к БД"""
    database_url = os.getenv("DATABASE_URL", "postgres://crd_user:crd12@crd12_pgvector:5432/crd12")
    return await asyncpg.connect(database_url)


# =====================================================================
# TRUTH REVISIONS ENDPOINTS
# =====================================================================

@router.get("/revisions", response_model=List[TruthRevision])
async def get_revisions(
    active_only: bool = Query(False, description="Только активные ревизии"),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Получить список ревизий истины
    
    - **active_only**: Вернуть только активную ревизию
    - **limit**: Максимальное количество результатов
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT rev_id, file_path, sha256, commit_sha, committed_at, actor, is_active
            FROM eng_it.truth_revisions
            WHERE ($1 = false OR is_active = true)
            ORDER BY committed_at DESC
            LIMIT $2
        """
        rows = await conn.fetch(query, active_only, limit)
        
        return [
            TruthRevision(
                rev_id=row['rev_id'],
                file_path=row['file_path'],
                sha256=row['sha256'],
                commit_sha=row['commit_sha'],
                committed_at=row['committed_at'],
                actor=row['actor'],
                is_active=row['is_active']
            )
            for row in rows
        ]
    finally:
        await conn.close()


@router.post("/revisions", response_model=TruthRevision, status_code=201)
async def create_revision(revision: TruthRevisionCreate):
    """
    Создать новую ревизию истины
    
    При создании активной ревизии (is_active=true), все остальные становятся неактивными.
    """
    conn = await get_db_connection()
    try:
        # Если создаем активную ревизию, деактивируем все остальные
        if revision.is_active:
            await conn.execute("UPDATE eng_it.truth_revisions SET is_active = false")
        
        query = """
            INSERT INTO eng_it.truth_revisions 
            (file_path, sha256, commit_sha, actor, is_active)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING rev_id, file_path, sha256, commit_sha, committed_at, actor, is_active
        """
        row = await conn.fetchrow(
            query,
            revision.file_path,
            revision.sha256,
            revision.commit_sha,
            revision.actor,
            revision.is_active
        )
        
        return TruthRevision(
            rev_id=row['rev_id'],
            file_path=row['file_path'],
            sha256=row['sha256'],
            commit_sha=row['commit_sha'],
            committed_at=row['committed_at'],
            actor=row['actor'],
            is_active=row['is_active']
        )
    finally:
        await conn.close()


# =====================================================================
# EVIDENCE ARTIFACTS ENDPOINTS
# =====================================================================

@router.get("/evidence", response_model=List[EvidenceArtifact])
async def get_evidence(
    kind: Optional[EvidenceKind] = Query(None, description="Фильтр по типу артефакта"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Получить список артефактов-доказательств
    
    - **kind**: Фильтр по типу (fs, sql, http, event, git)
    - **limit**: Максимальное количество результатов
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, kind, path_or_query, result_hash, created_at
            FROM eng_it.evidence_artifacts
            WHERE ($1::text IS NULL OR kind = $1)
            ORDER BY created_at DESC
            LIMIT $2
        """
        rows = await conn.fetch(query, kind.value if kind else None, limit)
        
        return [
            EvidenceArtifact(
                id=row['id'],
                kind=EvidenceKind(row['kind']),
                path_or_query=row['path_or_query'],
                result_hash=row['result_hash'],
                created_at=row['created_at']
            )
            for row in rows
        ]
    finally:
        await conn.close()


@router.post("/evidence", response_model=EvidenceArtifact, status_code=201)
async def create_evidence(evidence: EvidenceArtifactCreate):
    """
    Создать новый артефакт-доказательство
    
    Артефакт может быть связан с вердиктом задачи.
    """
    conn = await get_db_connection()
    try:
        query = """
            INSERT INTO eng_it.evidence_artifacts 
            (kind, path_or_query, result_hash)
            VALUES ($1, $2, $3)
            RETURNING id, kind, path_or_query, result_hash, created_at
        """
        row = await conn.fetchrow(
            query,
            evidence.kind.value,
            evidence.path_or_query,
            evidence.result_hash
        )
        
        return EvidenceArtifact(
            id=row['id'],
            kind=EvidenceKind(row['kind']),
            path_or_query=row['path_or_query'],
            result_hash=row['result_hash'],
            created_at=row['created_at']
        )
    finally:
        await conn.close()


# =====================================================================
# TASK VERDICTS ENDPOINTS
# =====================================================================

@router.get("/verdicts", response_model=List[TaskVerdict])
async def get_verdicts(
    status: Optional[VerdictStatus] = Query(None, description="Фильтр по статусу"),
    has_evidence: Optional[bool] = Query(None, description="Только с/без артефактов"),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Получить список вердиктов по задачам
    
    - **status**: Фильтр по статусу (planned, in_progress, done)
    - **has_evidence**: true = только с артефактами, false = только без
    - **limit**: Максимальное количество результатов
    """
    conn = await get_db_connection()
    try:
        query = """
            SELECT id, task_title, rev_id, status, evidence_id, verdict_ts
            FROM eng_it.task_verdicts
            WHERE ($1::text IS NULL OR status = $1)
              AND ($2::boolean IS NULL OR 
                   ($2 = true AND evidence_id IS NOT NULL) OR
                   ($2 = false AND evidence_id IS NULL))
            ORDER BY verdict_ts DESC
            LIMIT $3
        """
        rows = await conn.fetch(
            query,
            status.value if status else None,
            has_evidence,
            limit
        )
        
        return [
            TaskVerdict(
                id=row['id'],
                task_title=row['task_title'],
                rev_id=row['rev_id'],
                status=VerdictStatus(row['status']),
                evidence_id=row['evidence_id'],
                verdict_ts=row['verdict_ts']
            )
            for row in rows
        ]
    finally:
        await conn.close()


@router.post("/verdicts", response_model=TaskVerdict, status_code=201)
async def create_verdict(verdict: TaskVerdictCreate):
    """
    Создать новый вердикт по задаче
    
    Вердикт связывает задачу с ревизией и опционально с артефактом.
    """
    conn = await get_db_connection()
    try:
        query = """
            INSERT INTO eng_it.task_verdicts 
            (task_title, rev_id, status, evidence_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id, task_title, rev_id, status, evidence_id, verdict_ts
        """
        row = await conn.fetchrow(
            query,
            verdict.task_title,
            verdict.rev_id,
            verdict.status.value,
            verdict.evidence_id
        )
        
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


@router.patch("/verdicts/{verdict_id}", response_model=TaskVerdict)
async def update_verdict(verdict_id: int, update: TaskVerdictUpdate):
    """
    Обновить вердикт по задаче
    
    Можно обновить статус и/или добавить артефакт.
    """
    conn = await get_db_connection()
    try:
        # Построить динамический запрос
        updates = []
        params = []
        param_idx = 1
        
        if update.status is not None:
            updates.append(f"status = ${param_idx}")
            params.append(update.status.value)
            param_idx += 1
        
        if update.evidence_id is not None:
            updates.append(f"evidence_id = ${param_idx}")
            params.append(update.evidence_id)
            param_idx += 1
        
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        params.append(verdict_id)
        query = f"""
            UPDATE eng_it.task_verdicts
            SET {', '.join(updates)}
            WHERE id = ${param_idx}
            RETURNING id, task_title, rev_id, status, evidence_id, verdict_ts
        """
        
        row = await conn.fetchrow(query, *params)
        if not row:
            raise HTTPException(status_code=404, detail="Verdict not found")
        
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


# =====================================================================
# TRUTH MATRIX ENDPOINTS
# =====================================================================

@router.get("/matrix", response_model=TruthMatrix)
async def get_truth_matrix(limit: int = Query(100, ge=1, le=500)):
    """
    Получить Truth Matrix - сравнение Navigator vs Verified статусов
    
    Показывает расхождения между заявленными и верифицированными статусами задач.
    """
    conn = await get_db_connection()
    try:
        # Получить строки матрицы
        query = """
            SELECT 
                title,
                navigator_status,
                verified_status,
                has_evidence,
                verdict_ts,
                sha256,
                file_path
            FROM eng_it.v_truth_matrix
            ORDER BY verdict_ts DESC NULLS LAST
            LIMIT $1
        """
        rows = await conn.fetch(query, limit)
        
        matrix_rows = [
            TruthMatrixRow(
                title=row['title'],
                navigator_status=row['navigator_status'],
                verified_status=row['verified_status'],
                has_evidence=row['has_evidence'],
                verdict_ts=row['verdict_ts'],
                sha256=row['sha256'],
                file_path=row['file_path']
            )
            for row in rows
        ]
        
        # Подсчитать метрики
        total_tasks = len(matrix_rows)
        verified_tasks = sum(1 for r in matrix_rows if r.verified_status)
        with_evidence = sum(1 for r in matrix_rows if r.has_evidence)
        
        # Подсчитать расхождения
        mismatch_count = sum(
            1 for r in matrix_rows
            if r.navigator_status and r.verified_status and r.navigator_status != r.verified_status
        )
        
        # Получить активную ревизию
        rev_query = """
            SELECT rev_id, file_path, sha256, commit_sha, committed_at, actor, is_active
            FROM eng_it.truth_revisions
            WHERE is_active = true
            LIMIT 1
        """
        rev_row = await conn.fetchrow(rev_query)
        last_revision = None
        if rev_row:
            last_revision = TruthRevision(
                rev_id=rev_row['rev_id'],
                file_path=rev_row['file_path'],
                sha256=rev_row['sha256'],
                commit_sha=rev_row['commit_sha'],
                committed_at=rev_row['committed_at'],
                actor=rev_row['actor'],
                is_active=rev_row['is_active']
            )
        
        return TruthMatrix(
            rows=matrix_rows,
            total_tasks=total_tasks,
            verified_tasks=verified_tasks,
            with_evidence=with_evidence,
            mismatch_count=mismatch_count,
            last_revision=last_revision
        )
    finally:
        await conn.close()


# =====================================================================
# DASHBOARD ENDPOINT
# =====================================================================

@router.get("/dashboard", response_model=TruthDashboard)
async def get_truth_dashboard():
    """
    Получить Dashboard метрики Truth System
    
    Возвращает общую статистику по ревизиям, вердиктам и артефактам.
    """
    conn = await get_db_connection()
    try:
        # Total revisions
        total_revisions = await conn.fetchval("SELECT COUNT(*) FROM eng_it.truth_revisions")
        
        # Active revision
        rev_row = await conn.fetchrow("""
            SELECT rev_id, file_path, sha256, commit_sha, committed_at, actor, is_active
            FROM eng_it.truth_revisions
            WHERE is_active = true
            LIMIT 1
        """)
        active_revision = None
        if rev_row:
            active_revision = TruthRevision(
                rev_id=rev_row['rev_id'],
                file_path=rev_row['file_path'],
                sha256=rev_row['sha256'],
                commit_sha=rev_row['commit_sha'],
                committed_at=rev_row['committed_at'],
                actor=rev_row['actor'],
                is_active=rev_row['is_active']
            )
        
        # Verdicts stats
        total_verdicts = await conn.fetchval("SELECT COUNT(*) FROM eng_it.task_verdicts")
        verdicts_with_evidence = await conn.fetchval(
            "SELECT COUNT(*) FROM eng_it.task_verdicts WHERE evidence_id IS NOT NULL"
        )
        
        # Artifacts stats
        total_artifacts = await conn.fetchval("SELECT COUNT(*) FROM eng_it.evidence_artifacts")
        artifacts_rows = await conn.fetch("SELECT kind, COUNT(*) as cnt FROM eng_it.evidence_artifacts GROUP BY kind")
        artifacts_by_kind = {row['kind']: row['cnt'] for row in artifacts_rows}
        
        # Coverage calculations
        total_tasks = await conn.fetchval("SELECT COUNT(*) FROM eng_it.roadmap_tasks")
        verification_coverage = (total_verdicts / total_tasks * 100) if total_tasks > 0 else 0.0
        evidence_coverage = (verdicts_with_evidence / total_verdicts * 100) if total_verdicts > 0 else 0.0
        
        return TruthDashboard(
            total_revisions=total_revisions,
            active_revision=active_revision,
            total_verdicts=total_verdicts,
            verdicts_with_evidence=verdicts_with_evidence,
            total_artifacts=total_artifacts,
            artifacts_by_kind=artifacts_by_kind,
            verification_coverage=round(verification_coverage, 2),
            evidence_coverage=round(evidence_coverage, 2)
        )
    finally:
        await conn.close()


# =====================================================================
# HEALTH CHECK
# =====================================================================

@router.get("/health")
async def truth_health():
    """Health check для Truth API"""
    return {
        "status": "ok",
        "service": "truth-system",
        "timestamp": datetime.utcnow().isoformat()
    }
