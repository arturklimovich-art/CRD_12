from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import psycopg2
import uvicorn

app = FastAPI()

def get_db_connection():
    return psycopg2.connect("postgres://crd_user:crd12@crd12_pgvector:5432/crd12")

@app.get("/", response_class=HTMLResponse)
async def roadmap_html():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, status, progress_notes, created_at 
            FROM eng_it.tasks 
            ORDER BY created_at DESC
        """)
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Engineers_IT Roadmap</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
                .task { background: #f8f9fa; margin: 10px 0; padding: 15px; border-left: 4px solid #3498db; border-radius: 5px; }
                .task.done { border-left-color: #27ae60; }
                .task.in_progress { border-left-color: #f39c12; }
                .task.planned { border-left-color: #95a5a6; }
                .task-id { font-weight: bold; color: #2c3e50; }
                .task-status { float: right; padding: 2px 8px; border-radius: 3px; font-size: 12px; }
                .status-done { background: #d4edda; color: #155724; }
                .status-in_progress { background: #fff3cd; color: #856404; }
                .status-planned { background: #e2e3e5; color: #383d41; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧭 Engineers_IT Roadmap</h1>
                    <p>Система разработки с автоматическим деплоем</p>
                </div>
        """
        
        for task in cur.fetchall():
            task_id, title, status, notes, created = task
            status_class = f"status-{status}" if status else "status-planned"
            
            html += f"""
                <div class="task {status}">
                    <div class="task-id">{task_id}</div>
                    <span class="task-status {status_class}">{status or 'planned'}</span>
                    <div class="task-title" style="font-size: 16px; margin: 5px 0;"><strong>{title}</strong></div>
                    {f'<div class="task-notes" style="color: #666; font-size: 14px;">{notes}</div>' if notes else ''}
                    <div class="task-date" style="font-size: 12px; color: #999;">Создана: {created.strftime("%Y-%m-%d %H:%M") if created else "N/A"}</div>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>"
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
