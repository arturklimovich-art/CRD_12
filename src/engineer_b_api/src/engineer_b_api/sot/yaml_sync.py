"""
YAML Sync Engine - ?????? ????????????? YAML ? PostgreSQL
??????: E1-B0-T3, E1-B0-T4
?????: arturklimovich-art
????: 2025-11-23 17:48:00 UTC
??????: 2.1 (?????????? ???????????? JSON)
"""
import hashlib
import yaml
import json
import psycopg2
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

class YAMLSyncEngine:
    """?????? ????????????? YAML roadmap ? PostgreSQL"""
    
    def __init__(self, db_dsn: str, workspace_root: Path):
        self.db_dsn = db_dsn
        self.workspace_root = workspace_root
        self.conn = psycopg2.connect(db_dsn)
        self.conn.autocommit = False
    
    def close(self):
        """??????? ?????????? ? ??"""
        if self.conn:
            self.conn.close()
    
    def _compute_hash(self, data: dict) -> str:
        """????????? SHA256 ??? ?? ???????"""
        yaml_str = yaml.dump(data, sort_keys=True, allow_unicode=True)
        return hashlib.sha256(yaml_str.encode('utf-8')).hexdigest()
    
    def sync_core_catalog(self) -> Dict[str, Any]:
        """?????????????? Core-??????? ???????"""
        core_path = self.workspace_root / "ROADMAP" / "GENERAL_PLAN.yaml"
        
        if not core_path.exists():
            return {"status": "error", "error": f"Core catalog not found: {core_path}"}
        
        try:
            with open(core_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            content_hash = self._compute_hash(data)
            
            cur = self.conn.cursor()
            cur.execute("""
                SELECT content_hash FROM eng_it.sot_sync 
                WHERE domain_code IS NULL AND sync_type = 'snapshot'
                ORDER BY last_synced DESC LIMIT 1
            """)
            row = cur.fetchone()
            last_hash = row[0] if row else None
            
            changes = []
            domains_synced = 0
            
            if last_hash == content_hash:
                changes.append("No changes detected (hash match)")
            else:
                domains = data.get('domains', [])
                for domain in domains:
                    self._upsert_domain(domain)
                    changes.append(f"Updated domain: {domain['code']}")
                    domains_synced += 1
                
                cur.execute("""
                    INSERT INTO eng_it.sot_sync (domain_code, sync_type, status, content_hash)
                    VALUES (NULL, 'snapshot', 'success', %s)
                """, (content_hash,))
                
                self.conn.commit()
            
            cur.close()
            
            return {
                "status": "success",
                "domains_synced": domains_synced,
                "changes": changes,
                "hash": content_hash
            }
            
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "error": str(e)}
    
    def sync_domain_roadmap(self, domain_code: str) -> Dict[str, Any]:
        """?????????????? roadmap ??????????? ?????? (blocks, tasks, steps)"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT plan_path FROM eng_it.sot_domains 
            WHERE code = %s
        """, (domain_code,))
        row = cur.fetchone()
        
        if not row:
            return {"status": "error", "error": f"Domain {domain_code} not found in DB"}
        
        plan_path = self.workspace_root / row[0]
        
        if not plan_path.exists():
            return {"status": "error", "error": f"Roadmap file not found: {plan_path}"}
        
        try:
            with open(plan_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            content_hash = self._compute_hash(data)
            
            cur.execute("""
                SELECT content_hash FROM eng_it.sot_sync 
                WHERE domain_code = %s AND sync_type = 'roadmap'
                ORDER BY last_synced DESC LIMIT 1
            """, (domain_code,))
            row = cur.fetchone()
            last_hash = row[0] if row else None
            
            changes = []
            stats = {"blocks": 0, "tasks": 0, "steps": 0}
            
            if last_hash == content_hash:
                changes.append("No changes detected (hash match)")
            else:
                blocks = data.get('blocks', [])
                for block in blocks:
                    block_pk = self._upsert_block(domain_code, block)
                    changes.append(f"Updated block: {block['id']}")
                    stats["blocks"] += 1
                    
                    tasks = block.get('tasks', [])
                    for task in tasks:
                        task_pk = self._upsert_task(block_pk, domain_code, task)
                        changes.append(f"  Updated task: {task['id']}")
                        stats["tasks"] += 1
                        
                        steps = task.get('steps', [])
                        for step in steps:
                            self._upsert_step(task_pk, domain_code, step)
                            changes.append(f"    Updated step: {step['id']}")
                            stats["steps"] += 1
                
                cur.execute("""
                    INSERT INTO eng_it.sot_sync (domain_code, sync_type, status, content_hash)
                    VALUES (%s, 'roadmap', 'success', %s)
                """, (domain_code, content_hash))
                
                self.conn.commit()
            
            cur.close()
            
            return {
                "status": "success",
                "domain": domain_code,
                "stats": stats,
                "changes": changes,
                "hash": content_hash
            }
            
        except Exception as e:
            self.conn.rollback()
            return {"status": "error", "error": str(e)}
    
    def _upsert_domain(self, domain: dict):
        """??????? ??? ????????? ????? ? sot_domains"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO eng_it.sot_domains (code, title, owner, api_base, plan_path, status, meta)
            VALUES (%(code)s, %(title)s, %(owner)s, %(api_base)s, %(plan_path)s, %(status)s, %(meta)s::jsonb)
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                owner = EXCLUDED.owner,
                api_base = EXCLUDED.api_base,
                plan_path = EXCLUDED.plan_path,
                status = EXCLUDED.status,
                meta = EXCLUDED.meta,
                updated_at = NOW()
        """, domain)
        cur.close()
    
    def _upsert_block(self, domain_code: str, block: dict) -> int:
        """??????? ??? ????????? ???? ? roadmap_blocks"""
        cur = self.conn.cursor()
        
        block_id = block['id']
        stage = block_id
        kind = block_id[0] if block_id else "B"
        
        cur.execute("""
            INSERT INTO eng_it.roadmap_blocks (
                domain_code, code, title, description, status, priority, 
                stage, kind, meta
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb
            )
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                priority = EXCLUDED.priority,
                stage = EXCLUDED.stage,
                kind = EXCLUDED.kind,
                meta = EXCLUDED.meta,
                updated_at = NOW()
            RETURNING id
        """, (
            domain_code,
            block_id,
            block.get('title'),
            block.get('description'),
            self._map_status(block.get('status', 'planned')),
            self._priority_to_int(block.get('priority', 'medium')),
            stage,
            kind,
            json.dumps(block)  # ? ??????????: json.dumps ?????? yaml.dump
        ))
        block_pk = cur.fetchone()[0]
        cur.close()
        return block_pk
    
    def _upsert_task(self, block_pk: int, domain_code: str, task: dict) -> int:
        """??????? ??? ????????? ?????? ? roadmap_tasks"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO eng_it.roadmap_tasks (
                block_id, domain_code, code, title, description, status, priority,
                kind, artifacts, meta, completed_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s
            )
            ON CONFLICT (code) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                priority = EXCLUDED.priority,
                kind = EXCLUDED.kind,
                artifacts = EXCLUDED.artifacts,
                meta = EXCLUDED.meta,
                completed_at = EXCLUDED.completed_at,
                updated_at = NOW()
            RETURNING id
        """, (
            block_pk,
            domain_code,
            task['id'],
            task.get('title'),
            task.get('description'),
            self._map_status(task.get('status', 'planned')),
            self._priority_to_int(task.get('priority', 'medium')),
            'task',
            json.dumps(task.get('artifacts', [])),  # ? ??????????
            json.dumps(task),  # ? ??????????
            task.get('completed_at')
        ))
        task_pk = cur.fetchone()[0]
        cur.close()
        return task_pk
    
    def _upsert_step(self, task_pk: int, domain_code: str, step: dict):
        """??????? ??? ????????? ??? ? roadmap_steps"""
        cur = self.conn.cursor()
        cur.execute("""
            INSERT INTO eng_it.roadmap_steps (
                task_id, domain_code, code, title, description, status, priority,
                meta, completed_at
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s
            )
            ON CONFLICT (task_id, code) DO UPDATE SET
                title = EXCLUDED.title,
                description = EXCLUDED.description,
                status = EXCLUDED.status,
                priority = EXCLUDED.priority,
                meta = EXCLUDED.meta,
                completed_at = EXCLUDED.completed_at,
                updated_at = NOW()
        """, (
            task_pk,
            domain_code,
            step['id'],
            step.get('title'),
            step.get('description'),
            self._map_status(step.get('status', 'planned')),
            self._priority_to_int(step.get('priority', 'medium')),
            json.dumps(step),  # ? ??????????
            step.get('completed_at')
        ))
        cur.close()
    
    def _priority_to_int(self, priority_str: str) -> int:
        """??????????? ????????? ????????? ? ?????"""
        mapping = {
            'critical': 1,
            'high': 50,
            'medium': 100,
            'low': 150
        }
        return mapping.get(priority_str, 100)
    
    def _map_status(self, status_str: str) -> str:
        """??????? ???????? YAML ? ??"""
        mapping = {
            'completed': 'done',
            'in-progress': 'in_progress',
            'in progress': 'in_progress'
        }
        return mapping.get(status_str, status_str)

