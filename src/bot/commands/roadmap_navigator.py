# src/bot/commands/roadmap_navigator.py
"""
Команда /roadmap-navigator для отображения текущей задачи и её шагов
Использует новый API /api/current и /api/navigator/steps
"""

import httpx
from telegram import Update
from telegram.ext import ContextTypes
from config import ENGINEER_B_API_URL

async def roadmap_navigator_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /roadmap-navigator - показывает текущую задачу и её шаги"""
    await update.message.reply_text("🧭 Загружаю текущую задачу...")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Запрос к /api/current - получаем текущую задачу
            resp = await client.get(f"{ENGINEER_B_API_URL}/api/current")
            if resp.status_code != 200:
                await update.message.reply_text(f"❌ Ошибка API current: {resp.status_code}")
                return
            current_data = resp.json()
            
            task = current_data.get("task")
            if not task:
                await update.message.reply_text("📭 Нет текущей задачи в работе")
                return
            
            task_id = task['id']
            task_title = task['title']
            task_status = task['status']
            progress_notes = task.get('progress_notes', 'Нет заметок')
            
            # Запрос к /api/navigator/steps/{task_id} - получаем шаги задачи
            resp = await client.get(f"{ENGINEER_B_API_URL}/api/navigator/steps/{task_id}")
            if resp.status_code != 200:
                await update.message.reply_text(f"❌ Ошибка API steps: {resp.status_code}")
                return
            steps_data = resp.json()
            
            steps = steps_data.get("steps", [])
            steps_count = steps_data.get("steps_count", 0)

        # Форматирование ответа
        response = f"🧭 *CURRENT TASK*\n\n"
        response += f"📌 *ID:* `{task_id}`\n"
        response += f"📋 *Title:* {task_title}\n"
        response += f"🔧 *Status:* `{task_status}`\n"
        response += f"📝 *Notes:* {progress_notes[:200]}...\n\n"
        
        response += f"📊 *STEPS: {steps_count}*\n\n"
        
        if steps_count > 0:
            done_count = sum(1 for s in steps if s.get('done') or s.get('status') == 'done')
            completion = round((done_count / steps_count * 100) if steps_count > 0 else 0, 1)
            
            response += f"✅ Done: {done_count}\n"
            response += f"📈 Progress: {completion}%\n\n"
            response += f"*Steps List:*\n"
            
            for i, step in enumerate(steps[:10], 1):  # Показываем первые 10 шагов
                status_icon = "✅" if (step.get('done') or step.get('status') == 'done') else "⏳"
                code = step.get('code', 'N/A')
                title = step.get('title', 'No title')[:60]
                response += f"{i}. {status_icon} `{code}` {title}\n"
            
            if steps_count > 10:
                response += f"\n... и ещё {steps_count - 10} шагов\n"
        else:
            response += "📭 Шагов нет (steps=[])\n"
        
        response += f"\n🔗 [Open Navigator](http://localhost:8031/navigator)"
        
        await update.message.reply_text(response, parse_mode="Markdown", disable_web_page_preview=True)

    except httpx.RequestError as e:
        await update.message.reply_text(f"❌ Ошибка сети: {str(e)}")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")