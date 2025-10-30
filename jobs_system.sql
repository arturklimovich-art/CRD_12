-- Создаем таблицу jobs если не существует
CREATE TABLE IF NOT EXISTS core.jobs (
    job_id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ NULL,
    finished_at TIMESTAMPTZ NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
    source TEXT NOT NULL,
    task_type TEXT NOT NULL,
    meta JSONB NULL,
    result JSONB NULL,
    error_message TEXT NULL
);

-- Индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_jobs_created ON core.jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON core.jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_source ON core.jobs(source);

-- Представление для удобного отслеживания заданий
CREATE OR REPLACE VIEW core.jobs_overview AS
SELECT 
    job_id,
    created_at,
    started_at,
    finished_at,
    status,
    source,
    task_type,
    meta,
    CASE 
        WHEN finished_at IS NOT NULL THEN 
            EXTRACT(EPOCH FROM (finished_at - started_at))
        ELSE NULL
    END as duration_seconds,
    error_message
FROM core.jobs
ORDER BY created_at DESC;

-- Функция для создания нового задания
CREATE OR REPLACE FUNCTION core.create_job(
    p_job_id TEXT,
    p_source TEXT,
    p_task_type TEXT,
    p_meta JSONB DEFAULT NULL
) RETURNS core.jobs AS Cyan
DECLARE
    new_job core.jobs;
BEGIN
    INSERT INTO core.jobs (job_id, status, source, task_type, meta)
    VALUES (p_job_id, 'pending', p_source, p_task_type, p_meta)
    RETURNING * INTO new_job;
    
    RETURN new_job;
END;
Cyan LANGUAGE plpgsql;

-- Функция для обновления статуса задания
CREATE OR REPLACE FUNCTION core.update_job_status(
    p_job_id TEXT,
    p_status TEXT,
    p_result JSONB DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
) RETURNS core.jobs AS Cyan
DECLARE
    updated_job core.jobs;
BEGIN
    UPDATE core.jobs 
    SET 
        status = p_status,
        result = p_result,
        error_message = p_error_message,
        started_at = CASE WHEN p_status = 'running' AND started_at IS NULL THEN now() ELSE started_at END,
        finished_at = CASE WHEN p_status IN ('success', 'failed', 'cancelled') THEN now() ELSE finished_at END
    WHERE job_id = p_job_id
    RETURNING * INTO updated_job;
    
    RETURN updated_job;
END;
Cyan LANGUAGE plpgsql;
