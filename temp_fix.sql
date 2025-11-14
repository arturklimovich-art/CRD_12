-- Миграция: интеграция обновления roadmap_tree_view в проектор событий

-- Создаем упрощенную функцию обновления (без CONCURRENTLY для транзакций)
CREATE OR REPLACE FUNCTION nav.refresh_roadmap_tree_view_safe()
RETURNS void AS \$\$
BEGIN
    REFRESH MATERIALIZED VIEW nav.roadmap_tree_view;
END;
\$\$ LANGUAGE plpgsql;

-- Обновляем функцию проектора для вызова обновления представления
CREATE OR REPLACE FUNCTION nav.project_roadmap_catchup()
RETURNS bigint AS \$\$
DECLARE
    _last_id bigint;
    _offset bigint;
    _count bigint := 0;
    _rec record;
BEGIN
    -- Получаем текущий оффсет
    SELECT COALESCE(last_event_id, 0) INTO _offset 
    FROM nav.projector_offset 
    WHERE projector_name = 'roadmap_nav';
    
    IF _offset IS NULL THEN
        _offset := 0;
        INSERT INTO nav.projector_offset (projector_name, last_event_id) 
        VALUES ('roadmap_nav', 0);
    END IF;

    -- Обрабатываем события
    FOR _rec IN 
        SELECT id, ts, source, type, payload
        FROM core.events
        WHERE id > _offset
        ORDER BY id
    LOOP
        -- Вызываем обработчик события
        PERFORM nav.project_roadmap_event(_rec.id, _rec.ts, _rec.type, _rec.payload);
        _last_id := _rec.id;
        _count := _count + 1;
    END LOOP;

    -- Обновляем оффсет если были обработаны события
    IF _count > 0 THEN
        UPDATE nav.projector_offset 
        SET last_event_id = _last_id, updated_at = NOW()
        WHERE projector_name = 'roadmap_nav';
        
        -- Обновляем материализованное представление
        PERFORM nav.refresh_roadmap_tree_view_safe();
    END IF;

    RETURN _count;
END;
\$\$ LANGUAGE plpgsql;

-- Комментарии
COMMENT ON FUNCTION nav.refresh_roadmap_tree_view_safe() IS 'Безопасное обновление материализованного представления roadmap_tree_view (для использования в транзакциях)';
