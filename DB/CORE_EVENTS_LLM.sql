-- Views and helpers for LLM events
CREATE OR REPLACE VIEW core.v_llm_events AS
SELECT * FROM core.events WHERE event_type LIKE 'llm.%';

-- Expected llm.*:
-- llm.provider.switched, llm.healthcheck, llm.inference.metrics, llm.request.blocked
