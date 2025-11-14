from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import psycopg2
import uvicorn
from datetime import datetime

app = FastAPI(title="Engineers_IT Roadmap", version="2.0")

def get_db_connection():
    conn = psycopg2.connect("postgres://crd_user:crd12@crd12_pgvector:5432/crd12")
    # Устанавливаем кодировку UTF-8 для соединения
    conn.set_client_encoding('UTF8')
    return conn

@app.get("/", response_class=HTMLResponse)
async def beautiful_roadmap():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, status, progress_notes, created_at, updated_at 
            FROM eng_it.tasks 
            ORDER BY 
                CASE status 
                    WHEN 'in_progress' THEN 1
                    WHEN 'planned' THEN 2
                    WHEN 'done' THEN 3
                    ELSE 4
                END,
                created_at DESC
        """)
        
        tasks = []
        for row in cur.fetchall():
            # Обеспечиваем правильную обработку русских символов
            task_id = str(row[0]) if row[0] else ""
            task_title = str(row[1]) if row[1] else ""
            task_status = str(row[2]) if row[2] else "planned"
            task_notes = str(row[3]) if row[3] else ""
            
            tasks.append({
                'id': task_id,
                'title': task_title,
                'status': task_status,
                'notes': task_notes,
                'created': row[4],
                'updated': row[5]
            })
        
        # Генерация HTML с правильной кодировкой
        html = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧭 Engineers_IT Roadmap</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
        }
        .stat-item {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
        }
        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
        }
        .tasks-container {
            padding: 30px;
        }
        .task-columns {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
        }
        .column {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
        }
        .column-title {
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .in-progress .column-title { color: #e67e22; border-color: #e67e22; }
        .planned .column-title { color: #95a5a6; border-color: #95a5a6; }
        .done .column-title { color: #27ae60; border-color: #27ae60; }
        .task-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            border-left: 4px solid;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .task-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        .in-progress .task-card { border-left-color: #e67e22; }
        .planned .task-card { border-left-color: #95a5a6; }
        .done .task-card { border-left-color: #27ae60; }
        .task-id {
            font-weight: bold;
            color: #2c3e50;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .task-title {
            font-size: 1.1em;
            font-weight: 600;
            margin-bottom: 10px;
            color: #2c3e50;
            line-height: 1.4;
        }
        .task-notes {
            color: #6c757d;
            font-size: 0.9em;
            line-height: 1.4;
            margin-bottom: 10px;
        }
        .task-meta {
            display: flex;
            justify-content: space-between;
            font-size: 0.8em;
            color: #95a5a6;
        }
        .status-badge {
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-in_progress { background: #fff3cd; color: #856404; }
        .status-planned { background: #e2e3e5; color: #383d41; }
        .status-done { background: #d4edda; color: #155724; }
        .last-update {
            font-size: 0.8em;
            color: #95a5a6;
            text-align: center;
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧭 Engineers_IT Roadmap</h1>
            <p>Самообучающаяся система разработки с автоматическим деплоем</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">''' + str(len([t for t in tasks if t['status'] == 'in_progress'])) + '''</div>
                <div class="stat-label">В работе</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">''' + str(len([t for t in tasks if t['status'] == 'planned'])) + '''</div>
                <div class="stat-label">Запланировано</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">''' + str(len([t for t in tasks if t['status'] == 'done'])) + '''</div>
                <div class="stat-label">Выполнено</div>
            </div>
        </div>
        
        <div class="tasks-container">
            <div class="task-columns">
                <div class="column in-progress">
                    <div class="column-title">🔄 В работе</div>
        '''
        
        # Задачи в работе
        in_progress_tasks = [t for t in tasks if t['status'] == 'in_progress']
        for task in in_progress_tasks:
            html += f'''
                    <div class="task-card">
                        <div class="task-id">{task['id']}</div>
                        <div class="task-title">{task['title']}</div>
                        <div class="task-notes">{task['notes']}</div>
                        <div class="task-meta">
                            <span class="status-badge status-in_progress">В работе</span>
                            <span>{task['created'].strftime("%d.%m.%Y") if task['created'] else ""}</span>
                        </div>
                    </div>
            '''
        
        html += '''
                </div>
                
                <div class="column planned">
                    <div class="column-title">📋 Запланировано</div>
        '''
        
        # Запланированные задачи
        planned_tasks = [t for t in tasks if t['status'] == 'planned']
        for task in planned_tasks:
            html += f'''
                    <div class="task-card">
                        <div class="task-id">{task['id']}</div>
                        <div class="task-title">{task['title']}</div>
                        <div class="task-notes">{task['notes']}</div>
                        <div class="task-meta">
                            <span class="status-badge status-planned">Запланировано</span>
                            <span>{task['created'].strftime("%d.%m.%Y") if task['created'] else ""}</span>
                        </div>
                    </div>
            '''
        
        html += '''
                </div>
                
                <div class="column done">
                    <div class="column-title">✅ Выполнено</div>
        '''
        
        # Выполненные задачи
        done_tasks = [t for t in tasks if t['status'] == 'done']
        for task in done_tasks[:10]:
            html += f'''
                    <div class="task-card">
                        <div class="task-id">{task['id']}</div>
                        <div class="task-title">{task['title']}</div>
                        <div class="task-notes">{task['notes']}</div>
                        <div class="task-meta">
                            <span class="status-badge status-done">Выполнено</span>
                            <span>{task['created'].strftime("%d.%m.%Y") if task['created'] else ""}</span>
                        </div>
                    </div>
            '''
        
        html += f'''
                </div>
            </div>
            <div class="last-update">
                Последнее обновление: {datetime.now().strftime("%d.%m.%Y %H:%M")} | Всего задач: {len(tasks)}
            </div>
        </div>
    </div>
</body>
</html>'''
        
        return HTMLResponse(content=html)
        
    except Exception as e:
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>{str(e)}</p>", status_code=500)
    finally:
        conn.close()

if __name__ == "__main__":
    print("🚀 Запуск Roadmap с исправленной кодировкой...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
