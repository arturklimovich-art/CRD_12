-- ============================================================================
-- Миграция: 20251123_001_sot_foundation.sql
-- Задача: E1-B0-T1-S1 - SQL-миграция Core-каталога доменов
-- Автор: arturklimovich-art
-- Дата: 2025-11-23
-- Описание: Добавление федеративной модели SoT (Source of Truth)
-- ============================================================================

-- 1. ТАБЛИЦА: sot_domains - Каталог доменов (ENG, TL, ...)
-- ============================================================================
CREATE TABLE IF NOT EXISTS eng_it.sot_domains (
  id          BIGSERIAL PRIMARY KEY,
  code        TEXT UNIQUE NOT NULL,           -- 'ENG', 'TL'
  title       TEXT NOT NULL,                  -- 'Engineers_IT', 'TradLab'
  owner       TEXT NOT NULL,                  -- Email ответственного
  api_base    TEXT NOT NULL,                  -- REST endpoint домена (будущее)
  plan_path   TEXT NOT NULL,                  -- ROADMAP/DOMAINS/TL/GENERAL_PLAN.yaml
  status      TEXT NOT NULL DEFAULT 'active', -- active|archived|planned
  meta        JSONB DEFAULT '{}',             -- Произвольные поля
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE eng_it.sot_domains IS 'Каталог доменов системы (федеративная модель SoT)';
COMMENT ON COLUMN eng_it.sot_domains.code IS 'Уникальный код домена (ENG, TL)';
COMMENT ON COLUMN eng_it.sot_domains.plan_path IS 'Путь к GENERAL_PLAN.yaml домена';

-- Индекс для быстрого поиска по статусу
CREATE INDEX IF NOT EXISTS idx_sot_domains_status ON eng_it.sot_domains(status);

-- ============================================================================
-- 2. ТАБЛИЦА: sot_entries - Реестр артефактов домена
-- ============================================================================
CREATE TABLE IF NOT EXISTS eng_it.sot_entries (
  id          BIGSERIAL PRIMARY KEY,
  domain_code TEXT NOT NULL REFERENCES eng_it.sot_domains(code) ON DELETE CASCADE,
  kind        TEXT NOT NULL,   -- 'roadmap','passport','spec','data','report','code','sql'
  ref_uri     TEXT NOT NULL,   -- file://..., sot://TL/task/123, http://...
  version     TEXT,            -- Git commit hash или версия
  title       TEXT,
  description TEXT,
  meta        JSONB DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE eng_it.sot_entries IS 'Реестр всех артефактов домена (файлы, спеки, отчёты)';
COMMENT ON COLUMN eng_it.sot_entries.kind IS 'Тип артефакта: roadmap, passport, spec, data, report, code, sql';
COMMENT ON COLUMN eng_it.sot_entries.ref_uri IS 'URI ссылки на артефакт (file://, sot://, http://)';

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_sot_entries_domain_kind ON eng_it.sot_entries(domain_code, kind);
CREATE INDEX IF NOT EXISTS idx_sot_entries_ref_uri ON eng_it.sot_entries(ref_uri);

-- ============================================================================
-- 3. ТАБЛИЦА: sot_sync - История синхронизации YAML ↔ БД
-- ============================================================================
CREATE TABLE IF NOT EXISTS eng_it.sot_sync (
  id          BIGSERIAL PRIMARY KEY,
  domain_code TEXT REFERENCES eng_it.sot_domains(code) ON DELETE CASCADE,
  sync_type   TEXT NOT NULL,   -- 'yaml_to_db', 'db_to_yaml', 'snapshot'
  last_hash   TEXT,            -- SHA256 хэш YAML-файла
  last_synced TIMESTAMPTZ NOT NULL DEFAULT now(),
  diff_json   JSONB DEFAULT '{}',  -- Что изменилось (diff)
  status      TEXT NOT NULL,   -- 'success', 'error', 'conflict'
  error_msg   TEXT,            -- Сообщение об ошибке (если status='error')
  meta        JSONB DEFAULT '{}'
);

COMMENT ON TABLE eng_it.sot_sync IS 'История синхронизации YAML-файлов с БД';
COMMENT ON COLUMN eng_it.sot_sync.sync_type IS 'Тип синхронизации: yaml_to_db, db_to_yaml, snapshot';
COMMENT ON COLUMN eng_it.sot_sync.last_hash IS 'SHA256 хэш файла для проверки изменений';

-- Индекс для поиска последней синхронизации домена
CREATE INDEX IF NOT EXISTS idx_sot_sync_domain_time ON eng_it.sot_sync(domain_code, last_synced DESC);

-- ============================================================================
-- 4. РАСШИРЕНИЕ: roadmap_blocks - Добавление domain_code
-- ============================================================================
ALTER TABLE eng_it.roadmap_blocks
  ADD COLUMN IF NOT EXISTS domain_code TEXT NOT NULL DEFAULT 'ENG';

COMMENT ON COLUMN eng_it.roadmap_blocks.domain_code IS 'Код домена (ENG, TL) для мультидоменной системы';

-- Индекс для фильтрации по домену
CREATE INDEX IF NOT EXISTS idx_roadmap_blocks_domain ON eng_it.roadmap_blocks(domain_code);

-- Добавляем foreign key к sot_domains (после регистрации доменов)
-- ALTER TABLE eng_it.roadmap_blocks 
--   ADD CONSTRAINT fk_roadmap_blocks_domain 
--   FOREIGN KEY (domain_code) REFERENCES eng_it.sot_domains(code);
-- (закомментировано - применим после регистрации доменов в E1-B0-T1-S3)

-- ============================================================================
-- 5. РАСШИРЕНИЕ: roadmap_tasks - Добавление domain_code
-- ============================================================================
ALTER TABLE eng_it.roadmap_tasks
  ADD COLUMN IF NOT EXISTS domain_code TEXT NOT NULL DEFAULT 'ENG';

COMMENT ON COLUMN eng_it.roadmap_tasks.domain_code IS 'Код домена (ENG, TL) для мультидоменной системы';

-- Индекс для фильтрации по домену и статусу
CREATE INDEX IF NOT EXISTS idx_roadmap_tasks_domain_status ON eng_it.roadmap_tasks(domain_code, status);

-- ============================================================================
-- 6. ТАБЛИЦА: roadmap_steps - Детализация шагов задач (из JSONB → таблица)
-- ============================================================================
CREATE TABLE IF NOT EXISTS eng_it.roadmap_steps (
  id          BIGSERIAL PRIMARY KEY,
  domain_code TEXT NOT NULL DEFAULT 'ENG',
  task_id     BIGINT NOT NULL REFERENCES eng_it.roadmap_tasks(id) ON DELETE CASCADE,
  code        TEXT NOT NULL,           -- E1-B0-T1-S1
  title       TEXT NOT NULL,
  status      TEXT NOT NULL DEFAULT 'planned', -- planned|in_progress|done|failed|blocked
  priority    INTEGER NOT NULL DEFAULT 100,
  description TEXT,
  meta        JSONB DEFAULT '{}',
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ,
  UNIQUE(task_id, code)
);

COMMENT ON TABLE eng_it.roadmap_steps IS 'Детализация шагов задач (steps из roadmap_tasks.steps JSONB)';
COMMENT ON COLUMN eng_it.roadmap_steps.code IS 'Уникальный код шага (E1-B0-T1-S1)';

-- Индексы
CREATE INDEX IF NOT EXISTS idx_roadmap_steps_task ON eng_it.roadmap_steps(task_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_steps_domain_status ON eng_it.roadmap_steps(domain_code, status);
CREATE INDEX IF NOT EXISTS idx_roadmap_steps_code ON eng_it.roadmap_steps(code);

-- Check constraint для статусов
ALTER TABLE eng_it.roadmap_steps
  ADD CONSTRAINT roadmap_steps_status_check 
  CHECK (status IN ('planned', 'in_progress', 'done', 'failed', 'blocked', 'skipped'));

-- ============================================================================
-- 7. ТАБЛИЦА: roadmap_artifacts - Связь задач/шагов с файлами
-- ============================================================================
CREATE TABLE IF NOT EXISTS eng_it.roadmap_artifacts (
  id            BIGSERIAL PRIMARY KEY,
  domain_code   TEXT NOT NULL DEFAULT 'ENG',
  task_id       BIGINT REFERENCES eng_it.roadmap_tasks(id) ON DELETE CASCADE,
  step_id       BIGINT REFERENCES eng_it.roadmap_steps(id) ON DELETE CASCADE,
  artifact_type TEXT NOT NULL,  -- 'sql','python','yaml','markdown','report','spec'
  file_path     TEXT NOT NULL,  -- Относительный путь в репозитории
  git_commit    TEXT,           -- Hash коммита, когда файл создан/изменён
  status        TEXT NOT NULL DEFAULT 'planned', -- planned|in_progress|done|verified|failed
  meta          JSONB DEFAULT '{}',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE eng_it.roadmap_artifacts IS 'Связь задач и шагов с файлами репозитория';
COMMENT ON COLUMN eng_it.roadmap_artifacts.file_path IS 'Относительный путь файла (DB/migrations/xxx.sql)';
COMMENT ON COLUMN eng_it.roadmap_artifacts.git_commit IS 'Git commit hash создания/изменения файла';

-- Индексы
CREATE INDEX IF NOT EXISTS idx_roadmap_artifacts_task ON eng_it.roadmap_artifacts(task_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_artifacts_step ON eng_it.roadmap_artifacts(step_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_artifacts_file ON eng_it.roadmap_artifacts(file_path);
CREATE INDEX IF NOT EXISTS idx_roadmap_artifacts_domain ON eng_it.roadmap_artifacts(domain_code);

-- Check constraint
ALTER TABLE eng_it.roadmap_artifacts
  ADD CONSTRAINT roadmap_artifacts_status_check
  CHECK (status IN ('planned', 'in_progress', 'done', 'verified', 'failed'));

-- ============================================================================
-- 8. РАСШИРЕНИЕ: roadmap_history - Добавление domain_code (если таблица существует)
-- ============================================================================
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.tables 
    WHERE table_schema = 'eng_it' AND table_name = 'roadmap_history'
  ) THEN
    -- Добавляем domain_code если таблица существует
    ALTER TABLE eng_it.roadmap_history
      ADD COLUMN IF NOT EXISTS domain_code TEXT NOT NULL DEFAULT 'ENG';
    
    CREATE INDEX IF NOT EXISTS idx_roadmap_history_domain 
      ON eng_it.roadmap_history(domain_code);
  END IF;
END $$;

-- ============================================================================
-- 9. ВЬЮХА: v_roadmap_progress - Прогресс доменов
-- ============================================================================
CREATE OR REPLACE VIEW eng_it.v_roadmap_progress AS
SELECT 
  d.code AS domain_code,
  d.title AS domain_title,
  COUNT(DISTINCT b.id) AS blocks_total,
  COUNT(DISTINCT t.id) AS tasks_total,
  COUNT(DISTINCT s.id) AS steps_total,
  COUNT(DISTINCT CASE WHEN s.status = 'done' THEN s.id END) AS steps_done,
  COUNT(DISTINCT CASE WHEN s.status = 'in_progress' THEN s.id END) AS steps_in_progress,
  COUNT(DISTINCT CASE WHEN s.status = 'planned' THEN s.id END) AS steps_planned,
  COUNT(DISTINCT CASE WHEN s.status IN ('failed', 'blocked') THEN s.id END) AS steps_issues,
  ROUND(
    100.0 * COUNT(DISTINCT CASE WHEN s.status = 'done' THEN s.id END) / 
    NULLIF(COUNT(DISTINCT s.id), 0), 
    2
  ) AS progress_pct
FROM eng_it.sot_domains d
LEFT JOIN eng_it.roadmap_blocks b ON b.domain_code = d.code
LEFT JOIN eng_it.roadmap_tasks t ON t.domain_code = d.code
LEFT JOIN eng_it.roadmap_steps s ON s.domain_code = d.code
WHERE d.status = 'active'
GROUP BY d.code, d.title
ORDER BY d.code;

COMMENT ON VIEW eng_it.v_roadmap_progress IS 'Прогресс выполнения Roadmap по доменам';

-- ============================================================================
-- ЗАВЕРШЕНИЕ МИГРАЦИИ
-- ============================================================================
-- Логирование применения миграции
INSERT INTO eng_it.sot_sync (domain_code, sync_type, status, meta)
VALUES (
  NULL, 
  'snapshot', 
  'success', 
  jsonb_build_object(
    'migration', '20251123_001_sot_foundation.sql',
    'task', 'E1-B0-T1-S1',
    'description', 'Федеративная модель SoT - таблицы созданы',
    'timestamp', now()
  )
);

-- Вывод информации
DO $$
BEGIN
  RAISE NOTICE '============================================';
  RAISE NOTICE 'Миграция 20251123_001_sot_foundation.sql';
  RAISE NOTICE 'Задача: E1-B0-T1-S1';
  RAISE NOTICE 'Статус: ✅ УСПЕШНО ПРИМЕНЕНА';
  RAISE NOTICE '============================================';
  RAISE NOTICE 'Созданные таблицы:';
  RAISE NOTICE '  ✅ eng_it.sot_domains';
  RAISE NOTICE '  ✅ eng_it.sot_entries';
  RAISE NOTICE '  ✅ eng_it.sot_sync';
  RAISE NOTICE '  ✅ eng_it.roadmap_steps';
  RAISE NOTICE '  ✅ eng_it.roadmap_artifacts';
  RAISE NOTICE 'Расширенные таблицы:';
  RAISE NOTICE '  ✅ eng_it.roadmap_blocks (+ domain_code)';
  RAISE NOTICE '  ✅ eng_it.roadmap_tasks (+ domain_code)';
  RAISE NOTICE 'Следующий шаг: E1-B0-T1-S3 - Регистрация доменов';
  RAISE NOTICE '============================================';
END $$;