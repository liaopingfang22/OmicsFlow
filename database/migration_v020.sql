-- OmicsFlow v0.2.0 Migration: UUID PK + Performance Indexes
-- Run: psql -h localhost -U postgres -d pipeline_test -f migration_v020.sql

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Add UUID columns (coexist with existing id for backward compat)
ALTER TABLE users ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();
ALTER TABLE datasets ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();
ALTER TABLE pipelines ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();
ALTER TABLE tasks ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();
ALTER TABLE sequencers ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();
ALTER TABLE projects ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();
ALTER TABLE samples ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();
ALTER TABLE sequencer_runs ADD COLUMN IF NOT EXISTS uid UUID DEFAULT uuid_generate_v4();

-- Create indexes for foreign keys and common queries
CREATE INDEX IF NOT EXISTS idx_tasks_owner_id ON tasks(owner_id);
CREATE INDEX IF NOT EXISTS idx_tasks_pipeline_id ON tasks(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tasks_owner_status ON tasks(owner_id, status);

CREATE INDEX IF NOT EXISTS idx_datasets_owner_id ON datasets(owner_id);
CREATE INDEX IF NOT EXISTS idx_datasets_checksum ON datasets(checksum);

CREATE INDEX IF NOT EXISTS idx_pipelines_type ON pipelines(pipeline_type);
CREATE INDEX IF NOT EXISTS idx_pipelines_owner ON pipelines(owner_id);

CREATE INDEX IF NOT EXISTS idx_task_results_task_id ON task_results(task_id);

CREATE INDEX IF NOT EXISTS idx_sequencer_runs_sequencer ON sequencer_runs(sequencer_id);
CREATE INDEX IF NOT EXISTS idx_sequencer_runs_status ON sequencer_runs(status);

CREATE INDEX IF NOT EXISTS idx_samples_run ON samples(run_id);
CREATE INDEX IF NOT EXISTS idx_samples_project ON samples(project_id);

CREATE INDEX IF NOT EXISTS idx_projects_owner ON projects(owner_id);

-- UUID indexes for future migration
CREATE INDEX IF NOT EXISTS idx_users_uid ON users(uid);
CREATE INDEX IF NOT EXISTS idx_tasks_uid ON tasks(uid);
CREATE INDEX IF NOT EXISTS idx_pipelines_uid ON pipelines(uid);
CREATE INDEX IF NOT EXISTS idx_datasets_uid ON datasets(uid);

-- Composite index for user login
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_active ON users(username) WHERE is_active = true;

-- Task queue queries
CREATE INDEX IF NOT EXISTS idx_tasks_status_created ON tasks(status, created_at DESC);

COMMENT ON COLUMN users.uid IS 'UUID for external API exposure';
COMMENT ON COLUMN tasks.uid IS 'UUID for external API exposure';
