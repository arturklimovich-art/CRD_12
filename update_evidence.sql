UPDATE eng_it.agent_progress
SET evidence_uri = '/app/_evidence/artifact_20251023_134347.txt'
WHERE task_code = 'SB-HEALTH-001' AND agent_name = 'orchestrator';
COMMIT;
