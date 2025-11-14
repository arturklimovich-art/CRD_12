-- Migration V006: Add code_versions table and extend patches table
-- Purpose: Enable code versioning and improved rollback mechanism
-- Date: 2025-11-11
-- Author: Engineers_IT Core Team

-- 1. Create code_versions table
CREATE TABLE IF NOT EXISTS eng_it.code_versions (
    version_id VARCHAR(100) PRIMARY KEY,
    file_path TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(100),
    task_id VARCHAR(100),
    is_stable BOOLEAN DEFAULT FALSE,
    CONSTRAINT fk_task FOREIGN KEY (task_id) REFERENCES eng_it.tasks(id) ON DELETE SET NULL
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_code_versions_file ON eng_it.code_versions(file_path);
CREATE INDEX IF NOT EXISTS idx_code_versions_task ON eng_it.code_versions(task_id);
CREATE INDEX IF NOT EXISTS idx_code_versions_stable ON eng_it.code_versions(is_stable) WHERE is_stable = TRUE;
CREATE INDEX IF NOT EXISTS idx_code_versions_created ON eng_it.code_versions(created_at DESC);

-- 2. Extend patches table with new fields
ALTER TABLE eng_it.patches 
ADD COLUMN IF NOT EXISTS task_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS generated_by VARCHAR(50) DEFAULT 'manual',
ADD COLUMN IF NOT EXISTS previous_version_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS target_file TEXT;

-- Create indexes for patches
CREATE INDEX IF NOT EXISTS idx_patches_task ON eng_it.patches(task_id);
CREATE INDEX IF NOT EXISTS idx_patches_generated_by ON eng_it.patches(generated_by);

-- 3. Add foreign key constraint
ALTER TABLE eng_it.patches 
ADD CONSTRAINT IF NOT EXISTS fk_patches_task 
FOREIGN KEY (task_id) REFERENCES eng_it.tasks(id) ON DELETE SET NULL;

ALTER TABLE eng_it.patches 
ADD CONSTRAINT IF NOT EXISTS fk_patches_version 
FOREIGN KEY (previous_version_id) REFERENCES eng_it.code_versions(version_id) ON DELETE SET NULL;

-- 4. Comment tables for documentation
COMMENT ON TABLE eng_it.code_versions IS 'Stores historical versions of code files for rollback capability';
COMMENT ON COLUMN eng_it.code_versions.version_id IS 'Unique version identifier (format: taskid_timestamp)';
COMMENT ON COLUMN eng_it.code_versions.is_stable IS 'Marks known-good versions for nuclear rollback';

COMMENT ON COLUMN eng_it.patches.task_id IS 'Links patch to originating task';
COMMENT ON COLUMN eng_it.patches.generated_by IS 'Source: manual, llm_auto, or system';
COMMENT ON COLUMN eng_it.patches.previous_version_id IS 'Version ID before this patch was applied';
COMMENT ON COLUMN eng_it.patches.target_file IS 'Target file path for the patch';
