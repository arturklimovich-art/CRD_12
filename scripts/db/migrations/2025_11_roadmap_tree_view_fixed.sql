-- Миграция: создание материализованного представления roadmap_tree_view
-- Для иерархического отображения Roadmap (parent→children)

CREATE MATERIALIZED VIEW nav.roadmap_tree_view AS
WITH RECURSIVE roadmap_tree AS (
    -- Корневые элементы (без parent_id)
    SELECT 
        item_id,
        parent_id,
        title,
        summary,
        tech_hints,
        deliverable,
        priority,
        status,
        owner,
        order_index,
        active_revision_id,
        created_at,
        updated_at,
        1 as level,
        ARRAY[order_index] as path,
        title as path_titles
    FROM nav.roadmap_items 
    WHERE parent_id IS NULL
    
    UNION ALL
    
    -- Дочерние элементы
    SELECT 
        ri.item_id,
        ri.parent_id,
        ri.title,
        ri.summary,
        ri.tech_hints,
        ri.deliverable,
        ri.priority,
        ri.status,
        ri.owner,
        ri.order_index,
        ri.active_revision_id,
        ri.created_at,
        ri.updated_at,
        rt.level + 1 as level,
        rt.path || ri.order_index as path,
        rt.path_titles || ' -> ' || ri.title as path_titles
    FROM nav.roadmap_items ri
    INNER JOIN roadmap_tree rt ON ri.parent_id = rt.item_id
    WHERE ri.parent_id IS NOT NULL
)
SELECT 
    item_id,
    parent_id,
    title,
    summary,
    tech_hints,
    deliverable,
    priority,
    status,
    owner,
    order_index,
    active_revision_id,
    created_at,
    updated_at,
    level,
    path,
    path_titles
FROM roadmap_tree
ORDER BY path;

-- Индексы для производительности
CREATE INDEX idx_roadmap_tree_view_item_id ON nav.roadmap_tree_view (item_id);
CREATE INDEX idx_roadmap_tree_view_parent_id ON nav.roadmap_tree_view (parent_id);
CREATE INDEX idx_roadmap_tree_view_path ON nav.roadmap_tree_view USING gin(path);
CREATE INDEX idx_roadmap_tree_view_status ON nav.roadmap_tree_view (status);

-- Функция для обновления представления
CREATE OR REPLACE FUNCTION nav.refresh_roadmap_tree_view()
RETURNS void AS \$\$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY nav.roadmap_tree_view;
END;
\$\$ LANGUAGE plpgsql;

-- Комментарии
COMMENT ON MATERIALIZED VIEW nav.roadmap_tree_view IS 'Иерархическое представление элементов Roadmap для навигации и построения дерева';
COMMENT ON FUNCTION nav.refresh_roadmap_tree_view() IS 'Безопасное обновление материализованного представления roadmap_tree_view';
