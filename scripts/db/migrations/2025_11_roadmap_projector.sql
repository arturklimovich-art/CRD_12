-- 2025_11_roadmap_projector.sql — проектор nav.* по событиям core.events

CREATE SCHEMA IF NOT EXISTS nav;

CREATE TABLE IF NOT EXISTS nav.projector_offset (
  projector_name TEXT PRIMARY KEY,
  last_event_id  BIGINT NOT NULL DEFAULT 0,
  updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION nav.set_offset(_name TEXT, _id BIGINT) RETURNS VOID AS $$
BEGIN
  INSERT INTO nav.projector_offset(projector_name,last_event_id,updated_at)
  VALUES(_name,_id,NOW())
  ON CONFLICT(projector_name) DO UPDATE
  SET last_event_id = EXCLUDED.last_event_id,
      updated_at    = NOW();
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION nav.rebuild_tree() RETURNS VOID AS $$
BEGIN
  BEGIN
    REFRESH MATERIALIZED VIEW nav.roadmap_tree_view;
  EXCEPTION WHEN undefined_table THEN
    -- Матвью может ещё не существовать: безопасно игнорируем
    NULL;
  END;
END; $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION nav.project_roadmap_event(
  _id BIGINT,
  _ts TIMESTAMPTZ,
  _type TEXT,
  _payload JSONB
) RETURNS VOID AS $$
DECLARE
  v_item_id UUID;
  v_rev_id  UUID;
  v_parent  UUID;
  v_title   TEXT;
  v_summary TEXT;
  v_hints   JSONB;
  v_deliv   TEXT;
  v_prio    INT;
  v_status  TEXT;
  v_owner   TEXT;
  v_order   INT;
  v_ver_tag TEXT;
  v_diff    TEXT;
  v_mdref   TEXT;
  v_fields  JSONB;
BEGIN
  IF _type = 'roadmap.item.created' THEN
    v_item_id := (_payload->>'item_id')::uuid;
    v_parent  := NULLIF(_payload->>'parent_id','')::uuid;
    v_title   := _payload->>'title';
    v_summary := _payload->>'summary';
    v_hints   := COALESCE(_payload->'tech_hints','[]'::jsonb);
    v_deliv   := _payload->>'deliverable';
    v_prio    := NULLIF(_payload->>'priority','')::int;
    v_status  := _payload->>'status';
    v_owner   := _payload->>'owner';
    v_order   := NULLIF(_payload->>'order_index','')::int;

    INSERT INTO nav.roadmap_items(
      item_id,parent_id,title,summary,tech_hints,deliverable,priority,status,owner,order_index,created_at,updated_at
    )
    VALUES(v_item_id,v_parent,v_title,v_summary,v_hints,v_deliv,COALESCE(v_prio,3),v_status,v_owner,COALESCE(v_order,100),_ts,_ts)
    ON CONFLICT (item_id) DO NOTHING;

  ELSIF _type = 'roadmap.item.edited' THEN
    v_item_id := (_payload->>'item_id')::uuid;
    v_fields  := COALESCE(_payload->'fields','{}'::jsonb);

    UPDATE nav.roadmap_items SET
      title       = COALESCE(v_fields->>'title', title),
      summary     = COALESCE(v_fields->>'summary', summary),
      tech_hints  = COALESCE(v_fields->'tech_hints', tech_hints),
      deliverable = COALESCE(v_fields->>'deliverable', deliverable),
      priority    = COALESCE((v_fields->>'priority')::int, priority),
      status      = COALESCE(v_fields->>'status', status),
      owner       = COALESCE(v_fields->>'owner', owner),
      order_index = COALESCE((v_fields->>'order_index')::int, order_index),
      updated_at  = _ts
    WHERE item_id = v_item_id;

  ELSIF _type = 'roadmap.item.reordered' THEN
    v_item_id := (_payload->>'item_id')::uuid;
    v_order   := NULLIF(_payload->>'order_index','')::int;
    UPDATE nav.roadmap_items SET order_index = COALESCE(v_order,order_index), updated_at=_ts
    WHERE item_id = v_item_id;

  ELSIF _type = 'roadmap.item.status_changed' THEN
    v_item_id := (_payload->>'item_id')::uuid;
    v_status  := _payload->>'status';
    UPDATE nav.roadmap_items SET status = v_status, updated_at=_ts WHERE item_id = v_item_id;

  ELSIF _type = 'roadmap.item.archived' THEN
    v_item_id := (_payload->>'item_id')::uuid;
    UPDATE nav.roadmap_items SET status='blocked', updated_at=_ts WHERE item_id=v_item_id;

  ELSIF _type = 'roadmap.revision.submitted' THEN
    v_rev_id  := (_payload->>'revision_id')::uuid;
    v_item_id := (_payload->>'item_id')::uuid;
    v_ver_tag := _payload->>'version_tag';
    v_diff    := _payload->>'diff_type';
    v_mdref   := _payload->>'payload_md_ref';

    INSERT INTO nav.roadmap_revisions(revision_id,item_id,version_tag,diff_type,payload_md_ref,approved,approved_by,created_at)
    VALUES(v_rev_id,v_item_id,v_ver_tag,v_diff,v_mdref,FALSE,NULL,_ts)
    ON CONFLICT (revision_id) DO NOTHING;

  ELSIF _type = 'roadmap.revision.approved' THEN
    v_rev_id  := (_payload->>'revision_id')::uuid;
    v_item_id := (_payload->>'item_id')::uuid;

    UPDATE nav.roadmap_revisions
    SET approved=TRUE, approved_by=COALESCE(_payload->>'approved_by','user'), created_at=_ts
    WHERE revision_id=v_rev_id;

    UPDATE nav.roadmap_items SET active_revision_id = v_rev_id, updated_at=_ts WHERE item_id = v_item_id;

    v_fields := COALESCE(_payload->'fields','{}'::jsonb);
    IF v_fields <> '{}'::jsonb THEN
      UPDATE nav.roadmap_items SET
        title       = COALESCE(v_fields->>'title', title),
        summary     = COALESCE(v_fields->>'summary', summary),
        tech_hints  = COALESCE(v_fields->'tech_hints', tech_hints),
        deliverable = COALESCE(v_fields->>'deliverable', deliverable),
        priority    = COALESCE((v_fields->>'priority')::int, priority),
        status      = COALESCE(v_fields->>'status', status),
        owner       = COALESCE(v_fields->>'owner', owner),
        order_index = COALESCE((v_fields->>'order_index')::int, order_index),
        updated_at  = _ts
      WHERE item_id = v_item_id;
    END IF;
  END IF;

  PERFORM nav.rebuild_tree();
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION nav.project_roadmap_catchup() RETURNS BIGINT AS $$
DECLARE
  v_from BIGINT;
  v_last BIGINT := 0;
  r RECORD;
BEGIN
  SELECT last_event_id INTO v_from FROM nav.projector_offset WHERE projector_name='roadmap_nav' FOR UPDATE NOWAIT;
  IF NOT FOUND THEN
    v_from := 0;
    INSERT INTO nav.projector_offset(projector_name,last_event_id) VALUES('roadmap_nav',0)
    ON CONFLICT DO NOTHING;
  END IF;

  FOR r IN
    SELECT id, ts, type, payload
    FROM core.events
    WHERE id > v_from
      AND (type LIKE 'roadmap.%' OR type LIKE 'roadmap.revision.%')
    ORDER BY id
  LOOP
    PERFORM nav.project_roadmap_event(r.id, r.ts, r.type, r.payload);
    v_last := r.id;
  END LOOP;

  IF v_last > 0 THEN
    PERFORM nav.set_offset('roadmap_nav', v_last);
    RETURN v_last;
  ELSE
    RETURN v_from;
  END IF;
END;
$$ LANGUAGE plpgsql;
