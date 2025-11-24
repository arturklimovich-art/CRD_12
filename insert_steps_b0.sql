INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T1-S1', 'Запуск контейнера tradlab', 'done', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T1-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T1-S2', 'Проверка базовой работоспособности', 'done', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T1-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T1-S3', 'Документирование Quick Start', 'done', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T1'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T1-S3');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T2-S1', 'Реализация STR-100 ChainFlow', 'done', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T2-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T2-S2', 'Бэктест на демо-данных', 'done', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T2-S2');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T2-S3', 'Проверка метрик', 'done', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T2'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T2-S3');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T3-S1', 'Создание TL_GENERAL_PLAN.yaml', 'done', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T3'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T3-S1');

INSERT INTO eng_it.roadmap_steps (domain_code, task_id, code, title, status, priority)
SELECT 'TL', rt.id, 'E2-TL-B0-T3-S2', 'Синхронизация roadmap с БД', 'in_progress', 100
FROM eng_it.roadmap_tasks rt WHERE rt.code = 'E2-TL-B0-T3'
AND NOT EXISTS (SELECT 1 FROM eng_it.roadmap_steps WHERE code = 'E2-TL-B0-T3-S2');

SELECT 'Итого шагов для B0' AS info, COUNT(*) AS count 
FROM eng_it.roadmap_steps rs
JOIN eng_it.roadmap_tasks rt ON rs.task_id = rt.id
WHERE rt.code IN ('E2-TL-B0-T1', 'E2-TL-B0-T2', 'E2-TL-B0-T3');
