CREATE TABLE IF NOT EXISTS snapshots (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT now(),
    description TEXT,
    artifact_path TEXT
);

CREATE TABLE IF NOT EXISTS recovery_logs (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP DEFAULT now(),
    error_type TEXT,
    action_taken TEXT,
    snapshot_id INT REFERENCES snapshots(id)
);
