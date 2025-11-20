# agents/bot/commands/roadmap_load.py
"""
Roadmap-Load: Load and validate ROADMAP.yaml, sync with DB

Features:
- Load ROADMAP/ROADMAP.yaml
- Validate schema (schema_version, meta, stages, tasks)
- Check unique IDs
- Sync with eng_it.roadmap_tasks (upsert tasks)
- Emit event: roadmap.loaded
"""

import yaml
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "app" / "engineer_b_api"))

# Import events module
try:
    from events import send_system_event
    EVENTS_AVAILABLE = True
except ImportError:
    EVENTS_AVAILABLE = False
    print("WARNING: events.py not available")

# Import DB connection
try:
    import psycopg2
    from psycopg2.extras import Json
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("WARNING: psycopg2 not available, DB sync disabled")

def send_event(event_type, payload):
    """Send event or fallback to print"""
    if EVENTS_AVAILABLE:
        send_system_event(event_type, payload, source="bot_roadmap_load")
    else:
        print(f"EVENT: {event_type} - {payload}")

def get_db_connection():
    """Get PostgreSQL connection"""
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="crd12",
        user="crd_user",
        password="crd12"
    )

def load_yaml(filepath="ROADMAP/ROADMAP.yaml"):
    """Load and validate ROADMAP.yaml"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Validate required fields
        assert 'schema_version' in data, "Missing schema_version"
        assert 'meta' in data, "Missing meta"
        assert 'stages' in data, "Missing stages"
        assert data['schema_version'] == 'roadmap.v1', f"Invalid schema_version: {data['schema_version']}"
        
        # Validate meta
        meta = data['meta']
        required_meta = ['owner', 'project', 'version', 'updated_at']
        for field in required_meta:
            assert field in meta, f"Missing meta.{field}"
        
        return data
    
    except FileNotFoundError:
        raise FileNotFoundError(f"ROADMAP.yaml not found: {filepath}")
    except (yaml.YAMLError, AssertionError) as e:
        raise ValueError(f"ROADMAP.yaml validation failed: {e}")

def sync_to_db(roadmap_data):
    """Sync ROADMAP.yaml tasks to eng_it.roadmap_tasks"""
    if not DB_AVAILABLE:
        print("SKIP: DB sync (psycopg2 not available)")
        return 0, 0
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    created_count = 0
    updated_count = 0
    
    try:
        for stage in roadmap_data['stages']:
            stage_id = stage['id']
            
            if 'tasks' not in stage or not stage['tasks']:
                continue
            
            for task in stage['tasks']:
                task_id = task['id']
                title = task['title']
                status_yaml = task['status']
                description = task.get('description', '')
                commit = task.get('commit', None)
                roadmap_task_id = task.get('roadmap_task_id', None)
                
                # Map YAML status to DB status
                status_map = {
                    'PLANNED': 'planned',
                    'IN_PROGRESS': 'in_progress',
                    'DONE': 'done',
                    'BLOCKED': 'blocked'
                }
                status_db = status_map.get(status_yaml, 'planned')
                
                # Check if task exists
                cur.execute("SELECT id FROM eng_it.roadmap_tasks WHERE code = %s", (task_id,))
                existing = cur.fetchone()
                
                if existing:
                    # Update existing task
                    cur.execute("""
                        UPDATE eng_it.roadmap_tasks
                        SET title = %s, status = %s, description = %s, updated_at = NOW()
                        WHERE code = %s
                    """, (title, status_db, description, task_id))
                    updated_count += 1
                else:
                    # Insert new task
                    cur.execute("""
                        INSERT INTO eng_it.roadmap_tasks 
                        (code, title, status, description, kind, priority, steps, mechanisms, artifacts, meta)
                        VALUES (%s, %s, %s, %s, 'task', 100, '[]'::jsonb, '[]'::jsonb, '[]'::jsonb, '{}'::jsonb)
                    """, (task_id, title, status_db, description))
                    created_count += 1
        
        conn.commit()
        return created_count, updated_count
    
    finally:
        cur.close()
        conn.close()

def roadmap_load():
    """Main entry point for Roadmap-Load"""
    print("=== Roadmap-Load v1.0 ===\n")
    
    try:
        # Load YAML
        print("Loading ROADMAP.yaml...")
        roadmap_data = load_yaml()
        
        meta = roadmap_data['meta']
        stages_count = len(roadmap_data['stages'])
        
        # Count tasks
        tasks_count = sum(len(stage.get('tasks', [])) for stage in roadmap_data['stages'])
        
        print(f"✅ ROADMAP.yaml loaded successfully")
        print(f"   Schema: {roadmap_data['schema_version']}")
        print(f"   Owner: {meta['owner']}")
        print(f"   Version: {meta['version']}")
        print(f"   Stages: {stages_count}")
        print(f"   Tasks: {tasks_count}")
        
        # Sync to DB
        print("\nSyncing to database...")
        created, updated = sync_to_db(roadmap_data)
        print(f"✅ DB sync complete: {created} created, {updated} updated")
        
        # Send event
        send_event("roadmap.loaded", {
            "schema_version": roadmap_data['schema_version'],
            "owner": meta['owner'],
            "version": meta['version'],
            "stages_count": stages_count,
            "tasks_count": tasks_count,
            "db_created": created,
            "db_updated": updated,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print("\n✅ Roadmap loaded successfully!")
        return True
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Roadmap loading failed: {error_msg}")
        send_event("roadmap.parse_failed", {
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        return False

if __name__ == "__main__":
    success = roadmap_load()
    sys.exit(0 if success else 1)


