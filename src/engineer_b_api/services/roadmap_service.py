#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Roadmap Service - бизнес-логика для работы с Roadmap
Version: 2.0
Date: 2025-11-12
"""

import os
import yaml
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import json


class RoadmapService:
    """Сервис для работы с Roadmap Module"""
    
    def __init__(self):
        self.db_dsn = os.getenv(
            "DATABASE_URL", 
            "postgres://crd_user:crd12@crd12_pgvector:5432/crd12"
        )
    
    def _get_connection(self):
        """Получение подключения к БД"""
        return psycopg2.connect(self.db_dsn)
    
    # ================================================================
    # BLOCKS
    # ================================================================
    
    def get_blocks(
        self, 
        stage: Optional[str] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Получить список блоков с фильтрацией"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        id, code, title, stage, kind, status, priority,
                        description, meta, created_at, updated_at
                    FROM eng_it.roadmap_blocks
                    WHERE 1=1
                """
                params = []
                
                if stage:
                    query += " AND stage = %s"
                    params.append(stage)
                
                if kind:
                    query += " AND kind = %s"
                    params.append(kind)
                
                if status:
                    query += " AND status = %s"
                    params.append(status)
                
                query += " ORDER BY stage, priority LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def get_block_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Получить блок по коду"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        id, code, title, stage, kind, status, priority,
                        description, meta, created_at, updated_at
                    FROM eng_it.roadmap_blocks
                    WHERE code = %s
                """, (code,))
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()
    
    def create_block(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новый блок"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO eng_it.roadmap_blocks 
                        (code, title, stage, kind, status, priority, description, meta)
                    VALUES (%(code)s, %(title)s, %(stage)s, %(kind)s, %(status)s, 
                            %(priority)s, %(description)s, %(meta)s)
                    RETURNING id, code, title, stage, kind, status, priority, 
                              description, meta, created_at, updated_at
                """, block_data)
                
                result = dict(cur.fetchone())
                
                # Логирование события
                cur.execute("""
                    INSERT INTO eng_it.roadmap_events 
                        (entity_type, entity_id, event_type, new_value, changed_by)
                    VALUES ('block', %s, 'created', %s, 'api')
                """, (result['id'], json.dumps(result, default=str)))
                
                conn.commit()
                return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_block(self, code: str, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновить блок"""
        conn = self._get_connection()
        try:
            # Получаем старое значение
            block = self.get_block_by_code(code)
            if not block:
                return None
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Формируем SET clause динамически
                set_parts = []
                params = []
                for key, value in update_data.items():
                    if key in ['title', 'status', 'priority', 'description', 'meta']:
                        set_parts.append(f"{key} = %s")
                        params.append(value)
                
                if not set_parts:
                    return block
                
                set_parts.append("updated_at = NOW()")
                params.append(code)
                
                query = f"""
                    UPDATE eng_it.roadmap_blocks 
                    SET {', '.join(set_parts)}
                    WHERE code = %s
                    RETURNING id, code, title, stage, kind, status, priority,
                              description, meta, created_at, updated_at
                """
                
                cur.execute(query, params)
                result = dict(cur.fetchone())
                
                # Логирование события
                cur.execute("""
                    INSERT INTO eng_it.roadmap_events 
                        (entity_type, entity_id, event_type, old_value, new_value, changed_by)
                    VALUES ('block', %s, 'updated', %s, %s, 'api')
                """, (result['id'], json.dumps(block, default=str), json.dumps(result, default=str)))
                
                conn.commit()
                return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # ================================================================
    # TASKS
    # ================================================================
    
    def get_tasks(
        self,
        block_code: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Получить список задач"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT 
                        rt.id, rt.code, rt.title, rt.status, rt.kind, rt.priority,
                        rt.description, rt.tz_ref, rt.steps, rt.mechanisms, rt.artifacts,
                        rt.meta, rt.created_at, rt.updated_at, rt.completed_at,
                        rb.code as block_code, rb.title as block_title
                    FROM eng_it.roadmap_tasks rt
                    LEFT JOIN eng_it.roadmap_blocks rb ON rb.id = rt.block_id
                    WHERE 1=1
                """
                params = []
                
                if block_code:
                    query += " AND rb.code = %s"
                    params.append(block_code)
                
                if status:
                    query += " AND rt.status = %s"
                    params.append(status)
                
                query += " ORDER BY rt.priority DESC, rt.id LIMIT %s OFFSET %s"
                params.extend([limit, offset])
                
                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Получить задачу по ID"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        rt.id, rt.code, rt.title, rt.status, rt.kind, rt.priority,
                        rt.description, rt.tz_ref, rt.steps, rt.mechanisms, rt.artifacts,
                        rt.meta, rt.created_at, rt.updated_at, rt.completed_at,
                        rb.code as block_code, rb.title as block_title
                    FROM eng_it.roadmap_tasks rt
                    LEFT JOIN eng_it.roadmap_blocks rb ON rb.id = rt.block_id
                    WHERE rt.id = %s
                """, (task_id,))
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()
    
    def create_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новую задачу"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    INSERT INTO eng_it.roadmap_tasks 
                        (id, block_id, code, title, status, kind, priority, 
                         description, tz_ref, steps, mechanisms, artifacts, meta)
                    VALUES (%(id)s, %(block_id)s, %(code)s, %(title)s, %(status)s, 
                            %(kind)s, %(priority)s, %(description)s, %(tz_ref)s,
                            %(steps)s, %(mechanisms)s, %(artifacts)s, %(meta)s)
                    RETURNING id, code, title, status, kind, priority, description,
                              tz_ref, steps, mechanisms, artifacts, meta,
                              created_at, updated_at, completed_at
                """, task_data)
                
                result = dict(cur.fetchone())
                
                # Логирование события
                cur.execute("""
                    INSERT INTO eng_it.roadmap_events 
                        (entity_type, entity_id, event_type, new_value, changed_by)
                    VALUES ('task', %s, 'created', %s, 'api')
                """, (result['id'], json.dumps(result, default=str)))
                
                conn.commit()
                return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def update_task(self, task_id: int, update_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Обновить задачу"""
        conn = self._get_connection()
        try:
            # Получаем старое значение
            task = self.get_task_by_id(task_id)
            if not task:
                return None
            
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Формируем SET clause
                set_parts = []
                params = []
                for key, value in update_data.items():
                    if key in ['block_id', 'title', 'status', 'priority', 'description', 
                              'tz_ref', 'steps', 'mechanisms', 'artifacts', 'meta']:
                        set_parts.append(f"{key} = %s")
                        params.append(value)
                
                if not set_parts:
                    return task
                
                # Если статус меняется на 'done', обновляем completed_at
                if 'status' in update_data and update_data['status'] == 'done':
                    set_parts.append("completed_at = NOW()")
                
                set_parts.append("updated_at = NOW()")
                params.append(task_id)
                
                query = f"""
                    UPDATE eng_it.roadmap_tasks 
                    SET {', '.join(set_parts)}
                    WHERE id = %s
                    RETURNING id, code, title, status, kind, priority, description,
                              tz_ref, steps, mechanisms, artifacts, meta,
                              created_at, updated_at, completed_at
                """
                
                cur.execute(query, params)
                result = dict(cur.fetchone())
                
                # Логирование события
                event_type = 'status_changed' if 'status' in update_data else 'updated'
                cur.execute("""
                    INSERT INTO eng_it.roadmap_events 
                        (entity_type, entity_id, event_type, old_value, new_value, changed_by)
                    VALUES ('task', %s, %s, %s, %s, 'api')
                """, (result['id'], event_type, json.dumps(task, default=str), json.dumps(result, default=str)))
                
                conn.commit()
                return result
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    # ================================================================
    # DASHBOARD
    # ================================================================
    
    def get_dashboard(self) -> Dict[str, Any]:
        """Получить dashboard метрики"""
        conn = self._get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Блоки с метриками
                cur.execute("""
                    SELECT * FROM eng_it.v_roadmap_dashboard
                    ORDER BY block_code
                """)
                blocks = [dict(row) for row in cur.fetchall()]
                
                # Fix None values in completion_percentage
                for block in blocks:
                    if block.get('completion_percentage') is None:
                        block['completion_percentage'] = 0.0
                
                # Общие метрики
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT rb.id) as total_blocks,
                        COUNT(rt.id) as total_tasks,
                        COUNT(rt.id) FILTER (WHERE rt.status = 'done') as total_done,
                        COUNT(rt.id) FILTER (WHERE rt.status = 'in_progress') as total_in_progress,
                        COUNT(rt.id) FILTER (WHERE rt.status = 'planned') as total_planned
                    FROM eng_it.roadmap_blocks rb
                    LEFT JOIN eng_it.roadmap_tasks rt ON rt.block_id = rb.id
                """)
                stats = dict(cur.fetchone())
                
                # Вычисляем общий % выполнения
                if stats['total_tasks'] > 0:
                    stats['overall_completion'] = round(
                        (stats['total_done'] / stats['total_tasks']) * 100, 2
                    )
                else:
                    stats['overall_completion'] = 0.0
                
                return {
                    'blocks': blocks,
                    **stats
                }
        finally:
            conn.close()
    
    # ================================================================
    # SYNC (YAML Generation)
    # ================================================================
    
    def sync_to_yaml(self) -> Tuple[bool, Dict[str, str]]:
        """Генерация YAML из БД"""
        try:
            blocks = self.get_blocks(limit=1000)
            tasks_by_block = {}
            
            # Группируем задачи по блокам
            for block in blocks:
                tasks = self.get_tasks(block_code=block['code'], limit=1000)
                tasks_by_block[block['code']] = tasks
            
            # Генерация YAML структуры
            yaml_data = {
                'meta': {
                    'version': '2.0',
                    'system': 'Engineers_IT',
                    'generated_at': datetime.utcnow().isoformat() + 'Z',
                    'generated_by': 'api_sync',
                    'source': 'PostgreSQL eng_it schema'
                },
                'statistics': {
                    'total_blocks': len(blocks),
                    'total_tasks': sum(len(tasks) for tasks in tasks_by_block.values())
                },
                'blocks': []
            }
            
            # Формируем блоки
            for block in blocks:
                block_data = {
                    'code': block['code'],
                    'title': block['title'],
                    'stage': block['stage'],
                    'kind': block['kind'],
                    'status': block['status'],
                    'priority': block['priority'],
                    'description': block.get('description'),
                    'tasks': []
                }
                
                # Добавляем задачи блока
                for task in tasks_by_block.get(block['code'], []):
                    task_data = {
                        'id': task['id'],
                        'code': task['code'],
                        'title': task['title'],
                        'status': task['status']
                    }
                    block_data['tasks'].append(task_data)
                
                yaml_data['blocks'].append(block_data)
            
            # Сохранение YAML
            yaml_path = '/app/ROADMAP/ROADMAP_SYNC_AUTO.yaml'
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, allow_unicode=True, sort_keys=False)
            
            return True, {'yaml': yaml_path}
        except Exception as e:
            return False, {'error': str(e)}
