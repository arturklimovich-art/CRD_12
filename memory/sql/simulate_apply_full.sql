-- симуляция применения одобренного патча
INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
VALUES (
  'f46262d1-ff1d-4612-909e-939b607b149a',
  'eng.apply_patch.started',
  '{"by":"manual-simulator","phase":"apply"}'::jsonb
);

INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
VALUES (
  'f46262d1-ff1d-4612-909e-939b607b149a',
  'eng.apply_patch.finished',
  '{"result":"success","smoke":"not-run"}'::jsonb
);

INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
VALUES (
  'f46262d1-ff1d-4612-909e-939b607b149a',
  'eng.apply_patch.rolled_back',
  '{"result":"rollback","reason":"simulated"}'::jsonb
);

SELECT id, patch_id, event_type, ts
FROM eng_it.patch_events
WHERE patch_id = 'f46262d1-ff1d-4612-909e-939b607b149a'
ORDER BY id ASC;
