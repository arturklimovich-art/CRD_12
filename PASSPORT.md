# CRD12 — Passport (Day 1)

**Agents:** Engineer A (Telegram Bot), Engineer B (FastAPI)  
**DB:** Postgres/pgvector (порт 5433)  
**API:** http://localhost:8000/health  
**Green-corridor:** белые пути заданы; запрет на хаос с путями/портами/секретами.

Структура (каноническая):
- src/bot (Engineer A)
- src/app/engineer_b_api (Engineer B)
- agents/, tests/, scripts/, config/ports.yml
- workspace/ADR, workspace/patches, workspace/snapshots, workspace/context
## Day 2 — Memory & Artifacts

**DB tables:** tasks, messages, agent_stats, system_health (pgvector).  
**System health seed:** engineer_b_api, engineer_a_bot, pgvector.  
**Artifacts:** workspace/artifacts/SPEC_<id>.json, PLAN_<id>.md, CHECKLIST_<id>.md, RESULT_<id>.md; snapshots в workspace/snapshots.  
**Policy:** см. config/policy.yml (зелёный коридор).  
**Bootstrap:** workspace/context/bootstrap.md  
**FILES.csv:** workspace/context/FILES.csv (инвентарь проекта).


DB schema applied on 2025-10-12 09:59:03 ✅

## 📅 2025-10-12 — День 3
- Trader agent: ping() + тест.
- Артефакты: RESULT_20251012_105435.
- Время: 2025-10-12 10:54:34

## 📅 2025-10-12 — День 3
- Trader agent: ping() + тест.
- RESULT_20251012_105607.
- Время: 2025-10-12 10:56:07

## 📅 2025-10-12 — День 3
- Trader ping() + тест, pytest: PASSED (unit+sandbox)
- RESULT_20251012_110309.md
- Время: 2025-10-12 11:03:09

## 📅 2025-10-12 — День 3
- LLM/pipeline контракты задокументированы; trader: ping() + тест.
- Артефакты: RESULT_20251012_110336.md
- Время: 2025-10-12 11:03:36

## Day 3 — LLM & Trader Agent
- ✅ Подключён DeepSeek (переменные окружения, лимиты)
- ✅ Добавлен system-prompt engineer_b_system.txt
- ✅ Документирован контракт /llm/complete и /pipeline/run
- ✅ Создан каркас агента trader (README, .env.example)
- ✅ Выполнена сквозная задача /ping (ping.py + test_ping.py, тесты зелёные)
- ✅ Артефакты SPEC/PLAN/RESULT зафиксированы


Snapshot: workspace\snapshots\SNAP_20251012_112424 (created 2025-10-12 11:24:25) ✅

Snapshot: workspace\snapshots\SNAP_20251012_112516 (created 2025-10-12 11:25:16) ✅
## Security policy (Day 4)
- Запрещены опасные паттерны: rm -rf, drop database, delete from, password, api_key, token
- Sandbox timeout = 15 секунд

Snapshot Day 4: workspace\snapshots\SNAP_20251012_120028 (created 2025-10-12 12:00:29) ✅
## Самолечение
- Снапшоты: tar.gz архивы с \src\, \config\, \docker-compose.yml\
- Таблицы: \snapshots\, \ecovery_logs\
- 3 уровня восстановления:
  - quick restart (docker compose restart service)
  - snapshot restore (tar.gz)
  - rebuild (пересборка контейнеров и повторная инициализация)

[Day 7] 2025-10-13 19:34:55 — engineer_b_api healthy, bot запущен, тесты пройдены. ✅
