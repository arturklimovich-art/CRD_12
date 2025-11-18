"""
Bot v2 R7: Roadmap Navigator Command
Вызывает Navigator JSON API и форматирует ответ для Telegram
"""
import httpx
import os
from telegram import Update
from telegram.ext import ContextTypes

ENGINEER_B_API_URL = os.getenv("ENGINEER_B_API_URL", "http://engineer_b_api:8000")

async def roadmap_navigator_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /roadmap-navigator - показывает Navigator JSON API данные"""
    await update.message.reply_text("🔍 Загружаю данные Navigator...")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Запрос к /api/roadmap
            resp = await client.get(f"{ENGINEER_B_API_URL}/api/roadmap")
            if resp.status_code != 200:
                await update.message.reply_text(f"❌ Ошибка API roadmap: {resp.status_code}")
                return
            roadmap_data = resp.json()
            
            # Запрос к /api/truth/matrix
            resp = await client.get(f"{ENGINEER_B_API_URL}/api/truth/matrix")
            if resp.status_code != 200:
                await update.message.reply_text(f"❌ Ошибка API truth/matrix: {resp.status_code}")
                return
            truth_data = resp.json()
        
        # Форматирование ответа
        total = roadmap_data.get("total_tasks", 0)
        tasks = roadmap_data.get("tasks", [])
        
        # Статистика по статусам
        status_counts = {}
        for task in tasks:
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Форматированный текст
        response = f"📊 Navigator Roadmap Status\n\n"
        response += f"📦 Всего задач: {total}\n\n"
        response += f"📈 Статистика:\n"
        
        for status, count in sorted(status_counts.items()):
            emoji = {
                "planned": "📋",
                "in_progress": "🔧",
                "testing": "🧪",
                "completed": "✅",
                "blocked": "🚫"
            }.get(status, "❓")
            response += f"{emoji} {status}: {count}\n"
        
        response += f"\n🎯 Truth Matrix: {truth_data.get('status', 'unknown')}"
        response += f"\n⏰ Timestamp: {truth_data.get('timestamp', 'N/A')}"
        
        # Топ-3 задачи (по приоритету)
        top_tasks = sorted(tasks, key=lambda x: x.get("priority", 0), reverse=True)[:3]
        if top_tasks:
            response += "\n\n🔝 Топ-3 задачи:\n"
            for task in top_tasks:
                code = task.get("code", "?")
                title = task.get("title", "No title")
                status = task.get("status", "unknown")
                title_safe = title[:40].replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
                response += f"• {code} {title_safe}... ({status})\n"
        
        await update.message.reply_text(response)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")
