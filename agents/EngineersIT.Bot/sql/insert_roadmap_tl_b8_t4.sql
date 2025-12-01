BEGIN;

INSERT INTO eng_it.roadmap_tasks
    (code, title, description, status, priority, domain_code, block_code, created_at, updated_at)
VALUES
    ('TL-B8-T4',
     'DB Optimization: DatabaseManager & trades upsert',
     'Realized DB optimization: reliable upsert to lab.trades, meta JSON accumulation, summary upsert to lab.results, logging to eng_it.roadmap_events. See agents/EngineersIT.Bot/reports/TL-B8-T4-db-optimization.md for details.',
     'done',
     25,
     'TL',
     'TL-B8',
     NOW(),
     NOW()
    )
ON CONFLICT (code) DO UPDATE
  SET title = EXCLUDED.title,
      description = EXCLUDED.description,
      status = EXCLUDED.status,
      priority = EXCLUDED.priority,
      updated_at = NOW()
RETURNING id;

INSERT INTO eng_it.roadmap_events (entity_type, entity_id, event_type, old_value, new_value, changed_by, meta, ts)
VALUES ('task', NULL, 'note', '{}'::jsonb, '{"note":"DB optimization recorded: TL-B8-T4"}'::jsonb, 'automation', '{"report":"agents/EngineersIT.Bot/reports/TL-B8-T4-db-optimization.md"}'::jsonb, NOW());

COMMIT;