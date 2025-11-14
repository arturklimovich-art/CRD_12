-- =============================================
-- АДАПТИРОВАННАЯ БАЗА ДАННЫХ ТЗ ДЛЯ СИСТЕМЫ CRD12
-- Адаптировано для: crd12_pgvector (пользователь: crd_user, база: crd12)
-- Создано: 2025-11-06 13:15:01
-- =============================================

-- Создаем схему eng_it если не существует
CREATE SCHEMA IF NOT EXISTS eng_it;

-- Таблица технических заданий
CREATE TABLE IF NOT EXISTS eng_it.technical_specifications (
    tz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_task_id VARCHAR(100) NOT NULL, -- КРИТИЧЕСКОЕ ПРАВИЛО 2: ссылка на Roadmap
    tz_title VARCHAR(500) NOT NULL,
    tz_description TEXT,
    tz_steps JSONB, -- Шаги выполнения в формате JSON
    tz_priority VARCHAR(20) CHECK (tz_priority IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    status VARCHAR(50) NOT NULL DEFAULT 'PLANNED' CHECK (status IN ('PLANNED','IN_PROGRESS','DONE','BLOCKED','VALIDATED')), -- КРИТИЧЕСКОЕ ПРАВИЛО 1
    estimated_hours INTEGER,
    actual_hours INTEGER,
    created_by VARCHAR(100) DEFAULT 'Bot_Orchestrator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    kurator_verified BOOLEAN DEFAULT FALSE,
    verification_date TIMESTAMP
);

-- Таблица связей Roadmap - ТЗ
CREATE TABLE IF NOT EXISTS eng_it.roadmap_tz_mapping (
    mapping_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    roadmap_task VARCHAR(500) NOT NULL, -- Задача из Roadmap
    roadmap_task_id VARCHAR(100) NOT NULL, -- ID задачи для связи
    tz_id UUID NOT NULL,
    navigator_task_id UUID,
    mapping_type VARCHAR(50) DEFAULT 'DIRECT', -- DIRECT, DEPENDENCY, BLOCKED_BY
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tz_id) REFERENCES eng_it.technical_specifications(tz_id) ON DELETE CASCADE,
    UNIQUE(roadmap_task_id, tz_id) -- Уникальная связь задача-TZ
);

-- Таблица Kurator проверок
CREATE TABLE IF NOT EXISTS eng_it.kurator_verifications (
    verification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tz_id UUID NOT NULL,
    task_id UUID,
    kurator_signature VARCHAR(100) NOT NULL,
    artifacts JSONB, -- Артефакты проверки (код, конфиги, etc)
    snapshot_data JSONB, -- Снапшот состояния системы
    verification_notes TEXT,
    status VARCHAR(50) NOT NULL CHECK (status IN ('APPROVED','REJECTED','PENDING')),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_verification_date TIMESTAMP,
    FOREIGN KEY (tz_id) REFERENCES eng_it.technical_specifications(tz_id) ON DELETE CASCADE
);

-- Таблица истории изменений ТЗ
CREATE TABLE IF NOT EXISTS eng_it.tz_change_history (
    change_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tz_id UUID NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    change_type VARCHAR(50) NOT NULL, -- CREATE, UPDATE, STATUS_CHANGE, VERIFICATION
    old_values JSONB,
    new_values JSONB,
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (tz_id) REFERENCES eng_it.technical_specifications(tz_id) ON DELETE CASCADE
);

-- =============================================
-- ИНДЕКСЫ ДЛЯ ПРОИЗВОДИТЕЛЬНОСТИ
-- =============================================

-- Индексы для technical_specifications
CREATE INDEX IF NOT EXISTS idx_ts_roadmap_task_id ON eng_it.technical_specifications(roadmap_task_id);
CREATE INDEX IF NOT EXISTS idx_ts_status ON eng_it.technical_specifications(status);
CREATE INDEX IF NOT EXISTS idx_ts_priority ON eng_it.technical_specifications(tz_priority);
CREATE INDEX IF NOT EXISTS idx_ts_created_at ON eng_it.technical_specifications(created_at);
CREATE INDEX IF NOT EXISTS idx_ts_kurator_verified ON eng_it.technical_specifications(kurator_verified);

-- Индексы для roadmap_tz_mapping
CREATE INDEX IF NOT EXISTS idx_rtm_roadmap_task ON eng_it.roadmap_tz_mapping(roadmap_task);
CREATE INDEX IF NOT EXISTS idx_rtm_roadmap_task_id ON eng_it.roadmap_tz_mapping(roadmap_task_id);
CREATE INDEX IF NOT EXISTS idx_rtm_tz_id ON eng_it.roadmap_tz_mapping(tz_id);
CREATE INDEX IF NOT EXISTS idx_rtm_navigator_task_id ON eng_it.roadmap_tz_mapping(navigator_task_id);

-- Индексы для kurator_verifications
CREATE INDEX IF NOT EXISTS idx_kv_tz_id ON eng_it.kurator_verifications(tz_id);
CREATE INDEX IF NOT EXISTS idx_kv_status ON eng_it.kurator_verifications(status);
CREATE INDEX IF NOT EXISTS idx_kv_verified_at ON eng_it.kurator_verifications(verified_at);

-- Индексы для tz_change_history
CREATE INDEX IF NOT EXISTS idx_tch_tz_id ON eng_it.tz_change_history(tz_id);
CREATE INDEX IF NOT EXISTS idx_tch_changed_at ON eng_it.tz_change_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_tch_change_type ON eng_it.tz_change_history(change_type);

-- =============================================
-- ПРЕДСТАВЛЕНИЯ ДЛЯ УДОБСТВА РАБОТЫ
-- =============================================

-- Представление для полного отображения ТЗ с связями
CREATE OR REPLACE VIEW eng_it.vw_technical_specifications_full AS
SELECT 
    ts.tz_id,
    ts.roadmap_task_id,
    ts.tz_title,
    ts.tz_description,
    ts.tz_steps,
    ts.tz_priority,
    ts.status,
    ts.estimated_hours,
    ts.actual_hours,
    ts.created_by,
    ts.created_at,
    ts.updated_at,
    ts.kurator_verified,
    ts.verification_date,
    rtm.roadmap_task,
    rtm.navigator_task_id,
    kv.status as kurator_status,
    kv.verified_at as last_verification_date
FROM eng_it.technical_specifications ts
LEFT JOIN eng_it.roadmap_tz_mapping rtm ON ts.tz_id = rtm.tz_id
LEFT JOIN eng_it.kurator_verifications kv ON ts.tz_id = kv.tz_id AND kv.verified_at = (
    SELECT MAX(verified_at) 
    FROM eng_it.kurator_verifications 
    WHERE tz_id = ts.tz_id
);

-- Представление для статистики по ТЗ
CREATE OR REPLACE VIEW eng_it.vw_tz_statistics AS
SELECT 
    status,
    COUNT(*) as task_count,
    AVG(estimated_hours) as avg_estimated_hours,
    AVG(actual_hours) as avg_actual_hours,
    SUM(CASE WHEN kurator_verified THEN 1 ELSE 0 END) as verified_count
FROM eng_it.technical_specifications
GROUP BY status;

-- =============================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ
-- =============================================

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION eng_it.update_updated_at_column()
RETURNS TRIGGER AS $
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$ LANGUAGE plpgsql;

-- Применяем триггер к таблицам
CREATE TRIGGER update_ts_updated_at 
    BEFORE UPDATE ON eng_it.technical_specifications
    FOR EACH ROW EXECUTE FUNCTION eng_it.update_updated_at_column();

CREATE TRIGGER update_rtm_updated_at 
    BEFORE UPDATE ON eng_it.roadmap_tz_mapping
    FOR EACH ROW EXECUTE FUNCTION eng_it.update_updated_at_column();

-- =============================================
-- ПРАВА ДОСТУПА ДЛЯ CRD_USER
-- =============================================

-- Предоставляем права для пользователя crd_user
GRANT USAGE ON SCHEMA eng_it TO crd_user;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA eng_it TO crd_user;
GRANT SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA eng_it TO crd_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA eng_it TO crd_user;

-- =============================================
-- ТЕСТОВЫЕ ДАННЫЕ ДЛЯ ПРОВЕРКИ
-- =============================================

-- INSERT INTO eng_it.technical_specifications (roadmap_task_id, tz_title, tz_description, status) 
-- VALUES ('TZ_4.1', 'Стандартизация формата Roadmap', 'Преобразование Roadmap в машиночитаемый формат', 'IN_PROGRESS');

-- =============================================
-- ПРОВЕРОЧНЫЕ ЗАПРОСЫ
-- =============================================

-- SELECT 'База данных ТЗ успешно создана' as status;
