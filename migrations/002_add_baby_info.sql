-- Baby-Informationen für Nickerchen-Vorschläge

CREATE TABLE IF NOT EXISTS baby_info (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    birth_date TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Füge einen Standard-Eintrag hinzu (falls noch keiner existiert)
INSERT OR IGNORE INTO baby_info (id, birth_date) VALUES (1, date('now', '-6 months'));

