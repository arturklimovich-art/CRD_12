\# TL-B8-T4 — DB Optimization: DatabaseManager \& Trades Upsert



Дата: 2025-11-25  

Автор: arturklimovich-art



\## Краткое резюме (что было сделано)

\- Реализована надёжная запись сделок в `lab.trades` с ON CONFLICT (prevents duplicates by run\_id, entry\_ts, strategy\_id, side).

\- Обработка полей: корректная обработка `pnl\_pct` (None -> NULL), безопасный доступ к полям через `.get()`, корректная обработка `meta` как JSON.

\- Добавлен upsert минимального summary в `lab.results` для соответствующего `run\_id`.

\- Добавлены защиты от дубликатов и аккумулирование `meta` (merge JSONB).

\- Улучшена обработка ошибок и логирование (лог события в `eng\_it.roadmap\_events` для CRD12).

\- Тестовые запросы показали корректные вставки (последние 5 сделок выводятся корректно).



\## Почему это важно

\- Улучшает качество данных (нет дубликатов).

\- Позволяет аккумулировать метаданные (meta) по мере поступления новых данных.

\- Создаёт трассируемый след в Roadmap (через событие в `eng\_it.roadmap\_events`) — легко аудировать.



\## Что зафиксировать в Roadmap

\- Новая задача в домене TL: код `TL-B8-T4`

&nbsp; - Название: `DB Optimization: DatabaseManager \& trades upsert`

&nbsp; - Статус: `done`

&nbsp; - Приоритет: 25

&nbsp; - Описание: краткое содержание (см. этот файл), ссылки на добавленные скрипты и команды воспроизведения.



\## Список добавленных файлов

\- agents/EngineersIT.Bot/record\_session.ps1

\- agents/EngineersIT.Bot/sql/insert\_or\_update\_trade.sql

\- agents/EngineersIT.Bot/sql/insert\_roadmap\_tl\_b8\_t4.sql

\- agents/EngineersIT.Bot/reports/TL-B8-T4-db-optimization.md



\## Команды для проверки (после выполнения)

1\. Проверка вставок в `lab.trades`:

&nbsp;  docker exec -i tradlab\_postgres psql -U tradlab -d tradlab\_db -c "SELECT run\_id, strategy\_id, entry\_ts, side, price, qty, pnl\_pct, meta FROM lab.trades WHERE run\_id='STR-100\_20251125\_155147\_453493ed' ORDER BY entry\_ts DESC LIMIT 5;"

2\. Проверка summary:

&nbsp;  docker exec -i tradlab\_postgres psql -U tradlab -d tradlab\_db -c "SELECT run\_id, pnl\_total, sharpe, meta FROM lab.results WHERE run\_id='STR-100\_20251125\_155147\_453493ed';"

3\. Проверка события в roadmap\_events:

&nbsp;  docker exec -i crd12\_pgvector psql -U crd\_user -d crd12 -c "SELECT event\_type, changed\_by, meta, ts FROM eng\_it.roadmap\_events ORDER BY ts DESC LIMIT 10;"

