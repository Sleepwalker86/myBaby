-- Migration 015: Gewichtstracking Tabelle
CREATE TABLE IF NOT EXISTS weight (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    weight_kg REAL NOT NULL CHECK(weight_kg > 0 AND weight_kg < 50),
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_weight_timestamp ON weight(timestamp);
