# ===================================================================
# PATCH: ИНТЕГРАЦИЯ CURATOR В BOT
# Дата: 2025-11-19 20:20:32 UTC
# Цель: Добавить проверку кода через Curator перед применением
# ===================================================================

# ===================================================================
# CURATOR INTEGRATION - Проверка кода перед применением
# ===================================================================

async def call_curator_api(task_text: str, code: str, target_path: str = "/app/generated.py") -> dict:
    """
    Вызывает Curator API для проверки кода
    
    Args:
        task_text: Описание задачи
        code: Сгенерированный код для проверки
        target_path: Целевой путь файла
    
    Returns:
        {
            "decision": "approve" | "reject",
            "reasons": [...],
            "score": 0-100,
            "metrics": {...}
        }
    """
    import aiohttp
    
    curator_url = f"{ENGINEER_API_URL}/api/v1/validate"
    
    payload = {
        "task_text": task_text,
        "code": code,
        "target_path": target_path
    }
    
    try:
        logger.info(f"[CURATOR] Отправка кода на проверку: {curator_url}")
        
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(curator_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"[CURATOR] Решение: {result.get('decision')} (score: {result.get('score')})")
                    return result
                else:
                    logger.error(f"[CURATOR] HTTP {response.status}: {await response.text()}")
                    # Fallback: если Curator недоступен, блокируем код (безопасность!)
                    return {
                        "decision": "reject",
                        "reasons": [f"Curator API error: HTTP {response.status}"],
                        "score": 0,
                        "metrics": {}
                    }
    except Exception as e:
        logger.error(f"[CURATOR] Ошибка вызова: {e}")
        # Fallback: если ошибка, блокируем код (безопасность!)
        return {
            "decision": "reject",
            "reasons": [f"Curator API unavailable: {str(e)}"],
            "score": 0,
            "metrics": {}
        }

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

    # Обновляем статус на in_progress
    update_task_status(task_id, "in_progress")

    # Отправляем уведомление
    await update.message.reply_text(
        f"🚀 Запускаю задачу...\n\n📝 ID: `{task_id}`\n📄 Описание: {task_title}\n\n⏳ Отправляю в Engineer API..."
    )

    # Отправка задачи в Engineer API
    try:
        payload = {
            "task": task_title,
            "job_id": task_id
        }

        response = requests.post(
            f"{ENGINEER_API_URL}/agent/analyze",
            json=payload,
            timeout=300
        )

        if response.status_code == 200:
            result = response.json()
            status = result.get("engineer_status", "unknown")
            generated_code = result.get("generated_code", "")  # Получаем код из ответа

            if status == "passed" and generated_code:
                # ===================================================================
                # НОВОЕ: ПРОВЕРКА КОДА ЧЕРЕЗ CURATOR
                # ===================================================================
                
                await update.message.reply_text(
                    f"🔍 Отправляю код на проверку Curator...\n\n📊 Размер кода: {len(generated_code)} символов"
                )
                
                # Вызываем Curator для проверки кода
                curator_result = await call_curator_api(
                    task_text=task_title,
                    code=generated_code,
                    target_path=f"/app/task_{task_id}.py"
                )
                
                decision = curator_result.get("decision", "reject")
                reasons = curator_result.get("reasons", [])
                score = curator_result.get("score", 0)
                
                if decision == "approve":
                    # Код одобрен Curator → можно применять
                    bot_response = (
                        f"✅ Задача выполнена успешно!\n\n"
                        f"📝 ID: `{task_id}`\n"
                        f"👨‍⚖️ Curator: ОДОБРЕНО ✅\n"
                        f"📊 Score: {score}/100\n\n"
                        f"🎯 Результат: Код проверен и готов к применению\n"
                        f"⚠️ PatchManager: заглушка (код НЕ применён реально)"
                    )
                    update_task_status(task_id, "done")
                    logger.info(f"[TASK {task_id}] Curator APPROVED (score: {score})")
                    
                else:
                    # Код отклонён Curator → блокируем
                    reasons_text = "\n".join([f"  • {r}" for r in reasons])
                    bot_response = (
                        f"❌ Curator заблокировал код!\n\n"
                        f"📝 ID: `{task_id}`\n"
                        f"👨‍⚖️ Curator: ОТКЛОНЕНО ❌\n"
                        f"📊 Score: {score}/100\n\n"
                        f"⚠️ Причины:\n{reasons_text}\n\n"
                        f"🔧 Задача НЕ выполнена. Требуется исправление кода."
                    )
                    update_task_status(task_id, "failed")
                    logger.warning(f"[TASK {task_id}] Curator REJECTED: {reasons}")
                
            elif status == "passed" and not generated_code:
                # Engineer B вернул passed, но код отсутствует
                bot_response = (
                    f"⚠️ Задача завершена, но код не был сгенерирован\n\n"
                    f"📝 ID: `{task_id}`\n"
                    f"📊 Статус: {status}"
                )
                update_task_status(task_id, "done")
                
            else:
                # Engineer B вернул не-passed статус
                bot_response = (
                    f"⚠️ Задача завершена с предупреждениями\n\n"
                    f"📝 ID: `{task_id}`\n"
                    f"📊 Статус: {status}"
                )
                update_task_status(task_id, "done")
                
        else:
            bot_response = (
                f"❌ Ошибка выполнения задачи\n\n"
                f"📝 ID: `{task_id}`\n"
                f"⚠️ HTTP {response.status_code}: {response.text[:200]}"
            )
            update_task_status(task_id, "failed")

    except Exception as e:
        bot_response = f"❌ Ошибка при выполнении\n\n📝 ID: `{task_id}`\n\n⚠️ {str(e)}"
        update_task_status(task_id, "failed")
        logger.error(f"Error executing task {task_id}: {e}")

    await update.message.reply_text(bot_response)
    save_message_to_db(chat_id, user_id, username, "/run_roadmap", "command", bot_response)
