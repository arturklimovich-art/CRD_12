# bot.py (Полный рефакторинг для Task Manager)
import os
import sys
import logging
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from commands.roadmap_navigator import roadmap_navigator_command
import asyncio # <-- Необходим для асинхронного запуска задач
import re # <-- Может пригодиться для будущих функций

# === КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ ДЛЯ ПРОБЛЕМЫ С PATH В DOCKER ===
# Явно добавляем текущую директорию в путь поиска модулей.
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    # Используем insert(0) чтобы гарантировать приоритет
    sys.path.insert(0, current_dir)
# =============================================================

# Импорты из новых модулей Task Manager
try:
    # Импорт из config.py, tasks/task_manager.py, database.py
    from config import TELEGRAM_BOT_TOKEN
    from tasks.task_manager import TaskManager 
    from database import Task, SessionLocal # <--- ДОБАВЛЕН SessionLocal
except ImportError as e:
    print(f"❌ CRITICAL ERROR importing core modules: {e}")
    print("PYTHONPATH:", sys.path)
    sys.exit(1)

# ====== Логи =====
logging.basicConfig(
    level=logging.INFO, # Уровень INFO для продакшена
    format="%(asctime)s %(levelname)s [BOT] %(message)s"
)
log = logging.getLogger("bot")


# ===================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ===================================================================

def format_task_report(task: Task) -> str:
    """Форматирует отчет о задаче для отправки в Telegram."""
    
    # Дефолтные значения
    report_data = None

    if task.test_results and task.status != 'failed':
        try:
            # Отчет может быть JSON-строкой
            report_data = json.loads(task.test_results)
        except json.JSONDecodeError:
            # Или просто текст (например, лог ошибок)
            report_data = {"description": task.test_results}

    if task.status == 'pending':
        emoji = "⏳"
        detail = "Задача ожидает в очереди."
    elif task.status == 'in_progress':
        emoji = "⚙️"
        detail = "Генерация и тестирование кода..."
    elif task.status == 'completed':
        # ИСПРАВЛЕНИЕ: Используем статус deployment_ready, который установлен в БД (Task Manager)
        is_deployment_ready = task.deployment_ready # <--- ИСПОЛЬЗУЕМ ЗНАЧЕНИЕ ИЗ БД
        emoji = "✅" if is_deployment_ready else "⚠️"
        detail = "Развертывание готово." if is_deployment_ready else "Требуется ручная проверка (тесты не пройдены)."
    elif task.status == 'failed':
        emoji = "❌"
        detail = "Критический сбой во время обработки."
    else:
        emoji = "❓"
        detail = "Неизвестный статус."
    
    # Экранируем описание задачи
    safe_description = task.task_description[:50]
    safe_description = safe_description.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
    
    # Используем ПРОСТОЙ текст без Markdown
    response_text = (
        f"{emoji} ОТЧЕТ ПО ЗАДАЧЕ #{task.id} {emoji}\n\n"
        f"Статус: {task.status.upper()}\n"
        f"Результат: {detail}\n"
        f"Создано: {task.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"ТЗ: {safe_description}...\n\n"
    )
    
    if report_data:
        response_text += "=== Автономный Отчет ===\n"
        
        # ИСПРАВЛЕНИЕ: Используем статус из БД для отчета, чтобы он совпадал с эмодзи
        deployment_status = "ДА" if task.deployment_ready else "НЕТ" 
        response_text += f"Готовность к Деплою: {deployment_status}\n"
        
        # Ищем описание: сначала в 'description', затем в 'llm_report.notes'
        description = report_data.get('description')
        
        # Fallback на llm_report.notes, если основное описание пустое или не найдено
        if not description and isinstance(report_data.get('llm_report'), dict):
            description = report_data['llm_report'].get('notes')
            
        safe_description_report = str(description or 'N/A')
        
        # Экранируем описание отчета (для MarkdownV2, как запрошено)
        safe_description_report = safe_description_report.replace('*', '\\*').replace('_', '\\_').replace('`', '\\`')
        response_text += f"Описание: {safe_description_report}\n"

        # Обновлено: добавлен smoke_message
        safe_test_result = str(report_data.get('smoke_test_result', report_data.get('smoke_message', 'N/A')))
        # Используем ту же логику экранирования, что и была
        safe_test_result = safe_test_result.replace('*', '').replace('_', '').replace('`', '')
        response_text += f"Smoke Test: {safe_test_result}\n"
        
    return response_text


async def send_task_code(update: Update, task: Task):
    """Отправляет код задачи отдельным сообщением."""
    if task.generated_code:
        # ВОССТАНАВЛИВАЕМ правильные символы вместо HTML-entities (если они были сохранены в БД)
        clean_code = task.generated_code.replace('&lt;', '<').replace('&gt;', '>')
        
        # Обрезаем если слишком длинный (ограничение Telegram ~4000 символов)
        if len(clean_code) > 3500:
            clean_code = clean_code[:3500] + "\n\n... (код обрезан из-за ограничения длины)"
            
        # Отправляем код как отдельное сообщение с синтаксисом MarkdownV2
        # ВАЖНО: нужно экранировать ВСЕ оставшиеся специальные символы MarkdownV2
        # Однако, при использовании '```python\n{code}\n```' экранирование внутри блока кода
        # обычно не требуется. Мы будем считать, что код не содержит тройных кавычек.
        code_message = f"```python\n{clean_code}\n```"
        try:
             await update.message.reply_text(code_message, parse_mode='MarkdownV2')
        except Exception:
             # Если MarkdownV2 вызывает ошибку (например, из-за неэкранированных символов вне блока)
             # Отправляем как простой текст
             await update.message.reply_text("=== СГЕНЕРИРОВАННЫЙ КОД (ошибка форматирования) ===\n" + clean_code)


# ===================================================================
# КОМАНДЫ БОТА
# ===================================================================

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает команду /start."""
    await update.message.reply_text(
        "👋 Привет! Я ваш Task Manager. Пришлите мне описание задачи, и я займусь ее выполнением.\n\n"
        "Для проверки статуса задачи используйте: `/status [ID]` (например, `/status 1`).\n"
        "Для просмотра последних задач: `/list`"
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверяет статус задачи по ID."""
    
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите ID задачи. Пример: /status 1")
        return
        
    try:
        task_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("ID задачи должен быть числом.")
        return
        
    log.info(f"Checking status for Task ID: {task_id}")
    try:
        task = await TaskManager.get_task_by_id(task_id)
        
        if task:
            # Сначала отправляем отчет
            report = format_task_report(task)
            await update.message.reply_text(report)
            
            # Затем отправляем код отдельным сообщением (если есть)
            if task.generated_code and task.status in ['completed', 'failed']:
                await send_task_code(update, task)
        else:
            await update.message.reply_text(f"Задача с ID {task_id} не найдена в системе.")
    except Exception as e:
        log.error(f"Error getting status for task {task_id}: {e}")
        await update.message.reply_text(f"🔥 Произошла ошибка при получении статуса: {str(e)}")


async def list_tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает все задачи в системе."""
    try:
        db = SessionLocal()
        try:
            # Получаем последние 10 задач, отсортированных по ID
            tasks = db.query(Task).order_by(Task.id.desc()).limit(10).all()
            
            if not tasks:
                await update.message.reply_text("В системе нет задач.")
                return
            
            response = "📋 Последние задачи (макс. 10):\n\n"
            for task in tasks:
                # Определяем эмодзи
                status_emoji = "⏳" if task.status == 'pending' else "⚙️" if task.status == 'in_progress' else "✅" if task.status == 'completed' else "❌"
                
                # Обрезаем и очищаем описание от потенциального Markdown для plain text
                safe_description = task.task_description[:30]
                safe_description = safe_description.replace('*', '').replace('_', '').replace('`', '')
                
                # Формируем строку отчета
                response += f"{status_emoji} #{task.id} - {task.status.upper()} - {safe_description}...\n"
            
            # Отправляем как plain text
            await update.message.reply_text(response)
            
        finally:
            db.close()
            
    except Exception as e:
        log.error(f"Error listing tasks: {e}")
        await update.message.reply_text(f"Ошибка при получении списка задач: {e}")


async def handle_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Главный обработчик сообщений: создает задачу и запускает ее обработку в фоне.
    """
    user_prompt = update.message.text
    user_id = str(update.effective_user.id)
    
    # ВАЖНО: Игнорируем команды (начинающиеся с /)
    if user_prompt.startswith('/'):
        log.info(f"🔧 Ignoring command from {user_id}: {user_prompt}")
        return
    
    if not user_prompt.strip():
        # Игнорируем пустые сообщения
        return
        
    log.info(f"📝 Received message from {user_id}: {user_prompt[:50]}...")
    
    # Немедленный ответ пользователю с предпросмотром задачи (очищаем от спецсимволов)
    preview_prompt = user_prompt[:100].replace('`', '').replace('*', '').replace('_', '')
    await update.message.reply_text(
        f"⚙️ Принята новая задача:\n`{preview_prompt} ...`\n\nСоздаю задачу в очереди..."
    )

    try:
        # 1. Создание задачи в БД (асинхронно)
        new_task = await TaskManager.create_new_task(user_id, user_prompt)
        task_id = new_task.id
        
        # 2. Ответ пользователю с ID задачи
        await update.message.reply_text(
            f"✅ Задание принято! Ваша задача #{task_id} добавлена в очередь.\n"
            f"Я начну работу немедленно. Проверить статус можно командой: /status {task_id}"
        )
        
        # 3. Запуск обработки задачи в фоновом режиме
        # Используем asyncio.create_task для неблокирующего запуска
        asyncio.create_task(TaskManager.process_task(task_id))
        log.info(f"🚀 Started background task processing for Task ID: {task_id}")

    except Exception as e:
        log.exception(f"❌ Critical error during task creation: {e}")
        await update.message.reply_text(
            f"🔥 СИСТЕМНАЯ ОШИБКА: Не удалось создать задачу.\nПроверьте логи Task Manager. Ошибка: {e}"
        )


# ===================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ===================================================================

def register_handlers(app: Application):
    """Регистрация обработчиков команд и сообщений."""
    log.debug("📝 Registering handlers")
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("list", list_tasks_cmd))
    app.add_handler(CommandHandler("roadmap_navigator", roadmap_navigator_command))  # <-- ДОБАВЛЕНО
    # Обрабатываем только TEXT сообщения, которые НЕ являются командами
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_messages))


def main():
    """Основная функция для запуска Telegram Bot."""
    if not TELEGRAM_BOT_TOKEN:
        log.error("❌ TELEGRAM_BOT_TOKEN не найден. Проверьте ваш config.py или .env файл.")
        return

    log.info(f"🔧 Starting Task Manager Bot with TOKEN: {TELEGRAM_BOT_TOKEN[:10]}...")
    
    # 1. Создание объекта Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # 2. Регистрация обработчиков
    register_handlers(application)
    
    # 3. Запуск бота в режиме long-polling
    log.info("🤖 Bot started and waiting for messages...")
    application.run_polling(poll_interval=1.0)

if __name__ == '__main__':
    # Важно: В этом месте должен быть только запуск, без дополнительных настроек логирования
    # или asyncio, так как они инициализируются внутри main()
    main()