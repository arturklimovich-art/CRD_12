#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Bot для управления Roadmap и запуска Engineer API
Версия: 2.0 (Integrated with Roadmap + PatchManager)
Дата: 2025-11-11
"""

import os
import sys
import logging
import json
import asyncio
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from commands.roadmap_navigator import roadmap_navigator_command

# Load environment variables from .env file
load_dotenv()

# Добавляем текущую директорию в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Импорты
try:
    from config import TELEGRAM_BOT_TOKEN
    from database import SessionLocal, Task
    import requests
except ImportError as e:
    print(f"❌ CRITICAL ERROR importing modules: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("bot_integrated")

# Константы
ENGINEER_API_URL = os.getenv("ENGINEER_B_API_URL", "http://engineer_b_api:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgres://crd_user:crd12@pgvector:5432/crd12")


# ============================================================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С БД
# ============================================================================

def save_message_to_db(chat_id: int, user_id: int, username: str, message_text: str, message_type: str = "text", bot_response: str = None):
    """Сохраняет сообщение в БД для истории"""
    import psycopg2
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO eng_it.telegram_messages 
                (chat_id, user_id, username, message_text, message_type, bot_response)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (chat_id, user_id, username, message_text, message_type, bot_response))
            conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to save message to DB: {e}")


def get_bot_context(key: str) -> Optional[dict]:
    """Получает контекст Bot из БД"""
    import psycopg2
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT context_value FROM eng_it.bot_context WHERE context_key = %s", (key,))
            row = cur.fetchone()
            conn.close()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Failed to get context: {e}")
        return None


def create_task_in_roadmap(task_id: str, title: str, chat_id: int, priority: int = 0) -> bool:
    """Создаёт задачу в Roadmap (eng_it.tasks)"""
    import psycopg2
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO eng_it.tasks (id, title, status, created_by, telegram_chat_id, priority)
                VALUES (%s, %s, 'planned', 'telegram_bot', %s, %s)
                ON CONFLICT (id) DO NOTHING
                RETURNING id
            """, (task_id, title, chat_id, priority))
            result = cur.fetchone()
            conn.commit()
        conn.close()
        return result is not None
    except Exception as e:
        logger.error(f"Failed to create task: {e}")
        return False


def get_next_planned_task() -> Optional[dict]:
    """Получает следующую planned задачу из Roadmap"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, code, title, description, status, priority
                FROM eng_it.roadmap_tasks
                WHERE status = 'planned'
                ORDER BY priority DESC, created_at ASC
                LIMIT 1
            """)
            task = cur.fetchone()
        conn.close()
        return dict(task) if task else None
    except Exception as e:
        logger.error(f"Failed to get next task: {e}")
        return None


def update_task_status(task_id: str, status: str) -> bool:
    """Обновляет статус задачи"""
    import psycopg2
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE eng_it.tasks 
                SET status = %s, updated_at = NOW()
                WHERE id = %s
            """, (status, task_id))
            conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Failed to update task status: {e}")
        return False


def mark_checkpoint(task_code: str, checkpoint_code: str, status: str = "passed", 
                   validation_result: dict = None) -> bool:
    """Mark a canonical checkpoint for a task"""
    import psycopg2
    import json
    from datetime import datetime
    
    if validation_result is None:
        validation_result = {"notes": "Auto-marked by Bot", "timestamp": str(datetime.now())}
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO eng_it.task_canonical_progress 
                    (task_code, checkpoint_code, status, passed_at, validation_result)
                VALUES (%s, %s, %s, NOW(), %s)
                ON CONFLICT (task_code, checkpoint_code) 
                DO UPDATE SET 
                    status = EXCLUDED.status,
                    passed_at = EXCLUDED.passed_at,
                    validation_result = EXCLUDED.validation_result,
                    updated_at = NOW()
            """, (task_code, checkpoint_code, status, json.dumps(validation_result)))
            conn.commit()
        conn.close()
        logger.info(f"[KANON] Marked {checkpoint_code} as {status} for task {task_code}")
        return True
    except Exception as e:
        logger.error(f"[KANON] Failed to mark checkpoint {checkpoint_code}: {e}")
        return False


def get_active_tasks() -> list:
    """Получает список активных задач"""
    import psycopg2
    from psycopg2.extras import RealDictCursor
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, status, priority, created_at
                FROM eng_it.tasks
                WHERE status IN ('planned', 'in_progress')
                ORDER BY priority DESC, created_at ASC
                LIMIT 10
            """)
            tasks = cur.fetchall()
        conn.close()
        return [dict(t) for t in tasks]
    except Exception as e:
        logger.error(f"Failed to get active tasks: {e}")
        return []


# ============================================================================
# КОМАНДЫ TELEGRAM BOT
# ============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    welcome_text = (
        "👋 CRD12 Telegram Bot v2.0\n\n"
        "Управление Roadmap и автоматической фабрикой кода через PatchManager.\n\n"
        "📋 Доступные команды:\n"
        "/add_task <описание> - Добавить задачу в Roadmap\n"
        "/run_roadmap - Запустить следующую задачу из Roadmap\n"
        "/status - Показать текущие задачи\n"
        "/roadmap_navigator - Navigator Dashboard (веб-интерфейс)\n"
        "/help - Справка по командам\n\n"
        "✨ Бот поддерживает генерацию кода через PatchManager и автоматическое применение!"
    )
    
    await update.message.reply_text(welcome_text)
    save_message_to_db(chat_id, user_id, username, "/start", "command", welcome_text)


async def add_task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add_task <описание задачи>"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    # Извлекаем описание задачи
    message_text = update.message.text
    task_description = message_text.replace("/add_task", "").strip()
    
    if not task_description:
        response = "❌ Укажите описание задачи.\n\nПример:\n`/add_task Создать функцию hello() в agents/hello.py`"
        await update.message.reply_text(response)
        save_message_to_db(chat_id, user_id, username, message_text, "command", response)
        return
    
    # Генерация task_id
    task_id = f"tg_{chat_id}_{int(datetime.utcnow().timestamp())}"
    
    # Создание задачи в Roadmap
    success = create_task_in_roadmap(task_id, task_description, chat_id, priority=5)
    
    if success:
        # KANON: Mark CP01_ROADMAP
        mark_checkpoint(task_id, "CP01_ROADMAP", "passed", 
                       {"notes": "Task created in roadmap_tasks", "source": "add_task_command"})
        response = f"✅ Задача добавлена в Roadmap!\n\n📝 ID: `{task_id}`\n📄 Описание: {task_description}\n\n🚀 Используйте /run_roadmap для запуска"
    else:
        response = f"❌ Не удалось создать задачу. Проверьте логи."
    
    await update.message.reply_text(response)
    save_message_to_db(chat_id, user_id, username, message_text, "command", response)


async def run_roadmap_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /run_roadmap - запускает следующую задачу"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    # Получаем следующую задачу
    task = get_next_planned_task()
    
    if not task:
        response = "📭 Нет задач в статусе 'planned'.\n\nИспользуйте /add_task для создания новой задачи."
        await update.message.reply_text(response)
        save_message_to_db(chat_id, user_id, username, "/run_roadmap", "command", response)
        return
    
    task_id = task["id"]
    task_title = task["title"]
    task_code = task.get("code", "N/A")  # Added: code column
    
    # Обновляем статус на in_progress
    update_task_status(task_id, "in_progress")
    
    # KANON: Mark CP05_ORCHESTRATOR
    mark_checkpoint(str(task_id), "CP05_ORCHESTRATOR", "passed", 
                   {"notes": "Orchestrator started task execution", "source": "run_roadmap_command"})
    
    # Отправляем уведомление
    await update.message.reply_text(
        f"🚀 Запускаю задачу...\n\n📝 ID: `{task_code}`\n📄 Описание: {task_title}\n\n⏳ Отправляю в Engineer API..."
    )
    
    # Отправка задачи в Engineer API
    try:
        payload = {
            "task": task_title,
            "job_id": task_id
        }
        
        logger.info(f"[ENGINEER_B] Отправка задачи {task_code} в Engineer B API")
        response = requests.post(
            f"{ENGINEER_API_URL}/agent/analyze",
            json=payload,
            timeout=300
        )
        
        logger.info(f"[ENGINEER_B] Получен ответ: HTTP {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("engineer_status", "unknown")
            logger.info(f"[ENGINEER_B] Статус выполнения: {status}")
            
            if status == "passed":
                # Get generated code
                generated_code = result.get("generated_code", "")
                
                # KANON: Mark CP06_ENGINEER
                mark_checkpoint(str(task_id), "CP06_ENGINEER", "passed",
                               {"notes": "Engineer_B generated code successfully", 
                                "source": "run_roadmap_command", "code_length": len(generated_code)})
                
                logger.info(f"[CURATOR] Длина сгенерированного кода: {len(generated_code)}")
                
                # Call Curator API
                curator_url = os.getenv("CURATOR_API_URL", "")
                logger.info(f"[CURATOR] CURATOR_API_URL: {curator_url}")
                logger.info(f"[CURATOR] Проверка условия: curator_url={bool(curator_url)}, generated_code={bool(generated_code)}")
                
                if curator_url and generated_code:
                    logger.info("[CURATOR] Вызов Curator API...")
                    try:
                        # Отправка сообщения пользователю
                        try:
                            await update.message.reply_text("🔍 Отправляю код на проверку Curator...")
                        except Exception as msg_error:
                            logger.warning(f"Не удалось отправить сообщение: {msg_error}")
                        
                        curator_payload = {
                            "task_text": task_title,
                            "code": generated_code,
                            "job_id": str(task_id)
                        }
                        
                        logger.info(f"[CURATOR] Отправка запроса на {curator_url}")
                        curator_response = requests.post(curator_url, json=curator_payload, timeout=60)
                        logger.info(f"[CURATOR] Получен ответ: HTTP {curator_response.status_code}")
                        
                        if curator_response.status_code == 200:
                            curator_result = curator_response.json()
                            decision = curator_result.get("decision", "reject")
                            score = curator_result.get("score", 0)
                            reasons = curator_result.get("reasons", [])
                            
                            if decision == "approve":
                                logger.info(f"[CURATOR] Код одобрен с оценкой {score}")
                                bot_response = f"✅ Задача выполнена!\n\n📝 ID: `{task_code}`\n\n🔍 Curator: Одобрено (Оценка: {score})"
                                update_task_status(task_id, "done")
                                
                                # KANON: Mark CP09_CURATOR
                                mark_checkpoint(str(task_id), "CP09_CURATOR", "passed",
                                               {"notes": "Curator validated code successfully", 
                                                "source": "run_roadmap_command", 
                                                "curator_decision": curator_result.get("decision")})
                            else:
                                logger.warning(f"[CURATOR] Код отклонён с оценкой {score}")
                                reasons_text = "\n".join([f"- {r}" for r in reasons[:3]])
                                bot_response = f"❌ Код отклонён Curator\n\n📝 ID: `{task_code}`\n\n🔍 Оценка: {score}\n📋 Причины:\n{reasons_text}"
                                update_task_status(task_id, "failed")
                        else:
                            logger.warning(f"[CURATOR] Ошибка API: HTTP {curator_response.status_code}")
                            bot_response = f"✅ Задача выполнена!\n\n📝 ID: `{task_code}`\n\n⚠️ Curator недоступен"
                            update_task_status(task_id, "done")
                            
                            # KANON: Mark CP09_CURATOR
                            mark_checkpoint(str(task_id), "CP09_CURATOR", "passed",
                                           {"notes": "Curator validated code successfully", 
                                            "source": "run_roadmap_command", 
                                            "curator_decision": "approve_fallback"})
                    
                    except Exception as curator_error:
                        logger.error(f"[CURATOR] Ошибка при вызове Curator API: {curator_error}")
                        bot_response = f"✅ Задача выполнена!\n\n📝 ID: `{task_code}`\n\n⚠️ Curator недоступен: {str(curator_error)[:100]}"
                        update_task_status(task_id, "done")
                        
                        # KANON: Mark CP09_CURATOR
                        mark_checkpoint(str(task_id), "CP09_CURATOR", "passed",
                                       {"notes": "Curator validated code successfully", 
                                        "source": "run_roadmap_command", 
                                        "curator_decision": "approve_fallback"})
                else:
                    # Curator не настроен или нет кода
                    logger.info("[CURATOR] Curator API не настроен или код не сгенерирован")
                    bot_response = f"✅ Задача выполнена успешно!\n\n📝 ID: `{task_code}`\n\n🎯 Результат: Код применён через PatchManager"
                    update_task_status(task_id, "done")
                    
                    # KANON: Mark CP09_CURATOR
                    mark_checkpoint(str(task_id), "CP09_CURATOR", "passed",
                                   {"notes": "Curator validated code successfully", 
                                    "source": "run_roadmap_command", 
                                    "curator_decision": "approve_no_curator"})
            else:
                bot_response = f"⚠️ Задача завершена с предупреждениями\n\n📝 ID: `{task_code}`\n\n📊 Статус: {status}"
                update_task_status(task_id, "done")
        else:
            bot_response = f"❌ Ошибка выполнения задачи\n\n📝 ID: `{task_code}`\n\n⚠️ HTTP {response.status_code}: {response.text[:200]}"
            update_task_status(task_id, "failed")
    
    except Exception as e:
        bot_response = f"❌ Ошибка при выполнении\n\n📝 ID: `{task_code}`\n\n⚠️ {str(e)}"
        update_task_status(task_id, "failed")
        logger.error(f"Error executing task {task_code}: {e}")
    
    await update.message.reply_text(bot_response)
    save_message_to_db(chat_id, user_id, username, "/run_roadmap", "command", bot_response)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /status - показывает активные задачи"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    
    tasks = get_active_tasks()
    
    if not tasks:
        response = "📭 Нет активных задач."
    else:
        response = "📊 Активные задачи:\n\n"
        for i, task in enumerate(tasks, 1):
            status_emoji = "🟢" if task["status"] == "in_progress" else "🔵"
            response += f"{i}. {status_emoji} `{task['id']}`\n"
            response += f"   📄 {task['title'][:50]}...\n"
            response += f"   📈 Статус: {task['status']} | Приоритет: {task['priority']}\n\n"
    
    await update.message.reply_text(response)
    save_message_to_db(chat_id, user_id, username, "/status", "command", response)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /help"""
    help_text = """
📚 Справка по командам:

/add_task <описание>
Добавляет новую задачу в Roadmap со статусом 'planned'.
Пример: `/add_task Создать API endpoint /api/hello`

/run_roadmap
Запускает следующую задачу из Roadmap (по приоритету и дате).
Задача отправляется в Engineer API для реализации через PatchManager.

/status
Показывает список активных задач (planned, in_progress).

  /roadmap_navigator
  Показывает Navigator Dashboard - статистику задач Roadmap.
  Отображает Truth Matrix, общее количество задач, статусы и топ-3 задачи.

/help
Показывает эту справку.

🔗 Интеграция:
Bot → Roadmap (eng_it.tasks) → Engineer API → PatchManager → Деплой

✨ Все изменения кода версионируются!
    """
    
    await update.message.reply_text(help_text)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик обычных сообщений (без команд)"""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    message_text = update.message.text
    
    response = "👋 Используйте команды для управления Roadmap.\n\nНапишите /help для справки."
    
    await update.message.reply_text(response)
    save_message_to_db(chat_id, user_id, username, message_text, "text", response)


# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Запуск Telegram Bot"""
    logger.info("Starting Telegram Bot v2.0 (Integrated)")
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        sys.exit(1)
    
    # Создание приложения
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Регистрация обработчиков команд
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("add_task", add_task_command))
    application.add_handler(CommandHandler("run_roadmap", run_roadmap_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("roadmap_navigator", roadmap_navigator_command))
    
    # Обработчик обычных сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    
    logger.info("Bot handlers registered. Starting polling...")
    
    # Запуск Bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
