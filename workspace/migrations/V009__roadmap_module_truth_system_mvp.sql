-- =====================================================================
-- Migration V009: Roadmap Module - Truth System (MVP)
-- =====================================================================
-- Purpose: Создать структуру для модуля истины Roadmap
-- Date: 2025-11-12
-- Author: arturklimovich-art
-- Version: MVP (3 tables: blocks, tasks, events)
-- =====================================================================

-- =====================================================================
-- 1. ROADMAP BLOCKS (блоки: E1-L*, E1-B*, TL*)
-- =====================================================================
CREATE TABLE IF NOT EXISTS eng_it.roadmap_blocks (
    id              BIGSERIAL PRIMARY KEY,
    code            TEXT UNIQUE NOT NULL,        -- 'E1-L1', 'E1-B13', 'TL1-AGENT'
    title           TEXT NOT NULL,
    stage           TEXT NOT NULL,               -- 'E1', 'TL1', 'E2'
    kind            TEXT NOT NULL,               -- 'L' (Learning), 'B' (Building), 'TL' (TradLab)
    status          TEXT NOT NULL DEFAULT 'planned', -- planned|in_progress|done|archived
    priority        INTEGER NOT NULL DEFAULT 100,
    description     TEXT,
    meta            JSONB,                       -- Дополнительные данные (dependencies, tags, etc.)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT roadmap_blocks_status_check 
        CHECK (status IN ('planned', 'in_progress', 'done', 'archived')),
    CONSTRAINT roadmap_blocks_kind_check 
        CHECK (kind IN ('L', 'B', 'TL', 'OTHER'))
);

CREATE INDEX idx_roadmap_blocks_code ON eng_it.roadmap_blocks(code);
CREATE INDEX idx_roadmap_blocks_status ON eng_it.roadmap_blocks(status);
CREATE INDEX idx_roadmap_blocks_stage ON eng_it.roadmap_blocks(stage);

COMMENT ON TABLE eng_it.roadmap_blocks IS 
    'Блоки Roadmap (E1-L*, E1-B*, TL*) - стратегические элементы плана';
COMMENT ON COLUMN eng_it.roadmap_blocks.code IS 
    'Уникальный код блока (E1-L1, E1-B13, TL1-AGENT)';
COMMENT ON COLUMN eng_it.roadmap_blocks.kind IS 
    'Тип блока: L=Learning, B=Building, TL=TradLab';
COMMENT ON COLUMN eng_it.roadmap_blocks.meta IS 
    'JSONB для зависимостей, тегов, links и других метаданных';

-- =====================================================================
-- 2. ROADMAP TASKS (задачи внутри блоков)
-- =====================================================================
CREATE TABLE IF NOT EXISTS eng_it.roadmap_tasks (
    id              BIGINT PRIMARY KEY,          -- ID задачи (1001, 1002, ...) - совпадает с eng_it.tasks
    block_id        BIGINT REFERENCES eng_it.roadmap_blocks(id) ON DELETE SET NULL,
    code            TEXT NOT NULL,               -- 'E1-B13-IMPL', 'E1-L1-SETUP'
    title           TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'planned', -- planned|in_progress|done|failed|blocked
    kind            TEXT NOT NULL DEFAULT 'task',    -- task|subtask|epic
    priority        INTEGER NOT NULL DEFAULT 100,
    description     TEXT,
    tz_ref          TEXT,                        -- Ссылка на ТЗ (docs/TZ/...)
    steps           JSONB,                       -- Шаги задачи (MVP: хранится как JSON)
    mechanisms      JSONB,                       -- Механизмы реализации (файлы, таблицы, endpoints)
    artifacts       JSONB,                       -- Артефакты (код, логи, снапшоты)
    meta            JSONB,                       -- Дополнительные данные
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    
    CONSTRAINT roadmap_tasks_status_check 
        CHECK (status IN ('planned', 'in_progress', 'done', 'failed', 'blocked', 'removed')),
    CONSTRAINT roadmap_tasks_kind_check 
        CHECK (kind IN ('task', 'subtask', 'epic', 'milestone'))
);

CREATE INDEX idx_roadmap_tasks_block ON eng_it.roadmap_tasks(block_id);
CREATE INDEX idx_roadmap_tasks_status ON eng_it.roadmap_tasks(status);
CREATE INDEX idx_roadmap_tasks_code ON eng_it.roadmap_tasks(code);
CREATE INDEX idx_roadmap_tasks_priority ON eng_it.roadmap_tasks(priority DESC);

COMMENT ON TABLE eng_it.roadmap_tasks IS 
    'Задачи Roadmap с привязкой к блокам и детальным описанием реализации';
COMMENT ON COLUMN eng_it.roadmap_tasks.id IS 
    'ID задачи (совпадает с eng_it.tasks.id для совместимости)';
COMMENT ON COLUMN eng_it.roadmap_tasks.steps IS 
    'JSONB массив шагов: [{code, title, status, done}, ...]';
COMMENT ON COLUMN eng_it.roadmap_tasks.mechanisms IS 
    'JSONB массив механизмов: [{kind, ref, description}, ...] (kind: file|table|service|endpoint)';
COMMENT ON COLUMN eng_it.roadmap_tasks.artifacts IS 
    'JSONB массив артефактов: [{kind, ref, created_at}, ...] (kind: tz|code|ddl|snapshot|log)';

-- =====================================================================
-- 3. ROADMAP EVENTS (история всех изменений Roadmap)
-- =====================================================================
CREATE TABLE IF NOT EXISTS eng_it.roadmap_events (
    id              BIGSERIAL PRIMARY KEY,
    entity_type     TEXT NOT NULL,               -- 'block'|'task'
    entity_id       BIGINT NOT NULL,             -- ID блока или задачи
    event_type      TEXT NOT NULL,               -- created|status_changed|updated|tz_generated|impl_started|impl_done|archived
    old_value       JSONB,                       -- Старое значение (для изменений)
    new_value       JSONB,                       -- Новое значение
    changed_by      TEXT DEFAULT 'system',       -- manual|telegram_bot|api|system
    meta            JSONB,                       -- Дополнительный контекст
    ts              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT roadmap_events_entity_type_check 
        CHECK (entity_type IN ('block', 'task'))
);

CREATE INDEX idx_roadmap_events_entity ON eng_it.roadmap_events(entity_type, entity_id);
CREATE INDEX idx_roadmap_events_type ON eng_it.roadmap_events(event_type);
CREATE INDEX idx_roadmap_events_ts ON eng_it.roadmap_events(ts DESC);

COMMENT ON TABLE eng_it.roadmap_events IS 
    'История всех изменений Roadmap (event sourcing)';
COMMENT ON COLUMN eng_it.roadmap_events.entity_type IS 
    'Тип сущности: block (roadmap_blocks) или task (roadmap_tasks)';
COMMENT ON COLUMN eng_it.roadmap_events.event_type IS 
    'Тип события: created, status_changed, updated, tz_generated, impl_started, impl_done, archived';

-- =====================================================================
-- 4. СВЯЗЬ С СУЩЕСТВУЮЩЕЙ ТАБЛИЦЕЙ eng_it.tasks
-- =====================================================================
-- Добавляем поле roadmap_task_id для обратной совместимости
ALTER TABLE eng_it.tasks 
ADD COLUMN IF NOT EXISTS roadmap_task_id BIGINT 
REFERENCES eng_it.roadmap_tasks(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_tasks_roadmap_task 
ON eng_it.tasks(roadmap_task_id);

COMMENT ON COLUMN eng_it.tasks.roadmap_task_id IS 
    'Связь с roadmap_tasks для интеграции старых задач с новым Roadmap Module';

-- =====================================================================
-- 5. VIEW: Полная картина Roadmap
-- =====================================================================
CREATE OR REPLACE VIEW eng_it.v_roadmap_full AS
SELECT 
    rb.id as block_id,
    rb.code as block_code,
    rb.title as block_title,
    rb.status as block_status,
    rb.stage,
    rb.kind as block_kind,
    rt.id as task_id,
    rt.code as task_code,
    rt.title as task_title,
    rt.status as task_status,
    rt.priority as task_priority,
    rt.tz_ref,
    rt.steps,
    rt.mechanisms,
    rt.artifacts,
    rt.created_at as task_created_at,
    rt.updated_at as task_updated_at,
    rt.completed_at as task_completed_at,
    t.id as legacy_task_id,
    t.status as legacy_status
FROM eng_it.roadmap_blocks rb
LEFT JOIN eng_it.roadmap_tasks rt ON rt.block_id = rb.id
LEFT JOIN eng_it.tasks t ON t.roadmap_task_id = rt.id
ORDER BY rb.stage, rb.priority, rt.priority;

COMMENT ON VIEW eng_it.v_roadmap_full IS 
    'Полная картина Roadmap: блоки → задачи → связь с legacy eng_it.tasks';

-- =====================================================================
-- 6. VIEW: Dashboard для Bot
-- =====================================================================
CREATE OR REPLACE VIEW eng_it.v_roadmap_dashboard AS
SELECT 
    rb.code as block_code,
    rb.title as block_title,
    rb.status as block_status,
    COUNT(rt.id) as total_tasks,
    COUNT(rt.id) FILTER (WHERE rt.status = 'done') as done_tasks,
    COUNT(rt.id) FILTER (WHERE rt.status = 'in_progress') as in_progress_tasks,
    COUNT(rt.id) FILTER (WHERE rt.status = 'planned') as planned_tasks,
    ROUND(
        CAST(COUNT(rt.id) FILTER (WHERE rt.status = 'done') AS DECIMAL) / 
        NULLIF(COUNT(rt.id), 0) * 100, 
        2
    ) as completion_percentage
FROM eng_it.roadmap_blocks rb
LEFT JOIN eng_it.roadmap_tasks rt ON rt.block_id = rb.id
GROUP BY rb.id, rb.code, rb.title, rb.status, rb.priority
ORDER BY rb.priority;

COMMENT ON VIEW eng_it.v_roadmap_dashboard IS 
    'Dashboard для Bot: прогресс по блокам с метриками выполнения';

-- =====================================================================
-- ЗАВЕРШЕНИЕ МИГРАЦИИ
-- =====================================================================
-- Логирование успешного применения миграции
INSERT INTO eng_it.roadmap_events (entity_type, entity_id, event_type, changed_by, meta)
VALUES ('block', 0, 'migration_v009_applied', 'system', 
    '{"migration": "V009", "tables_created": ["roadmap_blocks", "roadmap_tasks", "roadmap_events"], "timestamp": "2025-11-12T00:42:39Z"}'::jsonb
);

-- =====================================================================
-- END OF MIGRATION V009
-- =====================================================================
