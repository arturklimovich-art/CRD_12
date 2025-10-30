-- Проверяем текущую структуру таблицы jobs
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_schema = 'core' AND table_name = 'jobs';

-- Удаляем таблицу если она существует с неправильной структурой
DROP TABLE IF EXISTS core.jobs CASCADE;

-- Создаем таблицу с правильной структурой
CREATE TABLE core.jobs (
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

-- Создаем индексы
CREATE INDEX idx_jobs_created ON core.jobs(created_at DESC);
CREATE INDEX idx_jobs_status ON core.jobs(status);
CREATE INDEX idx_jobs_source ON core.jobs(source);

-- Проверяем создание
SELECT 'Table core.jobs created successfully' as result;
