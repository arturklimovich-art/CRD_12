# 🤖 CRD12 Self-Building Test - COMPLETE GUIDE

**Дата:** 2025-11-19 12:13:27 UTC  
**Автор:** arturklimovich-art  
**Ветка:** feature/roadmap-arturklimovich-20251117  
**Версия:** 2.0 (Extended)

---

## 🏗️ АРХИТЕКТУРА СИСТЕМЫ

### Контейнеры Docker
\\\
crd12_pgvector        - PostgreSQL 16 + pgvector (порт 5432)
crd12_bot             - Telegram Bot (Python 3.11)
crd12_engineer_b_api  - FastAPI (порт 8001/8031)
crd12_nginx           - Nginx reverse proxy (порт 8031)
\\\

### База данных (PostgreSQL)
\\\sql
-- Основные таблицы:
eng_it.roadmap_tasks    -- 25 задач Roadmap
eng_it.tasks            -- Связь с roadmap_tasks
core.events             -- 40 событий (логирование)
eng_it.progress_navigator -- 74 детальных шага
\\\

### Порты
- 5432: PostgreSQL
- 8001: FastAPI (прямой доступ)
- 8031: Nginx (проксирует FastAPI)
- Telegram Bot: polling mode (без порта)

---

## 📊 ТЕКУЩЕЕ СОСТОЯНИЕ

### Roadmap Statistics
\\\
planned:     6 задач
in_progress: 3 задачи (1012, 1013, 1014)
done:        16 задач (включая 1001)
ИТОГО:       25 задач
\\\

### Текущая задача
\\\json
{
  "id": 1012,
  "code": "TASK-1012",
  "title": "E1-L8 Observability & Monitoring",
  "status": "in_progress",
  "priority": 2,
  "steps": []
}
\\\

### Последняя завершённая задача
\\\json
{
  "id": 1001,
  "code": "TASK-1001",
  "title": "E1-B6 Bot v2: Self-Learning Architecture",
  "status": "done",
  "completed_at": "2025-11-19T11:42:27+01:00"
}
\\\

---

## 🔗 ПОЛНАЯ ЦЕПОЧКА САМОСТРОИТЕЛЬСТВА

### Текущая реализация (что работает):
\\\
1. Roadmap загружен в БД (25 задач)
   ↓
2. API /api/current возвращает текущую задачу (1012)
   ↓
3. Bot команда /roadmap_navigator показывает задачу
   ↓
4. HTML Navigator отображает визуально
   ↓
5. События логируются в core.events
\\\

### Целевая цепочка (что должно быть):
\\\
1. TRIGGER: Завершение задачи (status = done)
   ↓
2. AUTO-SELECT: task_manager.get_next_self_building_task()
   ↓ (выбирает следующую задачу по приоритету)
3. LLM-ANALYZE: Анализ задачи через LLM
   ↓ (понимание требований, контекста, зависимостей)
4. LLM-PLAN: Генерация плана выполнения
   ↓ (разбивка на шаги, оценка сложности)
5. GITHUB-CREATE: Создание issue/PR на GitHub
   ↓ (автоматическое создание задачи)
6. EXECUTE: Выполнение кода (через AgentGraph)
   ↓ (изменения в коде, тесты, коммиты)
7. VERIFY: Проверка результата (CI/CD)
   ↓ (прохождение тестов, линтеры)
8. COMPLETE: Обновление статуса (done) + журнал
   ↓
9. LOOP: Возврат к шагу 1 (новая задача)
\\\

---

## 🔧 API ENDPOINTS (готовы)

### Roadmap API
\\\ash
# Все задачи
curl http://localhost:8001/api/roadmap

# Текущая задача
curl http://localhost:8001/api/current

# Шаги задачи
curl http://localhost:8001/api/navigator/steps/1012

# Все шаги Navigator
curl http://localhost:8001/api/navigator/all

# Матрица истины
curl http://localhost:8001/api/truth/matrix
\\\

### PowerShell примеры
\\\powershell
# Roadmap stats
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT status, COUNT(*) FROM eng_it.roadmap_tasks GROUP BY status;"

# Current task JSON
curl http://localhost:8001/api/current 2>&1 | ConvertFrom-Json | Select-Object -ExpandProperty task

# Events count
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT COUNT(*) FROM core.events;"

# Last 10 events
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT event_type, created_at, data->>'message' as message FROM core.events ORDER BY created_at DESC LIMIT 10;"
\\\

---

## 🤖 TELEGRAM BOT

### Доступные команды
\\\
/start                  - Приветствие
/help                   - Список команд
/roadmap_load           - Загрузка Roadmap YAML в БД
/roadmap_generate_tz    - Генерация ТЗ для задачи
/roadmap_update_status  - Обновление статуса задачи
/roadmap_navigator      - Текущая задача + шаги
\\\

### Примеры использования
\\\
/roadmap_navigator
→ Показывает задачу 1012 с прогрессом 0%

/roadmap_generate_tz 1012
→ Генерирует ТЗ для задачи 1012 через LLM
\\\

---

## 🧠 TASK MANAGER (автовыбор задачи)

### Файл: src/bot/tasks/task_manager.py

### Функция: get_next_self_building_task()
\\\python
async def get_next_self_building_task() -> Optional['asyncpg.Record']:
    """
    Выбирает следующую задачу для самостроительства
    Логика:
    1. Исключает done/cancelled задачи
    2. Приоритет: planned > in_progress
    3. Сортировка по priority (меньше = важнее)
    4. Возвращает первую задачу
    """
\\\

### Как протестировать
\\\python
# В контейнере bot
docker exec -it crd12_bot python
>>> from tasks.task_manager import TaskManager
>>> import asyncio
>>> tm = TaskManager()
>>> task = asyncio.run(tm.get_next_self_building_task())
>>> print(task)
\\\

---

## 🔬 LLM ИНТЕГРАЦИЯ

### Текущая реализация
- **Команда:** /roadmap_generate_tz
- **LLM:** OpenAI GPT-4 (через API)
- **Промпт:** Генерация ТЗ на основе title + description задачи

### Что нужно для полного цикла
1. **Анализ задачи:** Понимание требований
2. **Планирование:** Разбивка на шаги
3. **Генерация кода:** Создание файлов/изменений
4. **Код-ревью:** Проверка качества
5. **Тестирование:** Создание/запуск тестов

### Примерная цепочка промптов
\\\
Prompt 1 (Analyze):
"Analyze task: {title}. Extract requirements, dependencies, scope."

Prompt 2 (Plan):
"Create execution plan for: {requirements}. Break into steps."

Prompt 3 (Code):
"Generate code for step: {step}. Use existing codebase context."

Prompt 4 (Test):
"Generate tests for: {code}. Cover edge cases."
\\\

---

## 🚀 ПЛАН ТЕСТА (5 фаз)

### ФАЗА 1: Базовая проверка (5 мин)
**Цель:** Убедиться что система жива

\\\powershell
# 1. Проверка контейнеров
docker ps | Select-String "crd12"

# 2. Roadmap stats
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT status, COUNT(*) FROM eng_it.roadmap_tasks GROUP BY status;"

# 3. Current task API
curl http://localhost:8001/api/current

# 4. Bot test (в Telegram)
/roadmap_navigator

# 5. Events count
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT COUNT(*) FROM core.events;"
\\\

**Критерий успеха:** Все 5 проверок проходят без ошибок

---

### ФАЗА 2: Auto-path механизм (10 мин)
**Цель:** Проверить автоматический выбор задачи

\\\python
# В контейнере bot
docker exec -it crd12_bot python3 << EOF
import asyncio
from tasks.task_manager import TaskManager

async def test():
    tm = TaskManager()
    task = await tm.get_next_self_building_task()
    if task:
        print(f"✅ Next task: {task['id']} - {task['title']}")
        print(f"   Status: {task['status']}")
        print(f"   Priority: {task['priority']}")
    else:
        print("❌ No task selected")

asyncio.run(test())
EOF
\\\

**Критерий успеха:** Функция возвращает задачу с наименьшим priority из planned/in_progress

---

### ФАЗА 3: LLM цепочка (15 мин)
**Цель:** Проверить генерацию ТЗ через LLM

\\\
# В Telegram Bot
/roadmap_generate_tz 1012

# Ожидаем ответ:
"🤖 Генерирую ТЗ для задачи 1012...
📋 ТЗ сгенерировано:
[текст ТЗ с разбивкой на шаги]"
\\\

**Критерий успеха:** ТЗ содержит:
- Цель задачи
- Список шагов (минимум 3)
- Критерии приёмки

---

### ФАЗА 4: Интеграция (15 мин)
**Цель:** Проверить создание GitHub issue

\\\powershell
# Создание issue через GitHub API
# (требует настройки GitHub token)

# Альтернатива: проверка логирования события
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "
INSERT INTO core.events (event_type, entity_type, entity_id, data)
VALUES ('task_started', 'roadmap_task', 1012, '{\"message\": \"Test auto-start\"}');
"

# Проверка что событие залогировано
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT * FROM core.events ORDER BY created_at DESC LIMIT 1;"
\\\

**Критерий успеха:** Событие успешно создано в БД

---

### ФАЗА 5: Полный цикл (20 мин)
**Цель:** End-to-end тест самостроительства

\\\
СЦЕНАРИЙ:
1. Выбрать задачу (task_manager)
2. Сгенерировать ТЗ (LLM)
3. Создать план выполнения (LLM)
4. Залогировать события (core.events)
5. Обновить статус задачи (in_progress)
6. [ИМИТАЦИЯ] Выполнение шагов
7. Обновить статус (done)
8. Выбрать следующую задачу
\\\

**Критерий успеха:** Цикл завершается без ошибок, следующая задача выбрана

---

## 🎯 КРИТЕРИИ УСПЕХА

| Уровень | Что проверяем | Критерии |
|---------|--------------|----------|
| ✅ Минимальный | Базовые функции | API работает, Bot отвечает, task_manager выбирает задачу |
| ✅ Средний | LLM интеграция | ТЗ генерируется, план создаётся, события логируются |
| ✅ Полный | Автономность | Полный цикл без участия человека: выбор → анализ → план → выполнение → завершение → новая задача |

---

## 📞 КОНТАКТЫ

- **Repo:** github.com/arturklimovich-art/CRD_12
- **Branch:** feature/roadmap-arturklimovich-20251117
- **Bot:** @crd12_bot (Telegram)
- **API:** http://localhost:8001
- **Navigator:** http://localhost:8001/navigator

---

## ❓ FAQ

**Q: Где хранится Roadmap YAML?**  
A: docs/ROADMAP.yaml

**Q: Как добавить новую задачу?**  
A: Отредактировать ROADMAP.yaml → /roadmap_load

**Q: Где посмотреть логи бота?**  
A: docker logs crd12_bot --tail 50

**Q: Как проверить БД вручную?**  
A: docker exec -it crd12_pgvector psql -U crd_user -d crd12

**Q: Где код task_manager?**  
A: src/bot/tasks/task_manager.py

---

**Статус:** ✅ ГОТОВ К ТЕСТУ  
**Версия:** 2.0 (Extended with full context)
