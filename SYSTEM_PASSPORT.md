# 📘 CRD12 SYSTEM PASSPORT

**Версия:** 1.0  
**Дата:** 2025-11-19 12:28:38 UTC  
**Автор:** arturklimovich-art  
**Ветка:** feature/roadmap-arturklimovich-20251117  
**Коммитов:** 31  

---

## 📖 СОДЕРЖАНИЕ

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [File Structure](#3-file-structure)
4. [Configuration](#4-configuration)
5. [Database Schema](#5-database-schema)
6. [API Reference](#6-api-reference)
7. [Bot Commands](#7-bot-commands)
8. [Self-Building Chain](#8-self-building-chain)
9. [Roadmap](#9-roadmap)
10. [Development Workflow](#10-development-workflow)
11. [Testing](#11-testing)
12. [Monitoring & Logging](#12-monitoring--logging)
13. [Troubleshooting](#13-troubleshooting)
14. [Deployment](#14-deployment)

---

## 1. OVERVIEW

### 🎯 Цель проекта
**CRD12** - Self-Building AI System с автономным выполнением задач из Roadmap.

### 📊 Текущий этап
- **Roadmap:** 25 задач (16 done, 3 in_progress, 6 planned)
- **Прогресс:** 64% выполнено
- **Текущая задача:** #1012 (E1-L8 Observability & Monitoring)
- **Последняя завершённая:** #1001 (E1-B6 Bot v2: Self-Learning Architecture)

### 🏆 Ключевые достижения
- ✅ Roadmap загружен в БД (25 задач)
- ✅ Bot v2 с командами управления Roadmap
- ✅ JSON API для интеграций
- ✅ HTML Navigator Dashboard
- ✅ Система логирования событий (core.events)
- ✅ Task Manager с автовыбором задач

---

## 2. ARCHITECTURE

### 🐳 Docker Контейнеры

| Контейнер | Image | Порты | Назначение |
|-----------|-------|-------|------------|
| crd12_pgvector | pgvector/pgvector:pg16 | 5432 | PostgreSQL 16 + vector extension |
| crd12_bot | python:3.11-slim | - | Telegram Bot (polling) |
| crd12_engineer_b_api | python:3.11-slim | 8001, 8031 | FastAPI + Jinja2 templates |
| crd12_nginx | nginx:alpine | 8031 | Reverse proxy для API |

### 🔗 Связи между компонентами

\\\
┌─────────────────┐
│   Telegram      │
│   User          │
└────────┬────────┘
         │
         ↓
┌─────────────────┐      ┌─────────────────┐
│   crd12_bot     │─────→│  crd12_pgvector │
│  (Python Bot)   │      │   (PostgreSQL)  │
└────────┬────────┘      └────────┬────────┘
         │                        ↑
         │ HTTP calls             │
         ↓                        │
┌─────────────────┐               │
│ engineer_b_api  │───────────────┘
│   (FastAPI)     │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   crd12_nginx   │
│ (Reverse Proxy) │
└─────────────────┘
\\\

### 🌐 Порты и доступ

- **5432:** PostgreSQL (внутренний доступ)
- **8001:** FastAPI прямой доступ
- **8031:** Nginx (рекомендуемый)
- **Telegram Bot:** Polling mode (без входящего порта)

### 📦 Volumes

\\\yaml
pgvector_data: /var/lib/postgresql/data
bot_logs: /app/logs
api_logs: /app/logs
\\\

---

## 3. FILE STRUCTURE

### 📁 Основные директории

\\\
CRD12/
├── docs/                    # Документация
│   ├── ROADMAP.yaml         # Основной Roadmap (25 задач)
│   ├── SYSTEM_PASSPORT.md   # Этот документ
│   └── SELF_BUILD_TEST_PREP.md
│
├── src/                     # Исходный код
│   ├── bot/                 # Telegram Bot
│   │   ├── bot.py           # Главный файл бота
│   │   ├── commands/        # Команды бота
│   │   │   ├── roadmap_load.py
│   │   │   ├── roadmap_generate_tz.py
│   │   │   ├── roadmap_update_status.py
│   │   │   └── roadmap_navigator.py
│   │   └── tasks/
│   │       └── task_manager.py  # Автовыбор задач
│   │
│   ├── engineer_b_api/      # FastAPI приложение
│   │   ├── app.py           # Главный файл API
│   │   ├── templates/       # Jinja2 шаблоны
│   │   │   └── navigator.html
│   │   └── static/          # CSS, JS, images
│   │
│   └── app/                 # Копии для контейнеров
│
├── config/                  # Конфигурация
│   └── (будущие манифесты)
│
├── migrations/              # SQL миграции
│   └── (будущие миграции)
│
├── tests/                   # Тесты
│   └── (будущие тесты)
│
├── docker-compose.yaml      # Оркестрация контейнеров
├── .env                     # Переменные окружения (не в git)
├── .gitignore
└── README.md
\\\

### 🔑 Ключевые файлы

| Файл | Назначение |
|------|------------|
| \docs/ROADMAP.yaml\ | Основной Roadmap (source of truth) |
| \src/bot/bot.py\ | Entry point Telegram Bot |
| \src/engineer_b_api/app.py\ | Entry point FastAPI |
| \src/bot/tasks/task_manager.py\ | Логика автовыбора задач |
| \src/bot/commands/roadmap_navigator.py\ | Команда /roadmap_navigator |
| \docker-compose.yaml\ | Конфигурация всех сервисов |

---

## 4. CONFIGURATION

### 🔐 Environment Variables (.env)

\\\ash
# Database
POSTGRES_USER=crd_user
POSTGRES_PASSWORD=crd_password
POSTGRES_DB=crd12
DATABASE_URL=postgresql://crd_user:crd_password@pgvector:5432/crd12

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# OpenAI (для LLM)
OPENAI_API_KEY=your_openai_api_key_here

# GitHub (для автоматизации)
GITHUB_TOKEN=your_github_token_here
GITHUB_REPO=arturklimovich-art/CRD_12

# API URLs
ENGINEER_B_API_URL=http://engineer_b_api:8000
API_BASE_URL=http://localhost:8001

# Logging
LOG_LEVEL=INFO
\\\

### ⚙️ docker-compose.yaml (ключевые секции)

\\\yaml
services:
  pgvector:
    image: pgvector/pgvector:pg16
    container_name: crd12_pgvector
    environment:
      POSTGRES_USER: crd_user
      POSTGRES_PASSWORD: crd_password
      POSTGRES_DB: crd12
    volumes:
      - pgvector_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  bot:
    build: ./src/bot
    container_name: crd12_bot
    depends_on:
      - pgvector
      - engineer_b_api
    env_file:
      - .env

  engineer_b_api:
    build: ./src/engineer_b_api
    container_name: crd12_engineer_b_api
    depends_on:
      - pgvector
    ports:
      - "8001:8000"
      - "8031:8030"
    env_file:
      - .env
\\\

---

## 5. DATABASE SCHEMA

### 📊 Таблицы

#### eng_it.roadmap_tasks
**Назначение:** Хранение всех задач из ROADMAP.yaml

\\\sql
CREATE TABLE eng_it.roadmap_tasks (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planned',
    priority INTEGER DEFAULT 3,
    assigned_to VARCHAR(100),
    labels TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,
    due_date DATE,
    progress_notes TEXT
);
\\\

**Статусы:** \planned\, \in_progress\, \done\, \cancelled\

#### eng_it.tasks
**Назначение:** Связь с roadmap_tasks и дополнительные атрибуты

\\\sql
CREATE TABLE eng_it.tasks (
    id SERIAL PRIMARY KEY,
    roadmap_task_id INTEGER REFERENCES eng_it.roadmap_tasks(id),
    title TEXT NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'planned',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
\\\

#### core.events
**Назначение:** Логирование всех событий системы

\\\sql
CREATE TABLE core.events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50),
    entity_id INTEGER,
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
\\\

**Типы событий:** \	ask_started\, \	ask_completed\, \	z_generated\, \status_updated\, etc.

#### eng_it.progress_navigator
**Назначение:** Детальные шаги выполнения задач (Navigator)

\\\sql
CREATE TABLE eng_it.progress_navigator (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    title TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'planned',
    done BOOLEAN DEFAULT FALSE,
    task_id INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
\\\

**Всего записей:** 74 шага

### 🔗 Связи таблиц

\\\
roadmap_tasks (1) ←─── (N) tasks
                  ↓
                events (через entity_id)
                  ↓
          progress_navigator (через task_id)
\\\

---

## 6. API REFERENCE

### 🌐 Base URL
- **Прямой:** http://localhost:8001
- **Через Nginx:** http://localhost:8031

### 📋 Endpoints

#### GET /api/roadmap
**Описание:** Получить все задачи Roadmap

**Response:**
\\\json
{
  "total_tasks": 25,
  "tasks": [
    {
      "id": 1001,
      "code": "TASK-1001",
      "title": "E1-B6 Bot v2: Self-Learning Architecture",
      "status": "done",
      "priority": 1,
      "completed_at": "2025-11-19T11:42:27+01:00"
    },
    ...
  ]
}
\\\

#### GET /api/current
**Описание:** Получить текущую задачу (статус \in_progress\ с наименьшим priority)

**Response:**
\\\json
{
  "task": {
    "id": 1012,
    "title": "E1-L8 Observability & Monitoring",
    "status": "in_progress",
    "priority": 2
  }
}
\\\

#### GET /api/navigator/steps/{task_id}
**Описание:** Получить шаги конкретной задачи

**Response:**
\\\json
{
  "task_id": 1012,
  "steps_count": 0,
  "steps": []
}
\\\

#### GET /api/navigator/all
**Описание:** Получить все 74 шага Navigator

**Response:**
\\\json
{
  "total_steps": 74,
  "steps": [...]
}
\\\

#### GET /api/truth/matrix
**Описание:** Матрица истины (статистика по статусам)

**Response:**
\\\json
{
  "status": "ok",
  "timestamp": "2025-11-19T12:28:38Z",
  "statistics": {
    "planned": 6,
    "in_progress": 3,
    "done": 16
  }
}
\\\

---

## 7. BOT COMMANDS

### 📱 Доступные команды

| Команда | Описание | Пример использования |
|---------|----------|----------------------|
| \/start\ | Приветствие | \/start\ |
| \/help\ | Список команд | \/help\ |
| \/roadmap_load\ | Загрузка ROADMAP.yaml в БД | \/roadmap_load\ |
| \/roadmap_generate_tz\ | Генерация ТЗ для задачи | \/roadmap_generate_tz 1012\ |
| \/roadmap_update_status\ | Обновление статуса задачи | \/roadmap_update_status 1012 done\ |
| \/roadmap_navigator\ | Показать текущую задачу | \/roadmap_navigator\ |

### 🔧 Внутренняя логика

#### /roadmap_navigator
\\\python
# src/bot/commands/roadmap_navigator.py
async def roadmap_navigator_command(update, context):
    # 1. GET /api/current → текущая задача
    # 2. GET /api/navigator/steps/{task_id} → шаги
    # 3. Форматирование ответа с прогресс-баром
    # 4. Отправка в Telegram
\\\

---

## 8. SELF-BUILDING CHAIN

### 🔄 Текущая реализация (работает)

\\\
1. Roadmap в БД → 2. API /api/current → 3. Bot /roadmap_navigator → 4. HTML Navigator → 5. core.events
\\\

### 🎯 Целевая цепочка (в разработке)

\\\
1. TRIGGER: task done
   ↓
2. AUTO-SELECT: task_manager.get_next_self_building_task()
   ↓
3. LLM-ANALYZE: понимание задачи
   ↓
4. LLM-PLAN: разбивка на шаги
   ↓
5. GITHUB-CREATE: issue/PR
   ↓
6. EXECUTE: изменения кода
   ↓
7. VERIFY: тесты, CI/CD
   ↓
8. COMPLETE: статус done
   ↓
9. LOOP: следующая задача
\\\

### 🧠 Task Manager

**Файл:** \src/bot/tasks/task_manager.py\

**Функция:** \get_next_self_building_task()\

**Логика:**
1. Исключить \done\, \cancelled\
2. Приоритет: \planned\ > \in_progress\
3. Сортировка по \priority\ (ASC)
4. Вернуть первую задачу

---

## 9. ROADMAP

### 📊 Статистика (всего 25 задач)

- ✅ **Done:** 16 задач (64%)
- 🔧 **In Progress:** 3 задачи (12%)
- 📋 **Planned:** 6 задач (24%)

### 🎯 Текущие задачи (in_progress)

| ID | Код | Название | Priority |
|----|-----|----------|----------|
| 1012 | TASK-1012 | E1-L8 Observability & Monitoring | 2 |
| 1013 | TASK-1013 | E1-I4 Infra-as-Code Expansion | 3 |
| 1014 | TASK-1014 | E1-S7 Security & Compliance | 3 |

### 📁 Источник
**Файл:** \docs/ROADMAP.yaml\

---

## 10. DEVELOPMENT WORKFLOW

### 🌿 Git Branches

- \main\ - стабильная ветка (production)
- \eature/*\ - разработка новых фич
- \hotfix/*\ - срочные исправления

**Текущая ветка:** \$currentBranch\

### 🔄 Как начать новую задачу

\\\ash
# 1. Создать ветку
git checkout -b feature/task-{ID}-{short-name}

# 2. Сделать изменения

# 3. Коммит
git add .
git commit -m "feat(module): description"

# 4. Push
git push origin feature/task-{ID}-{short-name}

# 5. Создать PR на GitHub
\\\

### ✅ Как завершить задачу

\\\ash
# 1. Обновить статус в БД
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "UPDATE eng_it.roadmap_tasks SET status='done', completed_at=NOW() WHERE id={ID};"

# 2. Merge PR

# 3. Удалить ветку
git branch -d feature/task-{ID}-{short-name}
\\\

---

## 11. TESTING

### 🧪 Типы тестов

- **Unit тесты:** (в разработке)
- **Integration тесты:** (в разработке)
- **E2E тесты:** Запланированы в SELF_BUILD_TEST_PREP.md

---

## 12. MONITORING & LOGGING

### 📊 core.events

**Всего событий:** 40

**Структура события:**
\\\json
{
  "event_type": "task_started",
  "entity_type": "roadmap_task",
  "entity_id": 1012,
  "data": {
    "message": "Started task 1012",
    "user": "arturklimovich-art"
  },
  "created_at": "2025-11-19T12:28:38Z"
}
\\\

### 🔍 Как посмотреть логи

\\\ash
# Последние 10 событий
docker exec crd12_pgvector psql -U crd_user -d crd12 -c "SELECT * FROM core.events ORDER BY created_at DESC LIMIT 10;"

# Логи бота
docker logs crd12_bot --tail 50

# Логи API
docker logs crd12_engineer_b_api --tail 50
\\\

---

## 13. TROUBLESHOOTING

### ❓ FAQ

**Q: Контейнер не запускается?**
\\\ash
docker-compose down
docker-compose up -d
docker logs {container_name}
\\\

**Q: БД не доступна?**
\\\ash
docker exec -it crd12_pgvector psql -U crd_user -d crd12 -c "SELECT 1;"
\\\

**Q: Bot не отвечает?**
\\\ash
docker logs crd12_bot --tail 50
# Проверить TELEGRAM_BOT_TOKEN в .env
\\\

---

## 14. DEPLOYMENT

### 🚀 Запуск с нуля

\\\ash
# 1. Клонировать репозиторий
git clone https://github.com/arturklimovich-art/CRD_12.git
cd CRD_12

# 2. Создать .env (скопировать из примера выше)
nano .env

# 3. Запустить контейнеры
docker-compose up -d

# 4. Проверить статус
docker ps

# 5. Загрузить Roadmap в БД
# Отправить /roadmap_load в Telegram Bot
\\\

---

## 📞 КОНТАКТЫ

- **GitHub:** arturklimovich-art/CRD_12
- **Branch:** feature/roadmap-arturklimovich-20251117
- **Telegram Bot:** @crd12_bot

---

**Статус Паспорта:** ✅ ПОЛНЫЙ  
**Последнее обновление:** 2025-11-19 12:28:38 UTC  
**Версия:** 1.0
