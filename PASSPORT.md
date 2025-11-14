📘 ПАСПОРТ ПРОЕКТА ENGINEERS_IT (CRD12)
🎯 Название проекта
Engineers_IT (CRD12) - Самообучающаяся система разработки с автоматическим деплоем

Версия: 2.0
Дата: 2025-11-11
Статус: ✅ Production Ready

📋 ОГЛАВЛЕНИЕ
Обзор системы
Архитектура
Компоненты системы
База данных
Telegram Bot
Engineer API
PatchManager
Рабочие процессы
Быстрый старт
API Reference
Troubleshooting
🔍 ОБЗОР СИСТЕМЫ
Что это?
Engineers_IT - это автоматизированная система разработки, которая:

Принимает задачи через Telegram Bot
Генерирует код с помощью LLM (DeepSeek)
Автоматически применяет изменения с версионированием
Хранит полную историю всех изменений
Позволяет откатиться к любой версии кода
Основные возможности
✅ Telegram интерфейс - управление через мессенджер
✅ Roadmap система - планирование и приоритизация задач
✅ Автоматический деплой - код применяется без ручного вмешательства
✅ Версионирование - каждое изменение сохраняется
✅ Smoke testing - автоматическая проверка кода перед деплоем
✅ Curator проверка - валидация изменений перед применением
✅ Rollback механизм - откат к предыдущим версиям

🏗️ АРХИТЕКТУРА
Высокоуровневая схема
Code
┌─────────────────────────────────────────────────────────────┐
│                      ПОЛЬЗОВАТЕЛЬ                            │
│                    (Telegram Client)                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                              │
│              (bot_integrated.py)                             │
│  Команды: /add_task, /run_roadmap, /status, /help          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      ROADMAP                                 │
│               (eng_it.tasks в PostgreSQL)                    │
│  Статусы: planned → in_progress → done/failed               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   TASK MANAGER                               │
│              (tasks/task_manager.py)                         │
│  Проверяет Roadmap каждые 5 минут, запускает задачи        │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   ENGINEER API                               │
│          (engineer_b_api: app.py + main.py)                 │
│  Endpoint: POST /agent/analyze                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM (DeepSeek)                            │
│              Генерация кода из описания                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  CURATOR (Проверка)                          │
│         Валидация сгенерированного кода                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                  PATCH MANAGER                               │
│         (patch_manager.py + patch_applier.py)               │
│  • Создаёт патч в БД                                        │
│  • Сохраняет версию старого файла                           │
│  • Генерирует approve_token                                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                   PATCH API                                  │
│         POST /api/patches/{id}/apply                        │
│  • Применяет патч к файлу                                   │
│  • Smoke test                                                │
│  • Логирует события                                          │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                 ФАЙЛОВАЯ СИСТЕМА                             │
│            /app/<target_file> обновлён                      │
│     Версия сохранена в eng_it.code_versions                 │
└─────────────────────────────────────────────────────────────┘
🧩 КОМПОНЕНТЫ СИСТЕМЫ
1. Docker контейнеры
Контейнер	Порт	Назначение
crd12_bot	-	Telegram Bot + Task Manager
crd12_engineer_b_api	8001 → 8000	Engineer API (генерация кода)
crd12_pgvector	5433 → 5432	PostgreSQL + pgvector
crd12_deepseek_proxy	8010	Прокси для DeepSeek API
crd12_ollama	11434	Локальная LLM (опционально)
2. Основные файлы
В контейнере crd12_bot:
Code
/app/
├── bot_integrated.py          # Telegram Bot (команды)
├── tasks/
│   ├── task_manager.py        # Автоматический запуск задач
│   ├── code_generator.py      # Генерация кода
│   └── post_deploy.py         # Пост-деплой проверки
├── config.py                  # Конфигурация
├── database.py                # ORM модели
└── utils/                     # Утилиты
В контейнере crd12_engineer_b_api:
Code
/app/
├── app.py                     # Основной API (+ интеграция PatchManager)
├── main.py                    # Patch API endpoints
├── patch_manager.py           # Управление патчами
├── patch_applier.py           # Интеграционная обёртка
├── curator.py                 # Проверка кода
└── agents/                    # Сгенерированные модули
3. Переменные окружения
В crd12_bot:

bash
TELEGRAM_BOT_TOKEN=7263212857:AAGU_wi4XqccG--bK6g-6UvsQ0jLG0rVGmQ
DATABASE_URL=postgres://crd_user:crd12@pgvector:5432/crd12
ENGINEER_B_API_URL=http://engineer_b_api:8000
SELF_BUILDING_MODE=true
POST_DEPLOY_VALIDATE=true
В crd12_engineer_b_api:

bash
DATABASE_URL=postgres://crd_user:crd12@crd12_pgvector:5432/crd12
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL_NAME=gpt-5-thinking
🗄️ БАЗА ДАННЫХ
Схема: eng_it
Основные таблицы:
1. tasks - Roadmap задач

SQL
CREATE TABLE eng_it.tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL,  -- planned, in_progress, done, blocked, failed
    owner TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    progress_notes TEXT,
    created_by TEXT DEFAULT 'manual',  -- telegram_bot, manual, system
    telegram_chat_id BIGINT,           -- ID чата откуда создана
    priority INTEGER DEFAULT 0          -- Приоритет (выше = важнее)
);
2. patches - История патчей

SQL
CREATE TABLE eng_it.patches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    author TEXT NOT NULL,
    filename TEXT NOT NULL,
    content BYTEA NOT NULL,             -- Содержимое патча
    sha256 TEXT NOT NULL,
    status TEXT DEFAULT 'pending',      -- pending, validated, applied, failed
    approve_token TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    applied_at TIMESTAMPTZ,
    task_id TEXT REFERENCES eng_it.tasks(id),
    generated_by TEXT DEFAULT 'manual', -- llm_auto, manual
    previous_version_id TEXT,           -- Ссылка на версию в code_versions
    target_file TEXT                    -- Путь к целевому файлу
);
3. code_versions - Версионирование кода

SQL
CREATE TABLE eng_it.code_versions (
    version_id TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,              -- Полное содержимое файла
    content_hash TEXT NOT NULL,
    task_id TEXT REFERENCES eng_it.tasks(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_stable BOOLEAN DEFAULT false,    -- Stable snapshot для rollback
    created_by TEXT DEFAULT 'system'
);
4. patch_events - События патчей

SQL
CREATE TABLE eng_it.patch_events (
    id BIGSERIAL PRIMARY KEY,
    patch_id UUID REFERENCES eng_it.patches(id),
    event_type TEXT NOT NULL,           -- eng.patch.created, eng.patch.applied
    payload JSONB,
    ts TIMESTAMPTZ DEFAULT NOW()
);
5. telegram_messages - История сообщений

SQL
CREATE TABLE eng_it.telegram_messages (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    user_id BIGINT,
    username TEXT,
    message_text TEXT NOT NULL,
    message_type TEXT DEFAULT 'text',   -- text, command, document
    bot_response TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
6. bot_context - Память бота

SQL
CREATE TABLE eng_it.bot_context (
    id SERIAL PRIMARY KEY,
    context_key TEXT NOT NULL UNIQUE,
    context_value JSONB NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
7. bot_commands - Команды бота

SQL
CREATE TABLE eng_it.bot_commands (
    id BIGSERIAL PRIMARY KEY,
    chat_id BIGINT NOT NULL,
    command TEXT NOT NULL,
    arguments JSONB,
    status TEXT DEFAULT 'pending',      -- pending, processing, completed, failed
    result JSONB,
    task_id TEXT REFERENCES eng_it.tasks(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
8. job_queue - Очередь задач

SQL
CREATE TABLE eng_it.job_queue (
    id BIGSERIAL PRIMARY KEY,
    task_id TEXT REFERENCES eng_it.tasks(id),
    job_type TEXT NOT NULL,
    payload JSONB,
    status TEXT DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
Полезные Views:
v_bot_dashboard - Активные задачи с метриками

SQL
SELECT id, title, status, priority, 
       COUNT(DISTINCT patches) as patches_count,
       COUNT(DISTINCT jobs) as jobs_count
FROM eng_it.tasks
WHERE status IN ('planned', 'in_progress')
ORDER BY priority DESC, created_at ASC;
🤖 TELEGRAM BOT
Файл: /app/bot_integrated.py
Команды:
Команда	Описание	Пример
/start	Приветствие и список команд	/start
/help	Справка по командам	/help
/add_task <описание>	Добавить задачу в Roadmap	/add_task Создать API endpoint /api/hello
/run_roadmap	Запустить следующую planned задачу	/run_roadmap
/status	Показать активные задачи	/status
Workflow команды /add_task:
Python
# 1. Пользователь отправляет
/add_task Создать файл hello.py с функцией hello()

# 2. Bot создаёт task_id
task_id = f"tg_{chat_id}_{timestamp}"  # tg_123456_1731354423

# 3. Вставка в БД
INSERT INTO eng_it.tasks (id, title, status, created_by, telegram_chat_id, priority)
VALUES ('tg_123456_1731354423', 'Создать файл hello.py...', 'planned', 'telegram_bot', 123456, 5);

# 4. Сохранение в telegram_messages
INSERT INTO eng_it.telegram_messages (chat_id, message_text, message_type, bot_response)
VALUES (123456, '/add_task ...', 'command', '✅ Задача добавлена...');

# 5. Bot отвечает
✅ Задача добавлена в Roadmap!
📝 ID: tg_123456_1731354423
🚀 Используйте /run_roadmap для запуска
Workflow команды /run_roadmap:
Python
# 1. Получение следующей задачи
SELECT id, title FROM eng_it.tasks
WHERE status = 'planned'
ORDER BY priority DESC, created_at ASC
LIMIT 1;

# 2. Обновление статуса
UPDATE eng_it.tasks SET status = 'in_progress' WHERE id = 'tg_...';

# 3. Отправка в Engineer API
POST http://engineer_b_api:8000/agent/analyze
{
    "task": "Создать файл hello.py...",
    "job_id": "tg_123456_1731354423"
}

# 4. Ожидание ответа (~30-60 сек)

# 5. Обновление статуса по результату
UPDATE eng_it.tasks SET status = 'done' WHERE id = 'tg_...';  # если успех
# или
UPDATE eng_it.tasks SET status = 'failed' WHERE id = 'tg_...';  # если ошибка

# 6. Отправка уведомления пользователю
✅ Задача выполнена успешно!
🎯 Результат: Код применён через PatchManager
Запуск Bot:
bash
# В контейнере crd12_bot
python3 /app/bot_integrated.py

# Логи
tail -f /var/log/telegram_bot.log
⚙️ ENGINEER API
Файл: /app/app.py
Основной endpoint:
POST /agent/analyze

Request:

JSON
{
    "task": "Создать файл agents/hello.py с функцией hello() которая возвращает 'Hello World'",
    "job_id": "tg_123456_1731354423"
}
Response (успех):

JSON
{
    "status": "passed",
    "analysis": "Задача выполнена успешно",
    "is_complete": true,
    "generated_code": "def hello():\n    return 'Hello World'\n",
    "report": {
        "deployment_ready": true,
        "description": "Code applied via PatchManager to agents/hello.py",
        "tests_status": "passed",
        "patch_id": "340a3bdd-235b-4e34-98f1-6b8b62730d3f"
    }
}
Внутренний процесс:
Python
# 1. Получение задачи
task_text = request_data["task"]
job_id = request_data["job_id"]

# 2. Отправка в LLM (DeepSeek)
analysis_result = await agent.run_cycle(task_text)
# → Возвращает: analysis_text, generated_code, target_file

# 3. Smoke test (синтаксис Python)
smoke_test_ok = compile(generated_code, "<string>", "exec")

# 4. Runtime smoke test (опционально)
runtime_smoke_ok, msg = run_runtime_smoke_test(generated_code, target_file)

# 5. Curator проверка
review = curator.review(task_text, generated_code, target_file)
# → Возвращает: {"approved": True/False, "score": 0-100}

# 6. Если approved → PatchManager
if review["approved"]:
    success, message, patch_id = apply_code_with_fallback(
        target_file=target_file,
        generated_code=generated_code,
        task_id=job_id,
        fallback_function=_apply_code_changes
    )
Интеграция с PatchManager (в app.py):
Python
# В строке ~549 app.py
if PATCH_APPLIER_AVAILABLE:
    success, message, patch_id = apply_code_with_fallback(
        target_file=target_file,
        generated_code=generated_code,
        task_id=job_id,
        fallback_function=_apply_code_changes
    )
    applied_ok = success
    apply_msg = message
    backup_path = patch_id  # patch_id вместо backup_path
else:
    # Fallback к старому методу
    applied_ok, apply_msg, backup_path = _apply_code_changes(target_file, generated_code)
🔧 PATCHMANAGER
Файлы:
/app/patch_manager.py - Основной модуль
/app/patch_applier.py - Интеграционная обёртка
Класс PatchManager
Метод create_patch_from_generated_code():
Python
def create_patch_from_generated_code(
    target_file: str,       # "agents/hello.py"
    generated_code: str,    # "def hello(): ..."
    task_id: str,           # "tg_123456_1731354423"
    author: str = "engineer_b_auto"
) -> Tuple[str, str]:      # (patch_id, approve_token)
Процесс:

Генерирует patch_id (UUID)
Если файл существует → сохраняет текущую версию в code_versions
Создаёт файл патча в /app/workspace/patches_applied/{patch_id}.patch
Вычисляет SHA256
Генерирует approve_token (auto-{task_id}-{timestamp})
Вставляет запись в eng_it.patches
Логирует событие в eng_it.patch_events
Возвращает (patch_id, approve_token)
Пример использования:
Python
from patch_manager import PatchManager

pm = PatchManager(db_dsn="postgres://...")
patch_id, token = pm.create_patch_from_generated_code(
    target_file="agents/hello.py",
    generated_code="def hello(): return 'Hi'",
    task_id="tg_123456_1731354423"
)

# Результат:
# patch_id = "340a3bdd-235b-4e34-98f1-6b8b62730d3f"
# token = "auto-tg_12345-1731354423"
Функция apply_code_with_fallback() (из patch_applier.py):
Python
def apply_code_with_fallback(
    target_file: str,
    generated_code: str,
    task_id: str,
    fallback_function = None
) -> Tuple[bool, str, str]:  # (success, message, patch_id)
Процесс:

Создаёт патч через PatchManager
Отправляет POST запрос к /api/patches/{patch_id}/apply с approve_token
Если успех → возвращает (True, "Success", patch_id)
Если ошибка и есть fallback_function → вызывает его
Возвращает результат
📡 PATCH API
Файл: /app/main.py
Endpoint: POST /api/patches/{patch_id}/apply
Request (Body as plain text):

Code
auto-tg_12345-1731354423
Response (успех):

JSON
{
    "status": "success",
    "message": "Patch applied and validated",
    "patch_id": "340a3bdd-235b-4e34-98f1-6b8b62730d3f",
    "target_file": "agents/hello.py",
    "sha256": "addb80e18b61fac6..."
}
Процесс применения патча:
Python
# 1. Получение патча из БД
SELECT * FROM eng_it.patches WHERE id = '340a3bdd...' AND status = 'validated';

# 2. Проверка approve_token
if approve_token != patch.approve_token:
    return 403 Forbidden

# 3. Извлечение content (bytea → text)
patch_content = patch.content.decode('utf-8')

# 4. Запись в целевой файл
with open(f"/app/{target_file}", 'w') as f:
    f.write(patch_content)

# 5. Smoke test
compile(patch_content, "<string>", "exec")

# 6. Обновление статуса
UPDATE eng_it.patches SET status = 'applied', applied_at = NOW() WHERE id = '340a3bdd...';

# 7. Логирование события
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
VALUES ('340a3bdd...', 'eng.patch.applied', '{"target_file": "agents/hello.py"}');
🔄 РАБОЧИЕ ПРОЦЕССЫ
Процесс 1: Создание задачи через Telegram
Code
Пользователь → /add_task Создать функцию X
                    ↓
           Bot (bot_integrated.py)
                    ↓
    Создание записи в eng_it.tasks
                    ↓
        Статус: planned, priority: 5
                    ↓
    Bot → "✅ Задача добавлена в Roadmap!"
Процесс 2: Автоматический запуск задачи (Task Manager)
Code
Task Manager (каждые 5 минут)
                    ↓
    SELECT * FROM eng_it.tasks WHERE status = 'planned'
                    ↓
    Если есть задачи → отправка в Engineer API
                    ↓
    POST http://engineer_b_api:8000/agent/analyze
                    ↓
          Engineer API обрабатывает
                    ↓
    Результат → обновление статуса задачи
Процесс 3: Ручной запуск через /run_roadmap
Code
Пользователь → /run_roadmap
                    ↓
    Bot → получает следующую planned задачу
                    ↓
    Обновляет статус → in_progress
                    ↓
    Отправляет в Engineer API
                    ↓
    Ожидает результат (синхронно)
                    ↓
    Отправляет уведомление пользователю
Процесс 4: Генерация и применение кода
Code
Engineer API получает задачу
                    ↓
    LLM генерирует код + target_file
                    ↓
           Smoke test (синтаксис)
                    ↓
         Runtime smoke test
                    ↓
        Curator проверка (валидация)
                    ↓
    Если approved → PatchManager
                    ↓
    patch_applier.apply_code_with_fallback()
                    ↓
    PatchManager.create_patch_from_generated_code()
        ├─ Сохранение старой версии в code_versions
        ├─ Создание записи в eng_it.patches
        └─ Логирование в patch_events
                    ↓
    POST /api/patches/{id}/apply (с approve_token)
                    ↓
    Применение патча к файлу
                    ↓
    Smoke test применённого кода
                    ↓
    Обновление статуса → applied
                    ↓
    ✅ Деплой завершён!
🚀 БЫСТРЫЙ СТАРТ
Для нового разработчика:
1. Проверка работы системы
PowerShell
# Проверка контейнеров
docker ps --filter "name=crd12"

# Ожидаемый результат:
# crd12_bot              - Up (может быть unhealthy)
# crd12_engineer_b_api   - Up (healthy)
# crd12_pgvector         - Up (healthy)
2. Проверка Bot
PowerShell
# Логи Bot
docker exec crd12_bot tail -f /var/log/telegram_bot.log

# Должно быть:
# "Starting Telegram Bot v2.0"
# "Bot handlers registered. Starting polling..."
# "Application started"
3. Проверка Task Manager
PowerShell
# Логи Task Manager
docker exec crd12_bot tail -f /var/log/task_manager.log

# Должно быть (каждые 5 минут):
# "Checking for planned tasks..."
4. Тест через Telegram
Code
1. Откройте Telegram
2. Найдите бота (токен: 7263212857:...)
3. Отправьте: /start
4. Отправьте: /add_task Создать test.py
5. Отправьте: /run_roadmap
6. Ждите ~30-60 сек
7. Получите: "✅ Задача выполнена успешно!"
5. Проверка результата в БД
PowerShell
# Задачи
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "
SELECT id, title, status FROM eng_it.tasks ORDER BY created_at DESC LIMIT 5;
"

# Патчи
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "
SELECT id, status, target_file FROM eng_it.patches ORDER BY created_at DESC LIMIT 5;
"

# Версии
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "
SELECT version_id, file_path FROM eng_it.code_versions ORDER BY created_at DESC LIMIT 5;
"
📚 API REFERENCE
Telegram Bot API (внутренний)
Функции:
create_task_in_roadmap(task_id, title, chat_id, priority)

Python
# Создаёт задачу в Roadmap
success = create_task_in_roadmap(
    task_id="tg_123_1731354423",
    title="Создать hello.py",
    chat_id=123456,
    priority=5
)
# Returns: True/False
get_next_planned_task()

Python
# Получает следующую planned задачу
task = get_next_planned_task()
# Returns: {"id": "...", "title": "...", "priority": 5, ...}
update_task_status(task_id, status)

Python
# Обновляет статус задачи
update_task_status("tg_123_...", "in_progress")
# Returns: True/False
get_active_tasks()

Python
# Получает активные задачи
tasks = get_active_tasks()
# Returns: [{"id": "...", "title": "...", "status": "planned"}, ...]
Engineer API
POST /agent/analyze

bash
curl -X POST http://localhost:8001/agent/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Создать файл hello.py",
    "job_id": "test_123"
  }'
GET /health

bash
curl http://localhost:8001/health
# Response: {"status": "ok", "ts": "2025-11-11T19:27:03Z"}
Patch API
POST /api/patches/{patch_id}/apply

bash
curl -X POST http://localhost:8000/api/patches/340a3bdd.../apply \
  -H "Content-Type: text/plain" \
  -d "auto-test_tas-1731354423"
GET /api/patches/{patch_id}

bash
curl http://localhost:8000/api/patches/340a3bdd...
# Response: {"id": "...", "status": "applied", "target_file": "..."}
PatchManager API (Python)
Python
from patch_manager import PatchManager

# Создание экземпляра
pm = PatchManager(
    db_dsn="postgres://crd_user:crd12@pgvector:5432/crd12",
    base_path="/app",
    patches_dir="/app/workspace/patches_applied"
)

# Создание патча
patch_id, token = pm.create_patch_from_generated_code(
    target_file="agents/test.py",
    generated_code="def test(): pass",
    task_id="task_123",
    author="bot"
)
🐛 TROUBLESHOOTING
Проблема 1: Bot не отвечает в Telegram
Диагностика:

PowerShell
docker exec crd12_bot tail -f /var/log/telegram_bot.log
Ожидаемое:

Code
Starting Telegram Bot v2.0
Bot handlers registered. Starting polling...
Application started
Если нет → проверьте:

Процесс запущен?
PowerShell
docker exec crd12_bot sh -c "pgrep -f bot_integrated || echo 'Not running'"
Правильный токен?
PowerShell
docker exec crd12_bot env | grep TELEGRAM_BOT_TOKEN
Перезапуск:
PowerShell
docker exec crd12_bot pkill -f bot_integrated
docker exec -d crd12_bot sh -c "nohup python3 /app/bot_integrated.py > /var/log/telegram_bot.log 2>&1 &"
Проблема 2: Задача не запускается
Диагностика:

SQL
SELECT id, title, status FROM eng_it.tasks WHERE status = 'planned';
Если задач нет → создайте через /add_task

Если есть, но не запускаются:

Проверьте Task Manager:
PowerShell
docker exec crd12_bot tail -f /var/log/task_manager.log
Запустите вручную: /run_roadmap
Проблема 3: Патч не применяется
Диагностика:

PowerShell
docker exec crd12_engineer_b_api tail -f /app/logs/app.log
Проверьте:

Патч создан?
SQL
SELECT id, status FROM eng_it.patches WHERE task_id = 'tg_...';
approve_token правильный?
Попробуйте вручную:
bash
curl -X POST http://localhost:8000/api/patches/{id}/apply \
  -H "Content-Type: text/plain" \
  -d "auto-..."
Проблема 4: База данных недоступна
Диагностика:

PowerShell
docker exec crd12_pgvector pg_isready -U crd_user
Если не готова:

PowerShell
docker restart crd12_pgvector
Проверка подключения:

PowerShell
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT 1"
Проблема 5: Engineer API не отвечает
Диагностика:

PowerShell
curl http://localhost:8001/health
Если не отвечает:

PowerShell
docker logs crd12_engineer_b_api --tail 50
docker restart crd12_engineer_b_api
Проект: Engineers_IT (CRD12)
Версия: 2.0
Дата документации: 2025-11-11

Пользователь: arturklimovich-art
Telegram Bot Token: 7263212857:AAGU_wi4XqccG--bK6g-6UvsQ0jLG0rVGmQ

✅ ЧЕКЛИСТ ДЛЯ НОВОГО РАЗРАБОТЧИКА
 Проверил работу всех контейнеров (docker ps)
 Проверил логи Bot (tail -f /var/log/telegram_bot.log)
 Протестировал команду /start в Telegram
 Создал тестовую задачу через /add_task
 Запустил задачу через /run_roadmap
 Проверил результат в БД (SELECT * FROM eng_it.tasks)
 Нашёл созданный патч (SELECT * FROM eng_it.patches)
 Проверил версионирование (SELECT * FROM eng_it.code_versions)
 Прочитал секцию Troubleshooting
 Готов к работе! 🚀
🎉 ФИНАЛ
Система полностью готова к использованию!

Вы можете:

Создавать задачи через Telegram
Автоматически генерировать и деплоить код
Отслеживать историю изменений
Откатываться к предыдущим версиям
Мониторить все процессы через БД
Удачи в разработке! 🚀

Документация создана: 2025-11-11 19:27:03 UTC



