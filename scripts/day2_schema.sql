CREATE TABLE IF NOT EXISTS tasks (id SERIAL PRIMARY KEY, state TEXT NOT NULL, title TEXT NOT NULL, spec_json JSONB, snapshot_id TEXT, created_at TIMESTAMP DEFAULT now(), updated_at TIMESTAMP DEFAULT now());
CREATE TABLE IF NOT EXISTS messages (id SERIAL PRIMARY KEY, topic TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, created_at TIMESTAMP DEFAULT now());
CREATE TABLE IF NOT EXISTS agent_stats (agent_type TEXT PRIMARY KEY, wins INT DEFAULT 0, losses INT DEFAULT 0, streak INT DEFAULT 0, best_streak INT DEFAULT 0, last_updated TIMESTAMP DEFAULT now());
CREATE TABLE IF NOT EXISTS system_health (service TEXT PRIMARY KEY, status TEXT, last_heartbeat TIMESTAMP DEFAULT now(), lock_holder TEXT);
INSERT INTO system_health(service,status,last_heartbeat) VALUES
  ('engineer_b_api','ok',now()), ('engineer_a_bot','degraded',now()), ('pgvector','ok',now())
ON CONFLICT (service) DO UPDATE SET status=EXCLUDED.status, last_heartbeat=EXCLUDED.last_heartbeat;
