# Bootstrap CRD12 (Day 2)
Проект: CRD12
Агенты: Engineer A (Telegram Bot), Engineer B (FastAPI)
БД: Postgres+pgvector (порт 5433)
API: http://localhost:8000/health

Источники истины:
- Список файлов: workspace/context/FILES.csv
- Артефакты: SPEC/PLAN/CHECKLIST/RESULT/SNAPSHOT/PASSPORT
- ADR (архитектурные решения)

Правила:
- Только allowed_roots (см. config/policy.yml)
- Нет дубликатов src/, tests/
- Запрещены опасные строки (rm -rf, drop database, …)
- Docker/сеть/БД-схема = high-risk, требуют ручного гейта
## Безопасность
- Опасные строки (rm -rf, drop database, delete from, password, api_key, token) запрещены.
- Sandbox timeout = 15 секунд.
