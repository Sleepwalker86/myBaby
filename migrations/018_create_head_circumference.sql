-- Migration 018: Kopfumfang-Tracking Tabelle
CREATE TABLE IF NOT EXISTS head_circumference (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    head_circumference_cm REAL NOT NULL CHECK(head_circumference_cm > 0 AND head_circumference_cm < 60),
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_head_circumference_timestamp ON head_circumference(timestamp);
