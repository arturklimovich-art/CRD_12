# agents/bot/commands/roadmap_update_status.py
"""
Roadmap-UpdateStatus: Update task status and log to JOURNAL
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src" / "app" / "engineer_b_api"))

try:
    from events import send_system_event
    EVENTS_AVAILABLE = True
except ImportError:
    EVENTS_AVAILABLE = False

try:
    import psycopg2
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("ERROR: psycopg2 not available")
    sys.exit(1)

def send_event(event_type, payload):
    if EVENTS_AVAILABLE:
        send_system_event(event_type, payload, source="bot_update_status")
    else:
        print(f"EVENT: {event_type} - {payload}")

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        port=5433,
        database="crd12",
        user="crd_user",
        password="crd12"
    )

def update_task_status(task_code, new_status, commit_sha=None):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT id, code, title, status FROM eng_it.roadmap_tasks WHERE code = %s", (task_code,))
        row = cur.fetchone()
        if not row:
            return None, f"Task {task_code} not found"
        
        task_id, code, title, old_status = row
        
        if new_status == 'done':
            cur.execute("UPDATE eng_it.roadmap_tasks SET status = %s, completed_at = NOW(), updated_at = NOW() WHERE code = %s", (new_status, task_code))
        else:
            cur.execute("UPDATE eng_it.roadmap_tasks SET status = %s, updated_at = NOW() WHERE code = %s", (new_status, task_code))
        
        conn.commit()
        
        return {
            'task_id': task_id,
            'code': code,
            'title': title,
            'old_status': old_status,
            'new_status': new_status,
            'commit_sha': commit_sha
        }, None
    
    except Exception as e:
        conn.rollback()
        return None, str(e)
    finally:
        cur.close()
        conn.close()

def log_to_journal(task_info):
    try:
        journal_dir = Path("JOURNAL/daily")
        journal_dir.mkdir(parents=True, exist_ok=True)
        
        today = datetime.utcnow().strftime("%Y-%m-%d")
        journal_file = journal_dir / f"{today}.md"
        
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        commit_info = f" (commit: {task_info['commit_sha']})" if task_info['commit_sha'] else ""
        
        log_entry = f"\n## {timestamp}\n\n**Task Status Update**\n\n"
        log_entry += f"- **Code:** {task_info['code']}\n"
        log_entry += f"- **Title:** {task_info['title']}\n"
        log_entry += f"- **Status:** {task_info['old_status']} -> **{task_info['new_status']}**{commit_info}\n\n---\n"
        
        with open(journal_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        return str(journal_file)
    
    except Exception as e:
        print(f"WARNING: Failed to log to JOURNAL: {e}")
        return None

def roadmap_update_status(task_code, new_status, commit_sha=None):
    print(f"=== Roadmap-UpdateStatus v1.0 ===\n")
    print(f"Task: {task_code}, Status: {new_status}")
    if commit_sha:
        print(f"Commit: {commit_sha}")
    print()
    
    try:
        task_info, error = update_task_status(task_code, new_status, commit_sha)
        
        if error:
            print(f"ERROR: {error}")
            return False
        
        print(f"OK: {task_info['old_status']} -> {task_info['new_status']}")
        
        journal_path = log_to_journal(task_info)
        if journal_path:
            print(f"JOURNAL: {journal_path}")
        
        send_event("roadmap.status.updated", {
            "task_id": task_info['task_id'],
            "code": task_info['code'],
            "title": task_info['title'],
            "old_status": task_info['old_status'],
            "new_status": task_info['new_status'],
            "commit_sha": commit_sha,
            "journal_path": journal_path,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print("\nSUCCESS")
        return True
    
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python roadmap_update_status.py <task_code> <new_status> [commit_sha]")
        sys.exit(1)
    
    task_code = sys.argv[1]
    new_status = sys.argv[2]
    commit_sha = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = roadmap_update_status(task_code, new_status, commit_sha)
    sys.exit(0 if success else 1)
