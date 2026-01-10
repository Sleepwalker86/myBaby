-- Tabelle für gespeicherte Nickerchen-Vorschläge
-- Verhindert, dass berechnete Zeiten nach hinten verschoben werden

CREATE TABLE IF NOT EXISTS nap_suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    suggested_time TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(date, suggested_time)
);

-- Index für schnelle Abfragen
CREATE INDEX IF NOT EXISTS idx_nap_suggestions_date ON nap_suggestions(date);

