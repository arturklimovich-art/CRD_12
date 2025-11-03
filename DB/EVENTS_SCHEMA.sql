-- core.events: central append-only event log
CREATE SCHEMA IF NOT EXISTS core;

CREATE TABLE IF NOT EXISTS core.events (
  id           BIGSERIAL PRIMARY KEY,
  ts           TIMESTAMPTZ NOT NULL DEFAULT now(),
  actor        TEXT NOT NULL,
  event_type   TEXT NOT NULL,
  task_id      TEXT,
  labels       TEXT[],
  commit_sha   TEXT,
  payload      JSONB,
  ref          TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_ts ON core.events(ts);
CREATE INDEX IF NOT EXISTS idx_events_type ON core.events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_task ON core.events(task_id);

-- Recommended event_type namespaces:
-- ps.patch.*, eng.apply_patch.*, readmap.*, bot.telegram.*, bot.command.*, bot.intelligence.*, llm.*, curator.*, navigator.*, plan.*
