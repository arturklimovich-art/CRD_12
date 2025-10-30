UPDATE eng_it.agent_progress
SET evidence_uri = '/app/_evidence/probe_20251023_143401.txt'
WHERE task_code = 'SB-HEALTH-001' AND agent_name = 'coder';
COMMIT;
