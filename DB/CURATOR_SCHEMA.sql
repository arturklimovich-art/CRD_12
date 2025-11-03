CREATE SCHEMA IF NOT EXISTS eng_it;

CREATE TABLE IF NOT EXISTS eng_it.tasks (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  status        TEXT NOT NULL,
  owner         TEXT,
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eng_it.job_queue (
  id            BIGSERIAL PRIMARY KEY,
  task_id       TEXT REFERENCES eng_it.tasks(id) ON DELETE CASCADE,
  job_type      TEXT NOT NULL,
  payload       JSONB,
  status        TEXT NOT NULL DEFAULT 'queued',
  attempts      INT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ DEFAULT now(),
  updated_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eng_it.artifacts (
  id            BIGSERIAL PRIMARY KEY,
  task_id       TEXT REFERENCES eng_it.tasks(id) ON DELETE CASCADE,
  kind          TEXT NOT NULL,
  path          TEXT NOT NULL,
  meta          JSONB,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eng_it.task_history (
  id            BIGSERIAL PRIMARY KEY,
  task_id       TEXT REFERENCES eng_it.tasks(id) ON DELETE CASCADE,
  from_status   TEXT,
  to_status     TEXT,
  changed_at    TIMESTAMPTZ DEFAULT now(),
  actor         TEXT,
  note          TEXT
);

CREATE TABLE IF NOT EXISTS eng_it.curator_rationale (
  id            BIGSERIAL PRIMARY KEY,
  task_id       TEXT REFERENCES eng_it.tasks(id) ON DELETE CASCADE,
  rca           JSONB,
  mentor_tips   JSONB,
  policy_report JSONB,
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE OR REPLACE VIEW eng_it.v_unresolved_tasks AS
SELECT * FROM eng_it.tasks WHERE status IN ('unresolved','needs_info','parked');

CREATE OR REPLACE VIEW eng_it.v_curator_dashboard AS
SELECT t.id, t.title, t.status, j.job_type, j.status AS job_status, a.kind, a.path, h.changed_at
FROM eng_it.tasks t
LEFT JOIN eng_it.job_queue j ON j.task_id = t.id
LEFT JOIN eng_it.artifacts a ON a.task_id = t.id
LEFT JOIN eng_it.task_history h ON h.task_id = t.id;
