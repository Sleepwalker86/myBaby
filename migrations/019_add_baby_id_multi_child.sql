-- Migration 019: baby_id-Spalte für Mehrkind-Unterstützung (Issue #33)
-- DEFAULT 1 sorgt dafür, dass bestehende Ein-Kind-Installationen (baby_info.id = 1,
-- siehe 002_add_baby_info.sql) ohne Datenverlust weiterlaufen: alle vorhandenen
-- Zeilen gehören automatisch "Kind 1".
-- Hinweis: Die Model-Klassen filtern in dieser Stufe noch NICHT nach baby_id
-- (siehe Issue #33, Stufe 2) - das ist reine Schema-Vorbereitung.

ALTER TABLE sleep ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_sleep_baby_id ON sleep(baby_id);

ALTER TABLE feeding ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_feeding_baby_id ON feeding(baby_id);

ALTER TABLE bottle ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_bottle_baby_id ON bottle(baby_id);

ALTER TABLE diaper ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_diaper_baby_id ON diaper(baby_id);

ALTER TABLE temperature ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_temperature_baby_id ON temperature(baby_id);

ALTER TABLE medicine ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_medicine_baby_id ON medicine(baby_id);

ALTER TABLE night_waking ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_night_waking_baby_id ON night_waking(baby_id);

ALTER TABLE porridge ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_porridge_baby_id ON porridge(baby_id);

ALTER TABLE illness ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_illness_baby_id ON illness(baby_id);

ALTER TABLE weight ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_weight_baby_id ON weight(baby_id);

ALTER TABLE height ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_height_baby_id ON height(baby_id);

-- head_circumference (018_create_head_circumference.sql) wurde vor diesem Issue
-- gemergt und hatte noch keine baby_id-Spalte (siehe Issue #33, Abschnitt "Reihenfolge").
ALTER TABLE head_circumference ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_head_circumference_baby_id ON head_circumference(baby_id);

-- nap_suggestions-Cache (003_add_nap_suggestions.sql): der bestehende
-- UNIQUE(date, suggested_time)-Constraint bleibt vorerst unverändert, da SQLite
-- ALTER TABLE keine Constraint-Änderungen ohne Tabellen-Neuaufbau erlaubt und die
-- Vorschlagslogik in dieser Stufe noch nicht nach baby_id filtert (Issue #33,
-- Stufe 2 muss den Constraint auf UNIQUE(baby_id, date, suggested_time) erweitern,
-- sobald die Vorschlagslogik selbst umgestellt wird).
ALTER TABLE nap_suggestions ADD COLUMN baby_id INTEGER NOT NULL DEFAULT 1 REFERENCES baby_info(id);
CREATE INDEX IF NOT EXISTS idx_nap_suggestions_baby_id ON nap_suggestions(baby_id);
