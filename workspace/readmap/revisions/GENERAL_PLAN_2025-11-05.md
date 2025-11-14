🎯 Цель Этапа 1

Создать фундаментальную, самодостаточную версию системы Engineers_IT, способную:

принимать ТЗ от Orchestrator (Bot),

генерировать и безопасно применять код (Engineer_B),

логировать события и хранить историю (Event Sourcing),

восстанавливаться после ошибок (Self-Recovery),

вести централизованный контроль статусов (Navigator DB),

и формировать единый снимок текущего состояния системы для всех агентов.

После завершения Этапа 1 система должна обеспечивать цикл:

создание → тест → применение → лог → откат → снапшот → обновление базы знаний

📁 Пути проекта
C:\Users\Artur\Documents\CRD12\
├─ agents\EngineersIT.Bot\          # PowerShell-пульт
├─ src\bot\                         # Bot (REST/API)
├─ src\engineer_b\                  # Engineer_B (исполнитель)
├─ src\kurator\                     # Curator
├─ ROADMAP\                         # GENERAL_PLAN.md|yaml (истина)
├─ SPEC\                            # спецификации
├─ docs\TZ\                         # ТЗ и индекс SPEC_INDEX.yaml
├─ DB\                              # DDL/VIEW
├─ memory\                          # compose для LLM
├─ scripts\                         # служебные утилиты
├─ tests\                           # e2e/acceptance
├─ workspace\                       # артефакты, снапшоты, отчёты
└─ backups\                         # резервные копии


Зелёный коридор:
/app/agents/, /app/src/engineer_b_api/, /app/src/bot/, /app/workspace/patches/, /app/workspace/ADR/, /app/workspace/snapshots/.

Стек: Python 3.11 | PostgreSQL (pgvector) | Docker Compose (WSL2) | pytest | Grafana (datasource = Postgres)

⚙️ Служебные параметры

БД DSN: postgres://crd_user:crd12@localhost:5433/crd12
Namespaces событий: ps.patch.*, eng.apply_patch.*, plan.*, navigator.*, readmap.*, bot.*, llm.*, curator.*, audit.system.*
Общие DoD (S-0): smoke-тесты пройдены | артефакты и логи записаны | снапшот создан | статусы зафиксированы в Навигаторе.

🧩 Этап-1 (L1) — основные блоки
E1-L1 — Паспорт / ADR / Зелёный коридор

Артефакты: ROADMAP\GENERAL_PLAN.md|yaml, ADR\*, SPEC\STATUS_PANEL.md.
DoD: файлы присутствуют; коридор в конфиге; Bot читает версию плана.

E1-L2 — Navigator DB (структуры и статусы)

Таблицы: eng_it.tasks, eng_it.job_queue, eng_it.artifacts, eng_it.task_history.
Вьюхи: v_unresolved_tasks, v_curator_dashboard.
DoD: статусы меняются, история видна, события navigator.* пишутся.

E1-L3 — Снапшоты и откаты (Light)

Инструменты: pg_dump/pg_restore + архив кода; лог в core.events.
DoD: snapshot→restore работает; событие snapshot.done.

E1-L4 — Само-патч с авто-откатом (без rebuild)

Процесс: патч→smoke→rollback; процесс-рестарт без rebuild.
DoD: битый патч → rolled_back, сервисы живы.

E1-L5 — Контракты интеграций (минимум)

Спеки: SPEC\STRATEGY_ABI.md, SPEC\DATA_CONTRACT.md, SPEC\JOB_API.md.
DoD: валидны, моки доступны, plan.contracts.loaded.

E1-L6 — Жизненный цикл (FSM)

Стадии: IDEA→SPEC→PLAN→CODE→TEST→RESULT→SNAPSHOT.
DoD: 3 тест-задачи прошли цикл; журнал полный.

E1-L7 — Демо-поток стратегий (3–4)

Реестр strategies; backtest stub + paper-executor stub.
DoD: минимум 3 стратегии прошли демо; статусы в Навигаторе.

E1-L8 — Наблюдаемость и журналы

Логи JSON→БД + файл; вьюхи сводок.
DoD: сводка доступна, ключевые события отражаются.

🔄 Промежуточные 7 задач (до TL1)
КодНазваниеСтатусКлючевые DoD
E1-B9Контур А (PowerShell агенты)✅ DONESPEC HANDSHAKE_POWERSHELL.md ; approve_token ; идемпотентный лог.
E1-B6Bot v2 (Интеллектуальный планировщик)✅ DONEПолный цикл ТЗ→План→Очередь→Мониторинг ; интеграция с Curator.
E1-B7Bot v3 (Менеджер Roadmap/Readmap)✅ DONEReadmap загружается, ревизии и drift отслеживаются.
E1-B8Загрузка и инициализация Roadmap🕓 PLANNEDRoadmap читает структуру E↔TL ; ошибок парсинга нет.
E1-B11Local LLM Stack (Ollama + proxy)🕓 PLANNED/HIGH/v1/chat/completions локально; метрики llm.* в БД.
E1-B12Telegram-интеграция (2 режима)🕓 PLANNED/start меню, /tasks
E1-B10Curator v1→v3 (triage/spec-repair/policy)🕓 PLANNEDТаблицы curator ; статусы triage/RCA фиксируются.
🆕 E1-B13 — System Snapshot & Knowledge Sync (новая задача)

Цель:
Создать и регулярно обновлять базу знаний о структуре системы, чтобы все агенты (Bot, Engineer_B, Curator) имели единое представление об актуальной архитектуре, путях, таблицах, протоколах и ENV-параметрах.

Шаги реализации:

Создать модуль scripts/system_snapshot.py (или PowerShell вариант agents/EngineersIT.Bot/System-Snapshot.ps1).

Снимать метаданные:

таблицы БД (PostgreSQL schemas, views, triggers, functions),

пути проектов и структуру папок,

список сервисов Compose и их порты,

конфигурации ENV и DSN,

активные агенты и их эндпоинты,

контрольные события из core.events (по namespace).

Сохранять результат в workspace\reports\AUDIT_E1_FULL\SYSTEM_PASSPORT.json и ARCHITECTURE_MAP.md.

Загружать эти данные в Navigator DB (таблицы eng_it.system_snapshot, eng_it.components) для аналитики.

Добавить автообновление при изменении статуса задачи на done (через Bot Hook или Roadmap-SetStatus.ps1).

Обеспечить доступ через эндпоинт /system/info (для Curator и Engineer_B_API).

Встроить обновление в ежедневный cron (или Task Scheduler).

Артефакты:

SPEC\SYSTEM_SNAPSHOT.md

DB\SYSTEM_SNAPSHOT_SCHEMA.sql

workspace\reports\AUDIT_E1_FULL\SYSTEM_PASSPORT.json

workspace\reports\ARCHITECTURE_MAP.md

DoD:

Файлы SYSTEM_PASSPORT.json и ARCHITECTURE_MAP.md создаются и обновляются.

При каждом SetStatus на done фиксируется новый снимок.

Все агенты могут читать структуру через API или Navigator DB.

Логируется событие audit.system.snapshot_created.

При сравнении двух версий паспорта различия (добавленные/удалённые компоненты) отражаются в журнале.

✅ Финальные приёмочные тесты

snapshot→restore (Light) — PASS, snapshot.done.

Битый патч → eng.apply_patch.rolled_back, /ready зелёный.

3 тест-задачи проходят FSM до SNAPSHOT.

Демо-поток стратегий завершён; статусы в Навигаторе.

E1-B6, B7, B9 — DONE; E1-B8..B12 в работе.

E1-B13 — System Snapshot создан и доступен через API.

🧠 Риски и ограничения

6 ГБ VRAM → по умолчанию FAST профиль LLM.

Изменение Roadmap — только через Bot v3 (Readmap-Edit/SetStatus).

Секреты .env не попадают в Git и в отчёты.

Snapshot-механизм не редактирует систему, только чтение.

📍Выход Этапа 1:
Все DoD выполнены (по E1 и B-задачам), система самопроверяема, самовосстанавливаема и имеет актуальную базу знаний, которую используют все агенты для точных действий и анализа.

