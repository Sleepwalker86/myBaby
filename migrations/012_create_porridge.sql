-- Migration 012: Brei-Tracking Tabelle
CREATE TABLE IF NOT EXISTS porridge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    amount INTEGER NOT NULL,
    food TEXT
);
