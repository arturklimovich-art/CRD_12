-- 2025_11_roadmap.sql — создание проекций Roadmap
CREATE SCHEMA IF NOT EXISTS nav;

CREATE TABLE IF NOT EXISTS nav.roadmap_items (
  item_id UUID PRIMARY KEY,
  parent_id UUID NULL,
  title TEXT NOT NULL,
  summary TEXT,
  tech_hints JSONB DEFAULT '[]',
  deliverable TEXT,
  priority INT DEFAULT 3,
  status TEXT CHECK (status IN ('planned','in_progress','blocked','done')),
  owner TEXT CHECK (owner IN ('bot','engineer_b','user','mixed')),
  order_index INT DEFAULT 100,
  active_revision_id UUID,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roadmap_status_priority ON nav.roadmap_items(status, priority);
CREATE INDEX IF NOT EXISTS idx_roadmap_order ON nav.roadmap_items(order_index);
CREATE INDEX IF NOT EXISTS idx_roadmap_tech_hints_gin ON nav.roadmap_items USING GIN(tech_hints);

CREATE TABLE IF NOT EXISTS nav.roadmap_revisions (
  revision_id UUID PRIMARY KEY,
  item_id UUID REFERENCES nav.roadmap_items(item_id),
  version_tag TEXT,
  diff_type TEXT CHECK (diff_type IN ('append','edit','reorder','status_update')),
  payload_md_ref TEXT,
  approved BOOLEAN DEFAULT FALSE,
  approved_by TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_roadmap_rev_item ON nav.roadmap_revisions(item_id);

-- Материализованное представление иерархии
CREATE MATERIALIZED VIEW IF NOT EXISTS nav.roadmap_tree_view AS
WITH RECURSIVE tree AS (
  SELECT item_id, parent_id, title, 0 AS level
  FROM nav.roadmap_items
  WHERE parent_id IS NULL
  UNION ALL
  SELECT i.item_id, i.parent_id, i.title, t.level + 1
  FROM nav.roadmap_items i
  JOIN tree t ON i.parent_id = t.item_id
)
SELECT * FROM tree;

