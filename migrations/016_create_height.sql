-- Migration 016: Größen-Tracking Tabelle
CREATE TABLE IF NOT EXISTS height (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    height_cm REAL NOT NULL CHECK(height_cm > 0 AND height_cm < 200),
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_height_timestamp ON height(timestamp);
