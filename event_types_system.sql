-- SQL: Создаем справочник типов событий для системы
INSERT INTO core.event_types (type_name, description, category) VALUES 
('ANALYZE_OK', 'Успешный анализ задачи', 'analysis'),
('ANALYZE_ERROR', 'Ошибка анализа задачи', 'analysis'),
('PATCH_ATTEMPT', 'Попытка применения патча', 'patch'),
('PATCH_APPLIED', 'Патч успешно применен', 'patch'), 
('PATCH_ROLLBACK', 'Откат патча из-за ошибки', 'patch'),
('RECOVERY_OK', 'Успешное восстановление системы', 'recovery'),
('RECOVERY_ATTEMPT', 'Попытка восстановления', 'recovery'),
('SMOKE_OK', 'Smoke-тест пройден', 'health'),
('SMOKE_FAILED', 'Smoke-тест не пройден', 'health'),
('SERVICE_STARTED', 'Сервис запущен', 'system'),
('SERVICE_STOPPED', 'Сервис остановлен', 'system'),
('HEALTH_CHECK_OK', 'Health check пройден', 'health'),
('HEALTH_CHECK_FAILED', 'Health check не пройден', 'health'),
('JOB_CREATED', 'Задача создана', 'job'),
('JOB_COMPLETED', 'Задача завершена', 'job'),
('JOB_FAILED', 'Задача завершена с ошибкой', 'job'),
('DATABASE_BACKUP_CREATED', 'Создан backup БД', 'backup'),
('AUTO_RECOVERY_TRIGGERED', 'Запущено авто-восстановление', 'recovery');

-- Создаем представление для удобного анализа событий
CREATE OR REPLACE VIEW core.events_overview AS
SELECT 
    e.id,
    e.ts,
    e.source,
    e.type,
    e.job_id,
    et.category,
    et.description as type_description,
    e.payload
FROM core.events e
LEFT JOIN core.event_types et ON e.type = et.type_name
ORDER BY e.ts DESC;
