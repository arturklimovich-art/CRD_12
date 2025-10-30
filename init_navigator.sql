-- Создаем схему для самостроительства
CREATE SCHEMA IF NOT EXISTS eng_it;

-- Создаем кастомные типы (ENUMs) для статусов и уровней
CREATE TYPE eng_it.maturity_level AS ENUM ('B', 'A', 'S');
CREATE TYPE eng_it.status_t AS ENUM ('planned', 'in_progress', 'review', 'blocked', 'passed', 'failed');

-- 1. Таблица задач Навигатора
CREATE TABLE IF NOT EXISTS eng_it.progress_navigator (
  id BIGSERIAL PRIMARY KEY,
  task_code TEXT UNIQUE NOT NULL,           -- Код задачи 'L1-T001'
  title TEXT NOT NULL,                      -- Название задачи
  description TEXT,                         -- Детальное описание
  level eng_it.maturity_level NOT NULL,     -- Уровень сложности (B, A, S)
  module TEXT NOT NULL,                     -- Модуль системы
  priority INTEGER NOT NULL DEFAULT 5,      -- Приоритет (1-10)
  status eng_it.status_t DEFAULT 'planned', -- Общий статус
  estimated_hours INTEGER,                  -- Оценка сложности
  actual_hours INTEGER,                     -- Фактическое время
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- 2. Таблица прогресса Агентов по задачам
CREATE TABLE IF NOT EXISTS eng_it.agent_progress (
  id BIGSERIAL PRIMARY KEY,
  task_code TEXT REFERENCES eng_it.progress_navigator(task_code),
  agent_name TEXT NOT NULL,                 -- 'orchestrator', 'coder', 'curator', 'medic'
  status eng_it.status_t DEFAULT 'planned',
  progress_percent INTEGER DEFAULT 0,       -- 0-100%
  evidence_uri TEXT,                        -- Ссылка на артефакт
  notes TEXT,                               -- Что сделано, проблемы
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  blockers TEXT[],                          -- Блокирующие факторы
  next_steps TEXT[],                        -- Следующие шаги
  UNIQUE(task_code, agent_name)
);

-- 3. Таблица зависимостей между задачами
CREATE TABLE IF NOT EXISTS eng_it.task_dependencies (
  id BIGSERIAL PRIMARY KEY,
  task_code TEXT REFERENCES eng_it.progress_navigator(task_code),
  depends_on_task_code TEXT,                -- Задача-предшественник
  dependency_type TEXT DEFAULT 'hard',      -- 'hard', 'soft', 'parallel'
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 4. Таблица снимков системы для отката
CREATE TABLE IF NOT EXISTS eng_it.system_snapshots (
  id BIGSERIAL PRIMARY KEY,
  snapshot_name TEXT NOT NULL,
  description TEXT,
  task_code TEXT,                      -- На какой задаче сделан снимок
  database_schema JSONB,               -- Схема БД
  agent_configs JSONB,                 -- Конфигурации агентов
  active_tasks JSONB,                  -- Текущие задачи и их статусы
  created_at TIMESTAMPTZ DEFAULT now(),
  is_stable BOOLEAN DEFAULT true       -- Стабильная версия для отката
);

-- 5. Представление для визуализации матрицы прогресса
CREATE OR REPLACE VIEW eng_it.v_progress_matrix AS
SELECT 
  pn.task_code,
  pn.title,
  pn.level,
  pn.module,
  pn.priority,
  pn.status as overall_status,
  MAX(CASE WHEN ap.agent_name = 'orchestrator' THEN ap.status END) as orchestrator,
  MAX(CASE WHEN ap.agent_name = 'orchestrator' THEN ap.progress_percent END) as orchestrator_pct,
  MAX(CASE WHEN ap.agent_name = 'coder' THEN ap.status END) as coder,
  MAX(CASE WHEN ap.agent_name = 'coder' THEN ap.progress_percent END) as coder_pct,
  MAX(CASE WHEN ap.agent_name = 'curator' THEN ap.status END) as curator,
  MAX(CASE WHEN ap.agent_name = 'curator' THEN ap.progress_percent END) as curator_pct,
  MAX(CASE WHEN ap.agent_name = 'medic' THEN ap.status END) as medic,
  MAX(CASE WHEN ap.agent_name = 'medic' THEN ap.progress_percent END) as medic_pct,
  pn.estimated_hours,
  pn.actual_hours,
  COUNT(td.id) as dependency_count
FROM eng_it.progress_navigator pn
LEFT JOIN eng_it.agent_progress ap ON pn.task_code = ap.task_code
LEFT JOIN eng_it.task_dependencies td ON pn.task_code = td.task_code
GROUP BY pn.task_code, pn.title, pn.level, pn.module, pn.priority, pn.status, 
         pn.estimated_hours, pn.actual_hours;

-- 6. Представление для отслеживания эффективности
CREATE OR REPLACE VIEW eng_it.v_self_building_metrics AS
SELECT 
  COUNT(*) as total_tasks,
  COUNT(*) FILTER (WHERE status = 'passed') as completed_tasks,
  COUNT(*) FILTER (WHERE status = 'failed') as failed_tasks,
  COUNT(*) FILTER (WHERE status = 'in_progress') as active_tasks,
  AVG(actual_hours) FILTER (WHERE status = 'passed') as avg_completion_hours,
  SUM(estimated_hours) as total_estimated_hours,
  SUM(actual_hours) as total_actual_hours,
  CASE 
    WHEN SUM(estimated_hours) > 0 
    THEN (SUM(actual_hours) * 100.0 / SUM(estimated_hours)) 
    ELSE 100 
  END as planning_accuracy_percent
FROM eng_it.progress_navigator;

COMMIT;