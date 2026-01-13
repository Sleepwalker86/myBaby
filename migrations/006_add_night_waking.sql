-- Fügt die night_waking Tabelle hinzu für nächtliches Aufwachen
CREATE TABLE IF NOT EXISTS night_waking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TEXT NOT NULL,
    end_time TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Index für bessere Performance
CREATE INDEX IF NOT EXISTS idx_night_waking_start_time ON night_waking(start_time);

