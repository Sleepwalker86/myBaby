-- Initiales Datenbankschema für Baby-Tracking App

-- Schlaf-Tracking (Nickerchen und Nachtschlaf)
CREATE TABLE IF NOT EXISTS sleep (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('nap', 'night')),
    start_time TEXT NOT NULL,
    end_time TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Stillen-Tracking
CREATE TABLE IF NOT EXISTS feeding (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    side TEXT NOT NULL CHECK(side IN ('links', 'rechts')),
    created_at TEXT DEFAULT (datetime('now'))
);

-- Flasche-Tracking
CREATE TABLE IF NOT EXISTS bottle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    amount INTEGER NOT NULL CHECK(amount > 0),
    created_at TEXT DEFAULT (datetime('now'))
);

-- Windel-Tracking
CREATE TABLE IF NOT EXISTS diaper (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('nass', 'groß', 'beides')),
    created_at TEXT DEFAULT (datetime('now'))
);

-- Temperatur-Tracking
CREATE TABLE IF NOT EXISTS temperature (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    value REAL NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Medizin-Tracking
CREATE TABLE IF NOT EXISTS medicine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    name TEXT NOT NULL,
    dose TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Indizes für bessere Performance
CREATE INDEX IF NOT EXISTS idx_sleep_start_time ON sleep(start_time);
CREATE INDEX IF NOT EXISTS idx_feeding_timestamp ON feeding(timestamp);
CREATE INDEX IF NOT EXISTS idx_bottle_timestamp ON bottle(timestamp);
CREATE INDEX IF NOT EXISTS idx_diaper_timestamp ON diaper(timestamp);
CREATE INDEX IF NOT EXISTS idx_temperature_timestamp ON temperature(timestamp);
CREATE INDEX IF NOT EXISTS idx_medicine_timestamp ON medicine(timestamp);

