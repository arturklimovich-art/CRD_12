SELECT task_code,
       agent_name,
       status,
       progress_percent,
       evidence_uri,
       started_at,
       finished_at,
       LEFT(COALESCE(notes,''), 200) AS notes_left200
FROM eng_it.agent_progress
WHERE task_code = 'SB-HEALTH-001'
ORDER BY finished_at DESC NULLS LAST, started_at DESC, agent_name;
