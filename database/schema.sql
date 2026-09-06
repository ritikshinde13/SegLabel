-- SegLabel SQLite Schema
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS destinations (
    name TEXT PRIMARY KEY,
    description TEXT,
    category TEXT DEFAULT 'service'
);

CREATE TABLE IF NOT EXISTS workloads (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    initial_identity_signal TEXT NOT NULL,
    current_identity TEXT NOT NULL,
    confirmed_identity TEXT,
    status TEXT NOT NULL CHECK(status IN ('STARTING', 'AMBIGUOUS', 'CONFIRMED', 'QUARANTINED', 'REVOKED')),
    status_reason TEXT,
    started_at TEXT NOT NULL,
    confirmed_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS identity_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workload_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT,
    identity_signal TEXT,
    details TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(workload_id) REFERENCES workloads(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS policies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_identity TEXT NOT NULL,
    destination TEXT NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('ALLOW', 'DENY')),
    description TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_identity, destination)
);

CREATE TABLE IF NOT EXISTS communication_requests (
    id TEXT PRIMARY KEY,
    workload_id TEXT NOT NULL,
    source_identity TEXT NOT NULL,
    destination TEXT NOT NULL,
    identity_status TEXT NOT NULL,
    decision TEXT NOT NULL CHECK(decision IN ('ALLOW', 'DENY')),
    reason TEXT NOT NULL,
    in_ambiguity_window INTEGER NOT NULL CHECK(in_ambiguity_window IN (0, 1)),
    timestamp TEXT NOT NULL,
    FOREIGN KEY(workload_id) REFERENCES workloads(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    workload_id TEXT NOT NULL,
    source TEXT NOT NULL,
    destination TEXT NOT NULL,
    identity_at_decision TEXT NOT NULL,
    identity_status TEXT NOT NULL,
    decision TEXT NOT NULL,
    reason TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    in_ambiguity_window INTEGER NOT NULL CHECK(in_ambiguity_window IN (0, 1)),
    FOREIGN KEY(request_id) REFERENCES communication_requests(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS verification_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workload_id TEXT NOT NULL,
    window_start TEXT NOT NULL,
    window_end TEXT NOT NULL,
    total_attempts INTEGER NOT NULL,
    allowed_in_window INTEGER NOT NULL,
    denied_in_window INTEGER NOT NULL,
    wrong_identity_access INTEGER NOT NULL,
    result TEXT NOT NULL CHECK(result IN ('PASS', 'FAIL')),
    summary TEXT NOT NULL,
    flagged_requests_json TEXT,
    verified_at TEXT NOT NULL,
    FOREIGN KEY(workload_id) REFERENCES workloads(id) ON DELETE CASCADE
);

-- Users Table for Dashboard Authentication
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER NOT NULL DEFAULT 1
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_requests_workload_time ON communication_requests(workload_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_workload ON audit_logs(workload_id);
CREATE INDEX IF NOT EXISTS idx_verification_workload ON verification_results(workload_id);
CREATE INDEX IF NOT EXISTS idx_events_workload ON identity_events(workload_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
