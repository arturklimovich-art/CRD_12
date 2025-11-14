-- ================================
--  Миграция: eng_it.patches + patch_events
--  Цель: регистрация ручных и автоматических патчей в Navigator DB
-- ================================

CREATE TABLE IF NOT EXISTS eng_it.patches (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id uuid NULL,
    author text NOT NULL,
    created_at timestamptz DEFAULT now(),
    filename text NOT NULL,
    content bytea NOT NULL,
    sha256 text NOT NULL,
    status text NOT NULL DEFAULT 'submitted',
    approve_token text NULL,
    curator_notes text NULL,
    applied_at timestamptz NULL,
    rollback_at timestamptz NULL,
    meta jsonb NULL
);

CREATE TABLE IF NOT EXISTS eng_it.patch_events (
    id serial PRIMARY KEY,
    patch_id uuid NOT NULL REFERENCES eng_it.patches(id),
    ts timestamptz DEFAULT now(),
    event_type text NOT NULL,
    payload jsonb
);

CREATE INDEX IF NOT EXISTS idx_patches_status ON eng_it.patches(status);
CREATE INDEX IF NOT EXISTS idx_patches_created_at ON eng_it.patches(created_at DESC);
