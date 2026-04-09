"""
Database schema definitions for the Secure Training Platform.
All tables created via SQLite with WAL mode for concurrency.
"""

SCHEMA_SQL = """
-- ── Datasets ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS datasets (
    id              TEXT PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    description     TEXT,
    encrypted_file_path TEXT NOT NULL,
    encryption_key_id   TEXT NOT NULL,
    allowed_models  TEXT DEFAULT '[]',       -- JSON array of model names
    dataset_size    INTEGER DEFAULT 0,       -- size in bytes
    num_classes     INTEGER DEFAULT 10,
    input_shape     TEXT DEFAULT '[1,28,28]', -- JSON array
    num_samples     INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Encryption Keys (double-encrypted with master key) ────
CREATE TABLE IF NOT EXISTS encryption_keys (
    key_id          TEXT PRIMARY KEY,
    dataset_id      TEXT NOT NULL,
    encrypted_key   BLOB NOT NULL,           -- AES key encrypted with master key
    key_nonce       BLOB NOT NULL,           -- nonce for master-key encryption
    key_tag         BLOB NOT NULL,           -- GCM auth tag
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed   TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

-- ── Training Jobs ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS training_jobs (
    id              TEXT PRIMARY KEY,
    dataset_id      TEXT NOT NULL,
    model_type      TEXT NOT NULL,
    hyperparameters TEXT DEFAULT '{}',        -- JSON
    status          TEXT DEFAULT 'QUEUED',    -- QUEUED | RUNNING | COMPLETED | FAILED
    progress        REAL DEFAULT 0.0,        -- 0.0 to 1.0
    accuracy        REAL,
    loss            REAL,
    started_at      TIMESTAMP,
    completed_at    TIMESTAMP,
    error_msg       TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

-- ── Trained Models ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS trained_models (
    id              TEXT PRIMARY KEY,
    job_id          TEXT NOT NULL,
    dataset_id      TEXT NOT NULL,
    model_type      TEXT NOT NULL,
    file_path       TEXT NOT NULL,
    accuracy        REAL,
    loss            REAL,
    hyperparameters TEXT DEFAULT '{}',        -- JSON
    file_size       INTEGER DEFAULT 0,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id)     REFERENCES training_jobs(id),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

-- ── Audit Log ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type      TEXT NOT NULL,             -- KEY_ACCESS | JOB_SUBMIT | JOB_COMPLETE | API_CALL
    actor           TEXT DEFAULT 'system',
    details         TEXT DEFAULT '{}',         -- JSON
    ip_address      TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Indices ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_jobs_status ON training_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_dataset ON training_jobs(dataset_id);
CREATE INDEX IF NOT EXISTS idx_models_dataset ON trained_models(dataset_id);
CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_log(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(created_at);
"""
