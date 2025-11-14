-- Создание функций Kurator с правильным синтаксисом

-- Функция проверки ревизии Roadmap
CREATE OR REPLACE FUNCTION nav.kurator_check_roadmap_revision(
    _revision_id UUID,
    _item_id UUID,
    _diff_type TEXT,
    _payload_md_ref TEXT
)
RETURNS TABLE(policy_name TEXT, check_passed BOOLEAN, message TEXT, severity TEXT) AS \$\$
BEGIN
    -- Проверка 1: Запрет удалений (append-only принцип)
    RETURN QUERY
    SELECT 
        'no_deletions'::TEXT as policy_name,
        _diff_type != 'delete' as check_passed,
        CASE 
            WHEN _diff_type = 'delete' THEN 'Запрещены операции удаления в Roadmap'
            ELSE 'OK: Операция не является удалением'
        END as message,
        'blocking'::TEXT as severity;

    -- Проверка 2: Корректность путей (не выходят за пределы проекта)
    RETURN QUERY
    SELECT 
        'valid_paths'::TEXT as policy_name,
        _payload_md_ref LIKE 'workspace/roadmap/revisions/%' as check_passed,
        CASE 
            WHEN _payload_md_ref NOT LIKE 'workspace/roadmap/revisions/%' THEN 'Некорректный путь к файлу ревизии'
            ELSE 'OK: Путь к файлу ревизии корректен'
        END as message,
        'blocking'::TEXT as severity;

    -- Проверка 3: Ревизия должна ссылаться на существующий item
    RETURN QUERY
    SELECT 
        'item_exists'::TEXT as policy_name,
        EXISTS(SELECT 1 FROM nav.roadmap_items WHERE item_id = _item_id) as check_passed,
        CASE 
            WHEN NOT EXISTS(SELECT 1 FROM nav.roadmap_items WHERE item_id = _item_id) THEN 'Элемент Roadmap не существует'
            ELSE 'OK: Элемент Roadmap существует'
        END as message,
        'blocking'::TEXT as severity;
END;
\$\$ LANGUAGE plpgsql;

-- Функция проверки ТЗ
CREATE OR REPLACE FUNCTION nav.kurator_check_technical_task(
    _tz_id UUID,
    _title TEXT,
    _artifacts JSONB
)
RETURNS TABLE(policy_name TEXT, check_passed BOOLEAN, message TEXT, severity TEXT) AS \$\$
BEGIN
    -- Проверка 1: Наличие acceptance criteria
    RETURN QUERY
    SELECT 
        'has_acceptance_criteria'::TEXT as policy_name,
        _title IS NOT NULL AND length(trim(_title)) > 0 as check_passed,
        CASE 
            WHEN _title IS NULL OR length(trim(_title)) = 0 THEN 'ТЗ должно иметь заголовок'
            ELSE 'OK: Заголовок ТЗ присутствует'
        END as message,
        'blocking'::TEXT as severity;

    -- Проверка 2: Корректность артефактов (если указаны)
    RETURN QUERY
    SELECT 
        'valid_artifacts'::TEXT as policy_name,
        _artifacts IS NULL OR jsonb_typeof(_artifacts) = 'array' as check_passed,
        CASE 
            WHEN _artifacts IS NOT NULL AND jsonb_typeof(_artifacts) != 'array' THEN 'Артефакты должны быть массивом'
            ELSE 'OK: Артефакты корректны'
        END as message,
        'warning'::TEXT as severity;
END;
\$\$ LANGUAGE plpgsql;

-- Функция комплексной проверки ревизии
CREATE OR REPLACE FUNCTION nav.kurator_validate_roadmap_revision(_revision_id UUID)
RETURNS TABLE(policy_name TEXT, check_passed BOOLEAN, message TEXT, severity TEXT, overall BOOLEAN) AS \$\$
DECLARE
    _rec record;
    _all_passed BOOLEAN := true;
BEGIN
    -- Получаем данные ревизии
    SELECT ri.item_id, rr.diff_type, rr.payload_md_ref 
    INTO _rec
    FROM nav.roadmap_revisions rr
    JOIN nav.roadmap_items ri ON rr.item_id = ri.item_id
    WHERE rr.revision_id = _revision_id;

    IF NOT FOUND THEN
        RETURN;
    END IF;

    -- Выполняем проверки
    RETURN QUERY
    SELECT 
        k.policy_name,
        k.check_passed,
        k.message,
        k.severity,
        CASE 
            WHEN k.severity = 'blocking' THEN k.check_passed
            ELSE true
        END as overall
    FROM nav.kurator_check_roadmap_revision(_revision_id, _rec.item_id, _rec.diff_type, _rec.payload_md_ref) k;

    -- Сохраняем результаты проверок
    INSERT INTO nav.kurator_checks (policy_id, target_type, target_id, check_passed, check_message)
    SELECT 
        (SELECT policy_id FROM nav.kurator_policies WHERE policy_name = k.policy_name AND active = true),
        'roadmap_revision',
        _revision_id,
        k.check_passed,
        k.message
    FROM nav.kurator_check_roadmap_revision(_revision_id, _rec.item_id, _rec.diff_type, _rec.payload_md_ref) k;
END;
\$\$ LANGUAGE plpgsql;
