-- Tabelle für Erkrankungen (Illness)

CREATE TABLE IF NOT EXISTS illness (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    type TEXT NOT NULL,
    symptoms TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_illness_start_time ON illness(start_time);
CREATE INDEX IF NOT EXISTS idx_illness_end_time ON illness(end_time);

