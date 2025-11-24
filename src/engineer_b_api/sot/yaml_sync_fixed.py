"""
Модуль синхронизации YAML ↔ PostgreSQL для федеративной системы SoT
Задача: E1-B0-T3-S1
Автор: arturklimovich-art
Дата: 2025-11-23 16:50:49 UTC
"""

import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor, Json


class YAMLSyncEngine:
    """
    Синхронизация YAML-файлов Roadmap с PostgreSQL БД
    """
    
    def __init__(self, db_dsn: str, repo_root: Path):
        self.db_dsn = db_dsn
        self.repo_root = Path(repo_root)
        self.conn = None
    
    def connect(self):
        """Подключение к БД"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.db_dsn, cursor_factory=RealDictCursor)
    
    def close(self):
        """Закрытие подключения"""
        if self.conn and not self.conn.closed:
            self.conn.close()
    
    def _compute_hash(self, file_path: Path) -> str:
        """SHA256 хэш файла"""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _get_last_sync(self, domain_code: Optional[str], sync_type: str) -> Optional[Dict]:
        """Получить последнюю запись синхронизации"""
        self.connect()
        with self.conn.cursor() as cur:
            if domain_code:
                cur.execute(
                    """
                    SELECT * FROM eng_it.sot_sync 
                    WHERE domain_code = %s AND sync_type = %s 
                    ORDER BY last_synced DESC LIMIT 1
                    """,
                    (domain_code, sync_type)
                )
            else:
                cur.execute(
                    """
                    SELECT * FROM eng_it.sot_sync 
                    WHERE domain_code IS NULL AND sync_type = %s 
                    ORDER BY last_synced DESC LIMIT 1
                    """,
                    (sync_type,)
                )
            return cur.fetchone()
    
    def _save_sync_record(self, domain_code: Optional[str], sync_type: str, 
                          file_hash: str, status: str, changes: List[str], 
                          error_msg: Optional[str] = None):
        """Сохранить запись о синхронизации"""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO eng_it.sot_sync 
                (domain_code, sync_type, last_hash, status, diff_json, error_msg, meta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    domain_code,
                    sync_type,
                    file_hash,
                    status,
                    Json({'changes': changes}),
                    error_msg,
                    Json({'timestamp': datetime.utcnow().isoformat()})
                )
            )
        self.conn.commit()
    
    def _get_domain(self, code: str) -> Optional[Dict]:
        """Получить домен по коду"""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM eng_it.sot_domains WHERE code = %s""",
                (code,)
            )
            return cur.fetchone()
    
    def _upsert_domain(self, domain: Dict):
        """Создать или обновить домен"""
        self.connect()
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO eng_it.sot_domains 
                (code, title, owner, api_base, plan_path, status, meta)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (code) DO UPDATE SET
                    title = EXCLUDED.title,
                    owner = EXCLUDED.owner,
                    api_base = EXCLUDED.api_base,
                    plan_path = EXCLUDED.plan_path,
                    status = EXCLUDED.status,
                    meta = EXCLUDED.meta,
                    updated_at = now()
                """,
                (
                    domain['code'],
                    domain['title'],
                    domain.get('owner', 'unknown'),
                    domain.get('api_base', 'http://localhost:8000'),
                    domain['plan_path'],
                    domain.get('status', 'active'),
                    Json(domain.get('meta', {}))
                )
            )
        self.conn.commit()
    
    def sync_core_catalog(self) -> Dict:
        """
        Синхронизация ROADMAP/GENERAL_PLAN.yaml → sot_domains
        
        Returns:
            {
                'status': 'success|error',
                'domains_synced': int,
                'changes': List[str],
                'error': Optional[str]
            }
        """
        yaml_path = self.repo_root / 'ROADMAP' / 'GENERAL_PLAN.yaml'
        
        if not yaml_path.exists():
            return {
                'status': 'error',
                'error': f'File not found: {yaml_path}',
                'domains_synced': 0,
                'changes': []
            }
        
        try:
            # 1. Вычисляем hash файла
            file_hash = self._compute_hash(yaml_path)
            
            # 2. Проверяем, нужна ли синхронизация
            last_sync = self._get_last_sync(None, 'yaml_to_db')
            if last_sync and last_sync.get('last_hash') == file_hash:
                return {
                    'status': 'success',
                    'domains_synced': 0,
                    'changes': ['No changes detected (hash match)']
                }
            
            # 3. Парсим YAML
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            changes = []
            
            # 4. Синхронизируем домены
            for domain in data.get('domains', []):
                existing = self._get_domain(domain['code'])
                
                if not existing:
                    self._upsert_domain(domain)
                    changes.append(f\"Created domain: {domain['code']}\")
                else:
                    self._upsert_domain(domain)
                    changes.append(f\"Updated domain: {domain['code']}\")
            
            # 5. Сохраняем запись о синхронизации
            self._save_sync_record(None, 'yaml_to_db', file_hash, 'success', changes)
            
            return {
                'status': 'success',
                'domains_synced': len(data.get('domains', [])),
                'changes': changes,
                'file_hash': file_hash
            }
        
        except Exception as e:
            error_msg = f\"Sync error: {str(e)}\"
            self._save_sync_record(None, 'yaml_to_db', '', 'error', [], error_msg)
            return {
                'status': 'error',
                'error': error_msg,
                'domains_synced': 0,
                'changes': []
            }
    
    def sync_domain_roadmap(self, domain_code: str) -> Dict:
        """
        Синхронизация ROADMAP/DOMAINS/{domain_code}/GENERAL_PLAN.yaml → roadmap_*
        
        ПРИМЕЧАНИЕ: Полная реализация парсинга blocks → tasks → steps 
        будет добавлена после тестирования базовой синхронизации.
        
        Сейчас только проверяем существование файла и домена.
        """
        # 1. Проверяем существование домена
        domain = self._get_domain(domain_code)
        if not domain:
            return {
                'status': 'error',
                'error': f\"Domain {domain_code} not found in sot_domains\"
            }
        
        # 2. Путь к YAML домена
        yaml_path = self.repo_root / domain['plan_path']
        
        if not yaml_path.exists():
            return {
                'status': 'error',
                'error': f\"File not found: {yaml_path}\"
            }
        
        try:
            file_hash = self._compute_hash(yaml_path)
            
            # Проверка на изменения
            last_sync = self._get_last_sync(domain_code, 'yaml_to_db')
            if last_sync and last_sync.get('last_hash') == file_hash:
                return {
                    'status': 'success',
                    'changes': ['No changes detected (hash match)']
                }
            
            # Парсим YAML
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            changes = [f\"Domain {domain_code} YAML validated\"]
            
            # TODO: Реализовать парсинг blocks → tasks → steps
            # Сейчас только регистрируем факт синхронизации
            
            self._save_sync_record(domain_code, 'yaml_to_db', file_hash, 'success', changes)
            
            return {
                'status': 'success',
                'changes': changes,
                'file_hash': file_hash,
                'note': 'Full block/task/step sync will be implemented in next iteration'
            }
        
        except Exception as e:
            error_msg = f\"Sync error: {str(e)}\"
            self._save_sync_record(domain_code, 'yaml_to_db', '', 'error', [], error_msg)
            return {
                'status': 'error',
                'error': error_msg
            }


# Пример использования
if __name__ == '__main__':
    import os
    
    # DSN из переменной окружения или дефолт
    db_dsn = os.getenv(
        'CRD12_DB_DSN',
        'postgresql://crd_user:crd12@localhost:5433/crd12'
    )
    
    repo_root = Path('/app')  # В Docker-контейнере
    # Для локального использования: Path('C:/Users/Artur/Documents/CRD12')
    
    engine = YAMLSyncEngine(db_dsn, repo_root)
    
    # Синхронизация Core-каталога
    result = engine.sync_core_catalog()
    print(f\"Core sync result: {result}\")
    
    # Синхронизация домена TL
    result_tl = engine.sync_domain_roadmap('TL')
    print(f\"TL sync result: {result_tl}\")
    
    engine.close()
