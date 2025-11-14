# 🗺️ Карта Архитектуры Системы ИИ-Агентов CRD12

## 1. Корень Проекта и "Зелёный Коридор"

* **Корень проекта:** C:\Users\Artur\Documents\CRD12\
* **Зелёные пути (для патчинга/снапшотов):**
    * /app/agents/
    * /app/src/engineer_b_api/
    * /app/src/bot/
    * /app/workspace/patches/
    * /app/workspace/ADR/
    * /app/workspace/snapshots/

## 2. Основные Компоненты и Агенты

| Агент/Сервис | Роль | Команды/Точки входа |
| :--- | :--- | :--- |
| **CodeGenius** | Генерация, валидация и оптимизация кода PowerShell. | Invoke-AIAgent -AgentName CodeGenius... |
| **SystemArchitect** | Проектирование, анализ модулей, архитектура, документация. | Invoke-AIAgent -AgentName SystemArchitect... |
| **AutomationExpert** | Проектирование рабочих процессов, планирование задач, интеграция API. | Invoke-AIAgent -AgentName AutomationExpert... |
| **Curator** | Управление задачами, разрешение конфликтов, контроль политик (E1-B10). | Internal Service |
| **Bot (Telegram)** | Внешний интерфейс команд и уведомлений. | /tasks, /status, /addtask, /result |

## 3. Стек Базы Данных (PostgreSQL)

* **DSN:** postgres://crd_user:crd12@localhost:5433/crd12
* **Схемы:** core, eng_it
* **Ключевые Таблицы/Вьюхи:**
    * **core:** core.events (единый журнал всех событий), core.v_bot_events, core.v_llm_events.
    * **eng_it:** eng_it.tasks (проекция статусов), eng_it.job_queue, eng_it.artifacts, eng_it.system_snapshot (снапшоты системы).
    * **Вьюхи:** eng_it.v_unresolved_tasks, eng_it.v_curator_dashboard, eng_it.v_system_latest_snapshot.

## 4. Пространства Событий (Observability)

Система использует строгую иерархию событий для наблюдаемости, аудита и принятия решений агентами:

| Namespace | Назначение |
| :--- | :--- |
| `plan.*` | Жизненный цикл задач (создание, статусы, блокировки). |
| `readmap.*` | Загрузка и ревизии плана работ. |
| `navigator.*` | Навигация по файловой системе, операции со снапшотами. |
| `eng.apply_patch.*` / `ps.patch.*` | Применение патчей и само-обновление системы. |
| `llm.*` | Все взаимодействия с LLM (запросы, ответы, ошибки). |
| `bot.*` | Взаимодействие с внешними интерфейсами (Telegram). |
| `curator.*` | Решения и рацио Куратора. |
| `audit.system.*` | Общие системные проверки и аудит. |

## 5. Контракт Окружения (ENV-Contract)

**Ключи, которые должны быть в config\.env (без значений):**

* LLM_PROVIDER, LLM_PROFILE, OFFLINE_MODE
* OPENAI_BASE_URL, OPENAI_API_KEY, LLM_MODEL
* LLM_CTX_LEN, LLM_KV_POLICY, LLM_BATCH_SIZE
* TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

## 6. LLM-Стек и Telegram-Интерфейс

* **LLM-Профили:**
    * FAST: ctx_len=2048, kv_policy=gpu
    * LONG: ctx_len=4096, kv_policy=q8|cpu(offload)
* **Telegram-Интерфейс:**
    * **Режимы:** Command (для быстрых действий), Intelligence (для сложных запросов через LLM).
    * **Health Check:** /ping
