-- Views and helpers for LLM events
CREATE OR REPLACE VIEW core.v_llm_events AS
SELECT * FROM core.events WHERE type LIKE 'llm.%';

-- Expected llm.*:
-- llm.provider.switched, llm.healthcheck, llm.inference.metrics, llm.request.blocked

