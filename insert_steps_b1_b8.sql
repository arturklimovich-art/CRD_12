-- Блок B1 (3 шага для задачи E1-B1-T1)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B1-T1-S1', 'PASSPORT и шаблоны', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B1-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B1-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B1-T1-S2', 'Контракты данных и Strategy-ABI', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B1-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B1-T1-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B1-T1-S3', 'Стандартизация отчётов', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B1-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B1-T1-S3');

-- Блок B2 (5 шагов: T1=3, T2=2)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B2-T1-S1', 'Проектирование таблиц временных рядов', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B2-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B2-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B2-T1-S2', 'Миграция и индексы', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B2-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B2-T1-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B2-T1-S3', 'Валидация схемы', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B2-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B2-T1-S3');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B2-T2-S1', 'Парсинг исторических данных ETH', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B2-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B2-T2-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B2-T2-S2', 'Smoke-тест инжеста OHLCV', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B2-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B2-T2-S2');

-- Блок B3 (5 шагов: T1=2, T2=3)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B3-T1-S1', 'Спецификация Strategy-ABI', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B3-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B3-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B3-T1-S2', 'Базовый класс-контракт', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B3-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B3-T1-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B3-T2-S1', 'Реализация ChainFlow (ETH)', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B3-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B3-T2-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B3-T2-S2', 'Реализация логики STR-100', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B3-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B3-T2-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B3-T2-S3', 'Unit-тесты для STR-100', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B3-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B3-T2-S3');

-- Блок B4 (4 шага: T1=2, T2=2)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B4-T1-S1', 'Backtester CLI v1', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B4-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B4-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B4-T1-S2', 'Бэктест STR-100 на OHLCV', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B4-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B4-T1-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B4-T2-S1', 'Walk-Forward CLI v1', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B4-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B4-T2-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B4-T2-S2', 'Прогон WF для STR-100', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B4-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B4-T2-S2');

-- Блок B5 (3 шага: T1=2, T2=1)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B5-T1-S1', 'Реализация MinTRL / PSR / DSR', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B5-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B5-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B5-T1-S2', 'Применение фильтров к STR-100', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B5-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B5-T1-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B5-T2-S1', 'Mini-PBO для STR-100', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B5-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B5-T2-S1');

-- Блок B6 (2 шага для задачи E1-B6-T1)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B6-T1-S1', 'CLI для запуска пайплайна TL', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B6-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B6-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B6-T1-S2', 'Интеграция всех компонентов L1', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B6-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B6-T1-S2');

-- Блок B7 (2 шага для задачи E1-B7-T1)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B7-T1-S1', 'Настройка логирования', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B7-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B7-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B7-T1-S2', 'Дашборд метрик (Grafana)', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B7-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B7-T1-S2');

-- Блок B8 (5 шагов: T1=2, T2=3)
INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B8-T1-S1', 'Конфиг демо-биржи', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B8-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B8-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B8-T1-S2', 'Клиент демо-биржи', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B8-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B8-T1-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B8-T2-S1', 'Маппинг сигналов STR-100', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B8-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B8-T2-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B8-T2-S2', 'Отправка ордеров на демо-биржу', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B8-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B8-T2-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E1-B8-T2-S3', 'E2E-тест Demo-Executor', 'planned', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E1-B8-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E1-B8-T2-S3');

-- Финальная проверка всех шагов
SELECT 'Всего шагов в домене TL' AS info, COUNT(*) AS count 
FROM eng_it.roadmap_steps rs
JOIN eng_it.roadmap_tasks rt ON rs.task_id = rt.id
JOIN eng_it.roadmap_blocks rb ON rt.block_id = rb.id
WHERE rb.domain_code = 'TL';
