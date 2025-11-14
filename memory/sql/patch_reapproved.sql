INSERT INTO eng_it.patch_events (patch_id, event_type, payload)
VALUES (
  'f46262d1-ff1d-4612-909e-939b607b149a',
  'curator.patch.reapproved',
  '{"by":"system","reason":"need-approved-for-apply"}'::jsonb
);

SELECT id, patch_id, event_type, ts
FROM eng_it.patch_events
ORDER BY id DESC
LIMIT 10;
