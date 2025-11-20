# agents/bot/commands/roadmap_generate_tz.py
"""
Roadmap-GenerateTZ: Generate TZ for Engineer_B from ROADMAP task

Features:
- Read task from eng_it.roadmap_tasks by code (e.g., E1-02)
- Generate comprehensive TZ (title, description, acceptance criteria, rollback, trace_id)
- Create task in eng_it.tasks + job_queue
- Emit event: bot.tz.generated
"""

import sys
import os
import uuid
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
    print("ERROR: psycopg2 not available")
    sys.exit(1)

def send_event(event_type, payload):
    """Send event or fallback to print"""
    if EVENTS_AVAILABLE:
        send_system_event(event_type, payload, source="bot_generate_tz")
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

def fetch_roadmap_task(task_code):
    """Fetch roadmap task by code"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT id, code, title, status, description, steps, mechanisms, artifacts, tz_ref
            FROM eng_it.roadmap_tasks
            WHERE code = %s
        """, (task_code,))
        
        row = cur.fetchone()
        if not row:
            return None
        
        return {
            'id': row[0],
            'code': row[1],
            'title': row[2],
            'status': row[3],
            'description': row[4],
            'steps': row[5],
            'mechanisms': row[6],
            'artifacts': row[7],
            'tz_ref': row[8]
        }
    finally:
        cur.close()
        conn.close()

def generate_tz_content(roadmap_task):
    """Generate TZ content from roadmap task"""
    task_id = str(uuid.uuid4())
    trace_id = f"roadmap-{roadmap_task['code']}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
    
    # Build TZ content
    tz_content = {
        "task_id": task_id,
        "trace_id": trace_id,
        "roadmap_task_id": roadmap_task['id'],
        "roadmap_code": roadmap_task['code'],
        "title": roadmap_task['title'],
        "description": roadmap_task['description'] or "No description provided",
        "status": "planned",
        "priority": 100,
        "acceptance_criteria": [
            f"Task {roadmap_task['code']} implementation complete",
            "All tests passing",
            "Code reviewed and approved",
            "Documentation updated"
        ],
        "rollback_plan": [
            "Revert commit if tests fail",
            "Restore previous version from backup",
            "Notify team of rollback"
        ],
        "steps": roadmap_task['steps'] if roadmap_task['steps'] else [],
        "mechanisms": roadmap_task['mechanisms'] if roadmap_task['mechanisms'] else [],
        "artifacts": roadmap_task['artifacts'] if roadmap_task['artifacts'] else [],
        "tz_ref": roadmap_task['tz_ref'],
        "created_at": datetime.utcnow().isoformat(),
        "executor": "Engineer_B"
    }
    
    return task_id, tz_content

def create_task_and_queue(task_id, tz_content):
    """Create task in eng_it.tasks and job_queue"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Insert into eng_it.tasks
        cur.execute("""
            INSERT INTO eng_it.tasks (id, title, status, roadmap_task_id, priority)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, (
            task_id,
            tz_content['title'],
            'planned',
            tz_content['roadmap_task_id'],
            tz_content['priority']
        ))
        
        # Insert into job_queue
        cur.execute("""
            INSERT INTO eng_it.job_queue (task_id, job_type, payload, status) VALUES (%s, %s, %s, 'queued')
            RETURNING id
        """, (task_id, 'roadmap_tz', Json(tz_content)))
        
        queue_id = cur.fetchone()[0]
        
        conn.commit()
        return queue_id
    
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

def roadmap_generate_tz(task_code):
    """Main entry point for Roadmap-GenerateTZ"""
    print(f"=== Roadmap-GenerateTZ v1.0 ===\n")
    print(f"Task code: {task_code}\n")
    
    try:
        # Fetch roadmap task
        print(f"Fetching roadmap task {task_code}...")
        roadmap_task = fetch_roadmap_task(task_code)
        
        if not roadmap_task:
            print(f"❌ Task {task_code} not found in roadmap_tasks")
            return False
        
        print(f"✅ Found task: {roadmap_task['title']}")
        print(f"   Status: {roadmap_task['status']}")
        print(f"   Description: {roadmap_task['description'][:100] if roadmap_task['description'] else 'N/A'}...")
        
        # Generate TZ
        print(f"\nGenerating TZ content...")
        task_id, tz_content = generate_tz_content(roadmap_task)
        print(f"✅ TZ generated")
        print(f"   Task ID: {task_id}")
        print(f"   Trace ID: {tz_content['trace_id']}")
        
        # Create task and queue
        print(f"\nCreating task and queuing for Engineer_B...")
        queue_id = create_task_and_queue(task_id, tz_content)
        print(f"✅ Task created and queued")
        print(f"   Queue ID: {queue_id}")
        
        # Send event
        send_event("bot.tz.generated", {
            "task_id": task_id,
            "roadmap_code": task_code,
            "roadmap_task_id": roadmap_task['id'],
            "trace_id": tz_content['trace_id'],
            "queue_id": queue_id,
            "executor": "Engineer_B",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        print(f"\n✅ TZ generated successfully for {task_code}!")
        print(f"   Engineer_B can now execute task {task_id}")
        return True
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ TZ generation failed: {error_msg}")
        send_event("bot.tz.generation_failed", {
            "task_code": task_code,
            "error": error_msg,
            "timestamp": datetime.utcnow().isoformat()
        })
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python roadmap_generate_tz.py <task_code>")
        sys.exit(1)
    
    task_code = sys.argv[1]
    success = roadmap_generate_tz(task_code)
    sys.exit(0 if success else 1)

