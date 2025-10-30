import asyncpg
import hashlib
import time
import uuid
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

class IdempotencyManager:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    async def get_existing_result(self, idempotency_key: str) -> Optional[Dict[str, Any]]:
        """Получить существующий результат по ключу идемпотентности"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT status, result FROM core.patches 
                WHERE idempotency_key = $1
            ''', idempotency_key)
            
            return dict(row) if row else None
    
    async def create_patch_record(self, 
                                idempotency_key: str, 
                                target_path: str, 
                                code_sha256: str,
                                job_id: Optional[str] = None) -> bool:
        """Создать запись о патче (возвращает True если создана новая)"""
        async with self.db_pool.acquire() as conn:
            try:
                await conn.execute('''
                    INSERT INTO core.patches 
                    (job_id, idempotency_key, target_path, code_sha256, status)
                    VALUES ($1, $2, $3, $4, 'planned')
                ''', job_id, idempotency_key, target_path, code_sha256)
                return True
            except asyncpg.UniqueViolationError:
                return False
    
    async def update_patch_status(self, idempotency_key: str, status: str, result: Dict[str, Any] = None):
        """Обновить статус патча"""
        async with self.db_pool.acquire() as conn:
            if result:
                await conn.execute('''
                    UPDATE core.patches 
                    SET status = $1, result = $2, updated_at = NOW()
                    WHERE idempotency_key = $3
                ''', status, result, idempotency_key)
            else:
                await conn.execute('''
                    UPDATE core.patches 
                    SET status = $1, updated_at = NOW()
                    WHERE idempotency_key = $2
                ''', status, idempotency_key)

class AdvisoryLockManager:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool
    
    def _get_lock_key(self, target_path: str) -> int:
        """Генерация ключа блокировки для target_path"""
        normalized_path = target_path.strip().lower()
        hash_obj = hashlib.sha256(normalized_path.encode())
        # Берём первые 8 байт для bigint
        return int.from_bytes(hash_obj.digest()[:8], byteorder='big', signed=True)
    
    @asynccontextmanager
    async def acquire_lock(self, target_path: str, timeout_s: int = 30):
        """Контекстный менеджер для advisory lock"""
        lock_key = self._get_lock_key(target_path)
        conn = None
        
        try:
            # Отдельное соединение для блокировки
            conn = await self.db_pool.acquire()
            
            start_time = time.time()
            locked = False
            
            # Попытка захвата блокировки с таймаутом
            while time.time() - start_time < timeout_s:
                locked = await conn.fetchval('SELECT pg_try_advisory_lock($1)', lock_key)
                if locked:
                    break
                await asyncio.sleep(0.1)
            
            if not locked:
                raise LockTimeoutError(f'Не удалось захватить блокировку для {target_path} за {timeout_s}с')
            
            yield lock_key
            
        finally:
            if conn:
                try:
                    await conn.execute('SELECT pg_advisory_unlock($1)', lock_key)
                    await self.db_pool.release(conn)
                except Exception as e:
                    print(f'⚠️ Ошибка при освобождении блокировки: {e}')

class LockTimeoutError(Exception):
    pass

def generate_idempotency_key(target_file: str, code: str, task_text: str) -> str:
    """Генерация ключа идемпотентности"""
    normalized_task = task_text.strip().lower()
    content = f"{target_file}||{code}||{normalized_task}"
    return hashlib.sha256(content.encode()).hexdigest()

# Утилиты для инициализации
async def create_db_pool() -> asyncpg.Pool:
    """Создать пул соединений с БД"""
    return await asyncpg.create_pool(
        host='crd12_pgvector',
        port=5432,
        database='crd12',
        user='crd_user',
        password='crd12',
        min_size=1,
        max_size=10
    )
